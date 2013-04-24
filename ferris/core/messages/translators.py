import inspect
from protorpc import messages
from .converters import converters as default_converters


def _common_fields(entity, message):
    message_fields = [x.name for x in message.all_fields()]
    entity_properties = [k for k, v in entity._properties.iteritems()]
    fields = set(message_fields) & set(entity_properties)
    return message_fields, entity_properties, fields


def entity_to_message(entity, message, converters=None):
    message_fields, entity_properties, fields = _common_fields(entity, message)

    converters = dict(default_converters.items() + converters.items()) if converters else default_converters

    # Key first
    values = {
        'key': converters['Key'].to_message(entity, 'key', entity.key)
    }

    # Other fields
    for field in fields:
        property = entity._properties[field]
        value = getattr(entity, field)

        converter = converters[property.__class__]

        if converter:
            value = converter.to_message(entity, property, value)
            values[field] = value

    if inspect.isclass(message):
        return message(**values)
    else:
        for name, value in values.iteritems():
            setattr(message, name, value)
        return message


def message_to_entity(message, model, converters=None):
    message_fields, entity_properties, fields = _common_fields(model, message)

    converters = dict(default_converters.items() + converters.items()) if converters else default_converters

    values = {}

    # Key first, if it's there
    if hasattr(message, 'key') and message.key:
        values['key'] = converters['Key'].to_model(messages, 'key', message.key)

    # Other fields
    for field in fields:
        property = model._properties[field]
        value = getattr(message, field)

        converter = converters[property.__class__]

        if value and converter:
            value = converter.to_model(message, field, value)
            values[field] = value

    if inspect.isclass(model):
        return model(**values)
    else:
        model.populate(**values)
        return model


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

    # Add in the key field.
    field_dict = {
        'key': converters['Key'].to_field(Model, 'key', 1)
    }

    # Add all other fields.
    for count, name in enumerate(field_names, start=2):
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
