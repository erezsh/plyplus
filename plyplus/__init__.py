"""A friendly yet powerful LR-parser written in Python."""

from __future__ import absolute_import

from getpass import getuser
import os
from tempfile import gettempdir

__version__ = "0.7.5"

PLYPLUS_DIR = os.path.join(gettempdir(), 'plyplus-' + getuser())

try:
    os.mkdir(PLYPLUS_DIR)
except OSError:
    pass

from .strees import SVisitor, STransformer, is_stree
from .common import PlyplusException, GrammarException, TokenizeError, ParseError
from .plyplus import Grammar

from . import selector
selector.install()

