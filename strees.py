from weakref import ref

class STree(object):
    #__slots__ = 'head', 'tail'

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
    def __hash__(self):
        return hash((self.head, tuple(self.tail)))
    def __eq__(self, other):
        try:
            return self.head == other.head and self.tail == other.tail
        except AttributeError:
            return False

    def __repr__(self):
        return '%s(%s)' % (self.head, ', '.join(map(repr,self.tail)))

    def find_predicate(self, predicate):
        l = []
        if predicate(self):
            l.append(self)
        for kid in self.tail:
            l += kid.find_predicate(predicate)
        return l
    def map(self, func, context=None):
        if context is None:
            context = [ func(self) ]
        for kid in self.tail:
            try:
                kid.map(func, context)
            except AttributeError:
                pass
            context.append( func(kid) )
        return context

    def _to_pydot(self, graph):
        import pydot
        color = hash(self.head) & 0xffffff
        if not (color & 0x808080):
            color |= 0x808080

        def new_leaf(leaf):
            node = pydot.Node(id(leaf), label=repr(leaf))
            graph.add_node(node)
            return node

        subnodes = [kid._to_pydot(graph) if is_stree(kid) else new_leaf(kid) for kid in self.tail]
        node = pydot.Node(id(self), style="filled", fillcolor="#%x"%color, label=self.head)
        graph.add_node(node)

        for subnode in subnodes:
            graph.add_edge(pydot.Edge(node, subnode))

        return node

    def to_png_with_pydot(self, filename):
        import pydot
        graph = pydot.Dot(graph_type='digraph', rankdir="LR")
        self._to_pydot(graph)
        graph.write_png(filename)

    def calc_parents(self):
        self.parent = None
        self.index_in_parent = None
        for i, kid in enumerate(self.tail):
            try:
                kid.calc_parents()
            except AttributeError:
                pass
            kid.parent = ref(self)
            kid.index_in_parent = i
                    
    def select(self, s):
        from selector import selector   # import loop, don't use internally
        return selector(s).match(self)

def is_stree(obj):
    return type(obj) is STree or isinstance(obj, STree)

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

        tree = tree.__class__(tree.head, branches)

        f = getattr(self, tree.head, self.__default__)
        return f(tree)

    def __default__(self, tree):
        return tree  
