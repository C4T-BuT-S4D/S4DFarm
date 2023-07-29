#!/bin/bash -e

# Threaded workers are required for metrics to work.
celery \
    -A app_celery.celery \
    worker \
    --pool threads \
    -E --beat \
    --schedule "${FARM_DATA}/schedule" \
    --loglevel INFO
