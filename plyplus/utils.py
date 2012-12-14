try:
    # Python 2.6
    from types import StringTypes
except ImportError:
    # Python 3.0
    StringTypes = (str,)


StringType = type(u'')
