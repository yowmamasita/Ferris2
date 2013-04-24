from protorpc import messages
from .converters import converters as default_converters


def _common_fields(entity, message):
    message_fields = [x.name for x in message.all_fields()]
    entity_properties = [k for k, v in entity._properties.iteritems()]
    fields = set(message_fields) & set(entity_properties)
    return message_fields, entity_properties, fields


def entity_to_message(entity, message_type, converters=None):
    message_fields, entity_properties, fields = _common_fields(entity, message_type)

    converters = dict(default_converters.items() + converters.items()) if converters else default_converters

    values = {}
    for field in fields:
        property = entity._properties[field]
        value = getattr(entity, field)

        converter = converters[property.__class__]

        if converter:
            value = converter.to_message(entity, property, value)
            values[field] = value

    return message_type(**values)


def message_to_entity(message, model_type, converters=None):
    message_fields, entity_properties, fields = _common_fields(model_type, message)

    converters = dict(default_converters.items() + converters.items()) if converters else default_converters

    values = {}
    for field in fields:
        property = model_type._properties[field]
        value = getattr(message, field)

        converter = converters[property.__class__]

        if converter:
            value = converter.to_model(message, field, value)
            values[field] = value

    return model_type(**values)


def model_message(Model, only=None, exclude=None, converters=None):
    name = Model.__name__ + 'Message'

    props = Model._properties
    sorted_props = sorted(props.iteritems(), key=lambda prop: prop[1]._creation_counter)
    field_names = [x[0] for x in sorted_props if x[0]]

    if exclude:
        field_names = [x for x in field_names if x not in exclude]

    if only:
        field_names = [x for x in field_names if x in only]

    converters = dict(default_converters.items() + converters.items()) if converters else default_converters

    field_dict = {}
    for count, name in enumerate(field_names, start=1):
        prop = props[name]
        converter = default_converters.get(prop.__class__, None)

        if converter:
            field_dict[name] = converter.to_field(Model, prop, count)

    return type(name, (messages.Message,), field_dict)


def list_message(message_type):
    name = message_type.__name__ + 'List'
    fields = {
        'items': messages.MessageField(message_type, 1, repeated=True),
    }
    return type(name, (messages.Message,), fields)
