from ferris.core.ndb import ndb


class TinyMce(object):
    """
    Automatically makes TextProperty fields into TinyMCE editors (for the admin interface
    """

    def __init__(self, handler):
        self.handler = handler
        self.handler.events.after_process_form_data += self.after_process_form_data.__get__(self)

    def after_process_form_data(self, handler, form):
        if handler.Model:
            for field in form:
                if field.name in handler.Model._properties.keys():
                    if isinstance(handler.Model._properties[field.name], ndb.TextProperty):
                        field.flags.tinymce = True
