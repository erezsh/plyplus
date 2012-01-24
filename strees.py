
class STree(object):
    __slots__ = 'head', 'tail'

    def __init__(self, head, tail):
        self.head = head
        self.tail = tail


    def expand_kids(self, *indices):
        for i in sorted(indices, reverse=True): # reverse so that changing tail won't affect indices
            kid = self.tail[i]
            self.tail[i:i+1] = kid.tail
    def remove_kids(self, *indices):
        for i in sorted(indices, reverse=True): # reverse so that changing tail won't affect indices
            del self.tail[i]

    def __len__(self):
        raise Exception('len')
    def __nonzero__(self):
        return True    # XXX ???
    def __eq__(self, other):
        return self.head == other.head and self.tail == other.tail

    def __repr__(self):
        return '%s(%s)' % (self.head, ', '.join(map(repr,self.tail)))
                    

def is_stree(obj):
    return isinstance(obj, STree)

class SVisitor(object):
    def visit(self, tree):
        self._visit(tree)
        return tree

    def _visit(self, tree):
        pre_f = getattr(self, 'pre_' + tree.head, None)
        if pre_f:
            pre_f(tree)

        for branch in tree.tail:
            if is_stree(branch):
                self._visit(branch)

        f = getattr(self, tree.head, self.__default__)
        return f(tree)

    def __default__(self, tree):
        return False

class STransformer(object):
    def transform(self, tree):
        return self._transform(tree)

    def _transform(self, tree):
        branches = [
                self._transform(branch) if is_stree(branch) else branch
                for branch in tree.tail
            ]

        tree = STree(tree.head, branches)

        f = getattr(self, tree.head, self.__default__)
        return f(tree)

    def __default__(self, tree):
        return tree  
