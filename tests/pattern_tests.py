from unittest import TestCase

from parsing.primitive_parser import PrimitiveParser
from pattern.pattern import Pattern
from pattern.patterns import *


class PatternTests(TestCase):
    def test_pattern(self):
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
            p(0, 0).p(0, 1, 2).
        """

        code = code3
        print(code)
        rf = util.ReferenceFactory()
        parse = PrimitiveParser.parse(code, rf)
        pattern = Pattern.search_group_recursive(parse, [ConstantPattern, LinearPattern, PeriodicPattern], util.Tolerance(0.0, 0.1), rf)
        # pattern = Pattern.search_group(parse, [ConstantPattern, LinearPattern, PeriodicPattern], util.Tolerance(0.0, 0.1), rf)

        print(pattern.dsl())

        # Pattern.search_group_recursive(Parser.parse(code2), [ConstantPattern, LinearPattern], 0.1).print()
        # Pattern.search_group_recursive(Parser.parse(code3), [ConstantPattern, LinearPattern], 0.1).print()

    def test_bfs(self):
        # numbers = np.array([3, 7, 15, 31])
        # numbers = np.array([2, 3, 6, 15])
        numbers = np.array([1, 2, 0, 3, -1, 4])
        result = BFSOperatorPattern.apply(numbers, ParameterFlags(numbers))
        print(result)
        print(result.next(3, 0))
        print(result.next(3, 1))
        print(result.next(3, 2))

    def test_cte(self):
        numbers = np.array([275, 200, 275])
        result = ConstantPattern.apply(numbers, ParameterFlags(numbers), Tolerance(0.2 * np.ptp(numbers), 0))
        print(result)

    def test_period(self):
        # numbers = np.array(["rect", "rect", "rect", "vector"])
        numbers = np.array([275.0, 200.0, 275.0])

        result = PeriodicPattern.apply(numbers, ParameterFlags(numbers), Tolerance(0.2 * np.ptp(numbers), 0.1))
        print(result)

    def test_sine(self):
        numbers = np.array([1, 4, 1, -2])
        result = SinusoidalPattern.apply(numbers, ParameterFlags(numbers))
        print(result)

    def test_equal(self):
        a = PeriodicPattern([1, 2])
        b = PeriodicPattern([1, 2])
        print(a == b)

        a = ConstantPattern(50.000)
        b = ConstantPattern(50.0)
        print(a == b)