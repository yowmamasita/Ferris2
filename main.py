import fix_imports

# Import the application
import ferris
import ferris.app
import ferris.routes
import app.routes
import app.listeners

app = ferris.app.app  # the app object in the app package.

#from google.appengine.ext.appstats import recording
#app = recording.appstats_wsgi_middleware(app)
