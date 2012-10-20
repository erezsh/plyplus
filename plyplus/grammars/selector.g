start: selector;
selector: selector_op? elem;
selector_op: selector operator?;
operator: '>' | '\+' | '~';

elem: yield? (elem_head | elem_class | elem_regexp | elem_any | LPAR selector_list RPAR) modifier?;

modifier: modifier_name (LPAR index RPAR)?;

modifier_name: MODIFIER;
index: INDEX;
yield: '=';

elem_head: HEAD;
elem_class: CLASS;
elem_regexp: REGEXP;
elem_any: '\*';
selector_list: selector (',' selector)*;

HEAD: '[a-z_][a-z_0-9]*';
CLASS: '\.[a-z_][a-z_0-9]*';
MODIFIER: ':[a-z][a-z-]*';

INDEX: '\\d+';
LPAR:  '\(';
RPAR: '\)';

REGEXP: '/.*?[^\\]/';

WS: '[ \t\f]+' (%ignore);

###
from selector import STreeSelector
self.STree = STreeSelector
