from .common import ParseError, ErrorMsg, TokValue
from .strees import is_stree

from . import lark


class Callback:
    pass

class Engine_Lark(object):

    def __init__(self, options, rules_to_flatten, rules_to_expand):
        self.rules_to_flatten = rules_to_flatten
        self.rules_to_expand = rules_to_expand
        self.options = options

        self.lexer = None
        self.parser = None
        self.errors = None

        self.rules = []
        self.callback = Callback()

        self.tokens = []
        self.token_callbacks = {}


    def add_rule(self, rule_name, rule_def, self_expand):
        tree_class = self.options.tree_class
        auto_filter_tokens = self.options.auto_filter_tokens
        def _handle_rule(match):
            if rule_name == 'start' and is_stree(match):
                    return match

            subtree = []
            for child in match:
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
                return subtree[0]
            else:
                return tree_class(rule_name, subtree, skip_adjustments=True)

        setattr(self.callback, rule_name, _handle_rule)

        for option in rule_def:
            rule = (rule_name, option)
            self.rules.append(rule)

    def add_token(self, name, value):
        self.tokens.append((name, value))

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

        self.tokens.append((name, value))
        self.token_callbacks[name] = t_token

    def build_lexer(self):
        self.lexer = lark.Lexer(self.tokens, self.token_callbacks)

    def build_parser(self, cache_file):
        g = lark.GrammarAnalyzer(self.rules)
        g.analyze()
        self.parser = lark.Parser(g, self.callback)

    def parse(self, text):
        self.lexer.input(text)
        tokens = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            if isinstance(tok.value, TokValue):
                tokens.append(tok.value)
            else:
                tokens.append(TokValue(tok.value, tok.type))

        try:
            return self.parser.parse(tokens)
        except lark.ParseError as e:
            raise ParseError(e)

