from protorpc import messages


class UserMessage(messages.Message):
    email = messages.StringField(1)
    user_id = messages.StringField(2)
    nickname = messages.StringField(3)
