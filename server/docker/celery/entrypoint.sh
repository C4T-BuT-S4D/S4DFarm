#!/bin/bash -e

celery \
    -A app.celery \
    worker \
    -E --beat \
    --schedule "${FARM_DATA}/schedule" \
    --loglevel INFO
