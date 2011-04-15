from itertools import islice

# DFS
class Visitor(object):
    def visit(self, tree):
        self._visit(tree)
        return tree

    def _visit(self, tree):
        for branch in islice(tree,1,None):
            if isinstance(branch, list):
                self._visit(branch)

        f = getattr(self, tree[0], self.default)
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
                in islice(tree,1,None)
            ]

        tree = [tree[0]] + branches

        f = getattr(self, tree[0], self.default)
        return f(tree)

