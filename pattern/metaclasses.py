class MPattern:
    class ConstantPattern(type):
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "Constant"

    class LinearPattern(type):
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "Linear"

    class OperatorPattern(type):
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "Operator"

    class SinusoidalPattern(type):
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "Sinus"

    class PeriodicPattern(type):
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "Periodic"

    class CircularPattern(type):
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "Circular"

class MOperator:
    class Plus(type):
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "+"

    class Min(type):
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "-"

    class Mul(type):
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "*"

    class Div(type):
        def __str__(self):
            return repr(self)

        def __repr__(self):
            return "/"