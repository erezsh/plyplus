# calc.py - # A simple calculator without using eval
# A shorter and simpler re-implementation of http://www.dabeaz.com/ply/example.html

import operator as op

from plyplus import Grammar, STransformer

calc_grammar = Grammar("""
    start: add;

    ?add: (add add_symbol)? mul;
    ?mul: (mul mul_symbol)? atom;
    @atom: neg | number | '\(' add '\)';
    neg: '-' add;

    number: '[\d.]+';
    mul_symbol: '\*' | '/';
    add_symbol: '\+' | '-';

    WS: '[ \t]+' (%ignore);
""")

class Calc(STransformer):

    _bin_operator_mapping = { '+': op.add, '-': op.sub, '*': op.mul, '/': op.div }

    def _bin_operator(self, exp):
        arg1, operator_symbol, arg2 = exp.tail

        operator = self._bin_operator_mapping[operator_symbol]
        return operator(arg1, arg2)

    number      = lambda self, exp: float(exp.tail[0])
    neg         = lambda self, exp: -exp.tail[0]
    __default__ = lambda self, exp: exp.tail[0]

    add = _bin_operator
    mul = _bin_operator

def main():
    calc = Calc()
    while True:
        try:
            s = raw_input('> ')
        except EOFError:
            break
        if s == '':
            break
        tree = calc_grammar.parse(s)
        print calc.transform(tree)

def _test():
    from pprint import pprint
    s = "2*4.5/2-2+3*(-1/-2)"
    tree = calc_grammar.parse(s)
    pprint(tree)
    res = Calc().transform(tree)
    print s, "=" , res
    assert res == 4, res


#_test()
main()
