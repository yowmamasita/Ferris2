from webapp2 import Route
from ferris.app import app as ferris_app

from ferris.handlers.root import Root
from ferris.handlers.oauth import Oauth

ferris_app.router.add(Route('/admin', Root, handler_method='admin'))
Oauth.build_routes(ferris_app.router)
