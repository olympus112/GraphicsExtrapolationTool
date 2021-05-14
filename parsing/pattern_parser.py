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

    def parse_sequence(self, start_type: Optional[Lexer.Token.Type], end_type: Lexer.Token.Type, token: Lexer.Token) -> Tuple[Optional[List[Union[int, str]]], Lexer.Token]:
        if start_type is not None:
            if token.type != start_type:
                return None, token

            token = self.lexer.next()

        sequence: List[Union[int, str]] = []
        types = { Lexer.Token.INT, Lexer.Token.IDENTIFIER }
        while token.type != Lexer.Token.END:
            if token.type not in types:
                return None, token

            if token.type == Lexer.Token.IDENTIFIER:
                value = self.lexer.str(token)
                value = self.substitute_variable(value)

                def check_int(s):
                    if s[0] in ('-', '+'):
                        return s[1:].isdigit()
                    return s.isdigit()

                if check_int(value):
                    sequence.append(int(value))
                else:
                    sequence.append(value)

                types = { default.value_separator, end_type }
            elif token.type == Lexer.Token.INT:
                sequence.append(int(self.lexer.str(token)))

                types = { default.value_separator, end_type }
            elif token.type == default.value_separator:
                types = { Lexer.Token.INT, Lexer.Token.IDENTIFIER }
            elif token.type == end_type:
                return sequence, token
            else:
                return None, token

            token = self.lexer.next()

        return None, token

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

        if token.type == default.sizes:
            pattern = self.parse_group_pattern(token, reference_factory, _parse_identifier=False)
        elif token.type == default.arities:
            pattern = self.parse_primitive_pattern(token, reference_factory, _parse_identifier=False)
        elif token.type == Lexer.Token.IDENTIFIER and self.lexer.str(token) == default.none:
            return NonePattern()
        else:
            pattern = None

        if pattern is not None:
            pattern._identifier = identifier

        return pattern

    def parse_group_pattern(self, token: Lexer.Token, reference_factory: ReferenceFactory, _parse_identifier: bool = True) -> Optional[GroupPattern]:
        identifier, token = self.parse_identifier(token, reference_factory, _parse_identifier)

        if token.type != default.sizes:
            return None

        token = self.lexer.next()
        size_pattern = self.parse_parameter_pattern(token)

        token = self.lexer.next()
        if token.type != default.group_pattern_parent_begin:
            return None

        parent_begin = self.lexer.next()
        parent = self.parse_primitive_pattern(parent_begin, reference_factory, _parse_arities=True, _parse_identifier=True)
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
        types = { default.arities, default.sizes, default.identifier, Lexer.Token.IDENTIFIER, default.group_pattern_children_end }
        while token.type != Lexer.Token.END:
            if token.type not in types:
                return None

            if token.type == default.sizes or token.type == default.arities or token.type == default.identifier:
                pattern = self.parse_instance_pattern(token, reference_factory, _parse_identifier=True)
                patterns.append(pattern)

                types = { default.value_separator, default.group_pattern_children_end }
            elif token.type == Lexer.Token.IDENTIFIER and self.lexer.str(token) == default.none:
                patterns.append(NonePattern())
                types = {default.value_separator, default.group_pattern_children_end}
            elif token.type == default.value_separator:
                types = { default.arities, default.sizes, default.identifier, Lexer.Token.IDENTIFIER }
            elif token.type == default.group_pattern_children_end:
                pattern = GroupPattern(parent, identifier=identifier)
                pattern.append(*zip(patterns, [size_pattern.next(None, i) for i in range(len(patterns))]))

                return pattern
            else:
                return None

            token = self.lexer.next()

    def parse_primitive_pattern(self, token: Lexer.Token, reference_factory: ReferenceFactory, _parse_identifier: bool = True, _parse_arities: bool = True) -> Optional[PrimitivePattern]:
        identifier, token = self.parse_identifier(token, reference_factory, _parse_identifier=_parse_identifier)
        arities, token = self.parse_sequence(default.arities, default.primitive_pattern_begin, token)
        if arities is None:
            return None

        if token.type != default.primitive_pattern_begin:
            return None

        patterns: Dict[Union[int, str], ParameterPattern] = dict()

        token = self.lexer.next()
        types = { Lexer.Token.IDENTIFIER, Lexer.Token.INT, default.primitive_pattern_end }
        while token.type != Lexer.Token.END:
            if token.type not in types:
                return None

            if token.type == Lexer.Token.IDENTIFIER or token.type == Lexer.Token.INT:
                selectors, token = self.parse_sequence(None, default.selector, token)

                if token.type != default.selector:
                    return None

                token = self.lexer.next()
                if token.type != Lexer.Token.IDENTIFIER:
                    return None

                pattern = self.parse_parameter_pattern(token)
                for selector in selectors:
                    patterns[selector] = pattern

                types = { default.value_separator, default.primitive_pattern_end }
            elif token.type == default.value_separator:
                types = { Lexer.Token.IDENTIFIER, Lexer.Token.INT }
            elif token.type == default.primitive_pattern_end:
                return PrimitivePattern(patterns=patterns, identifier=identifier, arities=arities)
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
        types = { Lexer.Token.STRING, Lexer.Token.INT, Lexer.Token.FLOAT, Lexer.Token.IDENTIFIER, Lexer.Token.OPERATOR, default.parameter_pattern_end }
        while token.type != Lexer.Token.END:
            if token.type not in types:
                return None

            if token.type == Lexer.Token.IDENTIFIER:
                identifier = self.lexer.str(token)
                identifier = self.substitute_variable(identifier)
                parameters.append(identifier)

                types = { default.value_separator, default.parameter_pattern_end }
            elif token.type == Lexer.Token.OPERATOR:
                string = self.lexer.str(token)
                if string not in ['+', '-', '*', '/']:
                    return None

                parameters.append(string)
                types = {default.value_separator, default.parameter_pattern_end}

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
                types = { Lexer.Token.FLOAT, Lexer.Token.INT, Lexer.Token.IDENTIFIER, Lexer.Token.OPERATOR, Lexer.Token.STRING }
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