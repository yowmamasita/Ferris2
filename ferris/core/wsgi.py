"""
Ferris' WSGI customizations.
"""

import webapp2


class WSGIApp(webapp2.WSGIApplication):
    """
    Custom dispatcher that allows us to return strings for basic content,
    integers for response codes, or a tuple to initialize a response object
    """
    def __init__(self, *args, **kwargs):
        super(WSGIApp, self).__init__(*args, **kwargs)
        self.router.set_dispatcher(self.__class__.custom_dispatcher)

    @staticmethod
    def custom_dispatcher(router, request, response):
        rv = router.default_dispatcher(request, response)
        if isinstance(rv, basestring):
            rv = webapp2.Response(rv)
        elif isinstance(rv, tuple):
            rv = webapp2.Response(*rv)
        elif isinstance(rv, int):
            response.set_status(rv)
            rv = response

        return rv

    def route(self, *args, **kwargs):
        ''' Easy decorator for routing a function '''
        def wrapper(func):
            self.router.add(webapp2.Route(handler=func, *args, **kwargs))
            return func

        return wrapper
