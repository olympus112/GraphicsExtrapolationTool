from unittest import TestCase

from misc import util
from parsing.lexer import Lexer
from parsing.pattern_parser import PatternParser

class PatternParserTests(TestCase):

    def test_parameter_pattern(self):
        def test(code):
            parser = PatternParser(code)
            pattern = parser.parse_parameter_pattern(parser.lexer.next())
            print(pattern)

        code1 = "Linear(5)"
        code2 = "Constant(5)"
        code3 = "Period(5, 4, 7)"
        code4 = "Period(p, 4, p_7)"
        code5 = "None()"

        test(code1)
        test(code2)
        test(code3)
        test(code4)
        test(code5)

    def test_primitive_pattern(self):
        def test(code):
            parser = PatternParser(code)
            pattern = parser.parse_primitive_pattern(parser.lexer.next(), util.ReferenceFactory())
            print(pattern)
            print(pattern.dsl())

        code1 = "@1,2[1:Linear(5), 2:Constant(1)]"
        code2 = "[1:Linear(5), 2:Constant(1), 3:Period(1)]"
        code3 = "[]"

        test(code1)
        test(code2)
        test(code3)

    def test_group_pattern(self):
        def test(code):
            lexer = Lexer(code)
            parser = PatternParser(code)
            pattern = parser.parse_group_pattern(parser.lexer.next())
            print(pattern)

        code1 = "([]){}"

        test(code1)

    def test_add_identifiers(self):
        def test(code):
            parser = PatternParser(code)
            pattern = parser.parse_group_pattern(parser.lexer.next())
            print(pattern, end=" -> ")
            parser.add_identifiers(pattern)
            print(pattern)
            pattern.print(_format=repr)

        code1 = "([]){}"
        code2 = "(#0[]){}"
        code3 = "(#1[]){}"
        code4 = "#0(#1[]){[]}"

        test(code1)
        test(code2)
        test(code3)
        test(code4)

    def test_instance_pattern(self):
        def test(code):
            parser = PatternParser(code)
            pattern = parser.parse_instance_pattern(parser.lexer.next())
            print(pattern)

        code1 = "([]){}"
        code2 = "([]){([]){}}"

        test(code1)
        test(code2)

    def test_parse(self):
        def test(code):
            parser = PatternParser(code)
            pattern = parser.parse()
            print(pattern.dsl(_identifier=True))

        code1 = "([]){([]){[],([]){[]}},[]}"

        test(code1)

    def test_variable_assignment(self):
        def test(code):
            parser = PatternParser(code)
            pattern = parser.parse()
            print(parser.variables)
            pattern.print(_format=repr)

        code1 = "$a=rect$b=Constant [b[a], b[10]]"

        test(code1)