import logging
import os

from celery import Celery
from flask import Flask
from flask_cors import CORS

from api import api
from database import close_db
from reloader import get_config
from stats import stats


def create_app():
    app = Flask('ad_farm')

    # Trigger singleton init
    app.config.update(get_config())

    app.logger.setLevel(logging.DEBUG)
    for handler in app.logger.handlers:
        handler.setLevel(logging.DEBUG)

    app.register_blueprint(api)
    app.register_blueprint(stats)
    app.teardown_appcontext(close_db)

    CORS(app)

    return app


def create_celery():
    broker = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    celery = Celery(
        'ad_farm',
        broker=broker,
        include=['tasks'],
    )
    period = get_config()['SUBMIT_PERIOD']
    celery.conf.beat_schedule = {
        f'add-every-{period}-seconds': {
            'task': 'tasks.submit_flags_task',
            'schedule': period,
        },
    }
    return celery
