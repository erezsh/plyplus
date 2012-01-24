import re, os

from ply import lex, yacc

import grammar_parser

from strees import STree, SVisitor, STransformer, is_stree

# -- Must!
#TODO: Offer alternatives to PLY facilities: precedence, error, line-count
#TODO: Allow empty rules
#TODO: Support States
#TODO: @ on start symbols should expand them (right now not possible because of technical issues)
#      alternatively (but not as good?): add option to expand all 'start' symbols

# -- Nice to have
#TODO: Recursive parsing
#TODO: find better terms than expand and flatten
#TODO: Exact recovery of input (as text attr)
#      Allow to reconstruct the input with whatever changes were made to the tree
#TODO: Allow 'optimize' mode
#TODO: Rule Self-recursion (an operator? a 'self' keyword?)
#TODO: Add token history on parse error
#TODO: Add rule history on parse error?

# -- Unknown status
#TODO: Multiply defined tokens (just concatinate with |?)
#TODO: Complete EOF handling in python grammar (postlex)
#TODO: Make filter behaviour consitent for both ()? and ()* / ()+
#TODO: a (b c d => 1 2) e
#TODO: better filters
#TODO: Offer mechanisms to easily avoid ambiguity (expr: expr '\+' expr etc.)
#TODO: Change rule+ into "rule simp*" instead of "simp+"
#TODO: Use PLY's ignore mechanism (=tokens return None) instead of post-filtering it myself?
#TODO: Support Compiling grammars into a single parser python file
#TODO: Multi-line comments
#TODO: Support running multi-threaded
#TODO: Better error handling (choose between prints and raising exception, setting threshold, etc.)
#TODO: Better debug mode (set debug level, choose between prints and interactive debugging?)

# -- Continual Tasks
#TODO: Optimize for space
#TODO: Optimize for speed
#TODO: require less knowledge of ply
#TODO: meaningful names to anonymous tokens

# -- Done
#DONE: anonymous tokens
#DONE: Resolve errors caused by dups of tokens
#DONE: Allow comments in grammar
#DONE: (a+)? is different from a*
#       print_stmt : PRINT (RIGHTSHIFT? test (COMMA test)* COMMA?)?  ;
#           --> only works as -->
#       print_stmt : PRINT (RIGHTSHIFT? test ((COMMA test)+)? COMMA?)?  ;
#
#      Similarly:
#      dictmaker : test COLON test (COMMA test COLON test)* COMMA? ;
#           --> only works as -->
#      dictmaker : test COLON test (COMMA test COLON test)+? COMMA? ;
#DONE: rename simps
#


def get_token_name(token, default):
    return {
        ':' : 'COLON',
        ',' : 'COMMA',
        ';' : 'SEMICOLON',
        '+' : 'PLUS',
        '-' : 'MINUS',
        '*' : 'STAR',
        '/' : 'SLASH',
        '|' : 'VBAR',
        '!' : 'BANG',
        '?' : 'QMARK',
        '#' : 'HASH',
        '$' : 'DOLLAR',
        '&' : 'AMPERSAND',
        '<' : 'LESSTHAN',
        '>' : 'MORETHAN',
        '=' : 'EQUAL',
        '.' : 'DOT',
        '%' : 'PERCENT',
        '`' : 'BACKQUOTE',
        '^' : 'CIRCUMFLEX',
        '"' : 'DBLQUOTE',
        '\'' : 'QUOTE',
        '~' : 'TILDE',
        '@' : 'AT',
        '(' : 'LPAR',
        ')' : 'RPAR',
        '{' : 'LBRACE',
        '}' : 'RBRACE',
        '[' : 'LSQB',
        ']' : 'RSQB',
    }.get( token, default)

class GrammarException(Exception): pass

class GetTokenDefs_Visitor(SVisitor):
    def __init__(self, dict_to_populate):
        self.tokendefs = dict_to_populate

    def tokendef(self, tree):
        self.tokendefs[ tree.tail[1] ] = tree.tail[0]

class ExtractSubgrammars_Visitor(SVisitor):
    def __init__(self, parent_source_name, parent_tab_filename, parent_options):
        self.parent_source_name = parent_source_name
        self.parent_tab_filename = parent_tab_filename
        self.parent_options = parent_options

        self.last_tok = None

    def pre_tokendef(self, tok):
        self.last_tok = tok.tail[0]
    def subgrammar(self, tree):
        assert self.last_tok
        assert len(tree.tail) == 1
        source_name = '%s:%s'%(self.parent_source_name, self.last_tok.lower())
        tab_filename = '%s_%s'%(self.parent_tab_filename, self.last_tok.lower())
        subgrammar = _Grammar(tree.tail[0], source_name, tab_filename, **self.parent_options)
        tree.head, tree.tail = 'subgrammarobj', [subgrammar]

class ApplySubgrammars_Visitor(SVisitor):
    def __init__(self, subgrammars):
        self.subgrammars = subgrammars
    def default(self, tree):
        for i,tok in enumerate(tree.tail):
            if type(tok) == TokValue and tok.type in self.subgrammars:
                parsed_tok = self.subgrammars[tok.type].parse(tok)
                assert parsed_tok[0] == 'start'
                tree.tail[i] = parsed_tok

class SimplifyGrammar_Visitor(SVisitor):
    ANON_RULE_ID = 'anon'
    ANON_TOKEN_ID = 'ANON'

    def __init__(self, expand_all_repeaters=False):
        self._count = 0
        self._rules_to_add = []

        self.default_rule_mod = '@' if expand_all_repeaters else '#'

        self.tokendefs = {} # to be populated at visit

    def _get_new_rule_name(self):
        s = '_%s_%d'%(self.ANON_RULE_ID, self._count)
        self._count += 1
        return s

    def _get_new_tok_name(self, tok):
        s = '_%s_%d'%(get_token_name(tok[1:-1], self.ANON_TOKEN_ID), self._count)
        self._count += 1
        return s

    def _flatten(self, tree, name):
        to_expand = [i for i, subtree in enumerate(tree.tail) if is_stree(subtree) and subtree.head == name]
        if to_expand:
            tree.expand_kids(*to_expand)
            return True
        else:
            return False

    def visit(self, tree):
        GetTokenDefs_Visitor(self.tokendefs).visit(tree)
        self._visit(tree)
        return tree

    def _visit(self, tree):
        "_visit simplifies the tree as much as possible"
        # visit until nothing left to change (not the most efficient, but good enough)
        while SVisitor._visit(self, tree):
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
            tree.tail += self._rules_to_add
        self._rules_to_add = []
        return changed

    def _add_recurse_rule(self, mod, name, repeated_expr):
        new_rule = STree('ruledef', [mod+name, STree('rules_list', [STree('rule', [repeated_expr]), STree('rule', [name, repeated_expr])]) ])
        self._rules_to_add.append(new_rule)
        return new_rule

    def oper(self, tree):
        rule_operand, operator = tree.tail

        if operator in ('*', '@*'):
            # a : b c* d;
            #  --> in theory
            # a : b _c d;
            # _c : c _c |;
            #  --> in practice (much faster with PLY, approx x2)
            # a : b _c d | b d;
            # _c : _c c | c;
            new_name = self._get_new_rule_name() + '_star'
            mod = '@' if operator.startswith('@') else self.default_rule_mod
            self._add_recurse_rule(mod, new_name, rule_operand)
            tree.head, tree.tail = 'rules_list', [STree('rule', [new_name]), STree('rule', [])]
        elif operator in ('+', '@+'):
            # a : b c+ d;
            #  -->
            # a : b _c d;
            # _c : _c c | c;
            new_name = self._get_new_rule_name() + '_plus'
            mod = '@' if operator.startswith('@') else self.default_rule_mod
            self._add_recurse_rule(mod, new_name, rule_operand)
            tree.head, tree.tail = 'rule', [new_name]
        elif operator == '?':
            tree.head, tree.tail = 'rules_list', [rule_operand, STree('rule', [])]
        else:
            assert False, rule_operand

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

        for i,child in enumerate(tree.tail):
            if is_stree(child) and child.head == 'rules_list':
                # found. now flatten
                new_rules_list = []
                for option in child.tail:
                    new_rules_list.append(STree('rule', []))
                    # for each rule in rules_list
                    for j,child2 in enumerate(tree.tail):
                        if j == i:
                            new_rules_list[-1].tail.append(option)
                        else:
                            new_rules_list[-1].tail.append(child2)
                tree.head, tree.tail = 'rules_list', new_rules_list
                return True # changed

        for i, child in enumerate(tree.tail):
            if isinstance(child, str) and child.startswith("'"):
                try:
                    tok_name = self.tokendefs[child]
                except KeyError:
                    tok_name = self._get_new_tok_name(child) # Add anonymous token
                    self.tokendefs[child] = tok_name
                    self._rules_to_add.append(STree('tokendef', [tok_name, child]))
                tree.tail[i] = tok_name
                changed = True

        return changed # Not changed

    def rules_list(self, tree):
        return self._flatten(tree, 'rules_list')

class ToPlyGrammar_Tranformer(STransformer):
    """Transforms grammar into ply-compliant grammar
    This is only a partial transformation that should be post-processd in order to apply
    XXX Probably a bad class name
    """
    def rules_list(self, tree):
        return '\n\t| '.join(tree.tail)

    def rule(self, tree):
        return ' '.join(tree.tail)

    def extrule(self, tree):
        return ' '.join(tree.tail)

    def oper(self, tree):
        return '(%s)%s'%(' '.join(tree.tail[:-1]), tree.tail[-1])

    def ruledef(self, tree):
        return STree('rule', (tree.tail[0], '%s\t: %s'%(tree.tail[0], tree.tail[1])))

    def tokendef(self, tree):
        if len(tree.tail) > 2:
            return STree('token_with_mods', [tree.tail[0], tree.tail[1:]])
        else:
            return STree('token', tree.tail)

    def grammar(self, tree):
        return tree.tail

    def extgrammar(self, tree):
        return tree.tail


class SimplifySyntaxTree_Visitor(SVisitor):
    def __init__(self, rules_to_flatten, rules_to_expand):
        self.rules_to_flatten = set(rules_to_flatten)
        self.rules_to_expand = set(rules_to_expand)
        SVisitor.__init__(self)

    def _flatten(self, tree):
        # Expand/Flatten rules if requested in grammar
        to_expand = [i for i, subtree in enumerate(tree.tail) if is_stree(subtree) and (
                        (subtree.head == tree.head and subtree.head in self.rules_to_flatten)
                        or (subtree.head in self.rules_to_expand)
                    ) ]
        tree.expand_kids(*to_expand)

        # Remove empty trees ( XXX not strictly necessary, just cleaner... should I keep them?)
        to_remove = [i for i, subtree in enumerate(tree.tail) if is_stree(subtree) and not subtree.tail]
        tree.remove_kids(*to_remove)

    def __default__(self, tree):
        self._flatten(tree)

class FilterTokens_Tranformer(STransformer):
    def __default__(self, tree):
        if len(tree.tail) <= 1:
            return tree
        return STree(tree.head, [x for x in tree.tail if is_stree(x)])

class TokValue(str):
    #def __repr__(self):
    #    return repr("%s:%s|%s"%(self.line, self.column, self))
    pass

class LexerWrapper(object):
    def __init__(self, lexer, newline_tokens_names, newline_char='\n', ignore_token_names=()):
        self.lexer = lexer
        self.newline_tokens_names = set(newline_tokens_names)
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
    def __init__(self, grammar, **options):
        if isinstance(grammar, file):
            # PLY turns "a.b" into "b", so gotta get rid of the dot.
            tab_filename = "parsetab_%s"%os.path.split(grammar.name)[1].replace('.', '_')
            source = grammar.name
            grammar = grammar.read()
        else:
            assert isinstance(grammar, str)
            tab_filename = "parsetab_%s"%str(hash(grammar)%2**32)
            source = '<string>'

        grammar_tree = grammar_parser.parse(grammar, debug=options.get('debug',False))
        if not grammar_tree:
            raise GrammarException("Parse Error")

        self._grammar = _Grammar(grammar_tree, source, tab_filename, **options)

    def lex(self, text):
        return self._grammar.lex(text)

    def parse(self, text):
        return self._grammar.parse(text)

class _Grammar(object):
    def __init__(self, grammar_tree, source_name, tab_filename, **options):
        self.options = dict(options)
        self.debug=bool(options.pop('debug', False))
        self.just_lex=bool(options.pop('just_lex', False))
        self.ignore_postproc=bool(options.pop('ignore_postproc', False))
        self.auto_filter_tokens=bool(options.pop('auto_filter_tokens', True))
        self.expand_all_repeaters=bool(options.pop('expand_all_repeaters', False))
        if options:
            raise TypeError("Unknown options: %s"%options.keys())

        self.tab_filename = tab_filename
        self.source_name = source_name
        self.tokens = []    # for lex module
        self.rules_to_flatten = []
        self.rules_to_expand = []
        self._newline_tokens = set()
        self._ignore_tokens = set()
        self.lexer_postproc = None
        self._newline_value = '\n'

        self.subgrammars = {}
        ExtractSubgrammars_Visitor(source_name, tab_filename, self.options).visit(grammar_tree)
        grammar_tree = SimplifyGrammar_Visitor(expand_all_repeaters=self.expand_all_repeaters).visit(grammar_tree)
        ply_grammar_and_code = ToPlyGrammar_Tranformer().transform(grammar_tree)

        self.STree = STree

        # code may be omitted
        if len(ply_grammar_and_code) == 2:
            code = ply_grammar_and_code[1]
        else:
            assert len(ply_grammar_and_code) == 1
            code = ''
        ply_grammar = ply_grammar_and_code[0]

        for x in ply_grammar:
            type, (name, defin) = x.head, x.tail
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
        if self.lexer_postproc and not self.ignore_postproc:
            lexer = self.lexer_postproc(lexer)

        self.lexer = lexer
        if not self.just_lex:
            self.parser = yacc.yacc(module=self, debug=self.debug, tabmodule=tab_filename)

    def __repr__(self):
        return '<Grammar from %s, tab at %s>' % (self.source_name, self.tab_filename)

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

        # Apply subgrammars
        if self.subgrammars:
            ApplySubgrammars_Visitor(self.subgrammars).visit(tree)

        if self.auto_filter_tokens:
            tree = FilterTokens_Tranformer().transform(tree)
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
        re_defin, token_features = defin

        token_added = False
        if token_features.head == 'subgrammarobj':
            assert len(token_features.tail) == 1
            self.subgrammars[name] = token_features.tail[0]
        elif token_features.head == 'tokenmods':
            for token_mod in token_features.tail:
                mod, modtokenlist = token_mod.tail

                if mod == '%unless':
                    assert not token_added, "token already added, can't issue %unless"
                    unless_toks_dict = {}
                    for modtoken in modtokenlist.tail:
                        assert modtoken.head == 'token'
                        modtok_name, modtok_value = modtoken.tail

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
                    assert len(modtokenlist.tail) == 0
                    self._newline_tokens.add(name)

                elif mod == '%ignore':
                    assert len(modtokenlist.tail) == 0
                    self._ignore_tokens.add(name)
                else:
                    raise GrammarException("Unknown token modifier: %s" % mod)
        else:
            raise GrammarException("Unknown token feature: %s" % token_features.head)

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
            code = '\tp[0] = STree(%r, p[1:]) if len(p)>2 else p[1]' % rule_name
        else:
            code = '\tp[0] = STree(%r, p[1:])' % rule_name
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


