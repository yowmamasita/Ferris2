from settings import app_config
from google.appengine.api import mail


class Email(object):
    """
    Provides some helper methods to send email using templates.
    """

    def __init__(self, handler):
        self.handler = handler

    def test(self):
        self.send(
            'jonathan.parrott+appengine@cloudshepas.com',
            'Test',
            'App Engine Email Test')

    def send(self, recipient, subject, body, reply_to=None, **kwargs):
        """
        Sends an html email to ``recipient`` with the given ``subject`` and ``body``.

        The sender is automatically set to ``app_config['email']['sender']``.

        Any additionally arguments are passed to ``mail.send_mail``, such as headers.
        """
        mail.send_mail(
            sender=app_config['email']['sender'],
            to=recipient,
            subject=subject,
            body=body,
            html=body,
            reply_to=reply_to,
            **kwargs)

    def send_template(self, recipient, subject, template, reply_to=None, **kwargs):
        """
        Renders a template and sends an email in the same way as :meth:`send`.

        The current template context is used, so use ``Handler.set`` to bind any variables to the template.
        """
        template = 'email/' + template + '.html'
        body = self.handler.render_template(template)
        self.send(recipient, subject, body, reply_to, **kwargs)
