"""
The indexed list module contains all definitions needed to
use IndexedList and Table
"""
import abc
import csv
import io
from collections import namedtuple, OrderedDict
from collections.abc import MutableSequence, Mapping

class Index(object):
    """An abstract index on an IndexedList."""

    def __init__(self):
        """Set the name."""
        self.name = None
        super(Index, self).__init__()

    def bind_name(self, name):
        """Set the name."""
        if self.name is not None:
            # Shouldn't happen if using recommended semantics
            raise ValueError(
                'Trying to set the same index object on two lists'
            )
        self.name = name

    @abc.abstractmethod
    def process_item(self, item):
        """The method to process the list item in order to get index key."""

    @abc.abstractmethod
    def prepare_add(self, item, skip=None):
        """Raise exception if an item can't be added to this index."""

    @abc.abstractmethod
    def add(self, item):
        """Add an item to this index."""

    @abc.abstractmethod
    def remove(self, item):
        """Remove an item to this index."""

    def process_result(self, result):
        """Process the dict_ item to be returned"""
        return result


class BoundIndex(Mapping):
    """An index bound to a list instance."""

    def __init__(self, index, list_):
        self._index = index
        self._list = list_
        self._dict = {}

    def __getattr__(self, key):
        # Return the attribute from the index. If it is a descriptor - rebind
        # it to the BoundIndex
        classattr = getattr(type(self._index), key, None)
        if classattr is not None:
            is_descriptor = hasattr(classattr, '__get__')
            is_datadescriptor = is_descriptor and hasattr(classattr, '__set__')
        else:
            is_descriptor = is_datadescriptor = False
        if is_datadescriptor:
            return classattr.__get__(self, type(self))
        try:
            return self._index.__dict__[key]
        except KeyError:
            if is_descriptor:
                return classattr.__get__(self, type(self))
            raise AttributeError('Index has no attribute {0}'.format(key))


    def __getitem__(self, key):
        return self._dict[key]

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict)


class UniqueIndex(Index):
    """An index that ensures unique values."""

    def prepare_add(self, item, skip=None):
        processed = self.process_item(item)
        if processed in self._dict:
            if self._list.index(self._dict[processed]) == skip:
                return
            raise ValueError('Value {0} already in index {1}.'.format(
                self.process_item(item), self.name
            ))

    def add(self, item):
        self._dict[self.process_item(item)] = item

    def remove(self, item):
        del self._dict[self.process_item(item)]

class MultiIndex(Index):
    """An index that enables multiple values and returns a list."""

    def prepare_add(self, item, skip=None):
        return True

    def add(self, item):
        key = self.process_item(item)
        self._dict.setdefault(key, [])
        self._dict[key].append(item)

    def remove(self, item):
        key = self.process_item(item)
        self._dict[key].remove(item)

    def process_result(self, result):
        # We create iterator to prevent accidental modification
        return iter(result)

class IndexedListMeta(abc.ABCMeta):
    """Metaclass for indexed lists."""

    def __init__(cls, clsname, bases, dict_):
        cls.indexes = {}
        for name, index in dict_.items():
            if not isinstance(index, Index):
                continue
            index.bind_name(name)
            cls.indexes[name] = index
        super(IndexedListMeta, cls).__init__(clsname, bases, dict_)

class KeyIndex(Index):
    """Index that accesses a key of an object"""

    def __init__(self, default=None, *args, **kwargs):
        self.default = default
        super(KeyIndex, self).__init__(*args, **kwargs)

    def process_item(self, item):
        if self.default is not None:
            return item.get(self.name, self.default)
        return item[self.name]

class UniqueKeyIndex(UniqueIndex, KeyIndex):
    """Unique index by dictionary key."""

class MultiKeyIndex(MultiIndex, KeyIndex):
    """Unique index by dictionary key."""

class IndexedList(MutableSequence, metaclass = IndexedListMeta):
    """A list that supports docstrings."""

    def __init__(self):
        self._list = []
        self.indexes = {}
        for name, index in type(self).indexes.items():
            bound_index = BoundIndex(index, self)
            self.indexes[name] = bound_index
            setattr(self, name, bound_index)
        super(IndexedList, self).__init__()

    def __len__(self):
        return len(self._list)

    def __getitem__(self, i):
        return self._list[i]

    def __setitem__(self, i, value):
        self._check(value, skip=i)
        if i >= len(self._list):
            raise IndexError('list assignment index out of range')
        self._remove_from_indexes(self._list[i])
        self._add_to_indexes(value)
        self._list[i] = value

    def _check(self, value, skip=None):
        """Check if value can be added to an index."""
        for index in self.indexes.values():
            index.prepare_add(value, skip)

    def _add_to_indexes(self, value):
        """Add value to all indexes."""
        for index in self.indexes.values():
            index.add(value)

    def _remove_from_indexes(self, value):
        """Remove value from all indexes."""
        for index in self.indexes.values():
            index.remove(value)

    def insert(self, i, value):
        """Insert value at given index."""
        self._check(value)
        self._add_to_indexes(value)
        self._list.insert(i, value)

    def __delitem__(self, i):
        self._remove_from_indexes(self._list[i])
        del self._list[i]

class AttributeIndex(Index):
    """An attribute index indexes objects by an attribute or a group of them.
    The name of the attribute defaults to the name of index. However it can be
    changed by specyfying one or more positional arguments.
    """

    def __init__(self, *args, **kwargs):
        if args:
            self._names = args
        else:
            self._names = None
        super(AttributeIndex, self).__init__(**kwargs)

    @property
    def names(self):
        return self._names or [self.name]
        

    def process_item(self, item):
        result = []
        for name in self.names:
            result.append(getattr(item, name))
        if len(result) == 1:
            return result[0]
        else:
            return tuple(result)

class UniqueAttributeIndex(UniqueIndex, AttributeIndex):
    """Unique index on Attribute."""

class Column(AttributeIndex):
    """A column."""

    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError('A column can have only one name')
        super(Column, self).__init__(*args, **kwargs)

class UniqueColumn(UniqueIndex, Column):
    """A column with unique index."""

class MultiColumn(MultiIndex, Column):
    """A column without unique constaint."""


class TableMeta(IndexedListMeta):
    """Metaclass for Table."""

    def __init__(cls, clsname, bases, dict_):
        super(TableMeta, cls).__init__(clsname, bases, dict_)
        cls.columns = []
        cls.names = []
        for k, v in dict_.items():
            if isinstance(v, Column):
                cls.columns.append(v)
                cls.names.append(v.name)
        cls.TupleClass = namedtuple(clsname, cls.names)

    def __prepare__(cls, clsname):
        return OrderedDict()

class Table(IndexedList, metaclass=TableMeta):
    """A table. Special case IndexedList that stores named tuples."""

    def __init__(self, dialect='excel'):
        self.dialect = dialect
        super(Table, self).__init__()

    def __setitem__(self, i, value):
        value = self.TupleClass._make(value)
        super(Table, self).__setitem__(i, value)

    def insert(self, i, value):
        value = self.TupleClass._make(value)
        super(Table, self).insert(i, value)

    def __str__(self):
        string_io = io.StringIO()
        writer = csv.writer(string_io, dialect=self.dialect)
        writer.writerow(self.names)
        writer.writerows(self)
        return string_io.getvalue()
