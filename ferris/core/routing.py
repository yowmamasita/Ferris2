"""
Ferris' routing utilities
"""

import os
import inspect
import webapp2
import logging
import ferris
from ferris.core import inflector
from webapp2 import Route
from webapp2_extras import routes
from ferris.core.wsgi import DefaultArgsRoute

# Used to detect :key or 123 in urls
id_regex = "\:?(\d+|(?<=\:)[A-Za-z0-9\-\_]+)"


def auto_route(app_router=None, plugin=None):
    if not app_router:
        app_router = ferris.app.app.router
    route_all_handlers(app_router, plugin=None)


def route_all_handlers(app_router, plugin=None):
    """
    Called in app.routes to automatically route all handlers in the app/handlers
    folder
    """
    base_directory = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..', '..'))
    directory = os.path.join('app', 'handlers')
    if plugin:
        directory = os.path.join('plugins', plugin, 'handlers')

        # import the root plugin module first, this enables all templates and listeners
        plugin_module = __import__('plugins.%s' % plugin, fromlist=['*'])
        (plugin_module)

    directory = os.path.join(base_directory, directory)

    # Walk through the handlers, if the directory for handlers exists
    if not os.path.exists(directory):
        return

    for file in os.listdir(directory):
        if file.endswith(".py") and file != '__init__.py':
            try:
                name = file.split('.')[0]
                root_module = 'app.handlers'
                if plugin:
                    root_module = 'plugins.%s.handlers' % plugin
                module = __import__('%s.%s' % (root_module, name), fromlist=['*'])
                cls = getattr(module, inflector.camelize(name))
                cls.build_routes(app_router)
            except AttributeError, e:
                logging.error('Thought %s was a controller, but was wrong (or ran into some weird error): %s' % (file, e))
                raise


def route_name_exists(name, *args, **kwargs):
    """
    Checks if a particlar named route (i.e. 'entries-list') exists.
    """
    route = webapp2.get_app().router.build_routes.get(name)
    if route == None:
        return False
    return True


def current_route_name():
    """
    Gets the name (i.e. 'entries-list') from the router.
    """
    name = webapp2.get_app().request.route.name
    return name


def canonical_parts_from_method(method):
    """
    Returns the canonical parts (prefix, handler, action, named arguments)
    from a handler's method
    """
    method_name = method.__name__
    method_class = method.im_class
    method_class_name = inflector.underscore(method_class.__name__)
    prefix = None

    for tprefix in method_class.prefixes:
        if method_name.startswith(tprefix + '_'):
            prefix = tprefix
            method_name = method_name.replace(prefix + '_', '')

    args = inspect.getargspec(method).args[1:]

    return {
        'prefix': prefix,
        'handler': method_class_name,
        'action': method_name,
        'args': args
    }


def path_from_canonical_parts(prefix, handler, action, args):
    """
    Returns a route ('/admin/users/edit/3') from canonical parts
    ('admin', 'users', 'edit', [id])
    """
    args_parts = ['<' + x + '>' for x in args]
    route_parts = [prefix, handler, action] + args_parts
    route_parts = [x for x in route_parts if x]
    route_path = '/' + '/'.join(route_parts)

    return route_path


def name_from_canonical_parts(prefix, handler, action, args=None):
    """
    Returns the route's name ('admin-users-edit') from the canonical
    parts ('admin','users','edit')
    """
    route_parts = [prefix, handler, action]
    route_parts = [x for x in route_parts if x]
    route_name = '-'.join(route_parts)

    return route_name


def build_routes_for_handler(handlercls):
    """
    Returns list of routes for a particular handler, to enable
    methods to be routed, add the ferris.core.handler.auto_route
    decorator, or simply set the 'route' attr of the function to
    True.

    def some_method(self, arg1, arg2, arg3)

    becomes

    /handler/some_method/<arg1>/<arg2>/<arg3>
    """
    routes_list = []
    methods = inspect.getmembers(handlercls, predicate=inspect.ismethod)
    methods = [x[1] for x in methods if hasattr(x[1], 'route')]

    for method in methods:
        parts = canonical_parts_from_method(method)
        route_path = path_from_canonical_parts(**parts)
        route_name = name_from_canonical_parts(**parts)

        kwargs = dict(
            template=route_path,
            handler=handlercls,
            name=route_name,
            handler_method=method.__name__
        )
        method_args = method.route
        if isinstance(method_args, tuple):
            kwargs.update(method_args[1])

        route_cls = (DefaultArgsRoute
                    if not isinstance(method_args, tuple) and
                    getattr(inspect.getargspec(method), 'defaults', None)
                    else Route)

        routes_list.append(route_cls(**kwargs))

    return routes_list


def build_scaffold_routes_for_handler(handlercls, prefix_name=None):
    """
    Automatically sets up a restful routing interface for a handler
    that has any of the rest methods (list, view, add, edit, delete)
    either without or with a prefix. Note that these aren't true rest
    routes, some more wizardry has to be done for that.

    The routes generated are:

    handler-list : /handler
    handler-view : /handler/:id
    handler-add  : /handler/add
    handler-edit : /handler/:id/edit
    handler-delete : /handler/:id/delete

    prefixes just add to the beginning of the name and uri, for example:

    admin-handler-edit: /admin/handler/:id/edit
    """
    if(hasattr(handlercls, 'name')):
        name = handlercls.name
    name = inflector.underscore(handlercls.__name__)
    prefix_string = ''

    if not prefix_name == None:
        prefix_string = prefix_name + '_'

    top = []
    path = []
    id = []

    # GET /handler -> Handler::list
    if hasattr(handlercls, prefix_string + 'list'):
        top.append(Route('/' + name, handlercls, 'list', handler_method=prefix_string + 'list', methods=['HEAD', 'GET']))

    # GET /handler/:urlsafe -> Handler::view
    if hasattr(handlercls, prefix_string + 'view'):
        path.append(Route('/<id:%s>' % id_regex, handlercls, 'view', handler_method=prefix_string + 'view', methods=['HEAD', 'GET']))

    # GET/POST /handler/add -> Handler::add
    # POST /handler -> Handler::add
    if hasattr(handlercls, prefix_string + 'add'):
        path.append(Route('/add', handlercls, 'add', handler_method=prefix_string + 'add', methods=['GET', 'POST']))
        top.append(Route('/' + name, handlercls, 'add-rest', handler_method=prefix_string + 'add', methods=['POST']))

    # GET/POST /handler/:urlsafe/edit -> Handler::edit
    # PUT /handler/:urlsafe -> Handler::edit
    if hasattr(handlercls, prefix_string + 'edit'):
        id.append(Route('/edit', handlercls, 'edit', handler_method=prefix_string + 'edit', methods=['GET', 'POST']))
        path.append(Route('/<id:%s>' % id_regex, handlercls, 'edit-rest', handler_method=prefix_string + 'edit', methods=['PUT', 'POST']))

    # GET /handler/:urlsafe/delete -> Handler::delete
    # DELETE /handler/:urlsafe -> Handler::d
    if hasattr(handlercls, prefix_string + 'delete'):
        id.append(Route('/delete', handlercls, 'delete', handler_method=prefix_string + 'delete'))
        path.append(Route('/<id:%s>' % id_regex, handlercls, 'delete-rest', handler_method=prefix_string + 'delete', methods=["DELETE"]))

    top_route = routes.NamePrefixRoute(name + '-', top + [
        routes.PathPrefixRoute('/' + name, path + [
            routes.PathPrefixRoute('/<id:%s>' % id_regex, id)
        ])
    ])

    if not prefix_name == None:
        prefix_route = routes.NamePrefixRoute(prefix_name + '-', [
            routes.PathPrefixRoute('/' + prefix_name, [top_route])
        ])
        return prefix_route

    return top_route
