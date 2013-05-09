from protorpc import messages, message_types
from google.appengine.api import users
from google.appengine.ext import ndb
from .types import UserMessage, KeyMessage


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


class DateTimeConverter(Converter):
    @staticmethod
    def to_field(Model, property, count):
        return message_types.DateTimeField(count)


class UserConverter(Converter):
    @staticmethod
    def to_message(Model, property, value):
        if value:
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
        return messages.MessageField(UserMessage, count)


class KeyConverter(Converter):
    @staticmethod
    def to_message(Model, property, value):
        if value:
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
        return messages.MessageField(KeyMessage, count)


converters = {
    'Key': KeyConverter,
    ndb.StringProperty: StringConverter,
    ndb.TextProperty: StringConverter,
    ndb.DateTimeProperty: DateTimeConverter,
    ndb.UserProperty: UserConverter,
    ndb.KeyProperty: KeyConverter,
}
