package main

import (
	"bufio"
	"context"
	"fmt"
	"log"
	"net/http"
	"net/http/httputil"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/elazarl/goproxy"
	"github.com/go-redis/redis/v8"
)

const RedisDeadline = time.Second * 30

type cachingData struct {
	cacheKey      string
	cacheFor      time.Duration
	alreadyCached bool
}

type cachingHandler struct {
	cli *redis.Client
}

func (c *cachingHandler) getFromCache(key string) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), RedisDeadline)
	defer cancel()

	return c.cli.Get(ctx, key).Result()
}

func (c *cachingHandler) storeInCache(key string, value []byte, d time.Duration) error {
	ctx, cancel := context.WithTimeout(context.Background(), RedisDeadline)
	defer cancel()

	_, err := c.cli.SetNX(ctx, key, value, d).Result()
	return err
}

func (c *cachingHandler) getCacheDuration(r *http.Request) time.Duration {
	defer r.Header.Del("X-CBSProxy-Cache-Duration")

	val := r.Header.Get("X-CBSProxy-Cache-Duration")
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
	defer r.Header.Del("X-CBSProxy-Cache-Override")

	return r.Header.Get("X-CBSProxy-Cache-Override") != ""
}

func (c *cachingHandler) validateDuration(d time.Duration) time.Duration {
	if d <= 0 {
		return d
	}

	if d < time.Second {
		return time.Second
	}

	// Don't do stupid things.
	if d > time.Minute*5 {
		return time.Minute * 5
	}
	return d
}

func (c *cachingHandler) OnRequest(r *http.Request, ctx *goproxy.ProxyCtx) (*http.Request, *http.Response) {
	cd := c.getCacheDuration(r)
	cd = c.validateDuration(cd)

	cacheKey := r.URL.String()
	ctx.UserData = cachingData{cacheKey: cacheKey, cacheFor: cd, alreadyCached: false}

	cachedResponseString, err := c.getFromCache(cacheKey)
	if err == nil && len(cachedResponseString) > 0 {
		if c.overrideCacheFlag(r) {
			return r, nil
		}

		// Found response in cache. Try to decode.
		cachedResp, err := http.ReadResponse(bufio.NewReader(strings.NewReader(cachedResponseString)), r)
		if err != nil {
			fmt.Printf("Failed to parse cached response: %v\n", err)
			// Failed to decode will proxy the request.
			return r, nil
		}

		ctx.UserData = cachingData{cacheKey: cacheKey, cacheFor: cd, alreadyCached: true}
		return r, cachedResp
	}

	return r, nil
}

func (c *cachingHandler) OnResponse(resp *http.Response, ctx *goproxy.ProxyCtx) (out *http.Response) {
	cd, ok := ctx.UserData.(cachingData)
	if !ok {
		fmt.Printf("Failed to parse context: should be 'cachingData', got %T\n", cd)
		// Do not cache since we can't.
		return resp
	}

	if cd.alreadyCached {
		resp.Header.Set("X-CBSProxy-Cached", "true")
		return resp
	}

	defer func() {
		out.Header.Set("X-CBSProxy-Cached", "false")
	}()

	if cd.cacheFor == 0 {
		return resp
	}

	dump, err := httputil.DumpResponse(resp, true)
	if err != nil {
		fmt.Printf("Failed to dump HTTP response: %v \n", err)
		return resp
	}

	if err := c.storeInCache(cd.cacheKey, dump, cd.cacheFor); err != nil {
		fmt.Printf("Failed to store result in cache: %v \n", err)
	}
	return resp
}

func main() {
	redopts, err := redis.ParseURL(os.Getenv("REDIS_URL"))
	if err != nil {
		log.Fatal("Failed to parse REDIS_URL")
		return
	}

	handler := cachingHandler{redis.NewClient(redopts)}

	proxy := goproxy.NewProxyHttpServer()
	proxy.Verbose = true

	proxy.OnRequest().HandleConnect(goproxy.AlwaysMitm)
	proxy.OnRequest().DoFunc(handler.OnRequest)
	proxy.OnResponse().DoFunc(handler.OnResponse)

	fmt.Println("Proxy started on port 8888")
	log.Fatal(http.ListenAndServe(":8888", proxy))
}
