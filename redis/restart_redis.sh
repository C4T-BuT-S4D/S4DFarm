#!/usr/bin/env bash

docker-compose down -v && docker-compose up --build --always-recreate-deps -d
