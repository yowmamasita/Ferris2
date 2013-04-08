

class RequestParser(object):
    _parsers = {}

    class __metaclass__(type):
        def __new__(meta, name, bases, dict):
            cls = type.__new__(meta, name, bases, dict)
            if name != 'RequestParser':
                RequestParser._parsers[name] = cls
            return cls

    @classmethod
    def factory(cls, name):
        return cls._parsers[name]()

    def process(self, request, container, fallback):
        raise NotImplementedError()


class FormParser(RequestParser):

    def process(self, request, container, fallback=None):
        container.process(formdata=request.params, obj=fallback, **container.data)
        return container.data
