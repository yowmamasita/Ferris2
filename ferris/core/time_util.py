from pytz.gae import pytz
from . import settings


def utc_tz():
    return pytz.timezone('UTC')


def local_tz():
    return pytz.timezone(settings.get('timezone')['local'])


def localize(dt):
    if not dt.tzinfo:
        dt = utc_tz().localize(dt)
    return dt.astimezone(local_tz())
