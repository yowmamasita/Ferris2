Scaffolding
===========

Now that we understand controllers we're going to create one for Posts.

The Posts handler should have the following actions:

* List of all posts
* List of my posts
* View of a single post
* Form to add a new post
* Form to edit an existing post
* Action to delete an existing post

With what we've learned already you could write all of these actions yourself.
Fortunately, the bulk of this functionality is already provided to you by Ferris via
the Scaffold.

Admin Scaffolding
-----------------

To demonstrate the full extent of what scaffolding can do, we're going to use the scaffold to create an admin interface for Posts.

Create ``app/handlers/posts.py``::

    from ferris Controller, scaffold


    class Posts(EasyHandler):
        class Meta:
            prefixes = ('admin',)
            components = (scaffold.Scaffolding,)

        admin_list = scaffold.list
        admin_view = scaffold.view
        admin_add = scaffold.add
        admin_edit = scaffold.edit
        admin_delete = scaffold.delete


Open http://localhost:8080/admin/posts in your browser. You'll see that you now have a complete interface for managing posts.

Let's walk through what we did:

* We created our Controller as usual, however we now have a ``Meta`` internal class. This is used to configure aspects of the controller.

* In our ``Meta`` configuration, we're specifying that we'd like to have an `admin` prefix. Prefixes allow us to have actions that live under a common prefix. For example, ``Posts.admin_custom`` becomes ``/admin/posts/custom``.Prefixes are discussed in detail in :doc:`../users_guide/routing`.

* We've also added the ``Scaffolding`` component to our ``Meta`` configuration. :doc:`../users_guide/components` augment controller functionality and the Scaffolding component takes care of a few things behind the scenes and allows you to use scaffold actions.

* Finally, we've added the suite of CRUD actions for the admin prefix and assigned them to their ``scaffold`` counterparts. This allows the scaffold to do all of logic for us.


Exploring the Scaffold
----------------------

Let's take a moment to explore the features that the admin scaffold provides us. Open http://localhost:8080/admin/posts and click 'Add' on the left navigation.

Here we see that a form has been automatically generated for the two fields in our Post model. Recall that we made the title property required. If we try to submit this form without putting anything in the title field, we'll see that we get a nicely formatted error.

Let's go ahead and create an actual post with a title and content.  Once we've submitted the form, we'll be redirected to the list. Our new post has appeared (if it hasn't appeared, refresh, the datastore is eventually consistent).

On the right side of our new Post there are three buttons: view, edit, and delete. These map to the actions ``admin_view``, ``admin_edit``, and ``admin_delete``.


Listing Posts
-------------

Our requirements state that we need to have two different lists: one of everyone's posts, and one of just our posts.
This means that we need to build on top of the scaffold's list action to conditionally add a filter.

First, create a few posts as one user and a few posts as another user using the Admin scaffold so that we have some
data to test with.

.. note::
    You can sign in as a different user via the url http://localhost:8080/_ah/login. You'll want keep being an admin so you can add posts via the Admin scaffold.


First, we want to add an non-prefixed ``list`` action so that we can access a list of everyone's posts at http://localhost:8080/posts. We can do that exactly like we did with ``admin_list``::

    list = scaffold.list


If we open up http://localhost:8080/posts we'll see that the scaffold does indeed list everyone's posts. However, they're in the wrong order. We need to modify it to use the ``all_posts`` method from our Posts class.

The scaffold's logic for list is very simple. It just sets the ``self.context['posts'`` to our Model's default query. We can easily set that variable ourselves using our ``all_posts()`` method. Remove the scaffolded list and add this::

    def list(self):
        self.context['posts'] = self.Model.all_posts()

Notice that we're still able to use the scaffold's template; all we had to do was set the ``posts`` template variable
and the scaffold knew what to display. You'll also notice that the scaffold automatically determined that the ``Posts`` controller uses the ``Post`` model and provides that via ``self.Model``.

With that in place all that's left is to add the ability for list to show just our posts using the ``all_posts_by_user`` method. Modify the ``list`` method again::

    def list(self):
        if 'mine' in self.request.params:
            self.context['posts'] = self.Model.all_posts_by_user()
        else:
            self.context['posts'] = self.Model.all_posts()

Now if we open up http://localhost:8080/posts?mine it will show only the posts for the currently logged-in user.


Adding Posts
------------

As nice as the admin scaffold is, we don't want to have to give every user admin rights to be able to add a new
post. We can give all users that ability by adding a non-prefixed ``add`` action just like we did intially with ``list``::

    add = scaffold.add

We'll just use the scaffold's behavior since it is perfectly acceptable for this case. If we open up http://localhost:8080/posts/add we'll see a form like the one in the admin scaffolding.


Editing Posts
-------------

At this point users can add posts but they can't edit any of the posts they've already created. Let's
add the ``edit`` using the scaffold like we did with ``add``::

    edit = scaffold.edit

At this point we have a problem: a user can edit *any* post, even those created by other users. While this could be slightly amusing, this behavior is undesirable. We need to add a check to make sure the user is editing a post that they created::

    def edit(self, key):
        post = self.util.decode_key(key).get()

        if post.created_by != self.user:
            return 403

        return scaffold.edit(self, key)

Let's walk through this:

* Notice that we needed to add the second parameter ``key`` to this action. ``key`` is needed for ``view``, ``edit``, and ``delete``.
* First, we need to get the post that the user is trying to edit. We need an ``ndb.Key`` in order to get the Post entity, and :meth:`self.util.decode_key <ferris.core.controller.Controller.util.decode_key>` does that for us.
* Second, we need to make sure the post was created by the same user that's logged in. :attr:`self.user <ferris.core.controller.Controller.user>` is always set to the currently logged in user.
* Returning ``403`` automatically creates a 403 Unauthorized response.
* If everything went well, we want to use the scaffold's behavior. We can simply dispatch to ``scaffold.edit``.

Now users may not edit posts that they did not create.  However, they are still allowed to edit one of their own posts without a problem.


Next
----

Continue with :doc:`5_templates`
