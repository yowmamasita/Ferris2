import inspect


class RequestParser(object):
    _parsers = {}

    container_name = None

    class __metaclass__(type):
        def __new__(meta, name, bases, dict):
            cls = type.__new__(meta, name, bases, dict)
            if name != 'RequestParser':
                RequestParser._parsers[name.lower()] = cls
            return cls

    def __init__(self):
        self.container = None
        self.fallback = None
        self.data = None
        self.errors = None

    @classmethod
    def factory(cls, name):
        if inspect.isclass(name):
            return name
        return cls._parsers.get(name.lower(), cls._parsers.get(name.lower() + 'parser'))()

    def process(self, request, container, fallback):
        raise NotImplementedError()

    def update(self, obj):
        raise NotImplementedError()

    def validate(self):
        return True


from .json_util import parse as parse_json


class FormParser(RequestParser):
    container_name = 'Form'

    def process(self, request, container, fallback=None):
        from wtforms_json import MultiDict, flatten_json

        if request.content_type == 'application/json':
            request_data = MultiDict(flatten_json(parse_json(request.body)))
        else:
            request_data = request.params

        if inspect.isclass(container):
            container = container()

        container.process(formdata=request_data, obj=fallback, **container.data)

        self.container = container
        self.fallback = fallback

        return self

    def update(self, obj):
        self.container.populate_obj(obj)
        return obj

    def validate(self):
        return self.container.validate if self.container else False

    def _get_data(self):
        return self.container.data if self.container else None

    def _set_data(self, val):
        if self.container:
            self.container.data = val

    data = property(_get_data, _set_data)

    def _get_errors(self):
        return self.container.errors if self.container else None

    errors = property(_get_errors, lambda s, v: None)


class MessageParser(RequestParser):
    container_name = 'Message'

    def process(self, request, container, fallback=None):
        from protorpc import protojson, messages

        try:
            result = protojson.decode_message(container, request.body)
            self.errors = None

        except messages.ValidationError as e:
            result = container()
            self.errors = [e.message]

        self.container = result
        self.fallback = fallback
        return self

    def validate(self):
        return not self.errors and self.container.is_initialized() if self.container else False

    def update(self, obj):
        from .messages import message_to_entity
        return message_to_entity(self.container, obj)
