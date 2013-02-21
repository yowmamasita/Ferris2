from datetime import datetime
from pytz.gae import pytz
from settings import app_config

utc = pytz.timezone('UTC')
local_tz = pytz.timezone(app_config['timezone'])


def localize(dt):
    if not dt.tzinfo:
        dt = utc.localize(dt)
    return dt.astimezone(local_tz)
