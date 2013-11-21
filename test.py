import unittest
from indexed_list import IndexedList, UniqueKeyIndex

class KnightList(IndexedList):
    """A knight"""
    name = UniqueKeyIndex()
    nickname = UniqueKeyIndex()

class TestBadSemantics(unittest.TestCase):
    """Catch some bad practices."""

    def test_rebind(self):
        """Trying to rebind index from another list is a bad idea."""
        with self.assertRaises(ValueError):
            class PeasantList(IndexedList):
                name = KnightList.name

class TestBoundField(unittest.TestCase):
    """Bound field magic"""

    def setUp(self):
        class UniqueKeyIndex2(UniqueKeyIndex):
            @property
            def self(self):
                return self
        class SomeList(IndexedList):
            x = UniqueKeyIndex2()
        self.SomeList = SomeList
        self.some_list = SomeList()
        

    def test_property(self):
        """Test if bound field correctly calls properties of field."""
        self.assertEqual(self.some_list.x.self, self.some_list.x)
        self.assertNotEqual(self.some_list.x.self, self.SomeList.x)

    def test_noattr(self):
        """Invalid attributes handled correctly"""
        with self.assertRaises(AttributeError):
            self.some_list.x.y

    
class TestKeyIndexes(unittest.TestCase):
    """Test for indexed lists with unique key indexes."""

    def setUp(self):
        self.list_ = KnightList()
        self.list_.append({'name': 'Galahad', 'nickname': 'The Pure'})
        self.list_.append({'name': 'Bedevere', 'nickname': 'The Wise'})
        self.list_.append({'name': 'Robin', 'nickname': 'The Not So Brave'})


    def test_get(self):
        self.assertEqual(
            self.list_.name['Bedevere'],
            {'name': 'Bedevere', 'nickname': 'The Wise'},
        )

    def assertUnchanged(self):
        self.assertEqual(len(self.list_), 3)
        self.assertEqual(len(self.list_.name), 3)
        self.assertEqual(len(self.list_.nickname), 3)
        self.assertSetEqual(
            set(self.list_.name),
            {'Galahad', 'Bedevere', 'Robin'}
        )
        self.assertSetEqual(
            set(self.list_.nickname),
            {'The Pure', 'The Wise', 'The Not So Brave'}
        )
        self.assertListEqual(list(self.list_), [
            {'name': 'Galahad', 'nickname': 'The Pure'},
            {'name': 'Bedevere', 'nickname': 'The Wise'},
            {'name': 'Robin', 'nickname': 'The Not So Brave'},
        ])

    def test_simple_get(self):
        """We can access indexed list as a normal one."""
        self.assertEqual(
            self.list_[1],
            {'name': 'Bedevere', 'nickname': 'The Wise'},
        )

    def test_set(self):
        """We can set items on the list."""
        self.list_[1] = {'name': 'Bedevere', 'nickname': 'The Foolish'}
        self.assertEqual(
            self.list_[1],
            {'name': 'Bedevere', 'nickname': 'The Foolish'},
        )

    def test_set_invalid(self):
        """Setting item on invalid index doesn't break anything."""
        with self.assertRaises(IndexError):
            self.list_[4] = {'name': 'Lancelot', 'nickname': 'The Brave'}
        self.assertUnchanged()


    def test_remove(self):
        del self.list_[1]
        with self.assertRaises(KeyError):
            self.list_.name['Bedevere']

    def test_len(self):
        """Index has __len__"""
        self.assertEqual(len(self.list_.name), 3)
        self.assertEqual(len(self.list_.nickname), 3)

    def test_violate_unique(self):
        """We can't violate unique index."""
        with self.assertRaises(ValueError):
            self.list_.append({'name': 'Galahad', 'nickname': 'The Dirty'})
        # Check if nothing is broken
        self.assertUnchanged()
