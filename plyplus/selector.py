from __future__ import absolute_import

import re, copy
from itertools import chain
import weakref

from .strees import STree, is_stree
from .stree_collection import STreeCollection
from .plyplus import Grammar
from . import grammars

def sum_list(l):
    return chain(*l)  # Fastest way according to my tests

class _Match(object):
    __slots__ = 'match_track'

    def __init__(self, matched, selector_instance):
        self.match_track = [(matched, selector_instance)]

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
        yields = [m for m, s in self.match_track
                  if s.head=='elem'
                  and len(s.tail)>1
                  and s.tail[0].head=='yield']

        if not yields:
            # No yields; pick last element
            return self.match_track[-1][0]
        elif len(yields) == 1:
            return yields[0]
        else:
            # Multiple yields
            return tuple(yields)


class STreeSelector(STree):
    def _post_init(self):

        if self.head == 'modifier':
            assert self.tail[0].head == 'modifier_name' and len(self.tail[0].tail) == 1
            modifier_name = self.tail[0].tail[0]

            try:
                f = getattr(self, 'match__modifier__' + modifier_name.replace('-', '_').replace(':',''))
            except AttributeError:
                raise NotImplementedError("Didn't implement %s yet" % modifier_name)
            else:
                setattr(self, 'match__modifier', f)

        elif self.head == 'elem':
            if self.tail[-1].head == 'modifier':
                self.match__elem = self.match__elem_with_modifier
            else:
                self.match__elem = self.match__elem_without_modifier

        try:
            self._match = getattr(self, 'match__' + self.head)
        except AttributeError:
            self._match = None # We shouldn't be matched

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
            s = unicode(other)   # hopefully string
        regexp = self.tail[1]
        assert regexp[0] == regexp[-1] == '/'
        regexp = regexp[1:-1]
        return [other] if re.match(regexp, s) else []

    def match__elem_tree_param(self, other):
        assert self.head == 'elem_tree', 'Missing keyword: %s' % self
        return [other] if self.tail[1] == other else []

    def match__modifier__is_parent(self, other):
        return [other] if (is_stree(other) and other.tail) else []
    def match__modifier__is_leaf(self, other):
        return [other] if not is_stree(other) else []
    def match__modifier__is_root(self, other):
        return [other] if is_stree(other) and other is self.match_root() else []
    def match__modifier__is_first_child(self, other):
        return [other] if other.index_in_parent == 0 else []

    def match__elem_with_modifier(self, other):
        matches = self.tail[-1].match__modifier(other)   # skip possible yield
        matches = filter(self.tail[-2]._match, matches)
        return [_Match(m, self) for m in matches]

    def match__elem_without_modifier(self, other):
        matches = self.tail[-1]._match(other)   # skip possible yield
        return [_Match(m, self) for m in matches]


    def match__selector_list(self, other):
        assert self.head == 'result_list', 'call to _init_selector_list failed!'
        set_, = self.tail
        return [other] if other in set_ else []

    def _init_selector_list(self, other):
        if self.head == 'result_list':
            res = sum_list(kid._match(other) for kid in self.selector_list.tail)
            res = [r.get_result() for r in res]    # lose match objects, localize yields
            self.tail = [frozenset(res)] + self.tail[1:]
        else:
            res = sum_list(kid._match(other) for kid in self.tail)
            res = [r.get_result() for r in res]    # lose match objects, localize yields
            self.selector_list = copy.copy(self)
            self.reset('result_list', [frozenset(res)])

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
                parent = tree.parent()  # TODO: what happens if the parent is garbage-collected?
                while parent is not None:
                    yield parent
                    if parent is self.match_root():
                        break
                    parent = parent.parent() if parent.parent else None

        except IndexError:
            pass


    def _match_selector_op(self, matches_so_far):
        _selector = self.tail[0]
        op = self.tail[1].tail[0] if len(self.tail) > 1 else ' '


        matches_found = []
        for match in matches_so_far:
            to_check = list(self._travel_tree_by_op(match.last_elem_matched, op))

            if to_check:
                for match_found in _selector.match__selector(to_check):
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

    # def _match(self, other):
    #     return getattr(self, 'match__' + self.head)(other)

    def match(self, other, **kwargs):
        other.calc_parents()    # TODO add caching?
        self.map(lambda x: is_stree(x) and setattr(x, 'match_root', weakref.ref(other)))

        # Selectors are re-usable right now, so we have to handle both first
        # use, and re-use. This will be bad if ever used threaded. The right
        # thing to do (if we want to keep caching them) is to deepcopy on each
        # use. It should also make the code simpler.
        for elem_tree_param in self.filter(lambda x: is_stree(x)
                                          and x.head in ('elem_tree_param', 'elem_tree')):
            elem_tree_param.reset('elem_tree', [elem_tree_param.tail[0], kwargs[elem_tree_param.tail[0]]])

        str_args = dict((k,re.escape(v)) for k,v in kwargs.items() if isinstance(v, (str, unicode)))
        for elem_regexp in self.filter(lambda x: is_stree(x) and x.head == 'elem_regexp'):
            elem_regexp.tail = [elem_regexp.tail[0], elem_regexp.tail[0].format(**str_args)]

        # Evaluate all selector_lists into result_lists
        selector_lists = self.filter(lambda x: is_stree(x)
                                     and x.head in ('selector_list', 'result_list'))
        for selector_list in reversed(selector_lists):  # reverse turns pre-order -> post-order
            selector_list._init_selector_list(other)

        # Match and return results
        return STreeCollection([x.get_result() for x in self._match(other)])


selector_dict = {}

selector_grammar = Grammar(grammars.open('selector.g'), tree_class=STreeSelector)
def selector(text):
    if text not in selector_dict:
        selector_ast = selector_grammar.parse(text)
        selector_ast.map(lambda x: is_stree(x) and x._post_init())
        selector_dict[text] = selector_ast
    return selector_dict[text]

def install():
    def select(self, text, **kw):
        return selector(text).match(self, **kw)
    def select1(self, text, **kw):
        [r] = self.select(text, **kw)
        return r

    def collection_select(self, *args, **kw):
        return STreeCollection(sum_list(stree.select(*args, **kw) for stree in self))

    STree.select = select
    STree.select1 = select1

    STreeCollection.select = collection_select
    STreeCollection.select1 = select1

