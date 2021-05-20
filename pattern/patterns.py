from __future__ import annotations
from typing import *
from abc import *
import math

import numpy as np
from scipy.optimize import leastsq
from sklearn.metrics import mean_squared_error

from misc import util, default
from misc.util import Tolerance
from pattern.metaclasses import *
from gui.primitives import Primitive


class ParameterFlags:
    _none = 0
    _int = 1
    _float = 2
    _str = 4

    def __init__(self, parameters: Primitive.Parameters):
        self.value = ParameterFlags._none
        self.dtype = None
        for parameter in parameters:
            if isinstance(parameter, int):
                self.set_int()
            elif isinstance(parameter, float):
                self.set_float()
            elif isinstance(parameter, str):
                self.set_str()

    def has_int(self) -> bool:
        return self.value & ParameterFlags._int != 0

    def has_float(self) -> bool:
        return self.value & ParameterFlags._float != 0

    def has_str(self) -> bool:
        return self.value & ParameterFlags._str != 0

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
    def __init__(self, confidence: float, tolerance: Tolerance):
        self.confidence = confidence
        self.tolerance = tolerance
    @staticmethod
    @abstractmethod
    def name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def minimum_parameters() -> int:
        pass

    @staticmethod
    @abstractmethod
    def apply(parameters: np.ndarray[Primitive.Parameter], flags: ParameterFlags, tolerance: Tolerance = default.tolerance, _round: Optional[int] = None) -> Optional[ParameterPattern]:
        pass

    @abstractmethod
    def next(self, start: Optional[Primitive.Parameter], nth: int) -> Primitive.Parameter:
        pass

    @abstractmethod
    def dsl(self, _confidence: bool = False, _tolerance: bool = False) -> str:
        pass

    @staticmethod
    def calculate_confidence(parameters: np.ndarray[Primitive.Parameter], true_parameters: np.array, tolerance: Tolerance):
        mse = mean_squared_error(true_parameters, parameters)
        normalized_mse = mse / (1.0 + tolerance.absolute)
        return np.exp(-normalized_mse)

    @staticmethod
    def rounded(parameter: Union[Primitive.Parameter, Sequence[Primitive.Parameter]], value: Optional[int] = None):
        if value is not None:
            if isinstance(parameter, (int, float)):
                return round(parameter, value)
            elif isinstance(parameter, list):
                return [ParameterPattern.rounded(param, value) for param in parameter]

        return parameter

    @abstractmethod
    def weight(self) -> float:
        pass

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    @abstractmethod
    def __hash__(self) -> int:
        pass


class ConstantPattern(ParameterPattern, metaclass=MPattern.ConstantPattern):
    def __init__(self, value: Primitive.Parameter, confidence: float = default.confidence, tolerance: Tolerance = default.tolerance):
        super(ConstantPattern, self).__init__(confidence, tolerance)
        self.value: Primitive.Parameter = value

    def __str__(self) -> str:
        return "{}{}{}{}".format(
            self.name(),
            default.tokens[default.parameter_pattern_begin],
            self.value,
            default.tokens[default.parameter_pattern_end])

    def __repr__(self) -> str:
        return "{}[value={}, confidence={}, tolerance={}]".format(
            self.name(),
            self.value,
            self.confidence,
            self.tolerance)

    def __hash__(self):
        return hash((self.name(), self.value))

    def weight(self) -> float:
        return 1.8

    def dsl(self, _confidence: bool = False, _tolerance: bool = False) -> str:
        return "{}{}{}{}{}{}".format(
            self.name(),
            default.tokens[default.parameter_pattern_begin],
            self.value,
            "{} {}".format(default.tokens[default.value_separator], self.confidence) if _confidence else "",
            "{} {}".format(default.tokens[default.value_separator], self.tolerance) if _tolerance else "",
            default.tokens[default.parameter_pattern_end])

    @staticmethod
    def name() -> str:
        return "cte"

    @staticmethod
    def minimum_parameters() -> int:
        return 1

    @staticmethod
    def apply(parameters: np.ndarray[Primitive.Parameter], flags: ParameterFlags, tolerance: Tolerance = default.tolerance, _round: Optional[int] = None) -> Optional[ParameterPattern]:
        if flags.has_str():
            value = parameters[0]
            result = np.all(parameters == value)
        else:
            value = np.mean(parameters)
            result = np.allclose(parameters, value, rtol=tolerance.relative, atol=tolerance.absolute)

        if not result:
            return None

        if flags.has_str():
            confidence = 1.0
        else:
            true_parameters = np.full(parameters.shape, value, dtype=flags.dtype)
            confidence = ParameterPattern.calculate_confidence(parameters, true_parameters, tolerance)

        return ConstantPattern(ParameterPattern.rounded(value, _round), confidence, tolerance)

    def next(self, start: Optional[Primitive.Parameter], nth: int) -> Primitive.Parameter:
        if start is None:
            return self.value
        else:
            return start


class LinearPattern(ParameterPattern, metaclass=MPattern.LinearPattern):
    def __init__(self, start: Primitive.Parameter, delta: Primitive.Parameter, confidence: float = default.confidence, tolerance: Tolerance = default.tolerance):
        super(LinearPattern, self).__init__(confidence, tolerance)
        self.start: Primitive.Parameter = start
        self.delta: Primitive.Parameter = delta

    def __str__(self) -> str:
        return "{}{}{}{}{}{}".format(
            self.name(),
            default.tokens[default.parameter_pattern_begin],
            self.start,
            default.tokens[default.value_separator],
            self.delta,
            default.tokens[default.parameter_pattern_end])

    def __repr__(self) -> str:
        return "{}[delta={}, confidence={}, tolerance={}]".format(
            self.name(),
            self.delta,
            self.confidence,
            self.tolerance)

    def __hash__(self):
        return hash((self.name(), self.start, self.delta))

    def weight(self) -> float:
        return 1.3

    def dsl(self, _confidence: bool = False, _tolerance: bool = False) -> str:
        return "{}{}{}{}{}{}{}".format(
            self.name(),
            default.tokens[default.parameter_pattern_begin],
            self.start,
            "{} {}".format(default.tokens[default.value_separator], self.delta),
            "{} {}".format(default.tokens[default.value_separator], self.confidence) if _confidence else "",
            "{} {}".format(default.tokens[default.value_separator], self.tolerance) if _tolerance else "",
            default.tokens[default.parameter_pattern_end])

    @staticmethod
    def name() -> str:
        return "lin"

    @staticmethod
    def minimum_parameters() -> int:
        return 2

    @staticmethod
    def apply(parameters: np.ndarray[Primitive.Parameter], flags: ParameterFlags, tolerance: Tolerance = default.tolerance, _round: Optional[int] = None) -> Optional[ParameterPattern]:
        if flags.has_str():
            return None

        start = parameters[0]
        difference = np.ediff1d(parameters)
        value = np.mean(difference)
        result = np.allclose(difference, value, atol=tolerance.absolute, rtol=tolerance.relative)

        if not result:
            return None

        true_parameters = np.array([start + i * value for i in range(len(parameters))])
        confidence = ParameterPattern.calculate_confidence(parameters, true_parameters, tolerance)

        return LinearPattern(ParameterPattern.rounded(start, _round), ParameterPattern.rounded(value, _round), confidence, tolerance)

    def next(self, start: Primitive.Parameter, nth: int) -> Primitive.Parameter:
        if start is None:
            return self.start + nth * self.delta
        else:
            return start + nth * self.delta


class PeriodicPattern(ParameterPattern, metaclass=MPattern.PeriodicPattern):
    def __init__(self, pattern: Primitive.Parameters, confidence: float = default.confidence, tolerance: Tolerance = default.tolerance):
        super(PeriodicPattern, self).__init__(confidence, tolerance)
        self.pattern: Primitive.Parameters = pattern

    def __str__(self):
        return "{}{}".format(
            self.name(),
            util.format_list(self.pattern, str, default.tokens[default.parameter_pattern_begin], default.tokens[default.value_separator], default.tokens[default.parameter_pattern_end]))

    def __repr__(self):
        return "{}[pattern={}, confidence={}, tolerance={}]".format(
            self.name(),
            self.pattern,
            self.confidence,
            self.tolerance)

    def __hash__(self):
        return hash((self.name(), tuple(self.pattern)))

    def weight(self) -> float:
        return 1.2

    def dsl(self, _confidence: bool = False, _tolerance: bool = False) -> str:
        return "{}{}{}{}{}{}".format(
            self.name(),
            default.tokens[default.parameter_pattern_begin],
            util.format_list(self.pattern, str, '', default.tokens[default.value_separator], ''),
            "{} {}".format(default.tokens[default.value_separator], self.confidence) if _confidence else "",
            "{} {}".format(default.tokens[default.value_separator], self.tolerance) if _tolerance else "",
            default.tokens[default.parameter_pattern_end])

    @staticmethod
    def name() -> str:
        return "prd"

    @staticmethod
    def minimum_parameters():
        return 2

    @staticmethod
    def apply(parameters: np.ndarray[Primitive.Parameter], flags: ParameterFlags, tolerance: Tolerance = default.tolerance, _round: Optional[int] = None) -> Optional[ParameterPattern]:
        def equal(x, y):
            if flags.has_str():
                return x == y
            else:
                return util.equal_tolerant(x, y, tolerance)

        multiplicity = 1
        match_index = 0
        pattern: Primitive.Parameters = []

        for parameter in parameters:
            if len(pattern) == 0:
                pattern.append(parameter)
            else:
                if match_index == len(pattern):
                    multiplicity += 1
                    match_index = 0

                if equal(parameter, pattern[match_index]):
                    match_index += 1
                else:
                    pattern = pattern * multiplicity + pattern[:match_index] + [parameter]
                    multiplicity = 1
                    match_index = 0

        if multiplicity == 0:
            confidence = 0.5
        elif flags.has_str():
            confidence = 1.0
        else:
            true_parameters = (pattern * (multiplicity + 1))[:len(parameters)]

            confidence = ParameterPattern.calculate_confidence(parameters, true_parameters, tolerance)

        return PeriodicPattern(ParameterPattern.rounded(pattern, _round), confidence, tolerance)

    def next(self, start: Optional[Primitive.Parameter], nth: int) -> Primitive.Parameter:
        if any(isinstance(i, str) for i in [start, *self.pattern]):
            return self.pattern[nth % len(self.pattern)]

        if start is None:
            start = 0

        return start + self.pattern[nth % len(self.pattern)] - self.pattern[0]


class Operator:

    class Plus(object, metaclass=MOperator.Plus):
        @staticmethod
        def generate(parameters: np.ndarray[Primitive.Parameter]) -> np.ndarray[Primitive.Parameter]:
            return parameters[1:] + parameters[:-1]

        @staticmethod
        def next(delta: Primitive.Parameter, parameter: Primitive.Parameter) -> Primitive.Parameter:
            return delta - parameter

    class Min(object, metaclass=MOperator.Min):
        @staticmethod
        def generate(parameters: np.ndarray[Primitive.Parameter]) -> np.ndarray[Primitive.Parameter]:
            return np.ediff1d(parameters)

        @staticmethod
        def next(delta: Primitive.Parameter, parameter: Primitive.Parameter) -> np.ndarray[Primitive.Parameter]:
            return delta + parameter

    class Mul(object, metaclass=MOperator.Mul):
        @staticmethod
        def generate(parameters: np.ndarray[Primitive.Parameter]) -> np.ndarray[Primitive.Parameter]:
            return parameters[1:] * parameters[:-1]

        @staticmethod
        def next(delta: Primitive.Parameter, parameter: Primitive.Parameter) -> Primitive.Parameter:
            return delta / parameter

    class Div(object, metaclass=MOperator.Div):
        @staticmethod
        def generate(parameters: np.ndarray[Primitive.Parameter]) -> np.ndarray[Primitive.Parameter]:
            return parameters[1:] / parameters[:-1]

        @staticmethod
        def next(delta: Primitive.Parameter, parameter: Primitive.Parameter) -> np.ndarray[Primitive.Parameter]:
            return delta * parameter

    Operators = List[Union[Plus, Min, Mul, Div]]


class BFSOperatorPattern(ParameterPattern, metaclass=MPattern.OperatorPattern):
    zero_safe_operations = [Operator.Min, Operator.Plus]
    zero_unsafe_operations = [Operator.Min, Operator.Plus, Operator.Div, Operator.Mul]

    def __init__(self, operators: Operator.Operators, values: Primitive.Parameters, confidence: float = default.confidence, tolerance: Tolerance = default.tolerance):
        super(BFSOperatorPattern, self).__init__(confidence, tolerance)
        self.operators: Operator.Operators = operators
        self.values: Primitive.Parameters = values
        self._cache: List[float] = []

    def __str__(self) -> str:
        return "{}{}".format(
            self.name(),
            util.format_list(self.operators + self.values, str, default.tokens[default.parameter_pattern_begin], default.tokens[default.value_separator], default.tokens[default.parameter_pattern_end]))

    def __repr__(self) -> str:
        return "{}[type=BFS, operators={}, values={}, confidence={}, tolerance={}]".format(
            self.name(),
            self.operators,
            self.values,
            self.confidence,
            self.tolerance)

    def __hash__(self):
        return hash((self.name(), tuple(self.values), tuple(self.operators)))

    def weight(self) -> float:
        return 1.1

    def dsl(self, _confidence: bool = False, _tolerance: bool = False) -> str:
        return "{}{}{}{}{}{}".format(
            self.name(),
            default.tokens[default.parameter_pattern_begin],
            util.format_list(self.operators + self.values, str, '', default.tokens[default.value_separator], ''),
            "{} {}".format(default.tokens[default.value_separator], self.confidence) if _confidence else "",
            "{} {}".format(default.tokens[default.value_separator], self.tolerance) if _tolerance else "",
            default.tokens[default.parameter_pattern_end])

    @staticmethod
    def name() -> str:
        return "op"

    @staticmethod
    def minimum_parameters() -> int:
        return 3

    @staticmethod
    def apply(original_parameters: np.ndarray[Primitive.Parameter], flags: ParameterFlags, tolerance: Tolerance = default.tolerance, _round: Optional[int] = None) -> Optional[ParameterPattern]:
        if flags.has_str():
            return None

        def validate(pattern: BFSOperatorPattern) -> bool:
            parameter_reference = original_parameters
            parameter_min = parameter_reference.min(initial=0)
            parameter_max = parameter_reference.max(initial=0)
            n_start = len(parameter_reference)
            n_delta = 5
            tol = 1.5
            for extrapolation in range(n_start, n_start + n_delta):
                parameter_range = parameter_max - parameter_min

                parameter_next = pattern.next(parameter_reference[0], extrapolation)
                if parameter_next - parameter_reference[-1] > tol * parameter_range:
                    return False

                parameter_min = min(parameter_min, parameter_next)
                parameter_max = max(parameter_max, parameter_next)
                parameter_reference = np.append(parameter_reference, parameter_next)

            return True

        def expand_history(history, new_operator, new_parameter) -> Tuple[Operator.Operators, Primitive.Parameters]:
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
                new_parameters = original_parameters
            else:
                operation, parameters, history = queue.pop(0)
                new_parameters = operation.generate(parameters)

            if len(new_parameters) < 2:
                continue

            if util.all_same(new_parameters, tolerance):
                confidence = ParameterPattern.calculate_confidence(new_parameters, np.full(new_parameters.shape, new_parameters[0], flags.dtype), tolerance)
                operators, values = expand_history(history, None, new_parameters[0])

                pattern = BFSOperatorPattern(operators, ParameterPattern.rounded(values, _round), confidence, tolerance)
                if not validate(pattern):
                    return None

                return pattern

            if len(new_parameters) == 2:
                continue

            if any(new_parameter == 0 for new_parameter in new_parameters):
                operations = BFSOperatorPattern.zero_safe_operations
            else:
                operations = BFSOperatorPattern.zero_unsafe_operations

            for new_operation in operations:
                queue.append((new_operation, new_parameters, expand_history(history, new_operation, new_parameters[0])))

        return None

    def next(self, start: Optional[Primitive.Parameter], nth: int) -> Primitive.Parameter:
        # if nth < len(self._cache):
        #     return self._cache[nth]

        values = self.values.copy()

        for j in range(nth):
            for i in range(len(self.operators)):
                values[i] = self.operators[i].next(values[i + 1], values[i])

            # if j >= len(self._cache):
            #     self._cache.append(values[0])

        if start is None:
            return values[0]

        return start + values[0]


class SinusoidalPattern(ParameterPattern, metaclass=MPattern.SinusoidalPattern):
    def __init__(self, amplitude: float, frequency: float, phase: float, mean: float, confidence: float = default.confidence, tolerance: Tolerance = default.tolerance):
        super(SinusoidalPattern, self).__init__(confidence, tolerance)
        self.amplitude: float = amplitude
        self.frequency: float = frequency
        self.phase: float = phase
        self.mean: float = mean

    def __str__(self) -> str:
        return "{}{}".format(
            self.name(),
            util.format_list([self.amplitude, self.frequency, self.phase, self.mean], str, default.tokens[default.parameter_pattern_begin], default.tokens[default.value_separator], default.tokens[default.parameter_pattern_end]))

    def __repr__(self) -> str:
        return "{}[amp={}, freq={}, phase={}, mean={}, confidence={}, tolerance={}]".format(
            self.name(),
            self.amplitude,
            self.frequency,
            self.phase,
            self.mean,
            self.confidence,
            self.tolerance)

    def __hash__(self):
        return hash((self.name(), self.amplitude, self.frequency, self.phase, self.mean))

    def weight(self) -> float:
        return 1.0

    def dsl(self, _confidence: bool = False, _tolerance: bool = False) -> str:
        return "{}{}{}{}{}{}".format(
            self.name(),
            default.tokens[default.parameter_pattern_begin],
            util.format_list([self.amplitude, self.frequency, self.phase, self.mean], str, '', default.tokens[default.value_separator], ''),
            "{} {}".format(default.tokens[default.value_separator], self.confidence) if _confidence else "",
            "{} {}".format(default.tokens[default.value_separator], self.tolerance) if _tolerance else "",
            default.tokens[default.parameter_pattern_end])

    @staticmethod
    def name() -> str:
        return "sine"

    @staticmethod
    def minimum_parameters() -> int:
        return 4

    @staticmethod
    def apply(parameters: np.ndarray[Primitive.Parameter], flags: ParameterFlags, tolerance: Tolerance = default.tolerance, _round: Optional[int] = None) -> Optional[ParameterPattern]:
        if flags.has_str():
            return None

        t = np.array(range(len(parameters)))

        guess_mean = np.mean(parameters)
        guess_phase = 0
        guess_freq = 1
        guess_amp = 1
        est_amp, est_freq, est_phase, est_mean = leastsq(lambda x: x[0] * np.sin(x[1] * t + x[2]) + x[3] - parameters, np.array([guess_amp, guess_freq, guess_phase, guess_mean]))[0]
        true_sine = lambda x : est_amp * np.sin(est_freq * x + est_phase) + est_mean
        true_parameters = true_sine(t)
        confidence = ParameterPattern.calculate_confidence(parameters, true_parameters, tolerance)

        return SinusoidalPattern(ParameterPattern.rounded(est_amp, _round), ParameterPattern.rounded(est_freq, _round), ParameterPattern.rounded(est_phase, _round), ParameterPattern.rounded(est_mean, _round), confidence, tolerance)

    def next(self, start: Optional[Primitive.Parameter], nth: int) -> Primitive.Parameter:
        if start is None:
            return self.amplitude * math.sin(self.frequency * nth + self.phase) + self.mean

        return start + self.amplitude * math.sin(self.frequency * nth + self.phase) + self.mean


# class ILPPattern:
#     def __init__(self):
#         pass
#
#     def __repr__(self):
#         return "ILP[]"
#
#     @staticmethod
#     def apply(primitives: [Primitive], index):
#         if len(primitives) < 2:
#             return None
#
#         if min([primitive.arity for primitive in primitives]) <= index:
#             return None
#
#         knowledge = Knowledge()
#         name = primitives[0].name
#         arity = primitives[0].arity
#         primitive_type = c_type("primitive")
#         primitives_as_constants = [c_const(name + "_" + str(i), domain=primitive_type) for i in range(len(primitives))]
#
#         # Follows generation
#         follows = c_pred("follows", 2, domains=[primitive_type, primitive_type])
#         for i in range(len(primitives) - 1):
#             knowledge.add(follows(primitives_as_constants[i], primitives_as_constants[i + 1]))
#
#         unique_parameters_mapping = {}
#         parameter_type = c_type("parameter_type")
#         parameters = [primitive[index] for primitive in primitives]
#         for unique_parameter in set(parameters):
#             unique_parameters_mapping[unique_parameter] = c_const(unique_parameter, domain=parameter_type)
#
#         parameter_predicate = c_pred("parameter", 2, domains=[primitive_type, parameter_type])
#         for i in range(len(primitives)):
#             knowledge.add(parameter_predicate(primitives_as_constants[i], unique_parameters_mapping[parameters[i]]))
#
#         positive_examples = set()
#         negative_examples = set()
#         next_predicate = c_pred("next", 2, domains=[primitive_type, parameter_type])
#         for i in range(1,len(primitives) - 1):
#             positive_examples.add(next_predicate(primitives_as_constants[i], unique_parameters_mapping[parameters[i + 1]]))
#             negative_parameters_set = set(parameters)
#             negative_parameters_set.remove(parameters[i + 1])
#             for negative_parameter in negative_parameters_set:
#                 negative_examples.add(next_predicate(primitives_as_constants[i], unique_parameters_mapping[negative_parameter]))
#
#         task = Task(positive_examples=positive_examples, negative_examples=negative_examples)
#         solver = SWIProlog()
#         solver.retract_all()
#
#         # EvalFn must return an upper bound on quality to prune search space.
#         eval_fn1 = Coverage(return_upperbound=True)
#         # eval_fn2 = Compression(return_upperbound=True)
#         eval_fn3 = Accuracy(return_upperbound=True)
#
#         learners = [Aleph(solver, eval_fn, max_body_literals=4, do_print=True)
#                     for eval_fn in [eval_fn1, eval_fn3]]
#
#         for learner in learners:
#             res = learner.learn(task, knowledge, None, minimum_freq=1)
#             print(res)
#             prog = res["final_program"]
#             solver.assertz(prog)
#             print(solver.query(next_predicate(primitives_as_constants[-1], c_var("Color", domain=parameter_type))))
#
#
#     def next(self, primitives, nth=1, return_table=False):
#         return 0