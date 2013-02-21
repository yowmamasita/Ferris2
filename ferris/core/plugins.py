import logging
import ferris
import os

_plugins = []


def has_plugin(name):
    """
    Checks to see if a particular plugin is enabled
    """
    return name in _plugins


def register_plugin(name):
    """
    Adds a plugin's template path to the templating engine
    """
    import template
    _plugins.append(name)
    path = os.path.normpath(os.path.join(
        os.path.dirname(ferris.__file__),
        '../plugins/%s/templates' % name))
    template.add_search_path(path)


def enable_plugin(name):
    """
    Routes all of the handlers inside of a plugin
    """
    from routing import route_all_handlers
    try:
        route_all_handlers(ferris.app.app.router, name)
    except ImportError, e:
        logging.error("Plugin %s does not exist, or contains a bad import: %s" % (name, e))
        raise


def list():
    return _plugins
