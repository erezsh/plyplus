
start: module_header? stmts;
@stmts: stmt*; // A bit permissive, but will help with erroneous code */
@stmt: simple_stmt_list | block_stmt | empty_stmt ;
@simple_stmt_list: simple_stmt_list2 NL;
@simple_stmt_list2: simple_stmt ';'? | simple_stmt ';' simple_stmt_list2;
@simple_stmt: print|flow|import|global|exec|assert|expr_list|opassign|del|assign;
@block_stmt: if | while | for | try | with | funcdef | classdef;

empty_stmt: NL | INDENT NL? DEDENT; // should handle in lexer level?


module_header: string NL;

// this import is a bit more permissive than the official one
import  : IMPORT (module_name (AS NAME)? ) (',' module_name (AS NAME)? )*  // import is weird!
        | FROM relative_module_name IMPORT (import_as_names|LPAREN import_as_names RPAREN|'\*')
        ;
module_name : NAME (DOT NAME)*;
relative_module_name : module_name | (DOT DOT* module_name?) ;

import_as_names :  import_as_name ','? | import_as_name ',' import_as_names;
import_as_name: NAME (AS NAME)?;


name_list : NAME COMMA?
          | NAME COMMA name_list
          | LPAREN name_list RPAREN
          ;
var_list  : var ','?
          | var ',' var_list
          | LPAREN var_list RPAREN
          | LBRACK var_list RBRACK
          ;

global: GLOBAL NAME (',' NAME)*;
exec:   EXEC expr (IN expr (',' expr)?)?;
assert: ASSERT expr (',' expr)?;
del:    DEL var_list;

// A lot more permissive than Python's assign (in fact, allows wrong code)
// But this is for a very good cause, and should not cause confusion with other syntax.
// Should check the left-values are legal lvalues, post-processing
assign: expr_list ASSIGN expr_list
      | expr_list ASSIGN assign
      ;


opassign: var OPASSIGN expr ;


print: PRINT (expr_list)?
     | PRINT SHR expr (',' expr_list)? ;

@flow: return | yield | raise| pass | break | continue;
pass    : PASS;
break    : BREAK;
continue    : CONTINUE;
return: RETURN expr_list?;
yield: (expr_list ASSIGN)? (yield_expr|LPAREN yield_expr RPAREN);
yield_expr: YIELD expr_list?;

raise: RAISE expr? ((',' expr)? ',' expr)?
     ;


@code_block: INDENT stmts DEDENT;
suite: NL code_block | simple_stmt_list;

if  : IF expr ':' suite
      ( ELIF expr ':' suite )*
      ( ELSE ':' suite )?
    ;


while: WHILE expr ':' suite (ELSE ':' suite)?;
for: FOR var_list IN expr_list ':' suite (ELSE ':' suite)?;    // name_list


try: try1 | try2;
try1: TRY ':' suite
           (EXCEPT (expr (',' NAME)?)? ':' suite )*
           (ELSE ':' suite )?
           (FINALLY ':' suite )?
           ;
try2: TRY ':' suite
            FINALLY ':' suite
            ;

with: WITH expr (AS var_list)? ':' suite ;


funcdef: decorators? DEF NAME LPAREN param_list RPAREN ':' suite ;
decorators: ('@' expr NL)+ ;


param_list: simple_param_list
          | (def_param ',')+ simple_param_list
          ;

@simple_param_list: def_param ','?
               | MUL NAME (',' POW NAME)?
               | POW NAME
               |
               ;


def_param: (NAME | LPAREN name_list RPAREN) ('=' expr)? ;

classdef: CLASS NAME (LPAREN expr_list? RPAREN)? ':' suite ; // <=> tuple?



@expr : bin_expr
      | un_expr
      | funccall
      | var
      | LPAREN expr RPAREN
      | value
//      | implicit_tuple
      | inline_if
      | lambda
      ;

// XXX expr (',' expr)* ','?   - - not working, check why!
expr_list: expr ','?
         | expr ',' expr_list
         ;

var: NAME 
   | attrget
   | itemget
   ;


lambda: LAMBDA param_list? ':' expr ;


funccall: expr LPAREN (arg_list|comprehension) RPAREN ;
// A bit more permissive than Python
arg_list: simple_arg_list
       | arg ',' arg_list
       | expr ',' arg_list
       ;

@simple_arg_list: arg ','?
               | expr ','?
               | MUL expr (',' POW expr)?
               | POW expr
               |
               ;

arg: NAME '=' expr;

// a bit hacky (expr|subscriptlist), but seems to work?
itemget: expr LBRACK (expr|subscriptlist) RBRACK ;
subscriptlist: subscript ','?
             | subscript ',' subscriptlist
             ;
subscript: ELLIPSIS | expr | slice;
slice: subscriptlist? ':' subscriptlist? (':' subscriptlist?)?;


attrget: expr DOT NAME;



un_expr: '-' expr
        | '\+' expr
        | '\~' expr
        | NOT expr;

#bin_expr: expr '\+' expr
        | expr '-' expr
        | expr '\*' expr
        | expr POW expr
        | expr '/' expr
        | expr DBLSLASH expr
        | expr '&' expr
        | expr '\|' expr
        | expr '\^' expr
        | expr '>' expr
        | expr '<' expr
        | expr '==' expr
        | expr '!=' expr
        | expr '<>' expr
        | expr '<=' expr
        | expr '>=' expr
        | expr '%' expr
        | expr SHL expr
        | expr SHR expr
        | expr AND expr
        | expr OR expr
        | expr NOT? IN expr
        | expr IS NOT? expr
        ;

value: number
     | string
     | list
     | tuple
     | dict
     | set
     | repr_expr
     ;

number: DEC_NUMBER | HEX_NUMBER | OCT_NUMBER | FLOAT_NUMBER | IMAG_NUMBER;
list : LBRACK (list_inner|comprehension)? RBRACK ;
tuple: LPAREN (list_inner|comprehension)? RPAREN ;
list_inner	: expr | expr COMMA (expr (COMMA)? )* ;
set  : LCURLY list_inner RCURLY ;
dict : LCURLY dict_inner RCURLY ;
dict_inner  : (expr ':' expr (COMMA)? )* ;
repr_expr: '`' expr_list '`';



comprehension: expr comprehension_for;
comprehension_for: FOR var_list IN safe_expr_list comprehension_re?;
comprehension_if: IF safe_expr comprehension_re?;
comprehension_re: comprehension_for | comprehension_if;

inline_if: expr IF expr ELSE expr;

safe_expr_list: safe_expr ','?
              | safe_expr ',' safe_expr_list
              ;
safe_expr: bin_expr
         | un_expr
         | funccall
         | var
         | LPAREN safe_expr RPAREN
         | value
         | lambda   // XXX old lambda
         ;

string: (STRING|LONG_STRING) string? ;


// Tokens!

// number taken from tokenize module
DEC_NUMBER: '[1-9]\d*[lL]?';
HEX_NUMBER: '0[xX][\da-fA-F]*[lL]?';
OCT_NUMBER: '0[0-7]*[lL]?';
FLOAT_NUMBER: '((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)';
IMAG_NUMBER: '(\d+[jJ]|((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)[jJ])';


OPASSIGN: '\+=|-=|\*=|/=|/\/=|%=|\*\*=|&=|\|=|\^=|\<\<=|\>\>=';

STRING : 'u?r?("(?!"").*?(?<!\\)(\\\\)*?"|\'(?!\'\').*?(?<!\\)(\\\\)*?\')' ;
LONG_STRING : '(?s)u?r?(""".*?(?<!\\)(\\\\)*?"""|\'\'\'.*?(?<!\\)(\\\\)*?\'\'\')'
    (%newline)
    ;


LPAREN: '\(';
RPAREN: '\)';
LBRACK: '\[';
RBRACK: '\]';
LCURLY: '\{';
RCURLY: '\}';
COLON: ':';
SEMICOLON: ';';
VBAR: '\|';
AT: '@';
COMMA: ',';
ASSIGN: '=';
LTE: '<=';
MOD: '%';
DOT: '\.';
DIV: '/';
MUL: '\*';
POW: '\*\*';
DBLSLASH: '/\/';
SHL: '\<\<';
SHR: '\>\>';
ELLIPSIS: '(?<=(\[|,))\.\.\.';


NL: '(\r?\n[\t ]*)+'    // Don't count on the + to prevent multiple NLs. They can happen.
    (%newline)
    ;

WS: '[\t \f]+' (%ignore);
LINE_CONT: '\\[\t \f]*\r?\n' (%ignore) (%newline);

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


PLUS: '\+';
MINUS: '-';
INDENT: '<INDENT>';
DEDENT: '<DEDENT>';

%newline_char: '\n';

COMMENT: '\#[^\n]*' (%ignore);

###
from grammars.python_indent_postlex import PythonIndentTracker 
self.lexer_postproc = PythonIndentTracker

