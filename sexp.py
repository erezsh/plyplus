from itertools import islice

def head(tree):
    return tree[0]
def tail(tree):
    return islice(tree,1,None)
def is_sexp(tree):
    return isinstance(tree, list) and len(tree)

# DFS
class Visitor(object):
    def visit(self, tree):
        self._visit(tree)
        return tree

    def _visit(self, tree):
        for branch in tail(tree):
            if is_sexp(branch):
                self._visit(branch)

        f = getattr(self, head(tree), self.default)
        return f(tree)

    def default(self, tree):
        return False

class Transformer(object):
    def transform(self, tree):
        return self._transform(tree)

    def _transform(self, tree):
        branches = [
                self._transform(branch) if is_sexp(branch) else branch
                for branch in tail(tree)
            ]

        tree = [head(tree)] + branches

        f = getattr(self, head(tree), self.default)
        return f(tree)

    def default(self, tree):
        return tree


class _Finder(Visitor):
    def __init__(self, rules, target_list):
        self.rules = set(rules)
        self.l = target_list

    def default(self, tree):
        if head(tree) in self.rules:
            self.l.append(tree)

def find(tree, *rules):
    result = []
    _Finder(rules, result).visit(tree)
    return result
    
