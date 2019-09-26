import logging

from flask import Flask
from gevent import signal
from werkzeug import serving
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)

app.logger.setLevel(logging.DEBUG)
for handler in app.logger.handlers:
    handler.setLevel(logging.DEBUG)

app.wsgi_app = ProxyFix(app.wsgi_app)

import server.api
import server.submit_loop
import server.views

if not serving.is_running_from_reloader():
    app.logger.info('Not running from reloader')
    submit_loop_thread = submit_loop.SubmitThread()


    def close_submit_loop_thread(_signum, _frame):
        app.logger.info('Trying to stop submit loop')
        submit_loop_thread.is_active = False

    signal.signal(signal.SIGINT, close_submit_loop_thread)
    submit_loop_thread.start()
