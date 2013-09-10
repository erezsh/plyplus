
class STreeCollection(object):
    def __init__(self, strees):
        self.strees = list(strees)

    def __len__(self):
        return len(self.strees)

    def __getitem__(self, index):
        return self.strees[index]

    def __eq__(self, other):
        return self.strees == other

    def __repr__(self):
        return '%s%s' % (type(self).__name__, repr(self.strees))

    def leaf(self, leaf_head):
        for stree in self.strees:
            try:
                yield stree.leaf(leaf_head)
            except KeyError:
                pass
