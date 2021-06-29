from volgactf.final.flag_api import FlagAPIHelper, SubmitResult as SR

from models import FlagStatus, SubmitResult

RESPONSES = {
    FlagStatus.QUEUED: [
        SR.ERROR_ACCESS_DENIED,
        SR.ERROR_COMPETITION_NOT_STARTED,
        SR.ERROR_COMPETITION_PAUSED,
        SR.ERROR_RATELIMIT,
        SR.ERROR_FLAG_NOT_FOUND,
        SR.ERROR_SERVICE_STATE_INVALID,
    ],
    FlagStatus.ACCEPTED: [
        SR.SUCCESS,
    ],
    FlagStatus.REJECTED: [
        SR.ERROR_COMPETITION_FINISHED,
        SR.ERROR_FLAG_INVALID,
        SR.ERROR_FLAG_EXPIRED,
        SR.ERROR_FLAG_YOUR_OWN,
        SR.ERROR_FLAG_SUBMITTED,
    ],
}


def submit_flags(flags, config):
    flag_help = FlagAPIHelper(config['SYSTEM_HOST'])
    for item in flags:
        result = flag_help.submit(item.flag)[0]
        code = result['code']
        flag = result['flag']

        found_status = None
        data = f'Invalid response: {code}'
        for response, r_codes in RESPONSES.items():
            for r_code in r_codes:
                if r_code == code:
                    found_status = response
                    data = str(r_code.name)
                    break

        yield SubmitResult(flag, found_status, data)
