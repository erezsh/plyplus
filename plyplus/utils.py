import functools

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

class DefaultDictX(dict):
    def __init__(self, default_factory):
        self.__default_factory = default_factory
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            self[key] = value = self.__default_factory(key)
            return value
