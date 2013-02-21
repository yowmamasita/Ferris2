"""
The App module provides the main WSGI app for ferris.
See /settings.py to configure the app. See app/routes.py
to configure routing
"""

from ferris.core.wsgi import WSGIApp
from settings import app_config

# Entry point
app = WSGIApp(debug=True, config=app_config)
