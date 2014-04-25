# -*- coding: utf-8 -*-
from google.appengine.api import memcache
from google.appengine.ext import ndb
from functools import wraps
import datetime
import threading


none_sentinel_string = u'☃☸☃ - caching sentinel'


def cache(key, ttl=0, backend=None):
    """
    """
    if backend is None or backend == 'memcache':
        backend = MemcacheBackend
    elif backend == 'local':
        backend = LocalBackend
    elif backend == 'datastore':
        backend = DatastoreBackend

    def wrapper(f):
        @wraps(f)
        def dispatcher(*args, **kwargs):
            data = backend.get(key)

            if data == none_sentinel_string:
                return None

            if data is None:
                data = f(*args, **kwargs)
                backend.set(key, none_sentinel_string if data is None else data, ttl)

            return data

        #setattr(dispatcher, 'clear_cache', _cache_invalidator(key))
        #setattr(dispatcher, 'cached', _cache_getter(key))
        setattr(dispatcher, 'uncached', f)
        return dispatcher
    return wrapper


class LocalBackend(object):
    cache_obj = threading.local()

    @classmethod
    def set(cls, key, data, ttl):
        if ttl:
            expires = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        else:
            expires = None
        setattr(cls.cache_obj, key, (data, expires))

    @classmethod
    def get(cls, key):
        if not hasattr(cls.cache_obj, key):
            return None

        data, expires = getattr(cls.cache_obj, key)

        if expires and expires < datetime.datetime.now():
            delattr(cls.cache_obj, key)
            return None

        return data

    @classmethod
    def delete(cls, key):
        try:
            delattr(cls.cache_obj, key)
        except AttributeError:
            pass

    @classmethod
    def reset(cls):
        for a in cls.cache_obj.__dict__.keys():
            delattr(cls.cache_obj, a)


class MemcacheBackend(object):
    @classmethod
    def set(cls, key, data, ttl):
        memcache.set(key, data, ttl)

    @classmethod
    def get(cls, key):
        return memcache.get(key)

    @classmethod
    def delete(cls, key):
        memcache.delete(key)


class MemcacheCompareAndSetBackend(MemcacheBackend):
    @classmethod
    def set(cls, key, data, ttl):
        client = memcache.Client()
        if not client.gets(key):
            memcache.set(key, data, ttl)
            return

        for _ in range(10):
            if client.cas(key, data, ttl):
                break


class DatastoreBackend(object):
    @classmethod
    def set(cls, key, data, ttl):
        if ttl:
            expires = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        else:
            expires = None

        DatastoreCacheModel(id=key, data=data, expires=expires).put()

    @classmethod
    def get(cls, key):
        item = ndb.Key(DatastoreCacheModel, key).get()

        if not item:
            return None

        if item.expires and item.expires < datetime.datetime.now():
            item.key.delete()
            return None

        return item.data

    @classmethod
    def delete(cls, key):
        ndb.Key(DatastoreCacheModel, key).delete()


class DatastoreCacheModel(ndb.Model):
    data = ndb.PickleProperty(indexed=False, compressed=True)
    expires = ndb.DateTimeProperty(indexed=False)


class LayeredBackend(object):
    def __init__(self, *args):
        self.backends = args

    def set(self, key, data, ttl):
        for b in self.backends:
            b.set(key, data, ttl)

    def get(self, key):
        for b in self.backends:
            data = b.get(key)
            if data is not None:
                return data

    def delete(self, key):
        for b in self.backends:
            b.delete(key)
