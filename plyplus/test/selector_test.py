import sys, os
import logging
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../grammars'))
from plyplus import Grammar, TokValue, STree
from selector import selector
from pprint import pprint

logging.basicConfig(level=logging.INFO)

tree_grammar = Grammar("start: branch; branch: name ('{' branch* '}')?; name: '[a-z]';")

tree1 = tree_grammar.parse('a{b{cde}}')
tree2 = tree_grammar.parse('a{abc{bbab}c}')

def test_elem_head():
    assert len( selector('name').match(tree1) ) == 5
    assert len( selector('branch').match(tree1) ) == 5
    assert len( selector('name').match(tree2) ) == 9
    assert len( selector('branch').match(tree2) ) == 9

def test_elem_regexp():
    assert len( selector('/[a-c]$/').match(tree1) ) == 3
    assert len( selector('/[b-z]$/').match(tree2) ) == len('bcbbbc')

def test_elem_any():
    assert len( selector('*').match(tree1) ) == 16
    assert len( selector('*').match(tree2) ) == 28

def test_elem():
    test_elem_head()
    test_elem_regexp()
    test_elem_any()

def test_modifiers():
    assert len( selector('*:is-leaf').match(tree1) ) == 5
    assert len( selector('/[a-c]/:is-leaf').match(tree1) ) == 3

    assert len( selector('/[b]/:is-parent').match(tree1) ) == 5
    assert len( selector('/[b]/:is-parent').match(tree2) ) == 9

    # TODO: More modifiers!

def test_operators():
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

def test_lists():
    assert set( selector('(/a/)').match(tree1) ) == set('a')
    assert set( selector('(/a/,/b$/)').match(tree1) ) == set('ab')
    assert set( selector('(/e/, (/a/,/b$/), /c/)').match(tree1) ) == set('abce')

def test_yield():
    assert list( selector('=name /a/').match(tree1) )[0].head == 'name'
    assert len( selector('=branch /c/').match(tree1) ) == 3
    assert set( selector('(=name /a/,name /b$/)').match(tree1) ) == set([STree('name', ['a']), 'b'])
    assert set( selector('=branch branch branch').match(tree1) ) == set([tree1.tail[0]])
    assert set( selector('=(name,=branch branch branch) /c/').match(tree1) ) == set([STree('name', ['c']), tree1.tail[0]])

def test_all():
    test_elem()
    test_modifiers()
    test_operators()
    test_lists()
    test_yield()
    print "All done!"

test_all()
