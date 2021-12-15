import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().absolute().parent
RESOURCES_DIR = BASE_DIR / 'resources'

CONFIG_PATH = BASE_DIR / 'config.py'
SCHEMA_PATH = RESOURCES_DIR / 'schema.sql'

REDIS_STORAGE_URL = os.getenv('REDIS_URL', 'redis://redis:6379/1')
POSTGRES_DSN = os.getenv('POSTGRES_DSN', 'host=postgres port=5432 dbname=farm')
