from ferris.core import plugins
import threading
import logging
from .models.setting import Setting as SettingsModel


plugins.register('settings')

local_cache = threading.local()


def activate(settings):
    if not hasattr(local_cache, 'overrides'):
        local_cache.overrides = SettingsModel.get_settings(settings)
    settings.update(local_cache.overrides)


def is_active():
    return hasattr(local_cache, 'overrides')
