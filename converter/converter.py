"""Author: Piotr Ociepka
Copyright (C) 2015 Piotr Ociepka
This software is released under the MIT license.

Converts .l and .y files into simple PlyPlus parser.
"""
import sys

def read_file(name, ext, part=1):
    with open(name + "." + ext) as grammar_file:
        return grammar_file.read().split("%%")[part]

def read_yacc_tokens(name):
    yacc = read_file(name, "y", 0)
    tokens = yacc.split("%token")[1].strip()
    return tokens.split()

def prod_name(prod):
    return prod.split(":")[0]

name = sys.argv[1]
Name = name.capitalize()

lex = read_file(name, "l")
lex_prods = [p.strip() for p in lex.split(";") if p.strip()]
yacc = read_file(name, "y")
yacc_prods = [p.strip() + " ;" for p in yacc.split(";") if p.strip()]

first_prod = prod_name(yacc_prods[0])
parser = "\nstart: %s ;\n" % first_prod
tokens = []

for p in yacc_prods:
    parser += "\n" + p + "\n"
    tokens.append(prod_name(p))

parser += "\n"

for p in lex_prods:
    pattern = p.split("return")[0].strip()
    token = p.split("return")[1].strip()
    parser += token + " : '" + pattern + "' ;\n"
    tokens.append(token)

transformer = "class %sTransformer(STransformer):" % (Name)
for t in tokens:
    transformer += """
    %s = lambda self, node: node""" % (t)

program = """
from plyplus import Grammar, STransformer

json_grammar = Grammar(r\"\"\"
%s
\"\"\")

%s

input = raw_input()
tree = json_grammar.parse(input)
tree.to_png_with_pydot(r'tree.png')
print(%sTransformer().transform(tree))
""" % (parser, transformer, Name)

with open(name + ".py", "w") as out_file:
    out_file.write(program)
