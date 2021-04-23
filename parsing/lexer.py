from typing import *

class Lexer:
    class Util:
        @staticmethod
        def is_digit(character: str) -> bool:
            if character is None:
                return False

            return character.isdigit()

        @staticmethod
        def is_space(character: str) -> bool:
            if character is None:
                return False

            if len(character) != 1:
                return False

            return character in [' ', '\n', '\r', '\t']

        @staticmethod
        def is_letter(character: str) -> bool:
            if character is None:
                return False

            if len(character) != 1:
                return False

            return character.isalpha()

        @staticmethod
        def is_identifier_prefix(character: str) -> bool:
            if character is None:
                return False

            return Lexer.Util.is_letter(character) or character == '_'

        @staticmethod
        def is_identifier_body(character: str) -> bool:
            if character is None:
                return False

            return Lexer.Util.is_identifier_prefix(character) or Lexer.Util.is_digit(character)

        @staticmethod
        def is_operator(character: str) -> bool:
            if character is None:
                return False

            return character in ['+', '-', '*', '/', '<', '>', '~', '|', '?']

    class Token:
        Type = int

        ERROR = 1
        IDENTIFIER = 2
        LEFTPAREN = 3
        RIGHTPAREN = 4
        LEFTCURL = 5
        RIGHTCURL = 6
        LEFTBRACK = 7
        RIGHTBRACK = 8
        FLOAT = 9
        INT = 10
        DOT = 11
        COMMA = 12
        OPERATOR = 13
        HASHTAG = 14
        ADRESS = 15
        EQUAL = 16
        DOLLAR = 17
        SEMICOLON = 18
        COLON = 19
        AMPERSAND = 20
        EXLAMATION = 21
        SINGLEQUOTE = 22
        DOUBLEQUOTE = 23
        STRING = 24
        COMMENT = 25
        END = 26

        def __init__(self, type: int, start: int, length: int):
            self.type = type
            self.start = start
            self.length = length

        def __repr__(self):
            return 'type: {}, start: {}, length: {}'.format(self.type, self.start, self.length)

    def __init__(self, string: str):
        self.current = 0
        self.string = string

    def __repr__(self):
        return self.string[:self.current] + "->" + self.string[self.current:]

    def peek(self, offset: int = 0) -> Union[str, None]:
        index = self.current + offset

        if index >= len(self.string):
            return None

        return self.string[self.current + offset]

    def pop(self) -> str:
        self.current += 1

        return self.string[self.current - 1]

    def lex_char(self, type: int) -> Token:
        self.current += 1

        return Lexer.Token(type, self.current - 1, 1)

    def lex_end(self) -> Token:
        return Lexer.Token(Lexer.Token.END, self.current, 1)

    def lex_number(self):
        start = self.current

        self.pop()
        dot = False

        if self.peek() in ['-', '+']:
            self.pop()

        while Lexer.Util.is_digit(self.peek()) or self.peek() == '.':
            if self.peek() == '.':
                if dot:
                    return Lexer.Token(Lexer.Token.FLOAT, start, self.current - start)
                else:
                    dot = True

            self.pop()

        if dot:
            return Lexer.Token(Lexer.Token.FLOAT, start, self.current - start)

        return Lexer.Token(Lexer.Token.INT, start, self.current - start)

    def lex_identifier(self) -> Token:
        start = self.current

        self.pop()
        while Lexer.Util.is_identifier_body(self.peek()):
            self.pop()

        return Lexer.Token(Lexer.Token.IDENTIFIER, start, self.current - start)

    def lex_single_comment(self) -> Token:
        start = self.current

        while self.peek() not in ['\n', None]:
            self.pop()

        return Lexer.Token(Lexer.Token.COMMENT, start, self.current - start)

    def lex_multi_comment(self) -> Token:
        start = self.current

        while True:
            character = self.peek()
            if character is None:
                return Lexer.Token(Lexer.Token.COMMENT, start, self.current - start)
            elif character == '*':
                character = self.peek(1)
                if character is None:
                    self.pop()
                    return Lexer.Token(Lexer.Token.COMMENT, start, self.current - start - 1)
                elif character == '/':
                    self.pop()
                    self.pop()
                    return Lexer.Token(Lexer.Token.COMMENT, start, self.current - start - 2)
            else:
                self.pop()

    def lex_string(self, type: str) -> Token:
        start = self.current

        self.pop()
        while self.peek() != type:
            if self.peek() is None:
                return Lexer.Token(Lexer.Token.STRING, start + 1, self.current - start - 1)

            self.pop()

        self.pop()

        return Lexer.Token(Lexer.Token.STRING, start + 1, self.current - start - 2)

    def lex_operator(self) -> Token:
        start = self.current

        if self.peek() in ['-', '+'] and Lexer.Util.is_digit(self.peek(1)):
            return self.lex_number()

        self.pop()
        while Lexer.Util.is_operator(self.peek()):
            self.pop()

        return Lexer.Token(Lexer.Token.OPERATOR, start, self.current - start)

    def lex_operator_or_comment(self) -> Token:
        if self.peek() == '/':
            character = self.peek(1)
            if character is None:
                return self.lex_char(Lexer.Token.OPERATOR)
            elif character == '/':
                self.pop()
                self.pop()
                return self.lex_single_comment()
            elif character == '*':
                self.pop()
                self.pop()
                return self.lex_multi_comment()

        return self.lex_operator()

    def str(self, token: Token) -> str:
        return self.string[token.start: token.start + token.length]

    def reset(self):
        self.current = 0

    def next(self) -> Token:
        while Lexer.Util.is_space(self.peek()):
            self.pop()

        character = self.peek()

        if character is None:
            return self.lex_end()
        elif Lexer.Util.is_identifier_prefix(character):
            return self.lex_identifier()
        elif Lexer.Util.is_digit(character):
            return self.lex_number()
        elif Lexer.Util.is_operator(character):
            return self.lex_operator_or_comment()
        elif character == '(':
            return self.lex_char(Lexer.Token.LEFTPAREN)
        elif character == ')':
            return self.lex_char(Lexer.Token.RIGHTPAREN)
        elif character == '{':
            return self.lex_char(Lexer.Token.LEFTCURL)
        elif character == '}':
            return self.lex_char(Lexer.Token.RIGHTCURL)
        elif character == '[':
            return self.lex_char(Lexer.Token.LEFTBRACK)
        elif character == ']':
            return self.lex_char(Lexer.Token.RIGHTBRACK)
        elif character == '\'':
            return self.lex_char(Lexer.Token.SINGLEQUOTE)
        elif character == '"':
            return self.lex_string('"')
        elif character == '.':
            return self.lex_char(Lexer.Token.DOT)
        elif character == ',':
            return self.lex_char(Lexer.Token.COMMA)
        elif character == ';':
            return self.lex_char(Lexer.Token.SEMICOLON)
        elif character == '#':
            return self.lex_char(Lexer.Token.HASHTAG)
        elif character == '@':
            return self.lex_char(Lexer.Token.ADRESS)
        elif character == '=':
            return self.lex_char(Lexer.Token.EQUAL)
        elif character == '$':
            return self.lex_char(Lexer.Token.DOLLAR)
        elif character == ':':
            return self.lex_char(Lexer.Token.COLON)
        elif character == '&':
            return self.lex_char(Lexer.Token.AMPERSAND)
        elif character == '!':
            return self.lex_char(Lexer.Token.EXLAMATION)
        else:
            return self.lex_char(Lexer.Token.ERROR)

    @staticmethod
    def extract_constants(code) -> Tuple[List[Token], Dict[str, int]]:
        lexer = Lexer(code)

        counter: Dict[str, int] = dict()
        constants: List[Lexer.Token] = []

        token = lexer.next()
        while token.type != Lexer.Token.END:
            if token.type == Lexer.Token.IDENTIFIER or token.type == Lexer.Token.INT or token.type == Lexer.Token.FLOAT:
                value = lexer.str(token)

                constants.append(token)
                if value in counter.keys():
                    counter[value] += 1
                else:
                    counter[value] = 1

            token = lexer.next()

        return constants, counter