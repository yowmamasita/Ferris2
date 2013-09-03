import unittest
from lib import FerrisTestCase
from ferris.core import scaffold
from ferris.core.controller import Controller
from ferris.core.ndb import Model, ndb
from ferris.components import pagination


class Widget(Model):
    name = ndb.StringProperty()


class Widgets(Controller):
    class Meta:
        prefixes = ('api',)
        components = (scaffold.Scaffolding, pagination.Pagination)
        pagination_limit = 10
        Model = Widget

    list = scaffold.list
    view = scaffold.view
    add = scaffold.add
    edit = scaffold.edit
    delete = scaffold.delete


class TestPagination(FerrisTestCase):
    def setUp(self):
        super(TestPagination, self).setUp()
        Widgets._build_routes(self.testapp.app.router)

        # Create a few pages of widgets
        for i in range(1, 50):
            Widget(name=str(i)).put()

    def testNormalList(self):
        r = self.testapp.get('/widgets')
        assert '11' not in r

        _, cursor, _ = Widget.query().fetch_page(10)

        assert cursor
        r = self.testapp.get('/widgets?cursor=%s' % cursor.urlsafe())
        assert '11' in r

