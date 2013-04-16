from webapp2 import Route
from ferris.app import app as ferris_app

from ferris.controllers.root import Root
from ferris.controllers.oauth import Oauth

ferris_app.router.add(Route('/admin', Root, handler_method='admin'))
Oauth._build_routes(ferris_app.router)
