class FlashMessages(object):
    """
    Flash Messages are brief messages that are stored in the session and displayed to the user on
    the next page. These are useful for things like create/edit/delete acknowledgements.
    """

    def __init__(self, handler):
        self.handler = handler
        self.handler.events.before_render += self._on_before_render

    def flash(self, message, type='info'):
        """
        Adds the given message to the list of "flash" messages to show to the user on the next page.
        """
        flash = self.handler.session.get('__flash', [])
        flash.append((message, type))
        self.handler.session['__flash'] = flash

    def messages(self, clear=True):
        """
        returns all flash messsages, and by default clears the queue
        """
        flashes = self.handler.session.get('__flash', [])
        if clear:
            self.handler.session['__flash'] == []
        return flashes

    def _on_before_render(self, handler, *args, **kwargs):
        handler.context.set_dotted('ferris.flash_messages', self.messages)

    __call__ = flash
