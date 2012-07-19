# PlyPlus - a general-purpose, friendly yet powerful parser written in Python.

Plyplus is a general-purpose parser built on top of [PLY](http://www.dabeaz.com/ply/), written in python, with a slightly different approach to parsing.

Most parsers work by calling a function for each rule they identify, which processes the data and returns to the parser. Plyplus parses the entire file into a parse-tree, letting you search and process it using visitors and pattern-matching.

Plyplus makes two uncommon separations: of code from grammar, and of processing from parsing.  The result of this approach is (hopefully) a cleaner design, more powerful grammar processing, and a parser which is easier to write and to understand.

## Features

 - Automatic line counting
 - Readable errors
 - Inline tokens (named, or anonymous with partial auto-naming)
 - Rule operators mimicking regular expressions (supported: parentheses, '|', '\*', '?', and '+')
 - Nested grammars (a grammar within a grammar. Useful for HTML/CSS, for example)
 - Debug mode (dumps debug information during parsing)
 - Customizable parser output, defined in grammar
 - Comes with a full, flexible, Python grammar

## Questions

Q. How capable is Plyplus?

A. Plyplus is capable of parsing any LR-compatible grammar. It supports post-tokenizing code, so it's capable of parsing python (it comes with a ready-to-use python parser). Other features, such as sub-grammars, provide more options to handle the trickier grammars.

Q. How fast is it?

A. Plyplus does not put speed as its first priority. However, right now it manages to parse the entire Python26\Libs directory (200 files, 4mb of text, including post-processing) in about 42 seconds on my humble dual-core 2ghz 2gb-ram machine.

Q. So what is Plyplus' first priority?

A. Ease of use. See the example and judge for yourself.

## Tutorials

Learn how to write a grammar for Plyplus at the [tutorial](/erezsh/plyplus/blob/master/tutorial.md)

Learn how to query the AST using [selectors](/erezsh/plyplus/blob/master/selectors.md)

## Examples

This section contains examples of plyplus usage. For a better explanation, check out [the tutorial](/erezsh/plyplus/blob/master/tutorial.md). If something is still not clear, feel free to email me and ask!

### Parsing Python

Let's list all the functions (or methods) in the os module.

I will be querying the AST using [selectors](/erezsh/plyplus/blob/master/selectors.md), so click the link if you want to be able to follow (or maybe an understanding of CSS/JQuery is enough?).

    >>> import plyplus
    >>> g = plyplus.Grammar(file(r'e:\python\plyplus\grammars\python.g'))   # load grammar
    >>> t = g.parse(file(r'c:\python27\lib\os.py').read())                  # read os.py
    >>> t.select('funcdef > name > *:is-leaf')
    ['_get_exports_list', 'makedirs', 'removedirs', 'renames', 'walk', 'execl', 'execle', 'execlp', 'execlpe', 'execvp', 'execvpe', '_execvpe', 'unsetenv', '__init__', '__setitem__', '__getitem__', '__delitem__', '__delitem__', 'clear', 'pop', 'has_key', '__contains__', 'get', 'update', 'copy', '__init__', '__setitem__', 'update', '__delitem__', 'clear', 'pop', 'copy', 'getenv', '_exists', '_spawnvef', 'spawnv', 'spawnve', 'spawnvp', 'spawnvpe', 'spawnl', 'spawnle', 'spawnlp', 'spawnlpe', 'popen2', 'popen3', 'popen4', '_make_stat_result', '_pickle_stat_result', '_make_statvfs_result', '_pickle_statvfs_result', 'urandom']

Now let's count how many times os.py calls isinstance:

    >>> len(t.select('/isinstance/'))
    3

Interesting. Where in the file are they called? We can use the line attribute (there's also a column attribute!):

    >>> [x.line for x in t.select('/isinstance/')]
    [669, 689, 709]

Let's look at one of those calls. We'll need to select more context for that.

    >>> t.select('=funccall > name > /isinstance/')[0]
    funccall(name('isinstance'), arglist(arg(name('cmd')), arg(name('basestring'))))

More context?

    >>> _.parent().parent().parent()
    funccall(attrget(name('subprocess'), name('Popen')), arglist(arg(name('cmd')), arg(name('shell'), funccall(name('isinstance'), arglist(arg(name('cmd')), arg(name('basestring'))))), arg(name('bufsize'), name('bufsize')), arg(name('stdin'), name('PIPE')), arg(name('stdout'), name('PIPE')), arg(name('close_fds'), name('True'))))

Hard to read? Try looking at it visually! (requires pydot)

    >>> _.to_png_with_pydot(r'calling_popen.png')

[calling\_popen.png](/erezsh/plyplus/blob/master/calling_popen.png)


## License

Plyplus uses the [JQuery license](http://jquery.org/license). Briefly, it's licensed under either MIT of GPL, whichever suits you better.

## Afterword

I hope this readme inspired you to play with Plyplus a bit, and maybe even use it for your project.

For more examples, check out the test module: http://github.com/erezsh/plyplus/blob/master/test/plyplus\_test.py

If you have any questions or ideas, please email me at erez27+plyplus at gmail com
