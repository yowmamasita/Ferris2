MVC in Ferris
=============

Ferris is similar to a lot of other MVC frameworks, though the terminology is slightly different:

* :doc:`models` handle the retrieval and storage of data in the App Engine Datastore. Models are simply Google App Engine `ndb.Model <https://developers.google.com/appengine/docs/python/ndb/>`_ subclasses with a few helper methods. Typically a most of the business logic is implemented in the model layer.
* :doc:`controllers` are responsible for responding to HTTP requests. Handlers are typically thin glue between models and views. Handlers have special methods called *actions* that are accessable via HTTP.
* :doc:`views` handle the presentation of data to the user. Views have access to data from that's retrived by the controller. Views can render html, json, or other representations.
* :doc:`routing` Maps urls to controller actions. This happens more or less automatically, but you can define custom routes and redirects.
* :doc:`scaffolding` can automatically create CRUD (create, read, update, delete) actions and templates for you, and can be customized and augmeneted to fit your needs.
* :doc:`templates` can be rendered by the views. Ferris uses the `jinja2 <http://jinja.pocoo.org/>`_ template engine.
* :doc:`forms` and :doc:`messages` are ways of representing data submitted by a client that's used to update a model. Forms are better suited for html pages, whereas messages are better suited for JSON consumers.
* :doc:`components` are a way of packaging common controller functionality into reusable classes.
* :doc:`behaviors` are a way of packaging common model functionality into reusable classes.
* :doc:`plugins` are a way of packaging entire parts of an application to be reused in another.
