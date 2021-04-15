from __future__ import annotations

from pattern.patterns import *
from gui.primitives import PrimitiveGroup, Primitive
from misc.util import ReferenceFactory

class InstancePattern:

    def __init__(self, identifier: Optional[ReferenceFactory.Reference]):
        self._identifier = identifier

        self.parent: Optional[GroupPattern] = None
        self._level: int = 1

    @property
    def identifier(self) -> ReferenceFactory.Reference:
        return self._identifier

    @identifier.setter
    def identifier(self, value: ReferenceFactory.Reference):
        self._identifier = value

    @property
    def level(self) -> int:
        return self._level

    @abstractmethod
    def print(self, depth: int = 0, _format: Union[str, repr] = str):
        pass

    @abstractmethod
    def next(self, start: Primitive, nths: Union[int, List[int]], reference_factory: ReferenceFactory) -> List[Primitive]:
        pass


class PrimitivePattern(InstancePattern):
    def __init__(self, *patterns, identifier: Optional[ReferenceFactory.Reference] = None):
        super(PrimitivePattern, self).__init__(identifier)
        self.patterns: List[ParameterPattern] = [*patterns]

    def __str__(self) -> str:
        result = ""
        # result += "{}{}".format(default.tokens[default.identifier], self._identifier)
        result += util.format_list(self.patterns, str, default.tokens[default.primitive_pattern_begin], default.tokens[default.value_separator], default.tokens[default.primitive_pattern_end])

        return result

    def __repr__(self) -> str:
        result = "#{}".format(self._identifier)
        if self.parent is not None:
            result += "@{}".format(self.parent.identifier)
        result += util.format_list(self.patterns, repr, '[', ',', ']')

        return result

    def print(self, depth: int = 0, _format: Union[str, repr] = str):
        print("\t" * depth + _format(self))

    def append(self, *patterns: ParameterPattern):
        self.patterns += patterns

    def next(self, start: Primitive, nths: Union[int, List[int]], reference_factory: ReferenceFactory) -> List[Primitive]:
        input_parameters = start.as_list()

        def next_primitive(nth: int):
            parameters = []
            for index, pattern in enumerate(self.patterns):
                if pattern is None:
                    output_parameter = input_parameters[index] # Todo fix
                else:
                    output_parameter = pattern.next(input_parameters[index], nth)
                    # Todo check
                parameters.append(round(output_parameter, 2) if isinstance(output_parameter, float) else output_parameter)

            return Primitive.from_list(reference_factory.new(), parameters[0], parameters[1:])

        if isinstance(nths, int):
            return [next_primitive(nths)]

        return [next_primitive(nth) for nth in nths]


class GroupPattern(InstancePattern):
    def __init__(self, pattern: PrimitivePattern, identifier: Optional[ReferenceFactory.Reference] = None):
        super(GroupPattern, self).__init__(identifier)
        self.intergroup_pattern: PrimitivePattern = pattern
        self.intragroup_patterns: List[InstancePattern] = []

    def __str__(self) -> str:
        result = ""
        # result += "{}{}".format(default.tokens[default.identifier], self._identifier)
        result += default.tokens[default.group_pattern_parent_begin] + str(self.intergroup_pattern) + default.tokens[default.group_pattern_parent_end]
        result += util.format_list(self.intragroup_patterns, str, default.tokens[default.group_pattern_children_begin], default.tokens[default.value_separator], default.tokens[default.group_pattern_children_end])

        return result

    def __repr__(self) -> str:
        result = "#{}".format(self._identifier)
        if self.parent is not None:
            result += "@{}".format(self.parent.identifier)
        result += self.intergroup_pattern
        result += util.format_list(self.intragroup_patterns, repr, '{', ',', '}')

        return result

    def __getitem__(self, item: int) -> InstancePattern:
        return self.intragroup_patterns[item]

    def __iter__(self):
        return self.intragroup_patterns.__iter__()

    @InstancePattern.level.setter
    def level(self, value: int):
        if value >= 0:
            self._level = value

    def print(self, depth: int = 0, _format: Union[str, repr] = str):
        print("\t" * depth + "#{}".format(self.identifier), end="")
        if self.parent is not None:
            print("@{}".format(self.parent.identifier), end="")
        print("(" + _format(self.intergroup_pattern) + ") {")
        for child in self.intragroup_patterns:
            child.print(depth + 1, _format)
        print("\t" * depth + "}")

    def append(self, intragroup_pattern: InstancePattern):
        if len(self.intragroup_patterns) == 0:
            self.level = intragroup_pattern.level + 1
        else:
            self.level = max(self.level, intragroup_pattern.level)

        self.intragroup_patterns.append(intragroup_pattern)
        intragroup_pattern.parent = self

    def next(self, start: Primitive, nths: Union[int, List[int]], reference_factory: ReferenceFactory) -> List[Primitive]:
        if isinstance(nths, int):
            return self.intergroup_pattern.next(start, nths, reference_factory)

        return [self.intergroup_pattern.next(start, nth, reference_factory)[0] for nth in nths]


class Pattern:
    @staticmethod
    def from_list(name: str, parameters: Primitive.Parameters) -> Optional[ParameterPattern]:
        for pattern in [ConstantPattern, LinearPattern, SinusoidalPattern]:
            if name == pattern.name():
                return pattern(*parameters)

        if name == PeriodicPattern.name():
            return PeriodicPattern(parameters)

        if name == BFSOperatorPattern.name():
            operators = []
            for parameter in parameters:
                if isinstance(parameter, str):
                    for operator in BFSOperatorPattern.zero_unsafe_operations:
                        if parameter == str(operator):
                            operators.append(operator)
                            break
                    else:
                        return None
                else:
                    if len(operators) == 0:
                        return None

                    break

            return BFSOperatorPattern(operators, parameters[len(operators) : 2 * len(operators) + 1], *parameters[2 * len(operators) + 1:])

        return None

    @staticmethod
    def next(start_primitives: List[Primitive], pattern: InstancePattern, extrapolations: List[int], reference_factory: ReferenceFactory = ReferenceFactory()) -> List[Primitive]:
        assert len(extrapolations) == pattern.level

        extrapolation = extrapolations.pop(0)
        if isinstance(pattern, PrimitivePattern):
            result = []
            for start_primitive in start_primitives:
                result += pattern.next(start_primitive, list(range(extrapolation)), reference_factory)

            return result

        elif isinstance(pattern, GroupPattern):
            result = []
            for start_primitive in start_primitives:
                if pattern.intergroup_pattern is not None:
                    new_start_primitives = pattern.intergroup_pattern.next(start_primitive, list(range(extrapolation)), reference_factory)
                else:
                    new_start_primitives = [start_primitive]
                for index, new_start_primitive in enumerate(new_start_primitives):
                    result += Pattern.next([new_start_primitive], pattern[index % len(pattern.intragroup_patterns)], extrapolations.copy())

            return result

        else:
            raise Exception()

    @staticmethod
    def search_group_recursive(root: PrimitiveGroup, available_patterns: [ParameterPattern], tolerance: float, reference_factory: ReferenceFactory) -> Optional[Union[GroupPattern, PrimitivePattern]]:
        if root is None:
            return None

        primitive_pattern = Pattern.search_group(root, available_patterns, tolerance, reference_factory)
        group_pattern = primitive_pattern

        for group in root:
            if not isinstance(group, PrimitiveGroup):
                continue

            subpattern = Pattern.search_group_recursive(group, available_patterns, tolerance, reference_factory)
            if subpattern is None:
                return None

            if group_pattern is primitive_pattern:
                group_pattern = GroupPattern(primitive_pattern, reference_factory.new())

            group_pattern.append(subpattern)

        return group_pattern

    @staticmethod
    def search_group(group: PrimitiveGroup, available_patterns: [ParameterPattern], tolerance: float, reference_factory: ReferenceFactory) -> Optional[PrimitivePattern]:
        if group is None or group.max_arity is None:
            return None

        parameters_list = [[] for _ in range(group.max_arity + 1)]
        for primitive in group:
            parameters_list[0].append(primitive.master.name)
            for parameter_index, parameter in enumerate(primitive.master.parameters):
                parameters_list[parameter_index + 1].append(parameter)

        primitive_pattern = PrimitivePattern(identifier=reference_factory.new())
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
    def search(start_primitive: Primitive, root: PrimitiveGroup, available_patterns: List[ParameterPattern], extrapolations: List[int], tolerance: float, reference_factory: ReferenceFactory = ReferenceFactory()) -> Tuple[Optional[InstancePattern], Optional[List[Primitive]]]:
        patterns = Pattern.search_group_recursive(root, available_patterns, tolerance, reference_factory)
        if patterns is None:
            return None, None

        primitives = Pattern.next([start_primitive], patterns, extrapolations)

        return patterns, primitives