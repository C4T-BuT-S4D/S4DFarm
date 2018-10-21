#!/usr/bin/env bash

source destructive_farm_venv/bin/activate
gunicorn --worker-class gevent --worker-connections 768 --bind 0.0.0.0:5000 --reload --access-logfile logs/access.log --error-logfile logs/error.log server:app