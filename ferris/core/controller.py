import webapp2
from webapp2 import cached_property
from webapp2_extras import sessions
from google.appengine.api import users
from ferris.core import inflector, auth
from ferris.core.ndb import encode_key, decode_key
from ferris.core.uri import Uri
from ferris.core import events
from ferris.core.json_util import parse as json_parse, stringify as json_stringify
from ferris.core.view import View, TemplateView
from ferris.core.request_parsers import RequestParser
from ferris.core.response_handlers import ResponseHandler
import ferris.core.routing as routing
from bunch import Bunch


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


def add_authorizations(*args):
    """
    Adds additional authorization chains to a particular action. These are executed after the
    chains set in Controller.Meta.
    """
    def inner(f):
        setattr(f, 'authorizations', args)
        return f
    return inner


class Controller(webapp2.RequestHandler, Uri):
    """
    Controllers allows grouping of common actions and provides them with
    automatic routing, reusable components, and automatic template
    discovery and rendering.
    """

    _controllers = []

    class __metaclass__(type):
        def __new__(meta, name, bases, dict):
            cls = type.__new__(meta, name, bases, dict)
            if name != 'Controller':
                if not cls in Controller._controllers:
                    Controller._controllers.append(cls)
                if not issubclass(cls.Meta, Controller.Meta):
                    cls.Meta = type('Meta', (cls.Meta, Controller.Meta), {})
            return cls

    #: If set to true, the controller will attempt to render the template determined by :meth:`_get_template_name` if an action returns ``None``.
    auto_render = True

    # The name of this class, lowercase (automatically determined)
    name = 'controller'

    #: The current user as determined by ``google.appengine.api.users.get_current_user()``.
    user = None

    #: View Context, all these variables will be passed to the view.
    context = property(lambda self: self.meta.view.context)

    class Meta(object):
        #: List of components.
        #: When declaring a controller, this must be a list of classes.
        #: When the controller is constructed, this will be transformed into a Bunch of instances.
        components = tuple()

        #: Prefixes are added in from of controller (like admin_list) and will cause routing
        #: to produce a url such as '/admin/name/list' and a name such as 'admin-name-list'
        prefixes = tuple()

        #: Authorizations control access to the controller. Each authorization is a callable.
        #: Authorizations are called in order and all must return True for the request to be
        #: processed. If they return False or a tuple like (False, 'message'), the request will
        #: be rejected.
        #: You should **always** have auth.require_admin_for_prefix(prefix=('admin',)) in your
        #: authorization chain.
        authorizations = (auth.require_admin_for_prefix(prefix=('admin',)),)

        #: Which view class to use by default.
        View = TemplateView

        #: Which requestparser class to use by default
        Parser = 'Form'

        def __init__(self, controller):
            self._controller = controller
            self.view = None
            self.change_view(self.View)

        def change_view(self, view, persist_context=True):
            context = self.view.context if self.view else None
            self.View = view if not isinstance(view, basestring) else View.factory(view)
            self.view = self.View(self._controller, context)

    class Util(object):
        def __init__(self, controller):
            self._controller = controller

        decode_key = staticmethod(decode_key)
        encode_key = staticmethod(encode_key)
        parse_json = staticmethod(json_parse)
        stringify_json = staticmethod(json_stringify)

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)

        self.name = inflector.underscore(self.__class__.__name__)
        self.proper_name = self.__class__.__name__
        self.util = self.Util(self)

    def _build_components(self):
        self.events.before_build_components(controller=self)
        if hasattr(self.Meta, 'components'):
            component_classes = self.Meta.components
            self.components = Bunch()
            for cls in component_classes:
                if hasattr(cls, 'name'):
                    name = cls.name
                else:
                    name = inflector.underscore(cls.__name__)
                self.components[name] = (cls(self))
        else:
            self.components = Bunch()
        self.events.after_build_components(controller=self)

    def _init_route(self):
        action = self.request.route.handler_method
        prefix = None
        for possible_prefix in self.Meta.prefixes:
            if action.startswith(possible_prefix):
                prefix = possible_prefix
                action = action.replace(prefix + '_', '')
                break

        self.route = Bunch(
            prefix=prefix,
            controller=self.name,
            action=action,
            name=self.request.route.name)

    def _init_meta(self):
        self.user = users.get_current_user()
        self._init_route()

        self.events = events.NamedBroadcastEvents(prefix='controller_')
        self.meta = self.Meta(self)
        self._build_components()

    @classmethod
    def _build_routes(cls, router):
        """
        Called in the main app router to get all of this controller's routes.
        Override to add custom/additional routes.
        """

        # Route the rest methods
        router.add(routing.build_scaffold_routes_for_controller(cls))
        for prefix in cls.Meta.prefixes:
            router.add(routing.build_scaffold_routes_for_controller(cls, prefix))

        # Auto route the remaining methods
        for route in routing.build_routes_for_controller(cls):
            router.add(route)

        events.fire('controller_build_routes', cls=cls, router=router)

    def startup(self):
        """Called when a new request is received before authorization and dispatching."""
        pass

    def _is_authorized(self):
        authorizations = self.meta.authorizations

        #per-handler authorizations
        method = getattr(self, self.request.route.handler_method)
        if hasattr(method, 'authorizations'):
            authorizations = authorizations + method.authorizations

        auth_result = True

        for chain in authorizations:
            auth_result = chain(self)
            if auth_result is not True:
                break

        if auth_result is not True:
            message = u"Authorization chain rejected request"
            if isinstance(auth_result, tuple):
                message = auth_result[1]
            self.abort(403, message)

    def _clear_redirect(self):
        if self.response.status_int in [300, 301, 302]:
            self.response.status = 200
            del self.response.headers['Location']

    def dispatch(self):
        """
        Calls startup and then the controller method. Will also make sure that the user
        is an administrator is the current prefix is 'admin'.

        If self.auto_render is True, then we will try to automatically render the template
        at templates/{name}/{prefix}_{action}.{extension}. The automatic name can be overriden
        by setting self.template_name.

        If the controller method returns anything other than None, auto-rendering is skipped
        and the result (return value) is returned to the dispatcher.
        """

        # Setup everything, the session, etc.
        self._init_meta()

        self.session_store = sessions.get_store(request=self.request)
        self.context.set_dotted('this.session', self.session)

        self.events.before_startup(controller=self)
        self.startup()
        self.events.after_startup(controller=self)

        # Authorization
        self._is_authorized()

        # Dispatch to the method
        self.events.before_dispatch(controller=self)
        result = super(Controller, self).dispatch()
        self.events.after_dispatch(response=result, controller=self)

        # Return value handlers.
        # Response has highest precendence, the view class has lowest.
        response_handler = ResponseHandler.factory(type(result))

        if response_handler:
            self.response = response_handler(self, result)

        # View rendering works similar to the string mode above.
        elif self.meta.view.auto_render:
            self._clear_redirect()
            self.response = self.meta.view.render()

        else:
            self.abort(500, 'Nothing was able to handle the response %s (%s)' % (result, type(result)))

        self.events.dispatch_complete(controller=self)

        self.session_store.save_sessions(self.response)
        return self.response

    @cached_property
    def session(self):
        """
        Session object backed by an encrypted cookie and memcache.
        """
        return self.session_store.get_session(backend='memcache')

    def parse_request(self, container=None, fallback=None, parser=None):
        """
        Parses request data (like GET, POST, JSON, XML) into a container (like a Form or Message)
        instance using a RequestParser. By default, it assumes you want to process GET/POST data
        into a Form instance, for that simple case you can use::

            data = self.parse_request()

        provided you've set the From attribute of the Meta class.
        """
        parser_name = parser if parser else self.meta.Parser
        parser = RequestParser.factory(parser_name)

        if not container:
            container_name = parser.container_name
            if not hasattr(self.meta, container_name):
                raise AttributeError('Meta has no %s class, can not parse request' % container_name)
            container = getattr(self.meta, container_name)

        return parser.process(self.request, container, fallback)
