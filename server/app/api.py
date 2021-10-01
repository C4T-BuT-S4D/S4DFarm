import importlib
import time
from collections import defaultdict
from datetime import datetime

import redis.exceptions
from flask import request, jsonify, Blueprint

import auth
import database
import reloader
from models import FlagStatus
from series import rts

api = Blueprint('api', __name__, url_prefix='/api')


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
        (flag['flag'], flag['sploit'], flag['team'], cur_time, FlagStatus.QUEUED.name)
        for flag in flags
    ]

    db = database.get()
    db.executemany("INSERT OR IGNORE INTO flags (flag, sploit, team, time, status) "
                   "VALUES (?, ?, ?, ?, ?)", rows)
    db.commit()

    grouped = defaultdict(int)
    labels = {}
    for flag in flags:
        sploit, team = flag['sploit'], flag['team']
        name = f'flag:{sploit}:{team}'
        grouped[name] += 1
        labels[name] = {'sploit': sploit, 'team': team, 'type': 'attack'}

    for name, v in grouped.items():
        try:
            rts.create(name, labels=labels[name], duplicate_policy='sum')
        except redis.exceptions.ResponseError:
            pass
        rts.add(name, cur_time, v)

    return ''


@api.route('/filter_flags', methods=['GET'])
@auth.auth_required
def get_filtered_flags():
    filters = request.args

    conditions = []
    for column in ['sploit', 'status', 'team']:
        value = filters.get(column)
        if value:
            conditions.append(('{} = ?'.format(column), value))

    for column in ['flag', 'checksystem_response']:
        value = filters.get(column)
        if value:
            conditions.append(('INSTR(LOWER({}), ?)'.format(column), value.lower()))

    for column in ['time-since', 'time-until']:
        value = filters.get(column, '').strip()
        if value:
            timestamp = round(datetime.strptime(value, '%Y-%m-%d %H:%M').timestamp())
            sign = '>=' if column == 'time-since' else '<='
            conditions.append(('time {} ?'.format(sign), timestamp))

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

    sql = 'SELECT * FROM flags ' + conditions_sql + ' ORDER BY time DESC LIMIT ? OFFSET ?'
    args = conditions_args + [page_size, page_size * (page - 1)]
    flags = database.query(sql, args)

    sql = 'SELECT COUNT(*) FROM flags ' + conditions_sql
    args = conditions_args
    total_count = database.query(sql, args)[0][0]

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
    for column in ['sploit', 'status', 'team']:
        rows = database.query('SELECT DISTINCT {} FROM flags ORDER BY {}'.format(column, column))
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
