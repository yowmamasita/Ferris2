from ferris.core import inflector
from ferris.core.ndb import util as ndb_util
from ferris.core.bunch import Bunch


class Mixin(object):
    """ Properties directly mixed-in to the handler """

    scaffold = Bunch()  # Will be a bunch object
    ModelForm = None  # The class for the model form
    modelform = None  # The instance of the class of the model form.

    def _scaffold_init(self):
        self.scaffold.update({
            'use_ids': False,  # If set to true, scaffolding will use key.id() instead of key.urlsafe()
            'display_properties': [],
            'should_save': True,  # Flag to disable saving on Add/Edit
            'flash_messages': True,  # Flag to display flash messages, if turned off no flash messages will work.
            'redirect': True,  # Flag to control redirection
            'form_action': None,  # The action that add/edit forms will post to.
            'form_encoding': 'application/x-www-form-urlencoded',  # The encoding method used by the forms.
        })

    def _scaffold_on_template_names(self, handler, templates):
        """Injects scaffold templates into the template list"""
        if not isinstance(templates, list):
            templates = [templates]

        # Try the prefix template first
        if self.prefix:
            scaffold_template = (
                'scaffolding/%s_%s.%s' % (self.prefix, self.action, self.template_ext))
            templates.append(scaffold_template)

        # Then try the non-prefix one.
        scaffold_template = (
            'scaffolding/%s.%s' % (self.action, self.template_ext))
        templates.append(scaffold_template)

    def _scaffold_on_before_render(self, handler):

        self.template_vars['scaffolding'] = {
            'name': self.name,
            'proper_name': self.proper_name,
            'title': inflector.titleize(self.proper_name),
            'pluralized': inflector.pluralize(self.name),
            'singularized': inflector.singularize(self.name),
            'key_id_for': ndb_util.key_id_for,
            'key_urlsafe_for': ndb_util.key_urlsafe_for,
            'url_id_for': self.url_id_for,
            'use_ids': self.scaffold.use_ids,
            'form_action': self.scaffold.form_action,
            'form_encoding': self.scaffold.form_encoding
        }

        self._determine_display_properties()

    def _determine_display_properties(self):

        if hasattr(self, 'Model'):
            display_props = []

            try:
                properties = self.Model._properties  # ndb support
                display_props = [(name, property) for name, property in properties.items()]

            except AttributeError:
                properties = self.Model.properties()
                display_props = [(name, property) for name, property in properties.items()]

            if self.scaffold.display_properties:
                display_props = [x for x in display_props if x[0] in self.scaffold.display_properties]

            self.template_vars['scaffolding'].update({
                'model_class': self.Model,
                'display_properties': display_props,
            })

    def get_modelform(self, obj=None):
        """
        Fetches or creates the form for the handler's model.
        """
        if self.modelform == None:
            self.modelform = self.ModelForm()
        self.process_form_data(self.modelform, obj=obj)
        return self.modelform

    def flash(self, message, type='info'):
        """
        Adds the given message to the list of "flash" messages to show to the user on the next page.
        This never occurs for json requests.
        """
        if not self.scaffold.flash_messages or self.is_json_request():
            return

        flash = self.session.get('__flash', list())
        flash.append((message, type))
        self.session['__flash'] = flash

    def should_redirect(self):
        return self.scaffold.redirect and not self.request.params.get('__ferris__no_redirect', False)

    def is_json_request(self):
        return (('json' in self.components and self.components.json.render_as_json)
            or self.request.content_type == 'application/json')
