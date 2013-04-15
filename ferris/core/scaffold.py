from ferris.core import inflector
from ferris.core.forms import model_form


class Scaffolding(object):
    """
    Scaffolding Component
    """

    def __init__(self, Handler):
        self.handler = Handler
        self._init_meta()

    def _init_meta(self):
        """
        Constructs the handler's scaffold property from the handler's Scaffold class.
        If the handler doens't have a scaffold, uses the automatic one.
        """

        if not hasattr(self.handler.Meta, 'Model'):
            _load_model(self.handler)

        if not hasattr(self.handler, 'Scaffold'):
            setattr(self.handler, 'Scaffold', Scaffold)

        if not issubclass(self.handler.Scaffold, Scaffold):
            self.handler.Scaffold = type('Scaffold', (self.handler.Scaffold, Scaffold), {})

        setattr(self.handler, 'scaffold', self.handler.Scaffold(self.handler))

        self.handler.events.template_names += self._on_template_names
        self.handler.events.before_render += self._on_before_render

    def _on_template_names(self, handler, templates):
        """Injects scaffold templates into the template list"""

        handler, prefix, action, ext = self.handler.route.name, self.handler.route.prefix, self.handler.route.action, self.handler.meta.view.template_ext

        # Try the prefix template first
        if prefix:
            templates.append('scaffolding/%s_%s.%s' % (prefix, action, ext))

        # Then try the non-prefix one.
        templates.append('scaffolding/%s.%s' % (action, ext))

    def _on_before_render(self, handler):
        handler.context['scaffolding'] = {
            'name': handler.name,
            'proper_name': handler.proper_name,
            'title': handler.scaffold.title,
            'plural': handler.scaffold.plural,
            'singular': handler.scaffold.singular,
            'form_action': handler.scaffold.form_action,
            'form_encoding': handler.scaffold.form_encoding,
            'display_properties': handler.scaffold.display_properties
        }


class Scaffold(object):
    """
    Scaffold Meta Object Base Class
    """
    def __init__(self, handler):

        defaults = dict(
            title=inflector.titleize(handler.proper_name),
            plural=inflector.pluralize(handler.name),
            singular=inflector.underscore(handler.name),
            ModelForm=model_form(handler.meta.Model),
            display_properties=[name for name, property in handler.meta.Model._properties.items()],
            redirect=handler.uri(action='list'),
            form_action=None,
            form_encoding='application/x-www-form-urlencoded'
        )

        for k, v in defaults.iteritems():
            if not hasattr(self, k):
                setattr(self, k, v)


# Utility Functions


def _load_model(handler):
    import_form_base = '.'.join(handler.__module__.split('.')[:-2])
    # Attempt to import the model automatically
    model_name = inflector.singularize(handler.__class__.__name__)
    try:
        module = __import__('%s.models.%s' % (import_form_base, inflector.underscore(model_name)), fromlist=['*'])
        setattr(handler.Meta, 'Model', getattr(module, model_name))
    except (ImportError, AttributeError):
        raise RuntimeError("Scaffold coudn't automatically determine a model class for handler %s, please assign it a Meta.Model class variable." % handler.__class__.__name__)


# Handler Methods

def list(handler):
    handler.context.set(**{
        handler.scaffold.plural: handler.meta.Model.query()})


def view(handler, key):
    item = handler.util.decode_key(key).get()
    if not item:
        return 404

    handler.context.set(**{
        handler.scaffold.singular: item})


def add(handler):
    modelform = handler.scaffold.ModelForm()
    handler.parse_request(container=modelform)

    if handler.request.method in ('PUT', 'POST', 'PATCH'):
        if modelform.validate():
            item = handler.meta.Model(**modelform.data)
            item.put()

            if handler.scaffold.redirect:
                return handler.redirect(handler.scaffold.redirect)

    handler.context['form'] = modelform


def edit(handler, key):
    item = handler.util.decode_key(key).get()
    if not item:
        return 404

    modelform = handler.scaffold.ModelForm()
    handler.parse_request(container=modelform, fallback=item)

    if handler.request.method in ('PUT', 'POST', 'PATCH'):
        if modelform.validate():
            modelform.populate_obj(item)
            item.put()

            if handler.scaffold.redirect:
                return handler.redirect(handler.scaffold.redirect)

    handler.context.set(**{
        'form': modelform,
        handler.scaffold.singular: item})


def delete(handler, key):
    handler.util.decode_key(key).delete()
    return handler.redirect(handler.uri(action='list'))
