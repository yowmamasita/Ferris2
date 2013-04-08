from ferris.core import inflector


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
        if not hasattr(self.handler, 'Scaffold'):
            setattr(self.handler, 'Scaffold', Scaffold)

        if not issubclass(self.handler.Scaffold, Scaffold):
            self.handler.Scaffold = type('Scaffold', (self.handler.Scaffold, Scaffold), {})

        setattr(self.handler, 'scaffold', self.handler.Scaffold(self.handler))

        if not hasattr(self.handler.Meta, 'Model'):
            _load_model(self.handler)

        self.handler.events.template_names += self._on_template_names

    def _on_template_names(self, handler, templates):
        """Injects scaffold templates into the template list"""

        handler, prefix, action, ext = self.handler.route.name, self.handler.route.prefix, self.handler.route.action, self.handler.meta.view.template_ext

        # Try the prefix template first
        if prefix:
            templates.append('scaffolding/%s_%s.%s' % (prefix, action, ext))

        # Then try the non-prefix one.
        templates.append('scaffolding/%s.%s' % (action, ext))


class Scaffold(object):
    """
    Scaffold Meta Object Base Class
    """
    def __init__(self, handler):
        if not hasattr(self, 'plural'):
            self.plural = inflector.pluralize(handler.name)
            self.singular = inflector.underscore(handler.name)


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
    handler.context.set(**{
        handler.scaffold.singular: handler.util.decode_key(key).get()})
