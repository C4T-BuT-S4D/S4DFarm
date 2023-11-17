FROM golang:1.21-alpine3.18 as build

WORKDIR /app
COPY go.* .
COPY proxy proxy
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -o cacheproxy proxy/main.go

FROM alpine:3.18
COPY --from=build /app/cacheproxy /cacheproxy
CMD ["/cacheproxy"]
