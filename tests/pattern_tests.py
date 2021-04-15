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

    def test_bfs(self):
        # numbers = np.array([3, 7, 15, 31])
        numbers = np.array([2, 3, 6, 15])
        result = BFSOperatorPattern.apply(numbers, ParameterFlags(numbers), tolerance=0)
        print(result)
        print(result.next(3, 2))