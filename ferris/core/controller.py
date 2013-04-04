import webapp2
import json
from settings import app_config
from webapp2 import Response, cached_property
from webapp2_extras import sessions
from google.appengine.api import users
from ferris.core import inflector
from ferris.core.ndb import key_urlsafe_for, key_from_string
from ferris.core.uri import Uri
from ferris.core import events
from ferris.core.json_util import DatastoreEncoder, DatastoreDecoder
from ferris.core.view import ViewContext, TemplateView
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


class Controller(webapp2.RequestHandler, Uri):
    """
    Handler allows grouping of common actions and provides them with
    automatic routing, reusable components, and automatic template
    discovery and rendering.
    """

    #: List of components.
    #: When declaring a handler, this must be a list of classes.
    #: When the handler is constructed, this will be transformed into a Bunch of instances.
    components = ()

    #: If set to true, the handler will attempt to render the template determined by :meth:`_get_template_name` if an action returns ``None``.
    auto_render = True

    # Prefixes are added in from of handlers (like admin_list) and will cause routing
    # to produce a url such as '/admin/name/list' and a name such as 'admin-name-list'
    prefixes = ()

    #: The current action
    action = None

    #: The current prefix
    prefix = None

    # The name of this class, lowercase (automatically determined)
    name = 'handler'

    #: The current user as determined by ``google.appengine.api.users.get_current_user()``.
    user = None

    #: View Context, all these variables will be passed to the view.
    context = None

    class Meta(object):
        View = TemplateView

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)

    def _build_components(self):
        self.events.before_build_components(handler=self)
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
        self.events.after_build_components(handler=self)

    def _init_route_members(self):
        self.action = self.request.route.handler_method
        for prefix in self.prefixes:
            if self.action.startswith(prefix):
                self.prefix = prefix
                self.action = self.action.replace(self.prefix + '_', '')

    def _init_meta(self):
        self.name = inflector.underscore(self.__class__.__name__)
        self.proper_name = self.__class__.__name__
        self.events = events.NamedBroadcastEvents(prefix='controller_')
        self.meta = self.Meta()
        self.context = ViewContext()
        self.meta.view = self.meta.View(self, self.context)

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
            self.events.is_authorized(handler=self)
        except Exception, e:
            return Response(str(e), status='401 Unauthorized')
        return True

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
        self._init_meta()

        self.session_store = sessions.get_store(request=self.request)
        self.context.set_dotted('handler.session', self.session)

        self.events.before_startup(handler=self)
        self.startup()
        self.events.after_startup(handler=self)

        auth_result = self.is_authorized()
        if auth_result is not True:
            return auth_result

        try:
            self.events.before_dispatch(handler=self)

            response = super(Controller, self).dispatch()

            self.events.after_dispatch(response=response, handler=self)

            if self.auto_render and response is None and not self.response.body:
                response = self.meta.view.render()

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
        elif response is None:
            pass

        self.events.dispatch_complete(handler=self)

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
        self.events.before_process_form_data(handler=self, form=form)

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

        self.events.after_process_form_data(handler=self, form=form)
        return form
