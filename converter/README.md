# Simple converter from lex/yacc files to PlyPlus parser
## When to use

If you have grammar defined in lex and yacc files and you want to use it with Python.

## How to use it

Assuming your lex and yacc files are *expr.l* and *expr.y* respectively, type

*python converter.py expr*

This will produce *expr.py* file containing PlyPlus parser. Feed it with data via standard input.

## Requirements
### Lex files

Only second section (delimited by *%%*) is read. Each rule should match the pattern:

*REGEXP        return TOKEN ;*

### Yacc files

Only second section (delimited by *%%*) is read. Each rule should match the pattern:

*TOKEN : PATTERN1 | Pattern2 | Pattern3 ;*

## Example

Take a look at the example of simple calculator. Run

*python converter.py expr*

*python expr.py*

and then type in some expression to parse.

## Output

Converter generates simple parser. It's output, is printed into console (it's a kind of AST). In addition graphical representation of AST is generated in *tree.png* file.

## Customization

If you want to perform some action during parsing, take a look at the *ExprTransformer* class. Modify some lambdas or replace them with more complex functions.

For more info, please read PlyPlus tutorials.
