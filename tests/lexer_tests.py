from unittest import TestCase

from parsing.lexer import Lexer


class LexerTests(TestCase):
    def test_constant_extraction(self):
        code = "Linear[Linear[a], a, a, b]"

        print(Lexer.extract_constants(code))
