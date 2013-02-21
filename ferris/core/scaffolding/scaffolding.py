from decorator import decorator
from ferris.core import inflector
from ferris.core import autoadmin
from google.appengine.ext import db
from ferris.core.forms import model_form
import inspect
from ferris.core.bunch import Bunch
from .handler import Handler as ScaffoldHandler
from .mixin import Mixin as ScaffoldMixin
from .wrap import Wrap as ScaffoldWrap


def scaffold(cls_or_method, *args, **kwargs):
    """
    Main scaffolding method. Passing a class into this function will inject the class with
    everything needed to easily do CRUD operations.

    Passing a method into this function will scaffold the method with the corresponding of
    the methods in :attr:`Scaffolding.Handlers` class.
    """
    if inspect.isclass(cls_or_method):
        Scaffolding.inject(cls_or_method, *args, **kwargs)
        return cls_or_method
    elif inspect.isfunction(cls_or_method):
        return Scaffolding.wrap_handler_method(cls_or_method, *args, **kwargs)


class Scaffolding(object):
    """
    Class that adds utlities to assist with basic CRUD handlers
    """

    Handler = ScaffoldHandler  # Reference handler for scaffold methods.
    Mixin = ScaffoldMixin  # Reference properties for scaffolded handlers.
    Wrap = ScaffoldWrap  # Wrapper functions.

    @classmethod
    def inject(s, cls):
        """
        Adds properties and wraps a few methods in a handler
        to allow easy CRUD stuff
        """
        s.add_properties(cls)
        s.wrap_class_functions(cls)

        if 'admin' in cls.prefixes and not hasattr(cls, 'no_auto_admin') and hasattr(cls, 'admin_list'):
            autoadmin.add_handler(cls)

        return cls

    @classmethod
    def wrap_handler_method(s, f):
        """
        Scaffolds a handler function (like list or admin_list) with the corresponding
        function in Scaffolding.Handlers.
        """
        def wrapper(self, *args, **kwargs):
            if not hasattr(self.scaffold, self.action):
                raise Exception('Unable to scaffold %s for action %s' % (f.__name__, self.action))
            result = getattr(self.scaffold, self.action)(self, *args, **kwargs)
            other_result = f(self, *args, **kwargs)
            if not other_result == None:
                return other_result
            return result
        return wrapper

    @classmethod
    def add_properties(s, cls):
        if not s.Mixin in cls.__bases__:
            cls.__bases__ += (s.Mixin,)

        if not hasattr(cls, 'Model'):
            import_form_base = '.'.join(cls.__module__.split('.')[:-2])
            # Attempt to import the model automatically
            model_name = inflector.singularize(cls.__name__)
            try:
                module = __import__('%s.models.%s' % (import_form_base, inflector.underscore(model_name)), fromlist=['*'])
                setattr(cls, 'Model', getattr(module, model_name))
            except (ImportError, AttributeError):
                raise RuntimeError("Scaffold coudn't automatically determine a model class for handler %s, please assign it a Model class variable." % cls.__name__)

        if cls.ModelForm == None:
            cls.ModelForm = model_form(cls.Model)

        # self.scaffold.method
        methods = inspect.getmembers(s.Handler, predicate=inspect.ismethod)
        for n, f in methods:
            cls.scaffold[n] = f.__func__

    @classmethod
    def wrap_class_functions(s, cls):
        for prop in s.Wrap.__dict__:
            p = getattr(s.Wrap, prop)
            if callable(p) and hasattr(cls, prop):
                f = p(getattr(cls, prop))
                setattr(cls, prop, f)
        return cls
