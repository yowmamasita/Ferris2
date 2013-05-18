from protorpc import messages, message_types
from google.appengine.api import users
from google.appengine.ext import ndb
from .types import UserMessage, KeyMessage, GeoPtMessage


class Converter(object):
    @staticmethod
    def to_message(Model, property, value):
        return value

    @staticmethod
    def to_model(Message, field, value):
        return value

    @staticmethod
    def to_field(Model, property, count):
        return None


class StringConverter(Converter):
    @staticmethod
    def to_field(Model, property, count):
        return messages.StringField(count, repeated=property._repeated)


class BytesConverter(Converter):
    @staticmethod
    def to_field(Model, property, count):
        return messages.BytesField(count, repeated=property._repeated)


class BooleanConverter(Converter):
    @staticmethod
    def to_field(Model, property, count):
        return messages.BooleanField(count, repeated=property._repeated)


class IntegerConverter(Converter):
    @staticmethod
    def to_field(Model, property, count):
        return messages.IntegerField(count, repeated=property._repeated)


class FloatConverter(Converter):
    @staticmethod
    def to_field(Model, property, count):
        return messages.FloatField(count, repeated=property._repeated)


class DateTimeConverter(Converter):
    @staticmethod
    def to_field(Model, property, count):
        return message_types.DateTimeField(count, repeated=property._repeated)


class UserConverter(Converter):
    @staticmethod
    def to_message(Model, property, value):
        return UserMessage(
            email=value.email(),
            user_id=value.user_id(),
            nickname=value.nickname())

    @staticmethod
    def to_model(Message, field, value):
        if isinstance(value, basestring):
            return users.User(email=value)
        elif isinstance(value, UserMessage):
            if value.user_id:
                return users.User(email=value.user_id)
            elif value.email:
                return users.User(email=value.email)

    @staticmethod
    def to_field(Model, property, count):
        return messages.MessageField(UserMessage, count, repeated=property._repeated)


class BlobKeyConverter(Converter):
    @staticmethod
    def to_message(Model, property, value):
        return str(value)

    @staticmethod
    def to_model(Message, field, value):
        return ndb.BlobKey(value)

    @staticmethod
    def to_field(Model, property, count):
        return messages.StringField(count, repeated=property._repeated)


class KeyConverter(Converter):
    @staticmethod
    def to_message(Model, property, value):
        return KeyMessage(
            urlsafe=value.urlsafe(),
            id=u'%s' % value.id(),
            kind=value.kind())

    @staticmethod
    def to_model(Message, field, value):
        if isinstance(value, basestring):
            return ndb.Key(urlsafe=value)
        elif isinstance(value, KeyMessage):
            return ndb.Key(urlsafe=value.urlsafe)

    @staticmethod
    def to_field(Model, property, count):
        return messages.MessageField(KeyMessage, count, repeated=property._repeated)


class GeoPtConverter(Converter):
    @staticmethod
    def to_message(Model, property, value):
        return GeoPtMessage(lat=value.lat, lon=value.lon)

    @staticmethod
    def to_model(Message, field, value):
        if value:
            return ndb.GeoPt(value.lat, value.lon)

    @staticmethod
    def to_field(Model, property, count):
        return messages.MessageField(GeoPtMessage, count, repeated=property._repeated)


converters = {
    'Key': KeyConverter,
    ndb.BooleanProperty: BooleanConverter,
    ndb.IntegerProperty: IntegerConverter,
    ndb.FloatProperty: FloatConverter,
    ndb.BlobProperty: BytesConverter,
    ndb.StringProperty: StringConverter,
    ndb.TextProperty: StringConverter,
    ndb.DateTimeProperty: DateTimeConverter,
    ndb.UserProperty: UserConverter,
    ndb.GeoPtProperty: GeoPtConverter,
    ndb.KeyProperty: KeyConverter,
    ndb.BlobKeyProperty: BlobKeyConverter
}
