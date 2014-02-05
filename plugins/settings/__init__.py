from ferris.core import plugins
import threading

plugins.register('settings')


from .models.setting import Setting as SettingModel

local_cache = threading.local()


def activate(settings):
    if not hasattr(local_cache, 'overrides'):
        local_cache.overrides = SettingModel.get_settings()
    settings.update(local_cache.overrides)
