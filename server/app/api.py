import importlib
import time
from collections import defaultdict
from datetime import datetime

import redis.exceptions
from flask import request, jsonify, Blueprint
from prometheus_client import Counter, Gauge

import auth
import reloader
from database import db_cursor
from models import FlagStatus

api = Blueprint('api', __name__, url_prefix='/api')

FLAGS_RECEIVED = Counter(
    'flags_received',
    'Number of flags received',
    ['sploit', 'team'],
)

TOTAL_TEAMS = Gauge('total_teams', 'Number of teams')
TOTAL_TEAMS.set_function(lambda: len(reloader.get_config()['TEAMS']))


@api.route('/get_config')
@auth.auth_required
def get_config():
    config = reloader.get_config()
    return jsonify({
        key: value
        for key, value in config.items()
        if 'PASSWORD' not in key and 'TOKEN' not in key
    })


@api.route('/post_flags', methods=['POST'])
@auth.auth_required
def post_flags():
    flags = request.json
    cur_time = round(time.time())
    config = reloader.get_config()

    if config.get('SYSTEM_VALIDATOR'):
        validator_module = importlib.import_module('validators.' + config['SYSTEM_VALIDATOR'])
        flags = validator_module.validate_flags(flags, config)

    rows = [
        {
            'flag': flag['flag'],
            'sploit': flag['sploit'],
            'team': flag['team'],
            'time': cur_time,
            'status': FlagStatus.QUEUED.name,
        }
        for flag in flags
    ]

    with db_cursor() as (conn, curs):
        curs.executemany(
            """
            INSERT INTO flags (flag, sploit, team, time, status)
            VALUES (%(flag)s, %(sploit)s, %(team)s, %(time)s, %(status)s)
            ON CONFLICT DO NOTHING
            """,
            rows,
        )
        conn.commit()

    for flag in flags:
        FLAGS_RECEIVED.labels(sploit=flag['sploit'], team=flag['team']).inc()

    return ''


@api.route('/filter_flags', methods=['GET'])
@auth.auth_required
def get_filtered_flags():
    filters = request.args

    conditions = []
    for column in ['sploit', 'status', 'team']:
        value = filters.get(column)
        if value:
            conditions.append((f'{column} = %s', value))

    for column in ['flag', 'checksystem_response']:
        value = filters.get(column)
        if value:
            conditions.append((f'POSITION(%s in LOWER({column})) > 0', value.lower()))

    for column in ['since', 'until']:
        value = filters.get(column, '').strip()
        if value:
            timestamp = round(datetime.strptime(value, '%Y-%m-%d %H:%M').timestamp())
            sign = '>=' if column == 'since' else '<='
            conditions.append((f'time {sign} %s', timestamp))

    page = int(filters.get('page', 1))
    if page < 1:
        raise ValueError('Invalid page')

    page_size = int(filters.get('page_size', 30))
    if page_size < 1 or page_size > 100:
        raise ValueError('Invalid page size')

    if conditions:
        chunks, values = list(zip(*conditions))
        conditions_sql = 'WHERE ' + ' AND '.join(chunks)
        conditions_args = list(values)
    else:
        conditions_sql = ''
        conditions_args = []

    sql = 'SELECT * FROM flags ' + conditions_sql + ' ORDER BY time DESC LIMIT %s OFFSET %s'
    args = conditions_args + [page_size, page_size * (page - 1)]

    count_sql = 'SELECT COUNT(*) as cnt FROM flags ' + conditions_sql
    count_args = conditions_args

    with db_cursor(True) as (_, curs):
        curs.execute(sql, args)
        flags = curs.fetchall()
        curs.execute(count_sql, count_args)
        total_count = curs.fetchone()['cnt']

    response = {
        'flags': list(map(dict, flags)),
        'page_size': page_size,
        'page': page,
        'total': total_count,
    }

    return jsonify(response)


@api.route('/filter_config', methods=['GET'])
@auth.auth_required
def get_filter_config():
    distinct_values = {}
    with db_cursor(True) as (_, curs):
        for column in ['sploit', 'status', 'team']:
            curs.execute(f'SELECT DISTINCT {column} FROM flags ORDER BY {column}')
            rows = curs.fetchall()
            distinct_values[column] = [item[column] for item in rows]

    config = reloader.get_config()

    server_tz_name = time.strftime('%Z')
    if server_tz_name.startswith('+'):
        server_tz_name = 'UTC' + server_tz_name

    response = {
        'filters': distinct_values,
        'flag_format': config['FLAG_FORMAT'],
        'server_tz': server_tz_name
    }

    return jsonify(response)


@api.route('/teams', methods=['GET'])
@auth.auth_required
def get_teams():
    teams = reloader.get_config()['TEAMS']
    response = list(map(
        lambda x: {'name': x[0], 'address': x[1]},
        teams.items(),
    ))
    return jsonify(response)
