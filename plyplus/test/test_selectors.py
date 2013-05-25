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

        assert len( selector('*:is-root').match(self.tree1) ) == 1, selector('*:is-root').match(self.tree1)
        assert len( selector('*:is-root').match(self.tree2) ) == 1
        assert len( selector('a:is-root + b').match(self.tree2) ) == 0
        assert len( selector('branch:is-root > branch').match(self.tree1.tail[0]) ) == 1
        assert len( selector('start:is-root > branch').match(self.tree2) ) == 1

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

    def test_lists_repeated_use(self):
        assert self.tree1.select('name') == self.tree1.select('(name)')
        assert self.tree1.select('branch') == self.tree1.select('(branch)')
        assert self.tree2.select('name') == self.tree2.select('(name)')
        assert self.tree2.select('branch') == self.tree2.select('(branch)')

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

    def test_collection(self):
        tree1, tree2 = self.tree1, self.tree2
        assert tree1.select('name') == tree1.select('name').select('=name').select('(name)').select('=(name)').select('=(=name)')
        assert tree1.select('name').select('/a|b/') == list(u'ab')
        assert tree1.select('name').select('name /a|b/') == list(u'ab')
        assert len( tree2.select('=branch>name>/a/').select('/^b$/') ) == 4

    def test_tree_param(self):
        tree1, tree2 = self.tree1, self.tree2
        name_ast = STree('name', ['a'])

        # Sanity test
        assert name_ast.select('{name}', name=name_ast) == [name_ast]

        # Test that all params are required
        with self.assertRaises(KeyError):
            name_ast.select('{name}')

        # Make sure it plays nicely with values and arguments that don't exist
        assert not name_ast.select('{name}', name='A', another='B')

        # Test select1, and more "advanced" features with a param
        assert tree1.select1('=branch =(={name})', name=name_ast) == (tree1.tail[0], name_ast)

    def test_regexp_param(self):
        tree1, tree2 = self.tree1, self.tree2

        # Sanity test
        assert tree1.select('/{value}/', value='a') == ['a']

        # Test combination with other regexp element
        assert tree1.select('/^{value}/', value='a') == ['a']

        # Test regexp encoding, selector re-use
        assert not tree1.select('/{value}/', value='^a')


if __name__ == '__main__':
    unittest.main()
