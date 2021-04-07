class DFSOperatorPattern(object, metaclass=MPattern.OperatorPattern):
    def __init__(self, operators, values):
        self.operators = operators
        self.values = values

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "Operator[type=DFS, operators={}, values={}]".format(str(self.operators), self.values)

    @staticmethod
    def minimum_parameters():
        return 3

    @staticmethod
    def apply(parameters: Sequence[Union[float, str, int]], flags: PatternFlags, tolerance: float = 0.1, limit: int = 4):
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
            return DFSOperatorPattern(*result)

        return None

    def next(self, parameters: Sequence[Union[float, str, int]], nth: int = 1, return_table=False):
        values = self.values.copy()
        for _ in range(nth):
            for i in range(len(self.operators)):
                values[i + 1] = self.operators[-i - 1].next(values[i], values[i + 1])

        if return_table:
            return values

        return values[-1]
