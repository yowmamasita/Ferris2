from google.appengine.ext import ndb
from ferris.core import inflector
from ferris.core.ndb import util as ndb_util


class Handler(object):
    """
    Scaffolding methods for handlers
    """

    def list(self):
        """
        Passes a list of all of the entities for the model to the template.

        If your handler is Cats, it does::

            self.set(cats=Cat.query())

        The list of entities is always at ``inflector.pluralize(self.name)``, so 'cats', 'posts', etc.
        """
        self.set(inflector.pluralize(self.name), ndb_util.list(self.Model))

    def view(self, id):
        """
        Passes a single entity by id to the template.

        If your handler is Cats, it does::

            self.set(cat=self.key_from_string(id).get())

        The entity is always at ``inflector.singularize(self.name)``, so 'cat', 'post', etc.
        """
        item = self.key_from_string(id).get()
        if item == None:
            return 404
        self.set(inflector.singularize(self.name), item)

    def add(self):
        """
        Displays a form for creating an entity and processes form submissions to create the entity.

        The form displayed is an instance of ``self.ModelForm``, created via ``self.get_modelform()`` and is exposed via the ``form`` template variable.

        If an item is saved, then the ``added_item`` template variable will be set.
        """
        self.get_modelform()
        if self.request.method != 'GET' and self.scaffold.should_save:
            if self.modelform.validate():

                self._delegate_event('scaffold_before_apply', handler=self, form=self.modelform, item=None)

                item = self.Model(**self.modelform.data)

                self._delegate_event('scaffold_before_save', handler=self, form=self.modelform, item=item)

                item.put()

                self._delegate_event('scaffold_after_save', handler=self, form=self.modelform, item=item)

                self.set('added_item', item)

                self.flash('The item was created successfully.', 'success')
                if self.should_redirect():
                    return self.redirect(self.uri(action='list'))

            else:
                self.flash('There were errors on the form, please correct and try again.', 'error')

        self.set('form', self.modelform)

    def edit(self, id):
        """
        Displays a form for editing an entity and processes form submissions to update the entity.

        The form displayed is an instance of ``self.ModelForm``, created via ``self.get_modelform()`` and is exposed via the ``form`` template variable.

        If an item is saved, then the ``edited_item`` template variable will be set.
        """
        item = self.key_from_string(id).get()
        if item == None:
            return 404

        self.get_modelform(obj=item)

        if self.request.method != 'GET' and self.scaffold.should_save:
            if self.modelform.validate():

                self._delegate_event('scaffold_before_apply', handler=self, form=self.modelform, item=None)

                self.modelform.populate_obj(item)

                self._delegate_event('scaffold_before_save', handler=self, form=self.modelform, item=item)

                item.put()

                self._delegate_event('scaffold_after_save', handler=self, form=self.modelform, item=item)

                self.set('edited_item', item)

                self.flash('The item was saved successfully.', 'success')

                if self.should_redirect():
                    return self.redirect(self.uri(action='list'))
            else:
                self.flash('There were errors on the form, please correct and try again.', 'error')

        self.set(inflector.singularize(self.name), item)
        self.set('form', self.modelform)

    def delete(self, id):
        """
        Deletes an existing entity

        Basically does::

            self.key_from_string(id).delete()

        """
        item = self.key_from_string(id)
        if item == None:
            return 404

        self._delegate_event('scaffold_before_delete', handler=self, form=self.modelform, item=item)
        item.delete()
        self._delegate_event('scaffold_after_delete', handler=self, form=self.modelform, item=None)

        self.flash('The item was deleted successfully.', 'success')

        if self.should_redirect():
            return self.redirect(self.uri(action='list'))
        else:
            self.set('data', True)
