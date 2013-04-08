import unittest
from lib import FerrisTestCase
from ferris.core import scaffolding
from ferris.core.handler import Handler
from ferris.core.ndb import Model, ndb
from ferris.components.pagination import Pagination


class MegaWidget(Model):
    name = ndb.StringProperty()


@scaffolding.scaffold
class MegaWidgets(Handler):
    prefixes = ('admin',)
    components = (Pagination,)
    Model = MegaWidget
    paginate_limit = 5

    @scaffolding.scaffold
    def list(self):
        paginated = self.components.pagination.paginate()
        self.response.content_type = 'application/json'
        return self.json(self.template_vars)


class TestPagination(FerrisTestCase):
    def setUp(self):
        super(TestPagination, self).setUp()
        MegaWidgets.build_routes(self.testapp.app.router)

    def test(self):
        from pprint import pprint
        MegaWidget(name='Chihiro').put()
        MegaWidget(name='Haku').put()
        MegaWidget(name='Yubaba').put()
        MegaWidget(name='Zeniba').put()
        MegaWidget(name='Boh').put()
        MegaWidget(name='No-Face').put()
        MegaWidget(name='Kamajii').put()

        r = self.testapp.get('/mega_widgets')
        context = r.json

        pprint(context)

        assert len(context['mega_widgets']) == 5
