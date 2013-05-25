from __future__ import absolute_import

import unittest
import logging
import copy
import pickle

from plyplus.plyplus import STree

logging.basicConfig(level=logging.INFO)

class TestSTrees(unittest.TestCase):
    def setUp(self):
        self.tree1 = STree('a', [STree(x, y) for x, y in zip('bcd', 'xyz')])

    def test_deepcopy(self):
        assert self.tree1 == copy.deepcopy(self.tree1)

    def test_parents(self):
        s = copy.deepcopy(self.tree1)
        s.calc_parents()
        for i, x in enumerate(s.tail):
            assert x.parent() == s
            assert x.index_in_parent == i

    def test_pickle(self):
        s = copy.deepcopy(self.tree1)
        data = pickle.dumps(s)
        assert pickle.loads(data) == s

    def test_pickle_with_parents(self):
        s = copy.deepcopy(self.tree1)
        s.calc_parents()
        data = pickle.dumps(s)
        s2 = pickle.loads(data)
        assert s2 == s

        for i, x in enumerate(s2.tail):
            assert x.parent() == s2
            assert x.index_in_parent == i

if __name__ == '__main__':
    unittest.main()
