import logging
import signal

from gevent import signal as gsignal
from werkzeug import serving

import submit_loop
from flask_factory import create_app

app = create_app()

if not serving.is_running_from_reloader():
    app.logger.info('Not running from reloader')
    submit_loop_thread = submit_loop.SubmitThread(app)


    def close_submit_loop_thread(_signum, _frame):
        app.logger.info('Trying to stop submit loop')
        submit_loop_thread.is_active = False


    gsignal.signal(signal.SIGINT, close_submit_loop_thread)

    submit_loop_thread.start()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
