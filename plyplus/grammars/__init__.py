import os.path
from io import open

_open = open
def open(grammar_name):
    return _open( os.path.join(os.path.split(__file__)[0], grammar_name) )

