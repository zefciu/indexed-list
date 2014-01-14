import unittest
from indexed_list import IndexedList, UniqueKeyIndex, MultiKeyIndex
from indexed_list import Table, UniqueColumn, MultiColumn, UniqueAttributeIndex
from indexed_list import Unindexed

class KnightList(IndexedList):
    """A knight"""
    name = UniqueKeyIndex()
    nickname = UniqueKeyIndex()
    brave = MultiKeyIndex(default=True)

class TestBadSemantics(unittest.TestCase):
    """Catch some bad practices."""

    def test_rebind(self):
        """Trying to rebind index from another list is a bad idea."""
        with self.assertRaises(ValueError):
            class PeasantList(IndexedList):
                name = KnightList.name

    def test_column_with_two_names(self):
        """Trying to create a column with several names."""
        with self.assertRaises(TypeError):
            class KnightTable(Table):
                name_surname = UniqueColumn('name', 'Surname')

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
        self.assertUnchanged()


class TestMultiIndexes(unittest.TestCase):

    def setUp(self):
        self.list_ = KnightList()
        self.list_.append(
            {'name': 'Galahad', 'nickname': 'The Pure', 'brave': True}
        )
        self.list_.append(
            {'name': 'Bedevere', 'nickname': 'The Wise', 'brave': True}
        )
        self.list_.append(
            {'name': 'Robin', 'nickname': 'The Not So Brave', 'brave': False}
        )

    def test_indexes(self):
        self.assertSetEqual(
            {knight['name'] for knight in self.list_.brave[True]},
            {'Galahad', 'Bedevere'},
        )
        self.assertListEqual(self.list_.brave[None], [])

class KnightTable(Table):
    name = UniqueColumn()
    nickname = MultiColumn()
    name_nickname = UniqueAttributeIndex('name', 'nickname')


class TestTable(unittest.TestCase):
    """Tests for Table object"""

    def setUp(self):
        self.table = KnightTable()
        self.table.append(('Galahad', 'The Pure'))
        self.table.append(('Robin', 'The Brave'))
        self.table.append(('Bedevere', 'The Wise'))
        self.table.append(('Lancelot', 'The Brave'))

    def test_get(self):
        """Get nice namedtuples."""
        self.assertEqual(self.table[1].name, 'Robin')

    def test_get_by_index(self):
        """Access item by multicolumn index."""
        self.assertEqual(
            self.table.name_nickname[('Robin', 'The Brave')].name,
            'Robin',
        )

    def test_drop_none(self):
        """Check if values with None can be added non-uniqueli."""
        self.table.append((None, 'The Strong'))
        self.table.append((None, 'The Weak'))

    def test_setitem(self):
        """Setting an item."""
        self.table[1] = ('Robin', 'Not So Brave')
        self.assertEqual(
            self.table.nickname['Not So Brave'][0].name,
            'Robin',
        )

    def test_serialize(self):
        self.assertEqual(
            str(self.table),
            """name,nickname\r
Galahad,The Pure\r
Robin,The Brave\r
Bedevere,The Wise\r
Lancelot,The Brave\r
""")

class KnightsWithDict(Table):
    """A sample table with Unindexed column."""
    name = UniqueColumn()
    nickname = MultiColumn()
    quotes = Unindexed()
    name_nickname = UniqueAttributeIndex('name', 'nickname')

class TestTableWithUnindexed(unittest.TestCase):
    """Test the table that contains unindexed field."""

    def setUp(self):
        self.table = KnightsWithDict()
        self.table.append(('Galahad', 'The Pure', [
            'Oh, let me have just a bit of peril',
        ]))
        self.table.append(('Robin', 'The Brave', []))
        self.table.append(('Bedevere', 'The Wise', [
            'And that my liege is how we know the Earth to be banana shaped',
        ]))
        self.table.append(('Lancelot', 'The Brave', []))

    def test_get(self):
        """Get nice namedtuples."""
        self.assertEqual(self.table[1].name, 'Robin')

    def test_get_by_index(self):
        """Access item by multicolumn index."""
        self.assertListEqual(
            self.table.name_nickname[('Bedevere', 'The Wise')].quotes,
            ['And that my liege is how we know the Earth to be banana shaped'],
        )
