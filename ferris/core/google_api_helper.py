import httplib2
import logging
import json
import functools
from apiclient import errors


def apiclient_retry_policy(exception):
    if not isinstance(exception, errors.HttpError):
        return False

    try:
        error = json.loads(exception.content)
        if error.get('code') == 403 and error.get('errors')[0].get('reason') in ('rateLimitExceeded', 'userRateLimitExceeded'):
            logging.info("Rate limit exceeded, retrying...")
            return True

    except ValueError:
        logging.error("Failed to parse json from exception: %s" % exception.content)

    return False


def google_api_retries(f):
    """
    Shortcut decorator that uses the appropraite retry policy for dealing with Google APIs.

    Will retry if an HttpError in the 5xx range is raise, but will fail if the error is in the 4xx range.
    """
    from ferris import retries

    @functools.wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except errors.HttpError as error:
            raise
        except Exception as error:
            logging.error("Non-recoverable exception: %s" % error)
            raise

    r_inner = retries(max_tries=5, should_retry=apiclient_retry_policy, delay=1, backoff=2)(inner)
    return r_inner


def get_discovery_document(api, api_version, uri_template="https://www.googleapis.com/discovery/v1/apis/{api}/{api_version}/rest", http=None):
    """
    Provides an automatic caching version of the apiclient discovery
    document fetching mechanism using memcache.
    """
    from ferris import caching
    if not http:
        http = httplib2.Http()

    uri = uri_template.format(api=api, api_version=api_version)

    @caching.cache_using_memcache('gapi-discovery-doc-%s' % uri, 24*60*60)
    def fetch():
        r, c = http.request(uri)
        return r, c

    r, c = fetch()

    return c


def patch_discovery():
    from apiclient import discovery
    original_build = discovery.build

    def patched_build(serviceName, version, http=None, **kwargs):
        doc = get_discovery_document(serviceName, version, http=http)
        return discovery.build_from_document(doc, http=http, **kwargs)

    discovery.build = patched_build
    setattr(discovery, '_build', original_build)


patch_discovery()
