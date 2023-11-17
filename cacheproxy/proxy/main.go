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
	"time"

	"github.com/elazarl/goproxy"
	"github.com/redis/go-redis/v9"
)

const (
	envRedisURL         = "REDIS_URL"
	envAuthKey          = "AUTH_KEY"
	listenAddr          = ":8888"
	redisDeadline       = time.Second * 30
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

type cachingHandler struct {
	rc      *redis.Client
	authKey string
}

func (c *cachingHandler) getFromCache(ctx context.Context, key string) (string, error) {
	ctx, cancel := context.WithTimeout(ctx, redisDeadline)
	defer cancel()

	return c.rc.Get(ctx, key).Result()
}

func (c *cachingHandler) storeInCache(ctx context.Context, key string, value []byte, d time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, redisDeadline)
	defer cancel()

	_, err := c.rc.SetNX(ctx, key, value, d).Result()
	return err
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

	if c.overrideCacheFlag(r) {
		return r, nil
	}

	cachedResponseString, err := c.getFromCache(r.Context(), cd.cacheKey)
	if err == nil && len(cachedResponseString) > 0 {
		// Return cached response or proxy the request if the cache contains an invalid entry
		cachedResp, err := http.ReadResponse(bufio.NewReader(strings.NewReader(cachedResponseString)), r)
		if err != nil {
			ctx.Warnf("parsing cached response: %s", err)
			return r, nil
		}

		cd.alreadyCached = true
		return nil, cachedResp
	}

	return r, nil
}

func (c *cachingHandler) OnResponse(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
	// UserData isn't set when request authorization fails.
	if ctx.UserData == nil {
		return resp
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

	handler := cachingHandler{
		rc:      redis.NewClient(redopts),
		authKey: os.Getenv(envAuthKey),
	}

	proxy := goproxy.NewProxyHttpServer()
	proxy.Verbose = true

	proxy.OnRequest().HandleConnect(goproxy.AlwaysMitm)
	proxy.OnRequest().DoFunc(handler.OnRequest)
	proxy.OnResponse().DoFunc(handler.OnResponse)

	log.Printf("Proxy started on %s", listenAddr)
	srv := &http.Server{
		Addr:         listenAddr,
		Handler:      proxy,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: time.Minute,
		IdleTimeout:  time.Minute * 2,
	}

	log.Fatal(srv.ListenAndServe())
}
