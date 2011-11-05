import re, os

from ply import lex, yacc

import grammar_parser

from sexp import Visitor, Transformer, head, tail, is_sexp

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


class ReconstructedLine(object):
    DEFAULT_CHAR = ' ';
    def __init__(self, allow_overwrite=False):
        self.allow_overwrite = allow_overwrite
        self.line = bytearray()
    def add_text(self, text, column):
        end_column = column + len(text)
        if len(self.line) < end_column:
            self.line += self.DEFAULT_CHAR * ( end_column - len(self.line) )
        if not self.allow_overwrite and self.line[column:end_column].strip(self.DEFAULT_CHAR):
            raise Exception('Cannot add text: location already used')
        self.line[column:end_column] = text
    def __str__(self):
        return str(self.line)

class ReconstructedText(object):
    def __init__(self, allow_overwrite=False):
        self.allow_overwrite = allow_overwrite
        self.lines = {}
    def add_text(self, text, line, column):
        if '\n' in text:
            for text2 in text.split('\n'):
                self.add_text(text2, line, column)
                line += 1
                column = 0
            return

        if line not in self.lines:
            self.lines[line] = ReconstructedLine(allow_overwrite=self.allow_overwrite)
        self.lines[line].add_text(text, column)
    def __str__(self):
        text = []
        lines = dict(self.lines)
        while lines:
            try:
                text.append( str(lines.pop(len(text))) )
            except KeyError:
                text.append( '' )
        return '\n'.join(text)

class ReconstructInput(Visitor):
    def __init__(self):
        self.text = ReconstructedText()
    def default(self, tree):
        for child in tail(tree):
            if not is_sexp(child) and child and child.strip():
                assert type(child) == TokValue, '%r %s'%(child, type(child))
                self.text.add_text(str(child), child.line, child.column)
                print '*', child
    def get(self):
        return str(self.text)


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

class GetTokenDefs_Visitor(Visitor):
    def __init__(self, dict_to_populate):
        self.tokendefs = dict_to_populate

    def tokendef(self, tree):
        self.tokendefs[ tree[2] ] = tree[1]

class ExtractSubgrammars_Visitor(Visitor):
    def __init__(self, parent_source_name, parent_tab_filename, parent_options):
        self.parent_source_name = parent_source_name
        self.parent_tab_filename = parent_tab_filename
        self.parent_options = parent_options

        self.last_tok = None

    def pre_tokendef(self, tok):
        self.last_tok = tok[1]
    def subgrammar(self, tree):
        assert self.last_tok
        assert len(tree) == 2
        source_name = '%s:%s'%(self.parent_source_name, self.last_tok.lower())
        tab_filename = '%s_%s'%(self.parent_tab_filename, self.last_tok.lower())
        subgrammar = _Grammar(tree[1], source_name, tab_filename, **self.parent_options)
        tree[:] = ['subgrammarobj', subgrammar]

class ApplySubgrammars_Visitor(Visitor):
    def __init__(self, subgrammars):
        self.subgrammars = subgrammars
    def default(self, tree):
        for i,tok in tail(enumerate(tree)):
            if type(tok) == TokValue and tok.type in self.subgrammars:
                parsed_tok = self.subgrammars[tok.type].parse(tok)
                assert parsed_tok[0] == 'start'
                tree[i] = parsed_tok

class SimplifyGrammar_Visitor(Visitor):
    ANON_RULE_ID = 'anon'
    ANON_TOKEN_ID = 'ANON'

    def __init__(self, filters, expand_all_repeaters=False):
        self._count = 0
        self._rules_to_add = []
        self.filters = filters

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
        rule_operand = tree[1]
        operator = tree[2]
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
            new_rule = ['ruledef', mod+new_name, ['rules_list', ['rule', rule_operand], ['rule', new_name, rule_operand]] ]
            self._rules_to_add.append(new_rule)
            tree[:] = ['rules_list', ['rule', new_name], ['rule']]
        elif operator in ('+', '@+'):
            # a : b c+ d;
            #  -->
            # a : b _c d;
            # _c : _c c | c;
            new_name = self._get_new_rule_name() + '_plus'
            mod = '@' if operator.startswith('@') else self.default_rule_mod
            new_rule = ['ruledef', mod+new_name, ['rules_list', ['rule', rule_operand], ['rule', new_name, rule_operand]] ]
            self._rules_to_add.append(new_rule)
            tree[:] = ['rule', new_name]
        elif operator == '?':
            tree[:] = ['rules_list', rule_operand, ['rule']]
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
                    tok_name = self._get_new_tok_name(child) # Add anonymous token
                    self.tokendefs[child] = tok_name
                    self._rules_to_add.append(['tokendef', tok_name, child])
                tree[i] = tok_name
                changed = True

        return changed # Not changed

    def rule_into(self, tree):  # XXX deprecated?
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

class FilterTokens_Tranformer(Transformer):
    def default(self, tree):
        if len(tree) <= 2:
            return tree
        return [tree[0]] + [x for x in tail(tree) if is_sexp(x)]

class TokValue(str):
    def __new__(cls, s, type=None, line=None, column=None, pos_in_stream=None, index=None):
        inst = str.__new__(cls,s)
        inst.type = type
        inst.line = line
        inst.column = column
        inst.pos_in_stream = pos_in_stream
        inst.index = index
        return inst

    def __repr__(self):
        if self.line and self.column:
            return repr("%s:%s|%s"%(self.line, self.column, self))
        return str.__repr__(self)

class LexerWrapper(object):
    def __init__(self, lexer, newline_tokens_names, newline_char='\n', ignore_token_names=(), reconstructable_input=False):
        self.lexer = lexer
        self.newline_tokens_names = set(newline_tokens_names)
        self.ignore_token_names = ignore_token_names
        self.newline_char = newline_char

        self.current_state = lexer.current_state
        self.begin = lexer.begin

        self.last_token = None
        self.reconstructable_input = reconstructable_input
        self.all_tokens = []


    def input(self, s):
        self.lineno = 1
        self._lexer_pos_of_start_column = -1
        self._tok_count = 0
        return self.lexer.input(s)

    def _handle_newlines(self, t):
        newlines = t.value.count(self.newline_char)
        self.lineno += newlines

        if newlines:
            self._lexer_pos_of_start_column = t.lexpos + t.value.rindex(self.newline_char)
        else:
            self._lexer_pos_of_start_column = t.lexpos

    def token(self):
        # get a new token that shouldn't be ignored
        while True:
            t = self.lexer.token()
            self._tok_count += 1
            if not t:
                return t
            try:
                wrapped = False
                if self.reconstructable_input:
                    self._wrap_token(t)
                    self.all_tokens.append( t.value )
                    wrapped = True
                if t.type not in self.ignore_token_names:
                    if not wrapped:
                        self._wrap_token(t)
                    return t
            finally:
                # handle line and column
                # must happen after assigning, because we want the start, not the end
                # in other words, we want to apply the token's effect to the lexer, not to itself
                if t.type in self.newline_tokens_names:
                    self._handle_newlines(t)

    def _wrap_token(self, t):
        tok_value = TokValue(t.value,
                        line = self.lineno,
                        column = t.lexpos-self._lexer_pos_of_start_column,
                        pos_in_stream = t.lexpos,
                        type = t.type,
                        index = self._tok_count,
                    )
        if self.reconstructable_input:
                tok_value.rel_line = tok_value.line - (self.last_token.line if self.last_token else 0)
                tok_value.rel_column = tok_value.column - (self.last_token.column if self.last_token else 0)
                tok_value.rel_token = self.last_token
                self.last_token = tok_value

        if hasattr(t, 'lexer'):
            t.lexer.lineno = self.lineno    # not self.lexer, because it may be another wrapper

        t.lineno = self.lineno
        t.value = tok_value
        return t


class Grammar(object):
    def __init__(self, grammar, **options):
        self.tokens = []    # for lex module
        self.rules_to_flatten = []
        self.rules_to_expand = []
        self._newline_tokens = set()
        self._ignore_tokens = set()
        self.lexer_postproc = None
        self._newline_value = '\n'

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
        self.auto_filter_tokens=bool(options.pop('auto_filter_tokens', False))
        self.expand_all_repeaters=bool(options.pop('expand_all_repeaters', False))
        self.reconstructable_input=bool(options.pop('reconstructable_input', False))
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
        self.filters = {}
        ExtractSubgrammars_Visitor(source_name, tab_filename, self.options).visit(grammar_tree)
        grammar_tree = SimplifyGrammar_Visitor(self.filters, expand_all_repeaters=self.expand_all_repeaters).visit(grammar_tree)
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
        lexer = LexerWrapper(lexer, newline_tokens_names=self._newline_tokens, newline_char=self._newline_value, ignore_token_names=self._ignore_tokens, reconstructable_input=self.reconstructable_input)
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
        if self.filters:
            FilterSyntaxTree_Visitor(self.filters).visit(tree)

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
        if head(token_features) == 'subgrammarobj':
            assert len(token_features) == 2
            self.subgrammars[name] = token_features[1]
        elif head(token_features) == 'tokenmods':
            for token_mod in tail(token_features):
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
                    raise GrammarException("Unknown token modifier: %s" % mod)
        else:
            raise GrammarException("Unknown token feature: %s" % head(token_features))

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


