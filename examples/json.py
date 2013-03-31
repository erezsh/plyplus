from plyplus import Grammar, STransformer

json_grammar = Grammar(r"""
@start: value ;

?value : object | array | string | number | boolean | null ;

string : '".*?(?<!\\)(\\\\)*?"' ;
number : '-?([1-9]\d*|\d)(\.\d+)?([eE][+-]?\d+)?' ;
pair : string ':' value ;
object : '\{' ( pair ( ',' pair )* )? '\}' ;
array : '\[' ( value ( ',' value ) * )? '\]' ;
boolean : 'true' | 'false' ;
null : 'null' ;

WS: '[ \t\n]+' (%ignore) (%newline);
""")

class JSON_Transformer(STransformer):
    """Transforms JSON AST into Python native objects."""
    number  = lambda self, node: float(node.tail[0])
    string  = lambda self, node: node.tail[0][1:-1]
    boolean = lambda self, node: True if node.tail[0] == 'true' else False
    null    = lambda self, node: None
    array   = lambda self, node: node.tail
    pair    = lambda self, node: { node.tail[0] : node.tail[1] }
    def object(self, node):
        result = {}
        for i in node.tail:
            result.update( i )
        return result

def json_parse(json_string):
    """Parses a JSON string into native Python objects."""
    return JSON_Transformer().transform(json_grammar.parse(json_string))

def main():
    json = '''
        {
            "empty_object" : {},
            "empty_array"  : [],
            "booleans"     : { "YES" : true, "NO" : false },
            "numbers"      : [ 0, 1, -2, 3.3, 4.4e5, 6.6e-7 ],
            "strings"      : [ "This", [ "And" , "That" ] ],
            "nothing"      : null
        }
    '''
    print '### JSON Parser using PlyPlus'
    print '  # JSON allows empty arrays and objects.'
    print '  # This requires that empty AST sub-trees be kept in the AST tree.'
    print '  # If you pass the kwarg "keep_empty_trees=False" to the'
    print '  # Grammar() constructor, empty arrays and objects will be removed'
    print '  # and the JSON_Transformer class will fail.'
    print
    print '### Input'
    print json
    print '### Output'
    result = json_parse(json)
    import pprint
    pprint.pprint(result)

if __name__ == '__main__':
    main()
