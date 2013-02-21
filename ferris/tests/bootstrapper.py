import sys
import re
import logging


def bootstrap(sdk_path):
    sys.path.insert(0, sdk_path)

    # Force the google module to reload, for some reason on windows this can sometimes point to the one in site-packages.
    import google
    reload(google)

    import dev_appserver
    dev_appserver.fix_sys_path()
    sys.path = [re.sub('webob_0_9', 'webob_1_1_1', x) for x in sys.path]

    import fix_imports
    (fix_imports)

    # Activate a testbed so that httplib2 always knows that it's in app engine
    from google.appengine.ext import testbed
    testbed = testbed.Testbed()
    testbed.activate()
    testbed.init_urlfetch_stub()

    # Remove agressive logging
    rootLogger = logging.getLogger()
    for handler in rootLogger.handlers:
        if isinstance(handler, logging.StreamHandler):
            rootLogger.removeHandler(handler)
