import importlib
import threading
from typing import Optional

import config
from constants import CONFIG_PATH


class ConfigReloader:
    def __init__(self, app):
        self.app = app
        self.lock = threading.Lock()
        self.config = config.CONFIG
        self.updated_at = None

    def get_config(self):
        self._check_config()
        return self.config

    def _check_config(self):
        cur_mtime = CONFIG_PATH.stat().st_mtime_ns
        if cur_mtime != self.updated_at:
            with self.lock:
                if cur_mtime != self.updated_at:
                    try:
                        importlib.reload(config)
                        self.config = config.CONFIG
                        with self.app.app_context():
                            self.app.logger.info('New config loaded')
                    except Exception as e:
                        with self.app.app_context():
                            self.app.logger.error('Failed to reload config: %s', e)

                    self.updated_at = cur_mtime


_reloader_lock = threading.Lock()
_reloader: Optional[ConfigReloader] = None


def get_config(app=None):
    global _reloader
    with _reloader_lock:
        if _reloader is None:
            assert app is not None, 'Reloader is not initialized, but app=None'
            _reloader = ConfigReloader(app)
            app.logger.info('Created reloader instance')
    return _reloader.get_config()
