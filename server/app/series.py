import redis
from redistimeseries.client import Client

from constants import REDIS_STORAGE_URL

r = redis.Redis.from_url(REDIS_STORAGE_URL)
r.ping()
rts = Client(conn=r)
