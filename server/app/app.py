from factory import create_app, create_celery
from log import setup_logging

setup_logging('DEBUG')

app = create_app()
celery = create_celery()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
