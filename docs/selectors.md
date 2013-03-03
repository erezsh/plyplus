# PlyPlus selectors tutorial.

In this section I'll explain how selectors work and give a few examples.

Tip: If you've ever done web development, plyplus' selector syntax and behavior are modeled after CSS selectors.

## Syntax

Selectors are basically a list of element selectors, separated by an (optional) operator.

So informally: element [op] element [op] element ...

Here are the element selectors:

  - _name_ - match a the name of a branch (in plyplus (and lisp), called a "head").
  - _/regexp/_ - match an element for the regular expression. Catches both terminals (tokens) and heads (branches).
  - _*_ - match any element. Use sparingly.
  - _(selector1,selector2,...)_ - match the selector(s) within the current context and use the resulting element. Useful for when more than one path is valid, and for lookaheads.

And here are the operators:

  - _a b_ - matches if a is a descendant of b (okay, it's the empty operator. Still counts)
  - _a > b_ - matches if b is a child of a
  - _a ~ b_ - matches a and b are siblings (have the same parent), and b comes after a.
  - _a + b_ - matches a and b are siblings, and b comes _immmediately_ after a.
  
Elements can also have modifiers (more to come!):

  - _element:is-parent_ - matches if the element ia a head (branch)
  - _element:is-leaf_ - matches if the element ia a terminal (token)

One last thing worth noting: Selectors always return the last element. If you want to return another element, prepend the yield operator (_=_) to it.

## Some examples

So how do we use them? Let's look at this Python expression from the [readme](/README.md)

    funccall(attrget(name('subprocess'), name('Popen')), arglist(arg(name('cmd')), arg(name('shell'), funccall(name('isinstance'), arglist(arg(name('cmd')), arg(name('basestring'))))), arg(name('bufsize'), name('bufsize')), arg(name('stdin'), name('PIPE')), arg(name('stdout'), name('PIPE')), arg(name('close_fds'), name('True'))))

It's a little messy, so you can use [this visualization](/docs/calling_popen.png) as reference.

Assuming it's stored in x, let's get all of the "name" heads:

    >>> x.select('name')
    [name('subprocess'), name('Popen'), name('cmd'), name('shell'), name('isinstance '), name('cmd'), ...

Simple enough. But suppose we just want the terminals? We can select them easily:

    >>> x.select('name *')
    ['subprocess', 'Popen', 'cmd', 'shell', 'isinstance', 'cmd', 'basestring', 'bufsize', 'bufsize', 'stdin', 'PIPE', 'stdout', 'PIPE', 'close_fds', 'True']

This is equivalent to x.select('name =\*'), but if we put the yield operator first, like '=name \*', the results would be similar to the previous code.

Now let's try to find all terminals containing the letter 'n'. We can use a regexp, but just using '/.\*n.\*' will give us 'name' heads etc., so let's use a modifier too:

    >>> x.select('/.*n.*/:is-leaf')
    ['Popen', 'isinstance', 'basestring', 'stdin']

Let's filter those terminals only for arguments:
    >>> x.select('arg /.*n.*/:is-leaf')
    ['isinstance', 'basestring', 'basestring', 'stdin']

Wait! Why did we get "basestring" twice? And why is "isinstance" there? It's not a bug! Using '=arg' reveals the source: arg is matched twice, once for the inner arg, and one for the outer. Let's filter only for the inner arg, based on the known structure:

    >>> x.select('arg > name > /.*n.*/:is-leaf') 
    ['basestring', 'stdin']
    
How about all of the keyword arguments used? (notice they are pairs of names inside an "arg" head)

    >>> x.select('arg =name ~ *')
    [name('isinstance'), name('shell'), name('bufsize'), name('stdin'), name('stdout'), name('close_fds')]

## Afterword

I hope this article was clear and helpful.

Selectors have many limitations, and you can't select everything that comes to mind, but hopefully they cover most of the useful cases.

If you have any questions or ideas, please email me at erez27+plyplus at gmail com

