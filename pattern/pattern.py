import math
from typing import Sequence, Union

from scipy.optimize import leastsq
from pattern.metaclasses import *
from gui import util
import numpy as np

from loreleai.learning import Knowledge, Task
from loreleai.learning.eval_functions import Coverage, Compression, Accuracy
from loreleai.learning.learners import Aleph
from parsing.primitive_parser import Parser, Primitive

from pylo.engines import SWIProlog
from pylo.language.commons import c_type, c_pred, c_const, Clause, c_var

class Pattern:
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
            flags = PatternFlags(input_parameters)

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


class PatternFlags:
    _none = 0
    _int = 1
    _float = 2
    _str = 4

    def __init__(self, parameters: Sequence[Union[float, str, int]]):
        self.value = PatternFlags._none
        self.dtype = None
        for parameter in parameters:
            if isinstance(parameter, int):
                self.set_int()
            elif isinstance(parameter, float):
                self.set_float()
            elif isinstance(parameter, str):
                self.set_str()

    def has_int(self):
        return self.value & PatternFlags._int

    def has_float(self):
        return self.value & PatternFlags._float

    def has_str(self):
        return self.value & PatternFlags._str

    def set_int(self):
        self.value |= PatternFlags._int
        if self.dtype is None:
            self.dtype = int
        elif self.dtype == str:
            self.dtype = object

    def set_float(self):
        self.value |= PatternFlags._float
        if self.dtype is None or self.dtype == int:
            self.dtype = float
        elif self.dtype == str:
            self.dtype = object

    def set_str(self):
        self.value |= PatternFlags._str
        if self.dtype is None:
            self.dtype = str
        elif self.dtype == int or self.dtype == float:
            self.dtype = object


class ConstantPattern(object, metaclass=MPattern.ConstantPattern):
    def __init__(self, confidence: float, index: int, value, tolerance: float):
        self.confidence = confidence
        self.index = index
        self.value = value
        self.tolerance = tolerance

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Constant[confidence={}, index={}, value={}, tolerance={}]".format(self.confidence, self.index, self.value, self.tolerance)

    @staticmethod
    def minimum_parameters():
        return 2

    @staticmethod
    def apply(parameters: np.array, index: int, flags: PatternFlags, tolerance: float = 0.1):
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
            confidence = 1.0

        return ConstantPattern(confidence, index, value, tolerance)

    def next(self, parameters: np.array, nth: int = 1):
        return self.value

class LinearPattern(object, metaclass=MPattern.LinearPattern):
    def __init__(self, confidence: float, index: int, delta: float, tolerance: float):
        self.confidence = confidence
        self.index = index
        self.delta = delta
        self.tolerance = tolerance

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Linear[confidence={}, index={}, delta={}, tolerance={}]".format(self.confidence, self.index, self.delta, self.tolerance)

    @staticmethod
    def minimum_parameters():
        return 2

    @staticmethod
    def apply(parameters: np.array([Union[float, str, int]]), index: int, flags: PatternFlags, tolerance: float = 0.1):
        if flags.has_str():
            return None

        delta = parameters[1] - parameters[0]

        for i in range(2, len(parameters)):
            if not util.equal_tolerant(parameters[i - 1] + delta, parameters[i], abs(tolerance * delta)):
                return None

        confidence = 1.0

        return LinearPattern(confidence, index, delta, tolerance)

    def next(self, parameters: Sequence[Union[float, str, int]], nth: int = 1):
        return parameters[0] + (len(parameters) - 1 + nth) * self.delta


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


class DFSOperatorPattern(object, metaclass=MPattern.OperatorPattern):
    def __init__(self, index, operators, values):
        self.index = index
        self.operators = operators
        self.values = values

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Operator[type=DFS, index={}, operators={}, values={}]".format(self.index, str(self.operators), self.values)

    @staticmethod
    def minimum_parameters():
        return 3

    @staticmethod
    def apply(parameters: Sequence[Union[float, str, int]], index: int, flags: PatternFlags, tolerance: float = 0.1, limit: int = 4):
        if flags.has_str():
            return None

        def search(parameters, stack=None, depth=0, limit=10):
            if stack is None:
                stack = []

            if len(parameters) < 2 or depth >= limit:
                return None

            if util.all_same(parameters, parameters[0] * tolerance):
                return stack, []

            if any(parameter == 0 for parameter in parameters):
                operations = [Operator.Min, Operator.Plus]
            else:
                operations = [Operator.Min, Operator.Plus, Operator.Div, Operator.Mul]

            if len(parameters) == 2:
                return None

            for operation in operations:
                new_parameters = operation.generate(parameters)

                stack.append(operation)

                result = search(new_parameters, stack, depth + 1)
                if result is not None:
                    result[1].append(new_parameters[-1])
                    return result

                stack.pop()

            return None

        result = search(parameters, None, 0, limit)
        if result is not None:
            result[1].append(parameters[-1])
            return DFSOperatorPattern(index, *result)

        return None

    def next(self, parameters: Sequence[Union[float, str, int]], nth: int = 1, return_table=False):
        values = self.values.copy()
        for _ in range(nth):
            for i in range(len(self.operators)):
                values[i + 1] = self.operators[-i - 1].next(values[i], values[i + 1])

        if return_table:
            return values

        return values[-1]


class BFSOperatorPattern(object, metaclass=MPattern.OperatorPattern):
    def __init__(self, index, operators, values):
        self.index = index
        self.operators = operators
        self.values = values

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Operator[type=BFS, index={}, operators={}, values={}]".format(self.index, self.operators, self.values)

    @staticmethod
    def minimum_parameters():
        return 3

    @staticmethod
    def apply(parameters: Sequence[Union[float, str, int]], index: int, flags: PatternFlags, tolerance: float = 0.1):
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
                return BFSOperatorPattern(index, *expand_history(history, None, new_parameters[-1]))

            if len(new_parameters) == 2:
                continue

            if any(new_parameter == 0 for new_parameter in new_parameters):
                operations = [Operator.Min, Operator.Plus]
            else:
                operations = [Operator.Min, Operator.Plus, Operator.Div, Operator.Mul]

            for new_operation in operations:
                queue.append(
                    (new_operation, new_parameters, expand_history(history, new_operation, new_parameters[-1])))

        return None

    def next(self, parameters: Sequence[Union[float, str, int]], nth: int = 1, return_table: bool = False):
        values = self.values.copy()
        for _ in range(nth):
            for i in range(len(self.operators) - 1, -1, -1):
                values[i] = self.operators[i].next(values[i + 1], values[i])

        if return_table:
            return values

        return values[0]


class SinusoidalPattern(object, metaclass=MPattern.SinusoidalPattern):
    def __init__(self, confidence, index, amp, freq, phase, mean):
        self.confidence = confidence
        self.index = index
        self.amp = amp
        self.freq = freq
        self.phase = phase
        self.mean = mean

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Sinus[index={}, amp={}, freq={}, phase={}, mean={}]".format(self.index, self.amp, self.freq, self.phase, self.mean)

    @staticmethod
    def minimum_parameters():
        return 4

    @staticmethod
    def apply(parameters: Sequence[Union[float, str, int]], index: int, flags: PatternFlags, tolerance: float = 0.1):
        if flags.has_str():
            return None

        t = np.array(range(len(parameters)))

        guess_mean = np.mean(parameters)
        guess_std = 3 * np.std(parameters) / (2 ** 0.5) / (2 ** 0.5)
        guess_phase = 0
        guess_freq = 1
        guess_amp = 1
        est_amp, est_freq, est_phase, est_mean = leastsq(lambda x: x[0] * np.sin(x[1] * t + x[2]) + x[3] - parameters,
                                                         np.array([guess_amp, guess_freq, guess_phase, guess_mean]))[0]
        confidence = 1.0

        return SinusoidalPattern(confidence, index, est_amp, est_freq, est_phase, est_mean)

    def next(self, parameters: Sequence[Union[float, str, int]], nth: int = 1):
        return self.amp * math.sin(self.freq * nth + self.phase) + self.mean


class PeriodicPattern(object, metaclass=MPattern.PeriodicPattern):
    def __init__(self, index, pattern):
        self.index = index
        self.pattern = pattern

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Period[index={}, pattern={}]".format(self.index, self.pattern)

    @staticmethod
    def minimum_parameters():
        return 2

    @staticmethod
    def apply(parameters: Sequence[Union[float, str, int]], index: int, flags: PatternFlags, tolerance: float = 0.1):
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

        # if multiplicity == 0:
        #     return None

        return PeriodicPattern(index, pattern)

    def next(self, parameters: Sequence[Union[float, str, int]], nth: int = 1):
        return self.pattern[(len(parameters) + nth) % len(self.pattern) - 1]

class CircularPattern(object, metaclass=MPattern.CircularPattern):
    def __init__(self, index_x, index_y, center, angle):
        self.index_x = index_x
        self.index_y = index_y
        self.center = center
        self.angle = angle

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Circular[index_x={}, index_y={}, center={}, angle={}]".format(self.index_x, self.index_y, self.center,
                                                                              self.angle)

    @staticmethod
    def apply(primitives: [Primitive], index_x: int, index_y, tolerance: float = 0.1):
        if len(primitives) < 3:
            return None

        if min([primitive.arity for primitive in primitives]) <= min(index_x, index_y):
            return None

        parameters_x = [primitive[index_x] for primitive in primitives]
        parameters_y = [primitive[index_y] for primitive in primitives]

    def next(self, parameters: Sequence[Union[float, str, int]], nth: int = 1):
        return 0

class ILPPattern:
    def __init__(self, index):
        self.index = index

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "ILP[index={}]".format(self.index)

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


# pattern timeseries
# if __name__ == '__main__':
#     block = c_type("block")
#     col = c_type("col")
#
#     block1 = c_const("block1", domain=block)  # blue -> positive
#     block2 = c_const("block2", domain=block)  # red
#     block3 = c_const("block3", domain=block)  # green -> positive
#     block4 = c_const("block4", domain=block)  # red -> positive
#     block5 = c_const("block5", domain=block)  # red
#     block6 = c_const("block6", domain=block)  # green
#     block7 = c_const("block7", domain=block)  # blue
#     block8 = c_const("block8", domain=block)  # blue
#
#     red = c_const("red", domain="col")
#     green = c_const("green", domain="col")
#     blue = c_const("blue", domain="col")
#
#     follows = c_pred("follows", 2, domains=[block, block])
#     color = c_pred("color", 2, domains=[block, col])
#
#     # Predicate to learn:
#     f = c_pred("f", 1, domains=[block])
#
#     bk = Knowledge(
#         follows(block1, block2), follows(block2, block3), follows(block3, block4),
#         follows(block4, block5), follows(block5, block6), follows(block6, block7),
#         follows(block7, block8), color(block1, blue), color(block2, red),
#         color(block3, green), color(block4, red), color(block5, red),
#         color(block6, green), color(block7, blue), color(block8, blue)
#     )
#
#     pos = {f(x) for x in [block1, block3, block4]}
#     neg = {f(x) for x in [block2, block5, block6, block7, block8]}
#
#     task = Task(positive_examples=pos, negative_examples=neg)
#     solver = SWIProlog()
#
#     # EvalFn must return an upper bound on quality to prune search space.
#     eval_fn1 = Coverage(return_upperbound=True)
#     eval_fn2 = Compression(return_upperbound=True)
#     eval_fn3 = Accuracy(return_upperbound=True)
#
#     learners = [Aleph(solver, eval_fn, max_body_literals=4, do_print=False)
#                 for eval_fn in [eval_fn1, eval_fn3]]
#
#     for learner in learners:
#         res = learner.learn(task, bk, None, minimum_freq=1)
#         print(res)

if __name__ == '__main__':
    code = """
    p(1).
    p(1).
    p(1).
    p(1.35).
    """

    primitives = Parser.parse(code)
    print(Pattern.search(primitives, 3, 0.4))