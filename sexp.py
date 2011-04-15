from itertools import islice

def head(tree):
    return tree[0]
def tail(tree):
    return islice(tree,1,None)

# DFS
class Visitor(object):
    def visit(self, tree):
        self._visit(tree)
        return tree

    def _visit(self, tree):
        for branch in tail(tree):
            if isinstance(branch, list):
                self._visit(branch)

        f = getattr(self, head(tree), self.default)
        return f(tree)

class Transformer(object):
    def transform(self, tree):
        return self._transform(tree)

    def _transform(self, tree):
        branches = [
                self._transform(branch)
                if isinstance(branch, list)
                else branch
                for branch
                in tail(tree)
            ]

        tree = [tree[0]] + branches

        f = getattr(self, head(tree), self.default)
        return f(tree)

