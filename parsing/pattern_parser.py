from parsing.lexer import Lexer
from pattern.pattern import *
from pattern.patterns import *

class PatternParser:

    def __init__(self, code: str):
        self.lexer: Lexer = Lexer(code)
        self.variables: Dict[str, str] = dict()

    def substitute_variable(self, identifier: str) -> str:
        original_identifier = identifier
        while identifier in self.variables.keys():
            identifier = self.variables[identifier]

            if identifier == original_identifier:
                break

        return identifier

    def parse_variable_assignment(self, token: Lexer.Token):
        if token.type != default.variable:
            return

        name_token = self.lexer.next()
        if name_token.type != Lexer.Token.IDENTIFIER:
            return

        assignment = self.lexer.next()
        if assignment.type != default.assigment:
            return

        value_token = self.lexer.next()
        name = self.lexer.str(name_token)
        value = self.lexer.str(value_token)

        if value_token.type == Lexer.Token.IDENTIFIER:
            pass
        elif value_token.type == Lexer.Token.INT:
            value = int(value)
        elif value_token.type == Lexer.Token.FLOAT:
            value = float(value)
        else:
            return

        self.variables[name] = value


    def parse_identifier(self, token: Lexer.Token, reference_factory: ReferenceFactory, _parse_identifier: bool) -> Tuple[ReferenceFactory.Reference, Lexer.Token]:
        if _parse_identifier:
            if token.type == default.identifier:
                if token.type != default.identifier:
                    return -1, token

                token = self.lexer.next()
                if token.type != Lexer.Token.INT:
                    return -1, token

                identifier = int(self.lexer.str(token))
                reference_factory.reserve(identifier)

                return identifier, self.lexer.next()
            else:
                return -1, token
        else:
            return -1, token

    def parse_instance_pattern(self, token: Lexer.Token, reference_factory: ReferenceFactory, _parse_identifier: bool = True) -> Optional[InstancePattern]:
        if token.type == default.variable:
            self.parse_variable_assignment(token)
            return self.parse_instance_pattern(self.lexer.next(), reference_factory, _parse_identifier)

        identifier, token = self.parse_identifier(token, reference_factory, _parse_identifier=_parse_identifier)
        if token.type == default.group_pattern_parent_begin:
            pattern = self.parse_group_pattern(token, reference_factory, _parse_identifier=False)
        elif token.type == default.primitive_pattern_begin:
            pattern = self.parse_primitive_pattern(token, reference_factory, _parse_identifier=False)
        else:
            pattern = None

        if pattern is not None:
            pattern._identifier = identifier

        return pattern

    def parse_group_pattern(self, token: Lexer.Token, reference_factory: ReferenceFactory,  _parse_identifier: bool = True) -> Optional[GroupPattern]:
        identifier, token = self.parse_identifier(token, reference_factory, _parse_identifier)

        if token.type != default.group_pattern_parent_begin:
            return None

        parent_begin = self.lexer.next()
        parent = self.parse_primitive_pattern(parent_begin, reference_factory, _parse_identifier=True)
        if parent is None:
            return None

        group_pattern_end = self.lexer.next()
        if group_pattern_end.type != default.group_pattern_parent_end:
            return None

        group_children_begin = self.lexer.next()
        if group_children_begin.type != default.group_pattern_children_begin:
            return None

        patterns: List[InstancePattern] = []

        token = self.lexer.next()
        types = { default.primitive_pattern_begin, default.group_pattern_parent_begin, default.identifier, default.group_pattern_children_end }
        while token.type != Lexer.Token.END:
            if token.type not in types:
                return None

            if token.type == default.primitive_pattern_begin or token.type == default.group_pattern_parent_begin or token.type == default.identifier:
                pattern = self.parse_instance_pattern(token, reference_factory, _parse_identifier=True)
                patterns.append(pattern)

                types = { default.value_separator, default.group_pattern_children_end }
            elif token.type == default.value_separator:
                types = { default.primitive_pattern_begin, default.group_pattern_parent_begin, default.identifier }
            elif token.type == default.group_pattern_children_end:
                pattern = GroupPattern(parent, identifier=identifier)
                for child in patterns:
                    pattern.append(child)

                return pattern
            else:
                return None

            token = self.lexer.next()

    def parse_primitive_pattern(self, token: Lexer.Token, reference_factory: ReferenceFactory, _parse_identifier: bool = True) -> Optional[PrimitivePattern]:
        identifier, token = self.parse_identifier(token, reference_factory, _parse_identifier=_parse_identifier)

        if token.type != default.primitive_pattern_begin:
            return None

        patterns: List[ParameterPattern] = []

        token = self.lexer.next()
        types = { Lexer.Token.IDENTIFIER, default.primitive_pattern_end }
        while token.type != Lexer.Token.END:
            if token.type not in types:
                return None

            if token.type == Lexer.Token.IDENTIFIER:
                pattern = self.parse_parameter_pattern(token)
                patterns.append(pattern)

                types = { default.value_separator, default.primitive_pattern_end }
            elif token.type == default.value_separator:
                types = { Lexer.Token.IDENTIFIER }
            elif token.type == default.primitive_pattern_end:
                return PrimitivePattern(*patterns, identifier=identifier)
            else:
                return None

            token = self.lexer.next()

    def parse_parameter_pattern(self, token: Lexer.Token) -> Optional[ParameterPattern]:
        name = self.lexer.str(token)
        name = self.substitute_variable(name)

        if self.lexer.next().type != default.parameter_pattern_begin:
            return None

        parameters: Primitive.Parameters = []

        token = self.lexer.next()
        types = { Lexer.Token.STRING, Lexer.Token.INT, Lexer.Token.FLOAT, Lexer.Token.IDENTIFIER, default.parameter_pattern_end }
        while token.type != Lexer.Token.END:
            if token.type not in types:
                return None

            if token.type == Lexer.Token.IDENTIFIER:
                identifier = self.lexer.str(token)
                identifier = self.substitute_variable(identifier)
                parameters.append(identifier)

                types = { default.value_separator, default.parameter_pattern_end }
            elif token.type == Lexer.Token.FLOAT:
                parameters.append(float(self.lexer.str(token)))

                types = { default.value_separator, default.parameter_pattern_end }
            elif token.type == Lexer.Token.INT:
                parameters.append(int(self.lexer.str(token)))

                types = { default.value_separator, default.parameter_pattern_end }
            elif token.type == Lexer.Token.STRING:
                string = self.lexer.str(token)
                if len(string) == 0:
                    return None

                parameters.append(string)

                types = { default.value_separator, default.parameter_pattern_end }
            elif token.type == default.value_separator:
                types = { Lexer.Token.FLOAT, Lexer.Token.INT, Lexer.Token.IDENTIFIER, Lexer.Token.STRING }
            elif token.type == default.parameter_pattern_end:
                break
            else:
                return None

            token = self.lexer.next()

        return Pattern.from_list(name, parameters)


    def add_identifiers(self, pattern: InstancePattern, reference_factory: ReferenceFactory):
        if pattern.identifier == -1:
            pattern.identifier = reference_factory.new()

        if isinstance(pattern, GroupPattern):
            if pattern.intergroup_pattern.identifier == -1:
                pattern.intergroup_pattern.identifier = reference_factory.new()

            for child in pattern:
                self.add_identifiers(child, reference_factory)


    def parse(self, reference_factory: ReferenceFactory = ReferenceFactory()) -> Optional[InstancePattern]:
        self.lexer.reset()

        token = self.lexer.next()
        pattern = self.parse_instance_pattern(token, reference_factory, _parse_identifier=True)

        if pattern is not None:
            self.add_identifiers(pattern, reference_factory)

        return pattern