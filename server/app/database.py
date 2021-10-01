"""
Module with SQLite helpers, see http://flask.pocoo.org/docs/0.12/patterns/sqlite3/
"""

import logging
import sqlite3
import threading

from flask import g

from constants import DB_PATH, SCHEMA_PATH

_init_started = False
_init_lock = threading.RLock()

logger = logging.getLogger(__name__)


def _init(database):
    logger.info('Creating database schema at %s', DB_PATH)
    database.executescript(SCHEMA_PATH.read_text())


def get(context_bound=True):
    """
    If there is no opened connection to the SQLite database in the context
    of the current request or if context_bound=False, get() opens a new
    connection to the SQLite database. Reopening the connection on each request
    does not have a big overhead, but allows to avoid implementing a pool of
    thread-local connections (see https://stackoverflow.com/a/14520670).

    If the database did not exist, get() creates and initializes it.
    If get() is called from other threads at this time, they will wait
    for the end of the initialization.

    If context_bound=True, the connection will be closed after
    request handling (when the context will be destroyed).

    :returns: a connection to the initialized SQLite database
    """

    global _init_started

    if context_bound and 'database' in g:
        return g.database

    need_init = not DB_PATH.exists()
    database = sqlite3.connect(DB_PATH)
    database.row_factory = sqlite3.Row

    if need_init:
        with _init_lock:
            if not _init_started:
                _init_started = True
                _init(database)

    if context_bound:
        g.database = database
    return database


def query(sql, args=()):
    return get().execute(sql, args).fetchall()


def close_db(_):
    if 'database' in g:
        g.database.close()
