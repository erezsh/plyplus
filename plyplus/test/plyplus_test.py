import unittest
import sys, os, glob
import logging
import time
from plyplus import grammars
from plyplus.plyplus import Grammar, TokValue, ParseError
from pprint import pprint

from selector_test import TestSelectors

logging.basicConfig(level=logging.INFO)

CUR_PATH = os.path.split(__file__)[0]
_file = lambda n, *args: file(os.path.join(CUR_PATH, n), *args)

if os.name == 'nt':
    if 'PyPy' in sys.version:
        PYTHON_LIB = os.path.join(sys.prefix, 'lib-python', sys.winver)
    else:
        PYTHON_LIB = os.path.join(sys.prefix, 'Lib')
else:
    PYTHON_LIB = '/usr/lib64/python2.7/'

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
        assert l == l2, '%s != %s' % (l,l2)


def test_python_lex(code=FIB, expected=54):
    g = Grammar(_file('python.g').read())
    l = list(g.lex(code))
    print l
    for x in l:
        y = x.value
        if isinstance(y, TokValue):
            logging.debug('%s %s %s', y.type, y, y.line, y.column)
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

class TestPythonG(unittest.TestCase):
    def setUp(self):
        self.g = Grammar(grammars.open('python.g'))

    def test_basic1(self):
        g = self.g
        l = g.parse(_file('python_sample1.py').read())
        l = g.parse(_file('python_sample2.py').read())
        l = g.parse(_file('../../examples/calc.py').read())
        l = g.parse(_file('../grammar_lexer.py').read())
        l = g.parse(_file('../grammar_parser.py').read())
        l = g.parse(_file('../strees.py').read())
        l = g.parse(_file('../grammars/python_indent_postlex.py').read())

        l = g.parse(_file('../plyplus.py').read())

        l = g.parse("c,d=x,y=a+b\nc,d=a,b\n")

    def test_weird_stuff(self):
        g = self.g
        for n in range(3):
            if n == 0:
                s = """
a = \\
        \\
        1\\
        +2\\
-3
print a
"""
            elif n == 1:
                s = "a=b;c=d;x=e\n"

            elif n == 2:
                s = r"""
@spam3 (\
this,\
blahblabh\
)
def eggs9():
    pass

"""

            g.parse(s)


    def test_python_lib(self):
        g = self.g

        path = PYTHON_LIB
        files = glob.glob(path+'/*.py')
        start = time.time()
        for f in files:
            f2 = os.path.join(path,f)
            logging.info( f2 )
            l = g.parse(file(f2).read())

        end = time.time()
        logging.info( "test_python_lib (%d files), time: %s secs"%(len(files), end-start) )

    def test_python4ply_sample(self):
        g = self.g
        l = g.parse(_file(r'python4ply-sample.py').read())


class TestConfigG(unittest.TestCase):
    def setUp(self):
        self.g = Grammar(grammars.open('config.g'))

    def test_config_parser(self):
        g = self.g
        res = g.parse("""
            [ bla Blah bla ]
            thisAndThat = hel!l%o/
            one1111:~$!@ and all that stuff

            [Section2]
            whatever: whatever
            """)

if __name__ == '__main__':
    unittest.main()
