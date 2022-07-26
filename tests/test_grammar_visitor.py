from typing import Any

import pytest

from pegen.grammar import GrammarVisitor
from pegen.grammar_parser import GeneratedParser as GrammarParser
from pegen.utils import parse_string


class Visitor(GrammarVisitor):
    def __init__(self) -> None:
        self.n_nodes = 0

    def visit(self, node: Any, *args: Any, **kwargs: Any) -> None:
        self.n_nodes += 1
        super().visit(node, *args, **kwargs)


def test_parse_trivial_grammar() -> None:
    grammar = """
    start: 'a'
    """
    rules = parse_string(grammar, GrammarParser)
    visitor = Visitor()

    visitor.visit(rules)

    assert visitor.n_nodes == 6


def test_parse_or_grammar() -> None:
    grammar = """
    start: rule
    rule: 'a' | 'b'
    """
    rules = parse_string(grammar, GrammarParser)
    visitor = Visitor()

    visitor.visit(rules)

    # Grammar/Rule/Rhs/Alt/NamedItem/NameLeaf   -> 6
    #         Rule/Rhs/                         -> 2
    #                  Alt/NamedItem/StringLeaf -> 3
    #                  Alt/NamedItem/StringLeaf -> 3

    assert visitor.n_nodes == 14


def test_parse_repeat1_grammar() -> None:
    grammar = """
    start: 'a'+
    """
    rules = parse_string(grammar, GrammarParser)
    visitor = Visitor()

    visitor.visit(rules)

    # Grammar/Rule/Rhs/Alt/NamedItem/Repeat1/StringLeaf -> 6
    assert visitor.n_nodes == 7


def test_parse_repeat0_grammar() -> None:
    grammar = """
    start: 'a'*
    """
    rules = parse_string(grammar, GrammarParser)
    visitor = Visitor()

    visitor.visit(rules)

    # Grammar/Rule/Rhs/Alt/NamedItem/Repeat0/StringLeaf -> 6

    assert visitor.n_nodes == 7


def test_parse_optional_grammar() -> None:
    grammar = """
    start: 'a' ['b']
    """
    rules = parse_string(grammar, GrammarParser)
    visitor = Visitor()

    visitor.visit(rules)

    # Grammar/Rule/Rhs/Alt/NamedItem/StringLeaf                       -> 6
    #                      NamedItem/Opt/Rhs/Alt/NamedItem/Stringleaf -> 6

    assert visitor.n_nodes == 12


if __name__ == "__main__":
    pytest.main([__file__])
