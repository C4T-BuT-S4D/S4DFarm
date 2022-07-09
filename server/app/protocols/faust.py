import socket

from flask import current_app as app

from models import FlagStatus, SubmitResult

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
    for item in flags:
        sock.sendall(item.flag.encode() + b'\n')
        response = recvall(sock).decode().strip()
        if response:
            response = response.splitlines()[0]
        response = response.replace('{} '.format(item.flag), '')

        for status, substrings in RESPONSES.items():
            if any(s in response for s in substrings):
                found_status = status
                break
        else:
            found_status = FlagStatus.QUEUED
            if response not in unknown_responses:
                unknown_responses.add(response)
                app.logger.warning('Unknown checksystem response (flag will be resent): %s', response)

        yield SubmitResult(item.flag, found_status, response)

    sock.close()
