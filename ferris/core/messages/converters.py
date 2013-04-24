from protorpc import messages, message_types
from google.appengine.api import users
from google.appengine.ext import ndb
from .types import UserMessage


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
        return messages.StringField(count)


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


converters = {
    ndb.StringProperty: StringConverter,
    ndb.TextProperty: StringConverter,
    ndb.DateTimeProperty: DateTimeConverter,
    ndb.UserProperty: UserConverter
}