import time
from collections import defaultdict

from celery import shared_task
from celery.utils.log import get_task_logger

import reloader
from database import db_cursor
from models import Flag, FlagStatus
from utils import get_fair_share, submit_flags

logger = get_task_logger(__name__)


@shared_task
def submit_flags_task():
    logger.info('Starting submit_flags task')
    config = reloader.get_config()
    now = time.time()
    skip_time = round(now - config['FLAG_LIFETIME'])

    with db_cursor(True) as (conn, curs):
        curs.execute(
            """
            UPDATE flags SET status = %s WHERE status = %s AND time < %s
            """,
            (FlagStatus.SKIPPED.name, FlagStatus.QUEUED.name, skip_time),
        )
        conn.commit()
        curs.execute(
            """
            SELECT * FROM flags WHERE status = %s
            """,
            (FlagStatus.QUEUED.name,),
        )
        queued_flags = [Flag(**item) for item in curs.fetchall()]

    logger.info('Flags in queue: %s', len(queued_flags))

    if queued_flags:
        grouped_flags = defaultdict(list)
        for item in queued_flags:
            grouped_flags[item.sploit, item.team].append(item)
        flags = get_fair_share(list(grouped_flags.values()), config['SUBMIT_FLAG_LIMIT'])

        logger.info('Submitting %s/%s queued flags', len(flags), len(queued_flags))

        results = submit_flags(flags, config)

        rows = [(item.status.name, item.checksystem_response, item.flag) for item in results]
        with db_cursor(True) as (conn, curs):
            curs.executemany(
                """
                UPDATE flags SET status = %s, checksystem_response = %s WHERE flag = %s
                """,
                rows,
            )
            conn.commit()
