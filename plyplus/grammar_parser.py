from ply import yacc

from strees import STree as S

DEBUG = False
YACC_TAB_MODULE = "plyplus_grammar_parsetab"

import grammar_lexer
from grammar_lexer import tokens

def p_extgrammar(p):
    """extgrammar : grammar
                  | grammar SECTION
    """
    p[0] = S('extgrammar', p[1:])

def p_grammar(p):
    """grammar  : def
                | def grammar
    """
    p[0] = S('grammar', p[1:])

def p_def(p):
    """def  : ruledef
            | tokendef
            | optiondef
    """
    p[0] = p[1]


def p_tokendef(p):
    """tokendef : TOKEN COLON tokenvalue SEMICOLON
                | TOKEN COLON tokenvalue tokenmods SEMICOLON
                | TOKEN COLON tokenvalue subgrammar SEMICOLON
    """
    if len(p) > 5:
        p[0] = S('tokendef', (p[1], p[3], p[4]))
    else:
        p[0] = S('tokendef', (p[1], p[3]))

def p_tokenvalue(p):
    """tokenvalue : REGEXP
                  | TOKEN
                  | REGEXP tokenvalue
                  | TOKEN tokenvalue
    """
    p[0] = S('tokenvalue', p[1:])

def p_tokenmods(p):
    """tokenmods : tokenmod
                 | tokenmod tokenmods
    """
    p[0] = S('tokenmods', p[1:])

def p_tokenmod(p):
    """tokenmod : LPAR OPTION modtokenlist RPAR"""
    p[0] = S('tokenmod', (p[2], p[3]))

def p_modtokenlist(p):
    """modtokenlist : tokendef modtokenlist
                    |
    """
    p[0] = S('modtokenlist', p[1:])

def p_subgrammar(p):
    """subgrammar : LCURLY extgrammar RCURLY"""
    p[0] = S('subgrammar', [p[2]])

def p_ruledef(p):
    """ruledef : RULENAME COLON rules_list SEMICOLON"""
    p[0] = S('ruledef', [p[1], p[3]])

def p_optiondef(p):
    """optiondef : OPTION COLON REGEXP SEMICOLON
                 | OPTION COLON TOKEN SEMICOLON
                 | OPTION COLON RULENAME SEMICOLON
                 | OPTION TOKEN COLON tokenvalue SEMICOLON
    """
    if len(p) == 6:
        assert p[1] == '%fragment'
        p[0] = S('fragmentdef', (p[2], p[4]))
    else:
        p[0] = S('optiondef', (p[1], p[3]))

def p_rules_list(p):
    """rules_list   : rule
                    | rule OR rules_list"""
    p[0] = S('rules_list', [p[1]] + p[3:])

def p_rule(p):
    """rule : expr
            | expr rule
            |
    """
    p[0] = S('rule', p[1:])

def p_expr(p):
    """expr : RULENAME
            | TOKEN
            | REGEXP
            | oper
            | LPAR rules_list RPAR
    """
    if len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = p[1]

def p_oper(p):
    "oper : expr OPER"
    p[0] = S('oper', (p[1], p[2]))



def p_error(p):
    if p:
        print "PLYPLUS: Syntax error in grammar at '%s'" % p.value, 'line',p.lineno, 'type',p.type
    else:
        print "PLYPLUS: Unknown syntax error in grammar"

start = "extgrammar"

_parser = yacc.yacc(debug=DEBUG, tabmodule=YACC_TAB_MODULE)     # Return parser object
def parse(text, debug=False):
    grammar_lexer.lexer.lineno=1
    return _parser.parse(text,lexer=grammar_lexer.lexer, debug=debug)
