import socket
import logging
import time

from models import FlagStatus, SubmitResult

logger = logging.getLogger(__name__)

RESPONSES = {
    FlagStatus.QUEUED: [
        'ERR',
        'INV',
    ],
    FlagStatus.ACCEPTED: [
        'OK',
    ],
    FlagStatus.REJECTED: [
        'DUP',
        'OWN',
        'OLD',
    ],
}

READ_TIMEOUT = 5
APPEND_TIMEOUT = 0.05
BUFSIZE = 4096


def recvall(sock):
    sock.settimeout(READ_TIMEOUT)
    chunks = [sock.recv(BUFSIZE)]

    sock.settimeout(APPEND_TIMEOUT)
    while True:
        try:
            chunk = sock.recv(BUFSIZE)
            if not chunk:
                break

            chunks.append(chunk)
        except socket.timeout:
            break

    sock.settimeout(READ_TIMEOUT)
    return b''.join(chunks)


def submit_flags(flags, config):
    sock = socket.create_connection((config['SYSTEM_HOST'], config['SYSTEM_PORT']),
                                    READ_TIMEOUT)
    greeting = recvall(sock)
    if b'One flag per line please' not in greeting:
        raise Exception('Checksystem does not greet us: {}'.format(greeting))

    unknown_responses = set()
    sock.sendall(b'\n'.join(item.flag.encode() for item in flags) + b'\n')

    while len(flags) > 0:
        response = recvall(sock).decode().strip()
        if not response:
            break

        response = response.splitlines()
        for line in response:
            flag = flags[0]
            line = line.replace(f'{flag.flag} ', '')

            for status, substrings in RESPONSES.items():
                if any(s in line for s in substrings):
                    found_status = status
                    break
            else:
                found_status = FlagStatus.QUEUED
                if line not in unknown_responses:
                    unknown_responses.add(line)
                    logger.warning('Unknown checksystem response (flag will be resent): %s', line)

            if found_status == FlagStatus.QUEUED and time.time() - flag.time > 10:
                found_status = FlagStatus.REJECTED
                line = f'was response {line}, but inv flag too old'

            yield SubmitResult(flag.flag, found_status, line)

            flags = flags[1:]

    sock.close()
