

class Devices(object):
    """ Hooks into list to provide automatic detection of (apple) devices """

    def __init__(self, handler):
        self.handler = handler
        self.handler.events.before_dispatch += self.before_dispatch_callback.__get__(self)

    def detect(self):
        uas = self.handler.request.environ.get('HTTP_USER_AGENT', '')

        ua_dict = {
            'user_agent': uas,
            'mobile': (
                "Mobile" in uas or
                "Android" in uas or
                "iP" in uas),
            'ios': ("Mobile" in uas and "AppleWebKit" in uas and "iP" in uas)
        }

        self.handler.set('devices', ua_dict)
        return ua_dict

    def before_dispatch_callback(self, *args, **kwargs):
        self.detect()
