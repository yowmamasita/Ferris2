"""
Provides automatic registration of admin controllers to the admin nav bar
"""

import webapp2
from ferris.core import events
from ferris.core import template
from ferris.core import inflector

admin_handlers = []


def add_handler(handler_cls):
    """
    Adds a handler to the list of handlers to be included in the admin list.
    This is done automatically by Handler if it has the admin prefix
    """
    admin_handlers.append(handler_cls)


@events.on('before_template_render')
def render_template_listener(name, context, env):
    admin_links = {}
    for x in admin_handlers:
        try:
            admin_links[x.__name__] = webapp2.uri_for('admin-' + inflector.underscore(x.__name__) + '-list')
        except:
            pass

    context.update({
        'autoadmin': {
            'links': admin_links
        }
    })
