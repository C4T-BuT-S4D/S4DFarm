#!/usr/bin/env python3

import random
import sys
from time import sleep

ip = sys.argv[1]

print(ip)

while True:
    print("First flag is %031d=" % random.randrange(0, 10000), flush=True)
    sleep(1)