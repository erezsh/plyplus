start: (section|NEWLINE)@+;
section: SECTION NEWLINE (NEWLINE|option)@*;
option: OPTION NEWLINE;

SECTION: '\[[\w\s]+]'
{
    start: '\[' name ']';
    name: '\w([\w\s]*\w)?';
    WS: '[\t \f]+' (%ignore);
};
OPTION: '[A-Za-z]\w*\s*[=:][^\n]+'
{
    start: name VALUE;
    name: '[A-Za-z]\w*';
    VALUE: '[:=][^\n]*'
    {
        start: '[:=]' value;
        value: '[^:=\n][^\n]*';
    };
    WS: '[\t \f]+' (%ignore);
};

NEWLINE: '(\r?\n)+' (%newline) ;

WS: '[\t \f]+' (%ignore);
COMMENT: '[\#;][^\n]*'(%ignore);

