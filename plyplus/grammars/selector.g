start: selector;
selector: selector_op? elem;
selector_op: selector operator?;
operator: '>' | '\+' | '~';

elem: yield? (elem_head | elem_class | elem_regexp | LBRACE elem_tree_param RBRACE | elem_any | LPAR selector_list RPAR) modifier?;

modifier: modifier_name (LPAR index RPAR)?;

modifier_name: MODIFIER;
index: INDEX;
yield: '=';

elem_head: LOWER_NAME;
elem_class: CLASS;
elem_regexp: REGEXP;
elem_tree_param: LOWER_NAME;
elem_any: '\*';
selector_list: selector (',' selector)*;

CLASS: '\.' LOWER_NAME;
MODIFIER: ':[a-z][a-z-]*';
LOWER_NAME: '[a-z_][a-z_0-9]*';

INDEX: '\d+';
LPAR:  '\(';
RPAR: '\)';
LBRACE: '{';
RBRACE: '}';

REGEXP: '/.*?[^\\]/';

WS: '[ \t\f]+' (%ignore);

