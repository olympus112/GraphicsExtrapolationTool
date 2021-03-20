import math

from scipy.optimize import leastsq

from gui import util
from gui.primitives import Primitive
import numpy as np
from parsing.primitive_parser import Parser, Primitive
import pylab as plt

class LinearPattern:
    def __init__(self, index: int, delta: float, tolerance: float):
        self.index = index
        self.delta = delta
        self.tolerance = tolerance

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Linear[index={}, delta={}, tolerance={}]".format(self.index, self.delta, self.tolerance)

    @staticmethod
    def apply(primitives: [Primitive], index, delta=None, tolerance=0.1):
        if len(primitives) < 2:
            return None

        if min([primitive.arity for primitive in primitives]) <= index:
            return None

        if delta is None:
            delta = primitives[1][index] - primitives[0][index]

        for i in range(2, len(primitives)):
            if not util.equal_tolerant(primitives[i][index] - primitives[i - 1][index], delta, tolerance * delta):
                return None

        return LinearPattern(index, delta, tolerance)

    def next(self, primitives: [Primitive], nth=1):
        return primitives[-1][self.index] + nth * self.delta

class Operator:
    class Plus:
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "plus"

        @staticmethod
        def generate(parameters):
            return [parameters[i + 1] + parameters[i] for i in range(len(parameters) - 1)]

        @staticmethod
        def next(delta, parameter):
            return delta - parameter

    class Min:
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "min"

        @staticmethod
        def generate(parameters):
            return [parameters[i + 1] - parameters[i] for i in range(len(parameters) - 1)]

        @staticmethod
        def next(delta, parameter):
            return delta + parameter

    class Mul:
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "mul"

        @staticmethod
        def generate(parameters):
            return [parameters[i + 1] * parameters[i] for i in range(len(parameters) - 1)]

        @staticmethod
        def next(delta, parameter):
            return delta / parameter

    class Div:
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "div"

        @staticmethod
        def generate(parameters):
            return [parameters[i + 1] / parameters[i] for i in range(len(parameters) - 1)]

        @staticmethod
        def next(delta, parameter):
            return delta * parameter

class DFSOperatorPattern:
    def __init__(self, index, operators, values):
        self.index = index
        self.operators = operators
        self.values = values

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Operator[type=DFS, index={}, operators={}, values={}]".format(self.index, self.operators, self.values)

    @classmethod
    def apply(cls, primitives: [Primitive], index: int, tolerance: float = 0.1, limit=4):
        if len(primitives) < 2:
            return None

        if min([primitive.arity for primitive in primitives]) <= index:
            return None

        parameters = [primitive[index] for primitive in primitives]

        def search(parameters, stack = None, depth=0, limit=10):
            if stack is None:
                stack = []

            if len(parameters) < 2 or depth >= limit:
                return None

            if util.all_same(parameters, parameters[0] * tolerance):
                return stack, []

            if any(parameter == 0 for parameter in parameters):
                operations = [ Operator.Min, Operator.Plus ]
            else:
                operations = [ Operator.Min, Operator.Plus, Operator.Div, Operator.Mul ]

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

    def next(self, primitives, nth=1, return_table=False):
        values = self.values.copy()
        for _ in range(nth):
            for i in range(len(self.operators)):
                values[i + 1] = self.operators[-i - 1].next(values[i], values[i + 1])

        if return_table:
            return values

        return values[-1]

class BFSOperatorPattern:
    def __init__(self, index, operators, values):
        self.index = index
        self.operators = operators
        self.values = values

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Operator[type=BFS, index={}, operators={}, values={}]".format(self.index, self.operators, self.values)

    @staticmethod
    def apply(primitives: [Primitive], index: int, tolerance: float = 0.1):
        if len(primitives) < 2:
            return None

        if min([primitive.arity for primitive in primitives]) <= index:
            return None

        parameters = [primitive[index] for primitive in primitives]

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
                operations = [ Operator.Min, Operator.Plus ]
            else:
                operations = [ Operator.Min, Operator.Plus, Operator.Div, Operator.Mul ]

            for new_operation in operations:
                queue.append((new_operation, new_parameters, expand_history(history, new_operation, new_parameters[-1])))

        return None

    def next(self, primitives, nth=1, return_table=False):
        values = self.values.copy()
        for _ in range(nth):
            for i in range(len(self.operators) - 1, -1, -1):
                values[i] = self.operators[i].next(values[i + 1], values[i])

        if return_table:
            return values

        return values[0]

class SinusoidalPattern:
    def __init__(self, index, amp, freq, phase, mean):
        self.index = index
        self.amp = amp
        self.freq = freq
        self.phase = phase
        self.mean = mean

    @staticmethod
    def apply(primitives: [Primitive], index: int, tolerance: float = 0.1):
        if len(primitives) < 4:
            return None

        if min([primitive.arity for primitive in primitives]) <= index:
            return None

        parameters = [primitive[index] for primitive in primitives]
        t = np.array(range(len(parameters)))

        guess_mean = np.mean(parameters)
        guess_std = 3 * np.std(parameters) / (2 ** 0.5) / (2 ** 0.5)
        guess_phase = 0
        guess_freq = 1
        guess_amp = 1
        est_amp, est_freq, est_phase, est_mean = leastsq(lambda x: x[0] * np.sin(x[1] * t + x[2]) + x[3] - parameters, np.array([guess_amp, guess_freq, guess_phase, guess_mean]))[0]

        return SinusoidalPattern(index, est_amp, est_freq, est_phase, est_mean)

    def next(self, primitives, nth=1, return_table=False):
        return self.amp * math.sin(self.freq * nth + self.phase) + self.mean

class CircularPattern:
    def __init__(self, index_x, index_y, center, angle):
        self.index_x = index_x
        self.index_y = index_y
        self.center = center
        self.angle = angle

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Circular[index_x={}, index_y={}, center={}, angle={}]".format(self.index_x, self.index_y, self.center, self.angle)

    @staticmethod
    def apply(primitives: [Primitive], index_x: int, index_y, tolerance: float = 0.1):
        if len(primitives) < 3:
            return None

        if min([primitive.arity for primitive in primitives]) <= min(index_x, index_y):
            return None

        parameters_x = [primitive[index_x] for primitive in primitives]
        parameters_y = [primitive[index_y] for primitive in primitives]



    def next(self, primitives, nth=1, return_table=False):
        pass

        return 0

# pattern timeseries
if __name__ == '__main__':
    code = """
        p(0).
        p(0.5).
        p(1).
        p(0.5).
    """

    primitives = Parser.parse(code)
    SinusoidalPattern.apply(primitives, 0)