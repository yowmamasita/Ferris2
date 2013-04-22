import unittest
from lib import FerrisTestCase
from ferris.core import scaffold
from ferris.core.controller import Controller
from ferris.core.ndb import Model, ndb
from ferris.core.view import JsonView
from ferris.core.json_util import parse


class Widget(Model):
    name = ndb.StringProperty()


class Widgets(Controller):
    class Meta:
        prefixes = ('admin',)
        components = (scaffold.Scaffolding,)
        Model = Widget
        View = JsonView

    def list(self):
        self.context['widgets'] = [x.to_dict() for x in Widget.query()]


class TestJsonView(FerrisTestCase):
    def setUp(self):
        super(TestJsonView, self).setUp()
        Widgets._build_routes(self.testapp.app.router)

    def testRestMethods(self):
        Widget(name='Inigo Montoya').put()

        r = self.testapp.get('/widgets')

        r = parse(r.body)

        assert r[0]['name'] == 'Inigo Montoya'
