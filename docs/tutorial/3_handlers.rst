Handling Requests With Controllers
==================================

Now that we can store data we're going to need a way to serve it to our users.

First, we'll take a short detour to discuss one of the core parts of Ferris: Controller.

Ferris handles HTTP requests with Controllers. Controllers are classes that contain a collection of *actions*. Actions are methods that can be invoked via HTTP. Controllers invoke views that can render template files or serve content such as JSON, ProtoRPC Message, and Blobstore Blobs.

.. note::
    Controllers are usually UpperCamelCase plural nouns and are tied to a particular model (i.e. Posts controller for the Post model, Daleks controller for the Dalek model). However, there are cases where you'll make exceptions, such as handlers that don't have a model or those that have multiple models.


Saying Hello
------------

Here's a rather simple controller to get your feet wet. We'll just say hello.

Create ``app/conrollers/hello.py``::

    from ferris import Controller


    class Hello(Controller):

        def list(self):
            return "Hello, is it me you're looking for?"


If you open http://localhost:8080/hello, you should see a friendly welcome.

.. note::
    A dev server restart might be required at this point. If examples do not work immediately for you, it's recommended to try a server restart first.

You can also accept input from GET or POST, if you'd like.

Modify our list action::

    def list(self):
        return "Hello, %s" % self.request.params['name']

Now try to open http://localhost:8080/hello?name=Doctor

You may have noticed that ``Hello.list`` gets automatically routed to `/hello`. Ferris will automatically route the actions ``list``, ``add``, ``edit``, ``view``, and ``delete``. These actions, as well as other action names, will be discussed in the Routing and Scaffolding sections.


Views & Templates
-----------------

You're not limited to returning simple strings from your controller. Ferris has a flexible view infrastructure. The default view provides the fantastic `Jinja2 template engine <http://jinja.pocoo.org/>`_.

Let's create a template for our action at ``app/templates/hello/list.html``::

    {% extends 'layouts/default.html' %}

    {% block layout_content %}
        <h1>Hello, {{who}}</h1>
    {% endblock %}

The syntax for Jinja2 can be a bit much to take in at once; I highly recommend checking out their excellent `documentation <http://jinja.pocoo.org/docs/templates/>`_. The gist of this is that we are going to use the default layout and add some content that says hello.

Now we just need to modify our list action::

    def list(self):
        self.context['who'] = self.request.params['name']

Notice here that we have to explicitly set the ``who`` variable in the template using ``self.context``. This our view context and everything in this dictionary is made available inside of the template.

If you load up http://localhost:8080/hello?name=Doctor, you should see a slightly prettier greeting.

.. note::
    Ferris expects the template to be located at ``app/templates/controller/action.html``. So the template for this action is at ``app/templates/hello/list.html``. You can manually specify the template location by setting ``self.meta.view.template_name`` in your action.

Routing
-------

You've already seen how ``Hello.list`` gets automatically routed to `/hello`.
Ferris will implicitly route the following actions to these urls:

+---------+---------------------------+
|Action   | URL                       |
+=========+===========================+
|list     |  /controller              |
+---------+---------------------------+
|add      |  /controller/add          |
+---------+---------------------------+
|view     |  /controller/<key>        |
+---------+---------------------------+
|edit     |  /controller/<key>/edit   |
+---------+---------------------------+
|delete   |  /controller/<key>/delete |
+---------+---------------------------+

Notice the `controller` section of the url.  The controller's name is passed to ``inflector.underscore``. For example, `Posts` becomes `posts` and `FlyingMonsters` becomes `flying_monsters`.

But what about actions that are not part of this list? You have to explicitly route them using the ``route`` decorator.

Modify our imports in the Hello handler::

    from ferris import Controller, route

Add the following action to our Hello controller::

    @route
    def custom(self):
        return "Something, indeed."

Go ahead and open http://localhost:8080/hello/custom.

You'll notice that Ferris determines the url using the template ``/handler/action``.

Ferris can also put parameters in the url as well. Let's modify our custom function::

    @route
    def custom(self, text):
        return "%s, indeed." % text

Opening http://localhost:8080/hello/custom gives us a 404.  We must pass some text to the ``custom`` action.

Open http://localhost:8080/hello/custom/Yes. You should see "Yes, indeed."  The last argument in this url is passed as a parameter to the ``custom`` action.

You may have multiple mapped arguments::

    @route
    def custom(self, text, person):
        return "%s, %s, indeed." % (text, person)

Try with http://localhost:8080/hello/custom/Yes/sir

.. note::
    You can set your own URLs for methods using the ``route_with`` decorator.


Next
----

Continue with :doc:`4_scaffolding`
