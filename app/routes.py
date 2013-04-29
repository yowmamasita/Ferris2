from ferris.core import routing, plugins

# Routes all App handlers
routing.auto_route()

# Default root route
from ferris.app import app as ferris_app
from webapp2 import Route
from ferris.controllers.root import Root
ferris_app.router.add(Route('/', Root, handler_method='root'))


# Plugins
plugins.enable('tiny_mce')
plugins.enable('settings')
plugins.enable('oauth_manager')
plugins.enable('template_tester')
