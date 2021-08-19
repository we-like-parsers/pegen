"""Test syntax errors for cases where the parser can generate helpful messages."""
import io
import tokenize
import sys

import pytest

from pegen.tokenizer import Tokenizer


def parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exc_cls, message):
    with pytest.raises(exc_cls) as e:
        python_parse_str(source, "exec")

    print(str(e.exconly()))
    assert message in str(e.exconly())

    test_file = tmp_path / "test.py"
    with open(test_file, "w") as f:
        f.write(source)

    with pytest.raises(exc_cls) as e:
        python_parse_file(str(test_file))

    print(str(e.exconly()))
    assert message in str(e.exconly())


@pytest.mark.parametrize(
    "source, message", [("f'a = { 1 + }'", "line 1"), ("(\n\t'b'\n\tf'a = { 1 + }'\n)", "line 3")]
)
def test_syntax_error_in_str(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


@pytest.mark.parametrize(
    "source, message",
    [
        ("a 1", "invalid syntax. Perhaps you forgot a comma?"),
        ("2 if 4", "expected 'else' after 'if' expression"),
        ("a 1 if b else 2", "invalid syntax. Perhaps you forgot a comma?"),
        ("a 1ambda: 1", "invalid syntax. Perhaps you forgot a comma?"),
        ("print 1", "Missing parentheses in call to 'print'"),
        ("exec 1", "Missing parentheses in call to 'exec'"),
        ("a if b", "expected 'else' after 'if' expression"),
        ("c = a if b:", "SyntaxError: invalid syntax"),
    ],
)
def test_invalid_expression(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


# Those tests are mostly there to get coverage on exiting rules without matching
@pytest.mark.parametrize(
    "source, message",
    [
        ("global a, 1", "invalid syntax"),
        ("nonlocal a, 1", "invalid syntax"),
        ("yield raise", "invalid syntax"),
        ("assert raise", "invalid syntax"),
        ("return def", "invalid syntax"),
        ("raise def", "invalid syntax"),
        ("del raise", "invalid syntax"),
        ("if raise:\n\tpass", "invalid syntax"),
        ("@raise\ndef f():\n\tpass", "invalid syntax"),
        ("a: int = raise", "invalid syntax"),
    ],
)
def test_invalid_statements(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


@pytest.mark.parametrize(
    "source, message",
    [
        # Invalid arguments rules
        ("f(**a, *b)", "iterable argument unpacking follows keyword argument unpacking"),
        ("f(a for a in b, c)", "Generator expression must be parenthesized"),
        ("f(a for a in b, c for c in d)", "Generator expression must be parenthesized"),
        (
            "f(a=1 for i in range(10))",
            "invalid syntax. Maybe you meant '==' or ':=' instead of '='?",
        ),
        ("f(a, b for b in c)", "Generator expression must be parenthesized"),
        ("f(a, b for b in c, d)", "Generator expression must be parenthesized"),
        ("f(**a, b)", "positional argument follows keyword argument unpacking"),
        ("f(a=1, b)", "positional argument follows keyword argument"),
        # Invalid kwarg rules
        ("f(b=c for c in d)", "invalid syntax. Maybe you meant '==' or ':=' instead of '='?"),
        ("f(1 + b=2)", 'expression cannot contain assignment, perhaps you meant "=="?'),
    ],
)
def test_invalid_call_arguments(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


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
        ("a += raise", "invalid syntax"),
    ],
)
def test_invalid_assignments(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


@pytest.mark.parametrize(
    "source, message",
    [
        ("del [i for i in range(2)]", "cannot delete list comprehension"),
        ("del a + 1", "cannot delete expression"),
    ],
)
def test_invalid_del_statements(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


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
        # check cuts
        ("(a for a in raise)", "invalid syntax"),
        ("(a async for a in raise)", "invalid syntax"),
    ],
)
def test_invalid_comprehension(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


@pytest.mark.parametrize(
    "source",
    [
        "def f(a=1, b):\n\tpass",
        "def f(a=1, /, b):\n\tpass",
        "lambda x=1, y: x",
        "lambda x=1, /, y: x",
    ],
)
def test_invalid_parameters(python_parse_file, python_parse_str, tmp_path, source):
    parse_invalid_syntax(
        python_parse_file,
        python_parse_str,
        tmp_path,
        source,
        SyntaxError,
        "non-default argument follows default argument",
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
def test_invalid_star_etc(python_parse_file, python_parse_str, tmp_path, source):
    parse_invalid_syntax(
        python_parse_file,
        python_parse_str,
        tmp_path,
        source,
        SyntaxError,
        "named arguments must follow bare *",
    )


@pytest.mark.parametrize(
    "source, message",
    [
        ("with open(a) as {b: 1}:\n\tpass", "cannot assign to dict"),
        ("with open(a) as {b}:\n\tpass", "cannot assign to set"),
        ("with open(a) as 1:\n\tpass", "cannot assign to 1"),
    ],
)
def test_invalid_with_item(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


@pytest.mark.parametrize(
    "source, message",
    [
        ("for {a} in [[1]]:\n\tpass", "cannot assign to comparison"),
        ("async for (a := i)", "cannot assign to named expression"),
    ],
)
def test_invalid_for_target(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


@pytest.mark.parametrize(
    "source, message",
    [
        ("a = (1+1 := 2)", "cannot use assignment expressions with expression"),
        ("a := raise", "invalid syntax"),
    ],
)
def test_named_expression(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


@pytest.mark.parametrize(
    "source, message",
    [
        ("a = (*b)", "cannot use starred expression here"),
        ("a = (**b)", "cannot use double starred expression here"),
    ],
)
def test_invalid_group(python_parse_file, python_parse_str, tmp_path, source, message):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


@pytest.mark.parametrize(
    "source, message",
    [
        ("from a import b,", "trailing comma not allowed without surrounding parentheses"),
        ("from a import b, and 3", "invalid syntax"),
        ("from a import raise", "invalid syntax"),
    ],
)
def test_invalid_import_from_as_names(
    python_parse_file, python_parse_str, tmp_path, source, message
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message
    )


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
def test_invalid_with_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


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
def test_invalid_try_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        (
            "try:\n\tpass\nexcept:\npass",
            IndentationError,
            "expected an indented block after 'except' statement on line 3",
        ),
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
        (
            "try:\n\tpass\nexcept ValueError, IndexError,:",
            SyntaxError,
            "exception group must be parenthesized",
        ),
        (
            "try:\n\tpass\nexcept ValueError, IndexError, a=1:",
            SyntaxError,
            "invalid syntax",
        ),
        ("try:\n\tpass\nexcept Exception\npass", SyntaxError, "expected ':'"),
        ("try:\n\tpass\nexcept Exception as e\npass", SyntaxError, "expected ':'"),
        ("try:\n\tpass\nexcept\npass", SyntaxError, "expected ':'"),
    ],
)
def test_invalid_except_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


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
def test_invalid_finally_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


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
def test_invalid_match_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Valid only in Python 3.10+")
@pytest.mark.parametrize(
    "source, exception, message",
    [
        ("match a:\n\tcase 1\n\t\tpass", SyntaxError, "expected ':'"),
        (
            "match a:\n\tcase 1:\n\tpass",
            IndentationError,
            "expected an indented block after 'case' statement on line 2",
        ),
    ],
)
def test_invalid_case_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Valid only in Python 3.10+")
@pytest.mark.parametrize(
    "source, exception, message",
    [
        # As pattern
        ("match a:\n\tcase 1 as _:\n\t\tpass", SyntaxError, "cannot use '_' as a target"),
        (
            "match a:\n\tcase 1 as 1+1:\n\tpass",
            SyntaxError,
            "invalid pattern target",
        ),
        # Class pattern
        (
            "match a:\n\tcase Foo(z=1, y=2, x):\n\tpass",
            SyntaxError,
            "positional patterns follow keyword patterns",
        ),
        (
            "match a:\n\tcase Foo(a, z=1, y=2, x):\n\tpass",
            SyntaxError,
            "positional patterns follow keyword patterns",
        ),
        (
            "match a:\n\tcase Foo(z=1, x, y=2):\n\tpass",
            SyntaxError,
            "positional patterns follow keyword patterns",
        ),
        (
            "match a:\n\tcase Foo(a=b, c, d=e, f, g=h, i, j=k, ...):\n\tpass",
            SyntaxError,
            "positional patterns follow keyword patterns",
        ),
    ],
)
def test_invalid_case_pattern(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        ("if a\n\tpass", SyntaxError, "expected ':'"),
        (
            "if a:\npass",
            IndentationError,
            "expected an indented block after 'if' statement on line 1",
        ),
    ],
)
def test_invalid_if_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        ("if a:\n\tpass\nelif a\n\tpass", SyntaxError, "expected ':'"),
        (
            "if a:\n\tpass\nelif b:\npass",
            IndentationError,
            "expected an indented block after 'elif' statement on line 3",
        ),
    ],
)
def test_invalid_elif_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        ("if a:\n\tpass\nelse\n\tpass", SyntaxError, "expected ':'"),
        (
            "if a:\n\tpass\nelse:\npass",
            IndentationError,
            "expected an indented block after 'else' statement on line 3",
        ),
    ],
)
def test_invalid_else_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


@pytest.mark.parametrize(
    "source, exception, message",
    [
        ("while a\n\tpass", SyntaxError, "expected ':'"),
        (
            "while a:\npass",
            IndentationError,
            "expected an indented block after 'while' statement on line 1",
        ),
    ],
)
def test_invalid_while_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


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
        (
            "for a in raise:\npass",
            SyntaxError,
            "invalid syntax",
        ),
        (
            "async for a in raise:\npass",
            SyntaxError,
            "invalid syntax",
        ),
    ],
)
def test_invalid_for_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


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
        # (
        #     "def f():\n# type: () -> int\n# type: () -> str\n\tpass",
        #     SyntaxError,
        #     "expected an indented block after function definition on line 1",
        # ),
    ],
)
def test_invalid_def_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


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
def test_invalid_class_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)


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
        ("{**c, a: *b}", SyntaxError, "cannot use a starred expression in a dictionary value"),
    ],
)
def test_invalid_dict_key_value(
    python_parse_file, python_parse_str, tmp_path, source, exception, message
):
    parse_invalid_syntax(python_parse_file, python_parse_str, tmp_path, source, exception, message)
