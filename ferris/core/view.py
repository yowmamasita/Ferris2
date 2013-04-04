import template


class ViewContext(dict):
    def get_dotted(self, name, default=None):
        data = self
        path = name.split('.')
        for chunk in path[:-1]:
            data = data.setdefault(chunk, {})
        return data.setdefault(path[-1], default)

    def set_dotted(self, name, value):
        path = name.split('.')
        container = self.get_dotted('.'.join(path[:-1]), {})
        container[path[-1]] = value


class View(object):

    def __init__(self, handler, context):
        self.handler = handler
        if isinstance(context, dict):
            context = ViewContext(**context)
        self.context = context

    def render(self, *args, **kwargs):
        raise NotImplementedError("Base view can't render anything")


class TemplateView(View):

    def __init__(self, handler, context):
        super(TemplateView, self).__init__(handler, context)
        self.template_name = None
        self.template_ext = 'html'
        self.theme = None
        self.setup_template_variables()

    def setup_template_variables(self):
        self.context['handler'] = {
            'name': self.handler.name,
            'uri': self.handler.uri,
            'prefix': self.handler.prefix,
            'action': self.handler.action,
            'uri_exists': self.handler.uri_exists,
            'on_uri': self.handler.on_uri,
            'request': self.handler.request,
            'self': self.handler,
            'url_id_for': self.handler.url_id_for,
            'url_key_for': self.handler.url_id_for,
            'user': self.handler.user
        }
        self.handler._delegate_event('template_vars', handler=self.handler)

    def render(self, *args, **kwargs):
        self.handler._delegate_event('before_render', handler=self.handler)
        result = template.render_template(self.get_template_names(), self.context, theme=self.theme)
        self.handler._delegate_event('after_render', handler=self.handler, result=result)

        return result

    def get_template_names(self):
        """
        Generates a list of template names.

        The template engine will try each template in the list until it finds one.

        For non-prefixed actions, the return value is simply: ``[ "[handler]/[action].[ext]" ]``.
        For prefixed actions, another entry is added to the list : ``[ "[handler]/[prefix_][action].[ext]" ]``. This means that actions that are prefixed can fallback to using the non-prefixed template.

        For example, the action ``Posts.json_list`` would try these templates::

            posts/json_list.html
            posts/list.html

        """
        if self.template_name:
            return self.template_name

        templates = []

        if self.handler.prefix:
            template = self.handler.name + '/' + self.handler.prefix + '_' + self.handler.action + '.' + self.template_ext
            templates.append(template)

        # non-prefixed
        template = self.handler.name + '/' + self.handler.action + '.' + self.template_ext
        templates.append(template)

        self.handler._delegate_event('template_names', handler=self.handler, templates=templates)

        return templates
