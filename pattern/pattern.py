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
    def dsl(self, _depth: int = 0, _identifier: bool = False, _confidence: bool = False, _tolerance: bool = False) -> str:
        pass

    def __len__(self) -> int:
        return 1


class NonePattern(InstancePattern):
    def __init__(self, identifier: Optional[ReferenceFactory.Reference] = None):
        super(NonePattern, self).__init__(identifier)

    def __str__(self) -> str:
        result = default.none

        return result

    def __repr__(self) -> str:
        result = "#{}none".format(self._identifier)

        return result

    def print(self, depth: int = 0, _format: Union[str, repr] = str):
        print("\t" * depth + _format(self))

    def dsl(self, _depth: int = 0, _identifier: bool = False, _confidence: bool = False, _tolerance: bool = False) -> str:
        return "{}{}{}".format(
            "\t" * _depth, "{}{}".format(default.tokens[default.identifier], self.identifier) if _identifier else "",
            default.none)


class PrimitivePattern(InstancePattern):
    Arity = int
    Arities = List[Arity]
    Selector = Union[str, int]
    Selectors = List[Selector]

    def __init__(self, patterns: Dict[Selector, ParameterPattern] = None, identifier: Optional[ReferenceFactory.Reference] = None, arities: Optional[Arities] = None):
        super(PrimitivePattern, self).__init__(identifier)
        self.patterns: Dict[PrimitivePattern.Selector, ParameterPattern] = patterns if patterns is not None else dict()
        if arities is not None:
            self.arities: PrimitivePattern.Arities = arities
        else:
            self.arities = [len(self.patterns)]

    def __str__(self) -> str:
        result = ""
        # result += "{}{}".format(default.tokens[default.identifier], self._identifier)
        result += util.format_list(
            ["{}{}{}".format(selector, default.tokens[default.selector], pattern) for selector, pattern in self.patterns.items()],
            str, default.tokens[default.primitive_pattern_begin], default.tokens[default.value_separator], default.tokens[default.primitive_pattern_end])

        return result

    def __repr__(self) -> str:
        result = "#{}".format(self._identifier)
        if self.parent is not None:
            result += "@{}".format(self.parent.identifier)
        result += util.format_list([self.patterns], repr, '[', ',', ']')

        return result

    def dsl(self, _depth: int = 0, _identifier: bool = False, _confidence: bool = False, _tolerance: bool = False) -> str:
        patterns = dict()
        for selector, pattern in self.patterns.items():
            if pattern not in patterns:
                patterns[pattern] = []

            patterns[pattern].append(selector)

        result = "{}{}{}{}".format(
            "\t" * _depth,
            "{}{}".format(default.tokens[default.identifier], self.identifier) if _identifier else "",
            "{}{}".format(default.tokens[default.arities], util.format_list(self.arities, str, "", default.tokens[default.value_separator], "", _inner_space="")) if self.arities is not None else "",
            util.format_list(
                ["{}{}{}".format(util.format_list(selectors, str, '', ',', '', '', ''), default.tokens[default.selector], pattern.dsl(_confidence, _tolerance)) for pattern, selectors in patterns.items()],
                str,
                default.tokens[default.primitive_pattern_begin],
                default.tokens[default.value_separator],
                default.tokens[default.primitive_pattern_end]))

        return result


    def print(self, depth: int = 0, _format: Union[str, repr] = str):
        print("\t" * depth + _format(self))

    def append(self, selector: PrimitivePattern.Selector, pattern: ParameterPattern):
        self.patterns[selector] = pattern

    """
    1, 2, 2
    p(1).
    p(1, 2).
    p(1, 3).
    
    2, 1, 2, 1
    p(1, 2).
    p(1).
    p(1, 4).
    p(1).
    """

    def next(self, start: Primitive, nths: Union[int, List[int]], named_primitives: Dict[Tuple[str, int], PrimitivePattern.Selectors], reference_factory: ReferenceFactory) -> List[Primitive]:
        primitives = [(self.patterns[default.name].next(start.name, nth), self.arities[nth % len(self.arities)]) for nth in nths]
        selectors = { selector for primitive in primitives for selector in named_primitives[primitive]}
        counts = {}
        totals = {}
        for selector in selectors:
            counts[selector] = [1 if selector in named_primitives[primitive] else 0 for primitive in primitives]
            totals[selector] = sum(counts[selector])

        def next_primitive(nth: int):
            name, arity = primitives[nth]
            parameters = [None for _ in range(arity)]
            for selector, pattern in self.patterns.items():
                if selector == default.name:
                    continue

                if isinstance(selector, int):
                    index = selector

                    if index >= arity:
                        continue
                else:
                    selectors = named_primitives[primitives[nth]]
                    if selector not in selectors:
                        continue

                    index = selectors.index(selector)
                    if index >= arity:
                        continue

                start_selectors = named_primitives[(start.name, start.arity)]
                if index >= start.arity or selector not in start_selectors:
                    pattern_start = None
                else:
                    pattern_start = start[index]

                size = len(counts[selector])
                div, rem = nth // size, nth % size
                parameter_nth = totals[selector] * div + sum(counts[selector][:rem])
                parameters[index] = pattern.next(pattern_start, parameter_nth) if pattern is not None else pattern_start

            return Primitive.from_list(reference_factory.new(), name, parameters)

        if isinstance(nths, int):
            return [next_primitive(nths)]

        return [next_primitive(nth) for nth in nths]


class GroupPattern(InstancePattern):
    def __init__(self, pattern: PrimitivePattern, identifier: Optional[ReferenceFactory.Reference] = None):
        super(GroupPattern, self).__init__(identifier)
        self.intergroup_pattern: PrimitivePattern = pattern
        self.intragroup_patterns: List[InstancePattern] = []
        self.intragroup_sizes: List[int] = []
        self.intragroup_size_pattern: Optional[ParameterPattern] = None

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

    def __len__(self) -> int:
        return len(self.intragroup_patterns)

    @InstancePattern.level.setter
    def level(self, value: int):
        if value >= 0:
            self._level = value

    def dsl(self, _depth: int = 0, _identifier: bool = False, _confidence: bool = False, _tolerance: bool = False) -> str:
        result = "{}{}{}{}{}{} {}\n{}\n{}".format(
            "\t" * _depth,
            "{}{}".format(default.tokens[default.identifier], self.identifier) if _identifier else "",
            # "{}{}".format(default.tokens[default.sizes], util.format_list(self.intragroup_sizes, str, "", default.tokens[default.value_separator], "", _inner_space="")),
            "{}{}".format(default.tokens[default.sizes], self.intragroup_size_pattern.dsl()),
            default.tokens[default.group_pattern_parent_begin],
            self.intergroup_pattern.dsl(0, _identifier, _confidence, _tolerance),
            default.tokens[default.group_pattern_parent_end],
            default.tokens[default.group_pattern_children_begin],
            "{}\n".format(default.tokens[default.value_separator]).join([intragroup_pattern.dsl(_depth + 1, _identifier, _confidence, _tolerance) for intragroup_pattern in self.intragroup_patterns]),
            "\t" * _depth + default.tokens[default.group_pattern_children_end])

        return result


    def print(self, depth: int = 0, _format: Union[str, repr] = str):
        print("\t" * depth + "#{}".format(self.identifier), end="")
        if self.parent is not None:
            print("@{}".format(self.parent.identifier), end="")
        print("(" + _format(self.intergroup_pattern) + ") {")
        for child in self.intragroup_patterns:
            child.print(depth + 1, _format)
        print("\t" * depth + "}")

    def append(self, *intragroup_patterns: Tuple[InstancePattern, int], _size_pattern: bool = True):
        for intragroup_pattern, intragroup_size in intragroup_patterns:
            if len(self.intragroup_patterns) == 0:
                self.level = intragroup_pattern.level + 1
            else:
                self.level = max(self.level, intragroup_pattern.level)

            self.intragroup_patterns.append(intragroup_pattern)
            self.intragroup_sizes.append(intragroup_size)

            self.intragroup_size_pattern = PeriodicPattern.apply(np.array(self.intragroup_sizes), ParameterFlags(self.intragroup_sizes), Tolerance(0, 0), 0)
            if _size_pattern:
                for pattern in [ConstantPattern, LinearPattern]:
                    result = pattern.apply(np.array(self.intragroup_sizes), ParameterFlags(self.intragroup_sizes), Tolerance(0, 0), 0)
                    if result is not None and result.confidence == 1.0:
                        self.intragroup_size_pattern = result
                        break

            intragroup_pattern.parent = self

    def next(self, start: Primitive, nths: Union[int, List[int]], named_primitives: Dict[Tuple[str, int], PrimitivePattern.Selectors],  reference_factory: ReferenceFactory) -> List[Primitive]:
        pass


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
    def next(start_primitives: List[Primitive], pattern: InstancePattern, named_primitives: Dict[Tuple[str, int], PrimitivePattern.Selectors], extrapolations: List[int], reference_factory: ReferenceFactory = ReferenceFactory()) -> List[Primitive]:
        assert pattern.level == len(extrapolations)

        extrapolation = extrapolations.pop(0)
        if isinstance(pattern, PrimitivePattern):
            result = []
            for start_primitive in start_primitives:
                result += pattern.next(start_primitive, list(range(extrapolation)), named_primitives, reference_factory)

            return result

        elif isinstance(pattern, GroupPattern):
            result = []
            for start_primitive in start_primitives:
                if pattern.intergroup_pattern is not None:
                    new_start_primitives = pattern.intergroup_pattern.next(start_primitive, list(range(extrapolation)), named_primitives, reference_factory)
                else:
                    new_start_primitives = [start_primitive]

                for index, new_start_primitive in enumerate(new_start_primitives):
                    new_extrapolations = extrapolations.copy()
                    new_extrapolations[0] += int(pattern.intragroup_size_pattern.next(pattern.intragroup_sizes[0], index) - 1)

                    result += Pattern.next([new_start_primitive], pattern[index % len(pattern.intragroup_patterns)], named_primitives, new_extrapolations, reference_factory)

            return result

        elif isinstance(pattern, NonePattern):
            return start_primitives

        else:
            raise Exception()

    @staticmethod
    def search_group_recursive(root: PrimitiveGroup, named_primitives: Dict[Tuple[str, int], PrimitivePattern.Selectors], available_patterns: List[ParameterPattern], tolerance: Tolerance, reference_factory: ReferenceFactory, _round: Optional[int] = None, _size_pattern: bool = True) -> Optional[InstancePattern]:
        if root is None:
            return None

        primitive_pattern = Pattern.search_group(root, named_primitives, available_patterns, tolerance, reference_factory, _round)
        pattern = primitive_pattern

        subpatterns = []
        for instance in root:
            if isinstance(instance, Primitive):
                subpatterns.append((NonePattern(reference_factory.new()), 1))
            elif isinstance(instance, PrimitiveGroup):
                subpattern = Pattern.search_group_recursive(instance, named_primitives, available_patterns, tolerance, reference_factory, _round, _size_pattern)
                if subpattern is None:
                    return None

                subpatterns.append((subpattern, len(instance)))
            else:
                raise Exception("Unknown type in group")

        if any(not isinstance(subpattern, NonePattern) for subpattern, _ in subpatterns):
            pattern = GroupPattern(primitive_pattern, reference_factory.new())
            pattern.append(*subpatterns, _size_pattern=_size_pattern)

        return pattern

    @staticmethod
    def search_group(group: PrimitiveGroup, named_primitives: Dict[Tuple[str, int], PrimitivePattern.Selectors], available_patterns: List[ParameterPattern], tolerance: Tolerance, reference_factory: ReferenceFactory, _round: Optional[int] = None) -> Optional[Union[PrimitivePattern, NonePattern]]:
        if group is None:
            print("Group is none")
            return None

        arity_list = []
        parameter_dict: Dict[PrimitivePattern.Selector, Primitive.Parameters] = { default.name: [] }
        for primitive in group:
            arity_list.append(primitive.master.arity)
            key = primitive.master.name, primitive.master.arity
            selectors = named_primitives[key] if key in named_primitives else list(range(primitive.master.arity))

            for index, selector in enumerate(selectors):
                if selector not in parameter_dict:
                    parameter_dict[selector] = []

                parameter_dict[selector].append(primitive.master[index])

            parameter_dict[default.name].append(primitive.master.name)

        if len(arity_list) > 0:
            flags = ParameterFlags(arity_list)
            arity_pattern: Optional[PeriodicPattern] = PeriodicPattern.apply(np.array(arity_list, dtype=flags.dtype), flags)
            if arity_pattern is not None:
                arity_list = [int(i) for i in arity_pattern.pattern]

        primitive_pattern = PrimitivePattern(arities=arity_list, identifier=reference_factory.new())

        for selector, parameters in parameter_dict.items():
            found_pattern = Pattern.search_parameters(parameters, available_patterns, tolerance, _round)

            if found_pattern is None:
                return NonePattern()

            primitive_pattern.append(selector, found_pattern)

        return primitive_pattern

    @staticmethod
    def search_parameters(parameters: Primitive.Parameters, available_patterns: List[ParameterPattern], tolerance: Tolerance, _round: Optional[int] = None) -> Optional[ParameterPattern]:
        parameter_count = len(parameters)
        flags = ParameterFlags(parameters)

        ranked_patterns: List[Tuple[float, ParameterPattern]] = []
        for available_pattern in available_patterns:
            if parameter_count < available_pattern.minimum_parameters():
                continue

            input_parameters = np.array(parameters, flags.dtype)
            if not flags.has_str():
                adjusted_tolerance = Tolerance(np.ptp(input_parameters) * tolerance.absolute, tolerance.relative)
            else:
                adjusted_tolerance = default.tolerance
            result = available_pattern.apply(input_parameters, flags, adjusted_tolerance, _round)
            if result is not None:
                # return result
                if result.confidence == 100.0:
                    return result
                else:
                    ranked_patterns.append((result.weight() * result.confidence, result))

        ranked_patterns.sort(key=lambda pattern: pattern[0], reverse=True)

        if len(ranked_patterns) == 0:
            return None

        return ranked_patterns[0][1]

    @staticmethod
    def search(start_primitive: Primitive, root: PrimitiveGroup, named_primitives: Dict[Tuple[str, int], PrimitivePattern.Selectors], available_patterns: List[ParameterPattern], extrapolations: List[int], tolerance: Tolerance, reference_factory: ReferenceFactory = ReferenceFactory(), _round: Optional[int] = None, _size_pattern: bool = True) -> Tuple[Optional[InstancePattern], Optional[List[Primitive]]]:
        patterns = Pattern.search_group_recursive(root, named_primitives, available_patterns, tolerance, reference_factory, _round, _size_pattern)
        if patterns is None:
            return None, None

        primitives = Pattern.next([start_primitive], patterns, named_primitives, extrapolations)

        return patterns, primitives