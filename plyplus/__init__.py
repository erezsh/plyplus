"""A friendly yet powerful LR-parser written in Python."""

from __future__ import absolute_import

import os
from tempfile import gettempdir

PLYPLUS_DIR = os.path.join(gettempdir(), 'plyplus')

try:
    os.mkdir(PLYPLUS_DIR)
except OSError:
    pass

from .plyplus import Grammar, SVisitor, STransformer, is_stree

from .plyplus import PlyplusException, GrammarException, TokenizeError, ParseError

from . import selector
selector.install()

