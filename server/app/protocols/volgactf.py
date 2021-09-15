from enum import Enum
from os import stat
from typing import Tuple, Optional
from models import FlagStatus, SubmitResult
import dateutil.parser
import datetime
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

BAD_RESPONSES = {
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
        self.session = requests.Session()
        self.api = f'https://{host}/api/flag/{version}'
        self.prepared_submit = requests.Request(
            method='post',
            url=f'{self.api}/submit',
            headers={'Content-Type': 'text/plain'}
        ).prepare()
        self.prepared_info = requests.Request(
            method='get',
            url=f'{self.api}/info'
        ).prepare()

    def info_flag_api(self, flag: str) -> Tuple[GetInfoResult, Optional[dict]]:
        original = self.prepared_info.url
        self.prepared_info.url += '/' + flag
        response = self.session.send(self.prepared_info)
        self.prepared_info.url = original

        if response.status_code == 200:
            return GetInfoResult.SUCCESS, response.json()
        else:
            try:
                respcode = GetInfoResult[response.text]
            except:
                respcode = GetInfoResult.ERROR_UNKNOWN
            return respcode, None

    def submit_flag_api(self, flag: str) -> ChecksystemResult:
        self.prepared_submit.prepare_body(flag)
        response = self.session.send(self.prepared_submit)

        try:
            return ChecksystemResult[response.text]
        except:
            return ChecksystemResult.ERROR_UNKNOWN

    def flag_is_fresh(info, until_seconds=2):
        expiry = dateutil.parser.parse(info['exp'])
        until = datetime.datetime.now() + datetime.timedelta(seconds=until_seconds)
        return expiry >= until

    def validate_flag(self, flag: str) -> Tuple[bool, Optional[Tuple[FlagStatus, str]]]:
        info_code, info = self.info_flag_api(flag)
        if info_code == GetInfoResult.SUCCESS:
            if self.flag_is_fresh(info):
                return True, None
            return False, (FlagStatus.REJECTED, 'expired')
        if info_code == GetInfoResult.ERROR_RATELIMIT:
            return False, (FlagStatus.QUEUED, 'flag info ratelimit')
        return False, (FlagStatus.QUEUED, f'error response from flag getinfo: {info_code}')

    def submit_flag(self, flag: str) -> Tuple[FlagStatus, str]:
        submit_code = self.submit_flag_api(flag)
        if submit_code == ChecksystemResult.SUCCESS:
            return FlagStatus.ACCEPTED, 'accepted'
        for status, possible_codes in BAD_RESPONSES.items():
            if submit_code in possible_codes:
                return status, BAD_RESPONSES[status][submit_code]
        return FlagStatus.QUEUED, f'unknown checksystem code: {submit_code}'

FLAG_INFO_RATE = 10
FLAG_SUBMIT_RATE = 5

def submit_flags(flags, config):
    api = API(config['SYSTEM_HOST'])

    submitted = 0
    # Validate as many flags as we can
    for flag in flags[:FLAG_INFO_RATE]:
        valid, info = api.validate_flag(flag)
        if valid:
            # While we haven't reached the rate limit, submit flags
            if submitted < FLAG_SUBMIT_RATE:
                status, message = api.submit_flag(flag)
                yield SubmitResult(flag, status, message)
                submitted += 1
            else:
                yield SubmitResult(flag, FlagStatus.QUEUED, 'flag submission ratelimit')
        yield SubmitResult(flag, info[0], info[1])
    # Queue others
    for flag in flags[FLAG_INFO_RATE:]:
        yield SubmitResult(flag, FlagStatus.QUEUED, 'flag info ratelimit')
