from typing import *

from misc import default
from parsing.lexer import Lexer
from pattern.pattern import GroupPattern, ParameterPattern, InstancePattern, Pattern
from pattern.patterns import *


class PatternParser:
    @staticmethod
    def parse_group_pattern(lexer: Lexer, token: Lexer.Token) -> Optional[GroupPattern]:
        pass

    @staticmethod
    def parse_instance_pattern(lexer: Lexer, token: Lexer.Token) -> Optional[InstancePattern]:
        pass

    @staticmethod
    def parse_parameter_pattern(lexer: Lexer, token: Lexer.Token) -> Optional[ParameterPattern]:
        name = lexer.str(token)

        if lexer.next().type != default.parameter_pattern_begin:
            return None

        parameters: Primitive.Parameters = []
        current = lexer.next()
        types = { Lexer.Token.STRING, Lexer.Token.INT, Lexer.Token.FLOAT, Lexer.Token.IDENTIFIER, default.parameter_pattern_end }

        while True:
            if current.type not in types:
                return None

            if current.type == Lexer.Token.IDENTIFIER:
                parameters.append(lexer.str(current))

                types = { default.value_separator, default.parameter_pattern_end }
            elif current.type == Lexer.Token.FLOAT:
                parameters.append(float(lexer.str(current)))

                types = { default.value_separator, default.parameter_pattern_end }
            elif current.type == Lexer.Token.INT:
                parameters.append(int(lexer.str(current)))

                types = { default.value_separator, default.parameter_pattern_end }
            elif current.type == Lexer.Token.STRING:
                string = lexer.str(current)
                if len(string) == 0:
                    return None

                parameters.append(string)

                types = { default.value_separator, default.parameter_pattern_end }
            elif current.type == default.value_separator:
                types = { Lexer.Token.FLOAT, Lexer.Token.INT, Lexer.Token.IDENTIFIER, Lexer.Token.STRING }
            elif current.type == default.parameter_pattern_end:
                break
            else:
                return None

            current = lexer.next()

        return Pattern.from_list(parameters)

    @staticmethod
    def parse(code: str) -> GroupPattern:
        # lexer = Lexer(code)
        # pattern = GroupPattern()
        # stack = []
        #
        # parse_next_master = False
        # current = lexer.next()
        # while current.type != Lexer.Token.END:
        #     if current.type == Lexer.Token.OPERATOR and lexer.str(current) == "!":
        #         parse_next_master = True
        #     elif current.type == Lexer.Token.IDENTIFIER:
        #         primitive = PrimitiveParser.parse_primitive(lexer, current)
        #         if primitive is not None:
        #             stack[-1].append(primitive)
        #             if parse_next_master:
        #                 stack[-1].master = primitive
        #                 parse_next_master = False
        #     elif current.type == Lexer.Token.LEFTCURL:
        #         stack.append(Group())
        #     elif current.type == Lexer.Token.RIGHTCURL:
        #         if len(stack) == 1:
        #             return primitives
        #
        #         group = stack.pop()
        #         stack[-1].append(group)
        #     else:
        #         return primitives
        #
        #     current = lexer.next()
        #
        # return primitives
        pass

if __name__ == '__main__':
    code = "Linear[5]"
    lexer = Lexer(code)
    result = PatternParser.parse_parameter_pattern(lexer, lexer.next())
