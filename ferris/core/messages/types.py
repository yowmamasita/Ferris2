from protorpc import messages


class UserMessage(messages.Message):
    email = messages.StringField(1)
    user_id = messages.StringField(2)
    nickname = messages.StringField(3)


class KeyMessage(messages.Message):
    urlsafe = messages.StringField(1)
    id = messages.StringField(2)
    kind = messages.StringField(4)


class GeoPtMessage(messages.Message):
    lat = messages.FloatField(1)
    lon = messages.FloatField(2)
