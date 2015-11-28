%%
expr : add | subtract | times | divide | NUMBER ;
add : expr PLUS expr ;
subtract : expr MINUS expr ;
times : expr TIMES expr ;
divide : expr DIVIDE expr ;
%%
