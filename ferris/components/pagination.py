from ferris.core import inflector
from google.appengine.ext import db, ndb
from google.appengine.datastore.datastore_query import Cursor
import logging


class Pagination(object):
    """
    Provides automatic pagination of ``db.Query`` and ``ndb.Query`` objects.

    Automatically happens for any ``list`` actions but can also be manually invoked
    via :meth:`paginate`.

    In automatic operation, it looks for a template variable with the underscored pluralized version of the Handler's name. For instance, if you're on ``Pages`` it looks for the template variable ``pages``.
    """

    def __init__(self, handler):
        self.handler = handler
        self.handler.events.after_dispatch += self.after_dispatch_callback.__get__(self)

    def paginate(self, query_or_var_name=None):
        """
        Paginates a query and sets up the appropriate template variables.

        Uses ``handler.paginate_limit`` to determine how many items per page, or defaults to 10 if omitted.

        Sets the ``paging`` template variable to a dictionary like::

            {
                "cursor": "abc...",
                "next_cursor": "nzb...",
                "limit": 10
            }

        Returns the data, and if ``query_or_var_name`` is a string, sets that template variable.
        """
        if not query_or_var_name:
            query_or_var_name = inflector.pluralize(self.handler.name)
        if isinstance(query_or_var_name, basestring):
            query = self.handler.get(query_or_var_name)
        else:
            query = query_or_var_name

        if not isinstance(query, (db.Query, ndb.Query)):
            logging.debug('Unable to paginate, query is not a Query or ndb Query object')
            return

        cursor = self.handler.request.params.get('cursor', None)

        default_limit = 10

        if hasattr(self.handler, 'paginate_limit'):
            default_limit = self.handler.paginate_limit

        limit = int(self.handler.request.params.get('limit', default_limit))

        if hasattr(self.handler, 'max_paginate_limit'):
            if limit > self.handler.max_paginate_limit:
                limit = self.handler.max_paginate_limit

        if isinstance(query, db.Query):
            data = self.paginate_db(query, cursor, limit)
        elif isinstance(query, ndb.Query):
            data = self.paginate_ndb(query, cursor, limit)

        if isinstance(query_or_var_name, basestring):
            self.handler.set(query_or_var_name, data)
        else:
            self.handler.set(inflector.pluralize(self.handler.name), data)

        return data

    def paginate_db(self, query, cursor, limit):

        if cursor:
            query.with_cursor(cursor)

        data = query.fetch(limit)
        next_cursor = query.cursor()

        if len(data) < limit:
            next_cursor = ''
        else:
            # Hack alert!  Fetch one more result to see if this is the end of the results.
            # (Prevents potential blank last page.)
            query.with_cursor(next_cursor)
            if not query.fetch(1):
                next_cursor = ''

        self.handler.set('paging', {
            'cursor': cursor,
            'next_cursor': next_cursor,
            'limit': limit
        })

        return data

    def paginate_ndb(self, query, cursor, limit):
        if cursor:
            cursor = Cursor(urlsafe=cursor)

        data, next_cursor, more = query.fetch_page(limit, start_cursor=cursor)

        self.handler.set('paging', {
            'cursor': cursor.urlsafe() if cursor else '',
            'next_cursor': next_cursor.urlsafe() if more else '',
            'limit': limit
        })

        return data

    def after_dispatch_callback(self, response, *args, **kwargs):
        if not 'list' in self.handler.action:  # checks for list and any prefixed lists
            return
        self.paginate()
