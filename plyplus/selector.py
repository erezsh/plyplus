import re, os
from itertools import chain

from strees import STree, is_stree
from plyplus import Grammar
import grammars

def sum_list(l):
    return chain(*l)  # Fastest way according to my tests

class _Match(object):
    def __init__(self, matched, selector):
        self.match_track = [(matched, selector)]

    def __hash__(self):
        return hash(tuple(self.match_track))
    def __eq__(self, other):
        return self.match_track == other.match_track

    @property
    def last_elem_matched(self):
        return self.match_track[0][0]

    def extend(self, other):
        self.match_track += other.match_track

    def get_result(self):
        yields = [m for m,s in self.match_track if s.head=='elem' and len(s.tail)>1 and s.tail[0].head=='yield']
        #assert len(yields) <=1, yields
        if len(yields) <= 1:
            return yields[0] if yields else self.match_track[-1][0]
        else:
            return tuple(yields)


class STreeSelector(STree):
    def match__elem_head(self, other):
        if not hasattr(other, 'head'):
            return []
        [expected_head] = self.tail
        return [other] if other.head == expected_head else []

    def match__elem_class(self, other):
        raise NotImplementedError('Classes not implemented yet')

    def match__elem_any(self, other):
        return [other]

    def match__elem_regexp(self, other):
        if is_stree(other):
            s = other.head
        else:
            s = other   # hopefully string
        [regexp] = self.tail
        assert regexp[0] == regexp[-1] == '/'
        regexp = regexp[1:-1]
        return [other] if re.match(regexp, s) else []

    def match__modifier(self, other):
        assert self.tail[0].head == 'modifier_name' and len(self.tail[0].tail) == 1
        modifier_name = self.tail[0].tail[0]

        if modifier_name == ':is-parent':
            return [other] if (is_stree(other) and other.tail) else []
        elif modifier_name == ':is-leaf':
            return [other] if not is_stree(other) else []

        raise NotImplementedError("Didn't implement %s yet" % modifier_name)

    def match__selector_list(self, other):
        res = sum_list(kid._match([other]) for kid in self.tail)
        return [r.get_result() for r in res]    # lose match objects, localize yields

    def match__elem(self, other):
        if self.tail[0].head == 'yield':
            matches = self.tail[1]._match(other)
        else:
            matches = self.tail[0]._match(other)
        if len(self.tail)>1 and self.tail[1].head=='modifier':
            matches = filter(self.tail[1].match__modifier, matches)
        return [_Match(m, self) for m in matches]

    def _travel_tree_by_op(self, tree, op):
        if not hasattr(tree, 'parent') or tree.parent is None:
            return  # XXX should I give out a warning?
        try:
            if op == '>':   # travel to parent
                yield tree.parent()
            elif op == '+': # travel to previous adjacent sibling
                new_index = tree.index_in_parent - 1
                if new_index < 0:
                    raise IndexError('We dont want it to overflow back to the last element')
                yield tree.parent().tail[new_index]
            elif op == '~': # travel to all previous siblings
                for x in tree.parent().tail[ :tree.index_in_parent ]:
                    yield x
            elif op == ' ': # travel back to root
                to_check = []
                parent = tree.parent()  # TODO: what happens if the parent is garbage-collected?
                while parent is not None:
                    yield parent
                    parent = parent.parent() if parent.parent else None

        except (IndexError, ) as e:
            pass


    def _match_selector_op(self, matches_so_far):
        selector = self.tail[0]
        op = self.tail[1].tail[0] if len(self.tail) > 1 else ' '


        matches_found = []
        for match in matches_so_far:
            to_check = list(self._travel_tree_by_op(match.last_elem_matched, op))

            if to_check:
                for match_found in selector.match__selector(to_check):
                    match_found.extend( match )
                    matches_found.append( match_found )

        return matches_found

    def match__selector(self, other):
        elem = self.tail[-1]
        if is_stree(other):
            res = sum_list(other.map(elem._match))
        else:
            res = sum_list([elem._match(item) for item in other]) # we were called by a selector_op
        if not res:
            return []   # shortcut

        if self.tail[0].head == 'selector_op':
            res = self.tail[0]._match_selector_op(res)

        return res

    def match__start(self, other):
        assert len(self.tail) == 1
        return self.tail[0]._match(other)

    def _match(self, other):
        return getattr(self, 'match__' + self.head)(other)

    def match(self, other):
        other.calc_parents()    # TODO add caching?
        return [x.get_result() for x in self._match(other)]


selector_dict = {}

selector_grammar = Grammar(grammars.open('selector.g'))
def selector(s):
    if s not in selector_dict:
        selector_dict[s] = selector_grammar.parse(s)
    return selector_dict[s]

def install():
    def select(self, s):
        return selector(s).match(self)
    def select1(self, s):
        [r] = self.select(s)
        return r

    STree.select = select
    STree.select1 = select1
