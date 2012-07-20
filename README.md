# PlyPlus - a friendly yet powerful LR-parser written in Python.

Plyplus is a general-purpose parser built on top of [PLY](http://www.dabeaz.com/ply/), written in python, with a slightly different approach to parsing.

Most parsers work by calling a function for each rule they identify, which processes the data and returns to the parser. Plyplus parses the entire file into a parse-tree, letting you search and process it using visitors and pattern-matching.

Plyplus makes two uncommon separations: of code from grammar, and of processing from parsing.  The result of this approach is (hopefully) a cleaner design, more powerful grammar processing, and a parser which is easier to write and to understand.

## Features

 - Automatically builds an AST. Customizable in grammar (expand and flatten nodes automatically)
 - Selectors: run powerful queries on the AST
 - Rule operators mimicking regular expressions (supported: parentheses, '|', '\*', '?', and '+')
 - Comes with a full, flexible, Python grammar
 - Nested grammars (a grammar within a grammar. Useful for HTML/CSS, for example)
 - Automatic line counting
 - From PLY: Readable errors, Debug mode
 - And more! ...

## Questions

Q. How capable is Plyplus?

A. Plyplus is capable of parsing any LR-compatible grammar. It supports post-tokenizing code, so it's capable of parsing python (it comes with a ready-to-use python parser). Other features, such as sub-grammars, provide more options to handle the trickier grammars.

Q. How fast is it?

A. Plyplus does not put speed as its first priority. However, right now it manages to parse the entire Python26/Libs directory (200 files, 4mb of text, including post-processing) in about 42 seconds on my humble dual-core 2ghz 2gb-ram machine.

Q. So what is Plyplus' first priority?

A. Ease of use. See the example and judge for yourself.

## Tutorials

Learn how to write a grammar for Plyplus at the [tutorial](/erezsh/plyplus/blob/master/tutorial.md)

Learn how to query the AST using [selectors](/erezsh/plyplus/blob/master/selectors.md)

## Examples

This section contains examples of plyplus usage. For a better explanation, check out [the tutorial](/erezsh/plyplus/blob/master/tutorial.md). If something is still not clear, feel free to email me and ask!

### Parsing Python

We'll use Plyplus' grammar for Python, and play with os.py for a bit (though it could be any Python file).

For starters, let's do something simple: Let's list all of the functions (or methods) in the os module. We'll query the AST using [selectors](/erezsh/plyplus/blob/master/selectors.md), so click the link if you want to be able to follow (or maybe an understanding of CSS/JQuery is enough?).

    >>> import plyplus
    >>> g = plyplus.Grammar(file(r'e:\python\plyplus\grammars\python.g'))   # load grammar
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

[calling\_popen.png](/erezsh/plyplus/blob/master/calling_popen.png)

### Parsing INI files

INI files are too open-handed to be a good candidate for LR-parsing, but PlyPlus can handle them using nested grammars. By parsing different elements separately, a "]" symbol can be both a special token and just part of the text, all in the same file.

Let's parse an INI file that comes with numpy.

    >>> g = plyplus.Grammar(file(r'e:\python\plyplus\grammars\config.g'))   # load grammar
    >>> t = g.parse(file(r"C:\Python26\Lib\site-packages\numpy\core\lib\npy-pkg-config\npymath.ini").read())

List the sections:

    >>> t.select('section > start > name *')
    ['meta', 'variables', 'default', 'msvc']

Let's look at the meta section

    >>> t.select('=section /meta/')
    [section(start(name('meta')), option(start(name('Name'), start(value('npymath')))), ...

(The start heads denote a subgrammar)

Let's pretty-print it! We can use a transformer to do it. A transformer is a tree-visitor that returns a new value for each head (branch) it visits.

    >>> class PrettyINI(plyplus.STransformer):
        def option(self, tree):
            name = tree.select('name *')[0]
            value = tree.select('value *')[0]
            return '%s = %s' % (name, value)
        def section(self, tree):
            name = tree.select('name *')[0]           
            return '[%s]\n\t%s' % (name, '\n\t'.join(tree.tail[1:]))

Now that each rule has code to handle it, let's run it!

    >>> meta = t.select('=section /meta/')[0]
    >>> print PrettyINI().transform( meta )
    [meta]
            Name = npymath
            Description = Portable, core math library implementing C99 standard
            Version = 0.1

It works! Now that it's done, we can use it to output the rest of the file as well:

    >>> print '\n'.join( PrettyINI().transform(t) )
    ... (left as an excercise to the reader ;)


## License

Plyplus uses the [JQuery license](http://jquery.org/license). Briefly, it's licensed under either MIT of GPL, whichever suits you better.

## Afterword

I hope this readme inspired you to play with Plyplus a bit, and maybe even use it for your project.

For more examples, check out the [test module](/erezsh/plyplus/blob/master/test/plyplus_test.py)

If you have any questions or ideas, please email me at erez27+plyplus at gmail com
