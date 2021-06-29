import logging

from flask import Flask
from flask_cors import CORS

from api import api
from database import close_db
from reloader import get_config


def create_app():
    app = Flask('ad_farm')

    app.logger.setLevel(logging.DEBUG)
    for handler in app.logger.handlers:
        handler.setLevel(logging.DEBUG)

    # Trigger singleton init
    get_config(app)

    app.register_blueprint(api)
    app.teardown_appcontext(close_db)

    CORS(app)

    return app
