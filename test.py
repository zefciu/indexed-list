import unittest
from indexed_list import IndexedList, UniqueKeyIndex

class KnightList(IndexedList):
    name = UniqueKeyIndex()
    nickname = UniqueKeyIndex()

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

    def test_remove(self):
        del self.list_[1]
        with self.assertRaises(KeyError):
            self.list_.name['Bedevere']
