from __future__ import absolute_import, print_function
from io import open

import unittest
import time
import sys, os, glob
import logging

from plyplus import grammars
from plyplus.plyplus import Grammar

logging.basicConfig(level=logging.INFO)

CUR_PATH = os.path.split(__file__)[0]
def _read(n, *args):
    kwargs = {'encoding': 'iso-8859-1'}
    with open(os.path.join(CUR_PATH, n), *args, **kwargs) as f:
        return f.read()

if os.name == 'nt':
    if 'PyPy' in sys.version:
        PYTHON_LIB = os.path.join(sys.prefix, 'lib-python', sys.winver)
    else:
        PYTHON_LIB = os.path.join(sys.prefix, 'Lib')
else:
    PYTHON_LIB = '/usr/lib/python2.7/'

class TestPythonG(unittest.TestCase):
    def setUp(self):
        with grammars.open('python.g') as g:
            self.g = Grammar(g)

    def test_basic1(self):
        g = self.g
        g.parse(_read('python_sample1.py'))
        g.parse(_read('python_sample2.py'))
        g.parse(_read('../../examples/calc.py'))
        g.parse(_read('../grammar_lexer.py'))
        g.parse(_read('../grammar_parser.py'))
        g.parse(_read('../strees.py'))
        g.parse(_read('../grammars/python_indent_postlex.py'))

        g.parse(_read('../plyplus.py'))

        g.parse("c,d=x,y=a+b\nc,d=a,b\n")

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
            f2 = os.path.join(path, f)
            logging.info( f2 )
            g.parse(_read(f2))

        end = time.time()
        logging.info( "test_python_lib (%d files), time: %s secs"%(len(files), end-start) )

    def test_python4ply_sample(self):
        g = self.g
        g.parse(_read(r'python4ply-sample.py'))


class TestConfigG(unittest.TestCase):
    def setUp(self):
        with grammars.open('config.g') as g:
            self.g = Grammar(g)

    def test_config_parser(self):
        g = self.g
        g.parse("""
            [ bla Blah bla ]
            thisAndThat = hel!l%o/
            one1111:~$!@ and all that stuff

            [Section2]
            whatever: whatever
            """)


if __name__ == '__main__':
    unittest.main()
