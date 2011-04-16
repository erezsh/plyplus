from ply import yacc

DEBUG = False
YACC_TAB_MODULE = "plyplus_grammar_parsetab"

import grammar_lexer
from grammar_lexer import tokens

def p_extgrammar(p):
    """extgrammar : grammar
                  | grammar SECTION
    """
    p[0] = ['extgrammar'] + p[1:]

def p_grammar(p):
    """grammar  : def
                | def grammar
    """
    p[0] = ['grammar'] + p[1:]

def p_def(p):
    """def  : ruledef
            | tokendef
            | optiondef
    """
    p[0] = p[1]


def p_tokendef(p):
    """tokendef : TOKEN COLON REGEXP SEMICOLON
                | TOKEN COLON REGEXP tokenmods SEMICOLON
    """
    if len(p) > 5:
        p[0] = ['tokendef', p[1], p[3], p[4]]
    else:
        p[0] = ['tokendef', p[1], p[3]]

def p_tokenmods(p):
    """tokenmods : tokenmod
                 | tokenmod tokenmods
    """
    p[0] = ['tokenmods'] + p[1:]

def p_tokenmod(p):
    """tokenmod : LCURLY OPTION modtokenlist RCURLY"""
    p[0] = ['tokenmod', p[2], p[3]]

def p_modtokenlist(p):
    """modtokenlist : tokendef modtokenlist
                    |
    """
    p[0] = ['modtokenlist'] + p[1:]

def p_ruledef(p):
    """ruledef : RULENAME COLON rules_list SEMICOLON
               | RULENAME COLON rules_list INTO TOKEN SEMICOLON"""
    p[0] = ['ruledef'] + [p[1], p[3]]

def p_optiondef(p):
    """optiondef : OPTION COLON REGEXP SEMICOLON
                 | OPTION COLON TOKEN SEMICOLON
                 | OPTION COLON RULENAME SEMICOLON
    """
    p[0] = ['optiondef', p[1], p[3]]

def p_number_list(p):
    """number_list : NUMBER
                   | NUMBER number_list"""
    p[0] = ['number_list'] + p[1:]

def p_rules_list(p):
    """rules_list   : rule_into
                    | rule_into OR rules_list"""
    p[0] = ['rules_list'] + [p[1]] + p[3:]

def p_rule_into(p):
    """rule_into : rule
                 | rule INTO number_list"""
    p[0] = ['rule_into'] + [p[1]] + p[3:]

def p_rule(p):
    """rule : expr
            | expr rule
            |
    """
    p[0] = ['rule'] + p[1:]

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
    p[0] = ['oper', p[1], p[2]]



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
