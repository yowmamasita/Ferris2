import unittest
import json
import datetime
from lib import FerrisTestCase
from ferris.core.json_util import DatastoreEncoder, DatastoreDecoder
from ferris.core import scaffolding
from ferris.core.handler import Handler
from ferris.core.ndb import Model, ndb
from ferris.components.json import Json
from ferris.components.rest_api import RestApi


class RestWidget(Model):
    name = ndb.StringProperty()
    datetime = ndb.DateTimeProperty()
    ref = ndb.KeyProperty()


@scaffolding.scaffold
class RestWidgets(Handler):
    prefixes = ['api']
    components = [RestApi, Json]
    Model = RestWidget

    @scaffolding.scaffold
    def api_list(self):
        pass

    @scaffolding.scaffold
    def api_add(self):
        pass

    @scaffolding.scaffold
    def api_view(self, id):
        pass

    @scaffolding.scaffold
    def api_edit(self, id):
        pass

    @scaffolding.scaffold
    def api_delete(self, id):
        pass


class TestRestApi(FerrisTestCase):
    def setUp(self):
        super(TestRestApi, self).setUp()
        RestWidgets.build_routes(self.testapp.app.router)

    def testList(self):
        RestWidget(name='widget1').put()
        RestWidget(name='widget2').put()

        r = self.testapp.get('/api/rest_widgets').json

        self.assertEqual(len(r['items']), 2)
        self.assertEqual(r['itemCount'], 2)
        self.assertEqual(r['items'][0]['name'], 'widget1')

    def testView(self):
        ins = RestWidget(name='widget1')
        ins.put()

        r = self.testapp.get('/api/rest_widgets/:%s' % ins.key.urlsafe())

        self.assertEqual(r.body, json.dumps(ins, cls=DatastoreEncoder))

    def testAdd(self):
        ins = RestWidget(
            name='test widget',
            datetime=datetime.datetime.utcnow(),
            ref=ndb.Key('Random', 1))

        json_ins = json.dumps(ins, cls=DatastoreEncoder)

        r = self.testapp.post('/api/rest_widgets', json_ins,
            headers={'Content-Type': 'application/json'})

        remote_ins = json.loads(r.body, cls=DatastoreDecoder)
        self.assertEqual(remote_ins.name, ins.name)
        self.assertEqual(remote_ins.ref, ins.ref)
        self.assertEqual(remote_ins.datetime.utctimetuple(), ins.datetime.utctimetuple())

    def testEdit(self):
        ins = RestWidget(
            name='test widget',
            datetime=datetime.datetime.utcnow(),
            ref=ndb.Key('Random', 1))

        ins.put()

        ins.name = 'Updated name'
        ins.datetime += datetime.timedelta(days=60)
        ins.ref = ndb.Key('Random', 2)

        json_ins = json.dumps(ins, cls=DatastoreEncoder)

        r = self.testapp.put('/api/rest_widgets/:%s' % ins.key.urlsafe(), json_ins,
            headers={'Content-Type': 'application/json'})

        remote_ins = json.loads(r.body, cls=DatastoreDecoder)

        self.assertEqual(remote_ins.name, ins.name)
        self.assertEqual(remote_ins.ref, ins.ref)
        self.assertEqual(remote_ins.datetime.utctimetuple(), ins.datetime.utctimetuple())

    def testDelete(self):
        ins = RestWidget(name='test widget')
        ins.put()

        self.testapp.delete('/api/rest_widgets/:%s' % ins.key.urlsafe())

        self.assertEqual(RestWidget.query().count(), 0)
