from misc.util import Tolerance
from parsing.lexer import Lexer

# Default values
tolerance = Tolerance(0, 0.1)
confidence = 1.0
r = 0.4
g = 0.6
b = 0.4
a = 0.8

# Tokens
tokens = {
    Lexer.Token.LEFTCURL: '{',
    Lexer.Token.RIGHTCURL: '}',
    Lexer.Token.LEFTBRACK: '[',
    Lexer.Token.RIGHTBRACK: ']',
    Lexer.Token.LEFTPAREN: '(',
    Lexer.Token.RIGHTPAREN: ')',
    Lexer.Token.COMMA: ',',
    Lexer.Token.DOT: '.',
    Lexer.Token.HASHTAG: '#',
    Lexer.Token.ADRESS: '@',
    Lexer.Token.DOLLAR: '$',
    Lexer.Token.EQUAL: '=',
    Lexer.Token.COLON: ':',
    Lexer.Token.AMPERSAND: '&'
}

# Input DSL
primitive_group_begin = Lexer.Token.LEFTCURL
primitive_group_end = Lexer.Token.RIGHTCURL
primitive_begin = Lexer.Token.LEFTPAREN
primitive_end = Lexer.Token.RIGHTPAREN
primitive_separator = Lexer.Token.DOT

# Output DSL
name = "name"
none = "none"
sizes = Lexer.Token.HASHTAG
arities = Lexer.Token.ADRESS
identifier = Lexer.Token.AMPERSAND
selector = Lexer.Token.COLON
group_pattern_parent_begin = Lexer.Token.LEFTPAREN
group_pattern_children_begin = Lexer.Token.LEFTCURL
group_pattern_children_end = Lexer.Token.RIGHTCURL
group_pattern_parent_end = Lexer.Token.RIGHTPAREN
primitive_pattern_begin = Lexer.Token.LEFTBRACK
primitive_pattern_end = Lexer.Token.RIGHTBRACK
parameter_pattern_begin = Lexer.Token.LEFTPAREN
parameter_pattern_end = Lexer.Token.RIGHTPAREN

# Shared
variable = Lexer.Token.DOLLAR
assigment = Lexer.Token.EQUAL
value_separator = Lexer.Token.COMMA