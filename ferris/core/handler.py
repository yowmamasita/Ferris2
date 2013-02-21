import webapp2
import json
from settings import app_config
from webapp2 import Response, cached_property
from webapp2_extras import sessions
from google.appengine.api import users
from wtforms.ext.appengine.db import model_form
from ferris.core import inflector
from ferris.core.ndb import key_urlsafe_for, key_from_string
from ferris.core.uri import Uri
from ferris.core.event import NamedEvents
from ferris.core import events
from ferris.core.json_util import DatastoreEncoder, DatastoreDecoder
from scaffolding import Scaffolding, scaffold
import ferris.core.routing as routing
import ferris.core.template as templating
from bunch import Bunch
from webob.multidict import MultiDict
import logging


def route(f):
    """
    Marks a class method to enable it to be automatically routed and accessible via HTTP. This
    decorator should always be the outermost decorator.
    """
    setattr(f, 'route', True)
    return f


def route_with(*args, **kwargs):
    """
    Marks a class method to be routed and passes and additional arguments to the webapp2.Route
    constructor.

    :param template: Sets the URL template for this action
    """
    def inner(f):
        setattr(f, 'route', (args, kwargs))
        return f
    return inner


class Handler(webapp2.RequestHandler, Uri):
    """
    Handler allows grouping of common actions and provides them with
    automatic routing, reusable components, and automatic template
    discovery and rendering.
    """

    #: List of components.
    #: When declaring a handler, this must be a list of classes.
    #: When the handler is constructed, this will be transformed into a Bunch of instances.
    components = []

    #: If set to true, the handler will attempt to render the template determined by :meth:`_get_template_name` if an action returns ``None``.
    auto_render = True

    #: If set, this will be used as the template to render instead of calling :meth:`_get_template_name`
    template_name = None

    #: The extension used by :meth:`_get_template_name` when finding templates.
    template_ext = 'html'

    #: Set to change the theme used by render_template
    theme = None

    #: Context that is passed on to the template, use :meth:`get` and and :meth:`set`.
    template_vars = {}

    # Prefixes are added in from of handlers (like admin_list) and will cause routing
    # to produce a url such as '/admin/name/list' and a name such as 'admin-name-list'
    prefixes = []

    #: The current action
    action = None

    #: The current prefix
    prefix = None

    # The name of this class, lowercase (automatically determined)
    name = 'handler'

    #: The current user as determined by ``google.appengine.api.users.get_current_user()``.
    user = None

    def __init__(self, *args, **kwargs):
        """
        * Constructs the events map
        * Constructs all of the components
        * Determines the prefix and action
        * Populates default template arguments
        """
        super(Handler, self).__init__(*args, **kwargs)

        self.events = NamedEvents()
        self._init_route_members()
        self._init_template_vars()
        self._build_components()

    def _build_components(self):
        self._delegate_event('before_build_components', handler=self)
        if hasattr(self, 'components'):
            components = self.components
            self.components = Bunch()
            for cls in components:
                if hasattr(cls, 'name'):
                    name = cls.name
                else:
                    name = inflector.underscore(cls.__name__)
                self.components[name] = (cls(self))
        else:
            self.components = Bunch()
        self._delegate_event('after_build_components', handler=self)

    def _init_route_members(self):
        self.action = self.request.route.handler_method
        for prefix in self.prefixes:
            if self.action.startswith(prefix):
                self.prefix = prefix
                self.action = self.action.replace(self.prefix + '_', '')

    def _init_template_vars(self):
        self.name = inflector.underscore(self.__class__.__name__)
        self.proper_name = self.__class__.__name__
        self.template_vars = {}
        self.template_vars['handler'] = {
            'name': self.name,
            'uri': self.uri.__get__(self, Handler),
            'prefix': self.prefix,
            'action': self.action,
            'uri_exists': self.uri_exists.__get__(self, Handler),
            'on_uri': self.on_uri.__get__(self, Handler),
            'request': self.request,
            'self': self,
            'url_id_for': self.url_id_for.__get__(self, Handler),
            'url_key_for': self.url_id_for.__get__(self, Handler),
            'user': self.user
        }
        self._delegate_event('template_vars', handler=self)

    def _delegate_event(self, name, *args, **kwargs):
        """
        Calls an event locally, globally, and invokes callback methods
        """
        # callback events
        if name == 'before_dispatch':
            self.before_dispatch()
        elif name == 'after_dispatch':
            self.after_dispatch(kwargs['response'])
        elif name == 'before_render':
            self.before_render()
        elif name == 'after_render':
            self.after_render(kwargs['result'])

        self.events[name].fire(*args, **kwargs)  # Local events
        events.fire('handler_' + name, *args, **kwargs)  # Global Events

    @classmethod
    def build_routes(cls, router):
        """
        Called in the main app router to get all of this handler's routes.
        Override to add custom/additional routes.
        """

        # Route the rest methods
        router.add(routing.build_scaffold_routes_for_handler(cls))
        for prefix in cls.prefixes:
            router.add(routing.build_scaffold_routes_for_handler(cls, prefix))

        # Auto route the remaining methods
        for route in routing.build_routes_for_handler(cls):
            router.add(route)

        events.fire('handler_build_routes', cls=cls, router=router)

    def startup(self):
        """Called when a new request is received before authorization and dispatching."""
        pass

    def is_authorized(self):
        if self.prefix == 'admin' and not users.is_current_user_admin():
            return Response("You must be an administrator.", status="401 Unauthorized")
        if 'allowed_auth_domains' in app_config:
            if not users.get_current_user().email().split('@').pop() in app_config['allowed_auth_domains']:
                return Response("Your domain does not have access to this application.", status="401 Unauthorized")
        try:
            self._delegate_event('is_authorized', handler=self)
        except Exception, e:
            return Response(str(e), status='401 Unauthorized')
        return True

    def before_dispatch(self):
        """Called during dispatch before control is handed over to the action"""
        pass

    def after_dispatch(self, response):
        """Called during dispatch after control is handed back from the action"""
        pass

    def before_render(self):
        """Called during render_template before invoking the template engine"""
        pass

    def after_render(self, result):
        """Called during render_template after the template has been rendered by the template engine"""
        pass

    def dispatch(self):
        """
        Calls startup and then the handler method. Will also make sure that the user
        is an administrator is the current prefix is 'admin'.

        If self.auto_render is True, then we will try to automatically render the template
        at templates/{name}/{prefix}_{action}.{extension}. The automatic name can be overriden
        by setting self.template_name.

        If the handler method returns anything other than None, auto-rendering is skipped
        and the result (return value) is returned to the dispatcher.
        """

        self.user = users.get_current_user()
        self._init_route_members()
        self._init_template_vars()

        self.session_store = sessions.get_store(request=self.request)
        self.template_vars['handler']['session'] = self.session

        self._delegate_event('before_startup', handler=self)
        self.startup()
        self._delegate_event('after_startup', handler=self)

        auth_result = self.is_authorized()
        if auth_result != True:
            return auth_result

        try:
            self._delegate_event('before_dispatch', handler=self)

            response = super(Handler, self).dispatch()

            self._delegate_event('after_dispatch', response=response, handler=self)

            if self.auto_render and response == None and not self.response.body:
                response = self.render_template(self._get_template_name())

        finally:
            pass

        if isinstance(response, basestring):
            # Clear redirect
            if self.response.status_int in [300, 301, 302]:
                self.response.status = 200
                del self.response.headers['Location']

            if isinstance(response, unicode):
                self.response.charset = 'utf8'
                self.response.unicode_body = response
            else:
                self.response.body = response
        elif isinstance(response, tuple):
            self.response = Response(response)
        elif isinstance(response, int):
            self.response.status = response
        elif response == None:
            pass

        self._delegate_event('dispatch_complete', handler=self)

        self.session_store.save_sessions(self.response)
        return self.response

    @cached_property
    def session(self):
        """
        Session object backed by an encrypted cookie and memcache.
        """
        return self.session_store.get_session(backend='memcache')

    def json(self, data, *args, **kwargs):
        """Returns a json encoded string for the given object. Uses :mod:`ferris.core.json_util` so it is capable of handling Datastore types."""
        return json.dumps(data, cls=DatastoreEncoder, *args, **kwargs)

    def render_template(self, template):
        """
        Render a given template with :attr:`template_vars` as the context.

        This is called automatically during :meth:`dispatch` if :attr:`auto_render` is ``True`` and an action returns ``None``.
        """
        self._delegate_event('before_render', handler=self)

        result = templating.render_template(template, self.template_vars, theme=self.theme)

        self._delegate_event('after_render', handler=self, result=result)

        return result

    def _get_template_name(self):
        """
        Generates a list of template names.

        The template engine will try each template in the list until it finds one.

        For non-prefixed actions, the return value is simply: ``[ "[handler]/[action].[ext]" ]``.
        For prefixed actions, another entry is added to the list : ``[ "[handler]/[prefix_][action].[ext]" ]``. This means that actions that are prefixed can fallback to using the non-prefixed template.

        For example, the action ``Posts.json_list`` would try these templates::

            posts/json_list.html
            posts/list.html

        """
        if not self.template_name == None:
            return self.template_name

        templates = []

        if self.prefix:
            template = self.name + '/' + self.prefix + '_' + self.action + '.' + self.template_ext
            templates.append(template)

        # non-prefixed
        template = self.name + '/' + self.action + '.' + self.template_ext
        templates.append(template)

        self._delegate_event('template_names', handler=self, templates=templates)

        return templates

    def set(self, name=None, value=None, **kwargs):
        """ Set a variable in the template context. You can specify name and value or specify multiple values using kwargs. """
        if not name == None:
            self.template_vars[name] = value
        self.template_vars.update(kwargs)

    def get(self, name, default=None):
        """ Get a variable from the template context """
        return self.template_vars.get(name, default)

    def url_id_for(self, item):
        """
        Returns a properly formatted urlsafe version of an ``ndb.Key``.
        """
        return ':' + key_urlsafe_for(item)

    url_key_for = url_id_for

    def key_from_string(self, str, kind=None):
        """
        Returns an ``ndb.Key`` object from a properly formatted urlsafe version.
        """
        return key_from_string(str, kind)

    def process_form_data(self, form, obj=None):
        """
        Processes POST and JSON data and provides it to the given form.

        If obj is specified, that's used as the fallback data for the form is nothing was submitted.
        """
        self._delegate_event('before_process_form_data', handler=self, form=form)

        form.process(formdata=self.request.params, obj=obj, **form.data)

        if 'application/json' in self.request.content_type:
            try:
                data = json.loads(self.request.body)
                if '__class__' in data:
                    # This is a complex Json data object, treat it as such.
                    data = json.loads(self.request.body, cls=DatastoreDecoder)
                    form.process(obj=data, **form.data)
                else:
                    # This is a plain json object, load it in via multidict
                    # Do some special handling for list values in the dict.
                    if isinstance(data, dict):
                        new_data = MultiDict()
                        for key, value in data.iteritems():
                            if isinstance(value, list):
                                for v in value:
                                    new_data.add(key, v)
                            else:
                                new_data.add(key, value)
                        form.process(formdata=new_data, **form.data)
                    else:
                        raise Exception
            except Exception:
                logging.error('Request content-type is json, but I was unable to parse it!')
                logging.error(self.request.body)

        self._delegate_event('after_process_form_data', handler=self, form=form)
        return form


# Pre register some events
events.register([
    'handler_before_build_components',
    'handler_after_build_components',
    'handler_template_vars',
    'handler_build_routes',
    'handler_is_authorized',
    'handler_before_startup',
    'handler_after_startup',
    'handler_before_dispatch',
    'handler_after_dispatch',
    'handler_dispatch_complete',
    'handler_before_render',
    'handler_after_render',
    'handler_template_names',
    'handler_before_process_form_data',
    'handler_after_process_form_data',
])
