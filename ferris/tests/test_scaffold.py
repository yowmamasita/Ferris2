import unittest
from lib import FerrisTestCase
from ferris.core import scaffold
from ferris.core.controller import Controller
from ferris.core.ndb import Model, ndb


class Widget(Model):
    name = ndb.StringProperty()


class Widgets(Controller):
    class Meta:
        prefixes = ('admin',)
        components = (scaffold.Scaffolding,)
        Model = Widget

    list = scaffold.list
    view = scaffold.view
    add = scaffold.add
    edit = scaffold.edit


class _TestScaffoldInjection(unittest.TestCase):

    def testAttributes(self):
        self.assertTrue(hasattr(Widgets, 'scaffold'))
        self.assertTrue(hasattr(Widgets, 'ModelForm'))
        self.assertTrue(hasattr(Widgets.scaffold, 'display_properties'))
        self.assertTrue(hasattr(Widgets, 'modelform'))
        self.assertTrue(hasattr(Widgets, '_scaffold_on_before_render'))
        self.assertTrue(hasattr(Widgets, '_determine_display_properties'))
        self.assertTrue(hasattr(Widgets, 'get_modelform'))
        self.assertTrue(hasattr(Widgets, 'flash'))
        self.assertEqual(Widgets.dispatch.im_func.__module__, 'ferris.core.scaffolding.wrap')

    def testAutoAdmin(self):
        from ferris.core.autoadmin import admin_handlers
        self.assertTrue(Widgets in admin_handlers)

    def testMethods(self):
        self.assertEqual(Widgets.list.im_func.__module__, 'ferris.core.scaffolding.scaffolding')
        self.assertEqual(Widgets.add.im_func.__module__, 'ferris.core.scaffolding.scaffolding')
        self.assertEqual(Widgets.view.im_func.__module__, 'ferris.core.scaffolding.scaffolding')
        self.assertEqual(Widgets.edit.im_func.__module__, 'ferris.core.scaffolding.scaffolding')
        self.assertEqual(Widgets.delete.im_func.__module__, 'ferris.core.scaffolding.scaffolding')
        self.assertEqual(Widgets.admin_list.im_func.__module__, 'ferris.core.scaffolding.scaffolding')


class TestScaffoldBehavior(FerrisTestCase):
    def setUp(self):
        super(TestScaffoldBehavior, self).setUp()
        Widgets._build_routes(self.testapp.app.router)

    def testCrudMethods(self):
        self.testapp.get('/widgets/add')
        self.testapp.post('/widgets/add', {'name': 'Inigo Montoya'})
        self.assertEqual(Widget.query().count(), 1)

        r = self.testapp.get('/widgets')
        self.assertTrue('Inigo Montoya' in r)

        id = Widget.query().fetch(1)[0].key.urlsafe()

        r = self.testapp.get('/widgets/:%s' % id)
        self.assertTrue('Inigo Montoya' in r)

        r = self.testapp.get('/widgets/:%s/edit' % id)
        self.assertTrue('Inigo Montoya' in r)
        r.form['name'] = 'Dread Pirate Roberts'
        r = r.form.submit()

        r = self.testapp.get('/widgets/:%s' % id)
        self.assertTrue('Dread Pirate Roberts' in r)

        # r = self.testapp.get('/widgets/:%s/delete' % id)
        # self.assertEqual(Widget.query().count(), 0)

    def _testRestMethods(self):
        self.testapp.post('/widgets', {'name': 'Inigo Montoya'})
        self.assertEqual(Widget.query().count(), 1)

        r = self.testapp.get('/widgets')
        self.assertTrue('Inigo Montoya' in r)

        id = Widget.query().fetch(1)[0].key.urlsafe()

        self.testapp.put('/widgets/:%s' % id, {'name': 'Dread Pirate Roberts'}, {'Content-type': 'application/x-www-form-urlencoded'})
        r = self.testapp.get('/widgets/:%s' % id)
        self.assertTrue('Dread Pirate Roberts' in r)

        r = self.testapp.delete('/widgets/:%s' % id)
        self.assertEqual(Widget.query().count(), 0)
