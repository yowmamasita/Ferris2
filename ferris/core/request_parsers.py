

class RequestParser(object):
    _parsers = {}

    class __metaclass__(type):
        def __new__(meta, name, bases, dict):
            cls = type.__new__(meta, name, bases, dict)
            if name != 'RequestParser':
                RequestParser._parsers[name.lower()] = cls
            return cls

    @classmethod
    def factory(cls, name):
        return cls._parsers.get(name.lower(), cls._parsers.get(name.lower() + 'parser'))()

    def process(self, request, container, fallback):
        raise NotImplementedError()


from .json_util import parse as parse_json


class FormParser(RequestParser):

    def process(self, request, container, fallback=None):
        from wtforms_json import MultiDict, flatten_json

        if request.content_type == 'application/json':
            request_data = MultiDict(flatten_json(parse_json(request.body)))
        else:
            request_data = request.params

        container.process(formdata=request_data, obj=fallback, **container.data)
        return container.data


class MessageParser(RequestParser):

    def process(self, request, container, fallback=None):
        from protorpc import protojson
        result = protojson.decode_message(container, request.body)
        return result
