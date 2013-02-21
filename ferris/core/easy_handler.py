from ferris.core.handler import *


class EasyHandler(Handler):
    """
    a quick way to get up and running with a CRUD scaffold
    quickly. Provides admin list, view, add, edit, and delete as well as normal
    list and view. Subclasses need to be scaffolded and must specify a model.

    Example::

        @scaffold
        class Locations(EasyHandler):
            Model = Location

    """
    prefixes = ['admin']

    def __init__(self, *args, **kwargs):
        super(EasyHandler, self).__init__(*args, **kwargs)
        if not hasattr(self, 'scaffold'):
            raise RuntimeError("EasyHandler %s has not been decorated with @scaffold" % self.__class__.__name__)

    def startup(self):
        pass

    @scaffold
    def list(self):
        pass

    @scaffold
    def view(self, id):
        pass

    @scaffold
    def admin_view(self, id):
        pass

    @scaffold
    def admin_list(self):
        pass

    @scaffold
    def admin_add(self):
        pass

    @scaffold
    def admin_edit(self, id):
        pass

    @scaffold
    def admin_delete(self, id):
        pass
