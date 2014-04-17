import functools
from time import sleep
import logging
import json


def retries(max_tries, should_retry, delay=1, backoff=2):
    """
    Decorator that implements exponential backoff retry logic. If you have
    a function that may fail, this decorator can catch the exception and retry at
    exponentially increasing intervals until the number of retries is exhausted.

    The should_retry parameter should be a function that takes and exception as an argument
    and returns True if the function should be retried or False to permanently fail.

    This is extremely useful when working with external APIs. There is a shortcut
    decorator for working with Google APIs, see :func:`google_api_retries`.
    """
    def dec(func):
        functools.wraps(func)

        def f2(*args, **kwargs):
            seconds = delay
            tries = range(max_tries)
            tries.reverse()

            for tries_remaining in tries:
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    if tries_remaining > 0 and should_retry(e):
                        logging.info("Exception raised, retrying in %s seconds" % seconds)
                        sleep(seconds)
                        seconds *= backoff
                    else:
                        raise e
                else:
                    break
        return f2
    return dec


def apiclient_retry_policy(exception):
    from apiclient import errors
    if not isinstance(exception, errors.HttpError):
        return False

    error = json.loads(exception.content)
    if error.get('code') == 403 and error.get('errors')[0].get('reason') in ('rateLimitExceeded', 'userRateLimitExceeded'):
        logging.info("Rate limit exceeded, retrying...")
        return True

    return False


def google_api_retries(f):
    """
    Shortcut decorator that uses the appropraite retry policy for dealing with Google APIs.

    Will retry if an HttpError in the 5xx range is raise, but will fail if the error is in the 4xx range.
    """
    from apiclient import errors

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
