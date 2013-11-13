start: (NEWLINE|stmt)+;
//module_header: string NEWLINE;

//
//     STATEMENTS
//

  @stmt : simple_stmt | compound_stmt ;

  @simple_stmt : small_stmt (SEMI small_stmt)+? SEMI? (NEWLINE|EOF);

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

  // testlist is too permissive, maybe even unecessarily slow
  assign_stmt : testlist (EQUAL (yield_expr|testlist))+ ;
  augassign_stmt : testlist augassign_symbol (testlist|yield_expr) ;

  assert_stmt : ASSERT test (COMMA test)?;
  del_stmt : DEL exprlist;

  global_stmt : GLOBAL name (COMMA name)*;

  exec_stmt : EXEC expr (IN test (COMMA test)?)? ;

  print_stmt : PRINT (print_into COMMA)? test (COMMA test)+? COMMA?
    | PRINT print_into?
    ;
  print_into : RIGHTSHIFT test;

  import_stmt :
      IMPORT dotted_as_name (COMMA dotted_as_name)*
    | FROM (dotted_name|DOT+ dotted_name?)
      IMPORT (import_all|import_as_names|LPAR import_as_names RPAR)
    ;
  import_all: STAR;

  dotted_as_name : dotted_name (AS name)?  ;

  import_as_names : import_as_name (COMMA import_as_name)* COMMA?  ;
  import_as_name : name (AS name)?  ;

  dotted_name : name (DOT name)* ;


// definitions
  funcdef : decorators? DEF name parameters COLON suite ;
  classdef : CLASS name (LPAR testlist? RPAR)? COLON suite ;

// compound flow statements
  while_stmt : WHILE test COLON suite else_stmt? ;
  with_stmt : WITH test (AS expr)? (COMMA test (AS expr)?)* COLON suite;    // Too permissive
  if_stmt : IF test COLON suite (ELIF test COLON suite)* else_stmt? ;
  for_stmt : FOR exprlist IN testlist COLON suite else_stmt? ;
  try_stmt : TRY COLON suite (except_stmt+ else_stmt?  finally_stmt? | finally_stmt );
  except_stmt : (EXCEPT (test ((AS|COMMA) test)?)? COLON suite);
  else_stmt : ELSE COLON suite;
  finally_stmt : FINALLY COLON suite;

// simple flow statements
  @flow_stmt : break_stmt
    | continue_stmt
    | return_stmt
    | raise_stmt
    | yield_stmt
    | pass_stmt
    ;

  break_stmt : BREAK;
  continue_stmt : CONTINUE;
  pass_stmt : PASS;
  raise_stmt : RAISE (test (COMMA test (COMMA test)?)?)? ;
  return_stmt : RETURN testlist?;
  yield_stmt : yield_expr ;

// suites (auxiliary)

  suite : simple_stmt | NEWLINE INDENT stmt+ DEDENT ;

// decorators

//  decorator : AT dotted_name NEWLINE  // Strict, correct version
//    | AT dotted_name LPAR RPAR NEWLINE
//    | AT dotted_name LPAR arglist RPAR NEWLINE
//    ;

// Intentionally more flexible than python syntax
decorator : AT (attrget|funccall|name) NEWLINE;
decorators : decorator+ ;

//
//     EXPRESSIONS
//

  ?or_test : and_test (OR and_test)* ;
  ?and_test : not_test (AND not_test)* ;
  @not_test : not_expr | comparison ;
  not_expr : NOT not_test;
  ?comparison : expr (compare_symbol expr)*  ;
  ?expr : xor_expr (VBAR xor_expr)* ;
  ?xor_expr : and_expr (CIRCUMFLEX and_expr)* ;
  ?and_expr : shift_expr (AMPER shift_expr)* ;
  ?shift_expr : arith_expr (shift_symbol arith_expr)* ;
  ?arith_expr : term (add_symbol term)* ;


  arglist : (arg COMMA)+?
          ( arg COMMA?
          | args (COMMA kwargs)?
          | kwargs
          ) ;

// XXX Overly permissive? (maybe gen_for belongs in arglist)
  arg : test (|gen_for|EQUAL test) ;

  exprlist : expr (COMMA expr)* COMMA? ;

  ?factor : add_symbol factor
    | binary_not
    | power
    | molecule
    ;

  binary_not: TILDE factor;

  fpdef : name
    | LPAR fpdef (COMMA fpdef)* COMMA? RPAR
    ;

  lambdef : LAMBDA varargslist? COLON test ;

  old_lambdef : LAMBDA varargslist? COLON stunted_test ;
  stunted_test : or_test | old_lambdef ;

  parameters : LPAR varargslist? RPAR ;

  ?power : molecule (DOUBLESTAR factor)? ;

  @molecule : atom
//    | atom molecule_star
    | funccall
    | itemget
    | attrget
    ;

  funccall : molecule LPAR arglist? RPAR ;

  itemget : molecule LSQB subscriptlist RSQB;

  attrget : molecule DOT name;

  subscript : DOT DOT DOT
    | test
    | test? COLON (sliceop|test sliceop?|)
    ;
  sliceop : COLON test?  ;

  subscriptlist : subscript (COMMA subscript)* COMMA? ;

  ?term : factor (term_symbol factor)* ;

  ?test : or_test
    | or_test IF or_test ELSE test
    | lambdef
    ;

  ?testlist : test testlist_star? COMMA? ;
  testlist1 : test testlist_star? ;
  @testlist_star : testlist_star? COMMA test ;

  varargslist : vararg (COMMA vararg)+?
            ((COMMA args_decl)? (COMMA kwargs_decl)?
            |COMMA
            )
    | args_decl (COMMA kwargs_decl)?
    | kwargs_decl
    ;

vararg : fpdef (EQUAL test)? ;

yield_expr : YIELD testlist? ;

// There are small silly differences between list comprehensions and generators.
// Additionally, each of them has its own subtlities,
// Most of which don't really make sense.
// >>> [x for x in 1,2,]
// [1, 2]
// >>> [x for x in 1,]
// SyntaxError: invalid syntax
// >>> (x for x in 1,2)
// SyntaxError: invalid syntax
// >>> [x for x in 1,2]
// [1, 2]

tuple : LPAR tuplemaker? RPAR ;
@tuplemaker : test gen_for
            | test (COMMA | (COMMA test)+ COMMA? ) ;
gen_for : FOR exprlist IN or_test gen_iter?  ;
gen_if : IF stunted_test gen_iter?  ;
gen_iter : gen_for | gen_if ;
 
list : LSQB listmaker? RSQB ;
@listmaker : test (list_for | (COMMA test)+? COMMA?) ;
list_for : FOR exprlist IN stunted_testlist list_iter?  ;
list_if : IF stunted_test list_iter?  ;
list_iter : list_for | list_if ;
stunted_testlist : stunted_test ((COMMA stunted_test)+ COMMA?)? ;

dict : LBRACE dictmaker? RBRACE ;
@dictmaker : dict_item (dict_for | (COMMA dict_item)+? COMMA?) ;
dict_item: test COLON test;
dict_for : FOR exprlist IN stunted_testlist list_iter?  ;

set : LBRACE listmaker RBRACE;

repr : BACKQUOTE testlist1 BACKQUOTE;

@atom : tuple
    | list
    | dict
    | set
    | LPAR (yield_expr|test) RPAR
    | repr
    | name
    | number
    | string+
    ;

args_decl: STAR name;
kwargs_decl: DOUBLESTAR name;
args: STAR test;
kwargs: DOUBLESTAR test;

// Token groups

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

term_symbol : STAR|SLASH|PERCENT|DOUBLESLASH ;
shift_symbol: LEFTSHIFT|RIGHTSHIFT;
add_symbol: PLUS|MINUS;

name: NAME;
number: DEC_NUMBER | HEX_NUMBER | OCT_NUMBER | FLOAT_NUMBER | IMAG_NUMBER;
string: STRING|LONG_STRING;

// Tokens!
%fragment I: '(?i)';    // Case Insensitive
%fragment S: '(?s)';    // Dot Matches Newline


// number taken from tokenize module
%fragment LONG_POSTFIX: I 'l?';
%fragment EXP_POSTFIX: I 'e[-+]?\d+';

DEC_NUMBER: I '[1-9]\d*'   LONG_POSTFIX;
HEX_NUMBER: I '0x[\da-f]*' LONG_POSTFIX;
OCT_NUMBER: I '0o?[0-7]*'  LONG_POSTFIX;
FLOAT_NUMBER: I '(\d+\.\d*|\.\d+)(' EXP_POSTFIX ')?'
                '|\d+' EXP_POSTFIX;
IMAG_NUMBER: I '\d+j|(' FLOAT_NUMBER ')j';

%fragment STRING_PREFIX: '(u|b|)r?';
%fragment STRING_INTERNAL: '.*?(?<!\\)(\\\\)*?' ;
%fragment QUOTE: '\'';
%fragment DBLQUOTE: '"';
%fragment QUOTE3: '\'\'\'';
%fragment DBLQUOTE3: '"""';

STRING : STRING_PREFIX
            '(' DBLQUOTE '(?!"")' STRING_INTERNAL DBLQUOTE
            '|' QUOTE '(?!\'\')' STRING_INTERNAL QUOTE
            ')' ;
LONG_STRING : S STRING_PREFIX
            '(' DBLQUOTE3 STRING_INTERNAL DBLQUOTE3
            '|' QUOTE3 STRING_INTERNAL QUOTE3
            ')' (%newline) ;

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
    (%newline)
    ;

WS: '[\t \f]+' (%ignore);
LINE_CONT: '\\[\t \f]*\r?\n' (%ignore) (%newline);
COMMENT: '\#[^\n]*'(%ignore);

NAME: I '[a-z_]\w*(?!r?"|r?\')'  // Match names and not strings (r"...")
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

        // Definitions
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
EOF: '<EOF>';

###
from plyplus.grammars.python_indent_postlex import PythonIndentTracker
self.lexer_postproc = PythonIndentTracker

