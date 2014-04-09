# *-* coding: UTF-8 *-*

import random
import string

from webapp2_extras import sessions, auth

def random_string(size=6, chars=string.ascii_letters + string.digits):
    """ Generate random string """
    return ''.join(random.choice(chars) for _ in range(size))

def generate_csrf_token():
    """ Generates a new csrf token and stores it in the session"""
    session = sessions.get_store().get_session()
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string()
    return session['_csrf_token']


class CSRF(object):
    """
    Provides protection against Cross-site Request Forgery
    http://en.wikipedia.org/wiki/Cross-site_request_forgery
    """
    def __init__(self, controller):
        self.controller = controller
        self.controller.events.before_render += self._on_before_render

    def _on_before_render(self, controller, *args, **kwargs):
        controller.context['csrf_token'] = generate_csrf_token


def require_csrf_for_post(controller):
    """
    Returns True if the request method is POST and a valid csrf token was included in the request, otherwise returns False.
    """
    if controller.request.method == 'POST' and not controller.request.path.startswith('/taskqueue'):
        token = controller.session.get('_csrf_token')
        if not token or token != controller.request.get('_csrf_token'):
            return False
    return True
