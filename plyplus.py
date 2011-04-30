import re
from pprint import pprint

from ply import lex, yacc

import grammar_parser

from sexp import Visitor, Transformer, head, tail, is_sexp

# -- Must!
#TODO: Offer alternatives to PLY facilities: precedence, error, line-count
#TODO: Allow empty rules
#TODO: Support States
#TODO: a* is very slow. Optimize it.

# -- Nice to have
#TODO: find better terms than expand and flatten
#TODO: rename simps
#TODO: meaningful names to anonymous tokens
#TODO: Exact recovery of input (as text attr)
#TODO: Allow 'optimize' mode
#TODO: Rule Self-recursion (an operator? a 'self' keyword?)
#TODO: Multiply defined tokens (just concatinate with |?)

# -- Unknown status
#TODO: a (b c d => 1 2) e
#TODO: (a+)? is different from a*
#       print_stmt : PRINT (RIGHTSHIFT? test (COMMA test)* COMMA?)?  ;
#           --> only works as -->
#       print_stmt : PRINT (RIGHTSHIFT? test ((COMMA test)+)? COMMA?)?  ;
#
#      Similarly:
#      dictmaker : test COLON test (COMMA test COLON test)* COMMA? ;
#           --> only works as -->
#      dictmaker : test COLON test (COMMA test COLON test)+? COMMA? ;
#
#TODO: better filters
#TODO: Add token history on parse error
#TODO: Add rule history on parse error?
#TODO: Offer mechanisms to easily avoid ambiguity (expr: expr '\+' expr etc.)
#TODO: Allow to reconstruct the input with whatever changes were made to the tree
#TODO: Change rule+ into "rule simp*" instead of "simp+"
#TODO: Use PLY's ignore mechanism (=tokens return None) instead of post-filtering it myself?

# -- Continual Tasks
#TODO: Optimize for space
#TODO: Optimize for speed
#TODO: require less knowledge of ply

#DONE: anonymous tokens
#DONE: Resolve errors caused by dups of tokens
#DONE: Allow comments in grammar

TAB_LEN = 4


#----------------------------------------------------------------------
# Known Issue! -- Bad Rule Handling on Repitition (TODO)
#----------------------------------------------------------------------

#   Sometimes recursion (or repitition) will make the parser enter a rule which is incorrect (probably too small lookahead?). 
#   Unrolling the first (or two) element of the recursion can be helpful: I suppose that way it won't enter the recursion unless it has a good reason to
#   A temporary solution: Don't put repitition as the first thing on your rule?

#   OK: list_inner	: expr | expr COMMA (expr (COMMA)? )@* ;
#   BAD: list_inner	: expr | (expr (COMMA)? )@* ;
#   BAD: list_inner	: expr | (expr (COMMA)? )@+ ;
#----------------------------------------------------------------------



class GetTokenDefs_Visitor(Visitor):
    def __init__(self, dict_to_populate):
        self.tokendefs = dict_to_populate

    def tokendef(self, tree):
        self.tokendefs[ tree[2] ] = tree[1]


class SimplifyGrammar_Visitor(Visitor):
    def __init__(self, unique_id, filters):
        self._unique_id = unique_id
        self._count = 0
        self._rules_to_add = []
        self.filters = filters

        self.tokendefs = {} # to be populated at visit

    def _get_new_rule_name(self):
        s = '%s%d'%(self._unique_id, self._count)
        self._count += 1
        return s

    def _get_new_tok_name(self):
        s = '%s%d'%(self._unique_id.upper(), self._count)
        self._count += 1
        return s

    def _flatten(self, tree, name):
        changed = False
        for i in range(len(tree)-1, 0, -1):   # skips 0
            if len(tree[i]) and head(tree[i]) == name:
                tree[i:i+1] = tail(tree[i])
                changed = True
        return changed

    def visit(self, tree):
        GetTokenDefs_Visitor(self.tokendefs).visit(tree)
        self._visit(tree)
        return tree

    def _visit(self, tree):
        "_visit simplifies the tree as much as possible"
        # visit until nothing left to change (not the most efficient, but good enough)
        while Visitor._visit(self, tree):
            pass

    def modtokenlist(self, tree):
        return self._flatten(tree, 'modtokenlist')

    def tokenmods(self, tree):
        return self._flatten(tree, 'tokenmods')

    def number_list(self, tree):
        return self._flatten(tree, 'number_list')

    def grammar(self, tree):
        changed = self._flatten(tree, 'grammar')
        
        if self._rules_to_add:
            changed = True
        tree += self._rules_to_add
        self._rules_to_add = []
        return changed

    def oper(self, tree):
        operand_rule = tree[1]
        operator = tree[2]
        if operator in ('*', '@*'):
            # a : b c* d;
            #  -->
            # a : b _c d;
            # _c : c _c |;
            new_name = self._get_new_rule_name()
            mod = '@' if operator.startswith('@') else '#'
            new_rule = ['ruledef', mod+new_name, ['rules_list', ['rule', operand_rule, new_name], ['rule']] ]
            self._rules_to_add.append(new_rule)
            tree[:] = ['rule', new_name]
        elif operator in ('+', '@+'):
            # a : b c+ d;
            #  -->
            # a : b _c d;
            # _c : c _c | c;
            new_name = self._get_new_rule_name()
            mod = '@' if operator.startswith('@') else '#'
            new_rule = ['ruledef', mod+new_name, ['rules_list', ['rule', operand_rule], ['rule', new_name, operand_rule]] ]
            self._rules_to_add.append(new_rule)
            tree[:] = ['rule', new_name]
        elif operator == '?':
            tree[:] = ['rules_list', operand_rule, ['rule']]
        else:
            assert False, operand_rule

        return True # changed

    def rule(self, tree):
        # rules_list unpacking
        # a : b (c|d) e
        #  -->
        # a : b c e | b d e
        #
        # In actual terms:
        #
        # [rule [b] [rules_list [c] [d]] [e]]
        #   -->
        # [rules_list [rule [b] [c] [e]] [rule [b] [d] [e]] ]
        #
        changed = False

        if self._flatten(tree, 'rule'):
            changed = True

        for i,child in enumerate(tail(tree)):
            if head(child) == 'rules_list':
                # found. now flatten
                new_rules_list = ['rules_list']
                for option in tail(child):
                    new_rules_list.append(['rule'])
                    # for each rule in rules_list                
                    for j,child2 in enumerate(tail(tree)):
                        if j == i:
                            new_rules_list[-1].append(option)
                        else:
                            new_rules_list[-1].append(child2)
                tree[:] = new_rules_list
                return True # changed

        for i, child in tail(enumerate(tree)):
            if isinstance(child, str) and child.startswith("'"):
                try:
                    tok_name = self.tokendefs[child]
                except KeyError:
                    tok_name = self._get_new_tok_name()
                    self.tokendefs[child] = tok_name
                    self._rules_to_add.append(['tokendef', tok_name, child])
                tree[i] = tok_name
                changed = True

        return changed # Not changed

    def rule_into(self, tree):
        assert 2 <= len(tree) <= 3
        if len(tree) > 2:
            rule, filter_list = tree[1], tree[2]
            new_name = self._get_new_rule_name()
            new_rule = ['ruledef', '@'+new_name, ['rules_list', ['rule', rule]]]
            self._rules_to_add.append(new_rule)
            self.filters[new_name] = (
                    map(int, (n for n in tail(filter_list) if not n.startswith('^'))),
                    map(int, (n[1:] for n in tail(filter_list) if n.startswith('^')))
                )
            tree[:] = ['rule', new_name]
            return True
        else:
            tree[:] = tree[1]

    def rules_list(self, tree):
        return self._flatten(tree, 'rules_list')

class ToPlyGrammar_Tranformer(Transformer):
    """Transforms grammar into ply-compliant grammar
    This is only a partial transformation that should be post-processd in order to apply
    XXX Probably a bad class name
    """
    def rules_list(self, tree):
        return '\n\t| '.join(tail(tree))

    def rule(self, tree):
        return ' '.join(tail(tree))

    def extrule(self, tree):
        return ' '.join(tail(tree))

    def oper(self, tree):
        return '(%s)%s'%(' '.join(tree[1:-1]), tree[-1])

    def ruledef(self, tree):
        return 'rule', tree[1], '%s\t: %s'%(tree[1], tree[2])

    def tokendef(self, tree):
        if len(tree) > 3:
            return 'token_with_mods', tree[1], [tree[2], tree[3]]
        else:
            return 'token', tree[1], tree[2]

    def grammar(self, tree):
        return list(tail(tree))

    def extgrammar(self, tree):
        return list(tail(tree))


class SimplifySyntaxTree_Visitor(Visitor):
    def __init__(self, rules_to_flatten, rules_to_expand):
        self.rules_to_flatten = set(rules_to_flatten)
        self.rules_to_expand = set(rules_to_expand)
        Visitor.__init__(self)

    def _flatten(self, tree):
        for i in range(len(tree)-1, 0, -1):   # skips 0
            if not is_sexp(tree[i]):
                continue
            assert len(tree[i])
            # -- Is empty branch? (list with len=1)
            if len(tree[i]) == 1:
                del tree[i] # removes empty branches
            # -- Is branch same rule as self and the rule should be flattened?
            elif head(tree[i]) == head(tree) and head(tree[i]) in self.rules_to_flatten:
                assert len(tree[i]), str(tree)
                tree[i:i+1] = tail(tree[i])
            # -- Should rule be expanded?
            elif head(tree[i]) in self.rules_to_expand:
                assert len(tree[i]), str(tree)
                tree[i:i+1] = tail(tree[i])

    def default(self, tree):
        self._flatten(tree)

class FilterSyntaxTree_Visitor(Visitor):
    def __init__(self, filters):
        self.filters = filters

    def default(self, tree):
        if head(tree) in self.filters:
            pos_filter, neg_filter = self.filters[head(tree)]
            neg_filter = [x if x>=0 else x+len(tree) for x in neg_filter]
            tree[1:] = [x for i,x in tail(enumerate(tree)) 
                    if (not pos_filter or i in pos_filter)
                    and (not neg_filter or i not in neg_filter)
                ]


class TokValue(str):
    #def __repr__(self):
    #    return repr("%s:%s|%s"%(self.line, self.column, self))
    pass

class LexerWrapper(object):
    def __init__(self, lexer, newline_tokens_names, newline_char='\n', ignore_token_names=()):
        self.lexer = lexer
        self.newline_tokens_names = newline_tokens_names
        self.ignore_token_names = ignore_token_names
        self.newline_char = newline_char

        self.current_state = lexer.current_state
        self.begin = lexer.begin


    def input(self, s):
        self.lineno = 1
        self._lexer_pos_of_start_column = -1
        self._tok_count = 0
        return self.lexer.input(s)

    def _handle_newlines(self, t):
        newlines = t.value.count(self.newline_char)
        self.lineno += newlines

        if newlines:
            #newline_text, trailing_text = t.value.rsplit( self.newline_char, 1 )
            #self._lexer_pos_of_start_column = t.lexpos + len(newline_text)
            self._lexer_pos_of_start_column = t.lexpos + t.value.rindex(self.newline_char)
        else:
            self._lexer_pos_of_start_column = t.lexpos 

    def token(self):
        # get a new token that shouldn't be ignored
        while True:
            t = self.lexer.token()
            if not t:
                return t
            if t.type not in self.ignore_token_names:
                break
            if t.type in self.newline_tokens_names:
                self._handle_newlines(t)

        # create a tok_value
        tok_value = TokValue(t.value)
        tok_value.line = self.lineno
        tok_value.column = t.lexpos-self._lexer_pos_of_start_column
        tok_value.pos_in_stream = t.lexpos
        tok_value.type = t.type
        tok_value.index = self._tok_count

        # handle line and column
        # must happen after assigning, because we want the start, not the end
        if t.type in self.newline_tokens_names:
            self._handle_newlines(t)


        if hasattr(t, 'lexer'):
            t.lexer.lineno = self.lineno    # why not self.lexer ?

        self._tok_count += 1

        t.lineno = self.lineno  # XXX may change from tok_value.line. On purpose??
        t.value = tok_value
        return t
        


class Grammar(object):

    def __init__(self, grammar, debug=False, just_lex=False, ignore_postproc=False):
        self.tokens = []    # for lex module
        self.rules_to_flatten = []
        self.rules_to_expand = []
        self._newline_tokens = set()
        self._ignore_tokens = set()
        self.lexer_postproc = None
        self._newline_value = '\n'

        if isinstance(grammar, file):
            # PLY turns "a.b" into "b", so gotta get rid of the dot.
            tab_filename = "parsetab_%s"%grammar.name.replace('.', '_')
            grammar = grammar.read()
        else:
            tab_filename = "parsetab_%s"%str(hash(grammar)%2**32)
            assert isinstance(grammar, str)

        grammar_tree = grammar_parser.parse(grammar, debug=debug)
        if not grammar_tree:
            raise Exception("Parse Error")

        self.filters = {}
        grammar_tree = SimplifyGrammar_Visitor('simp_', self.filters).visit(grammar_tree)
        ply_grammar_and_code = ToPlyGrammar_Tranformer().transform(grammar_tree)

        # code may be omitted
        if len(ply_grammar_and_code) == 2:
            code = ply_grammar_and_code[1]
        else:
            assert len(ply_grammar_and_code) == 1
            code = ''
        ply_grammar = ply_grammar_and_code[0]
        
        for type, name, defin in ply_grammar:
            if type=='token':
                assert defin[0] == "'"
                assert defin[-1] == "'"
                self.add_token(name, defin)
            elif type=='token_with_mods':
                self.add_token_with_mods(name, defin)
            elif type=='rule':
                self.add_rule(name, defin)
            elif type=='optiondef':
                self.handle_option(name, defin)
            else:
                assert False, type

        exec(code)

        lexer = lex.lex(module=self)
        lexer = LexerWrapper(lexer, newline_tokens_names=self._newline_tokens, newline_char=self._newline_value, ignore_token_names=self._ignore_tokens)
        if self.lexer_postproc and not ignore_postproc:
            lexer = self.lexer_postproc(lexer)

        self.lexer = lexer
        if not just_lex:
            self.parser = yacc.yacc(module=self, debug=debug, tabmodule=tab_filename)

    def lex(self, text):
        self.lexer.input(text)
        toks = []
        tok = self.lexer.token()
        while tok:
            toks.append(tok)
            tok = self.lexer.token()
        return toks

    def parse(self, text):
        tree = self.parser.parse(text, lexer=self.lexer)
        if not tree:
            raise Exception("Parse error!")
        FilterSyntaxTree_Visitor(self.filters).visit(tree)
        SimplifySyntaxTree_Visitor(self.rules_to_flatten, self.rules_to_expand).visit(tree)
        return tree

    def handle_option(self, name, defin):
        if name == '%newline_char':
            self._newline_value = eval(defin)   # XXX BAD BAD! I have TODO it differently
        else:
            print "Unknown option:", name

    @staticmethod
    def _unescape_token_def(token_def):
        assert token_def[0] == "'" == token_def[-1]
        return token_def[1:-1].replace(r"\'", "'")

    def add_token_with_mods(self, name, defin):
        re_defin, token_mods = defin

        token_added = False
        for token_mod in tail(token_mods):
            mod, modtokenlist = tail(token_mod)
        
            if mod == '%unless':
                assert not token_added, "token already added, can't issue %unless"
                unless_toks_dict = {}
                for modtoken in tail(modtokenlist):
                    assert head(modtoken) == 'token'
                    modtok_name, modtok_value = tail(modtoken)

                    self.add_token(modtok_name, modtok_value)
                     
                    unless_toks_dict[ self._unescape_token_def(modtok_value) ] = modtok_name


                self.tokens.append(name)

                code = ('\tt.type = self._%s_unless_toks_dict.get(t.value, %r)\n' % (name, name)
                       +'\treturn t')
                s = ('def t_%s(self, t):\n\t%s\n%s\nx = t_%s\n'
                    %(name, re_defin, code, name))
                exec(s)

                setattr(self, 't_%s'%name, x.__get__(self))
                setattr(self, '_%s_unless_toks_dict'%name, unless_toks_dict)

                token_added = True

            elif mod == '%newline':
                assert len(modtokenlist) == 1
                self._newline_tokens.add(name)

            elif mod == '%ignore':
                assert len(modtokenlist) == 1
                self._ignore_tokens.add(name)
            else:
                assert False

        if not token_added:
            self.add_token(name, re_defin)            

    def add_token(self, name, defin):
        self.tokens.append(name)
        setattr(self, 't_%s'%name, self._unescape_token_def(defin))


    def add_rule(self, rule_name, rule_def):
        mods, name = re.match('([@#?]*)(.*)', rule_name).groups()
        if mods:
            assert rule_def[:len(mods)] == mods
            rule_def = rule_def[len(mods):]
            rule_name = rule_name[len(mods):]

        if '@' in mods:
            self.rules_to_expand.append( rule_name )
        elif '#' in mods:
            self.rules_to_flatten.append( rule_name )

        if '?' in mods or '@' in mods:  # @ is here just for the speed-up
            code = '\tp[0] = ([%r] + p[1:]) if len(p)>2 else p[1]' % rule_name
        else:
            code = '\tp[0] = [%r] + p[1:]' % rule_name
        s = ('def p_%s(p):\n\t%r\n%s\nx = p_%s\n'
            %(rule_name, rule_def, code, rule_name))
        exec(s)

        setattr(self, 'p_%s'%rule_name, x)


    @staticmethod
    def t_error(t):
        raise Exception("Illegal character in input: '%s', line: %s, %s" % (t.value[:32], t.lineno, t.type))

    def p_error(self, p):
        if p:
            if isinstance(p.value, TokValue):
                print "Syntax error in input at '%s' (type %s)" % (p.value,p.type), 'line',p.value.line, 'col', p.value.column
            else:
                print "Syntax error in input at '%s' (type %s)" % (p.value,p.type), 'line',p.lineno
        else:
            print "Syntax error in input (details unknown)", p

    start = "start"


