import ferris
from ..models.setting import Setting


class Settings(ferris.Controller):
    class Meta:
        prefixes = ('admin',)
        components = (ferris.scaffold.Scaffolding,)
        Model = Setting

    def startup(self):
        self.context['setting_classes'] = Setting.get_classes()

    def admin_list(self):
        self.context['settings'] = ferris.settings.settings()

    def admin_edit(self, key):
        model = Setting.factory(key)
        instance = model.get_instance()

        self.meta.Model = model
        self.scaffold.ModelForm = ferris.model_form(model)

        self.context['settings_class'] = model

        def reload_settings(**kwargs):
            ferris.settings.load_settings()
            self.components.flash_messages('Settings saved, however, the settings may not be updated on all instances. You may have to restart instances for the settings to take effect.', 'warning')

        self.events.scaffold_after_save += reload_settings

        return ferris.scaffold.edit(self, instance.key.urlsafe())
