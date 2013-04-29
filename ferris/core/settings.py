from webapp2 import get_request
from . import events

_defaults = {}


class ConfigurationError(Exception):
    pass


def defaults(dict):
    """
    Adds a set of default values to the settings registry. These can and will be updated
    by any settings modules in effect, such as the Settings Manager
    """
    _defaults.update(dict)


def settings():
    """
    Returns the entire settings registry
    """

    # Check local request storage for the completed settings registry
    try:
        request = get_request()
    except AssertionError:
        request = None

    if request and 'ferris-settings' in request.registry:
        return request.registry['ferris-settings']

    # If it's not there, do the normal thing

    settings = {}
    settings.update(_defaults)
    events.fire('build_settings', settings=settings)

    # Try to store it back in the request
    if request:
        request.registry['ferris-settings'] = settings

    return settings


def get(key):
    """
    Returns the setting at key, if available, raises an ConfigurationError otherwise
    """
    _settings = settings()
    if not key in _settings:
        raise ConfigurationError("Missing setting %s" % key)
    return _settings[key]
