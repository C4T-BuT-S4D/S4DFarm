package main

import (
	"bufio"
	"bytes"
	"context"
	"crypto/subtle"
	"io"
	"log"
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

const maxCacheDuration = time.Minute * 5

func popHeader(r *http.Request, key string) string {
	value := r.Header.Get(key)
	r.Header.Del(key)
	return value
}

// connDataKey is used for storing connContextData for a single connection in case of HTTPS,
// and a single request in case of plaintext HTTP.
type connDataKey struct{}

// connData contains the last locked key for the current connection/request,
// in case the proxy ends without calling OnResponse and we need to cleanup the lock.
type connData struct {
	proxyCtx *goproxy.ProxyCtx
	cacheKey string
	unlockFn func()
}

func (ccd *connData) cleanup() {
	if ccd.unlockFn != nil {
		ccd.proxyCtx.Logf("unlocking cache lock for %q", ccd.cacheKey)
		ccd.unlockFn()
		ccd.unlockFn = nil
	}
}

func connDataFromContext(ctx context.Context) *connData {
	return ctx.Value(connDataKey{}).(*connData)
}

func contextWithConnData(ctx context.Context, connData *connData) context.Context {
	return context.WithValue(ctx, connDataKey{}, connData)
}

// cleanupRoundTripper is a special RoundTripper which cleans up the connection data
// if the underlying proxy roundtripper returns an error. This is needed because
// RoundTrip fails during HTTPS proxying aren't reported via OnResponse, and thus aren't closed.
type cleanupRoundTripper struct{}

func (cleanupRoundTripper) RoundTrip(req *http.Request, ctx *goproxy.ProxyCtx) (*http.Response, error) {
	resp, err := ctx.Proxy.Tr.RoundTrip(req)
	if err != nil {
		connDataFromContext(req.Context()).cleanup()
	}

	return resp, err
}

// proxyData stores data about a request's caching configuration and
// state in the proxy context shared between OnRequest and OnResponse.
type proxyData struct {
	connData      *connData
	cacheKey      string
	cacheDuration time.Duration
	cacheHot      bool
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

	return c.redis.Get(ctx, key).Result()
}

func (c *cachingHandler) storeInCache(ctx context.Context, key string, value []byte, d time.Duration) error {
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

	// a few retries are needed because TryLock can fail during
	// high contention for all the goroutines trying to lock it.
	for i := 0; i < 5; i++ {
		if keyMu.TryLock() {
			return true, keyMu.Unlock
		}

		// Benchmarks have shown that this works better than runtime.Gosched()
		time.Sleep(time.Millisecond)
	}

	return false, nil
}

func (c *cachingHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	connData := new(connData)
	ctx := contextWithConnData(r.Context(), connData)

	// proxy.ServeHTTP can fail after OnRequest has locked a key,
	// in which case that key would stay locked forever without this defer
	defer connData.cleanup()

	c.proxy.ServeHTTP(w, r.WithContext(ctx))
}

func (c *cachingHandler) HandleConnect(host string, ctx *goproxy.ProxyCtx) (*goproxy.ConnectAction, string) {
	// UserData needs to be set here because the original CONNECT request only appears here,
	// and the OnRequest callback will receive MITM'd requests with their own contexts,
	// all of which need to be linked to this one in order to be properly cleaned up.
	data := &proxyData{connData: connDataFromContext(ctx.Req.Context())}
	data.connData.proxyCtx = ctx
	ctx.UserData = data

	return goproxy.MitmConnect, host
}

func validateDuration(d time.Duration) time.Duration {
	if d > 0 && d < time.Second {
		return time.Second
	}

	// the final duration fits: d <= 0 || (d >= time.Second && d <= maxCacheDuration)
	return min(d, maxCacheDuration)
}

func requestCacheDuration(r *http.Request) (d time.Duration) {
	defer func() {
		d = validateDuration(d)
	}()

	val := popHeader(r, "X-Cache-Duration")
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

func (c *cachingHandler) OnRequest(r *http.Request, ctx *goproxy.ProxyCtx) (*http.Request, *http.Response) {
	ctx.RoundTripper = cleanupRoundTripper{}

	// Either get UserData that was set during HandleConnect in case of HTTPS proxying,
	// additionally saving the connection context to the current request context, or create and set per-request data.
	var data *proxyData
	if ctx.UserData == nil {
		data = &proxyData{connData: connDataFromContext(r.Context())}
		data.connData.proxyCtx = ctx
		ctx.UserData = data
	} else {
		data = ctx.UserData.(*proxyData)
		r = r.WithContext(contextWithConnData(r.Context(), data.connData))
	}

	if subtle.ConstantTimeCompare([]byte(popHeader(r, "X-Cache-Auth-Key")), []byte(c.authKey)) != 1 {
		return nil, &http.Response{
			StatusCode: http.StatusUnauthorized,
			Header:     make(http.Header),
			Body:       io.NopCloser(bytes.NewReader(nil)),
			Trailer:    make(http.Header),
			Request:    r,
		}
	}

	data.cacheKey = r.URL.String()
	data.cacheDuration = requestCacheDuration(r)

	// Forcefully override cache using response to this request.
	if popHeader(r, "X-Cache-Override") != "" {
		return r, nil
	}

	// Loop needed because the cache can be empty, but when we try to acquire a write lock,
	// someone could've already gotten it first, and we need to wait for them to finish and read the result.
	for {
		cachedResponseString, err := c.getFromCache(r.Context(), data.cacheKey)
		if err == nil && len(cachedResponseString) > 0 {
			// Return cached response or proxy the request if the cache contains an invalid entry
			cachedResp, err := http.ReadResponse(bufio.NewReader(strings.NewReader(cachedResponseString)), r)
			if err != nil {
				ctx.Warnf("parsing cached response: %s", err)
				return r, nil
			}

			ctx.Logf("returning cached response for %q", data.cacheKey)
			data.cacheHot = true
			return nil, cachedResp
		}

		ok, unlock := c.tryLockKey(data.cacheKey)
		if !ok {
			// someone else should've acquired a lock by now, so RLock with block
			continue
		}

		// Write lock acquired:
		// - save the unlock function to be called in the ServeHTTP defer
		// - proxy the request and then save the response
		ctx.Logf("cache lock acquired for %q, will proxy request", data.cacheKey)
		data.connData.unlockFn = unlock
		data.connData.cacheKey = data.cacheKey
		return r, nil
	}
}

func (c *cachingHandler) OnResponse(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
	data := ctx.UserData.(*proxyData)
	defer data.connData.cleanup()

	// resp is nil when an error has occurred
	if resp == nil {
		return nil
	}

	resp.Header.Set("X-Cache-Hot", strconv.FormatBool(data.cacheHot))
	if data.cacheHot || data.cacheDuration <= 0 {
		return resp
	}

	dump, err := httputil.DumpResponse(resp, true)
	if err != nil {
		ctx.Warnf("dumping HTTP response with body: %s", err)
		return resp
	}

	if err := c.storeInCache(ctx.Req.Context(), data.cacheKey, dump, data.cacheDuration); err != nil {
		ctx.Warnf("storing dumped result in cache: %s", err)
	}
	return resp
}

func main() {
	redopts, err := redis.ParseURL(os.Getenv("REDIS_URL"))
	if err != nil {
		log.Fatalf("Failed to parse REDIS_URL: %s", err)
	}

	handler := &cachingHandler{
		redis:    redis.NewClient(redopts),
		proxy:    goproxy.NewProxyHttpServer(),
		keylocks: make(map[string]*sync.RWMutex),
		authKey:  os.Getenv("AUTH_KEY"),
	}

	handler.proxy.Verbose = os.Getenv("VERBOSE_LOGS") == "t"
	handler.proxy.OnRequest().HandleConnect(goproxy.FuncHttpsHandler(handler.HandleConnect))
	handler.proxy.OnRequest().DoFunc(handler.OnRequest)
	handler.proxy.OnResponse().DoFunc(handler.OnResponse)

	log.Printf("Proxy started on :8888")
	srv := &http.Server{
		Addr:        ":8888",
		Handler:     handler,
		ReadTimeout: time.Second * 10,
		IdleTimeout: time.Minute * 2,
	}

	log.Fatal(srv.ListenAndServe())
}
