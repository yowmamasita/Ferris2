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


def auto_route(app_router=None, plugin=None):
    if not app_router:
        app_router = ferris.app.app.router
    route_all_controllers(app_router, plugin=None)


def route_all_controllers(app_router, plugin=None):
    """
    Called in app.routes to automatically route all controllers in the app/controllers
    folder
    """
    base_directory = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..', '..'))
    directory = os.path.join('app', 'controllers')
    if plugin:
        directory = os.path.join('plugins', plugin, 'controllers')

        # import the root plugin module first, this enables all templates and listeners
        plugin_module = __import__('plugins.%s' % plugin, fromlist=['*'])
        (plugin_module)

    directory = os.path.join(base_directory, directory)

    # Walk through the controllers, if the directory for controllers exists
    if not os.path.exists(directory):
        return

    for file in os.listdir(directory):
        if file.endswith(".py") and file != '__init__.py':
            try:
                name = file.split('.')[0]
                root_module = 'app.controllers'
                if plugin:
                    root_module = 'plugins.%s.controllers' % plugin
                module = __import__('%s.%s' % (root_module, name), fromlist=['*'])
                cls = getattr(module, inflector.camelize(name))

                if hasattr(cls, '_build_routes'):
                    cls._build_routes(app_router)
                else:
                    cls.build_routes(app_router)
            except AttributeError, e:
                logging.error('Thought %s was a controller, but was wrong (or ran into some weird error): %s' % (file, e))
                raise


def route_name_exists(name, *args, **kwargs):
    """
    Checks if a particlar named route (i.e. 'entries-list') exists.
    """
    route = webapp2.get_app().router.build_routes.get(name)
    return True if route else False


def current_route_name():
    """
    Gets the name (i.e. 'entries-list') from the router.
    """
    name = webapp2.get_app().request.route.name
    return name


def canonical_parts_from_method(method):
    """
    Returns the canonical parts (prefix, controller, action, named arguments)
    from a controller's method
    """
    method_name = method.__name__
    method_class = method.im_class
    method_class_name = inflector.underscore(method_class.__name__)
    prefix = None

    if hasattr(method_class, 'Meta'):
        prefixes = method_class.Meta.prefixes
    else:
        prefixes = method_class.prefixes

    for tprefix in prefixes:
        if method_name.startswith(tprefix + '_'):
            prefix = tprefix
            method_name = method_name.replace(prefix + '_', '')

    args = inspect.getargspec(method).args[1:]

    return {
        'prefix': prefix,
        'controller': method_class_name,
        'action': method_name,
        'args': args
    }


def path_from_canonical_parts(prefix, controller, action, args):
    """
    Returns a route ('/admin/users/edit/3') from canonical parts
    ('admin', 'users', 'edit', [id])
    """
    args_parts = ['<' + x + '>' for x in args]
    route_parts = [prefix, controller, action] + args_parts
    route_parts = [x for x in route_parts if x]
    route_path = '/' + '/'.join(route_parts)

    return route_path


def name_from_canonical_parts(prefix, controller, action, args=None):
    """
    Returns the route's name ('admin-users-edit') from the canonical
    parts ('admin','users','edit')
    """
    route_parts = [prefix, controller, action]
    route_parts = [x for x in route_parts if x]
    route_name = '-'.join(route_parts)

    return route_name


def build_routes_for_controller(controllercls):
    """
    Returns list of routes for a particular controller, to enable
    methods to be routed, add the ferris.core.controller.auto_route
    decorator, or simply set the 'route' attr of the function to
    True.

    def some_method(self, arg1, arg2, arg3)

    becomes

    /controller/some_method/<arg1>/<arg2>/<arg3>
    """
    routes_list = []
    methods = inspect.getmembers(controllercls, predicate=inspect.ismethod)
    methods = [x[1] for x in methods if hasattr(x[1], 'route')]

    for method in methods:
        parts = canonical_parts_from_method(method)
        route_path = path_from_canonical_parts(**parts)
        route_name = name_from_canonical_parts(**parts)

        kwargs = dict(
            template=route_path,
            handler=controllercls,
            name=route_name,
            handler_method=method.__name__
        )
        method_args = method.route
        if isinstance(method_args, tuple):
            kwargs.update(method_args[1])

        routes_list.append(Route(**kwargs))

    return routes_list


def build_scaffold_routes_for_controller(controllercls, prefix_name=None):
    """
    Automatically sets up a restful routing interface for a controller
    that has any of the rest methods (list, view, add, edit, delete)
    either without or with a prefix. Note that these aren't true rest
    routes, some more wizardry has to be done for that.

    The routes generated are:

    controller-list : /controller
    controller-view : /controller/:id
    controller-add  : /controller/add
    controller-edit : /controller/:id/edit
    controller-delete : /controller/:id/delete

    prefixes just add to the beginning of the name and uri, for example:

    admin-controller-edit: /admin/controller/:id/edit
    """
    if(hasattr(controllercls, 'name')):
        name = controllercls.name
    name = inflector.underscore(controllercls.__name__)
    prefix_string = ''

    if prefix_name:
        prefix_string = prefix_name + '_'

    top = []
    path = []
    id = []

    # GET /controller -> controller::list
    if hasattr(controllercls, prefix_string + 'list'):
        top.append(Route('/' + name, controllercls, 'list', handler_method=prefix_string + 'list', methods=['HEAD', 'GET']))

    # GET /controller/:urlsafe -> controller::view
    if hasattr(controllercls, prefix_string + 'view'):
        path.append(Route('/:<key>', controllercls, 'view', handler_method=prefix_string + 'view', methods=['HEAD', 'GET']))

    # GET/POST /controller/add -> controller::add
    # POST /controller -> controller::add
    if hasattr(controllercls, prefix_string + 'add'):
        path.append(Route('/add', controllercls, 'add', handler_method=prefix_string + 'add', methods=['GET', 'POST']))
        top.append(Route('/' + name, controllercls, 'add-rest', handler_method=prefix_string + 'add', methods=['POST']))

    # GET/POST /controller/:urlsafe/edit -> controller::edit
    # PUT /controller/:urlsafe -> controller::edit
    if hasattr(controllercls, prefix_string + 'edit'):
        id.append(Route('/edit', controllercls, 'edit', handler_method=prefix_string + 'edit', methods=['GET', 'POST']))
        path.append(Route('/:<key>', controllercls, 'edit-rest', handler_method=prefix_string + 'edit', methods=['PUT', 'POST']))

    # GET /controller/:urlsafe/delete -> controller::delete
    # DELETE /controller/:urlsafe -> controller::d
    if hasattr(controllercls, prefix_string + 'delete'):
        id.append(Route('/delete', controllercls, 'delete', handler_method=prefix_string + 'delete'))
        path.append(Route('/:<key>', controllercls, 'delete-rest', handler_method=prefix_string + 'delete', methods=["DELETE"]))

    top_route = routes.NamePrefixRoute(name + '-', top + [
        routes.PathPrefixRoute('/' + name, path + [
            routes.PathPrefixRoute('/:<key>', id)
        ])
    ])

    if prefix_name:
        prefix_route = routes.NamePrefixRoute(prefix_name + '-', [
            routes.PathPrefixRoute('/' + prefix_name, [top_route])
        ])
        return prefix_route

    return top_route
