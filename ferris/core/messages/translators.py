from protorpc import messages
from .converters import converters


def entity_to_message(entity, message_type):
    message_fields = [x.name for x in message_type.all_fields()]
    entity_properties = [k for k, v in entity._properties.iteritems()]
    fields = set(message_fields) & set(entity_properties)

    values = {}
    for field in fields:
        property = entity._properties[field]
        value = getattr(entity, field)

        converter = converters[property.__class__]

        if converter:
            value = converter.to_message(entity, property, value)
            values[field] = value

    return message_type(**values)


def message_to_entity(message, model_type):
    message_fields = [x.name for x in message.all_fields()]
    entity_properties = [k for k, v in model_type._properties.iteritems()]
    fields = set(message_fields) & set(entity_properties)

    values = {}
    for field in fields:
        property = model_type._properties[field]
        value = getattr(message, field)

        converter = converters[property.__class__]

        if converter:
            value = converter.to_model(message, field, value)
            values[field] = value

    return model_type(**values)


def model_message(Model):
    name = Model.__name__ + 'Message'

    props = Model._properties
    sorted_props = sorted(props.iteritems(), key=lambda prop: prop[1]._creation_counter)
    field_names = list(x[0] for x in sorted_props)

    field_dict = {}
    for count, name in enumerate(field_names, start=1):
        prop = props[name]
        converter = converters.get(prop.__class__, None)

        if converter:
            field_dict[name] = converter.to_field(Model, prop, count)

    return type(name, (messages.Message,), field_dict)


def list_message(message_type):
    name = message_type.__name__ + 'List'
    fields = {
        'items': messages.MessageField(message_type, 1, repeated=True),
    }
    return type(name, (messages.Message,), fields)
