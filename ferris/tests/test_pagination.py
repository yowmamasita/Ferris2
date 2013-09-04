import unittest
from lib import FerrisTestCase
from ferris.core import scaffold
from ferris.core.controller import Controller, route
from ferris.core.ndb import Model, ndb
from ferris.components import pagination, search
from ferris.behaviors import searchable
from ferris.core import messages


class Widget(Model):
    class Meta:
        behaviors = (searchable.Searchable,)

    name = ndb.StringProperty()


class Widgets(Controller):
    class Meta:
        prefixes = ('api',)
        components = (scaffold.Scaffolding, pagination.Pagination, messages.Messaging, search.Search)
        pagination_limit = 10
        Model = Widget

    list = scaffold.list
    api_list = scaffold.list

    @route
    def api_search(self):
        self.components.search()


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

    def testApiList(self):
        r = self.testapp.get('/api/widgets')
        assert '10' in r
        assert '11' not in r

        assert len(r.json['items']) == 10
        assert r.json['count'] == 10
        assert r.json['limit'] == 10
        assert r.json['next_page']
        assert r.json['page'] == 1
        assert 'previous_page' not in r.json

        r = self.testapp.get(r.json['next_page'])
        assert '11' in r
        assert 'previous_page' in r.json
        assert r.json['page'] == 2

    # def testSearchList(self):
    #     r = self.testapp.get('/api/widgets/search')
    #     assert '10' in r

    #     assert len(r.json['items']) == 10
    #     assert r.json['count'] == 10
    #     assert r.json['limit'] == 10
    #     assert r.json['next_page']

    #     r = self.testapp.get(r.json['next_page'])
    #     print r
    #     assert '11' in r
