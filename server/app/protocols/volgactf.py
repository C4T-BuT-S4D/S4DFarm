from enum import Enum
from typing import Iterable, List, Tuple, Optional
from models import FlagStatus, SubmitResult
import dateutil.parser
import datetime
import grequests
import requests

class ChecksystemResult(Enum):
    SUCCESS = 0  # submitted flag has been accepted
    ERROR_UNKNOWN = 1  # generic error
    ERROR_ACCESS_DENIED = 2  # the attacker does not appear to be a team
    ERROR_COMPETITION_NOT_STARTED = 3  # contest has not been started yet
    ERROR_COMPETITION_PAUSED = 4  # contest has been paused
    ERROR_COMPETITION_FINISHED = 5  # contest has been completed
    ERROR_FLAG_INVALID = 6  # submitted data has invalid format
    ERROR_RATELIMIT = 7  # attack attempts limit exceeded
    ERROR_FLAG_EXPIRED = 8  # submitted flag has expired
    ERROR_FLAG_YOUR_OWN = 9  # submitted flag belongs to the attacking team
    ERROR_FLAG_SUBMITTED = 10  # submitted flag has been accepted already
    ERROR_FLAG_NOT_FOUND = 11  # submitted flag hs not been found
    ERROR_SERVICE_STATE_INVALID = 12  # the attacking team service is not up

class GetInfoResult(Enum):
    SUCCESS = 0  # submitted flag has been accepted
    ERROR_UNKNOWN = 1  # generic error
    ERROR_ACCESS_DENIED = 2  # getinfo calls are allowed from a team's subnet
    ERROR_NOT_FOUND = 3  # flag is invalid
    ERROR_RATELIMIT = 4  # rate limit exceeded

RESPONSES = {
    FlagStatus.ACCEPTED: {
        ChecksystemResult.SUCCESS: 'success'
    },
    FlagStatus.QUEUED: {
        ChecksystemResult.ERROR_UNKNOWN: 'unknown error',
        ChecksystemResult.ERROR_ACCESS_DENIED: 'access denied',
        ChecksystemResult.ERROR_COMPETITION_NOT_STARTED: 'competition has not started',
        ChecksystemResult.ERROR_COMPETITION_PAUSED: 'competition is paused',
        ChecksystemResult.ERROR_COMPETITION_FINISHED: 'competition has finished',
        ChecksystemResult.ERROR_RATELIMIT: 'ratelimit exceeded',
        ChecksystemResult.ERROR_SERVICE_STATE_INVALID: 'attacking team service down',
    },
    FlagStatus.REJECTED: {
        ChecksystemResult.ERROR_FLAG_INVALID: 'invalid flag',
        ChecksystemResult.ERROR_FLAG_EXPIRED: 'expired',
        ChecksystemResult.ERROR_FLAG_YOUR_OWN: 'you own flag',
        ChecksystemResult.ERROR_FLAG_SUBMITTED: 'already submitted',
        ChecksystemResult.ERROR_FLAG_NOT_FOUND: 'not found',
    }
}

class API:
    def __init__(self, host, version='v1'):
        self.api = f'https://{host}/api/flag/{version}'

    @staticmethod
    def flag_is_fresh(info, until_seconds=2):
        expiry = dateutil.parser.parse(info['exp'])
        until = datetime.datetime.now() + datetime.timedelta(seconds=until_seconds)
        return expiry >= until

    @staticmethod
    def parse_flag_info_response(flag: str, response: requests.Response):
        if response.status_code == 200:
            info = response.json()
            if API.flag_is_fresh(info):
                return True, None
            return False, SubmitResult(flag, FlagStatus.REJECTED, 'expired')
        try:
            respcode = GetInfoResult[response.text]
        except:
            respcode = GetInfoResult.ERROR_UNKNOWN
        if respcode == GetInfoResult.ERROR_RATELIMIT:
            return False, SubmitResult(flag, FlagStatus.QUEUED, 'flag info ratelimit')
        return False, SubmitResult(flag, FlagStatus.QUEUED, f'error response from flag getinfo: {respcode}')

    def info_flags(self, *flags: str):
        pending = (grequests.get(f'{self.api}/info/{flag}') for flag in flags)
        responses = grequests.map(pending)
        return dict(zip(flags, map(API.parse_flag_info_response, flags, responses)))

    @staticmethod
    def parse_flag_submit_response(flag: str, response: requests.Response):
        try:
            result_code = ChecksystemResult[response.text]
        except:
            result_code = ChecksystemResult.ERROR_UNKNOWN
        for status, possible_codes in RESPONSES.items():
            if result_code in possible_codes:
                return SubmitResult(flag, status, RESPONSES[status][result_code])
        return SubmitResult(flag, FlagStatus.QUEUED, f'unknown checksystem code: {result_code}')

    def submit_flags(self, *flags: str):
        h = {'Content-Type': 'text/plain'}
        pending = (grequests.post(f'{self.api}/submit', data=flag, headers=h) for flag in flags)
        responses = grequests.map(pending)
        return map(API.parse_flag_submit_response, flags, responses)

def submit_flags(flags, config):
    api = API(config['SYSTEM_HOST'])
    info_rate = config['INFO_FLAG_LIMIT']
    submit_rate = config['SUBMIT_FLAG_LIMIT']

    # Get as much flag infos as we can
    flags_info = api.info_flags(*flags[:info_rate])
    flags_processed = info_rate

    # Filter by flags which we can submit
    submit_flags = filter(lambda flag: flags_info[flag][0], flags_info)
    # Other flags which are expired / invalid
    other_flags = map(lambda flag: flags_info[flag][1], filter(lambda flag: not flags_info[flag][0], flags_info))
    # Add extra flags to submit if we don't hae submit_rate valid flags
    if len(submit_flags) < submit_rate:
        flags_processed += submit_rate - len(submit_flags)
        submit_flags += flags[info_rate:flags_processed]

    for s in api.submit_flags(*submit_flags[:submit_rate]) + other_flags + \
            map(
                lambda f: SubmitResult(f, FlagStatus.QUEUED, 'flag submission ratelimit'),
                submit_flags[submit_rate:] + flags[flags_processed:]
            ):
        yield s