from ferris.core.ndb import encode_key, decode_key, new_key


class Wrap(object):
    """
    Functions that decorate/replace existing functions in the handler
    """

    @staticmethod
    def dispatch(f):
        def wrapper(self, *args, **kwargs):
            self._scaffold_init()
            self.events.before_render += self._scaffold_on_before_render
            self.events.template_names += self._scaffold_on_template_names
            return f(self, *args, **kwargs)
        return wrapper

    @staticmethod
    def url_id_for(f):
        def f(self, item):
            """
            Used in templates/urlgeneration to return an id or urlsafe
            key depending on settings.
            """
            if self.scaffold.use_ids:
                return new_key(item).id()
            return ':' + encode_key(item)
        return f

    @staticmethod
    def key_from_string(f):
        def rf(self, str, kind=None):
            if not kind:
                kind = self.Model
            return f(self, str, kind)
        return rf
