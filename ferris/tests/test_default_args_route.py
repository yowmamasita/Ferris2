from ferris.core.handler import Handler, route
from ferris.tests.lib import FerrisTestCase


class TestHandler(Handler):

    prefixes = ['pre']

    @route
    def method(self, a=0, b=0, c=0):
        return 'method_' + '/'.join([str(i) for i in (a, b, c)])

    @route
    def pre_method(self, a=0, b=0, c=0):
        return 'pre_method_' + '/'.join([str(i) for i in (a, b, c)])

    @route
    def urls(self):
        assert self.uri('test_handler-method') == '/test_handler/method'
        assert self.uri('test_handler-method', a=1) == '/test_handler/method/1'
        assert self.uri('test_handler-method', a=1, b=2) == '/test_handler/method/1/2'
        assert self.uri('test_handler-method', a=1, b=2, c=3) == '/test_handler/method/1/2/3'
        return 'done'

    @route
    def prefixed_urls(self):
        assert self.uri('pre-test_handler-method') == '/pre/test_handler/method'
        assert self.uri('pre-test_handler-method', a=1) == '/pre/test_handler/method/1'
        assert self.uri('pre-test_handler-method', a=1, b=2) == '/pre/test_handler/method/1/2'
        assert self.uri('pre-test_handler-method', a=1, b=2, c=3) == '/pre/test_handler/method/1/2/3'
        return 'done'


class DefaultArgsTest(FerrisTestCase):

    def setUp(self):
        super(DefaultArgsTest, self).setUp()
        TestHandler.build_routes(self.testapp.app.router)

    def test_default_args(self):
        response = self.testapp.get('/test_handler/method')
        self.assertEqual(response.body, 'method_0/0/0')

        response = self.testapp.get('/test_handler/method/1')
        self.assertEqual(response.body, 'method_1/0/0')

        response = self.testapp.get('/test_handler/method/1/2')
        self.assertEqual(response.body, 'method_1/2/0')

        response = self.testapp.get('/test_handler/method/1/2/3')
        self.assertEqual(response.body, 'method_1/2/3')

    def test_prefixed_default_args(self):
        response = self.testapp.get('/pre/test_handler/method')
        self.assertEqual(response.body, 'pre_method_0/0/0')

        response = self.testapp.get('/pre/test_handler/method/1')
        self.assertEqual(response.body, 'pre_method_1/0/0')

        response = self.testapp.get('/pre/test_handler/method/1/2')
        self.assertEqual(response.body, 'pre_method_1/2/0')

        response = self.testapp.get('/pre/test_handler/method/1/2/3')
        self.assertEqual(response.body, 'pre_method_1/2/3')

    def test_uri_building(self):

        response = self.testapp.get('/test_handler/urls')
        self.assertEqual(response.body, 'done')

        response = self.testapp.get('/test_handler/prefixed_urls')
        self.assertEqual(response.body, 'done')
