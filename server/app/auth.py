from functools import wraps

from flask import request, abort

from reloader import get_config


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        config = get_config()
        if config['DEBUG']:
            return f(*args, **kwargs)

        auth = request.headers.get('Authorization')
        if auth != config['SERVER_PASSWORD']:
            abort(403)

        return f(*args, **kwargs)

    return decorated
