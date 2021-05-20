from misc.util import Tolerance
from parsing.lexer import Lexer

# Default values
tolerance = Tolerance(0.1, 0)
confidence = 1.0
r = 0.4
g = 0.6
b = 0.4
a = 1.0

dark = 0
light = 1
color = dark
colors = [
    {"background": [0.2, 0.2, 0.2, 1.0],
     "border": [1.0, 1.0, 1.0, 1.0],
     "cursor": [0.8, 0.8, 0.8, 1.0],
     "grid": [0.8, 0.8, 0.8, 0.2],
     "origin": [1.0, 1.0, 1.0, 1.0],
     "arrow": [0.9, 0.9, 0.9, 1.0]},
    {"background": [0.945, 0.945, 0.945, 1.0],
     "border": [0.0, 0.0, 0.0, 1.0],
     "cursor": [0.2, 0.2, 0.2, 1.0],
     "grid": [0.2, 0.2, 0.2, 0.2],
     "origin": [0.0, 0.0, 0.0, 1.0],
     "arrow": [0.1, 0.1, 0.1, 1.0]}
]

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