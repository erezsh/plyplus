# PlyPlus tutorial.

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

The rule 'name' (as referred to by start), contains just one token. The token is defined using a regular expression (all tokens are regexps), and matches words (any sequence of one or more letters). Note that we defined it in a new rule, instead of defining it anonymously in 'start', because plyplus filters the output for tokens that don't reside within their own rule. The rationale is that most tokens are useless punctuation, and in the cases that they aren't, the rule is useful to explain their significance.

Let's see the result of parsing with the grammar.

    >>> r=list_parser.parse('cat,milk,dog')
    >>> print r
    start(name(u'1:1|cat'), name(u'1:5|milk'), name(u'1:10|dog'))

The result is a STree instance, with a 'head' attribute of 'start' and a 'tail' attribute which is a list of nested STree instances. The tokens themselves are instances of str (or unicode) that contain extra information such as the line and column of the token in the text.

( Note: It's possible to keep the commas as well ("punctuation tokens"), by instanciating Grammar with auto\_filter\_tokens=False )

We can apply a simple list comprehension to get the list data:

    >>> [str(x.tail[0]) for x in r.tail]
    ['cat', 'milk', 'dog']

Or we can use selectors:

    >>> r.select('name>*')
    [u'1:1|cat', u'1:5|milk', u'1:10|dog']


That seems like a lot of overhead just to split a list, doesn't it? It is. But the beauty of using grammars is in how easy it is to add a lot of complexity. Now that we know the basics, let's write a grammar that takes a string of nested python-ish lists and returns a flat list of all the numbers in it.

    >>> list_parser = Grammar("""
            start: list ;                           // We only match a list
            @list : '\[' item (',' item)* '\]' ;   // Define a list
            @item : number | list ;                 // Define an item, provide nesting
            number: '\d+' ;
            SPACES: '[ ]+' (%ignore) ;              // Ignore spaces
            """)

    >>> res = list_parser.parse('[1, 2, [ [3,4], 5], [6,7   ] ]')
    >>> map(int, res.select('number>*'))
    [1, 2, 3, 4, 5, 6, 7]

This example contained some new elements, so here they are briefly:

1. Prepending '@' to a rule name tells plyplus to always expand it. This is why the rules '@list' and '@item' do not appear in the output.

2. Plyplus grammars support C++-like comments (// or /*..*/)

3. 'SPACES' is the first token we defined explicitly. It matches a sequence of spaces, and the special token flag '%ignore' tells plyplus not to include it when parsing (adding 'WHITESPACE+' everywhere would make the grammar very cumbersome, and slower).

Finally, if we have pydot and graphviz installed, we can visualize the tree by typing:

    >>> res.to_png_with_pydot('list_parser_tree.png')

![pydot visualization](/docs/list_parser_tree.png "pydot visualization")

The last example (for now) shows Plyplus' error handling. Let's say we forgot to open the brackets in the former sample input:

    >>> list_parser.parse('[1, 2,[], [ [3,4], 5], [6,7   ]]')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "plyplus\plyplus.py", line 505, in parse
        return self._grammar.parse(text)
      File "plyplus\plyplus.py", line 584, in parse
        raise ParseError('\n'.join(self.errors))
    plyplus.plyplus.ParseError: Syntax error in input at ']' (type _ANON_1) line 1 col 8
    Syntax error in input at ',' (type _ANON_3) line 1 col 22
    Syntax error in input at ']' (type _ANON_1) line 1 col 32
    Could not create parse tree!

Plyplus does not let the error pass quietly, and raises an exception. However, internally it keeps on going as far as it can, and raises the exception with a list of errors.


