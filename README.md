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

##   Example / Tutorial

In this section I'll show how to quickly write a list parser.

First we import the Grammar class:

    >>> from plyplus import Grammar

Now let's define the initial grammar:

    >>> list_parser = Grammar(r"start: name (',' name)* ; name: '\w+' ;")

A grammar is a collection of rules and tokens. In this example, we only use implicit tokens, by putting them in quotations. Let's dissect this grammar, which contains two rules:

Rule 1. --  start: name (',' name)\* ;

'start' is the rule's name. By default, parsing always starts with the 'start' rule.
The rule specifies that it must begin with a rule called 'name', follow by a sequence of (comma, name). The asterisk means that this sequence can have any length, including zero. The rule ends with a semicolon, as all rules must.

Rule 2. -- name: '\w+' ;

The rule 'name' (as referred to by start), contains just one token. The token is defined using a regular expression (all tokens are regexps), and matches words (any sequence of one or more letters). Note that we defined it in a new rule, instead of defining it anonymously in 'start', because plyplus filters the output for tokens don't reside within their own rule. The rationale is that most tokens are useless punctuation, and in the cases that they aren't, the rule is useful to explain their significance.

Let's see the result of parsing with the grammar.

    >>> list_parser.parse('cat,milk,dog')
    start(name('cat'), _anon_1_star(name('milk'), name('dog')))

The result is a STree instance, with a 'head' attribute of 'start' and a 'tail' attribute which is a list of nested STree instances.

It's simple to understand, but what is \_anon\_1\_star? It's the name of the implicit rule we created with the asterisk in 'start'. We can tell plyplus to expand it (i.e. move its matches to its parent) by using the @\* operator.

( Note: It's possible to get the commas as well ("punctuation tokens"), by instanciating Grammar with auto\_filter\_tokens=False )

Let's apply change the operator and see the result:

    >>> list_parser = Grammar(r"start: name (',' name)@* ; name: '\w+' ;")
    >>> list_parser.parse('cat,milk,dog')
    start(name('cat'), name('milk'), name('dog'))

That's cleaner! And now we can apply a simple list comprehension to get the list data:

    >>> [x.tail[0] for x in _.tail]
    ['cat', 'milk', 'dog']

Well, that seems like a lot of overhead just to split a list, doesn't it? But the beauty of using grammars is in how easy it is to add a lot of complexity. Now that we know the basics, let's write a grammar that takes a string of nested python-ish lists and returns a flat list of all the numbers in it.

    >>> list_parser = Grammar("""
            start: list ;                           // We only match a list
            @list : '\[' item (',' item)@* '\]' ;   // Define a list
            @item : number | list ;                 // Define an item, provide nesting
            number: '\d+' ;
            SPACES: '[ ]+' (%ignore) ;              // Ignore spaces
            """)

    >>> res = list_parser.parse('[1, 2, [ [3,4], 5], [6,7   ] ]')
    >>> [x.tail[0] for x in _.tail]
    ['1', '2', '3', '4', '5', '6', '7']

This example contained some new elements, so here they are briefly:

1. Prepending '@' to a rule name tells plyplus to always expand it. This is why the rules '@list' and '@item' do not appear in the output.

2. Plyplus grammars support C++-like comments (not C's at the moment, though)

3. 'SPACES' is the first token we defined explicitly. It matches a sequence of spaces, and the special token flag '%ignore' tells plyplus not to include it when parsing (adding 'WHITESPACE+' everywhere would make the grammar very cumbersome, and slower).

Finally, if we have pydot and graphviz installed, we can visualize the tree by typing:

    >>> res.to_png_with_pydot('list_parser_tree.png')

    ![pydot visualization](list_parser_tree.png "pydot visualization")

The last example (for now) shows Plyplus' error handling and forgiving nature (largely the effect of using PLY as its engine). Let's say we forgot to open the brackets in the former sample input:

    >>> list_parser.parse('1, 2, [ [3,4], 5], [6,7   ]')
    Syntax error in input at '1' (type SIMP_4) line 1 col 1
    Syntax error in input at ',' (type SIMP_0) line 1 col 18
    start(number('6'), number('7'))

Plyplus yells that it didn't expect a '1' at this point. However, it keep on going. It get confused again at the 4th comma, but then pulls itself together and continues parsing the last list properly, returning 6 and 7.
SIMP\_4 and SIMP\_0 are the automatic name given to the bracket tokens. Had we defined them explicitly we would get even better error messages.

I hope this inspired you to play with Plyplus a bit, and maybe even use it for your project.

For more examples, check out the test module: http://github.com/erezsh/plyplus/blob/master/test/plyplus\_test.py

If you have any questions or ideas, you can email my at: erez27+plyplus at gmail com
