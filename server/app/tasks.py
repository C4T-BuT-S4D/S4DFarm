import time
from collections import defaultdict

from celery import shared_task
from celery.utils.log import get_task_logger

import database
import reloader
from models import Flag, FlagStatus
from utils import get_fair_share, submit_flags

logger = get_task_logger(__name__)


@shared_task
def submit_flags_task():
    logger.info('Starting submit_flags task')
    db = database.get(context_bound=False)
    config = reloader.get_config()
    now = time.time()
    skip_time = round(now - config['FLAG_LIFETIME'])
    db.execute("UPDATE flags SET status = ? WHERE status = ? AND time < ?",
               (FlagStatus.SKIPPED.name, FlagStatus.QUEUED.name, skip_time))
    db.commit()

    cursor = db.execute("SELECT * FROM flags WHERE status = ?", (FlagStatus.QUEUED.name,))
    queued_flags = [Flag(**item) for item in cursor.fetchall()]
    logger.info('Flags in queue: %s', len(queued_flags))

    if queued_flags:
        grouped_flags = defaultdict(list)
        for item in queued_flags:
            grouped_flags[item.sploit, item.team].append(item)
        flags = get_fair_share(list(grouped_flags.values()), config['SUBMIT_FLAG_LIMIT'])

        logger.info('Submitting %s/%s queued flags', len(flags), len(queued_flags))

        results = submit_flags(flags, config)

        rows = [(item.status.name, item.checksystem_response, item.flag) for item in results]
        db.executemany("UPDATE flags SET status = ?, checksystem_response = ? "
                       "WHERE flag = ?", rows)
        db.commit()
