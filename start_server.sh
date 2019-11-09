#!/usr/bin/env bash

gunicorn --worker-class gevent --worker-connections 768 --bind 0.0.0.0:5000 --timeout 120 --reload server:app