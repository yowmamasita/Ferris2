from webapp2 import Response
from .messages import Message


class ResponseHandler(object):
    _handlers = {}

    class __metaclass__(type):
        def __new__(meta, name, bases, dict):
            cls = type.__new__(meta, name, bases, dict)
            if name != 'ResponseHandler':
                ResponseHandler._handlers[cls.type] = cls
            return cls

    @classmethod
    def factory(cls, kind):
        if kind in cls._handlers:
            return cls._handlers[kind]()
        for parent_kind in cls._handlers.keys():
            if issubclass(kind, parent_kind):
                return cls._handlers[parent_kind]()

    def process(self, handler, result):
        raise NotImplementedError()

    def __call__(self, *args, **kwargs):
        return self.process(*args, **kwargs)


class ResponseResponseHandler(ResponseHandler):
    type = Response

    def process(self, handler, result):
        return result


class StringResponseHandler(ResponseHandler):
    type = basestring

    def process(self, handler, result):
        handler._clear_redirect()
        handler.response.charset = 'utf8'
        handler.response.unicode_body = unicode(result)
        handler.response.content_type = result.content_type if hasattr(result, 'content_type') else 'text/plain'
        return handler.response


class TupleResponseHandler(ResponseHandler):
    type = tuple

    def process(self, handler, result):
        handler._clear_redirect()
        handler.response = Response(result)
        return handler.response


class IntResponseHandler(ResponseHandler):
    type = int

    def process(self, handler, result):
        handler._clear_redirect()
        handler.abort(result)


class MessageHandler(ResponseHandler):
    type = Message

    def process(self, handler, result):
        handler._clear_redirect()
        handler.meta.change_view('message')
        handler.context['data'] = result
        return handler.meta.view.render()
