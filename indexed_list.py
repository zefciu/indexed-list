import abc
from collections.abc import MutableSequence, Mapping

class Index():
    """An abstract index on an IndexedList."""

    def __init__(self):
        """Set the name."""
        self._name = None
        self._dict = {}
        super(Index, self).__init__()

    def bind_name(self, name):
        """Set the name."""
        if self._name is not None:
            # Shouldn't happen if using recommended semantics
            raise ValueError(
                'Trying to set the same index object on two lists'
            )
        self._name = name

    @abc.abstractmethod
    def process_item(self, item):
        """The method to process the list item in order to get index key."""

    @abc.abstractmethod
    def prepare_add(self, item):
        """Raise exception if an item can't be added to this index."""

    @abc.abstractmethod
    def add(self, item):
        """Add an item to this index."""

    @abc.abstractmethod
    def remove(self, item):
        """Remove an item to this index."""


class BoundIndex(Mapping):
    """An index bound to a list instance."""

    def __init__(self, index, list_):
        self._index = index
        self._list = list

    def __getitem__(self, key):
        return self._dict[key]

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict)

    def prepare_add(self, item):
        self._index.prepare_add(item)

    def add(self, item):
        self._index.add(item)

    def remove(self, item):
        self._index.remove(item)


class UniqueIndex(Index):
    """An index that ensures unique values."""

    def prepare_add(self, item):
        if self.process_item(item) in self._dict:
            raise ValueError('Value {0} already in index {1}.'.format(
                self.process_item(item), self._name
            ))

    def add(self, item):
        self._dict[self.process_item(item)] = item

    def remove(self, item):
        del self._dict[self.process_item(item)]

class MultiIndex(Index):
    """An index that enables multiple values and returns a list."""

    def prepare_add(self, item):
        return True

    def add(self, item):
        key = self.process_item(item)
        self.dict_.setdefault(key, [])
        self.dict_[key].append(item)

    def remove(self, item):
        key = self.process_item(item)
        self.dict_[key].remove(item)

class IndexedListMeta(abc.ABCMeta):
    """Metaclass for indexed lists."""

    def __init__(cls, clsname, bases, dict_):
        cls._indexes = {}
        for name, index in dict_.items():
            if not isinstance(index, Index):
                continue
            index.bind_name(name)
            cls._indexes[name] = index
        super(IndexedListMeta, cls).__init__(clsname, bases, dict_)

class KeyIndex(Index):
    """Index that accesses a key of an object"""

    def process_item(self, item):
        return item[self._name]

class UniqueKeyIndex(UniqueIndex, KeyIndex):
    """Unique index by dictionary key."""


class IndexedList(MutableSequence, metaclass = IndexedListMeta):

    def __init__(self):
        self._list = []
        self._indexes = {}
        for name, index in type(self)._indexes.items():
            self._indexes[name] = BoundIndex(index, self)
        super(IndexedList, self).__init__()

    def __len__(self):
        return len(self._list)

    def __getitem__(self, i):
        return self._list[i]

    def __setitem__(self, i, value):
        self.check(value)
        if i >= len(self._list):
            raise IndexError('list assignment index out of range')
        self.remove_from_indexes(self._list[i])
        self.add_to_indexes(value)
        self._list[i] = value

    def check(self, value):
        for index in self._indexes.values():
            index.prepare_add(value)

    def add_to_indexes(self, value):
        for index in self._indexes.values():
            index.add(value)

    def remove_from_indexes(self, value):
        for index in self._indexes.values():
            index.remove(value)

    def insert(self, i, value):
        self.check(value)
        self.add_to_indexes(value)
        self._list.insert(i, value)

    def __delitem__(self, i):
        self.remove_from_indexes(self._list[i])
        del self._list[i]


if __name__ == '__main__':
    class ListPeople(IndexedList):
        name = UniqueKeyIndex()
        surname = UniqueKeyIndex()

    l = ListPeople()
    l.append({'name': 'Szymon', 'surname': 'Pyżalski'})
