from enum import Enum
import requests
from server.models import FlagStatus, SubmitResult

API_PREFIX = 'api/capsule/v1'
SUBMIT_ENDPOINT = 'submit'

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

RESPONSES = {
        FlagStatus.ACCEPTED: {ChecksystemResult.SUCCESS, 'accepted'},
        FlagStatus.QUEUED: {
            ChecksystemResult.ERROR_UNKNOWN.value : 'unknown error',
            ChecksystemResult.ERROR_ACCESS_DENIED.value : 'access denied',
            ChecksystemResult.ERROR_COMPETITION_NOT_STARTED.value : 'competition has not started',
            ChecksystemResult.ERROR_COMPETITION_PAUSED.value : 'competition is paused',
            ChecksystemResult.ERROR_COMPETITION_FINISHED.value : 'competition has finished',
            ChecksystemResult.ERROR_RATELIMIT.value : 'ratelimit exceeded',
            ChecksystemResult.ERROR_SERVICE_STATE_INVALID.value : 'attacking team service down',
            },
        FlagStatus.REJECTED: {
            ChecksystemResult.ERROR_FLAG_INVALID.value : 'invalid flag',
            ChecksystemResult.ERROR_FLAG_EXPIRED.value : 'expired',
            ChecksystemResult.ERROR_FLAG_YOUR_OWN.value : 'you own flag',
            ChecksystemResult.ERROR_FLAG_SUBMITTED.value : 'already submitted',
            ChecksystemResult.ERROR_FLAG_NOT_FOUND.value : 'not found',
            }
        }

def submit_flags(flags, config):
    headers = {'Content-Type': 'text/plain'}
    possible_http_codes = [
        requests.codes.ok,
        requests.codes.bad_request,
        requests.codes.forbidden,
        requests.codes.request_entity_too_large,
        requests.codes.too_many_requests
        ]

    for item in flags:
        r = requests.post(
            "%s/%s/%s" % (config['SYSTEM_HOST'], API_PREFIX, SUBMIT_ENDPOINT),
            data=item.flag,
            headers=headers
            )

        if r.status_code not in possible_http_codes or r.text.strip() not in ChecksystemResult:
            yield SubmitResult(item.flag, FlagStatus.QUEUED, 'could not submit flag')
            continue
        code = ChecksystemResult[r.text]

        for status, possible_codes in RESPONSES.items():
            if code in possible_codes:
                yield SubmitResult(item.flag, status, RESPONSES[status][code])
