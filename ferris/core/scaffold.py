from ferris.core import inflector, autoadmin
from ferris.core.forms import model_form
from ferris.components.flash_messages import FlashMessages
(autoadmin)  # load autoadmin here, if any handler use scaffold it'll be included and initialized


class Scaffolding(object):
    """
    Scaffolding Component
    """

    def __init__(self, Handler):
        self.handler = Handler
        self._init_meta()
        self._init_flash()

    def _init_flash(self):
        if not FlashMessages in self.handler.Meta.components:
            self.handler.components['flash_messages'] = FlashMessages(self.handler)

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
            form_encoding='application/x-www-form-urlencoded',
            flash_messages=True
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


def _flash(handler, *args, **kwargs):
    if 'flash_messages' in handler.components and handler.scaffold.flash_messages:
        handler.components.flash_messages(*args, **kwargs)


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
    # Get the form/message and data
    modelform = handler.scaffold.ModelForm()
    handler.parse_request(container=modelform)

    # If the form was submitted
    if handler.request.method in ('PUT', 'POST', 'PATCH'):
        if modelform.validate():  # validate the container
            handler.events.scaffold_before_apply(handler=handler, container=modelform, item=None)

            # construct the item
            item = handler.meta.Model(**modelform.data)

            handler.events.scaffold_before_save(handler=handler, container=modelform, item=item)
            # save the item
            item.put()
            handler.events.scaffold_after_save(handler=handler, container=modelform, item=item)

            # set the item in the context to allow other things to access it.
            handler.context.set(**{
                handler.scaffold.singular: item})

            # Flash Message
            _flash(handler, 'The item was created successfully', 'success')

            # redirect
            if handler.scaffold.redirect:
                return handler.redirect(handler.scaffold.redirect)

        else:
            _flash(handler, 'There were errors on the form, please correct and try again.', 'error')

    # expose the form/message to the template.
    handler.context['form'] = modelform


def edit(handler, key):
    item = handler.util.decode_key(key).get()
    if not item:
        return 404

    modelform = handler.scaffold.ModelForm()
    handler.parse_request(container=modelform, fallback=item)

    if handler.request.method in ('PUT', 'POST', 'PATCH'):
        if modelform.validate():

            handler.events.scaffold_before_apply(handler=handler, container=modelform, item=None)
            modelform.populate_obj(item)

            handler.events.scaffold_before_save(handler=handler, container=modelform, item=item)
            item.put()
            handler.events.scaffold_after_save(handler=handler, container=modelform, item=item)

            handler.context.set(**{
                handler.scaffold.singular: item})

            _flash(handler, 'The item was saved successfully', 'success')

            if handler.scaffold.redirect:
                return handler.redirect(handler.scaffold.redirect)

        else:
            _flash(handler, 'There were errors on the form, please correct and try again.', 'error')

    handler.context.set(**{
        'form': modelform,
        handler.scaffold.singular: item})


def delete(handler, key):
    key = handler.util.decode_key(key)
    handler.events.scaffold_before_delete(handler=handler, key=key)
    key.delete()
    handler.events.scaffold_after_delete(handler=handler, key=key)
    _flash(handler, 'The item was deleted successfully', 'success')
    if handler.scaffold.redirect:
        return handler.redirect(handler.scaffold.redirect)
