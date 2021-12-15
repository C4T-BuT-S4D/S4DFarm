"""
Module with SQLite helpers, see http://flask.pocoo.org/docs/0.12/patterns/sqlite3/
"""

import logging
import threading
from contextlib import contextmanager

from psycopg2 import pool, extras

from constants import SCHEMA_PATH, POSTGRES_DSN

logger = logging.getLogger(__name__)


class DBPool:
    _lock = threading.RLock()
    _value = None

    @staticmethod
    def create():
        p = pool.ThreadedConnectionPool(
            minconn=5,
            maxconn=20,
            dsn=POSTGRES_DSN,
        )
        conn = p.getconn()
        logger.info("Initializing db schema")
        try:
            with conn.cursor() as curs:
                curs.execute(SCHEMA_PATH.read_text())
                conn.commit()
        finally:
            p.putconn(conn)
        return p

    @classmethod
    def get(cls):
        with cls._lock:
            if cls._value is None:
                cls._value = cls.create()
        return cls._value


@contextmanager
def db_cursor(dict_cursor: bool = True):
    db_pool = DBPool.get()
    conn = db_pool.getconn()

    if dict_cursor:
        curs = conn.cursor(cursor_factory=extras.RealDictCursor)
    else:
        curs = conn.cursor()
    try:
        yield conn, curs
    finally:
        curs.close()
        db_pool.putconn(conn)
