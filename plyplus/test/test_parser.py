from __future__ import absolute_import

import unittest
import logging
import os
import sys
try:
    from cStringIO import StringIO as cStringIO
except ImportError:
    # Available only in Python 2.x, 3.x only has io.StringIO from below
    cStringIO = None
from io import (
        StringIO as uStringIO,
        open,
    )
from ply import yacc

from plyplus.plyplus import Grammar, TokValue, ParseError

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

    @unittest.skipIf(cStringIO is None, "cStringIO not available")
    def test_stringio_bytes(self):
        """Verify that a Grammar can be created from file-like objects other than Python's standard 'file' object"""
        Grammar(cStringIO(b"start: a+ b a+? 'b' a*; b: 'b'; a: 'a';"))

    def test_stringio_unicode(self):
        """Verify that a Grammar can be created from file-like objects other than Python's standard 'file' object"""
        Grammar(uStringIO(u"start: a+ b a+? 'b' a*; b: 'b'; a: 'a';"))

    def test_unicode(self):
        g = Grammar(r"""start: UNIA UNIB UNIA;
                    UNIA: '\xa3';
                    UNIB: '\u0101';
                    """)
        g.parse(u'\xa3\u0101\u00a3')

    def test_recurse_expansion(self):
        """Verify that stack depth doesn't get exceeded on recursive rules marked for expansion."""
        g = Grammar(r"""@start: a | start a ; a : A ; A : 'a' ;""")

        # Force PLY to write to the debug log, but prevent writing it to the terminal (uses repr() on the half-built
        # STree data structures, which uses recursion).
        g._grammar.debug = yacc.NullLogger()

        g.parse("a" * (sys.getrecursionlimit() // 4))

    def test_expand1_lists_with_one_item(self):
        g = Grammar(r"""start: list ;
                        ?list: item+ ;
                        item : A ;
                        A: 'a' ;
                    """)
        r = g.parse("a")

        # because 'list' is an expand-if-contains-one rule and we only provided one element it should have expanded to 'item'
        self.assertSequenceEqual([subtree.head for subtree in r.tail], ('item',))

        # regardless of the amount of items: there should be only *one* child in 'start' because 'list' isn't an expand-all rule
        self.assertEqual(len(r.tail), 1)

    def test_expand1_lists_with_one_item_2(self):
        g = Grammar(r"""start: list ;
                        ?list: item+ '!';
                        item : A ;
                        A: 'a' ;
                    """)
        r = g.parse("a!")

        # because 'list' is an expand-if-contains-one rule and we only provided one element it should have expanded to 'item'
        self.assertSequenceEqual([subtree.head for subtree in r.tail], ('item',))

        # regardless of the amount of items: there should be only *one* child in 'start' because 'list' isn't an expand-all rule
        self.assertEqual(len(r.tail), 1)

    def test_dont_expand1_lists_with_multiple_items(self):
        g = Grammar(r"""start: list ;
                        ?list: item+ ;
                        item : A ;
                        A: 'a' ;
                    """)
        r = g.parse("aa")

        # because 'list' is an expand-if-contains-one rule and we've provided more than one element it should *not* have expanded
        self.assertSequenceEqual([subtree.head for subtree in r.tail], ('list',))

        # regardless of the amount of items: there should be only *one* child in 'start' because 'list' isn't an expand-all rule
        self.assertEqual(len(r.tail), 1)

        # Sanity check: verify that 'list' contains the two 'item's we've given it
        [list] = r.tail
        self.assertSequenceEqual([item.head for item in list.tail], ('item', 'item'))

    def test_dont_expand1_lists_with_multiple_items_2(self):
        g = Grammar(r"""start: list ;
                        ?list: item+ '!';
                        item : A ;
                        A: 'a' ;
                    """)
        r = g.parse("aa!")

        # because 'list' is an expand-if-contains-one rule and we've provided more than one element it should *not* have expanded
        self.assertSequenceEqual([subtree.head for subtree in r.tail], ('list',))

        # regardless of the amount of items: there should be only *one* child in 'start' because 'list' isn't an expand-all rule
        self.assertEqual(len(r.tail), 1)

        # Sanity check: verify that 'list' contains the two 'item's we've given it
        [list] = r.tail
        self.assertSequenceEqual([item.head for item in list.tail], ('item', 'item'))



    def test_empty_expand1_list(self):
        g = Grammar(r"""start: list ;
                        ?list: item* ;
                        item : A ;
                        A: 'a' ;
                     """)
        r = g.parse("")

        # because 'list' is an expand-if-contains-one rule and we've provided less than one element (i.e. none) it should *not* have expanded
        self.assertSequenceEqual([subtree.head for subtree in r.tail], ('list',))

        # regardless of the amount of items: there should be only *one* child in 'start' because 'list' isn't an expand-all rule
        self.assertEqual(len(r.tail), 1)

        # Sanity check: verify that 'list' contains no 'item's as we've given it none
        [list] = r.tail
        self.assertSequenceEqual([item.head for item in list.tail], ())

    def test_empty_expand1_list_2(self):
        g = Grammar(r"""start: list ;
                        ?list: item* '!'?;
                        item : A ;
                        A: 'a' ;
                     """)
        r = g.parse("")

        # because 'list' is an expand-if-contains-one rule and we've provided less than one element (i.e. none) it should *not* have expanded
        self.assertSequenceEqual([subtree.head for subtree in r.tail], ('list',))

        # regardless of the amount of items: there should be only *one* child in 'start' because 'list' isn't an expand-all rule
        self.assertEqual(len(r.tail), 1)

        # Sanity check: verify that 'list' contains no 'item's as we've given it none
        [list] = r.tail
        self.assertSequenceEqual([item.head for item in list.tail], ())


    def test_empty_flatten_list(self):
        g = Grammar(r"""start: list ;
                        #list: | item ',' list;
                        item : A ;
                        A: 'a' ;
                     """)
        r = g.parse("")

        # Because 'list' is a flatten rule it's top-level element should *never* be expanded
        self.assertSequenceEqual([subtree.head for subtree in r.tail], ('list',))

        # Sanity check: verify that 'list' contains no 'item's as we've given it none
        [list] = r.tail
        self.assertSequenceEqual([item.head for item in list.tail], ())

    def test_single_item_flatten_list(self):
        g = Grammar(r"""start: list ;
                        #list: | item ',' list ;
                        item : A ;
                        A: 'a' ;
                     """)
        r = g.parse("a,")

        # Because 'list' is a flatten rule it's top-level element should *never* be expanded
        self.assertSequenceEqual([subtree.head for subtree in r.tail], ('list',))

        # Sanity check: verify that 'list' contains exactly the one 'item' we've given it
        [list] = r.tail
        self.assertSequenceEqual([item.head for item in list.tail], ('item',))

    def test_multiple_item_flatten_list(self):
        g = Grammar(r"""start: list ;
                        #list: | item ',' list ;
                        item : A ;
                        A: 'a' ;
                     """)
        r = g.parse("a,a,")

        # Because 'list' is a flatten rule it's top-level element should *never* be expanded
        self.assertSequenceEqual([subtree.head for subtree in r.tail], ('list',))

        # Sanity check: verify that 'list' contains exactly the two 'item's we've given it
        [list] = r.tail
        self.assertSequenceEqual([item.head for item in list.tail], ('item', 'item'))

    def test_recurse_flatten(self):
        """Verify that stack depth doesn't get exceeded on recursive rules marked for flattening."""
        g = Grammar(r"""#start: a | start a ; a : A ; A : 'a' ;""")

        # Force PLY to write to the debug log, but prevent writing it to the terminal (uses repr() on the half-built
        # STree data structures, which uses recursion).
        g._grammar.debug = yacc.NullLogger()

        g.parse("a" * (sys.getrecursionlimit() // 4))

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
