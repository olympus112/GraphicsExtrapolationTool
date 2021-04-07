import math
from typing import Sequence, Union, Optional, Dict
from abc import *

from scipy.optimize import leastsq
from metaclasses import *
from gui import util
import numpy as np

from parsing.primitive_parser import Parser, Primitive
# from loreleai.learning import Knowledge, Task
# from loreleai.learning.eval_functions import Coverage, Compression, Accuracy
# from loreleai.learning.learners import Aleph
# from pylo.engines import SWIProlog
# from pylo.language.commons import c_type, c_pred, c_const, Clause, c_var
from loreleai.learning import Knowledge, Task
from loreleai.learning.eval_functions import Coverage, Compression, Accuracy
from loreleai.learning.learners import Aleph
from parsing.primitive_parser import Parser, Primitive, Group


class ParameterFlags:
    _none = 0
    _int = 1
    _float = 2
    _str = 4

    def __init__(self, parameters: Sequence[Union[float, str, int]]):
        self.value = ParameterFlags._none
        self.dtype = None
        for parameter in parameters:
            if isinstance(parameter, int):
                self.set_int()
            elif isinstance(parameter, float):
                self.set_float()
            elif isinstance(parameter, str):
                self.set_str()

    def has_int(self):
        return self.value & ParameterFlags._int

    def has_float(self):
        return self.value & ParameterFlags._float

    def has_str(self):
        return self.value & ParameterFlags._str

    def set_int(self):
        self.value |= ParameterFlags._int
        if self.dtype is None:
            self.dtype = int
        elif self.dtype == str:
            self.dtype = object

    def set_float(self):
        self.value |= ParameterFlags._float
        if self.dtype is None or self.dtype == int:
            self.dtype = float
        elif self.dtype == str:
            self.dtype = object

    def set_str(self):
        self.value |= ParameterFlags._str
        if self.dtype is None:
            self.dtype = str
        elif self.dtype == int or self.dtype == float:
            self.dtype = object


class ParameterPattern:
    @staticmethod
    @abstractmethod
    def minimum_parameters():
        pass

    @staticmethod
    @abstractmethod
    def apply(parameters: np.array, flags: ParameterFlags, tolerance: float = 0.1):
        pass

    @abstractmethod
    def next(self, nth: int):
        pass


class ConstantPattern(ParameterPattern, metaclass=MPattern.ConstantPattern):
    def __init__(self, confidence: float, value, tolerance: float):
        self.confidence = confidence
        self.value = value
        self.tolerance = tolerance

    def __str__(self):
        return "Constant[{}]".format(self.value)

    def __repr__(self):
        return "Constant[confidence={}, value={}, tolerance={}]".format(self.confidence, self.value, self.tolerance)

    @staticmethod
    def minimum_parameters():
        return 2

    @staticmethod
    def apply(parameters: np.array, flags: ParameterFlags, tolerance: float = 0.1):
        value = parameters[0]
        for i in range(1, len(parameters)):
            if flags.has_str():
                if not parameters[i] == value:
                    return None
            else:
                if not util.equal_tolerant(parameters[i], value, tolerance):
                    return None

        if flags.has_str():
            confidence = 1.0
        else:
            true_parameters = np.full(len(parameters), value, dtype=flags.dtype)
            confidence = Pattern.confidence(parameters, true_parameters, tolerance)

        return ConstantPattern(confidence, value, tolerance)

    def next(self, nth: int):
        return self.value


class LinearPattern(ParameterPattern, metaclass=MPattern.LinearPattern):
    def __init__(self, confidence: float, start: float, delta: float, tolerance: float):
        self.confidence = confidence
        self.start = start
        self.delta = delta
        self.tolerance = tolerance

    def __str__(self):
        return "Linear[{}+{}]".format(self.start, self.delta)

    def __repr__(self):
        return "Linear[confidence={}, start={}, delta={}, tolerance={}]".format(self.confidence, self.start, self.delta, self.tolerance)

    @staticmethod
    def minimum_parameters():
        return 2

    @staticmethod
    def apply(parameters: np.array([Union[float, str, int]]), flags: ParameterFlags, tolerance: float = 0.1):
        if flags.has_str():
            return None

        start = parameters[0]
        delta = parameters[1] - parameters[0]

        for i in range(2, len(parameters)):
            if not util.equal_tolerant(parameters[i - 1] + delta, parameters[i], abs(tolerance * delta)):
                return None

        true_parameters = np.arange(start, start + len(parameters) * delta, delta)
        confidence = Pattern.confidence(parameters, true_parameters, tolerance)

        return LinearPattern(confidence, start, delta, tolerance)

    def next(self, nth: int):
        return self.start + nth * self.delta


class PeriodicPattern(ParameterPattern, metaclass=MPattern.PeriodicPattern):
    def __init__(self, confidence: float, pattern: []):
        self.confidence = confidence
        self.pattern = pattern

    def __str__(self):
        return "Period{}".format(self.pattern)

    def __repr__(self):
        return "Period[confidence={}, pattern={}]".format(self.confidence, self.pattern)

    @staticmethod
    def minimum_parameters():
        return 2

    @staticmethod
    def apply(parameters: np.array, flags: ParameterFlags, tolerance: float = 0.1):
        def equal(x, y):
            if flags.has_str():
                return x == y
            else:
                return util.equal_tolerant(x, y, tolerance)

        multiplicity = 0
        match_index = 0
        pattern = []

        for parameter in parameters:
            if len(pattern) == 0:
                pattern.append(parameter)
            else:
                if match_index == len(pattern):
                    multiplicity += 1
                    match_index = 0

                if equal(parameter, pattern[match_index]):
                    if match_index == 0:
                        multiplicity += 1
                    match_index += 1
                else:
                    pattern += pattern * (multiplicity - 1)
                    pattern += pattern[:match_index]
                    pattern.append(parameter)
                    multiplicity = 0
                    match_index = 0

        if multiplicity == 0:
            confidence = 0.5
        elif flags.has_str():
            confidence = 1.0
        else:
            true_parameters = pattern * multiplicity + pattern[:len(parameters) % len(pattern)]
            confidence = Pattern.confidence(parameters, true_parameters, tolerance)

        return PeriodicPattern(confidence, pattern)

    def next(self, nth: int):
        return self.pattern[nth % len(self.pattern) - 1]


class Operator:
    class Plus(object, metaclass=MOperator.Plus):
        @staticmethod
        def generate(parameters):
            return [parameters[i + 1] + parameters[i] for i in range(len(parameters) - 1)]

        @staticmethod
        def next(delta, parameter):
            return delta - parameter

    class Min(object, metaclass=MOperator.Min):
        @staticmethod
        def generate(parameters):
            return [parameters[i + 1] - parameters[i] for i in range(len(parameters) - 1)]

        @staticmethod
        def next(delta, parameter):
            return delta + parameter

    class Mul(object, metaclass=MOperator.Mul):
        @staticmethod
        def generate(parameters):
            return [parameters[i + 1] * parameters[i] for i in range(len(parameters) - 1)]

        @staticmethod
        def next(delta, parameter):
            return delta / parameter

    class Div(object, metaclass=MOperator.Div):
        @staticmethod
        def generate(parameters):
            return [parameters[i + 1] / parameters[i] for i in range(len(parameters) - 1)]

        @staticmethod
        def next(delta, parameter):
            return delta * parameter


class BFSOperatorPattern(object, metaclass=MPattern.OperatorPattern):
    def __init__(self, operators, values):
        self.operators = operators
        self.values = values

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Operator[type=BFS, operators={}, values={}]".format(self.operators, self.values)

    @staticmethod
    def minimum_parameters():
        return 3

    @staticmethod
    def apply(parameters: Sequence[Union[float, str, int]], flags: ParameterFlags, tolerance: float = 0.1):
        if flags.has_str():
            return None

        def expand_history(history, new_operator, new_parameter):
            if history is None:
                new_operators, new_parameters = [], []
            else:
                new_operators, new_parameters = history[0].copy(), history[1].copy()
            if new_operator is not None:
                new_operators.append(new_operator)
            if new_parameter is not None:
                new_parameters.append(new_parameter)
            return new_operators, new_parameters

        queue = []
        init = True
        while len(queue) != 0 or init:
            if init:
                init = False
                history = None
                new_parameters = parameters
            else:
                operation, parameters, history = queue.pop(0)
                new_parameters = operation.generate(parameters)

            if len(new_parameters) < 2:
                continue

            if util.all_same(new_parameters, new_parameters[0] * tolerance):
                return BFSOperatorPattern(*expand_history(history, None, new_parameters[-1]))

            if len(new_parameters) == 2:
                continue

            if any(new_parameter == 0 for new_parameter in new_parameters):
                operations = [Operator.Min, Operator.Plus]
            else:
                operations = [Operator.Min, Operator.Plus, Operator.Div, Operator.Mul]

            for new_operation in operations:
                queue.append((new_operation, new_parameters, expand_history(history, new_operation, new_parameters[-1])))

        return None

    def next(self, parameters: Sequence[Union[float, str, int]], nth: int = 1):
        values = self.values.copy()
        for _ in range(nth):
            for i in range(len(self.operators) - 1, -1, -1):
                values[i] = self.operators[i].next(values[i + 1], values[i])

        return values[0]


class SinusoidalPattern(object, metaclass=MPattern.SinusoidalPattern):
    def __init__(self, confidence, amp, freq, phase, mean):
        self.confidence = confidence
        self.amp = amp
        self.freq = freq
        self.phase = phase
        self.mean = mean

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Sinus[amp={}, freq={}, phase={}, mean={}]".format(self.amp, self.freq, self.phase, self.mean)

    @staticmethod
    def minimum_parameters():
        return 4

    @staticmethod
    def apply(parameters: Sequence[Union[float, str, int]], flags: ParameterFlags, tolerance: float = 0.1):
        if flags.has_str():
            return None

        t = np.array(range(len(parameters)))

        guess_mean = np.mean(parameters)
        guess_std = 3 * np.std(parameters) / (2 ** 0.5) / (2 ** 0.5)
        guess_phase = 0
        guess_freq = 1
        guess_amp = 1
        est_amp, est_freq, est_phase, est_mean = leastsq(lambda x: x[0] * np.sin(x[1] * t + x[2]) + x[3] - parameters, np.array([guess_amp, guess_freq, guess_phase, guess_mean]))[0]
        confidence = 1.0

        return SinusoidalPattern(confidence, est_amp, est_freq, est_phase, est_mean)

    def next(self, parameters: Sequence[Union[float, str, int]], nth: int = 1):
        return self.amp * math.sin(self.freq * nth + self.phase) + self.mean


class CircularPattern(object, metaclass=MPattern.CircularPattern):
    def __init__(self, center, angle):
        self.center = center
        self.angle = angle

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Circular[center={}, angle={}]".format(self.center, self.angle)

    @staticmethod
    def apply(primitives: [Primitive], tolerance: float = 0.1):
        pass

    def next(self, parameters: Sequence[Union[float, str, int]], nth: int = 1):
        return 0


class ILPPattern:
    def __init__(self):
        pass


    def __repr__(self):
        return "ILP[]"

    @staticmethod
    def apply(primitives: [Primitive], index):
        if len(primitives) < 2:
            return None

        if min([primitive.arity for primitive in primitives]) <= index:
            return None

        knowledge = Knowledge()
        name = primitives[0].name
        arity = primitives[0].arity
        primitive_type = c_type("primitive")
        primitives_as_constants = [c_const(name + "_" + str(i), domain=primitive_type) for i in range(len(primitives))]

        # Follows generation
        follows = c_pred("follows", 2, domains=[primitive_type, primitive_type])
        for i in range(len(primitives) - 1):
            knowledge.add(follows(primitives_as_constants[i], primitives_as_constants[i + 1]))

        unique_parameters_mapping = {}
        parameter_type = c_type("parameter_type")
        parameters = [primitive[index] for primitive in primitives]
        for unique_parameter in set(parameters):
            unique_parameters_mapping[unique_parameter] = c_const(unique_parameter, domain=parameter_type)

        parameter_predicate = c_pred("parameter", 2, domains=[primitive_type, parameter_type])
        for i in range(len(primitives)):
            knowledge.add(parameter_predicate(primitives_as_constants[i], unique_parameters_mapping[parameters[i]]))

        positive_examples = set()
        negative_examples = set()
        next_predicate = c_pred("next", 2, domains=[primitive_type, parameter_type])
        for i in range(1,len(primitives) - 1):
            positive_examples.add(next_predicate(primitives_as_constants[i], unique_parameters_mapping[parameters[i + 1]]))
            negative_parameters_set = set(parameters)
            negative_parameters_set.remove(parameters[i + 1])
            for negative_parameter in negative_parameters_set:
                negative_examples.add(next_predicate(primitives_as_constants[i], unique_parameters_mapping[negative_parameter]))

        task = Task(positive_examples=positive_examples, negative_examples=negative_examples)
        solver = SWIProlog()
        solver.retract_all()

        # EvalFn must return an upper bound on quality to prune search space.
        eval_fn1 = Coverage(return_upperbound=True)
        # eval_fn2 = Compression(return_upperbound=True)
        eval_fn3 = Accuracy(return_upperbound=True)

        learners = [Aleph(solver, eval_fn, max_body_literals=4, do_print=True)
                    for eval_fn in [eval_fn1, eval_fn3]]

        for learner in learners:
            res = learner.learn(task, knowledge, None, minimum_freq=1)
            print(res)
            prog = res["final_program"]
            solver.assertz(prog)
            print(solver.query(next_predicate(primitives_as_constants[-1], c_var("Color", domain=parameter_type))))


    def next(self, primitives, nth=1, return_table=False):
        pass

        return 0


class PrimitivePattern:
    def __init__(self, *patterns):
        self.patterns: Sequence[ParameterPattern] = [*patterns]
        self.reference = None

    def __str__(self):
        return "#{}".format(self.reference) + ", ".join(list(map(str, self.patterns))).join(['[', ']'])

    def __repr__(self):
        return "#{}".format(self.reference) + ", ".join(list(map(repr, self.patterns))).join(['[', ']'])

    def print(self, depth: int = 0, _format=str):
        print("\t" * depth + _format(self))

    def append(self, *patterns: ParameterPattern):
        self.patterns += patterns

    def set_reference(self, reference: int):
        self.reference = reference

    def next(self, nth: int) -> Primitive:
        parameters = []
        for pattern in self.patterns:
            parameters.append(pattern.next(nth))

        return Parser.create_primitive(parameters[0], len(parameters) - 1, parameters[1:])

class Pattern:
    references: Dict[int, Primitive] = dict()

    def __init__(self, pattern: PrimitivePattern):
        self.pattern: PrimitivePattern = pattern
        self.subpatterns: Sequence[Union[Pattern, PrimitivePattern]] = []

    def __str__(self):
        return str(self.pattern) + ", ".join(list(map(str, self.subpatterns))).join(['{', '}'])

    def __repr__(self):
        return repr(self.pattern) + ", ".join(list(map(repr, self.subpatterns))).join(['{', '}'])

    def print(self, depth: int = 0, _format=str):
        print("\t" * depth + _format(self.pattern))
        for subpattern in self.subpatterns:
            subpattern.print(depth + 1, _format)

    def append(self, *subpatterns):
        self.subpatterns += subpatterns

    def next(self, nth: int):
        pass

    @staticmethod
    def search_group_recursive(root: Group, available_patterns: Sequence, tolerance: float):
        primitive_pattern = Pattern.search_group(root, available_patterns, tolerance)
        group_pattern = primitive_pattern

        for group in root:
            if not isinstance(group, Group):
                continue

            primitive_subpattern = Pattern.search_group_recursive(group, available_patterns, tolerance)
            if primitive_subpattern is None:
                return None

            if group_pattern is primitive_pattern:
                group_pattern = Pattern(primitive_pattern)

            group_pattern.append(primitive_subpattern)

        return group_pattern

    @staticmethod
    def search_group(group: Group, available_patterns: Sequence, tolerance: float) -> Optional[PrimitivePattern]:
        parameters_list = [[] for _ in range(group.max_arity() + 1)]
        for primitive in group:
            parameters_list[0].append(primitive.master().name)
            for parameter_index, parameter in enumerate(primitive.master().parameters):
                parameters_list[parameter_index + 1].append(parameter)

        patterns = PrimitivePattern()
        for parameters in parameters_list:
            pattern = Pattern.search_parameters(parameters, available_patterns, tolerance)
            if pattern is None:
                return None

            patterns.append(pattern)

        patterns.set_reference(group.master().reference)

        return patterns

    @staticmethod
    def search_parameters(parameters: Sequence[Union[str, int, float]], available_patterns: Sequence, tolerance: float):
        parameter_count = len(parameters)
        flags = ParameterFlags(parameters)

        for pattern in available_patterns:
            if parameter_count < pattern.minimum_parameters():
                continue

            input_parameters = np.array(parameters, flags.dtype)
            result = pattern.apply(input_parameters, flags, tolerance)
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

    @staticmethod
    def confidence(parameters: np.array, true_parameters: np.array, tolerance: float):
        return np.exp(-np.sqrt(np.average(np.square((parameters - true_parameters) / tolerance))) / (1.0 + tolerance))

if __name__ == '__main__':
    code1 = """
    {{p(1). p(2).} {p(3).p(3).}}
    {p(4). {p(5). p(6).}}
    """
    code2 = """
        {rect(0, 0, 10, 10). rect(20, 0, 10, 10).}
        {rect(0, 20, 10, 10). rect(20, 20, 10, 10).}
        rect(0, 40, 10, 10).
    """
    code3 = """
        p(0, 0).p(0, 1).
    """
    Pattern.search_group_recursive(Parser.parse(code1), [ConstantPattern, LinearPattern], 0.1).print()
    Pattern.search_group_recursive(Parser.parse(code2), [ConstantPattern, LinearPattern], 0.1).print()
    Pattern.search_group_recursive(Parser.parse(code3), [ConstantPattern, LinearPattern], 0.1).print()
