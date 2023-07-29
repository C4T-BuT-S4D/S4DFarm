#!/bin/bash -e

gunicorn \
    --worker-class gevent \
    --worker-connections 1024 \
    --bind 0.0.0.0:5000 \
    --timeout 120 \
    app_flask:app
