start: file_input;
//module_header: string NEWLINE;

  ?and_expr : shift_expr
    | shift_expr and_expr_star
    ;

  @and_expr_star : AMPER shift_expr
    | and_expr_star AMPER shift_expr
    ;

  ?and_test : not_test
    | not_test and_test_star
    ;

  @and_test_star : AND not_test
    | and_test_star AND not_test
    ;

  arglist : argument
    | argument COMMA
    | STAR test
    | STAR test COMMA DOUBLESTAR test
    | DOUBLESTAR test
    | arglist_star argument
    | arglist_star argument COMMA
    | arglist_star STAR test
    | arglist_star STAR test COMMA DOUBLESTAR test
    | arglist_star DOUBLESTAR test
    ;

  @arglist_star : argument COMMA
    | arglist_star argument COMMA
    ;

  argument : test
    | test gen_for
    | test EQUAL test
    ;

  ?arith_expr : term
    | term arith_expr_star
    ;

  @arith_expr_star : PLUS term
    | MINUS term
    | arith_expr_star PLUS term
    | arith_expr_star MINUS term
    ;

  assert_stmt : ASSERT test
    | ASSERT test COMMA test
    ;



  augassign : PLUSEQUAL
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

break_stmt : BREAK ;

  classdef : CLASS NAME COLON suite
    | CLASS NAME LPAR RPAR COLON suite
    | CLASS NAME LPAR testlist RPAR COLON suite
    ;

  comp_op : LESS
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

  ?comparison : expr
    | expr comparison_star
    ;

  @comparison_star : comp_op expr
    | comparison_star comp_op expr
    ;

  compound_stmt : if_stmt
    | while_stmt
    | for_stmt
    | try_stmt
    | with_stmt
    | funcdef
    | classdef
    ;

continue_stmt : CONTINUE ;

  decorator : AT dotted_name NEWLINE
    | AT dotted_name LPAR RPAR NEWLINE
    | AT dotted_name LPAR arglist RPAR NEWLINE
    ;

decorators : decorator+ ;

del_stmt : DEL exprlist ;

  dictmaker : test COLON test
    | test COLON test COMMA
    | test COLON test dictmaker_star
    | test COLON test dictmaker_star COMMA
    ;

  @dictmaker_star : COMMA test COLON test
    | dictmaker_star COMMA test COLON test
    ;


// import_as_name: NAME ['as' NAME]
  dotted_as_name : dotted_name (AS NAME)?  ;


  dotted_as_names : dotted_as_name
    | dotted_as_name dotted_as_names_star
    ;

  @dotted_as_names_star : COMMA dotted_as_name
    | dotted_as_names_star COMMA dotted_as_name
    ;

  dotted_name : NAME
    | NAME dotted_name_star
    ;

  @dotted_name_star : DOT NAME
    | dotted_name_star DOT NAME
    ;

encoding_decl : NAME
;

  except_clause : EXCEPT
    | EXCEPT test
    | EXCEPT test AS test
    | EXCEPT test COMMA test
    ;

  exec_stmt : EXEC expr
    | EXEC expr IN test
    | EXEC expr IN test COMMA test
    ;

  ?expr : xor_expr
    | xor_expr expr_star
    ;

  @expr_star : VBAR xor_expr
    | expr_star VBAR xor_expr
    ;

  expr_stmt : testlist augassign yield_expr
    | testlist augassign testlist
    | testlist
    | testlist expr_stmt_star
    ;

  @expr_stmt_star : EQUAL yield_expr
    | EQUAL testlist
    | expr_stmt_star EQUAL yield_expr
    | expr_stmt_star EQUAL testlist
    ;

  exprlist : expr
    | expr COMMA
    | expr exprlist_star
    | expr exprlist_star COMMA
    ;

  @exprlist_star : COMMA expr
    | exprlist_star COMMA expr
    ;

  ?factor : PLUS factor
    | MINUS factor
    | TILDE factor
    | power
    ;

  @file_input : //ENDMARKER
    | file_input_star //ENDMARKER
    ;

  @file_input_star : NEWLINE
    | stmt
    | file_input_star NEWLINE
    | file_input_star stmt
    ;

  flow_stmt : break_stmt
    | continue_stmt
    | return_stmt
    | raise_stmt
    | yield_stmt
    ;

  for_stmt : FOR exprlist IN testlist COLON suite
    | FOR exprlist IN testlist COLON suite ELSE COLON suite
    ;

  fpdef : NAME
    | LPAR fplist RPAR
    ;

  fplist : fpdef
    | fpdef COMMA
    | fpdef fplist_star
    | fpdef fplist_star COMMA
    ;

  @fplist_star : COMMA fpdef
    | fplist_star COMMA fpdef
    ;

  funcdef : DEF NAME parameters COLON suite
    | decorators DEF NAME parameters COLON suite
    ;

  gen_for : FOR exprlist IN or_test
    | FOR exprlist IN or_test gen_iter
    ;

  gen_if : IF old_test
    | IF old_test gen_iter
    ;

  gen_iter : gen_for
    | gen_if
    ;

  global_stmt : GLOBAL NAME
    | GLOBAL NAME global_stmt_star
    ;

  @global_stmt_star : COMMA NAME
    | global_stmt_star COMMA NAME
    ;

  if_stmt : IF test COLON suite
    | IF test COLON suite ELSE COLON suite
    | IF test COLON suite if_stmt_star
    | IF test COLON suite if_stmt_star ELSE COLON suite
    ;

  @if_stmt_star : ELIF test COLON suite
    | if_stmt_star ELIF test COLON suite
    ;

  import_as_name : NAME
    | NAME AS NAME
    ;

  import_as_names : import_as_name
    | import_as_name COMMA
    | import_as_name import_as_names_star
    | import_as_name import_as_names_star COMMA
    ;

  @import_as_names_star : COMMA import_as_name
    | import_as_names_star COMMA import_as_name
    ;

  import_from : FROM dotted_name IMPORT STAR
    | FROM dotted_name IMPORT LPAR import_as_names RPAR
    | FROM dotted_name IMPORT import_as_names
    | FROM import_from_plus dotted_name IMPORT STAR
    | FROM import_from_plus dotted_name IMPORT LPAR import_as_names RPAR
    | FROM import_from_plus dotted_name IMPORT import_as_names
    | FROM import_from_plus IMPORT STAR
    | FROM import_from_plus IMPORT LPAR import_as_names RPAR
    | FROM import_from_plus IMPORT import_as_names
    ;

  import_from_plus : DOT
    | import_from_plus DOT
    ;

import_name : IMPORT dotted_as_names ;

  import_stmt : import_name
    | import_from
    ;

  lambdef : LAMBDA COLON test
    | LAMBDA varargslist COLON test
    ;

  list_for : FOR exprlist IN testlist_safe
    | FOR exprlist IN testlist_safe list_iter
    ;

  list_if : IF old_test
    | IF old_test list_iter
    ;

  list_iter : list_for
    | list_if
    ;

  listmaker : test list_for
    | test
    | test COMMA
    | test listmaker_star
    | test listmaker_star COMMA
    ;

  @listmaker_star : COMMA test
    | listmaker_star COMMA test
    ;

  ?not_test : NOT not_test
    | comparison
    ;

  old_lambdef : LAMBDA COLON old_test
    | LAMBDA varargslist COLON old_test
    ;

  old_test : or_test
    | old_lambdef
    ;

  ?or_test : and_test
    | and_test or_test_star
    ;

  @or_test_star : OR and_test
    | or_test_star OR and_test
    ;

  parameters : LPAR RPAR
    | LPAR varargslist RPAR
    ;

pass_stmt : PASS ;

  ?power : atom
    | atom DOUBLESTAR factor
    | atom power_star
    | atom power_star DOUBLESTAR factor
    ;

  @power_star : trailer
    | power_star trailer
    ;

// print_stmt: 'print' ( [ test (',' test)* [','] ] |
//                      '>>' test [ (',' test)+ [','] ] )
  print_stmt : PRINT
    | PRINT test COMMA?
    | PRINT test print_stmt_plus COMMA?
    | PRINT RIGHTSHIFT test
    | PRINT RIGHTSHIFT test print_stmt_plus COMMA?
    ;

  print_stmt_plus : COMMA test
    | print_stmt_plus COMMA test
    ;

// raise_stmt: 'raise' [test [',' test [',' test]]]
  raise_stmt : RAISE
    | RAISE test (COMMA test (COMMA test)?)?
    ;

  return_stmt : RETURN
    | RETURN testlist
    ;

  ?shift_expr : arith_expr
    | arith_expr shift_expr_star
    ;

  @shift_expr_star : LEFTSHIFT arith_expr
    | RIGHTSHIFT arith_expr
    | shift_expr_star LEFTSHIFT arith_expr
    | shift_expr_star RIGHTSHIFT arith_expr
    ;

  @simple_stmt : small_stmt NEWLINE
    | small_stmt SEMI NEWLINE
    | small_stmt simple_stmt_star NEWLINE
    | small_stmt simple_stmt_star SEMI NEWLINE
    ;

  @simple_stmt_star : SEMI small_stmt
    | simple_stmt_star SEMI small_stmt
    ;

  sliceop : COLON
    | COLON test
    ;

  @small_stmt : expr_stmt
    | print_stmt
    | del_stmt
    | pass_stmt
    | flow_stmt
    | import_stmt
    | global_stmt
    | exec_stmt
    | assert_stmt
    ;

  @stmt : simple_stmt
    | compound_stmt
    ;

  subscript : DOT DOT DOT
    | test
    | COLON
    | COLON sliceop
    | COLON test
    | COLON test sliceop
    | test COLON
    | test COLON sliceop
    | test COLON test
    | test COLON test sliceop
    ;

  subscriptlist : subscript
    | subscript COMMA
    | subscript subscriptlist_star
    | subscript subscriptlist_star COMMA
    ;

  @subscriptlist_star : COMMA subscript
    | subscriptlist_star COMMA subscript
    ;

  suite : simple_stmt
    | NEWLINE INDENT suite_plus DEDENT
    ;

  suite_plus : stmt
    | suite_plus stmt
    ;

  ?term : factor
    | factor term_star
    ;

  @term_star : STAR factor
    | SLASH factor
    | PERCENT factor
    | DOUBLESLASH factor
    | term_star STAR factor
    | term_star SLASH factor
    | term_star PERCENT factor
    | term_star DOUBLESLASH factor
    ;

  ?test : or_test
    | or_test IF or_test ELSE test
    | lambdef
    ;

  ?testlist : test
    | test COMMA
    | test testlist_star
    | test testlist_star COMMA
    ;

  testlist1 : test
    | test testlist1_star
    ;

  @testlist1_star : COMMA test
    | testlist1_star COMMA test
    ;

  testlist_gexp : test gen_for
    | test
    | test COMMA
    | test testlist_gexp_star
    | test testlist_gexp_star COMMA
    ;

  @testlist_gexp_star : COMMA test
    | testlist_gexp_star COMMA test
    ;

  testlist_safe : old_test
    | old_test testlist_safe_plus
    | old_test testlist_safe_plus COMMA
    ;

  testlist_safe_plus : COMMA old_test
    | testlist_safe_plus COMMA old_test
    ;

  @testlist_star : COMMA test
    | testlist_star COMMA test
    ;

  trailer : LPAR RPAR
    | LPAR arglist RPAR
    | LSQB subscriptlist RSQB
    | DOT NAME
    ;

  try_stmt : TRY COLON suite try_stmt_plus
    | TRY COLON suite try_stmt_plus FINALLY COLON suite
    | TRY COLON suite try_stmt_plus ELSE COLON suite
    | TRY COLON suite try_stmt_plus ELSE COLON suite FINALLY COLON suite
    | TRY COLON suite FINALLY COLON suite
    ;

  try_stmt_plus : except_clause COLON suite
    | try_stmt_plus except_clause COLON suite
    ;

  varargslist : fpdef COMMA STAR NAME
    | fpdef COMMA STAR NAME COMMA DOUBLESTAR NAME
    | fpdef COMMA DOUBLESTAR NAME
    | fpdef
    | fpdef COMMA
    | fpdef varargslist_star COMMA STAR NAME
    | fpdef varargslist_star COMMA STAR NAME COMMA DOUBLESTAR NAME
    | fpdef varargslist_star COMMA DOUBLESTAR NAME
    | fpdef varargslist_star
    | fpdef varargslist_star COMMA
    | fpdef EQUAL test COMMA STAR NAME
    | fpdef EQUAL test COMMA STAR NAME COMMA DOUBLESTAR NAME
    | fpdef EQUAL test COMMA DOUBLESTAR NAME
    | fpdef EQUAL test
    | fpdef EQUAL test COMMA
    | fpdef EQUAL test varargslist_star COMMA STAR NAME
    | fpdef EQUAL test varargslist_star COMMA STAR NAME COMMA DOUBLESTAR NAME
    | fpdef EQUAL test varargslist_star COMMA DOUBLESTAR NAME
    | fpdef EQUAL test varargslist_star
    | fpdef EQUAL test varargslist_star COMMA
    | STAR NAME
    | STAR NAME COMMA DOUBLESTAR NAME
    | DOUBLESTAR NAME
    ;

  @varargslist_star : COMMA fpdef
    | COMMA fpdef EQUAL test
    | varargslist_star COMMA fpdef
    | varargslist_star COMMA fpdef EQUAL test
    ;

  while_stmt : WHILE test COLON suite
    | WHILE test COLON suite ELSE COLON suite
    ;

  with_stmt : WITH test COLON suite
    | WITH test with_var COLON suite
    ;

with_var : AS expr ;

  ?xor_expr : and_expr
    | and_expr xor_expr_star
    ;

  @xor_expr_star : CIRCUMFLEX and_expr
    | xor_expr_star CIRCUMFLEX and_expr
    ;

  yield_expr : YIELD
    | YIELD testlist
    ;

yield_stmt : yield_expr ;


  atom : LPAR RPAR
    | LPAR yield_expr RPAR
    | LPAR testlist_gexp RPAR
    | LSQB RSQB
    | LSQB listmaker RSQB
    | LBRACE RBRACE
    | LBRACE dictmaker RBRACE
    | BACKQUOTE testlist1 BACKQUOTE
    | name
    | number
    | atom_plus
    ;

name: NAME;
number: DEC_NUMBER | HEX_NUMBER | OCT_NUMBER | FLOAT_NUMBER | IMAG_NUMBER;
string: STRING|LONG_STRING;

atom_plus : atom_plus? string;

// Tokens!

// number taken from tokenize module
DEC_NUMBER: '[1-9]\d*[lL]?';
HEX_NUMBER: '0[xX][\da-fA-F]*[lL]?';
OCT_NUMBER: '0[0-7]*[lL]?';
FLOAT_NUMBER: '((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)';
IMAG_NUMBER: '(\d+[jJ]|((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)[jJ])';

//OPASSIGN: '\+=|-=|\*=|/=|/\/=|%=|\*\*=|&=|\|=|\^=|\<\<=|\>\>=';

STRING : 'u?r?("(?!"").*?(?<!\\)(\\\\)*?"|\'(?!\'\').*?(?<!\\)(\\\\)*?\')' ;
LONG_STRING : '(?s)u?r?(""".*?(?<!\\)(\\\\)*?"""|\'\'\'.*?(?<!\\)(\\\\)*?\'\'\')'
    (%newline)
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

NEWLINE: '(\r?\n[\t ]*)+'    // Don't count on the + to prevent multiple NLs. They can happen.
    (%newline)
    ;

WS: '[\t \f]+' (%ignore);
LINE_CONT: '\\[\t \f]*\r?\n' (%ignore) (%newline);
COMMENT: '\#[^\n]*'(%ignore);

NAME: '[a-zA-Z_][a-zA-Z_0-9]*(?!r?"|r?\')'  //"// Match names and not strings (r"...")
    (%unless
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
    )
    ;

INDENT: '<INDENT>';
DEDENT: '<DEDENT>';

%newline_char: '\n';    // default, can be omitted

###
from python2_indent_postlex import PythonIndentTracker
self.lexer_postproc = PythonIndentTracker

