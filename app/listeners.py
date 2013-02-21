"""
Central place to store event listeners for your application,
automatically imported at run time.
"""
import logging
import webapp2
from ferris.core.events import on


@on('handler_is_authorized')
def is_authorized(handler):
    pass


@on('before_template_render')
def before_template_render(name, *args, **kwargs):
    pass
