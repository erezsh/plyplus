import re
import types
import logging

from ply import lex, yacc

from .common import *
from .strees import is_stree
from . import PLYPLUS_DIR

grammar_logger = logging.getLogger('Grammar')
grammar_logger.setLevel(logging.ERROR)

class Engine_PLY_Callback(object):
    start = "start"

    def __init__(self):
        self.tokens = []

    @staticmethod
    def t_error(t):
        raise TokenizeError("Illegal character in input: '%s', line: %s, %s" % (t.value[:32], t.lineno, t.type))

    p_error = NotImplemented

class Engine_PLY(object):
    def __init__(self, options, rules_to_flatten, rules_to_expand):
        self.rules_to_flatten = rules_to_flatten
        self.rules_to_expand = rules_to_expand
        self.options = options

        self.callback = Engine_PLY_Callback()
        self.callback.p_error = self.p_error

        self.lexer = None
        self.parser = None
        self.errors = None

    def add_rule(self, rule_name, rule_def, self_expand):
        rule_def = '%s\t: %s'%(rule_name, '\n\t| '.join(map(' '.join, rule_def)))
        tree_class = self.options.tree_class
        auto_filter_tokens = self.options.auto_filter_tokens

        def p_rule(_, p):
            subtree = []
            for child in p.__getslice__(1, None):
                if isinstance(child, tree_class) and (
                           (                            child.head in self.rules_to_expand )
                        or (child.head == rule_name and child.head in self.rules_to_flatten)
                        ):
                    # (EXPAND | FLATTEN) & mods -> here to keep tree-depth minimal, prevents unbounded tree-depth on
                    #                              recursive rules.
                    #           EXPAND1  & mods -> perform necessary expansions on children first to ensure we don't end
                    #                              up expanding inside our parents if (after expansion) we have more
                    #                              than one child.
                    subtree.extend(child.tail)
                else:
                    subtree.append(child)

            # Apply auto-filtering (remove 'punctuation' tokens)
            if auto_filter_tokens and len(subtree) != 1:
                subtree = list(filter(is_stree, subtree))

            if len(subtree) == 1 and self_expand:
                # Self-expansion: only perform on EXPAND and EXPAND1 rules
                p[0] = subtree[0]
            else:
                p[0] = tree_class(rule_name, subtree, skip_adjustments=True)
        p_rule.__doc__ = rule_def
        setattr(self.callback, 'p_%s' % (rule_name,), types.MethodType(p_rule, self))

    def add_token(self, name, value):
        self.callback.tokens.append(name)
        setattr(self.callback, 't_%s'%name, value)


    def add_token_unless(self, name, value, unless_toks_dict, unless_toks_regexps):
        def t_token(t):
            if t.value in unless_toks_dict:
                t.type = unless_toks_dict[t.value]
            else:
                t.type = name
                for regexp, tokname in unless_toks_regexps:
                    if regexp.match(t.value):
                        t.type = tokname
                        break
            return t
        t_token.__doc__ = value

        self.add_token(name, t_token)


    def build_lexer(self):
        self.lexer = lex.lex(module=self.callback, reflags=re.UNICODE)

    def build_parser(self, cache_file):
        self.parser = yacc.yacc(module=self.callback, debug=self.options.debug, tabmodule=cache_file, errorlog=grammar_logger, outputdir=PLYPLUS_DIR)

    def parse(self, text):
        self.errors = []
        tree = self.parser.parse(text, lexer=self.lexer, debug=self.options.debug)
        if not tree:
            self.errors.append(ErrorMsg(msg="Could not create parse tree!"))
        if self.errors:
            raise ParseError(self.errors)

        return tree


    def p_error(self, p):
        # TODO: Move to callback?
        if p:
            if isinstance(p.value, TokValue):
                err = SyntaxErrorMsg_LineCol(value=p.value, type=p.type, line=p.value.line, col=p.value.column)
            else:
                err = SyntaxErrorMsg_Line(value=p.value, type=p.type, line=p.lineno)
        else:
            err = SyntaxErrorMsg_Unknown()

        if self.options.debug:
            print(err)

        self.errors.append(err)

