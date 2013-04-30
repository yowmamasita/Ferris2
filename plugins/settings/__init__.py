from ferris.core import events, plugins

plugins.register('settings')


@events.on('build_settings')
def on_build_settings(settings):
    from .models.setting import Setting
    overrides = Setting.get_settings()
    settings.update(overrides)
