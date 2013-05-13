Views
=====

Template Rendering
------------------

Handler contains a bit of logic to make rendering templates easier. By default, returning ``None`` from an action will trigger automatic template rendering. You can easily pass data from the handler to the template and control how the handler finds its template.

View Context
~~~~~~~~~~~~

To provide data to the view use the :attr:`context` property:

    .. autoattribute:: Controller.context

For example::

    def list(self):
        self.context['band'] = "The Beatles"
        self.context['members'] = ['John', 'Paul', 'George', 'Ringo']

Determination
~~~~~~~~~~~~~

A Handler can automatically determine which template to use:

.. automethod:: Handler._get_template_name

If you're not serving up html, you can change the extension:

.. autoattribute:: Handler.template_ext

If you'd like to use a theme:

.. autoattribute:: Handler.theme

If you set ``template_name`` to the full path of the template that will be used instead of the result of :meth:`~Handler._get_template_name`. This allows you to use templates from other actions and even other handlers:

.. autoattribute:: Handler.template_name

For example::

    def list(self):
        self.template_name = 'shows/grid.html'


Rendering
~~~~~~~~~

By default, :attr:`auto_render` is enabled:

.. autoattribute:: Handler.auto_render

Of course, you can also manually render a template:

.. automethod:: Handler.render_template

For example::

    def list(self):
        return render_template('planets/earth.html')
