#!/usr/bin/env python3

import socket
from time import sleep

create = """CREATE /vending_machine HTTP/1.0

name inventor meta {0} {0}

"""

TEAMS = ['10.23.{}.2'.format(i % 256) for i in range(1, 12) if i != 1]


def generate_spam_flag():
    import base64, hashlib, os, re
    encode = lambda s: re.sub(r'[a-z/+=\n]', r'', base64.encodebytes(s).decode()).upper()
    secret = '1234'

    prefix = encode(os.urandom(64))[:16]
    suffix = encode(hashlib.sha256((prefix + secret).encode()).digest())[:15]
    return prefix + suffix + '='


for ip in TEAMS:
    s = socket.socket()
    s.connect((ip, 11883))
    s.send(create.format(generate_spam_flag()).encode())

sleep(60)
