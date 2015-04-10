# PlyPlus - a friendly yet powerful LR-parser in Python.

Plyplus is a general-purpose parser built on top of [PLY](http://www.dabeaz.com/ply/), written in python, with a slightly different approach to parsing.

## Main Concepts

1. *Separation of code from grammar*: Grammar files are more readable and portable, and it makes the code cleaner too.

2. *Always build an AST (tree)*: Every application, not matter how small, can benefit from the power and simplicity of working with a tree, instead of a state-machine.

3. *Follow Python's Idioms*: Beauty, simplicity and readability are more important than speed. But Plyplus is fast enough!


## Features

 - EBNF grammar (supported: parentheses, '|', '\*', '?', and '+', inline tokens, token fragements, and more)
 - LR-parser
 - Builds an AST automagically based on the grammar
 - Selectors: run powerful css-like queries on the AST
 - Nested grammars (a grammar within a grammar. Useful for HTML/CSS, for example)
 - Unicode support
 - Python 2.7, Python 3.3 and PyPy 1.9 compatible
 - Fully-working Python 2.x grammar included

## Q & A

Q. How capable is Plyplus?

A. Plyplus is capable of parsing any LR-compatible grammar. It supports post-tokenizing code, so it's capable of parsing python (it comes with a ready-to-use python parser). Other features, such as sub-grammars, provide more flexibility to handle the trickier grammars.

Q. How fast is it?

A. Plyplus does not put speed as its first priority. However, right now it manages to parse the entire Python26/Libs directory (200 files, 4mb of text, including post-processing) in about 42 seconds on my humble dual-core 2ghz 2gb-ram machine (and 30 seconds with PyPy).

Q. So what is Plyplus' first priority?

A. Power and simplicity. See the examples and judge for yourself.

Q. I want to use Plyplus in a threaded application. Is it thread safe?

A. Yes, but you must pay attention. Plyplus relies on PLY, it can cause problems if you try to define multiple parsers at the same time using threads. Please make sure not to do that.


## Tutorials

Learn how to write a grammar for Plyplus at the [tutorial](/docs/tutorial.md)

Learn how to query the AST using [selectors](/docs/selectors.md)

## Examples

This section contains examples of plyplus usage. For a better explanation, check out [the tutorial](/docs/tutorial.md). If something is still not clear, feel free to email me and ask!

### Parsing Python

We'll use Plyplus' grammar for Python, and play with os.py for a bit (though it could be any Python file).

For starters, let's do something simple: Let's list all of the functions (or methods) in the os module. We'll query the AST using [selectors](/docs/selectors.md), so click the link if you want to be able to follow (or maybe an understanding of CSS/JQuery is enough?).

    >>> import plyplus, plyplus.grammars
    >>> g = plyplus.Grammar(plyplus.grammars.open('python.g'))   # load python grammar
    >>> t = g.parse(file(r'c:\python27\lib\os.py').read())                  # read os.py
    >>> t.select('funcdef > name > *:is-leaf')
    ['_get_exports_list', 'makedirs', 'removedirs', 'renames', 'walk', 'execl', 'execle', 'execlp', 'execlpe', ...

(Run it yourself for the full input)

Now let's count how many times os.py calls isinstance:

    >>> len(t.select('/isinstance/'))
    3

Interesting! But where in the file are they called? We can use the "line" attribute to find out (there's also a column attribute!):

    >>> [x.line for x in t.select('/isinstance/')]
    [669, 689, 709]

Let's look at one of those calls. We'll need to select more context for that.

    >>> t.select('=funccall > name > /isinstance/')[0]
    funccall(name('isinstance'), arglist(arg(name('cmd')), arg(name('basestring'))))

More context?

    >>> _.parent().parent().parent()
    funccall(attrget(name('subprocess'), name('Popen')), arglist(arg(name('cmd')), arg(name('shell'), funccall(...

Hard to read? Try looking at it visually! (requires pydot)

    >>> _.to_png_with_pydot(r'calling_popen.png')

![calling\_popen.png](/docs/calling_popen.png)

### Parsing INI files

INI files are too open-handed to be a good candidate for LR-parsing, but PlyPlus can handle them using nested grammars. By parsing different elements separately, a "]" symbol can be both a special token and just part of the text, all in the same file.

Let's parse an INI file that comes with NumPy.

    >>> g = plyplus.Grammar(plyplus.grammars.open('config.g'), auto_filter_tokens=False)   # load config grammar
    >>> t = g.parse(file(r"C:\Python26\Lib\site-packages\numpy\core\lib\npy-pkg-config\npymath.ini").read())

List the sections:

    >>> t.select('section > start > name *')
    ['meta', 'variables', 'default', 'msvc']

Let's look at the meta section

    >>> t.select('=section /meta/')
    [section(start(name('meta')), option(start(name('Name'), start(value('npymath')))), ...

(The start heads denote a sub-grammar)

Let's pretty-print it! We can use a transformer to do it. A transformer is a tree-visitor that returns a new value for each head (branch) it visits.

    >>> class PrettyINI(plyplus.STransformer):
        def option(self, tree):
            name = tree.select1('name *')   # select1 asserts only one result
            value = tree.select1('value *')
            return '%s = %s' % (name, value)
        def section(self, tree):
            name = tree.select1('name *')
            return '[%s]\n\t%s' % (name, '\n\t'.join(tree.tail[1:]))

Now that each rule has code to handle it, let's run it!

    >>> meta = t.select1('=section /meta/')
    >>> print PrettyINI().transform( meta )
    [meta]
            Name = npymath
            Description = Portable, core math library implementing C99 standard
            Version = 0.1

It works! Now that it's done, we can use it to output the rest of the file as well:

    >>> print '\n'.join( PrettyINI().transform(t).tail )
    ... (left as an excercise to the reader ;)


## License

Plyplus uses the [MIT license](https://github.com/jquery/jquery/blob/master/MIT-LICENSE.txt).

## Afterword

I hope this readme inspired you to play with Plyplus a bit, and maybe even use it for your project.

For more examples, check out the [test module](/plyplus/test/test_parser.py)

If you have any questions or ideas, please email me at erezshin+plyplus at gmail com
