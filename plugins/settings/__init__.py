from ferris.core import plugins

plugins.register('settings')


from .models.setting import Setting as SettingModel


def activate(settings):
    overrides = SettingModel.get_settings()
    settings.update(overrides)
