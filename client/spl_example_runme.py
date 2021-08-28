#!/usr/bin/env python3

import os
import random
import sys

REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = 6378
REDIS_DB = 2

try:
    import redis

    cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
except ImportError:
    redis = None  # suppress import warning
    print('Redis is not installed, so you won\'t be able to use script caching')

if len(sys.argv) < 2:
    print(f'Usage: {sys.argv[0]} <target>')
    sys.exit(1)

ip = sys.argv[1]

print("Hello! I am a little sploit. I could be written on any language, but "
      "my author loves Python. Look at my source - it is really simple. "
      "I should steal flags and print them on stdout or stderr. ")

print(f"I need to attack a team with host `{ip}`.")

print("Here are some random flags for you:")

print("First flag is %031d=" % random.randrange(0, 10000), flush=True)
print("Second flag is %031d=" % random.randrange(0, 10000), flush=True)
