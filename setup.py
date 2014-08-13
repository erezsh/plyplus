import re
from distutils.core import setup

__version__ ,= re.findall('__version__ = "(.*)"', open('plyplus/__init__.py').read())

setup(
    name = "PlyPlus",
    version = __version__,
    packages = ['plyplus', 'plyplus.test', 'plyplus.grammars', 'examples', 'docs'], #find_packages(),
    #scripts = ['say_hello.py'],

    requires = ['ply'], #['docutils>=0.3'],
    install_requires = ['ply'],

    package_data = {
        '': ['*.md', '*.g'],
        'docs': ['*.png'],
    },

    # metadata for upload to PyPI
    author = "Erez Shinan",
    author_email = "erezshin@gmail.com",
    description = "a friendly yet powerful LR-parser written in Python",
    license = "MIT/GPL",
    keywords = "LR parser ast ply",
    url = "https://github.com/erezsh/plyplus",   # project home page, if any
    download_url = "https://github.com/erezsh/plyplus/tarball/master",
    long_description='''
Plyplus is a general-purpose parser built on top of PLY (http://www.dabeaz.com/ply/), written in python, with a slightly different approach to parsing.

Most parsers work by calling a function for each rule they identify, which processes the data and returns to the parser. Plyplus parses the entire file into a parse-tree, letting you search and process it using visitors and pattern-matching.

Plyplus makes two uncommon separations: of code from grammar, and of processing from parsing. The result of this approach is (hopefully) a cleaner design, more powerful grammar processing, and a parser which is easier to write and to understand.

Features:

- Automatically builds an AST. Customizable in grammar (expand and flatten nodes automatically)
- Selectors: run powerful queries on the AST
- Rule operators mimicking regular expressions (supported: parentheses, '|', '*', '?', and '+')
- Comes with a full, flexible, Python grammar
- Nested grammars (a grammar within a grammar. Useful for HTML/CSS, for example)
- Automatic line counting
- From PLY: Readable errors, Debug mode
- And more! ...
    ''',

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],

    # could also include long_description, download_url, classifiers, etc.
)

