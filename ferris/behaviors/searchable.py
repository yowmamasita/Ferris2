from ferris.core.ndb import Behavior
from ferris.components.search import index, unindex


class Searchable(Behavior):
    def after_put(self, instance):
        index(instance)

    def before_delete(self, key):
        unindex(key)
