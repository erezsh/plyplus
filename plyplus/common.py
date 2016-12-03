from weakref import ref

from .utils import StringType

class ErrorMsg(object):

    MESSAGE = u"{msg}"

    def __init__(self, **kw):
        self.args = kw

    def __str__(self):
        return self.MESSAGE.format(**self.args)

class SyntaxErrorMsg_Unknown(ErrorMsg):
    MESSAGE = u"Syntax error in input (details unknown)"

class SyntaxErrorMsg_Line(ErrorMsg):
    MESSAGE = u"Syntax error in input at '{value}' (type {type}) line {line}"

class SyntaxErrorMsg_LineCol(ErrorMsg):
    MESSAGE = u"Syntax error in input at '{value}' (type {type}) line {line} col {col}"

class PlyplusException(Exception):
    pass

class GrammarException(PlyplusException):
    pass

class ParseError(PlyplusException):
    def __init__(self, errors):
        self.errors = errors
        super(ParseError, self).__init__(u'\n'.join(map(StringType, self.errors)))

class TokenizeError(PlyplusException):
    pass


class WeakPickleMixin(object):
    """Prevent pickling of weak references to attributes"""

    weak_attributes = (
            'parent',
        )

    def __getstate__(self):
        d = self.__dict__.copy()

        # Pickle weak references as hard references, pickle deals with circular references for us
        for key, val in d.items():
            if isinstance(val, ref):
                d[key] = val()

        return d

    def __setstate__(self, data):
        self.__dict__.update(data)

        # Convert hard references that should be weak to weak references
        for key in data:
            val = getattr(self, key)
            if key in self.weak_attributes and val is not None:
                setattr(self, key, ref(val))

class Str(WeakPickleMixin, StringType):
    pass

class TokValue(Str):
    def __new__(cls, s, type=None, line=None, column=None, pos_in_stream=None, index=None):
        inst = Str.__new__(cls, s)
        inst.type = type
        inst.line = line
        inst.column = column
        inst.pos_in_stream = pos_in_stream
        inst.index = index
        return inst

