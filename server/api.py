import importlib
import time

from flask import request, jsonify

from server import app, auth, database, reloader
from server.models import FlagStatus


@app.route('/api/get_config')
@auth.api_auth_required
def get_config():
    config = reloader.get_config()
    return jsonify({
        key: value
        for key, value in config.items()
        if 'PASSWORD' not in key and 'TOKEN' not in key
    })


@app.route('/api/post_flags', methods=['POST'])
@auth.api_auth_required
def post_flags():
    flags = request.get_json()
    cur_time = round(time.time())
    config = reloader.get_config()

    if config.get('SYSTEM_VALIDATOR'):
        validator_module = importlib.import_module('server.validators.' + config['SYSTEM_VALIDATOR'])
        flags = validator_module.validate_flags(flags)

    rows = [(item['flag'], item['sploit'], item['team'], cur_time, FlagStatus.QUEUED.name)
            for item in flags]

    db = database.get()
    db.executemany("INSERT OR IGNORE INTO flags (flag, sploit, team, time, status) "
                   "VALUES (?, ?, ?, ?, ?)", rows)
    db.commit()

    return ''
