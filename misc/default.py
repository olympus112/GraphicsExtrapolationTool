from parsing.lexer import Lexer

# Default values
tolerance = 0.1
confidence = 1.0

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
    Lexer.Token.ADRESS: '@'
}

# Input DSL
primitive_group_begin = Lexer.Token.LEFTCURL
primitive_group_end = Lexer.Token.RIGHTCURL
primitive_begin = Lexer.Token.LEFTPAREN
primitive_end = Lexer.Token.RIGHTPAREN
primitive_separator = Lexer.Token.DOT

# Output DSL
reference = Lexer.Token.HASHTAG
parent = Lexer.Token.ADRESS
group_pattern_parent_begin = Lexer.Token.LEFTPAREN
group_pattern_begin = Lexer.Token.LEFTCURL
group_pattern_end = Lexer.Token.RIGHTCURL
group_pattern_parent_end = Lexer.Token.RIGHTPAREN
instance_pattern_begin = Lexer.Token.LEFTBRACK
instance_pattern_end = Lexer.Token.RIGHTBRACK
parameter_pattern_begin = Lexer.Token.LEFTBRACK
parameter_pattern_end = Lexer.Token.RIGHTBRACK

# Shared
value_separator = Lexer.Token.COMMA
