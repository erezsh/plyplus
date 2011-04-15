import sys
sys.path.append('..')
from plyplus import Grammar, TokValue

def test():
    #p = grammar_parser.parse(file('sample_grammar.txt').read())
    #pt = ParseTree(p)
    #t = FlattenGrammar_Visitor().visit(p)
    #t = SimplifyGrammar_Visitor('simp_').visit(p)
    #pt.visit(FlattenGrammar_Visitor())
    
    g = Grammar(file('sample_grammar.txt').read())
    #pprint(g.parse(file('sample_input.txt').read()))
    for x in g.parse(file('sample_input.txt').read())[1][1]:
        if isinstance(x, TokValue):
            tok = x
            #print 'tok #%d: %s = %s {%d:%d}' % (tok.index, tok.type, tok, tok.line, tok.column)
        else:
            #print type(x), x
            pass

    #g = Grammar("start: 'a' 'a' B* ('c'? de)+; B: 'b'; C: 'c'; @de: DE; DE: 'de'; ")
    #print g.parse('aabbbde')
    #print g.parse('aacdede')


    #g = Grammar("start: A | a -> A; a: B (A|B) -> B; A: 'a'; B: 'b';")
    #print g.parse('aaabaab')
    pass

def test2():
    g = Grammar("start: A+ B A@+ 'b' A*; B: 'b'; A: 'a';")
    #print g.parse('aaabaab')
    for x in g.parse('aaabaab'):
        if isinstance(x, TokValue):
            tok = x
            print 'tok #%d: %s = %s {%d:%d}' % (tok.index, tok.type, tok, tok.line, tok.column)
        else:
            print type(x), x


def test3():
    # Multiple parsers and colliding tokens
    g = Grammar("start: B A ; B: '12'; A: '1'; ")
    g2 = Grammar("start: B A; B: '12'; A: '2'; ")
    #print g.parse('aaabaab')
    print g.parse('121')
    print g2.parse('122')

def test4():
    g = Grammar("start: '\(' name_list (COMMA MUL NAME)? '\)'; @name_list: NAME | name_list COMMA NAME ;  MUL: '\*'; COMMA: ','; NAME: '\w+'; ")
    print g.parse('(a,b,c,*x)')
    
    g = Grammar("start: '\(' name_list (COMMA MUL NAME)? '\)'; @name_list: NAME | name_list COMMA NAME ;  MUL: '\*'; COMMA: ','; NAME: '\w+'; ")
    print g.parse('(a,b,c,*x)')


def test5():
    g = Grammar("""
    start: bin;
    bin: num | num '-' bin;
    num: '0';
    """)



def test_python_lex():
    g = Grammar(file('python.g').read())
    l = g.lex("""
def fib(n):
    if n <= 1:
        return 1
    return fib(
n-1) + fib(n-2)
        
for i in range(11):
    print fib(i),
""")
    for x in l:
        y = x.value
        if isinstance(y, TokValue):
            print y.type, y, y.line, y.column
            pass
        else:
            print x.type, x.value
            pass


def test_python_lex2():
    g = Grammar(file('python.g').read())
    l = g.lex("""
def add_token():
    a
# hello

# hello
    setattr(self, b)

        """)
    for x in l:
        y = x.value
        if isinstance(y, TokValue):
            print y.type, y, y.line, y.column
            pass
        else:
            print x.type, x.value
            pass

def test_python_lex3():
    g = Grammar(file('python.g').read())
    l = g.lex("""
def test2():
    sexp = ['start',
             ]
        """)
    for x in l:
        y = x.value
        if isinstance(y, TokValue):
            print y.type, y, y.line, y.column
        else:
            print x.type, x.value


python_g_file = 'python2.g'

import time
def test_python_parse():
    g = Grammar(file(python_g_file))
    #print "Start"
    #l = g.parse(file('python_sample1.py').read())
    if 1:
        start = time.time()
        l = g.parse(file('python_sample1.py').read())
        l = g.parse(file('python_sample2.py').read())
        l = g.parse(file('calc.py').read())
        l = g.parse(file('../grammar_lexer.py').read())
        l = g.parse(file('../grammar_parser.py').read())
        l = g.parse(file('../sexp.py').read())
        l = g.parse(file('python_indent_postlex.py').read())
    ##l = g.parse(file('parsetab.py').read())

        l = g.parse(file('../plyplus.py').read())

        l = g.parse("c,d=x,y=a+b\nc,d=a,b\n")
        end = time.time()
        #print "End"
        print "Time: ", end-start, "secs"

    l = g.parse(file(r'C:\Python25\Lib\os.py').read())
    l = g.parse(file(r'C:\Python25\Lib\pydoc.py').read())

def test_python_parse2(n):
    g = Grammar(file(python_g_file))
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
    else:
        assert False

    print s
    #for i in  g.lex(s):
    #    print i

    print g.parse(s)


def test_python_parse3():
    import glob, os
    g = Grammar(file(python_g_file))

    path = 'C:\Python25\Lib'
    files = glob.glob(path+'\\*.py')
    start = time.time()
    for f in files:
        f2 = os.path.join(path,f)
        print f2
        l = g.parse(file(f2).read())

    end = time.time()
    print "Test3 (%d files), time: "%len(files), end-start, "secs"

def test_python4ply_sample():
    g = Grammar(file(python_g_file))
    l = g.parse(file(r'python4ply-sample.py').read())


if __name__ == '__main__':
    test_python_lex()
    test_python_lex3()
    test_python_parse()
    test_python_parse3()
    test_python4ply_sample()
    test_python_parse2(0)
    test_python_parse2(1)
    test_python_parse2(2)
    test5()
    test4()


