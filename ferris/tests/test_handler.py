from lib import FerrisTestCase
import wtforms
import json
from ferris.core.handler import Handler, route, route_with
from ferris.core.json_util import DatastoreEncoder
from google.appengine.ext import ndb


class TestModel(ndb.Model):
    field1 = ndb.StringProperty()
    field2 = ndb.StringProperty()


class TestForm(wtforms.Form):
    field1 = wtforms.TextField()
    field2 = wtforms.TextField()


class TestComponent(object):
    def __init__(self, handler):
        self.handler = handler

    def present(self):
        return 'si'


class TestHandler(Handler):
    prefixes = ['monster']
    components = [TestComponent]

    def list(self):
        return 'list'

    def view(self, id):
        return 'view'

    def add(self):
        return 'add'

    def edit(self, id):
        return 'edit'

    def delete(self, id):
        return 'delete'

    def monster_list(self):
        return 'monster_list'

    @route
    def monkey(self, id):
        return 'monkey-%s' % id

    @route
    def monster_monkey(self, id):
        return 'monster_monkey-%s' % id

    @route_with(template='/test_handler/monet')
    def degas(self):
        return 'degas'

    @route
    def urls(self):
        assert self.uri(action='list') == '/test_handler'
        assert self.uri(prefix='monster', action='list') == '/monster/test_handler'
        assert self.uri(action='edit', id=12) == '/test_handler/12/edit'
        assert self.uri('test_handler-list') == '/test_handler'
        assert self.uri('monster-test_handler-list') == '/monster/test_handler'
        assert self.uri('test_handler-monkey', id=13) == '/test_handler/monkey/13'

        return 'success'

    @route
    def component(self):
        return self.components.test_component.present()

    @route
    def numeric(self):
        return 401

    @route
    def self_response(self):
        self.response.status_int = 401
        self.response.body = 'lolidk'
        return self.response

    @route
    def do_redirect(self):
        return self.redirect(self.uri('test_handler-list'))

    @route
    def monster_template_names(self):
        return str(self._get_template_name())

    @route
    def form(self):
        form = TestForm()
        self.process_form_data(form)
        return str(form.data)


class HandlerTest(FerrisTestCase):
    def setUp(self):
        super(HandlerTest, self).setUp()
        TestHandler.build_routes(self.testapp.app.router)

    def testCrudRoutes(self):
        response = self.testapp.get('/test_handler')
        self.assertEqual(response.body, 'list')

        response = self.testapp.get('/test_handler/add')
        self.assertEqual(response.body, 'add')

        response = self.testapp.get('/test_handler/:abcd')
        self.assertEqual(response.body, 'view')

        response = self.testapp.get('/test_handler/:abcd/edit')
        self.assertEqual(response.body, 'edit')

        response = self.testapp.get('/test_handler/:abcd/delete')
        self.assertEqual(response.body, 'delete')

        response = self.testapp.get('/test_handler/12')
        self.assertEqual(response.body, 'view')

        response = self.testapp.get('/test_handler/12/edit')
        self.assertEqual(response.body, 'edit')

        response = self.testapp.get('/test_handler/12/delete')
        self.assertEqual(response.body, 'delete')

    def testRestRoutes(self):
        response = self.testapp.get('/test_handler')
        self.assertEqual(response.body, 'list')

        response = self.testapp.post('/test_handler')
        self.assertEqual(response.body, 'add')

        response = self.testapp.get('/test_handler/:abcd')
        self.assertEqual(response.body, 'view')

        response = self.testapp.put('/test_handler/:abcd')
        self.assertEqual(response.body, 'edit')

        response = self.testapp.delete('/test_handler/:abcd')
        self.assertEqual(response.body, 'delete')

        response = self.testapp.get('/test_handler/12')
        self.assertEqual(response.body, 'view')

        response = self.testapp.put('/test_handler/12')
        self.assertEqual(response.body, 'edit')

        response = self.testapp.delete('/test_handler/12')
        self.assertEqual(response.body, 'delete')

    def testPrefixRoutes(self):
        response = self.testapp.get('/monster/test_handler')
        self.assertEqual(response.body, 'monster_list')

    def testRouteDecorator(self):
        response = self.testapp.get('/test_handler/monkey/3')
        self.assertEqual(response.body, 'monkey-3')

        response = self.testapp.get('/monster/test_handler/monkey/3')
        self.assertEqual(response.body, 'monster_monkey-3')

    def testRouteWithDecorator(self):
        response = self.testapp.get('/test_handler/monet')
        self.assertEqual(response.body, 'degas')

    def testUrlGeneration(self):
        response = self.testapp.get('/test_handler/urls')
        self.assertEqual(response.body, 'success')

    def testComponents(self):
        response = self.testapp.get('/test_handler/component')
        self.assertEqual(response.body, 'si')

    def testReturnValues(self):
        response = self.testapp.get('/test_handler/numeric', status=401)

        response = self.testapp.get('/test_handler/self_response', status=401)
        self.assertEqual(response.body, 'lolidk')

        response = self.testapp.get('/test_handler/do_redirect', status=302)
        self.assertEqual(response.headers['Location'], 'http://localhost/test_handler')

    def testTemplateNames(self):
        response = self.testapp.get('/monster/test_handler/template_names')
        self.assertEqual(response.body, str(['test_handler/monster_template_names.html', 'test_handler/template_names.html']))

    def testProcessFormData(self):
        data = {'field2': u'f2', 'field1': u'f1'}
        response = self.testapp.post('/test_handler/form', data)
        self.assertEqual(response.body, str(data))

        data['field3'] = u'f3'
        response = self.testapp.post('/test_handler/form', data)
        self.assertNotEqual(response.body, str(data), 'Field3 should not be in data')

        data = json.dumps(data, cls=DatastoreEncoder)
        response = self.testapp.post('/test_handler/form', data, headers={'Content-Type': 'application/json'})
        self.assertTrue('f1' in response)
        self.assertTrue('f2' in response)

        ins = TestModel(field1='f1', field2='f2')
        data = json.dumps(ins, cls=DatastoreEncoder)
        response = self.testapp.post('/test_handler/form', data, headers={'Content-Type': 'application/json'})
        self.assertTrue('f1' in response)
        self.assertTrue('f2' in response)
