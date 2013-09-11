import logging
import datetime
import calendar
from ferris.core import inflector
from google.appengine.api import search, users, memcache
from google.appengine.ext import ndb


class Search(object):
    """
    Provides a simple high-level interface to the App Engine Search API.
    """

    def __init__(self, controller):
        self.controller = controller

    def _get_index(self):
        if hasattr(self.controller.meta, 'search_index'):
            return self.controller.meta.search_index
        if hasattr(self.controller.meta, 'Model'):
            Model = self.controller.meta.Model
            if hasattr(Model.Meta, 'search_index'):
                return Model.Meta.search_index[0] if isinstance(Model.Meta.search_index, (list, tuple)) else Model.Meta.search_index
            return 'auto_ix_%s' % Model._get_kind()
        raise ValueError('No search index could be determined')

    def search(self, index=None, query=None, limit=None, cursor=None, options=None):
        """
        Searches using the provided index (or an automatically determine one).

        Expects the search query to be in the ``query`` request parameter.

        Also takes care of setting pagination information if the :class:`pagination component <ferris.components.pagination.Pagnation>` is present.
        """

        index = index if index else self._get_index()
        query_string = query if query else self.controller.request.params.get('query', '')
        options = options if options else {}

        if 'pagination' in self.controller.components:
            cursor, limit = self.controller.components.pagination.get_pagination_params(cursor, limit)

        try:

            cursor = search.Cursor(web_safe_string=cursor) if cursor else search.Cursor()

            options_params = dict(
                limit=limit,
                ids_only=True,
                cursor=cursor)

            options_params.update(options)

            query = search.Query(query_string=query_string, options=search.QueryOptions(**options_params))
            index = search.Index(name=index)
            index_results = index.search(query)

            results = ndb.get_multi([ndb.Key(urlsafe=x.doc_id) for x in index_results])
            results = [x for x in results if x]

            if 'pagination' in self.controller.components:
                self.controller.components.pagination.set_pagination_info(
                    current_cursor=cursor.web_safe_string if cursor else None,
                    next_cursor=index_results.cursor.web_safe_string if index_results.cursor and results else None,
                    limit=limit,
                    count=len(results))

        except (search.Error, search.query_parser.QueryException) as e:
            results = []
            self.controller.context['search_error'] = e

        self.controller.context['search_query'] = query_string
        self.controller.context['search_results'] = results

        if hasattr(self.controller, 'scaffold'):
            self.controller.context[self.controller.scaffold.plural] = results

        return results

    __call__ = search

