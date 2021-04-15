from gui.primitives import *
from parsing.lexer import Lexer
from misc import default

class PrimitiveParser:
    @staticmethod
    def parse_primitive(lexer: Lexer, token: Lexer.Token, reference_factory: ReferenceFactory) -> Union[Primitive, None]:
        name = lexer.str(token)
        if lexer.next().type != default.primitive_begin:
            return None

        parameters: Primitive.Parameters = []
        current = lexer.next()
        types = { Lexer.Token.STRING, Lexer.Token.INT, Lexer.Token.FLOAT, Lexer.Token.IDENTIFIER, default.primitive_end }

        while True:
            if current.type not in types:
                return None

            if current.type == Lexer.Token.IDENTIFIER:
                parameters.append(lexer.str(current))

                types = { default.value_separator, default.primitive_end }
            elif current.type == Lexer.Token.FLOAT:
                parameters.append(float(lexer.str(current)))

                types = { default.value_separator, default.primitive_end }
            elif current.type == Lexer.Token.INT:
                parameters.append(int(lexer.str(current)))

                types = { default.value_separator, default.primitive_end }
            elif current.type == Lexer.Token.STRING:
                string = lexer.str(current)
                if len(string) == 0:
                    return None

                parameters.append(string)

                types = { default.value_separator, default.primitive_end }
            elif current.type == default.value_separator:
                types = { Lexer.Token.FLOAT, Lexer.Token.INT, Lexer.Token.IDENTIFIER, Lexer.Token.STRING }
            elif current.type == default.primitive_end:
                if lexer.next().type != default.primitive_separator:
                    return None

                break
            else:
                return None

            current = lexer.next()

        return Primitive.from_list(reference_factory.new(), name, parameters)

    @staticmethod
    def parse(code: str, reference_factory=ReferenceFactory()) -> PrimitiveGroup:
        lexer = Lexer(code)
        primitives = PrimitiveGroup(reference_factory.new())
        stack = [primitives]

        parse_next_master = False
        current = lexer.next()
        while current.type != Lexer.Token.END:
            if current.type == Lexer.Token.OPERATOR and lexer.str(current) == "!":
                parse_next_master = True
            elif current.type == Lexer.Token.IDENTIFIER:
                primitive = PrimitiveParser.parse_primitive(lexer, current, reference_factory)
                if primitive is not None:
                    stack[-1].append(primitive)
                    if parse_next_master:
                        stack[-1].master = primitive
                        parse_next_master = False
            elif current.type == default.primitive_group_begin:
                stack.append(PrimitiveGroup(reference_factory.new()))
            elif current.type == default.primitive_group_end:
                if len(stack) == 1:
                    return primitives

                group = stack.pop()
                stack[-1].append(group)
            else:
                return primitives

            current = lexer.next()

        return primitives