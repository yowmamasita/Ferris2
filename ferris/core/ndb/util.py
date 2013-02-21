"""
Utilities for working with both db and ndb models
"""

from google.appengine.ext import db, ndb


def list(Model, *args, **kwargs):
    """
    Returns a query object for a db or ndb Model
    """
    if issubclass(Model, db.Model):
        return Model.all()
    else:
        return Model.query()


def key_from_string(str, kind=None):
    """
    Makes a ndb Key object from the given data
    and optionally a kind. Kind is only needed if
    the str is an id.
    """
    str = str.lstrip(':')
    try:
        id = long(str)
        return ndb.Key(kind, id)
    except ValueError:
        return ndb.Key(urlsafe=str)


def key_id_for(ins):
    """
    Gets the id of a key for either a db or ndb instance
    """
    return new_key(ins).id()


def key_urlsafe_for(ins):
    """
    Gets the urlsafe of a key for either a db or ndb instance
    """
    return new_key(ins).urlsafe()


def new_key(ins_or_key):
    """
    Makes a ndb.Key from ndb or db instances or keys
    """
    if isinstance(ins_or_key, ndb.Key):
        return ins_or_key
    elif isinstance(ins_or_key, db.Model):
        return ndb.Key.from_old_key(ins_or_key.key())
    elif isinstance(ins_or_key, db.Key):
        return ndb.Key.from_old_key(ins_or_key)
    elif isinstance(ins_or_key, ndb.Model):
        return ins_or_key.key
    return None


def old_key(ins_or_key):
    """
    Makes a db.Key from ndb or db instances or keys
    """
    if isinstance(ins_or_key, ndb.Model):
        return ins_or_key.key.to_old_key()
    elif isinstance(ins_or_key, ndb.Key):
        return ins_or_key.to_old_key()
    elif isinstance(ins_or_key, db.Model):
        return ins_or_key.key()
    else:
        return ins_or_key
