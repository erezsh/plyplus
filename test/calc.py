from pprint import pprint
from plyplus import Grammar
from visitors import Transformer
#from sexp import Sub

g = Grammar("""
    start: expression;
    @expression: bin_op | un_op | parenthesis | NUMBER ;
    parenthesis: '\(' expression '\)';
    bin_op: expression ('\+'|'-'|'\*'|'/') expression;
    un_op: '-' expression;

    NUMBER: '[\d.]+';
    PLUS: '\+';
    MINUS: '-';
    MUL: '\*';
    DIV: '/';

    WS: '[ \t]+' {%ignore};

###
self.precedence = (
    ('left','PLUS','MINUS'),
    ('left','MUL','DIV'),
)
""")
#self.literals = ['=','+','-','*','/', '(',')']

class Calc(Transformer):
    def default(self, exp):
        return exp[1]

    def parenthesis(self, exp):
        return exp[2]

    def un_op(self, exp):
        operator = exp[1]
        arg = float(exp[2])
        if operator == '-':
            return -arg

        raise NotImplementedError(
                "Unknown unary operator: %s" % operator
            )

    def bin_op(self, exp):
        operator = exp[2]
        arg1, arg2 = float(exp[1]), float(exp[3])
        if operator == '+':
            return arg1 + arg2
        elif operator == '-':
            return arg1 - arg2
        elif operator == '*':
            return arg1 * arg2
        elif operator == '/':
            return arg1 / arg2

        raise NotImplementedError(
                "Unknown binary operator: %s" % operator
            )


def main():
    calc = Calc()
    while True:
        try:
            s = raw_input('> ')
        except EOFError:
            break
        if s == '':
            break
        tree = g.parse(s)
        print calc.transform(tree)

def _test():
    tree = g.parse("4.5-2+3*(-1/-2)")
    pprint(tree)
    print "Result:",Calc().transform(tree)

_test()
#main()
