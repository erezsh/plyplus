from __future__ import absolute_import

import unittest
import logging
from plyplus.plyplus import Grammar, STree
from plyplus.selector import selector

logging.basicConfig(level=logging.INFO)

class TestSelectors(unittest.TestCase):
    def setUp(self):
        tree_grammar = Grammar("start: branch; branch: name ('{' branch* '}')?; name: '[a-z]';")

        self.tree1 = tree_grammar.parse('a{b{cde}}')
        self.tree2 = tree_grammar.parse('a{abc{bbab}c}')

    def test_elem_head(self):
        assert len( selector('name').match(self.tree1) ) == 5
        assert len( selector('branch').match(self.tree1) ) == 5
        assert len( selector('name').match(self.tree2) ) == 9
        assert len( selector('branch').match(self.tree2) ) == 9

    def test_elem_regexp(self):
        assert len( selector('/[a-c]$/').match(self.tree1) ) == 3
        assert len( selector('/[b-z]$/').match(self.tree2) ) == len('bcbbbc')

    def test_elem_any(self):
        assert len( selector('*').match(self.tree1) ) == 16
        assert len( selector('*').match(self.tree2) ) == 28


    def test_modifiers(self):
        assert len( selector('*:is-leaf').match(self.tree1) ) == 5
        assert len( selector('/[a-c]/:is-leaf').match(self.tree1) ) == 3

        assert len( selector('/[b]/:is-parent').match(self.tree1) ) == 5
        assert len( selector('/[b]/:is-parent').match(self.tree2) ) == 9

        # TODO: More modifiers!

    def test_operators(self):
        tree1, tree2 = self.tree1, self.tree2
        assert len( selector('name /b/').match(tree2) ) == 4
        assert len( selector('name>/b/').match(tree2) ) == 4
        assert len( selector('branch>branch>name').match(tree1) ) == 4
        assert len( selector('branch>branch>branch>name').match(tree1) ) == 3
        assert len( selector('branch branch branch name').match(tree1) ) == 3
        assert len( selector('branch branch branch').match(tree1) ) == 3

        assert len( selector('branch+branch').match(tree1) ) == 2
        assert len( selector('branch~branch~branch').match(tree1) ) == 1
        assert len( selector('branch~branch~branch~branch').match(tree1) ) == 0

        assert len( selector('branch:is-parent + branch branch > name > /a/:is-leaf').match(tree2) ) == 1   # test all at once; only innermost 'a' matches

    def test_lists(self):
        tree1, tree2 = self.tree1, self.tree2
        assert set( selector('(/a/)').match(tree1) ) == set('a')
        assert set( selector('(/a/,/b$/)').match(tree1) ) == set('ab')
        assert set( selector('(/e/, (/a/,/b$/), /c/)').match(tree1) ) == set('abce')

    def test_lists2(self):
        tree1, tree2 = self.tree1, self.tree2
        assert set( tree1.select('(branch /d/)') ) == set('d')
        assert tree1.select1('=(=branch /d/) + (=branch /e/)').tail[0].tail[0] == 'd'
        assert len( self.tree2.select('(=branch>name>/c/) branch /b/') )

    def test_yield(self):
        tree1, tree2 = self.tree1, self.tree2
        assert list( selector('=name /a/').match(tree1) )[0].head == 'name'
        assert len( selector('=branch /c/').match(tree1) ) == 3
        assert set( selector('(=name /a/,name /b$/)').match(tree1) ) == set([STree('name', ['a']), 'b'])
        assert set( selector('=branch branch branch').match(tree1) ) == set([tree1.tail[0]])
        assert set( selector('=(name,=branch branch branch) /c/').match(tree1) ) == set([STree('name', ['c']), tree1.tail[0]])

if __name__ == '__main__':
    unittest.main()
