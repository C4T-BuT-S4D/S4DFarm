#!/bin/bash -e

gunicorn --worker-class gevent --worker-connections 768 --bind 0.0.0.0:5000 --timeout 120 app:app
