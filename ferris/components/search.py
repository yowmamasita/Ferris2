import logging
import datetime
from ferris.core import inflector
from google.appengine.api import search, users
from google.appengine.ext import ndb


class Search(object):
    """
    Provides a simple high-level interface to the App Engine Search API.
    """

    def __init__(self, handler):
        self.handler = handler

    def search(self, index=None):
        """
        Searches using the provided index (or an automatically determine one).

        Expects the search query to be in the ``query`` request parameter.

        Also takes care of setting pagination information if the :class:`pagination component <ferris.components.pagination.Pagnation>` is present.
        """
        Model = self.handler.Model
        limit = 50
        if hasattr(self.handler, 'paginate_limit'):
            limit = self.handler.paginate_limit

        try:
            query_string = self.handler.request.params.get('query', '')

            cursor = self.handler.request.params.get('cursor', None)
            if cursor:
                cursor = search.Cursor(web_safe_string=cursor)
            else:
                cursor = search.Cursor()

            options = search.QueryOptions(
                limit=limit,
                ids_only=True,
                cursor=cursor)
            query = search.Query(query_string=query_string, options=options)

            if not index:
                if hasattr(Model, 'get_search_index'):
                    index = Model.get_search_index()
                elif hasattr(Model, 'search_index_name'):
                    index = Model.search_index_name
                else:
                    index = 'auto_ix_%s' % Model._get_kind()
            index = search.Index(name=index)

            logging.debug("Searching %s with \"%s\" and cursor %s" % (index.name, query.query_string, cursor.web_safe_string))
            index_results = index.search(query)

            if issubclass(Model, ndb.Model):
                results = ndb.get_multi([ndb.Key(urlsafe=x.doc_id) for x in index_results])
                results = [x for x in results if x]
            else:
                results = Model.get([x.doc_id for x in index_results])
                Model.prefetch_references(results)

            if index_results.cursor:
                self.handler.set(paging={
                    'limit': limit,
                    'cursor': cursor.web_safe_string,
                    'next_cursor': str(index_results.cursor.web_safe_string)})

        except (search.Error, search.query_parser.QueryException):
            results = []
            self.handler.set(error=True)

        self.handler.set(query_string=query_string)
        self.handler.set(inflector.pluralize(self.handler.name), results)

        return results


def index(instance, only=None, exclude=None, index=None, callback=None):
    """
    Adds an instance of a Model into full-text search.

    :param instance: an instance of ndb.Model
    :param list(string) only: If provided, will only index these fields
    :param list(string) exclude: If provided, will not index any of these fields
    :param index: The name of the search index to use, if not provided one will be automatically generated
    :param callback: A function that will recieve (instance, fields), fields being a map of property names to search.xField instances.

    This is usually done in :meth:`Model.after_put <ferris.core.ndb.Model.after_put>`, for example::

        def after_put(self):
            index(self)

    """

    if only:
        props = only
    else:
        props = instance._properties.keys()
        if exclude:
            props = [x for x in props if x not in exclude]

    if not index:
        index = 'auto_ix_%s' % instance.key.kind()
    index = search.Index(name=index)

    fields = {}
    for prop_name in props:
        if not hasattr(instance, prop_name):
            continue

        val = getattr(instance, prop_name)
        field = None

        if isinstance(instance._properties[prop_name], ndb.BlobProperty) and not isinstance(instance._properties[prop_name], (ndb.StringProperty, ndb.TextProperty)):
            continue
        if isinstance(val, basestring):
            field = search.TextField(name=prop_name, value=val)
        elif isinstance(val, datetime.datetime):
            field = search.DateField(name=prop_name, value=val.date())
        elif isinstance(val, datetime.date):
            field = search.DateField(name=prop_name, value=val)
        elif isinstance(val, users.User):
            field = search.TextField(name=prop_name, value=unicode(val))
        elif isinstance(val, bool):
            val = 'true' if val else 'false'
            field = search.AtomField(name=prop_name, value=val)
        elif isinstance(val, (float, int, long)):
            field = search.NumberField(name=prop_name, value=val)
        else:
            logging.debug('Property %s couldn\'t be added because it\'s a %s' % (prop_name, type(val)))

        if field:
            fields[prop_name] = field

    if callback:
        callback(instance=instance, fields=fields)

    try:
        fields = fields.values()
        doc = search.Document(doc_id=str(instance.key.urlsafe()), fields=fields)
        index.put(doc)
    except:
        logging.error("Adding model %s instance %s to the full-text index failed" % (instance.key.kind(), instance.key.id()))
        logging.error([(x.name, x.value) for x in fields])


def unindex(instance_or_key, index=None):
    """
    Removes a document from the full-text search.

    This is usually done in :meth:`Model.after_delete <ferris.core.ndb.Model.after_delete>`, for example::

        @classmethod
        def after_delete(cls, key):
            unindex(key)

    """
    if isinstance(instance_or_key, ndb.Model):
        instance_or_key = instance_or_key.key

    if not index:
        index = 'auto_ix_%s' % instance_or_key.kind()
    index = search.Index(name=index)

    index.delete(str(instance_or_key.urlsafe()))
