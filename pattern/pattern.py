from __future__ import annotations

from patterns import *
from parsing.primitive_parser import PrimitiveParser
from gui.primitives import PrimitiveGroup, Primitive
from misc.util import ReferenceFactory

class PrimitivePattern:
    referenceFactory = ReferenceFactory()

    def __init__(self):
        self._identifier: ReferenceFactory.Reference = PrimitivePattern.referenceFactory.new()
        self.parent: Optional[GroupPattern] = None
        self._level: int = 1

    def __del__(self):
        del self.identifier

    @property
    def identifier(self) -> ReferenceFactory.Reference:
        return self._identifier

    @identifier.setter
    def identifier(self, value: ReferenceFactory.Reference):
        del self.identifier
        self._identifier = value

    @identifier.deleter
    def identifier(self):
        PrimitivePattern.referenceFactory.release(self._identifier)
        self._identifier = None

    @property
    def level(self) -> int:
        return self._level


class InstancePattern(PrimitivePattern):
    def __init__(self, *patterns):
        super(InstancePattern, self).__init__()
        self.patterns: Sequence[ParameterPattern] = [*patterns]

    def __str__(self) -> str:
        result = "{}{}".format(default.tokens[default.reference], self._identifier)
        if self.parent is not None:
            result += "{}{}".format(default.tokens[default.parent], self.parent.identifier)
        if len(self.patterns) > 0:
            result += util.format_list(self.patterns, str, default.tokens[default.instance_pattern_begin], default.tokens[default.value_separator], default.tokens[default.instance_pattern_end])

        return result

    def __repr__(self) -> str:
        result = "#{}".format(self._identifier)
        if self.parent is not None:
            result += "@{}".format(self.parent.identifier)
        if len(self.patterns) > 0:
            result += ", ".join(list(map(repr, self.patterns))).join(['[', ']'])

        return result

    def print(self, depth: int = 0, _format: Union[str, repr] = str):
        print("\t" * depth + _format(self))

    def append(self, *patterns: ParameterPattern):
        self.patterns += patterns

    def next(self, start: Primitive, nths: Union[int, List[int]]) -> List[Primitive]:
        input_parameters = start.as_list()

        def next_primitive(nth: int):
            parameters = []
            for index, pattern in enumerate(self.patterns):
                output_parameters = pattern.next(input_parameters[index], nth)
                parameters.append(output_parameters)

            return Primitive.from_list(parameters)

        if isinstance(nths, int):
            return [next_primitive(nths)]

        return [next_primitive(nth) for nth in nths]


class GroupPattern(PrimitivePattern):
    def __init__(self, pattern: InstancePattern):
        super(GroupPattern, self).__init__()
        self.intergroup_pattern: InstancePattern = pattern
        self.intragroup_patterns: List[Union[GroupPattern, InstancePattern]] = []

    def __str__(self) -> str:
        result = "{}{}".format(default.tokens[default.reference], self._identifier)
        if self.parent is not None:
            result += "{}{}".format(default.tokens[default.parent], self.parent.identifier)
        result += default.tokens[default.group_pattern_parent_begin] + str(self.intergroup_pattern) + default.tokens[default.group_pattern_parent_end]
        if len(self.intragroup_patterns) > 0:
            result += util.format_list(self.intragroup_patterns, str, default.tokens[default.group_pattern_begin], default.tokens[default.value_separator], default.tokens[default.group_pattern_end])

        return result

    def __repr__(self) -> str:
        result = "#{}".format(self._identifier)
        if self.parent is not None:
            result += "@{}".format(self.parent.identifier)
        result += self.intergroup_pattern
        if len(self.intragroup_patterns) > 0:
            result += util.format_list(self.intragroup_patterns, repr, '{', ',', '}')

        return result

    def __getitem__(self, item: int) -> Union[GroupPattern, InstancePattern]:
        return self.intragroup_patterns[item]

    def __iter__(self):
        return self.intragroup_patterns.__iter__()

    @PrimitivePattern.level.setter
    def level(self, value: int):
        if value >= 0:
            self._level = value

    def print(self, depth: int = 0, _format: Union[str, repr] = str):
        print("\t" * depth + "#{}".format(self.identifier), end="")
        if self.parent is not None:
            print("@{}".format(self.parent.identifier), end="")
        print("(" + _format(self.intergroup_pattern) + ") {{ {}".format(self.level))
        for child in self.intragroup_patterns:
            child.print(depth + 1, _format)
        print("\t" * depth + "}")

    def append(self, intragroup_pattern: Union[GroupPattern, InstancePattern]):
        if len(self.intragroup_patterns) == 0:
            self.level = intragroup_pattern.level + 1
        else:
            self.level = max(self.level, intragroup_pattern.level)

        self.intragroup_patterns.append(intragroup_pattern)
        intragroup_pattern.parent = self

    def next(self, start: Primitive, nths: Union[int, List[int]]) -> List[Primitive]:
        if isinstance(nths, int):
            return self.intergroup_pattern.next(start, nths)

        return [self.intergroup_pattern.next(start, nth)[0] for nth in nths]


class Pattern:
    @staticmethod
    def from_list(parameters: Primitive.Parameters) -> Optional[ParameterPattern]:
        for pattern in [ConstantPattern, LinearPattern, PeriodicPattern]:
            if parameters[0] == pattern.name():
                return pattern(parameters[1:])

        return None

    @staticmethod
    def next(start_primitives: List[Primitive], pattern: Union[GroupPattern, InstancePattern], extrapolations: List[int]) -> List[Primitive]:
        assert len(extrapolations) == pattern.level

        extrapolation = extrapolations.pop(0)
        if isinstance(pattern, InstancePattern):
            result = []
            for start_primitive in start_primitives:
                result += pattern.next(start_primitive, list(range(extrapolation)))

            return result

        elif isinstance(pattern, GroupPattern):
            result = []
            for start_primitive in start_primitives:
                new_start_primitives = pattern.intergroup_pattern.next(start_primitive, list(range(extrapolation)))
                for index, new_start_primitive in enumerate(new_start_primitives):
                    result += Pattern.next([new_start_primitive], pattern[index % len(pattern.intragroup_patterns)], extrapolations.copy())

            return result

        else:
            raise Exception()

    @staticmethod
    def search_group_recursive(root: PrimitiveGroup, available_patterns: [ParameterPattern], tolerance: float) -> Optional[Union[GroupPattern, InstancePattern]]:
        primitive_pattern = Pattern.search_group(root, available_patterns, tolerance)
        group_pattern = primitive_pattern

        for group in root:
            if not isinstance(group, PrimitiveGroup):
                continue

            subpattern = Pattern.search_group_recursive(group, available_patterns, tolerance)
            if subpattern is None:
                return None

            if group_pattern is primitive_pattern:
                group_pattern = GroupPattern(primitive_pattern)

            group_pattern.append(subpattern)

        return group_pattern

    @staticmethod
    def search_group(group: PrimitiveGroup, available_patterns: [ParameterPattern], tolerance: float) -> Optional[InstancePattern]:
        parameters_list = [[] for _ in range(group.max_arity + 1)]
        for primitive in group:
            parameters_list[0].append(primitive.master.name)
            for parameter_index, parameter in enumerate(primitive.master.parameters):
                parameters_list[parameter_index + 1].append(parameter)

        primitive_pattern = InstancePattern()
        for parameters in parameters_list:
            found_pattern = Pattern.search_parameters(parameters, available_patterns, tolerance)
            if found_pattern is None:
                return None

            primitive_pattern.append(found_pattern)

        return primitive_pattern

    @staticmethod
    def search_parameters(parameters: Primitive.Parameters, available_patterns: List[ParameterPattern], tolerance: float) -> Optional[ParameterPattern]:
        parameter_count = len(parameters)
        flags = ParameterFlags(parameters)

        for available_pattern in available_patterns:
            if parameter_count < available_pattern.minimum_parameters():
                continue

            input_parameters = np.array(parameters, flags.dtype)
            result = available_pattern.apply(input_parameters, flags, tolerance)
            if result is not None:
                return result

        return None

    @staticmethod
    def search(primitives: Sequence[Primitive], available_patterns: Sequence, extrapolations: int, tolerance: float):
        output_parameters = [[] for _ in range(extrapolations)]
        arity = primitives[0].arity

        if not all(primitive.arity == arity for primitive in primitives):
            return None, []

        found_patterns = []
        for index in range(-1, arity):
            if index == -1:
                input_parameters = [primitive.name for primitive in primitives]
            else:
                input_parameters = [primitive[index] for primitive in primitives]

            parameter_count = len(input_parameters)
            flags = ParameterFlags(input_parameters)

            for pattern in available_patterns:
                if parameter_count < pattern.minimum_parameters():
                    continue

                input_parameters = np.array(input_parameters, flags.dtype)
                result = pattern.apply(input_parameters, index, flags, tolerance)
                if result is not None:
                    found_patterns.append(result)
                    for extrapolation in range(extrapolations):
                        output_parameters[extrapolation].append(result.next(input_parameters, extrapolation + 1))
                    break
            else:
                return None, found_patterns

        return output_parameters, found_patterns

if __name__ == '__main__':
    code1 = """
    {
        {p(1). p(2).} 
        {p(3). p(3).}
    }{
        p(4). 
        {p(5). p(6).}
    }
    """
    code2 = """
        {p(0, 0). l(1, 0).}
        {l(0, 1). p(1, 1).}
    """
    code3 = """
        p(0, 0).p(0, 1).
    """

    code = code2
    print(code)
    parse = PrimitiveParser.parse(code)
    pattern = Pattern.search_group_recursive(parse, [ConstantPattern, LinearPattern, PeriodicPattern], 0.1)
    pattern.print()
    print(pattern)
    print(Pattern.next([parse[0].master], pattern, [4, 4]))

    # Pattern.search_group_recursive(Parser.parse(code2), [ConstantPattern, LinearPattern], 0.1).print()
    # Pattern.search_group_recursive(Parser.parse(code3), [ConstantPattern, LinearPattern], 0.1).print()
