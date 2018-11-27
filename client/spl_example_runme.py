#!/usr/bin/env python3

# Exploit format and this example was adopted
# from the exploit farm by Alexander Bersenev (https://github.com/alexbers/exploit_farm).

import random
import sys


# redis host is the same as farm host (usually, as farm starts redis server)
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6378
REDIS_DB = 2

try:
    import redis

    cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
except ImportError:
    print('Redis is not installed, so you won\'t be able to use script caching')

print("Hello! I am a little sploit. I could be written on any language, but "
      "my author loves Python. Look at my source - it is really simple. "
      "I should steal flags and print them on stdout or stderr. ")

print("I need to attack a team with host `%s`." % sys.argv[1])

print("Here are some random flags for you:")

print("First flag is %031d=" % random.randrange(0, 10000), flush=True)
print("Second flag is %031d=" % random.randrange(0, 10000), flush=True)
