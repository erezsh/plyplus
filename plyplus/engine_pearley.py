from .common import ParseError, ErrorMsg, TokValue
from .strees import is_stree

from .engine_ply import Engine_PLY

from . import pearley


class Engine_Pearley(object):
    """Pearley engine based on nearley.js implementation.

    * Supports a much larger class of grammars
    * Uses PLY's lexer for performance
    * It is still much slower than PLY for the common case
    * In some cases it's faster than PLY
    * Ambiguous grammars may result in very long run-time

    This is an experimental engine!
    """

    def __init__(self, options, rules_to_flatten, rules_to_expand):
        self.engine_ply = Engine_PLY(options, rules_to_flatten, rules_to_expand)

        self.rules_to_flatten = rules_to_flatten
        self.rules_to_expand = rules_to_expand
        self.options = options

        self.lexer = None
        self.parser = None
        self.errors = None

        self.rules = []


    def add_rule(self, rule_name, rule_def, self_expand):
        tree_class = self.options.tree_class
        auto_filter_tokens = self.options.auto_filter_tokens
        def _handle_rule(match, index):
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


        for option in rule_def:
            symbols = [{'literal': x} if x.isupper() else x for x in option]
            rule = {"name": rule_name, "symbols": symbols, "postprocess": _handle_rule}
            self.rules.append(rule)

    def add_token(self, name, value):
        self.engine_ply.add_token(name, value)

    def add_token_unless(self, name, value, unless_toks_dict, unless_toks_regexps):
        self.engine_ply.add_token_unless(name, value, unless_toks_dict, unless_toks_regexps)

    def build_lexer(self):
        self.engine_ply.build_lexer()
        self.lexer = self.engine_ply.lexer

    def build_parser(self, cache_file):
        self.parser = pearley.Parser(self.rules, 'start')

    def parse(self, text):
        self.build_parser('bla')
        self.errors = []
        self.lexer.input(text)
        tokens = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            # tokens.append({'type': tok.type, 'value': tok.value})
            if isinstance(tok.value, TokValue):
                tokens.append(tok.value)
            else:
                tokens.append(TokValue(tok.value, tok.type))

        self.parser.feed(tokens)
        if not self.parser.results:
            self.errors.append(ErrorMsg(msg="Could not create parse tree!"))
        if self.errors:
            raise ParseError(self.errors)

        if len(self.parser.results) > 1:
            raise ParseError([ErrorMsg(msg="Ambiguous parsing results (%d)" % (len(self.parser.results)))])
        tree ,= self.parser.results
        return tree


