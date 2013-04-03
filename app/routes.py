from ferris.core.routing import auto_route
from ferris.core.plugins import enable_plugin
from ferris.app import app as ferris_app

# Routes all App handlers
auto_route()

# Default root route
from webapp2 import Route
from ferris.handlers.root import Root
ferris_app.router.add(Route('/', Root, handler_method='root'))

# Plugins
enable_plugin('tiny_mce')
enable_plugin('oauth_manager')
#enable_plugin('template_tester')
