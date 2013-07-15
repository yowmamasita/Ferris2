from lib import FerrisTestCase
from ferris.core import scaffolding
from ferris.core.handler import Handler
from ferris.core.ndb import Model, ndb
from ferris.components.pagination import Pagination


class SuperMegaWidget(Model):
    name = ndb.StringProperty()


@scaffolding.scaffold
class SuperMegaWidgets(Handler):
    prefixes = ('admin',)
    components = (Pagination,)
    Model = SuperMegaWidget
    paginate_limit = 5

    @scaffolding.scaffold
    def list(self):
        self.components.pagination.paginate()
        self.response.content_type = 'application/json'
        self._scaffold_on_before_render(self)
        return self.json(self.template_vars)


class TestPagination(FerrisTestCase):
    def setUp(self):
        super(TestPagination, self).setUp()
        SuperMegaWidgets.build_routes(self.testapp.app.router)

    def test(self):
        SuperMegaWidget(name='Chihiro').put()
        SuperMegaWidget(name='Haku').put()
        SuperMegaWidget(name='Yubaba').put()
        SuperMegaWidget(name='Zeniba').put()
        SuperMegaWidget(name='Boh').put()
        SuperMegaWidget(name='No-Face').put()
        SuperMegaWidget(name='Kamajii').put()

        r = self.testapp.get('/super_mega_widgets')
        context = r.json

        assert len(context['super_mega_widgets']) == 5
