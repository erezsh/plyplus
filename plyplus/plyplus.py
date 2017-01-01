"Author: Erez Shinan, erezshin at gmail.com"

from __future__ import absolute_import

import re
import os
import itertools
import logging
import ast
import hashlib
import codecs
try:
    import cPickle as pickle
except ImportError:
    import pickle

from . import __version__, PLYPLUS_DIR, grammar_parser
from .utils import StringTypes, list_join, StringType
from .common import TokValue, GrammarException, ParseError

from .strees import STree, SVisitor, STransformer, is_stree, SVisitor_Recurse

from .engine_ply import Engine_PLY
from .engine_pearley import Engine_Pearley

# -- Must!
#TODO: Support States
#TODO: @ on start symbols should expand them (right now not possible because of technical design issues)
#      alternatively (but not as good?): add option to expand all 'start' symbols

# -- Nice to have
#TODO: Operator precedence
#TODO: find better terms than expand and flatten
#TODO: Exact recovery of input (as text attr)
#      Allow to reconstruct the input with whatever changes were made to the tree
#TODO: Allow 'optimize' mode
#TODO: Rule Self-recursion (an operator? a 'self' keyword?)
#TODO: Add token history on parse error
#TODO: Add rule history on parse error?

# -- Unknown status
#TODO: Allow empty rules
#TODO: Multiply defined tokens (just concatinate with |?)
#TODO: Complete EOF handling in python grammar (postlex)
#TODO: Make filter behaviour consitent for both ()? and ()* / ()+
#TODO: better filters
#TODO: Offer mechanisms to easily avoid ambiguity (expr: expr '\+' expr etc.)
#TODO: Use PLY's ignore mechanism (=tokens return None) instead of post-filtering it myself?
#TODO: Support Compiling grammars into a single parser python file
#TODO: Support running multi-threaded
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
#DONE: Recursive parsing
#DONE: Change rule+ into "rule simp*" instead of "simp+"
#DONE: Multi-line comments
#DONE: Better error handling (choose between prints and raising exception, setting threshold, etc.)
#

logging.basicConfig()


_TOKEN_NAMES = {
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
}

def get_token_name(token, default):
    return _TOKEN_NAMES.get( token, default)


class RuleMods(object):
    EXPAND = '@'    # Expand all instances of rule
    FLATTEN = '#'   # Expand all nested instances of rule
    EXPAND1 = '?'   # Expand all instances of rule with only one child


class ExtractSubgrammars_Visitor(SVisitor):
    def __init__(self, parent_source_name, parent_tab_filename, parent_options):
        self.parent_source_name = parent_source_name
        self.parent_tab_filename = parent_tab_filename
        self.parent_options = parent_options

        self.last_tok = None

    def tokendef(self, tok):
        self.last_tok = tok.tail[0]
    def subgrammar(self, tree):
        assert self.last_tok
        assert len(tree.tail) == 1
        source_name = '%s:%s' % (self.parent_source_name, self.last_tok.lower())
        tab_filename = '%s_%s' % (self.parent_tab_filename, self.last_tok.lower())
        subgrammar = _Grammar(tree.tail[0], source_name, tab_filename, self.parent_options)
        tree.head, tree.tail = 'subgrammarobj', [subgrammar]

class ApplySubgrammars_Visitor(SVisitor):
    def __init__(self, subgrammars):
        self.subgrammars = subgrammars
    def __default__(self, tree):
        for i, tok in enumerate(tree.tail):
            if isinstance(tok, TokValue) and tok.type in self.subgrammars:
                parsed_tok = self.subgrammars[tok.type].parse(tok)
                assert parsed_tok.head == 'start'
                tree.tail[i] = parsed_tok


class CollectTokenDefs_Visitor(SVisitor):
    def __init__(self, dict_to_populate):
        self.tokendefs = dict_to_populate

    def tokendef(self, tree):
        self.tokendefs[ tree.tail[0] ] = tree

    fragmentdef = tokendef

def _unescape_token_def(token_def):
    assert token_def[0] == "'" == token_def[-1]
    return token_def[1:-1].replace(r"\'", "'")

def _simplify_tokendef(tokendef, tokendefs):
    token_value = tokendef.tail[1]
    if is_stree(token_value):
        assert token_value.head == 'tokenvalue'

        regexp = ''.join( _unescape_token_def(d)
                            if d.startswith("'")
                            else _simplify_tokendef(tokendefs[d], tokendefs)
                            for d in token_value.tail )
        tokendef.tail = list(tokendef.tail) # can't assign to a tuple
        tokendef.tail[1] = regexp

    return tokendef.tail[1]

def simplify_tokendefs(tree):
    tokendefs = {}
    CollectTokenDefs_Visitor(tokendefs).visit(tree)

    for tokendef in tokendefs.values():
        _simplify_tokendef(tokendef, tokendefs)

    return tokendefs


class NameAnonymousTokens_Visitor(SVisitor):
    ANON_TOKEN_ID = 'ANON'

    def __init__(self, tokendefs):
        self._count = itertools.count()
        self._rules_to_add = []

        self.token_name_from_value = {}
        for name, tokendef in tokendefs.items():
            self.token_name_from_value[tokendef.tail[1]] = name

    def _get_new_tok_name(self, tok):
        return '_%s_%d' % (get_token_name(tok[1:-1], self.ANON_TOKEN_ID), next(self._count))

    def rule(self, tree):
        for i, child in enumerate(tree.tail):
            if isinstance(child, StringTypes) and child.startswith("'"):
                child = _unescape_token_def(child)
                try:
                    tok_name = self.token_name_from_value[child]
                except KeyError:
                    tok_name = self._get_new_tok_name(child) # Add anonymous token
                    self.token_name_from_value[child] = tok_name    # for future anonymous occurences
                    self._rules_to_add.append(STree('tokendef', [tok_name, child]))
                tree.tail[i] = tok_name

    def grammar(self, tree):
        if self._rules_to_add:
            tree.tail += self._rules_to_add


class SimplifyGrammar_Visitor(SVisitor_Recurse):

    def _visit(self, tree):
        "_visit simplifies the tree as much as possible"
        # visit until nothing left to change (not the most efficient, but good enough since it's only the grammar)
        while SVisitor_Recurse._visit(self, tree):
            pass

    @staticmethod
    def _flatten(tree):
        to_expand = [i for i, subtree in enumerate(tree.tail) if is_stree(subtree) and subtree.head == tree.head]
        if to_expand:
            tree.expand_kids_by_index(*to_expand)
        return bool(to_expand)


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

        if self._flatten(tree):
            changed = True

        for i, rules_list in enumerate(tree.tail):
            if is_stree(rules_list) and rules_list.head == 'rules_list':
                # found. now flatten
                tree.head = 'rules_list'
                tree.tail = [STree('rule', [list_item if i==j else other
                                            for j, other in enumerate(tree.tail)])
                             for list_item in rules_list.tail ]
                return True # changed

        return changed


    modtokenlist = _flatten
    tokenmods = _flatten
    tokenvalue = _flatten
    number_list = _flatten
    rules_list = _flatten
    perm_phrase = _flatten
    grammar = _flatten


class ExpandOper_Visitor(SimplifyGrammar_Visitor):
    ANON_RULE_ID = 'anon'

    def __init__(self):
        self._count = itertools.count()
        self._rules_to_add = []

    def _get_new_rule_name(self):
        return '_%s_%d' % (self.ANON_RULE_ID, next(self._count))

    def grammar(self, tree):
        if self._rules_to_add:
            tree.tail += self._rules_to_add
            self._rules_to_add = []
            return True
        return False

    def _add_recurse_rule(self, mod, name, repeated_expr):
        new_rule = STree('ruledef', [mod+name, STree('rules_list', [STree('rule', [repeated_expr]), STree('rule', [name, repeated_expr])]) ])
        self._rules_to_add.append(new_rule)

    def oper(self, tree):
        rule_operand, operator = tree.tail

        if operator == '*':
            # a : b c* d;
            #  --> in theory
            # a : b _c d;
            # _c : _c c |;
            #  --> in practice (a bit faster with PLY, approx 20%)
            # a : b _c d | b d;
            # _c : _c c | c;
            new_name = self._get_new_rule_name() + '_star'
            self._add_recurse_rule(RuleMods.EXPAND, new_name, rule_operand)
            tree.head, tree.tail = 'rules_list', [STree('rule', [new_name]), STree('rule', [])]
        elif operator == '+':
            # a : b c+ d;
            #  -->
            # a : b _c d;
            # _c : _c c | c;
            new_name = self._get_new_rule_name() + '_plus'
            self._add_recurse_rule(RuleMods.EXPAND, new_name, rule_operand)
            tree.head, tree.tail = 'rule', [new_name]
        elif operator == '?':
            tree.head, tree.tail = 'rules_list', [rule_operand, STree('rule', [])]
        else:
            assert False, rule_operand

        return True # changed

    def perm_rule(self, tree):
        """ Transforms a permutation rule into a rules_list of the permutations.
            x : a ^ b ^ c
             -->
            x : a b c | a c b | b a c | b c a | c a b | c b a

            It also handles operators on rules to be permuted.
            x : a ^ b? ^ c
             -->
            x : a b c | a c b | b a c | b c a | c a b | c b a
              | a c   | c a

            x : a ^ ( b | c ) ^ d
             -->
            x : a b d | a d b | b a d | b d a | d a b | d b a
              | a c d | a d c | c a d | c d a | d a c | d c a

            You can also insert a separator rule between permutated rules.
            x : a ^ b ^ c ^^ Z
             -->
            x : a Z b Z c | a Z c Z b | b Z a Z c
              | b Z c Z a | c Z a Z b | c Z b Z a

            x : a ^ b? ^ c ^^ Z
             -->
            x : a Z b Z c | a Z c Z b | b Z a Z c
              | b Z c Z a | c Z a Z b | c Z b Z a
              | a Z c     | c Z a
        """
        rules = tree.tail[0].tail
        sep = tree.tail[1] if len(tree.tail) == 2 else None
        tree.head = 'rules_list'
        tree.tail = [STree('rule', rule_perm) for rule_perm in itertools.permutations(rules)]
        self._visit(tree)
        tree.tail = list(set(tree.tail))
        if sep:
            tree.tail = [STree('rule', list_join(rule.tail, sep))
                         for rule in tree.tail]
        return True



class GrammarTreeToList_Transformer(STransformer):
    """Transforms a grammar tree into a list of grammar elements"""

    @staticmethod
    def rules_list(tree):
        return tree.tail

    @staticmethod
    def rule(tree):
        return tree.tail
    #     return ' '.join(tree.tail)

    @staticmethod
    def ruledef(tree):
        return ('rule', tree.tail)

    @staticmethod
    def optiondef(tree):
        return ('option', tree.tail)

    @staticmethod
    def fragmentdef(tree):
        return ('fragment', [None, None])

    @staticmethod
    def tokendef(tree):
        if len(tree.tail) > 2:
            return ('token_with_mods', [tree.tail[0], tree.tail[1:]])
        else:
            return ('token', tree.tail)

    @staticmethod
    def grammar(tree):
        return tree.tail

    @staticmethod
    def extgrammar(tree):
        return tree.tail


class SimplifySyntaxTree_Visitor(SVisitor):
    def __init__(self, rules_to_flatten, rules_to_expand, keep_empty_trees):
        self.rules_to_flatten = frozenset(rules_to_flatten)
        self.rules_to_expand = frozenset(rules_to_expand)
        self.keep_empty_trees = bool(keep_empty_trees)

    def __default__(self, tree):
        # Expand/Flatten rules if requested in grammar
        to_expand = [i for i, subtree in enumerate(tree.tail) if is_stree(subtree) and (
                        (subtree.head == tree.head and subtree.head in self.rules_to_flatten)
                        or (subtree.head in self.rules_to_expand)
                    ) ]
        if to_expand:
            tree.expand_kids_by_index(*to_expand)

        # Remove empty trees if requested
        if not self.keep_empty_trees:
            to_remove = [i for i, subtree in enumerate(tree.tail) if is_stree(subtree) and not subtree.tail]
            if to_remove:
                tree.remove_kids_by_index(*to_remove)

class LexerWrapper(object):
    def __init__(self, lexer, newline_tokens_names, newline_char='\n', ignore_token_names=()):
        self.lexer = lexer
        self.newline_tokens_names = frozenset(newline_tokens_names)
        self.ignore_token_names = ignore_token_names
        self.newline_char = newline_char

        self.current_state = lexer.current_state
        self.begin = lexer.begin

    def input(self, s):
        self.lineno = 1
        self._lexer_pos_of_start_column = -1
        self._tok_count = 0
        return self.lexer.input(s)

    def token(self):
        # get a new token that shouldn't be %ignored
        while True:
            self._tok_count += 1

            t = self.lexer.token()
            if not t:
                return t    # End of stream

            try:
                if t.type not in self.ignore_token_names:
                    self._wrap_token(t)
                    return t
            finally:
                # handle line and column
                # must happen after assigning, because we change _lexer_pos_of_start_column
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

        if hasattr(t, 'lexer'):
            t.lexer.lineno = self.lineno    # not self.lexer, because it may be another wrapper

        t.lineno = self.lineno
        t.value = tok_value

    def _handle_newlines(self, t):
        newlines = t.value.count(self.newline_char)

        if newlines:
            self.lineno += newlines
            self._lexer_pos_of_start_column = t.lexpos + t.value.rindex(self.newline_char)


class GrammarOptions(object):
    """Specifies the options for PlyPlus

    Commonly-used Options:
        debug - Affects verbosity (default: False)
        just_lex - Don't build a parser. Useful for debugging (default: False)
        auto_filter_tokens - Automagically remove "punctuation" tokens (default: True)
        cache_grammar - Cache the PlyPlus grammar (PLY caches regardless of this. Default: False)
        ignore_postproc - Don't call the post-processing function (default: False)

    Read the GrammarOptions class for more details.
    """
    def __init__(self, options_dict):
        o = dict(options_dict)

        self.debug = bool(o.pop('debug', False))
        self.just_lex = bool(o.pop('just_lex', False))
        self.auto_filter_tokens = bool(o.pop('auto_filter_tokens', True))
        self.keep_empty_trees = bool(o.pop('keep_empty_trees', True))
        self.tree_class = o.pop('tree_class', STree)
        self.cache_grammar = o.pop('cache_grammar', False)
        self.ignore_postproc = bool(o.pop('ignore_postproc', False))
        self.engine = o.pop('engine', 'ply')

        if o:
            raise ValueError("Unknown options: %s" % o.keys())


class Grammar(object):
    """Grammar object. Provides the main interface to PlyPlus.
    """

    def __init__(self, grammar, **options):
        """
            grammar : a string or file-object containing the grammar spec
                      (using plyplus' bnf syntax)
            options : a dictionary controlling various aspects of plyplus.
                      """
        options = GrammarOptions(options)

        # Some, but not all file-like objects have a 'name' attribute
        try:
            source = grammar.name
        except AttributeError:
            source = '<string>'
            tab_filename = "parsetab_%s" % str(hash(grammar)%(2**32))
        else:
            # PLY turns "a.b" into "b", so gotta get rid of the dot.
            tab_filename = "parsetab_%s" % os.path.basename(source).replace('.', '_')

        # Drain file-like objects to get their contents
        try:
            read = grammar.read
        except AttributeError:
            pass
        else:
            grammar = read()

        assert isinstance(grammar, StringTypes)

        if options.cache_grammar:
            plyplus_cache_filename = PLYPLUS_DIR + '/%s-%s-%s.plyplus' % (tab_filename, hashlib.sha256(grammar).hexdigest(), __version__)
            if os.path.exists(plyplus_cache_filename):
                with open(plyplus_cache_filename, 'rb') as f:
                    self._grammar = pickle.load(f)
            else:
                self._grammar = self._create_grammar(grammar, source, tab_filename, options)

                with open(plyplus_cache_filename, 'wb') as f:
                    pickle.dump(self._grammar, f, pickle.HIGHEST_PROTOCOL)
        else:
            self._grammar = self._create_grammar(grammar, source, tab_filename, options)


    @staticmethod
    def _create_grammar(grammar, source, tab_filename, options):
        grammar_tree = grammar_parser.parse(grammar)
        if not grammar_tree:
            raise GrammarException("Parse Error: Could not create grammar")

        return _Grammar(grammar_tree, source, tab_filename, options)

    def lex(self, text):
        return self._grammar.lex(text)

    def parse(self, text):
        return self._grammar.parse(text)

    __init__.__doc__ += GrammarOptions.__doc__


class GrammarVerifier(SVisitor):
    def __init__(self):
        self.rules_used = None
        self.tokens_used = None
        self.rules_defined = None
        self.token_defined = None

    def rule(self, rule):
        if not rule.tail:
            return
        rule_name = rule.tail[0]
        if not isinstance(rule_name, StringTypes):
            return
        if rule_name.startswith("'"):
            pass    # literal
        elif re.match('^[a-z0-9_]+$', rule_name):
            self.rules_used.add(rule_name)
        elif re.match('^[A-Z0-9_]+$', rule_name):
            self.tokens_used.add(rule_name)
        else:
            raise RuntimeError("Unexpected rule/token name: %s", rule_name)

    oper = rule

    def ruledef(self, ruledef):
        self.rules_defined.add(ruledef.tail[0].lstrip('@#?'))
    def tokendef(self, tokendef):
        self.tokens_defined.add(tokendef.tail[0])

    def verify(self, tree):
        self.rules_used = set()
        self.tokens_used = set()
        self.rules_defined = set()
        self.tokens_defined = set()
        self.visit(tree)
        undefined_tokens = self.tokens_used - self.tokens_defined
        undefined_rules = self.rules_used - self.rules_defined
        if undefined_tokens:
            raise ParseError(["Undefined tokens: [%s]" % ', '.join(map(StringType, undefined_tokens))])
        if undefined_rules:
            raise ParseError(["Undefined rules: [%s]" % ', '.join(map(StringType, undefined_rules))])



class _Grammar(object):
    def __init__(self, grammar_tree, source_name, tab_filename, options):
        GrammarVerifier().verify(grammar_tree)

        self.options = options

        self.tab_filename = tab_filename
        self.source_name = source_name
        self.rules_to_flatten = set()
        self.rules_to_expand = set()
        self._newline_tokens = set()
        self._ignore_tokens = set()
        self.lexer_postproc = None
        self._newline_value = '\n'

        engine_class = {
            'ply': Engine_PLY,
            'pearley': Engine_Pearley,
        }[options.engine]

        self.engine = engine_class(self.options, self.rules_to_flatten, self.rules_to_expand)

        # -- Build Grammar --
        self.subgrammars = {}
        ExtractSubgrammars_Visitor(source_name, tab_filename, self.options).visit(grammar_tree)
        SimplifyGrammar_Visitor().visit(grammar_tree)
        ExpandOper_Visitor().visit(grammar_tree)
        tokendefs = simplify_tokendefs(grammar_tree)
        NameAnonymousTokens_Visitor(tokendefs).visit(grammar_tree)
        grammar_list_and_code = GrammarTreeToList_Transformer().transform(grammar_tree)

        # code may be omitted
        if len(grammar_list_and_code) == 1:
            grammar_list, = grammar_list_and_code
        else:
            grammar_list, code = grammar_list_and_code

            # prefix with newlines to get line-number count correctly (ensures tracebacks are correct)
            src_code = '\n' * (max(code.line, 1) - 1) + code

            # compiling before executing attaches source_name as filename: shown in tracebacks
            exec_code = compile(src_code, source_name, 'exec')
            exec(exec_code, locals())

        for type_, (name, defin) in grammar_list:
            assert type_ in ('token', 'token_with_mods', 'rule', 'option', 'fragment'), "Can't handle type %s"%type_
            handler = getattr(self, '_add_%s' % type_)
            handler(name, defin)

        # -- Build lexer --
        self.engine.build_lexer()
        lexer = LexerWrapper(self.engine.lexer, newline_tokens_names=self._newline_tokens, newline_char=self._newline_value, ignore_token_names=self._ignore_tokens)
        if self.lexer_postproc and not self.options.ignore_postproc:
            lexer = self.lexer_postproc(lexer)  # apply wrapper
        self.engine.lexer = lexer

        # -- Build Parser --
        if not self.options.just_lex:
            self.engine.build_parser(cache_file=tab_filename)

    def __repr__(self):
        return '<Grammar from %s, tab at %s>' % (self.source_name, self.tab_filename)

    def lex(self, text):
        "Performs tokenizing as a generator"
        self.engine.lexer.input(text)
        while True:
            tok = self.engine.lexer.token()
            if not tok:
                break
            yield tok

    def parse(self, text):
        "Parse the text into an AST"
        assert not self.options.just_lex

        tree = self.engine.parse(text)

        if self.subgrammars:
            ApplySubgrammars_Visitor(self.subgrammars).visit(tree)

        SimplifySyntaxTree_Visitor(self.rules_to_flatten, self.rules_to_expand, self.options.keep_empty_trees).visit(tree)

        return tree

    def _add_fragment(self, _1, _2):
        pass

    def _add_option(self, name, defin):
        "Set an option"
        if name == '%newline_char':
            self._newline_value = ast.literal_eval(defin)   # XXX Safe enough?
        else:
            raise GrammarException( "Unknown option: %s " % name )


    def _extract_unless_tokens(self, modtokenlist):
        unless_toks_dict = {}
        unless_toks_regexps = []
        for x, (modtok_name, modtok_value) in modtokenlist.tail:
            assert x == 'token'

            self._add_token(modtok_name, modtok_value)

            if not re.search(r'[^\w/-]', modtok_value):   # definitely not a regexp, let's optimize it
                unless_toks_dict[modtok_value] = modtok_name
            else:
                if not modtok_value.startswith('^'):
                    modtok_value = '^' + modtok_value
                if not modtok_value.endswith('$'):
                    modtok_value = modtok_value + '$'
                unless_toks_regexps += [(re.compile(modtok_value), modtok_name)]

        unless_toks_regexps.sort(key=lambda x:len(x[0].pattern), reverse=True)

        return unless_toks_dict, unless_toks_regexps

    def _unescape_unicode_in_token(self, token_value):
        # XXX HACK XXX
        # We want to convert unicode escapes into unicode characters,
        # because the regexp engine only supports the latter.
        # But decoding with unicode-escape converts whitespace as well,
        # which is bad because our regexps are whitespace agnostic.
        # It also unescapes double backslashes, which messes up with the
        # regexp.

        token_value = token_value.replace('\\'*2, '\\'*4)
        # The equivalent whitespace escaping is:
        # token_value = token_value.replace(r'\n', r'\\n')
        # token_value = token_value.replace(r'\r', r'\\r')
        # token_value = token_value.replace(r'\f', r'\\f')
        # but for speed reasons, I ended-up with this ridiculus regexp:
        token_value = re.sub(r'(\\[nrf])', r'\\\1', token_value)

        return codecs.getdecoder('unicode_escape')(token_value)[0]

    def _add_token_with_mods(self, name, defin):
        token_value, token_features = defin
        token_value = self._unescape_unicode_in_token(token_value)

        token_added = False
        if token_features is None:
            pass    # skip to simply adding it
        elif token_features.head == 'subgrammarobj':
            assert len(token_features.tail) == 1
            self.subgrammars[name] = token_features.tail[0]
        elif token_features.head == 'tokenmods':
            for token_mod in token_features.tail:
                mod, modtokenlist = token_mod.tail

                if mod == '%unless':
                    assert not token_added, "token already added, can't issue %unless"

                    unless_toks_dict, unless_toks_regexps = self._extract_unless_tokens(modtokenlist)

                    self.engine.add_token_unless(name, token_value, unless_toks_dict, unless_toks_regexps)

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
            self.engine.add_token(name, token_value)

    def _add_token(self, name, token_value):
        assert isinstance(token_value, StringTypes), token_value
        self._add_token_with_mods(name, (token_value, None))

    def _add_rule(self, rule_name, rule_def):
        mods, = re.match('([@#?]*).*', rule_name).groups()
        if mods:
            rule_name = rule_name[len(mods):]

        if RuleMods.EXPAND in mods:
            self.rules_to_expand.add( rule_name )
        elif RuleMods.FLATTEN in mods:
            self.rules_to_flatten.add( rule_name )

        self_expand = (RuleMods.EXPAND in mods or RuleMods.EXPAND1 in mods)
        self.engine.add_rule(rule_name, rule_def, self_expand)




