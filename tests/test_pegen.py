import ast
import difflib
import io
import textwrap
from tokenize import NAME, NEWLINE, NUMBER, OP, TokenInfo
from typing import Any, Dict, Type

import pytest  # type: ignore

from pegen.grammar import Grammar, GrammarError
from pegen.grammar_parser import GeneratedParser as GrammarParser
from pegen.parser import Parser
from pegen.python_generator import PythonParserGenerator

from .utils import generate_parser, make_parser, parse_string


def test_parse_grammar() -> None:
    grammar_source = """
    start: sum NEWLINE
    sum: t1=term '+' t2=term { action } | term
    term: NUMBER
    """
    expected = """
    start: sum NEWLINE
    sum: term '+' term | term
    term: NUMBER
    """
    grammar: Grammar = parse_string(grammar_source, GrammarParser)
    rules = grammar.rules
    assert str(grammar) == textwrap.dedent(expected).strip()
    # Check the str() and repr() of a few rules; AST nodes don't support ==.
    assert str(rules["start"]) == "start: sum NEWLINE"
    assert str(rules["sum"]) == "sum: term '+' term | term"
    expected_repr = "Rule('term', None, Rhs([Alt([NamedItem(None, NameLeaf('NUMBER'))])]))"
    assert repr(rules["term"]) == expected_repr


def test_parse_grammar_with_types() -> None:
    grammar = """
    start[ast.BinOp]: term ('+' term)* NEWLINE
    term[T[int]]: NUMBER
    c_rule[expr_ty*]: a=NUMBER? { _new_expr_ty(a) }
    """

    grammar: Grammar = parse_string(grammar, GrammarParser)
    rules = grammar.rules
    assert rules["start"].type.replace(" ", "") == "ast.BinOp"
    assert rules["term"].type.replace(" ", "") == "T[int]"
    assert rules["c_rule"].type == "expr_ty*"


def test_long_rule_str() -> None:
    grammar_source = """
    start: zero | one | one zero | one one | one zero zero | one zero one | one one zero | one one one
    """
    expected = """
    start:
        | zero
        | one
        | one zero
        | one one
        | one zero zero
        | one zero one
        | one one zero
        | one one one
    """
    grammar: Grammar = parse_string(grammar_source, GrammarParser)
    assert str(grammar.rules["start"]) == textwrap.dedent(expected).strip()


def test_typed_rules() -> None:
    grammar = """
    start[int]: sum NEWLINE
    sum[int]: t1=term '+' t2=term { action } | term
    term[int]: NUMBER
    """
    rules = parse_string(grammar, GrammarParser).rules
    # Check the str() and repr() of a few rules; AST nodes don't support ==.
    assert str(rules["start"]) == "start: sum NEWLINE"
    assert str(rules["sum"]) == "sum: term '+' term | term"
    assert (
        repr(rules["term"])
        == "Rule('term', 'int', Rhs([Alt([NamedItem(None, NameLeaf('NUMBER'))])]))"
    )


def test_gather() -> None:
    grammar = """
    start: ','.thing+ NEWLINE
    thing: NUMBER
    """
    rules = parse_string(grammar, GrammarParser).rules
    assert str(rules["start"]) == "start: ','.thing+ NEWLINE"
    print(repr(rules["start"]))
    assert repr(rules["start"]).startswith(
        "Rule('start', None, Rhs([Alt([NamedItem(None, Gather(StringLeaf(\"','\"), NameLeaf('thing'"
    )
    assert str(rules["thing"]) == "thing: NUMBER"
    parser_class = make_parser(grammar)
    node = parse_string("42\n", parser_class)
    assert node == [
        [TokenInfo(NUMBER, string="42", start=(1, 0), end=(1, 2), line="42\n")],
        TokenInfo(NEWLINE, string="\n", start=(1, 2), end=(1, 3), line="42\n"),
    ]
    node = parse_string("1, 2\n", parser_class)
    assert node == [
        [
            TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1, 2\n"),
            TokenInfo(NUMBER, string="2", start=(1, 3), end=(1, 4), line="1, 2\n"),
        ],
        TokenInfo(NEWLINE, string="\n", start=(1, 4), end=(1, 5), line="1, 2\n"),
    ]


def test_expr_grammar() -> None:
    grammar = """
    start: sum NEWLINE
    sum: term '+' term | term
    term: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("42\n", parser_class)
    assert node == [
        TokenInfo(NUMBER, string="42", start=(1, 0), end=(1, 2), line="42\n"),
        TokenInfo(NEWLINE, string="\n", start=(1, 2), end=(1, 3), line="42\n"),
    ]


def test_optional_operator() -> None:
    grammar = """
    start: sum NEWLINE
    sum: term ('+' term)?
    term: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("1+2\n", parser_class)
    assert node == [
        [
            TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1+2\n"),
            [
                TokenInfo(OP, string="+", start=(1, 1), end=(1, 2), line="1+2\n"),
                TokenInfo(NUMBER, string="2", start=(1, 2), end=(1, 3), line="1+2\n"),
            ],
        ],
        TokenInfo(NEWLINE, string="\n", start=(1, 3), end=(1, 4), line="1+2\n"),
    ]
    node = parse_string("1\n", parser_class)
    assert node == [
        [TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1\n"), None],
        TokenInfo(NEWLINE, string="\n", start=(1, 1), end=(1, 2), line="1\n"),
    ]


def test_optional_literal() -> None:
    grammar = """
    start: sum NEWLINE
    sum: term '+' ?
    term: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("1+\n", parser_class)
    assert node == [
        [
            TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1+\n"),
            TokenInfo(OP, string="+", start=(1, 1), end=(1, 2), line="1+\n"),
        ],
        TokenInfo(NEWLINE, string="\n", start=(1, 2), end=(1, 3), line="1+\n"),
    ]
    node = parse_string("1\n", parser_class)
    assert node == [
        [TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1\n"), None],
        TokenInfo(NEWLINE, string="\n", start=(1, 1), end=(1, 2), line="1\n"),
    ]


def test_alt_optional_operator() -> None:
    grammar = """
    start: sum NEWLINE
    sum: term ['+' term]
    term: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("1 + 2\n", parser_class)
    assert node == [
        [
            TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 + 2\n"),
            [
                TokenInfo(OP, string="+", start=(1, 2), end=(1, 3), line="1 + 2\n"),
                TokenInfo(NUMBER, string="2", start=(1, 4), end=(1, 5), line="1 + 2\n"),
            ],
        ],
        TokenInfo(NEWLINE, string="\n", start=(1, 5), end=(1, 6), line="1 + 2\n"),
    ]
    node = parse_string("1\n", parser_class)
    assert node == [
        [TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1\n"), None],
        TokenInfo(NEWLINE, string="\n", start=(1, 1), end=(1, 2), line="1\n"),
    ]


def test_repeat_0_simple() -> None:
    grammar = """
    start: thing thing* NEWLINE
    thing: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("1 2 3\n", parser_class)
    assert node == [
        TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 2 3\n"),
        [
            TokenInfo(NUMBER, string="2", start=(1, 2), end=(1, 3), line="1 2 3\n"),
            TokenInfo(NUMBER, string="3", start=(1, 4), end=(1, 5), line="1 2 3\n"),
        ],
        TokenInfo(NEWLINE, string="\n", start=(1, 5), end=(1, 6), line="1 2 3\n"),
    ]
    node = parse_string("1\n", parser_class)
    assert node == [
        TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1\n"),
        [],
        TokenInfo(NEWLINE, string="\n", start=(1, 1), end=(1, 2), line="1\n"),
    ]


def test_repeat_0_complex() -> None:
    grammar = """
    start: term ('+' term)* NEWLINE
    term: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("1 + 2 + 3\n", parser_class)
    assert node == [
        TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 + 2 + 3\n"),
        [
            [
                TokenInfo(OP, string="+", start=(1, 2), end=(1, 3), line="1 + 2 + 3\n"),
                TokenInfo(NUMBER, string="2", start=(1, 4), end=(1, 5), line="1 + 2 + 3\n"),
            ],
            [
                TokenInfo(OP, string="+", start=(1, 6), end=(1, 7), line="1 + 2 + 3\n"),
                TokenInfo(NUMBER, string="3", start=(1, 8), end=(1, 9), line="1 + 2 + 3\n"),
            ],
        ],
        TokenInfo(NEWLINE, string="\n", start=(1, 9), end=(1, 10), line="1 + 2 + 3\n"),
    ]


def test_repeat_1_simple() -> None:
    grammar = """
    start: thing thing+ NEWLINE
    thing: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("1 2 3\n", parser_class)
    assert node == [
        TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 2 3\n"),
        [
            TokenInfo(NUMBER, string="2", start=(1, 2), end=(1, 3), line="1 2 3\n"),
            TokenInfo(NUMBER, string="3", start=(1, 4), end=(1, 5), line="1 2 3\n"),
        ],
        TokenInfo(NEWLINE, string="\n", start=(1, 5), end=(1, 6), line="1 2 3\n"),
    ]
    with pytest.raises(SyntaxError):
        parse_string("1\n", parser_class)


def test_repeat_1_complex() -> None:
    grammar = """
    start: term ('+' term)+ NEWLINE
    term: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("1 + 2 + 3\n", parser_class)
    assert node == [
        TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 + 2 + 3\n"),
        [
            [
                TokenInfo(OP, string="+", start=(1, 2), end=(1, 3), line="1 + 2 + 3\n"),
                TokenInfo(NUMBER, string="2", start=(1, 4), end=(1, 5), line="1 + 2 + 3\n"),
            ],
            [
                TokenInfo(OP, string="+", start=(1, 6), end=(1, 7), line="1 + 2 + 3\n"),
                TokenInfo(NUMBER, string="3", start=(1, 8), end=(1, 9), line="1 + 2 + 3\n"),
            ],
        ],
        TokenInfo(NEWLINE, string="\n", start=(1, 9), end=(1, 10), line="1 + 2 + 3\n"),
    ]
    with pytest.raises(SyntaxError):
        parse_string("1\n", parser_class)


def test_repeat_with_sep_simple() -> None:
    grammar = """
    start: ','.thing+ NEWLINE
    thing: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("1, 2, 3\n", parser_class)
    assert node == [
        [
            TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1, 2, 3\n"),
            TokenInfo(NUMBER, string="2", start=(1, 3), end=(1, 4), line="1, 2, 3\n"),
            TokenInfo(NUMBER, string="3", start=(1, 6), end=(1, 7), line="1, 2, 3\n"),
        ],
        TokenInfo(NEWLINE, string="\n", start=(1, 7), end=(1, 8), line="1, 2, 3\n"),
    ]


def test_left_recursive() -> None:
    grammar_source = """
    start: expr NEWLINE
    expr: ('-' term | expr '+' term | term)
    term: NUMBER
    foo: NAME+
    bar: NAME*
    baz: NAME?
    """
    grammar: Grammar = parse_string(grammar_source, GrammarParser)
    parser_class = generate_parser(grammar)
    rules = grammar.rules
    assert not rules["start"].left_recursive
    assert rules["expr"].left_recursive
    assert not rules["term"].left_recursive
    assert not rules["foo"].left_recursive
    assert not rules["bar"].left_recursive
    assert not rules["baz"].left_recursive
    node = parse_string("1 + 2 + 3\n", parser_class)
    assert node == [
        [
            [
                TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 + 2 + 3\n"),
                TokenInfo(OP, string="+", start=(1, 2), end=(1, 3), line="1 + 2 + 3\n"),
                TokenInfo(NUMBER, string="2", start=(1, 4), end=(1, 5), line="1 + 2 + 3\n"),
            ],
            TokenInfo(OP, string="+", start=(1, 6), end=(1, 7), line="1 + 2 + 3\n"),
            TokenInfo(NUMBER, string="3", start=(1, 8), end=(1, 9), line="1 + 2 + 3\n"),
        ],
        TokenInfo(NEWLINE, string="\n", start=(1, 9), end=(1, 10), line="1 + 2 + 3\n"),
    ]


def test_python_expr() -> None:
    grammar = """
    start: expr NEWLINE? $ { ast.Expression(expr, LOCATIONS) }
    expr: ( expr '+' term { ast.BinOp(expr, ast.Add(), term, LOCATIONS) }
          | expr '-' term { ast.BinOp(expr, ast.Sub(), term, LOCATIONS) }
          | term { term }
          )
    term: ( l=term '*' r=factor { ast.BinOp(l, ast.Mult(), r, LOCATIONS) }
          | l=term '/' r=factor { ast.BinOp(l, ast.Div(), r, LOCATIONS) }
          | factor { factor }
          )
    factor: ( '(' expr ')' { expr }
            | atom { atom }
            )
    atom: ( n=NAME { ast.Name(id=n.string, ctx=ast.Load(), LOCATIONS) }
          | n=NUMBER { ast.Constant(value=ast.literal_eval(n.string), LOCATIONS) }
          )
    """
    parser_class = make_parser(grammar)
    node = parse_string("(1 + 2*3 + 5)/(6 - 2)\n", parser_class)
    code = compile(node, "", "eval")
    val = eval(code)
    assert val == 3.0


def test_nullable() -> None:
    grammar_source = """
    start: sign NUMBER
    sign: ['-' | '+']
    """
    grammar: Grammar = parse_string(grammar_source, GrammarParser)
    out = io.StringIO()
    genr = PythonParserGenerator(grammar, out)
    rules = grammar.rules
    assert rules["start"].nullable is False  # Not None!
    assert rules["sign"].nullable


def test_advanced_left_recursive() -> None:
    grammar_source = """
    start: NUMBER | sign start
    sign: ['-']
    """
    grammar: Grammar = parse_string(grammar_source, GrammarParser)
    out = io.StringIO()
    genr = PythonParserGenerator(grammar, out)
    rules = grammar.rules
    assert rules["start"].nullable is False  # Not None!
    assert rules["sign"].nullable
    assert rules["start"].left_recursive
    assert not rules["sign"].left_recursive


def test_mutually_left_recursive() -> None:
    grammar_source = """
    start: foo 'E'
    foo: bar 'A' | 'B'
    bar: foo 'C' | 'D'
    """
    grammar: Grammar = parse_string(grammar_source, GrammarParser)
    out = io.StringIO()
    genr = PythonParserGenerator(grammar, out)
    rules = grammar.rules
    assert not rules["start"].left_recursive
    assert rules["foo"].left_recursive
    assert rules["bar"].left_recursive
    genr.generate("<string>")
    ns: Dict[str, Any] = {}
    exec(out.getvalue(), ns)
    parser_class: Type[Parser] = ns["GeneratedParser"]
    node = parse_string("D A C A E", parser_class)
    assert node == [
        [
            [
                [
                    TokenInfo(type=NAME, string="D", start=(1, 0), end=(1, 1), line="D A C A E"),
                    TokenInfo(type=NAME, string="A", start=(1, 2), end=(1, 3), line="D A C A E"),
                ],
                TokenInfo(type=NAME, string="C", start=(1, 4), end=(1, 5), line="D A C A E"),
            ],
            TokenInfo(type=NAME, string="A", start=(1, 6), end=(1, 7), line="D A C A E"),
        ],
        TokenInfo(type=NAME, string="E", start=(1, 8), end=(1, 9), line="D A C A E"),
    ]
    node = parse_string("B C A E", parser_class)
    assert node != None
    assert node == [
        [
            [
                TokenInfo(type=NAME, string="B", start=(1, 0), end=(1, 1), line="B C A E"),
                TokenInfo(type=NAME, string="C", start=(1, 2), end=(1, 3), line="B C A E"),
            ],
            TokenInfo(type=NAME, string="A", start=(1, 4), end=(1, 5), line="B C A E"),
        ],
        TokenInfo(type=NAME, string="E", start=(1, 6), end=(1, 7), line="B C A E"),
    ]


def test_nasty_mutually_left_recursive() -> None:
    # This grammar does not recognize 'x - + =', much to my chagrin.
    # But that's the way PEG works.
    # [Breathlessly]
    # The problem is that the toplevel target call
    # recurses into maybe, which recognizes 'x - +',
    # and then the toplevel target looks for another '+',
    # which fails, so it retreats to NAME,
    # which succeeds, so we end up just recognizing 'x',
    # and then start fails because there's no '=' after that.
    grammar_source = """
    start: target '='
    target: maybe '+' | NAME
    maybe: maybe '-' | target
    """
    grammar: Grammar = parse_string(grammar_source, GrammarParser)
    out = io.StringIO()
    genr = PythonParserGenerator(grammar, out)
    genr.generate("<string>")
    ns: Dict[str, Any] = {}
    exec(out.getvalue(), ns)
    parser_class = ns["GeneratedParser"]
    with pytest.raises(SyntaxError):
        parse_string("x - + =", parser_class)


def test_lookahead() -> None:
    grammar = """
    start: (expr_stmt | assign_stmt) &'.'
    expr_stmt: !(target '=') expr
    assign_stmt: target '=' expr
    expr: term ('+' term)*
    target: NAME
    term: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("foo = 12 + 12 .", parser_class)
    assert node == [
        TokenInfo(NAME, string="foo", start=(1, 0), end=(1, 3), line="foo = 12 + 12 ."),
        TokenInfo(OP, string="=", start=(1, 4), end=(1, 5), line="foo = 12 + 12 ."),
        [
            TokenInfo(NUMBER, string="12", start=(1, 6), end=(1, 8), line="foo = 12 + 12 ."),
            [
                [
                    TokenInfo(OP, string="+", start=(1, 9), end=(1, 10), line="foo = 12 + 12 ."),
                    TokenInfo(
                        NUMBER, string="12", start=(1, 11), end=(1, 13), line="foo = 12 + 12 ."
                    ),
                ]
            ],
        ],
    ]


def test_named_lookahead_error() -> None:
    grammar = """
    start: foo=!'x' NAME
    """
    with pytest.raises(SyntaxError):
        make_parser(grammar)


def test_start_leader() -> None:
    grammar = """
    start: attr | NAME
    attr: start '.' NAME
    """
    # Would assert False without a special case in compute_left_recursives().
    make_parser(grammar)


def test_left_recursion_too_complex() -> None:
    grammar = """
    start: foo
    foo: bar '+' | baz '+' | '+'
    bar: baz '-' | foo '-' | '-'
    baz: foo '*' | bar '*' | '*'
    """
    with pytest.raises(ValueError) as errinfo:
        make_parser(grammar)
    assert "no leader" in str(errinfo.value)


def test_cut() -> None:
    grammar = """
    start: '(' ~ expr ')'
    expr: NUMBER
    """
    parser_class = make_parser(grammar)
    node = parse_string("(1)", parser_class, verbose=True)
    assert node == [
        TokenInfo(OP, string="(", start=(1, 0), end=(1, 1), line="(1)"),
        TokenInfo(NUMBER, string="1", start=(1, 1), end=(1, 2), line="(1)"),
        TokenInfo(OP, string=")", start=(1, 2), end=(1, 3), line="(1)"),
    ]


def test_cut_early_exit() -> None:
    grammar = """
    start: '(' ~ expr ')' | '(' name ')'
    expr: NUMBER
    name: NAME
    """
    parser_class = make_parser(grammar)
    with pytest.raises(SyntaxError):
        parse_string("(a)", parser_class, verbose=True)


def test_dangling_reference() -> None:
    grammar = """
    start: foo ENDMARKER
    foo: bar NAME
    """
    with pytest.raises(GrammarError):
        parser_class = make_parser(grammar)


def test_bad_token_reference() -> None:
    grammar = """
    start: foo
    foo: NAMEE
    """
    with pytest.raises(GrammarError):
        parser_class = make_parser(grammar)


def test_missing_start() -> None:
    grammar = """
    foo: NAME
    """
    with pytest.raises(GrammarError):
        parser_class = make_parser(grammar)


def test_soft_keyword() -> None:
    grammar = """
    start:
        | "number" n=NUMBER { eval(n.string) }
        | "string" n=STRING { n.string }
        | SOFT_KEYWORD l=NAME n=(NUMBER | NAME | STRING) { f"{l.string} = {n.string}"}
    """
    parser_class = make_parser(grammar)
    assert parse_string("number 1", parser_class, verbose=True) == 1
    assert parse_string("string 'b'", parser_class, verbose=True) == "'b'"
    assert parse_string("number test 1", parser_class, verbose=True) == "test = 1"
    assert parse_string("string test 'b'", parser_class, verbose=True) == "test = 'b'"
    with pytest.raises(SyntaxError):
        parse_string("test 1", parser_class, verbose=True)


def test_forced() -> None:
    grammar = """
    start: NAME &&':' | NAME
    """
    parser_class = make_parser(grammar)
    assert parse_string("number :", parser_class, verbose=True)
    with pytest.raises(SyntaxError) as e:
        parse_string("a", parser_class, verbose=True)

    assert "expected ':'" in str(e.exconly())


def test_forced_with_group() -> None:
    grammar = """
    start: NAME &&(':' | ';') | NAME
    """
    parser_class = make_parser(grammar)
    assert parse_string("number :", parser_class, verbose=True)
    assert parse_string("number ;", parser_class, verbose=True)
    with pytest.raises(SyntaxError) as e:
        parse_string("a", parser_class, verbose=True)

    assert "expected (':' | ';')" in e.value.args[0]


def test_unreachable_explicit() -> None:
    source = """
    start: NAME { UNREACHABLE }
    """
    grammar = parse_string(source, GrammarParser)
    out = io.StringIO()
    genr = PythonParserGenerator(grammar, out, unreachable_formatting="This is a test")
    genr.generate("<string>")
    assert "This is a test" in out.getvalue()


def test_unreachable_implicit1() -> None:
    source = """
    start: NAME | invalid_input
    invalid_input: NUMBER
    """
    grammar = parse_string(source, GrammarParser)
    out = io.StringIO()
    genr = PythonParserGenerator(grammar, out, unreachable_formatting="This is a test")
    genr.generate("<string>")
    assert "This is a test" in out.getvalue()


def test_unreachable_implicit2() -> None:
    source = """
    start: NAME | invalid_input
    invalid_input: NUMBER { None }
    """
    grammar = parse_string(source, GrammarParser)
    out = io.StringIO()
    genr = PythonParserGenerator(grammar, out, unreachable_formatting="This is a test")
    genr.generate("<string>")
    assert "This is a test" not in out.getvalue()


def test_locations_in_alt_action_and_group() -> None:
    grammar = """
    start: t=term NEWLINE? $ { ast.Expression(t, LOCATIONS) }
    term:
        | l=term '*' r=factor { ast.BinOp(l, ast.Mult(), r, LOCATIONS) }
        | l=term '/' r=factor { ast.BinOp(l, ast.Div(), r, LOCATIONS) }
        | factor
    factor:
        | (
            n=NAME { ast.Name(id=n.string, ctx=ast.Load(), LOCATIONS) } |
            n=NUMBER { ast.Constant(value=ast.literal_eval(n.string), LOCATIONS) }
         )
    """
    parser_class = make_parser(grammar)
    source = "2*3\n"
    o = ast.dump(parse_string(source, parser_class).body, include_attributes=True)
    p = ast.dump(ast.parse(source).body[0].value, include_attributes=True)
    diff = "\n".join(difflib.unified_diff(o.split("\n"), p.split("\n"), "cpython", "python-pegen"))
    if diff:
        print(diff)
    assert not diff
