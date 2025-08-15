import requests
import logging
import json

from models import FlagStatus, SubmitResult

logger = logging.getLogger(__name__)

RESPONSES = {
    FlagStatus.QUEUED: ['timeout', 'game not started', 'try again later', 'game over', 'is not up',
                        'no such flag'],
    FlagStatus.ACCEPTED: ['accept'],
    FlagStatus.REJECTED: ['wrong', 'duplicated'],
}

TIMEOUT = 5


def submit_flags(flags, config):
    r = requests.post(
        config['SYSTEM_URL'],
        params={
            'flags': [item.flag for item in flags],
            'token': config['TEAM_TOKEN'],
        },
        timeout=TIMEOUT,
    )

    logger.info('Checksystem response: %s', r.text)

    response_json = json.loads(r.json())

    unknown_responses = set()
    for flag, item in zip(flags, response_json):
        response_lower = item.lower()
        for status, substrings in RESPONSES.items():
            if any(s in response_lower for s in substrings):
                found_status = status
                break
        else:
            found_status = FlagStatus.QUEUED
            if response_lower not in unknown_responses:
                unknown_responses.add(response_lower)
                logger.warning('Unknown checksystem response (flag will be resent): %s', response_lower)

        yield SubmitResult(flag.flag, found_status, item)
