Extras
======

At this point our application is complete and tested. At this point you can dive right in to the User's Guide, but there are a few extra things we can add to further demonstrate some more of Ferris' capabilities.


Pagination
----------

Ferris uses *Components* as a way of organizing commonly used functionality for controllers. Ferris comes with a handful of built-in components and includes one for automatic pagination for list methods.

It's pretty easy to use. First import it::

    from ferris.components.pagination import Pagination

Then add it to our controller's Meta component list and set the limit::

    class Posts(Controller):
        class Meta:
            components = (scaffold.Scaffolding, Pagination)
            paginate_limit = 5

If you open up http://localhost:8080/posts, you'll see that it will show no more than five posts. However, we don't currently have a way to move between pages. Luckily, the scaffolding macros can handle that.

Add this to our ``list.html`` template right before the end of the ``layout_content`` block::

    {{scaffold.next_page_link()}}

Now there is a paginator at the bottom of the page.


Behaviors and Searching
-----------------------

Similar to components, Ferris uses *Behaviors* as a way of organizing commonly used functionality for models. A useful behavior is the Searchable behavior.

First, we need to modify our model::

    from ferris.behaviors.searchable import Searchable

    def Post(BasicModel):
        class Meta:
            behaviors = (Searchable,)

.. note::
    Any posts created before you made this change will not be searchable until you edit and resave them.


Now we'll use the ``Search`` component in our controller to use the behavior::

    from ferris.components.search import Search

    class Posts(Controller):
        components = (scaffold.Scaffolding, Pagination, Search)


Now let's the ability to search to our ``list`` action::

    def list(self):
        if 'query' in self.request.params:
            self.context['posts'] = self.components.search()
        elif 'mine' in self.request.params:
            self.context['posts'] = self.Model.all_posts_by_user()
        else:
            self.context['posts'] = self.Model.all_posts()


Import the search macros into ``templates/posts/list.html``::

    {% import 'macros/search.html' as search with context %}


Finally, add these somewhere at the top of the inside of the ``layout_content`` block::

    {{search.search_filter(action='search')}}
    {{search.search_info()}}


Now when we visit http://localhost:8080/posts there should be a search box from which we can search through all posts.
