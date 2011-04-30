start: file_input;
//module_header: string NEWLINE;

  @file_input : file_input? (NEWLINE|stmt) ;

//
//     STATEMENTS
//

  @stmt : simple_stmt | compound_stmt ;

  @simple_stmt : small_stmt (SEMI small_stmt)+? SEMI? NEWLINE;

  @small_stmt : expr_stmt
    | assign_stmt
    | augassign_stmt
    | print_stmt
    | del_stmt
    | flow_stmt
    | import_stmt
    | global_stmt
    | exec_stmt
    | assert_stmt
    ;


  @compound_stmt : if_stmt
    | while_stmt
    | for_stmt
    | try_stmt
    | with_stmt
    | funcdef
    | classdef
    ;

  expr_stmt : testlist;

  assign_stmt : testlist (EQUAL (yield_expr|testlist))+ ;
  augassign_stmt : testlist augassign_symbol (testlist|yield_expr) ;
  augassign_symbol : PLUSEQUAL
    | MINEQUAL
    | STAREQUAL
    | SLASHEQUAL
    | PERCENTEQUAL
    | AMPEREQUAL
    | VBAREQUAL
    | CIRCUMFLEXEQUAL
    | LEFTSHIFTEQUAL
    | RIGHTSHIFTEQUAL
    | DOUBLESTAREQUAL
    | DOUBLESLASHEQUAL
    ;

  assert_stmt : ASSERT test (COMMA test => 2)? => 2 3 ;
  del_stmt : DEL exprlist => 2;

  global_stmt : GLOBAL NAME (COMMA NAME => 2)* => 2 3;

  exec_stmt : EXEC expr (IN test (COMMA test)?)? => 2 4 6 ;

  print_stmt : PRINT (RIGHTSHIFT? test (COMMA test)+? COMMA?)?  ;

  import_stmt :
      IMPORT dotted_as_name (COMMA dotted_as_name)*
    | FROM (dotted_name|DOT+ dotted_name?)
      IMPORT (STAR|import_as_names|LPAR import_as_names RPAR)
    ;

  dotted_as_name : dotted_name (AS NAME)?  ;

  import_as_names : import_as_name (COMMA import_as_name)* COMMA?  ;
  import_as_name : NAME (AS NAME)?  ;

  dotted_name : NAME (DOT NAME)* ;


// definitions
  funcdef : decorators? (DEF NAME parameters COLON suite => 2 3 5) ;
  classdef : CLASS NAME (LPAR testlist? RPAR)? COLON suite ;

// compound flow statements
  while_stmt : WHILE test COLON suite (ELSE COLON suite)? => 2 4 7 ;
  with_stmt : WITH test (AS expr)? COLON suite;
  if_stmt : IF test COLON suite (ELIF test COLON suite)* (ELSE COLON suite)? ;
  for_stmt : FOR exprlist IN testlist COLON suite (ELSE COLON suite)? ;
  try_stmt : TRY COLON suite
        (EXCEPT (test ((AS|COMMA) test)?)? COLON suite)+
        (ELSE COLON suite)?
        (FINALLY COLON suite)?
    | TRY COLON suite FINALLY COLON suite
    ;

// simple flow statements

  @flow_stmt : break_stmt
    | continue_stmt
    | return_stmt
    | raise_stmt
    | yield_stmt
    | pass_stmt
    ;

  break_stmt : BREAK => 0;
  continue_stmt : CONTINUE => 0;
  pass_stmt : PASS => 0;
  raise_stmt : RAISE (test (COMMA test (COMMA test)?)?)? ;
  return_stmt : RETURN testlist? => 2;
  yield_stmt : yield_expr ;

// suites (auxiliary)

  suite : simple_stmt | NEWLINE INDENT stmt+ DEDENT ;

// decorators

//  decorator : AT dotted_name NEWLINE  // Strict, correct version
//    | AT dotted_name LPAR RPAR NEWLINE
//    | AT dotted_name LPAR arglist RPAR NEWLINE
//    ;

// Intentionally more flexible than python syntax
decorator : AT (attrget|funccall|name) NEWLINE => 2;
decorators : decorator@+ ;

//
//     EXPRESSIONS
//

  ?or_test : and_test (OR and_test)* ;
  ?and_test : not_test (AND not_test)* ;
  @not_test : not_expr | comparison ;
  not_expr : NOT not_test => 2;
  ?comparison : expr (compare_symbol expr)*  ;
  ?expr : xor_expr (VBAR xor_expr)* ;
  ?xor_expr : and_expr (CIRCUMFLEX and_expr)* ;
  ?and_expr : shift_expr (AMPER shift_expr)* ;
  ?shift_expr : arith_expr ((LEFTSHIFT|RIGHTSHIFT) arith_expr)* ;
  ?arith_expr : term ((PLUS|MINUS) term)* ;


  arglist : (argument COMMA)+?
          ( argument COMMA?
          | STAR test (COMMA DOUBLESTAR test)?
          | DOUBLESTAR test
          ) ;

// XXX Overly permissive? (maybe gen_for belongs in arglist)
  @argument : test (|gen_for|EQUAL test) ;

  compare_symbol : LESS
    | GREATER
    | EQEQUAL
    | GREATEREQUAL
    | LESSEQUAL
    | NOTEQUAL
    | IN
    | NOT IN
    | IS
    | IS NOT
    ;

  exprlist : expr (COMMA expr)* COMMA? ;

  ?factor : PLUS factor
    | MINUS factor
    | TILDE factor
    | power
    | molecule
    ;

  fpdef : NAME
    | LPAR fplist RPAR
    ;

  fplist : fpdef (COMMA fpdef)* COMMA? ;

  lambdef : LAMBDA varargslist? COLON test ;

  old_lambdef : LAMBDA varargslist? COLON old_test ;
  old_test : or_test | old_lambdef ;

  parameters : LPAR varargslist? RPAR ;

  ?power : molecule (DOUBLESTAR factor)? ;

  @molecule : atom
//    | atom molecule_star
    | funccall
    | itemget
    | attrget
    ;

  funccall : molecule LPAR arglist? RPAR ;

  itemget : molecule LSQB subscriptlist RSQB => 1 3;

  attrget : molecule DOT NAME => 1 3;

  subscript : DOT DOT DOT
    | test
    | test? COLON (sliceop|test sliceop?|)
    ;
  sliceop : COLON test?  ;

  subscriptlist : subscript (COMMA subscript)* COMMA? ;

  ?term : factor ((STAR|SLASH|PERCENT|DOUBLESLASH) factor)* ;

  ?test : or_test
    | or_test IF or_test ELSE test
    | lambdef
    ;

  ?testlist : test testlist_star? COMMA? ;
  testlist1 : test testlist_star?  ;
  @testlist_star : testlist_star? COMMA test ;

  varargslist : vararg (COMMA vararg)+?
            ((COMMA STAR NAME)? (COMMA DOUBLESTAR NAME)?
            |COMMA
            )
    | STAR NAME (COMMA DOUBLESTAR NAME)?
    | DOUBLESTAR NAME
    ;

vararg : fpdef (EQUAL test)? ;

  yield_expr : YIELD testlist? ;

// There are small silly differences between list comprehensions and generators.
// Additionally, each of them have its own subtlities.
// Most of them don't really make sense.
// >>> [x for x in 1,2,]
// [1, 2]
// >>> [x for x in 1,]
// SyntaxError: invalid syntax
// >>> (x for x in 1,2)
// SyntaxError: invalid syntax
// >>> [x for x in 1,2]
// [1, 2]

tuple : LPAR tuplemaker? RPAR ;
tuplemaker : test (gen_for | (COMMA test)+? COMMA?) ;
gen_for : FOR exprlist IN or_test gen_iter?  ;
gen_if : IF old_test gen_iter?  ;
gen_iter : gen_for | gen_if ;
 
list : LSQB listmaker? RSQB ;
listmaker : test (list_for | (COMMA test)+? COMMA?) ;
list_for : FOR exprlist IN testlist_safe list_iter?  ;
list_if : IF old_test list_iter?  ;
list_iter : list_for | list_if ;
testlist_safe : old_test ((COMMA old_test)+ COMMA?)? ;

dict : LBRACE dictmaker? RBRACE ;
dictmaker : test COLON test (COMMA test COLON test)+? COMMA? ;

set : LBRACE listmaker RBRACE => 2;

repr : BACKQUOTE testlist1 BACKQUOTE => 2;

@atom : tuple
    | list
    | dict
    | set
    | LPAR yield_expr RPAR => 2
    | repr
    | name
    | number
    | string+
    ;

name: NAME;
number: DEC_NUMBER | HEX_NUMBER | OCT_NUMBER | FLOAT_NUMBER | IMAG_NUMBER;
string: STRING|LONG_STRING;

// Tokens!

// number taken from tokenize module
DEC_NUMBER: '[1-9]\d*[lL]?';
HEX_NUMBER: '0[xX][\da-fA-F]*[lL]?';
OCT_NUMBER: '0[0-7]*[lL]?';
FLOAT_NUMBER: '((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)';
IMAG_NUMBER: '(\d+[jJ]|((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)[jJ])';

//OPASSIGN: '\+=|-=|\*=|/=|/\/=|%=|\*\*=|&=|\|=|\^=|\<\<=|\>\>=';

STRING : '(u|b|)r?("(?!"").*?(?<!\\)(\\\\)*?"|\'(?!\'\').*?(?<!\\)(\\\\)*?\')' ;
LONG_STRING : '(?s)(u|b|)r?(""".*?(?<!\\)(\\\\)*?"""|\'\'\'.*?(?<!\\)(\\\\)*?\'\'\')'
    {%newline}
    ;

LEFTSHIFTEQUAL: '\<\<=';
RIGHTSHIFTEQUAL: '\>\>=';
DOUBLESTAREQUAL: '\*\*=';
DOUBLESLASHEQUAL: '/\/=';

EQEQUAL: '==';
NOTEQUAL: '!=|<>';
LESSEQUAL: '<=';
LEFTSHIFT: '\<\<';
GREATEREQUAL: '>=';
RIGHTSHIFT: '\>\>';
PLUSEQUAL: '\+=';
MINEQUAL: '-=';
DOUBLESTAR: '\*\*';
STAREQUAL: '\*=';
DOUBLESLASH: '/\/';
SLASHEQUAL: '/=';
VBAREQUAL: '\|=';
PERCENTEQUAL: '%=';
AMPEREQUAL: '&=';
CIRCUMFLEXEQUAL: '\^=';

COLON: ':';
COMMA: ',';
SEMI: ';';
PLUS: '\+';
MINUS: '-';
STAR: '\*';
SLASH: '/';
VBAR: '\|';
AMPER: '&';

LESS: '<';
GREATER: '>';
EQUAL: '=';
DOT: '\.';
PERCENT: '%';
BACKQUOTE: '`';
CIRCUMFLEX: '\^';
TILDE: '~';
AT: '@';

LPAR: '\(';
RPAR: '\)';
LBRACE: '{';
RBRACE: '}';
LSQB: '\[';
RSQB: ']';

NEWLINE: '(\r?\n[\t ]*)+'    // Don't count on the + to prevent multiple NEWLINE tokens. It's just an optimization
    {%newline}
    ;

WS: '[\t \f]+' {%ignore};
LINE_CONT: '\\[\t \f]*\r?\n' {%ignore} {%newline};
COMMENT: '\#[^\n]*'{%ignore};

NAME: '[a-zA-Z_][a-zA-Z_0-9]*(?!r?"|r?\')'  //"// Match names and not strings (r"...")
    {%unless
        PRINT: 'print';
        IMPORT: 'import';
        FROM: 'from';
        GLOBAL: 'global';
        EXEC: 'exec';
        ASSERT: 'assert';
        DEL: 'del';
        AS: 'as';
        LAMBDA: 'lambda';

        // 
        DEF: 'def';
        CLASS: 'class';

        // Flow Blocks
        TRY: 'try';
        EXCEPT: 'except';
        FINALLY: 'finally';
        IF: 'if';
        ELIF: 'elif';
        ELSE: 'else';
        FOR: 'for';
        WHILE: 'while';
        WITH: 'with';

        // Flow
        BREAK: 'break';
        CONTINUE: 'continue';
        RETURN: 'return';
        YIELD: 'yield';
        RAISE: 'raise';
        PASS: 'pass';

        // Operators
        AND: 'and';
        OR: 'or';
        NOT: 'not';
        IS: 'is';
        IN: 'in';
    }
    ;

INDENT: '<INDENT>';
DEDENT: '<DEDENT>';

%newline_char: '\n';    // default, can be omitted

###
from python2_indent_postlex import PythonIndentTracker 
self.lexer_postproc = PythonIndentTracker

