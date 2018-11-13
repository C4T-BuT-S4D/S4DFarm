import requests

from server import app
import json
from server.models import FlagStatus, SubmitResult


RESPONSES = {
    FlagStatus.QUEUED: ['timeout', 'game not started', 'try again later', 'game over', 'is not up',
                        'no such flag'],
    FlagStatus.ACCEPTED: ['accepted', 'congrat'],
    FlagStatus.REJECTED: ['bad', 'wrong', 'expired', 'unknown', 'your own',
                          'too old', 'not in database', 'already submitted', 'invalid flag'],
}
# The RuCTF checksystem adds a signature to all correct flags. It returns
# "invalid flag" verdict if the signature is invalid and "no such flag" verdict if
# the signature is correct but the flag was not found in the checksystem database.
#
# The latter situation happens if a checker puts the flag to the service before putting it
# to the checksystem database. We should resent the flag later in this case.


TIMEOUT = 5


def submit_flags(flags, config):
    for flag in flags:
        print(flag)
        r = requests.post(config['SYSTEM_URL'], json={"flag": flag.flag}, timeout=TIMEOUT).text
        print(r)
        r = json.loads(r)
        if r["success"]:
            yield SubmitResult(flag.flag, FlagStatus.ACCEPTED, "horosh")
        else:
            if 'Unable to post' in r["error"]["msg"]:
                yield SubmitResult(flag.flag, FlagStatus.QUEUED, r["error"]["msg"])
            else:
                yield SubmitResult(flag.flag, FlagStatus.REJECTED, r["error"]["msg"])