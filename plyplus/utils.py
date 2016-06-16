import functools
import itertools

try:
    # Python 2.6
    from types import StringTypes
except ImportError:
    # Python 3.0
    StringTypes = (str,)


StringType = type(u'')

def classify(seq, key=lambda x:x):
    d = {}
    for item in seq:
        k = key(item)
        if k not in d:
            d[k] = [ ]
        d[k].append( item )

    return d

def _cache_0args(obj):
    @functools.wraps(obj)
    def memoizer(self):
        _cache = self._cache
        _id = id(obj)
        if _id not in _cache:
            self._cache[_id] = obj(self)
        return _cache[_id]
    return memoizer


def sum_list(l):
    return list(itertools.chain(*l))

def list_join(lst, sep):
    return sum_list([sep,j] for j in lst)[1:]
