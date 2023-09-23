import importlib
import logging
import random
import traceback
from typing import List, TypeVar

from models import Flag, FlagStatus, SubmitResult

T = TypeVar('T')

logger = logging.getLogger(__name__)


def get_fair_share(groups: List[List[T]], limit: int) -> List[T]:
    if not groups:
        return []

    groups = sorted(groups, key=len)
    places_left = limit
    group_count = len(groups)
    fair_share = places_left // group_count

    result = []
    residuals = []
    for group in groups:
        if len(group) <= fair_share:
            result += group

            places_left -= len(group)
            group_count -= 1
            if group_count > 0:
                fair_share = places_left // group_count
            # The fair share could have increased because the processed group
            # had a few elements. Sorting order guarantees that the smaller
            # groups will be processed first.
        else:
            selected = random.sample(group, fair_share + 1)
            result += selected[:-1]
            residuals.append(selected[-1])
    result += random.sample(residuals, min(limit - len(result), len(residuals)))

    random.shuffle(result)
    return result


def submit_flags(flags: List[Flag], config) -> List[SubmitResult]:
    module_path = 'protocols.' + config['SYSTEM_PROTOCOL']
    logger.debug('importing the protocol from %s', module_path)
    module = importlib.import_module(module_path)

    try:
        return list(module.submit_flags(flags, config))
    except Exception as e:
        message = '{}: {}'.format(type(e).__name__, str(e))
        logger.error('Exception in submit protocol: %s\n%s', message, traceback.format_exc())
        return [SubmitResult(item.flag, FlagStatus.QUEUED, message) for item in flags]
