from ferris.core import inflector


class Scaffolding(object):
    """
    Scaffolding Component
    """

    def __init__(self, Handler):
        self.handler = Handler
        self._init_meta()

    def _init_meta(self):
        """
        Constructs the handler's scaffold property from the handler's Scaffold class.
        If the handler doens't have a scaffold, uses the automatic one.
        """
        if not hasattr(self.handler, 'Scaffold'):
            setattr(self.handler, 'Scaffold', Scaffold)

        if not issubclass(self.handler.Scaffold, Scaffold):
            self.handler.Scaffold = type('Scaffold', (self.handler.Scaffold, Scaffold), {})

        setattr(self.handler, 'scaffold', self.handler.Scaffold(self.handler))


class Scaffold(object):
    """
    Scaffold Meta Object Base Class
    """
    def __init__(self, handler):
        if not hasattr(self, 'plural'):
            self.plural = inflector.pluralize(handler.name)


def list(handler):
    handler.context.set(**{
        handler.scaffold.plural: handler.meta.Model.query()})
