"""Test syntax errors for cases where the parser can generate helpful messages."""
import io
import tokenize
import sys

import pytest

from pegen.tokenizer import Tokenizer


def parse_invalid_syntax(python_parser_cls, source, exc_cls, message):
    temp = io.StringIO(source)
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer)
    with pytest.raises(exc_cls) as e:
        pp.parse("file")

    print(str(e.exconly()))
    assert message in str(e.exconly())


@pytest.mark.parametrize(
    "source, message", [("f'a = { 1 + }'", "line 1"), ("(\n\t'b'\n\tf'a = { 1 + }'\n)", "line 3")]
)
def test_syntax_error_in_str(python_parser_cls, source, message):
    parse_invalid_syntax(python_parser_cls, source, SyntaxError, message)


@pytest.mark.parametrize(
    "source, message",
    [
        # Invalid arguments rules
        # ("f(a=1, *b)", "iterable argument unpacking follows keyword argument unpacking"),
        ("f(a for a in b, c)", "Generator expression must be parenthesized"),
        # ("f(a=1+1)", "invalid syntax. Maybe you meant '==' or ':=' instead of '='?"),
        ("f(a, b for b in c)", "Generator expression must be parenthesized"),
        ("f(**a, b)", "positional argument follows keyword argument unpacking"),
        ("f(a=1, b)", "positional argument follows keyword argument"),
        # Invalid kwarg rules
        ("f(a=1, b=c for c in d)", "invalid syntax. Maybe you meant '==' or ':=' instead of '='?"),
        # ("f(a= 1 + b=2)", 'expression cannot contain assignment, perhaps you meant "=="?'),
    ],
)
def test_invalid_call_arguments(python_parser_cls, source, message):
    parse_invalid_syntax(python_parser_cls, source, SyntaxError, message)


@pytest.mark.parametrize(
    "source, message",
    [
        ("'a' = 1", "cannot assign to literal"),
        ("1 = 1", "cannot assign to 1"),
        ("True = 1", "cannot assign to True"),
        ("False = 1", "cannot assign to False"),
        ("... = 1", "cannot assign to Ellipsis"),
        ("None = 1", "cannot assign to None"),
        ("(a, b) : int = (1, 2)", "only single target (not tuple) can be annotated"),
        ("[a, b] : int = [1, 2]", "only single target (not list) can be annotated"),
        ("([a, b]) : int = (1, 2)", "only single target (not list) can be annotated"),
        ("a, b: int, int = 1, 2", "only single target (not tuple) can be annotated"),
        ("{a, b} : set", "illegal target for annotation"),
        ("a + 1 = 2", "cannot assign to expression"),
        ("[i for i in range(2)] = 2", "cannot assign to list comprehension"),
        ("yield a = 1", "assignment to yield expression not possible"),
        ("a = yield b = 1", "assignment to yield expression not possible"),
        ("a + 1 += 1", "expression is an illegal expression for augmented assignment"),
        ("a + 1 += yield", "expression is an illegal expression for augmented assignment"),
        (
            "[i for i in range(2)] += 1",
            "list comprehension is an illegal expression for augmented assignment",
        ),
    ],
)
def test_invalid_assignments(python_parser_cls, source, message):
    parse_invalid_syntax(python_parser_cls, source, SyntaxError, message)


@pytest.mark.parametrize(
    "source, message",
    [
        ("del [i for i in range(2)]", "cannot delete list comprehension"),
        ("del a + 1", "cannot delete expression"),
    ],
)
def test_invalid_del_statements(python_parser_cls, source, message):
    parse_invalid_syntax(python_parser_cls, source, SyntaxError, message)


@pytest.mark.parametrize(
    "source, message",
    [
        (
            "(*a for a in enumerate(range(5)))",
            "iterable unpacking cannot be used in comprehension",
        ),
        (
            "[*a for a in enumerate(range(5))]",
            "iterable unpacking cannot be used in comprehension",
        ),
        (
            "{*a for a in enumerate(range(5))}",
            "iterable unpacking cannot be used in comprehension",
        ),
        (
            "[a, a for a in range(5)]",
            "did you forget parentheses around the comprehension target?",
        ),
        (
            "[a, a for a in range(5)]",
            "did you forget parentheses around the comprehension target?",
        ),
        (
            "[a,  for a in range(5)]",
            "did you forget parentheses around the comprehension target?",
        ),
        (
            "[a,  for a in range(5)]",
            "did you forget parentheses around the comprehension target?",
        ),
        ("{**a for a in [{1: 2}]}", "dict unpacking cannot be used in dict comprehension"),
    ],
)
def test_invalid_comprehension(python_parser_cls, source, message):
    parse_invalid_syntax(python_parser_cls, source, SyntaxError, message)


@pytest.mark.parametrize(
    "source",
    [
        "def f(a=1, b):\n\tpass",
        "def f(a=1, /, b):\n\tpass",
        # "def f(a=1, *, b):\n\tpass",
        "lambda x=1, y: x",
        "lambda x=1, /, y: x",
        # "lambda x=1, *, y: x",
    ],
)
def test_invalid_parameters(python_parser_cls, source):
    parse_invalid_syntax(
        python_parser_cls, source, SyntaxError, "non-default argument follows default argument"
    )


@pytest.mark.parametrize(
    "source",
    [
        "def f(a, *):\n\tpass",
        "def f(a, *,):\n\tpass",
        "def f(a, *, **):\n\tpass",
        "lambda a, *: a",
        "lambda a, *, **:a",
    ],
)
def test_invalid_star_etc(python_parser_cls, source):
    parse_invalid_syntax(
        python_parser_cls, source, SyntaxError, "named arguments must follow bare *"
    )


# @pytest.mark.parametrize(
#     "source, message",
#     [
#         ("with open(a) as (b,):\n\tpass", "cannot assign to tuple"),
#         ("with open(a) as [b]:\n\tpass", "cannot assign to list"),
#         ("with open(a) as {b: 1}]:\n\tpass", "cannot assign to dict"),
#         ("with open(a) as {b}:\n\tpass", "cannot assign to set"),
#     ],
# )
# def test_invalid_with_item(python_parser_cls, source, message):
#     parse_invalid_syntax(python_parser_cls, source, SyntaxError, message)


# @pytest.mark.parametrize(
#     "source, message",
#     [
#         ("for [a] in [[1]]:\n\tpass", "cannot assign to list"),
#         ("async for a := i in [[1]]:\n\tpass", "cannot assign to named expression"),
#     ],
# )
# def test_invalid_for_target(python_parser_cls, source, message):
#     parse_invalid_syntax(python_parser_cls, source, SyntaxError, message)


# @pytest.mark.parametrize(
#     "source, message",
#     [
#         ("a = (*b, 1)", "cannot use starred expression here"),
#         ("a = (**b, 1)", "cannot use double starred expression here"),
#     ],
# )
# def test_invalid_group(python_parser_cls, source, message):
#     parse_invalid_syntax(python_parser_cls, source, SyntaxError, message)


# @pytest.mark.parametrize(
#     "source",
#     ["import a, b,", "from a import b,"],
# )
# def test_invalid_import_from_as_names(python_parser_cls, source):
#     parse_invalid_syntax(
#         python_parser_cls,
#         source,
#         SyntaxError,
#         "trailing comma not allowed without surrounding parentheses",
#     )


@pytest.mark.parametrize(
    "source, exception, message",
    [
        (
            "with open(a) as f, b as d:\npass",
            IndentationError,
            "expected an indented block after 'with' statement on line 1",
        ),
        (
            "\nasync with (open(a) as f, b as d):\npass",
            IndentationError,
            "expected an indented block after 'with' statement on line 2",
        ),
        ("with open(a) as f, b as d\npass", SyntaxError, "expected ':'"),
        ("\nasync with (open(a) as f, b as d)\npass", SyntaxError, "expected ':'"),
    ],
)
def test_invalid_with_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        (
            "try:\npass",
            IndentationError,
            "expected an indented block after 'try' statement on line 1",
        ),
        ("try\n\tpass", SyntaxError, "expected ':'"),
        ("try:\n\tpass\na = 1", SyntaxError, "expected 'except' or 'finally' block"),
    ],
)
def test_invalid_try_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        (
            "try:\n\tpass\nexcept Exception:\npass",
            IndentationError,
            "expected an indented block after 'except' statement on line 3",
        ),
        (
            "try:\n\tpass\nexcept Exception as e:\npass",
            IndentationError,
            "expected an indented block after 'except' statement on line 3",
        ),
        (
            "try:\n\tpass\nexcept ValueError, IndexError as e:",
            SyntaxError,
            "exception group must be parenthesized",
        ),
        (
            "try:\n\tpass\nexcept ValueError, IndexError:",
            SyntaxError,
            "exception group must be parenthesized",
        ),
        ("try:\n\tpass\nexcept Exception\npass", SyntaxError, "expected ':'"),
        ("try:\n\tpass\nexcept Exception as e\npass", SyntaxError, "expected ':'"),
        ("try:\n\tpass\nexcept\npass", SyntaxError, "expected ':'"),
    ],
)
def test_invalid_except_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        (
            "try:\n\tpass\nfinally:\npass",
            IndentationError,
            "expected an indented block after 'finally' statement on line 3",
        ),
        (
            "try:\n\tpass\nexcept Exception:\n\tpass\nfinally:\npass",
            IndentationError,
            "expected an indented block after 'finally' statement on line 5",
        ),
    ],
)
def test_invalid_finally_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Valid only in Python 3.10+")
@pytest.mark.parametrize(
    "source, exception, message",
    [
        ("match a\n\tpass", SyntaxError, "expected ':'"),
        (
            "match a:\npass",
            IndentationError,
            "expected an indented block after 'match' statement on line 1",
        ),
    ],
)
def test_invalid_match_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Valid only in Python 3.10+")
@pytest.mark.parametrize(
    "source, exception, message",
    [
        ("match a:\n\tcase 1\n\t\tpass", SyntaxError, "expected ':'"),
        (
            "match a:\n\tcase 1:\n\tpass",
            IndentationError,
            "expected an indented block after 'case' statement on line 1",
        ),
    ],
)
def test_invalid_case_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        # ("if a\n\tpass", SyntaxError, "expected ':'"),
        (
            "if a:\npass",
            IndentationError,
            "expected an indented block after 'if' statement on line 1",
        ),
    ],
)
def test_invalid_if_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        # ("if a:\n\tpass\nelif a\n\tpass", SyntaxError, "expected ':'"),
        (
            "if a:\n\tpass\nelif b:\npass",
            IndentationError,
            "expected an indented block after 'elif' statement on line 3",
        ),
    ],
)
def test_invalid_elif_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        # ("if a:\n\tpass\nelse\n\tpass", SyntaxError, "expected ':'"),
        (
            "if a:\n\tpass\nelse:\npass",
            IndentationError,
            "expected an indented block after 'else' statement on line 3",
        ),
    ],
)
def test_invalid_else_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        # ("while a\n\tpass", SyntaxError, "expected ':'"),
        (
            "while a:\npass",
            IndentationError,
            "expected an indented block after 'while' statement on line 1",
        ),
    ],
)
def test_invalid_while_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        (
            "for a in range(10):\npass",
            IndentationError,
            "expected an indented block after 'for' statement on line 1",
        ),
        (
            "async for a in range(10):\npass",
            IndentationError,
            "expected an indented block after 'for' statement on line 1",
        ),
    ],
)
def test_invalid_for_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        (
            "def f():\npass",
            IndentationError,
            "expected an indented block after function definition on line 1",
        ),
        (
            "async def f():\npass",
            IndentationError,
            "expected an indented block after function definition on line 1",
        ),
        (
            "def f(a,):\npass",
            IndentationError,
            "expected an indented block after function definition on line 1",
        ),
        (
            "def f() -> None:\npass",
            IndentationError,
            "expected an indented block after function definition on line 1",
        ),
    ],
)
def test_invalid_def_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        (
            "class A:\npass",
            IndentationError,
            "expected an indented block after class definition on line 1",
        ),
        (
            "class f(object):\npass",
            IndentationError,
            "expected an indented block after class definition on line 1",
        ),
    ],
)
def test_invalid_class_stmt(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        ("{a: 1, b}", SyntaxError, "':' expected after dictionary key"),
        ("{a: 1, c: 2, b}", SyntaxError, "':' expected after dictionary key"),
        ("{a: 1, b:}", SyntaxError, "expression expected after dictionary key and ':'"),
        ("{c: 1, a: *b}", SyntaxError, "cannot use a starred expression in a dictionary value"),
        ("{b:}", SyntaxError, "expression expected after dictionary key and ':'"),
        ("{b:, c}", SyntaxError, "expression expected after dictionary key and ':'"),
        ("{a: *b}", SyntaxError, "cannot use a starred expression in a dictionary value"),
    ],
)
def test_invalid_dict_key_value(python_parser_cls, source, exception, message):
    parse_invalid_syntax(python_parser_cls, source, exception, message)
