import fix_imports

# Import the application
import settings
import ferris
import ferris.app
import ferris.deferred_app
import ferris.routes
import app.routes
import app.listeners

main_app = ferris.app.app  # Main application
deferred_app = ferris.deferred_app.app  # Deferred application

# from google.appengine.ext.appstats import recording
# app = recording.appstats_wsgi_middleware(app)
