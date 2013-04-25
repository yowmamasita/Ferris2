from lib import WithTestBed
from ferris import Model, ndb, messages


class Widget(Model):
    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty()


class TestMessageModelTranslators(WithTestBed):

    def testModelMessage(self):
        WidgetMessage = messages.model_message(Widget)

        properties = Widget._properties.keys()
        fields = dir(WidgetMessage)

        for prop in properties:
            assert prop in fields

    def testModelToMessage(self):
        WidgetMessage = messages.model_message(Widget)

        widget = Widget(title='The Doctor', content='Time-traveling binary vascular alien from Gallifrey')
        message = messages.entity_to_message(widget, WidgetMessage)

        assert message.title == widget.title
        assert message.content == widget.content

        # Updating an existing instance
        message = messages.entity_to_message(widget, WidgetMessage(title='Meow'))

        assert message.title == widget.title
        assert message.content == widget.content

    def testMessageToModel(self):
        WidgetMessage = messages.model_message(Widget)

        message = WidgetMessage(title='Dalek', content='Exterminate!')

        widget = messages.message_to_entity(message, Widget)

        assert message.title == widget.title
        assert message.content == widget.content

        # Updating an existing instance
        widget = messages.message_to_entity(message, Widget(title='Meow'))

        assert message.title == widget.title
        assert message.content == widget.content
