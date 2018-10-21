import logging

from werkzeug.contrib.fixers import ProxyFix
from flask import Flask


app = Flask(__name__)

app.logger.setLevel(logging.DEBUG)
for handler in app.logger.handlers:
    handler.setLevel(logging.DEBUG)

app.wsgi_app = ProxyFix(app.wsgi_app)

import server.api
import server.submit_loop
import server.views
