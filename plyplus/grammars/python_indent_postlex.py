from copy import copy

NL_type = 'NEWLINE'
INDENT_type = 'INDENT'
DEDENT_type = 'DEDENT'
PAREN_OPENERS = 'LPAR', 'LBRACE', 'LSQB'
PAREN_CLOSERS = 'RPAR', 'RBRACE', 'RSQB'


class Tok():
    def __init__(self, type=None, value=None, lexer=None):
        self.type = type
        self.value = value
        self.lineno = None
        self.lexpos = None
        self.lexer = lexer

class PythonIndentTracker:
    def __init__(self, lexer, tab_len=4):
        self.lexer = lexer

        self.tab_len = tab_len
        self.tab_str = ' '*tab_len
        self.current_state = lexer.current_state
        self.begin = lexer.begin

    def input(self, s):
        self.token_queue = []
        self.indent_level = [0]
        self.ignore_newline = False
        self.paren_level = 0
        return self.lexer.input(s)

    def token(self):
        # If tokens are waiting to be pushed, push them --
        if len(self.token_queue):
            return self.token_queue.pop()

        # Get original token
        tok = self.lexer.token()
        #print type(tok)

        if tok and tok.type == NL_type:
            # -- New line --
            ignore_nl = self.ignore_newline # save now, may change on self.token()
            while tok and tok.type == NL_type:  # treat successive NLs as one (the last of them)
                nl_tok = tok
                tok = self.token()

            if ignore_nl:  # ignore = don't indent, and skip new line too
                return tok

            self.token_queue.append(tok)
            return self.handle_newline(nl_tok)

        # -- End of input --
        if tok is None:
            #print self.indent_level
            if len(self.indent_level) > 1:
                while len(self.indent_level) > 1:
                    self.indent_level.pop()

                    new_token = Tok(lexer=self.lexer)
                    new_token.type = DEDENT_type
                    self.token_queue.append(new_token)
                return self.token() # assume it always returns None

            assert self.indent_level == [0], self.indent_level

            self.token_queue.append( None )
            #eof = Tok(lexer=self.lexer)
            #eof.type = 'EOF'
            #eof.value = '<EOF>'
            #return eof
            return None

        # -- Regular token --
        if tok.type != NL_type:
            #self.ignore_indent = (tok.type != 'COLON')
            if tok.type in PAREN_OPENERS:
                self.paren_level += 1
            elif tok.type in PAREN_CLOSERS:
                self.paren_level -= 1

            assert self.paren_level >= 0
            self.ignore_newline = (self.paren_level > 0)

            return tok

        assert False

    def handle_newline(self, tok):  # Do (most) indentation
        text = tok.value
        indent_str = text.rsplit('\n', 1)[1] # Tabs and spaces
        text = text[:text.rfind('\n') + 1]    # Without the indent

        #print tok.start, tok.stop, `tok.text`
        #indent = len(indent_str.replace('\t', self.tab_str))
        indent = indent_str.count(' ') + indent_str.count('\t') * self.tab_len

        # -- Indent --
        if indent > self.indent_level[-1]:
            #print "INDENT", indent
            self.indent_level.append(indent)

            new_token = copy(tok)
            new_token.type = INDENT_type
            new_token.value = indent_str
            self.token_queue.append(new_token)
        else:
            while indent < self.indent_level[-1]:
                #print "DEDENT", indent
                self.indent_level.pop()

                new_token = copy(tok)
                new_token.type = DEDENT_type
                new_token.value = indent_str
                self.token_queue.append(new_token)

            assert indent == self.indent_level[-1], '%s != %s' % (indent, self.indent_level[-1])


        return tok



def test():
    class Tok:
        def __init__(self, type, value=''):
            self.type = type
            self.value = value
    class A:
        def __init__(self):
            self.l = [
                    Tok('STMT'), Tok('NL', '\n'
                    ), Tok('STMT'), Tok('NL', '\n'
                    '\t'), Tok('STMT'), Tok('NL', '\n'
                    '\t'), Tok('LBRACK'), Tok('NL', '\n'
                    '\t\t'), Tok('STMT'), Tok('NL', '\n'
                    '\t\t\t'), Tok('RBRACK'), Tok('NL', '\n'
                    ), Tok('STMT'), Tok('NL', '\n'
                    '\t\t'), Tok('STMT'), Tok('NL', '\n'
                    '\t\t'), Tok('STMT'), Tok('NL', '\n'
                    '\t\t\t'),
                ][::-1]
        def input(self, t):
            return
        def token(self):
            if self.l:
                return self.l.pop()

    expected_result = [
            'STMT', 'NL',
            'STMT', 'NL',
            'INDENT', 'STMT', 'NL',
            'LBRACK', 'STMT', 'RBRACK', 'NL',
            'DEDENT', 'STMT', 'NL',
            'INDENT', 'STMT', 'NL',
            'STMT', 'NL',
            'INDENT', 'DEDENT', 'DEDENT'
            ]
    a = PythonIndentTracker(A())
    toks = []
    tok = a.token()
    while tok:
        print(tok.type)
        toks.append(tok.type)
        tok = a.token()

    print(['FAILED!', 'OK!'][toks == expected_result])



if __name__ == '__main__':
    test()
