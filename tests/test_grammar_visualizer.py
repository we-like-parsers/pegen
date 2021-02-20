import textwrap
from typing import List

from pegen.grammar_parser import GeneratedParser as GrammarParser
from pegen.grammar_visualizer import ASTGrammarPrinter
from tests.utils import parse_string


def test_simple_rule() -> None:
    grammar = """
    start: 'a' 'b'
    """
    rules = parse_string(grammar, GrammarParser)

    printer = ASTGrammarPrinter()
    lines: List[str] = []
    printer.print_grammar_ast(rules, printer=lines.append)

    output = "\n".join(lines)
    expected_output = textwrap.dedent(
        """\
    └──Rule
       └──Rhs
          └──Alt
             ├──NamedItem
             │  └──StringLeaf("'a'")
             └──NamedItem
                └──StringLeaf("'b'")
    """
    )

    assert output == expected_output


def test_multiple_rules() -> None:
    grammar = """
    start: a b
    a: 'a'
    b: 'b'
    """
    rules = parse_string(grammar, GrammarParser)

    printer = ASTGrammarPrinter()
    lines: List[str] = []
    printer.print_grammar_ast(rules, printer=lines.append)

    output = "\n".join(lines)
    expected_output = textwrap.dedent(
        """\
    └──Rule
       └──Rhs
          └──Alt
             ├──NamedItem
             │  └──NameLeaf('a')
             └──NamedItem
                └──NameLeaf('b')

    └──Rule
       └──Rhs
          └──Alt
             └──NamedItem
                └──StringLeaf("'a'")

    └──Rule
       └──Rhs
          └──Alt
             └──NamedItem
                └──StringLeaf("'b'")
                    """
    )

    assert output == expected_output


def test_deep_nested_rule() -> None:
    grammar = """
    start: 'a' ['b'['c'['d']]]
    """
    rules = parse_string(grammar, GrammarParser)

    printer = ASTGrammarPrinter()
    lines: List[str] = []
    printer.print_grammar_ast(rules, printer=lines.append)

    output = "\n".join(lines)
    print()
    print(output)
    expected_output = textwrap.dedent(
        """\
    └──Rule
       └──Rhs
          └──Alt
             ├──NamedItem
             │  └──StringLeaf("'a'")
             └──NamedItem
                └──Opt
                   └──Rhs
                      └──Alt
                         ├──NamedItem
                         │  └──StringLeaf("'b'")
                         └──NamedItem
                            └──Opt
                               └──Rhs
                                  └──Alt
                                     ├──NamedItem
                                     │  └──StringLeaf("'c'")
                                     └──NamedItem
                                        └──Opt
                                           └──Rhs
                                              └──Alt
                                                 └──NamedItem
                                                    └──StringLeaf("'d'")
                            """
    )

    assert output == expected_output
