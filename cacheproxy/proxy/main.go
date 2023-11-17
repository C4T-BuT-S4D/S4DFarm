package main

import (
	"bufio"
	"bytes"
	"context"
	"crypto/subtle"
	"io"
	"log"
	"math/rand"
	"net/http"
	"net/http/httputil"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/elazarl/goproxy"
	"github.com/redis/go-redis/v9"
)

const (
	envRedisURL         = "REDIS_URL"
	envAuthKey          = "AUTH_KEY"
	listenAddr          = ":8888"
	redisDeadline       = time.Second * 30
	readLockInterval    = time.Millisecond * 25
	maxCacheDuration    = time.Minute * 5
	headerAuthKey       = "X-CBSProxy-Auth-Key"
	headerCacheDuration = "X-CBSProxy-Cache-Duration"
	headerCacheOverride = "X-CBSProxy-Cache-Override"
	headerCached        = "X-CBSProxy-Cached"
)

type cachingData struct {
	cacheKey      string
	cacheFor      time.Duration
	alreadyCached bool
}

type cachingContext struct {
	context.Context
	key       string
	keyUnlock func()
}

type cachingHandler struct {
	redis *redis.Client
	proxy *goproxy.ProxyHttpServer

	mu       sync.Mutex
	keylocks map[string]*sync.RWMutex
	authKey  string
}

func (c *cachingHandler) getFromCache(ctx context.Context, key string) (string, error) {
	rUnlock := c.rLockKey(key)
	defer rUnlock()

	ctx, cancel := context.WithTimeout(ctx, redisDeadline)
	defer cancel()

	return c.redis.Get(ctx, key).Result()
}

func (c *cachingHandler) storeInCache(ctx context.Context, key string, value []byte, d time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, redisDeadline)
	defer cancel()

	_, err := c.redis.SetNX(ctx, key, value, d).Result()
	return err
}

func (c *cachingHandler) getKeyLock(key string) *sync.RWMutex {
	c.mu.Lock()
	defer c.mu.Unlock()

	keyMu, ok := c.keylocks[key]
	if !ok {
		keyMu = new(sync.RWMutex)
		c.keylocks[key] = keyMu
	}

	return keyMu
}

// rLockKey locks a key for reading, blocking if needed.
func (c *cachingHandler) rLockKey(key string) (unlock func()) {
	keyMu := c.getKeyLock(key)

	keyMu.RLock()
	return keyMu.RUnlock
}

// tryLockKey tries to lock a key for writing without blocking.
func (c *cachingHandler) tryLockKey(key string) (ok bool, unlock func()) {
	keyMu := c.getKeyLock(key)

	if keyMu.TryLock() {
		return true, keyMu.Unlock
	}
	return false, nil
}

func (c *cachingHandler) getCacheDuration(r *http.Request) time.Duration {
	defer r.Header.Del(headerCacheDuration)

	val := r.Header.Get(headerCacheDuration)
	if val == "" {
		return 0
	}

	// Try parse duration first.
	if dur, err := time.ParseDuration(val); err == nil {
		return dur
	}

	// Parse number of seconds
	if durS, err := strconv.Atoi(val); err == nil {
		return time.Second * time.Duration(durS)
	}

	return 0
}

func (c *cachingHandler) overrideCacheFlag(r *http.Request) bool {
	defer r.Header.Del(headerCacheOverride)

	return r.Header.Get(headerCacheOverride) != ""
}

func (c *cachingHandler) validateDuration(d time.Duration) time.Duration {
	if d > 0 && d < time.Second {
		return time.Second
	}

	// the final duration fits: d <= 0 || (d >= time.Second && d <= maxCacheDuration)
	return min(d, maxCacheDuration)
}

func (c *cachingHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	ctx := &cachingContext{
		Context:   r.Context(),
		key:       "",
		keyUnlock: nil,
	}

	// proxy.ServeHTTP can fail after OnRequest has locked a key,
	// in which case that key would stay locked forever without this defer
	defer func() {
		if ctx.keyUnlock != nil {
			log.Printf("unlocking cache lock for %q", ctx.key)
			ctx.keyUnlock()
		}
	}()

	c.proxy.ServeHTTP(w, r.WithContext(ctx))
}

func (c *cachingHandler) OnRequest(r *http.Request, ctx *goproxy.ProxyCtx) (*http.Request, *http.Response) {
	if subtle.ConstantTimeCompare([]byte(r.Header.Get(headerAuthKey)), []byte(c.authKey)) != 1 {
		return nil, &http.Response{
			StatusCode: http.StatusUnauthorized,
			Header:     make(http.Header),
			Body:       io.NopCloser(bytes.NewReader(nil)),
			Trailer:    make(http.Header),
			Request:    r,
		}
	}

	cd := &cachingData{
		cacheKey:      r.URL.String(),
		cacheFor:      c.validateDuration(c.getCacheDuration(r)),
		alreadyCached: false,
	}

	ctx.UserData = cd

	// Forcefully override cache using response to this request.
	if c.overrideCacheFlag(r) {
		return r, nil
	}

	// Loop needed because the cache can be empty, but when we try to acquire a write lock,
	// someone could've already gotten it first, and we need to wait for them to finish and read the result.
	for {
		cachedResponseString, err := c.getFromCache(r.Context(), cd.cacheKey)
		if err == nil && len(cachedResponseString) > 0 {
			// Return cached response or proxy the request if the cache contains an invalid entry
			cachedResp, err := http.ReadResponse(bufio.NewReader(strings.NewReader(cachedResponseString)), r)
			if err != nil {
				ctx.Warnf("parsing cached response: %s", err)
				return r, nil
			}

			ctx.Logf("returning cached response for %q", cd.cacheKey)
			cd.alreadyCached = true
			return nil, cachedResp
		}

		ok, unlock := c.tryLockKey(cd.cacheKey)
		if !ok {
			// sleep for 25±5ms before next iteration
			time.Sleep(time.Duration(float64(readLockInterval) * (1 + rand.Float64()*0.4 - 0.2)))
			continue
		}

		// Write lock acquired:
		// - save the unlock function to be called in the ServeHTTP defer
		// - proxy the request and then save the response
		ctx.Logf("cache lock acquired for %q, will proxy request", cd.cacheKey)
		cachingCtx := r.Context().(*cachingContext)
		cachingCtx.keyUnlock = unlock
		cachingCtx.key = cd.cacheKey
		return r, nil
	}
}

func (c *cachingHandler) OnResponse(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
	if ctx.UserData == nil {
		// UserData isn't set when request authorization fails.
		return resp
	} else if resp == nil {
		// resp is nil when an error has occurred
		return nil
	}

	cd, ok := ctx.UserData.(*cachingData)
	if !ok {
		ctx.Warnf("proxy context data contained %T instead of *cachingData", ctx.UserData)
		return resp
	}

	resp.Header.Set(headerCached, strconv.FormatBool(cd.alreadyCached))
	if cd.alreadyCached || cd.cacheFor <= 0 {
		return resp
	}

	dump, err := httputil.DumpResponse(resp, true)
	if err != nil {
		ctx.Warnf("dumping HTTP response with body: %s", err)
		return resp
	}

	if err := c.storeInCache(ctx.Req.Context(), cd.cacheKey, dump, cd.cacheFor); err != nil {
		ctx.Warnf("storing dumped result in cache: %s", err)
	}
	return resp
}

func main() {
	redopts, err := redis.ParseURL(os.Getenv(envRedisURL))
	if err != nil {
		log.Fatalf("Failed to parse %s: %s", envRedisURL, err)
	}

	handler := &cachingHandler{
		redis:    redis.NewClient(redopts),
		proxy:    goproxy.NewProxyHttpServer(),
		keylocks: make(map[string]*sync.RWMutex),
		authKey:  os.Getenv(envAuthKey),
	}

	handler.proxy.Verbose = true
	handler.proxy.OnRequest().HandleConnect(goproxy.AlwaysMitm)
	handler.proxy.OnRequest().DoFunc(handler.OnRequest)
	handler.proxy.OnResponse().DoFunc(handler.OnResponse)

	log.Printf("Proxy started on %s", listenAddr)
	srv := &http.Server{
		Addr:         listenAddr,
		Handler:      handler,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: time.Minute,
		IdleTimeout:  time.Minute * 2,
	}

	log.Fatal(srv.ListenAndServe())
}
