"""
OAuth dance session
"""

from google.appengine.ext import ndb
from ferris.core.ndb import Model
from credentials_property import CredentialsProperty
from ndb_storage import NdbStorage


class UserCredentials(Model):

    user = ndb.UserProperty()
    scopes = ndb.StringProperty(repeated=True)
    admin = ndb.BooleanProperty()
    credentials = CredentialsProperty()
    filter_scopes = ndb.StringProperty()

    @classmethod
    def _get_kind(cls):
        return '__ferris__oauth2_user_credentials'

    @classmethod
    def after_get(cls, key, item):
        if item and item.credentials:
            item.credentials = NdbStorage(key, 'credentials', item).get()

    def before_put(self):
        if self.scopes:
            self.filter_scopes = ','.join(sorted(self.scopes))

    @classmethod
    def find(cls, user=None, scopes=None, admin=None):
        scopes = ','.join(sorted(scopes))
        kwargs = {}
        if user:
            kwargs['user'] = user
        if scopes:
            kwargs['filter_scopes'] = scopes
        if admin:
            kwargs['admin'] = True
        else:
            kwargs['admin'] = False

        x = cls.find_by_properties(**kwargs)
        if x:
            cls.after_get(x.key, x)
        return x

    @classmethod
    def find_all(cls, user, scopes, admin):
        scopes = ','.join(sorted(scopes))
        kwargs = {}
        if user:
            kwargs['user'] = user
        if scopes:
            kwargs['filter_scopes'] = scopes
        if admin:
            kwargs['admin'] = True
        else:
            kwargs['admin'] = False

        x = cls.find_all_by_properties(**kwargs)
        for _ in x:
            cls.after_get(_.key, _)
        return x
