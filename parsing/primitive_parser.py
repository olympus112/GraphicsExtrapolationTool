from gui.primitives import *
from parsing.lexer import Lexer
from misc import default

class PrimitiveParser:

    def __init__(self, code: str):
        self.lexer: Lexer = Lexer(code)

    def parse_primitive(self, token: Lexer.Token, reference_factory: ReferenceFactory) -> Optional[Primitive]:
        name = self.lexer.str(token)
        if self.lexer.next().type != default.primitive_begin:
            return None

        parameters: Primitive.Parameters = []
        current = self.lexer.next()
        types = { Lexer.Token.STRING, Lexer.Token.INT, Lexer.Token.FLOAT, Lexer.Token.IDENTIFIER, default.primitive_end }

        while True:
            if current.type not in types:
                return None

            if current.type == Lexer.Token.IDENTIFIER:
                parameters.append(self.lexer.str(current))

                types = { default.value_separator, default.primitive_end }
            elif current.type == Lexer.Token.FLOAT:
                parameters.append(float(self.lexer.str(current)))

                types = { default.value_separator, default.primitive_end }
            elif current.type == Lexer.Token.INT:
                parameters.append(int(self.lexer.str(current)))

                types = { default.value_separator, default.primitive_end }
            elif current.type == Lexer.Token.STRING:
                string = self.lexer.str(current)
                if len(string) == 0:
                    return None

                parameters.append(string)

                types = { default.value_separator, default.primitive_end }
            elif current.type == default.value_separator:
                types = { Lexer.Token.FLOAT, Lexer.Token.INT, Lexer.Token.IDENTIFIER, Lexer.Token.STRING }
            elif current.type == default.primitive_end:
                if self.lexer.next().type != default.primitive_separator:
                    return None

                break
            else:
                return None

            current = self.lexer.next()

        return Primitive.from_list(reference_factory.new(), name, parameters)

    def parse_named_primitive(self, token: Lexer.Token) -> Tuple[Optional[Tuple[str, int]], List[Union[str, int]]]:
        variables: List[Union[str, int]] = []

        if token.type != default.variable:
            return None, variables

        name = self.lexer.next()
        if name.type != Lexer.Token.IDENTIFIER:
            return None, variables

        name = self.lexer.str(name)

        if self.lexer.next().type != default.primitive_begin:
            return None, variables

        types = { Lexer.Token.IDENTIFIER, Lexer.Token.INT }
        current = self.lexer.next()
        while True:
            if current.type not in types:
                return None, variables

            if current.type == Lexer.Token.IDENTIFIER:
                variables.append(self.lexer.str(current))

                types = { default.value_separator, default.primitive_end }
            elif current.type == Lexer.Token.INT:
                variables.append(int(self.lexer.str(current)))

                types = { default.value_separator, default.primitive_end }
            elif current.type == default.value_separator:

                types = { Lexer.Token.IDENTIFIER, Lexer.Token.INT }
            elif current.type == default.primitive_end:

                break
            else:
                return None, variables

            current = self.lexer.next()

        return (name, len(variables)), variables

    def parse_named_primitives(self) -> Dict[Tuple[str, int], List[Union[str, int]]]:
        self.lexer.reset()

        named_primitives: Dict[Tuple[str, int], List[str]] = dict()

        current = self.lexer.next()
        while current.type != Lexer.Token.END:
            if current.type == default.variable:
                key, variables = self.parse_named_primitive(current)
                if key is not None:
                    named_primitives[key] = variables

            current = self.lexer.next()

        return named_primitives


    def parse(self, reference_factory: ReferenceFactory) -> Tuple[PrimitiveGroup, Dict[Tuple[str, int], List[Union[str, int]]]]:
        self.lexer.reset()

        named_primitives: Dict[Tuple[str, int], List[Union[str, int]]] = dict()
        primitives = PrimitiveGroup(reference_factory.new())
        stack = [primitives]

        parse_next_master = False
        current = self.lexer.next()
        while current.type != Lexer.Token.END:
            if current.type == Lexer.Token.EXLAMATION:
                parse_next_master = True
            elif current.type == default.variable:
                key, variables = self.parse_named_primitive(current)
                if key is not None:
                    named_primitives[key] = variables
            elif current.type == Lexer.Token.IDENTIFIER:
                primitive = self.parse_primitive(current, reference_factory)
                if isinstance(primitive, Primitive):
                    key = (primitive.name, primitive.arity)
                    if key not in named_primitives:
                        named_primitives[key] = list(range(primitive.arity))
                if primitive is not None:
                    stack[-1].append(primitive)
                    if parse_next_master:
                        stack[-1].master = primitive
                        parse_next_master = False
            elif current.type == default.primitive_group_begin:
                stack.append(PrimitiveGroup(reference_factory.new()))
            elif current.type == default.primitive_group_end:
                if len(stack) == 1:
                    return primitives, named_primitives

                group = stack.pop()
                stack[-1].append(group)
            else:
                return primitives, named_primitives

            current = self.lexer.next()

        return primitives, named_primitives