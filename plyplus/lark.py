from collections import defaultdict, deque

class fzset(frozenset):
    def __repr__(self):
        return '{%s}' % ', '.join(map(repr, self))


def classify_bool(seq, pred):
    true_elems = []
    false_elems = []

    for elem in seq:
        if pred(elem):
            true_elems.append(elem)
        else:
            false_elems.append(elem)

    return true_elems, false_elems

def classify(seq, key=None):
    d = {}
    for item in seq:
        k = key(item) if (key is not None) else item
        if k in d:
            d[k].append(item)
        else:
            d[k] = [item]
    return d

def bfs(initial, expand):
    open_q = deque(list(initial))
    visited = set(open_q)
    while open_q:
        node = open_q.popleft()
        yield node
        for next_node in expand(node):
            if next_node not in visited:
                visited.add(next_node)
                open_q.append(next_node)



def is_terminal(sym):
    return sym.isupper() or sym == '$'

class _Rule(object):
    """
        origin : a symbol
        expansion : a list of symbols
    """
    def __init__(self, origin, expansion):
        assert expansion, "No support for empty rules"
        self.origin = origin
        self.expansion = expansion

    def __repr__(self):
        return '<%s : %s>' % (self.origin, ' '.join(self.expansion))

class RulePtr(object):
    def __init__(self, rule, index):
        assert isinstance(rule, _Rule)
        assert index <= len(rule.expansion)
        self.rule = rule
        self.index = index

    def __repr__(self):
        before = self.rule.expansion[:self.index]
        after = self.rule.expansion[self.index:]
        return '<%s : %s * %s>' % (self.rule.origin, ' '.join(before), ' '.join(after))

    @property
    def next(self):
        return self.rule.expansion[self.index]

    def advance(self, sym):
        assert self.next == sym
        return RulePtr(self.rule, self.index+1)

    @property
    def is_satisfied(self):
        return self.index == len(self.rule.expansion)

    def __eq__(self, other):
        return self.rule == other.rule and self.index == other.index
    def __hash__(self):
        return hash((self.rule, self.index))


def pairs(lst):
    return zip(lst[:-1], lst[1:])

def update_set(set1, set2):
    copy = set(set1)
    set1 |= set2
    return set1 != copy

class GrammarAnalyzer(object):
    def __init__(self, grammar):
        self.grammar = grammar

        self.rules = set()
        self.rules_by_origin = {k[0]: [] for k in grammar}
        for origin, exp in grammar:
            r =  _Rule( origin, exp )
            self.rules.add(r)
            self.rules_by_origin[origin].append(r)

        print
        self.init_state = self.expand_rule('start')

    def expand_rule(self, rule):
        "Returns all init_ptrs accessible by rule (recursive)"
        init_ptrs = set()
        def _expand_rule(rule):
            assert not is_terminal(rule)

            for r in self.rules_by_origin[rule]:
                init_ptr = RulePtr(r, 0)
                init_ptrs.add(init_ptr)

                new_r = init_ptr.next
                if not is_terminal(new_r):
                    yield new_r

        _ = list(bfs([rule], _expand_rule))

        return fzset(init_ptrs)

    def _first(self, r):
        if is_terminal(r):
            return {r}
        else:
            return {rp.next for rp in self.expand_rule(r) if is_terminal(rp.next)}

    def _calc_FOLLOW(self):
        # For every T following x: follow(x) += T
        # For every y following x: follow(x) += first(y) if non-empty(y) else follow(y)
        # For every x at end of y: follow(x) += follow(y)

        FOLLOW = {rule.origin: set() for rule in self.rules}

        for rule in self.rules:
            for sym1, sym2 in pairs(rule.expansion):
                if not is_terminal(sym1) and is_terminal(sym2):
                    FOLLOW[sym1].add( sym2 )

        changed = True
        while changed:
            changed = False
            for rule in self.rules:
                for sym1, sym2 in pairs(rule.expansion):
                    if not is_terminal(sym1) and not is_terminal(sym2):
                        if update_set( FOLLOW[sym1], self._first(sym2) ):
                            changed = True

                last = rule.expansion[-1]
                if not is_terminal(last):
                    if update_set( FOLLOW[last], FOLLOW[rule.origin] ):
                        changed = True


        self.FOLLOW = FOLLOW


    def analyze(self):
        self._calc_FOLLOW()

        self.states = {}
        def step(state):
            lookahead = defaultdict(list)
            sat, unsat = classify_bool(state, lambda rp: rp.is_satisfied)
            for rp in sat:
                for term in self.FOLLOW.get(rp.rule.origin, ()):
                    lookahead[term].append(('reduce', rp.rule))

            d = classify(unsat, lambda rp: rp.next)
            for sym, rps in d.items():
                rps = {rp.advance(sym) for rp in rps}

                for rp in set(rps):
                    if not rp.is_satisfied and not is_terminal(rp.next):
                        rps |= self.expand_rule(rp.next)

                lookahead[sym].append(('shift', fzset(rps)))
                yield fzset(rps)

            for k, v in lookahead.items():
                if len(v) > 1:
                    for x in v:
                        if x[0] == 'shift':
                            lookahead[k] = [x]

            for k, v in lookahead.items():
                assert len(v) == 1, ("Collision", k, v)

            self.states[state] = {k:v[0] for k, v in lookahead.items()}

        x = list(bfs([self.init_state], step))

        # --
        self.enum = list(self.states)
        self.enum_rev = {s:i for i,s in enumerate(self.enum)}
        self.states_idx = {}

        for s, la in self.states.items():
            la = {k:(v[0], self.enum_rev[v[1]]) if v[0]=='shift' else v for k,v in la.items()}
            self.states_idx[ self.enum_rev[s] ] = la


        self.init_state_idx = self.enum_rev[self.init_state]

class ParseError(Exception):
    pass

class Parser(object):
    def __init__(self, ga, callback):
        self.ga = ga
        self.callback = callback

    def parse(self, seq):
        stack = [(None, self.ga.init_state_idx)]
        i = 0

        def reduce(rule):
            s = stack[-len(rule.expansion):]
            del stack[-len(rule.expansion):]
            res = getattr(self.callback, rule.origin)([x[0] for x in s])

            if rule.origin == 'start':
                return res

            state = stack[-1][1]
            _action, new_state = self.ga.states_idx[state][rule.origin]
            assert _action == 'shift'
            stack.append((res, new_state))

        while i < len(seq):
            state = stack[-1][1]
            next_sym = seq[i]

            action, arg = self.ga.states_idx[state][next_sym.type]
            if action == 'shift':
                i += 1
                stack.append((next_sym, arg))
            elif action == 'reduce':
                reduce(arg)
            else:
                assert False


        while len(stack) > 1:
            state = self.ga.enum[stack[-1][1]]
            satisfied = [rp for rp in state if rp.is_satisfied]
            if len(satisfied) != 1:
                raise ParseError('Error reducing', satisfied)
            reduce_rp ,= satisfied

            res = reduce(reduce_rp.rule)
            if res:
                break

        assert stack == [(None, self.ga.init_state_idx)], len(stack)
        return res

