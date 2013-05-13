Events
======

Ferris has a very simple global pubsub-style event system. Beyond the events emitted by :doc:`controllers`, there's also a way to globally emit and respond to events.

.. module:: ferris.core.events

listeners.py
------------

Inside of the ``app`` directory lives ``listeners.py``. This is where you can register global event listeners using ``on``:

.. autofunction:: on

For example, to switch the default template::

    @on('handler_before_startup')
    def before_startup(controller, *args, **kwargs):
        controller.meta.view.theme = 'corny'


All controller events are prefixed with ``controller_`` when broadcast globally.

Emitting Events
---------------

You can emit events on the global bus by using ``fire``:

.. autofunction:: fire

For example::

    @route
    def transmat(self, item):
        fire("item_transmat", item)
