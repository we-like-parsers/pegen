import unittest

from pegen.grammar import Grammar
from pegen.grammar_parser import GeneratedParser as GrammarParser
from pegen.utils import parse_string
from pegen.validator import SubRuleValidator, ValidationError


class TestPegen(unittest.TestCase):
    def test_rule_with_no_collision(self) -> None:
        grammar_source = """
        start: bad_rule
        sum:
            | NAME '-' NAME
            | NAME '+' NAME
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        validator = SubRuleValidator(grammar)
        for rule_name, rule in grammar.rules.items():
            validator.validate_rule(rule_name, rule)

    def test_rule_with_simple_collision(self) -> None:
        grammar_source = """
        start: bad_rule
        sum:
            | NAME '+' NAME
            | NAME '+' NAME ';'
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        validator = SubRuleValidator(grammar)
        with self.assertRaises(ValidationError):
            for rule_name, rule in grammar.rules.items():
                validator.validate_rule(rule_name, rule)

    def test_rule_with_collision_after_some_other_rules(self) -> None:
        grammar_source = """
        start: bad_rule
        sum:
            | NAME '+' NAME
            | NAME '*' NAME ';'
            | NAME '-' NAME
            | NAME '+' NAME ';'
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        validator = SubRuleValidator(grammar)
        with self.assertRaises(ValidationError):
            for rule_name, rule in grammar.rules.items():
                validator.validate_rule(rule_name, rule)
