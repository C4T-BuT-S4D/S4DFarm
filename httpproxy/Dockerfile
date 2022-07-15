FROM golang:1.18-alpine as build

WORKDIR /app
COPY go.* ./
RUN go mod download

COPY proxy proxy
RUN CGO_ENABLED=0 go build -o cacheproxy proxy/main.go

FROM alpine

COPY --from=build /app/cacheproxy /cacheproxy
RUN chmod +x /cacheproxy

CMD ["/cacheproxy"]


