import time

from flask import request, jsonify, abort

from server import app, database, reloader
from server.models import FlagStatus


@app.route('/api/get_config')
def get_config():
    if request.headers.get('AUTH') != get_config()['SERVER_PASSWORD']:
        abort(403)

    config = reloader.get_config()
    return jsonify({
        key: value
        for key, value in config.items()
        if 'PASSWORD' not in key and 'TOKEN' not in key
    })


@app.route('/api/post_flags', methods=['POST'])
def post_flags():
    if request.headers.get('AUTH') != get_config()['SERVER_PASSWORD']:
        abort(403)

    flags = request.get_json()

    cur_time = round(time.time())
    rows = [(item['flag'], item['sploit'], item['team'], cur_time, FlagStatus.QUEUED.name)
            for item in flags]

    db = database.get()
    db.executemany("INSERT OR IGNORE INTO flags (flag, sploit, team, time, status) "
                   "VALUES (?, ?, ?, ?, ?)", rows)
    db.commit()

    return ''
