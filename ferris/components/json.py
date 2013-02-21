import logging
from webapp2 import Response
from ferris.core import inflector


class Json(object):
    """
    Hooks into a handler to return json instead of rendering a template when the requestor asks for JSON.

    The requestor can ask for json by adding ``?alt=json`` to the URL, or by setting the ``Accepts`` header to ``application/json``. You can also manually activate JSON in your handler by setting the ``render_as_json`` attribute.

    By default, the json component will try to get the data to serialize using the following template variables: data, pluralize(handler), singularize(handler), edit_item, added_item, and item. You can specify additional variables to try by appending to the ``try_vars`` attribute.
    """

    def __init__(self, handler):
        self.handler = handler
        self.render_as_json = False
        self.indent = None
        self.try_vars = [
            'data',
            inflector.pluralize(self.handler.name),
            inflector.singularize(self.handler.name),
            'edited_item',
            'added_item',
            'item']

        self.handler.events.before_dispatch += self.before_dispatch_callback.__get__(self)
        self.handler.events.after_dispatch += self.after_dispatch_callback.__get__(self)

    def before_dispatch_callback(self, *args, **kwargs):
        if self.handler.request.params.get('alt', None) == 'json' or self.handler.request.headers.get('Accept', None) == 'application/json':
            self.render_as_json = True

    def after_dispatch_callback(self, response, *args, **kwargs):
        if response == None and self.render_as_json == True:
            self.render()

    def render(self):
        self.handler.auto_render = False

        for key in self.try_vars:
            data = self.handler.get(key)
            if data is not None:
                logging.debug('Generating json from key %s' % key)
                break

        if data is not None:
            self.handler.response.charset = 'utf8'
            self.handler.response.headers['Content-Type'] = 'application/json'
            self.handler.response.body = self.handler.json(data, indent=self.indent)
