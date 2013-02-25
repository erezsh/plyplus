from __future__ import absolute_import, print_function
from io import open

import unittest
import os
import logging
import copy
import pickle
from plyplus.plyplus import Grammar, TokValue, ParseError, STree

from .selector_test import TestSelectors
from .test_grammars import TestPythonG, TestConfigG

logging.basicConfig(level=logging.INFO)

CUR_PATH = os.path.dirname(__file__)
def _read(n, *args):
    with open(os.path.join(CUR_PATH, n), *args) as f:
        return f.read()


FIB = """
def fib(n):
    if n <= 1:
        return 1
    return fib(
n-1) + fib(n-2)

for i in range(11):
    print fib(i),
"""

class TestPlyPlus(unittest.TestCase):
    def test_basic1(self):
        g = Grammar("start: a+ b a+? 'b' a*; b: 'b'; a: 'a';")
        r = g.parse('aaabaab')
        self.assertEqual( ''.join(x.head for x in r.tail), 'aaabaa' )
        r = g.parse('aaabaaba')
        self.assertEqual( ''.join(x.head for x in r.tail), 'aaabaaa' )

        self.assertRaises(ParseError, g.parse, 'aaabaa')

    def test_basic2(self):
        # Multiple parsers and colliding tokens
        g = Grammar("start: B A ; B: '12'; A: '1'; ", auto_filter_tokens=False)
        g2 = Grammar("start: B A; B: '12'; A: '2'; ", auto_filter_tokens=False)
        x = g.parse('121')
        assert x.head == 'start' and x.tail == ['12', '1'], x
        x = g2.parse('122')
        assert x.head == 'start' and x.tail == ['12', '2'], x

    def test_basic3(self):
        g = Grammar("start: '\(' name_list (COMMA MUL NAME)? '\)'; @name_list: NAME | name_list COMMA NAME ;  MUL: '\*'; COMMA: ','; NAME: '\w+'; ")
        l = g.parse('(a,b,c,*x)')

        g = Grammar("start: '\(' name_list (COMMA MUL NAME)? '\)'; @name_list: NAME | name_list COMMA NAME ;  MUL: '\*'; COMMA: ','; NAME: '\w+'; ")
        l2 = g.parse('(a,b,c,*x)')
        assert l == l2, '%s != %s' % (l, l2)

    def test_unicode(self):
        g = Grammar(r"""start: UNIA UNIB UNIA;
                    UNIA: '\xa3';
                    UNIB: '\u0101';
                    """)
        g.parse(u'\xa3\u0101\u00a3')

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

def test_python_lex(code=FIB, expected=54):
    g = Grammar(_read('python.g'))
    l = list(g.lex(code))
    for x in l:
        y = x.value
        if isinstance(y, TokValue):
            logging.debug('%s %s %s', y.type, y.line, y.column)
        else:
            logging.debug('%s %s', x.type, x.value)
    assert len(l) == expected, len(l)

def test_python_lex2():
    test_python_lex(code="""
def add_token():
    a
# hello

# hello
    setattr(self, b)

        """, expected=26)

def test_python_lex3():
    test_python_lex("""
def test2():
    sexp = ['start',
             ]
        """, expected=18)

if __name__ == '__main__':
    unittest.main()
