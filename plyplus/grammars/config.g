start: (section|NEWLINE)+;
section: SECTION NEWLINE (NEWLINE|option)*;
option: OPTION NEWLINE;

SECTION: '\[[^\[\]\n;]+]'
{
    start: '\[' name ']';
    name: '[^\[\]\n;]+';
    WS: '[\t \f]+' (%ignore);
};
OPTION: '[^=:\n;]+[=:][^\n]*'
{
    start: name VALUE?;
    name: '[^=:\n;]+';
    VALUE: '[:=][^\n;]*'
    {
        start: '[:=]' value?;
        value: '[^:=\n;][^\n;]*';
    };
    WS: '[\t \f]+' (%ignore);
};

NEWLINE: '(\r?\n)+' (%newline) ;

WS: '[\t \f]+' (%ignore);
COMMENT: '[\#;][^\n]*'(%ignore);

