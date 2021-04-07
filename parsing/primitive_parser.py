from typing import Union, Sequence

from gui.primitives import *
from parsing.primitive_lexer import Lexer

class Parser:
    @staticmethod
    def create_primitive(name: str, arity: int, parameters: [Union[str, float, int]]):
        for primitive in [Line, Rect, Circle, Vector]:
            if name == primitive.static_name():
                if arity not in primitive.static_arity():
                    return None
                return primitive(arity, *parameters)

        return Primitive(name, arity, *parameters)

    @staticmethod
    def parse_primitive(lexer: Lexer, token: Lexer.Token) -> Union[Primitive, None]:
        name = lexer.str(token)
        if lexer.next().type != Lexer.Token.LEFTPAREN:
            return None

        parameters: [Union[str, float, int]] = []
        current = lexer.next()
        types = { Lexer.Token.STRING, Lexer.Token.INT, Lexer.Token.FLOAT, Lexer.Token.IDENTIFIER, Lexer.Token.RIGHTPAREN }

        while True:
            if current.type not in types:
                return None

            if current.type == Lexer.Token.IDENTIFIER:
                parameters.append(lexer.str(current))

                types = { Lexer.Token.COMMA, Lexer.Token.RIGHTPAREN }
            elif current.type == Lexer.Token.FLOAT:
                parameters.append(float(lexer.str(current)))

                types = { Lexer.Token.COMMA, Lexer.Token.RIGHTPAREN }
            elif current.type == Lexer.Token.INT:
                parameters.append(int(lexer.str(current)))

                types = { Lexer.Token.COMMA, Lexer.Token.RIGHTPAREN }
            elif current.type == Lexer.Token.STRING:
                string = lexer.str(current)
                if len(string) == 0:
                    return None

                parameters.append(string)

                types = { Lexer.Token.COMMA, Lexer.Token.RIGHTPAREN }
            elif current.type == Lexer.Token.COMMA:
                types = { Lexer.Token.FLOAT, Lexer.Token.INT, Lexer.Token.IDENTIFIER, Lexer.Token.STRING }
            elif current.type == Lexer.Token.RIGHTPAREN:
                if lexer.next().type not in [Lexer.Token.DOT, Lexer.Token.SEMICOLON]:
                    return None

                break
            else:
                return None

            current = lexer.next()

        arity = len(parameters)

        return Parser.create_primitive(name, arity, parameters)

    @staticmethod
    def parse(code: str) -> Group:
        lexer = Lexer(code)
        primitives = Group()
        stack = [primitives]

        parse_next_master = False
        current = lexer.next()
        while current.type != Lexer.Token.END:
            if current.type == Lexer.Token.OPERATOR and lexer.str(current) == "!":
                parse_next_master = True
            elif current.type == Lexer.Token.IDENTIFIER:
                primitive = Parser.parse_primitive(lexer, current)
                if primitive is not None:
                    stack[-1].append(primitive)
                    if parse_next_master:
                        stack[-1].set_master(primitive)
                        parse_next_master = False
            elif current.type == Lexer.Token.LEFTCURL:
                stack.append(Group())
            elif current.type == Lexer.Token.RIGHTCURL:
                if len(stack) == 1:
                    return primitives

                group = stack.pop()
                stack[-1].append(group)
            else:
                return primitives

            current = lexer.next()

        return primitives

if __name__ == '__main__':
    r = Parser.parse("""
        line(10, 10, 10, 10). 
        !p(10).
        { 
            rect(20, 20, 20, 20). 
            !p(2).
            {
                !snoepie(poepie).
            }
        }
    """)
    print(r.master())
    print(r[1].master())
    print(r[2].master())