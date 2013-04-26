"""
Ferris' WSGI customizations.
"""

import webapp2
import inspect
import re
import urllib


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

class DefaultArgsRoute(webapp2.Route):
  """
  webapp2.Route subclass that handles default arguments
  """
  def __init__(self, template, handler=None, name=None, defaults=None,
                 build_only=False, handler_method=None, methods=None,
                 schemes=None):

    super(DefaultArgsRoute, self).__init__(template, handler=handler, name=name, 
                 defaults=defaults, build_only=build_only, handler_method=handler_method,
                 methods=methods, schemes=schemes)

  def _build(self, args, kwargs):
        """Returns the URI path for this route.

        :returns:
            A tuple ``(path, kwargs)`` with the built URI path and extra
            keywords to be used as URI query arguments.
        """
        # Access self.regex just to set the lazy properties.
        regex = self.regex
        variables = self.variables
        if self.args_count:
            for index, value in enumerate(args):
                key = '__%d__' % index
                if key in variables:
                    kwargs[key] = value

        method = getattr(self.handler, self.handler_method, None)
        if method:
          default_args = getattr(inspect.getargspec(method), 'defaults', None) or []
          arg_names = getattr(inspect.getargspec(method), 'args', None) or []
          optional_args = arg_names[len(arg_names)-len(default_args):]
        else:
          optional_args = []

        skipped_args = 0
        values = {}
        for name, regex in variables.iteritems():
            value = kwargs.pop(name, self.defaults.get(name))
            if value is None and name not in optional_args:
                raise KeyError('Missing argument "%s" to build URI.' % \
                    name.strip('_'))

            elif value is None and name in optional_args:
              skipped_args += 1
              continue

            if not isinstance(value, basestring):
                value = str(value)

            if not regex.match(value):
                raise ValueError('URI buiding error: Value "%s" is not '
                    'supported for argument "%s".' % (value, name.strip('_')))

            values[name] = value

        if optional_args:
          reverse_template = self.reverse_template.split('/')
          index = len(reverse_template)-skipped_args
          reverse_template = '/'.join(reverse_template[:index])
        else:
          reverse_template = self.reverse_template

        return (reverse_template % values, kwargs)

  def match(self, request):
    regex_list = [self.regex]
    method = getattr(self.handler, self.handler_method, None)

    if method:
      default_args = getattr(inspect.getargspec(method), 'defaults', None) or []

      if len(default_args) > 0:
        split = self.regex.pattern.split('\/')
        for i in xrange(1, len(default_args)+1):
          pattern = '\/'.join(split[:-i]) + '$'
          regex_list.append(re.compile(pattern, self.regex.flags))

    for regex in regex_list:
      match = regex.match(urllib.unquote(request.path))
      if match:
        break

    if not match or self.schemes and request.scheme not in self.schemes:
      return None

    if self.methods and request.method not in self.methods:
      # This will be caught by the router, so routes with different
      # methods can be tried.
      raise webapp2.exc.HTTPMethodNotAllowed()

    args, kwargs = webapp2._get_route_variables(match, self.defaults.copy())
    return self, args, kwargs
