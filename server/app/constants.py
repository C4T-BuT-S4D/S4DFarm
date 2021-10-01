import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().absolute().parent
RESOURCES_DIR = BASE_DIR / 'resources'

CONFIG_PATH = BASE_DIR / 'config.py'
SCHEMA_PATH = RESOURCES_DIR / 'schema.sql'

if farm_data := os.getenv('FARM_DATA'):
    DATA_DIR = Path(farm_data)
else:
    DATA_DIR = BASE_DIR / 'data'

DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / 'flags.sqlite'

REDIS_STORAGE_URL = os.getenv('REDIS_URL', 'redis://redis:6379/1')
