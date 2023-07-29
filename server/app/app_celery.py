from factory import create_celery
from log import setup_logging
from prometheus_client import start_http_server

setup_logging('DEBUG')

celery = create_celery()

print('Starting prometheus server on port 5000')
start_http_server(port=5000)
