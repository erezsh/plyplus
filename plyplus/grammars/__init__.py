import os.path
from io import open as _open

def open(grammar_name):
    return _open( os.path.join(os.path.dirname(__file__), grammar_name) )

python = open('python.g')
config = open('config.g')
selector = open('selector.g')
