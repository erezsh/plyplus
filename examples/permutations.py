"""Demonstrates the use of the permutation operator."""
from plyplus import Grammar

# Basic Permutations
perm1 = Grammar("""
start : a ^ b? ^ c ;

a : 'a' ;
b : 'b' ;
c : 'c' ;

WS: '[ \t]+' (%ignore);
""")

print perm1.parse(' a c b').pretty()
print perm1.parse('c a ').pretty()

# Permutations with a separator
perm2 = Grammar("""
start : a ^ (b|d)? ^ c ^^ ( COMMA | SEMI ) ;

a : 'a' ;
b : 'b' ;
c : 'c' ;
d : 'd' ;

COMMA : ',' ;
SEMI  : ';' ;

WS: '[ \t]+' (%ignore);
""")

print perm2.parse(' c ; a,b').pretty()
print perm2.parse('c;d, a ').pretty()
print perm2.parse('c , a ').pretty()
