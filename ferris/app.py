"""
The App module provides the main WSGI app for ferris.
See /settings.py to configure the app. See app/routes.py
to configure routing
"""

from ferris.core.wsgi import WSGIApp
from ferris.core import settings

# Entry point
app = WSGIApp(debug=True, config=settings.get('app_config'))

from ferris.controllers import errors
app.error_handlers[400] = errors.handle_400
app.error_handlers[401] = errors.handle_401
app.error_handlers[403] = errors.handle_403
app.error_handlers[404] = errors.handle_404
app.error_handlers[500] = errors.handle_500
