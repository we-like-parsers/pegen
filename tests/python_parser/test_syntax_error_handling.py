"""Test syntax errors for cases where the parser can generate helpful messages."""
import sys

import pytest


def parse_invalid_syntax(
    python_parse_file, python_parse_str, tmp_path, source, exc_cls, message, start, end
):

    # Check we obtain the expected error from Python
    try:
        exec(source, {}, {})
    except exc_cls as py_e:
        py_exc = py_e
    except Exception as py_e:
        assert (
            False
        ), f"Python produced {py_e.__class__.__name__} instead of {exc_cls.__name__}: {py_e}"
    else:
        assert False, f"Python did not throw any exception, expected {exc_cls}"

    # Check our parser raises both from str and file mode.
    with pytest.raises(exc_cls) as e:
        python_parse_str(source, "exec")

    print(str(e.exconly()))
    assert message in str(e.exconly())

    test_file = tmp_path / "test.py"
    with open(test_file, "w") as f:
        f.write(source)

    with pytest.raises(exc_cls) as e:
        python_parse_file(str(test_file))

    # Check Python message but do not expect message to match for earlier Python versions
    if sys.version_info >= (3, 10):
        # NOTE ugly hack for 1 CPython bug
        if exc_cls is SyntaxError and e.type is IndentationError:
            assert message.replace("'", "") in py_exc.args[0]
        else:
            assert message in py_exc.args[0]

    print(str(e.exconly()))
    assert message in str(e.exconly())

    # Check start/end line/column on Python 3.10
    if sys.version_info >= (3, 10):
        for parser, exc in [("Python", py_exc), ("pegen", e.value)]:
            if (
                exc.lineno != start[0]
                or exc.offset != start[1]
                # Do not check end for indentation errors
                or (not isinstance(e, IndentationError) and exc.end_lineno != end[0])
                or (not isinstance(e, IndentationError) and (end[1] is not None and exc.end_offset != end[1]))
            ):
                raise ValueError(
                    f"Expected locations of {start} and {end}, but got "
                    f"{(exc.lineno, exc.offset)} and {(exc.end_lineno, exc.end_offset)} "
                    f"from {parser}"
                )


@pytest.mark.parametrize(
    "source, message, start, end",
    [
        ("f'a = { 1 + }'", "line 1", (1, 1), (1, 15)),
        ("(\n\t'b'\n\tf'a = { 1 + }'\n)", "line 3", (3, 2), (3, 16)),
    ],
)
def test_syntax_error_in_str(
    python_parse_file, python_parse_str, tmp_path, source, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
    )


@pytest.mark.parametrize(
    "source, message, start, end",
    [
        ("a 1", "invalid syntax. Perhaps you forgot a comma?", (1, 1), (1, 4)),
        ("2 if 4", "expected 'else' after 'if' expression", (1, 1), (1, 7)),
        ("a 1 if b else 2", "invalid syntax. Perhaps you forgot a comma?", (1, 1), (1, 16)),
        ("a 1ambda: 1", "invalid syntax. Perhaps you forgot a comma?", (1, 1), (1, 4)),
        ("print 1", "Missing parentheses in call to 'print'", (1, 1), (1, 8)),
        ("exec 1", "Missing parentheses in call to 'exec'", (1, 1), (1, 7)),
        ("a if b", "expected 'else' after 'if' expression", (1, 1), (1, 7)),
        ("c = a if b:", "SyntaxError: invalid syntax", (None, None), (None, None)),
    ],
)
def test_invalid_expression(
    python_parse_file, python_parse_str, tmp_path, source, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
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
    "source, message, start, end",
    [
        # Invalid arguments rules
        (
            "f(**a, *b)",
            "iterable argument unpacking follows keyword argument unpacking",
            (1, 3),
            (1, 6),
        ),
        ("f(a for a in b, c)", "Generator expression must be parenthesized", (1, 3), (1, 10)),
        ("f(a for a in b if a, c)", "Generator expression must be parenthesized", (1, 3), (1, 10)),
        (
            "f(a for a in b, c for c in d)",
            "Generator expression must be parenthesized",
            (1, 3),
            (1, 10),
        ),
        (
            "f(a=1 for i in range(10))",
            "invalid syntax. Maybe you meant '==' or ':=' instead of '='?",
            (1, 3),
            (1, 5),
        ),
        ("f(a, b for b in c)", "Generator expression must be parenthesized", (1, 6), (1, 18)),
        ("f(a, b for b in c, d)", "Generator expression must be parenthesized", (1, 6), (1, 18)),
        ("f(**a, b)", "positional argument follows keyword argument unpacking", (1, 9), (1, 10)),
        ("f(a=1, b)", "positional argument follows keyword argument", (1, 9), (1, 10)),
        # Invalid kwarg rules
        (
            "f(b=c for c in d)",
            "invalid syntax. Maybe you meant '==' or ':=' instead of '='?",
            (1, 3),
            (1, 5),
        ),
        (
            "f(1 + b=2)",
            'expression cannot contain assignment, perhaps you meant "=="?',
            (1, 3),
            (1, 9),
        ),
    ],
)
def test_invalid_call_arguments(
    python_parse_file, python_parse_str, tmp_path, source, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
    )


@pytest.mark.parametrize(
    "source, message, start, end",
    [
        ("'a' = 1", "cannot assign to literal", (1, 2), (1, 5)),
        ("1 = 1", "cannot assign to 1", (1, 1), (1, 2)),
        ("True = 1", "cannot assign to True", (1, 1), (1, 5)),
        ("False = 1", "cannot assign to False", (1, 1), (1, 6)),
        ("... = 1", "cannot assign to Ellipsis", (1, 1), (1, 4)),
        ("None = 1", "cannot assign to None", (1, 1), (1, 5)),
        (
            "(a, b) : int = (1, 2)",
            "only single target (not tuple) can be annotated",
            (1, 1),
            (1, 7),
        ),
        (
            "[a, b] : int = [1, 2]",
            "only single target (not list) can be annotated",
            (1, 1),
            (1, 7),
        ),
        (
            "([a, b]) : int = (1, 2)",
            "only single target (not list) can be annotated",
            (1, 2),
            (1, 8),
        ),
        (
            "a, b: int, int = 1, 2",
            "only single target (not tuple) can be annotated",
            (1, 1),
            (1, 2),
        ),
        ("{a, b} : set", "illegal target for annotation", (1, 1), (1, 7)),
        ("a + 1 = 2", "cannot assign to expression", (1, 1), (1, 6)),
        ("[i for i in range(2)] = 2", "cannot assign to list comprehension", (1, 1), (1, 22)),
        ("yield a = 1", "assignment to yield expression not possible", (1, 1), (1, 8)),
        ("a = yield b = 1", "assignment to yield expression not possible", (1, 5), (1, 12)),
        (
            "a + 1 += 1",
            "expression is an illegal expression for augmented assignment",
            (1, 1),
            (1, 6),
        ),
        (
            "a + 1 += yield",
            "expression is an illegal expression for augmented assignment",
            (1, 1),
            (1, 6),
        ),
        (
            "[i for i in range(2)] += 1",
            "list comprehension is an illegal expression for augmented assignment",
            (1, 1),
            (1, 22),
        ),
        ("a += raise", "invalid syntax", (None, None), (None, None)),
    ],
)
def test_invalid_assignments(
    python_parse_file, python_parse_str, tmp_path, source, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
    )


@pytest.mark.parametrize(
    "source, message, start, end",
    [
        ("del [i for i in range(2)]", "cannot delete list comprehension", (1, 5), (1, 26)),
        ("del a + 1", "cannot delete expression", (1, 5), (1, 10)),
    ],
)
def test_invalid_del_statements(
    python_parse_file, python_parse_str, tmp_path, source, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
    )


@pytest.mark.parametrize(
    "source, message, start, end",
    [
        (
            "(*a for a in enumerate(range(5)))",
            "iterable unpacking cannot be used in comprehension",
            (1, 2),
            (1, 4),
        ),
        (
            "[*a for a in enumerate(range(5))]",
            "iterable unpacking cannot be used in comprehension",
            (1, 2),
            (1, 4),
        ),
        (
            "{*a for a in enumerate(range(5))}",
            "iterable unpacking cannot be used in comprehension",
            (1, 2),
            (1, 4),
        ),
        (
            "[a, a for a in range(5)]",
            "did you forget parentheses around the comprehension target?",
            (1, 2),
            (1, 6),
        ),
        (
            "[a, a for a in range(5)]",
            "did you forget parentheses around the comprehension target?",
            (1, 2),
            (1, 6),
        ),
        (
            "[a,  for a in range(5)]",
            "did you forget parentheses around the comprehension target?",
            (1, 2),
            (1, 4),
        ),
        (
            "[a,  for a in range(5)]",
            "did you forget parentheses around the comprehension target?",
            (1, 2),
            (1, 4),
        ),
        (
            "{**a for a in [{1: 2}]}",
            "dict unpacking cannot be used in dict comprehension",
            (1, 2),
            (1, 4),
        ),
        # check cuts
        ("(a for a in raise)", "invalid syntax", (None, None), (None, None)),
        ("(a async for a in raise)", "invalid syntax", (None, None), (None, None)),
    ],
)
def test_invalid_comprehension(
    python_parse_file, python_parse_str, tmp_path, source, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
    )


@pytest.mark.parametrize(
    "source, start, end",
    [
        ("def f(a=1, b):\n\tpass", (1, 12), (1, 13)),
        ("def f(a=1, /, b):\n\tpass", (1, 15), (1, 16)),
        ("lambda x=1, y: x", (1, 13), (1, 14)),
        ("lambda x=1, /, y: x", (1, 16), (1, 17)),
    ],
)
def test_invalid_parameters(python_parse_file, python_parse_str, tmp_path, source, start, end):
    parse_invalid_syntax(
        python_parse_file,
        python_parse_str,
        tmp_path,
        source,
        SyntaxError,
        "non-default argument follows default argument",
        start,
        end,
    )


@pytest.mark.parametrize(
    "source, start, end",
    [
        ("def f(a, *):\n\tpass", (1, 10), (1, 11)),
        ("def f(a, *,):\n\tpass", (1, 10), (1, 11)),
        ("def f(a, *, **):\n\tpass", (1, 10), (1, 11)),
        ("lambda a, *: a", (1, 12), (1, 13)),
        ("lambda a, *, **:a", (1, 14), (1, 16)),
    ],
)
def test_invalid_star_etc(python_parse_file, python_parse_str, tmp_path, source, start, end):
    parse_invalid_syntax(
        python_parse_file,
        python_parse_str,
        tmp_path,
        source,
        SyntaxError,
        "named arguments must follow bare *",
        start,
        end,
    )


@pytest.mark.parametrize(
    "source, message, start, end",
    [
        ("with open(a) as {b: 1}:\n\tpass", "cannot assign to dict", (1, 17), (1, 23)),
        ("with open(a) as {b}:\n\tpass", "cannot assign to set", (1, 17), (1, 20)),
        ("with open(a) as 1:\n\tpass", "cannot assign to 1", (1, 17), (1, 18)),
    ],
)
def test_invalid_with_item(
    python_parse_file, python_parse_str, tmp_path, source, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
    )


@pytest.mark.parametrize(
    "source, message, start, end",
    [
        ("for {a} in [[1]]:\n\tpass", "cannot assign to comparison", (1, 5), (1, 17)),
        ("async for (a := i)", "cannot assign to named expression", (1, 12), (1, 18)),
    ],
)
def test_invalid_for_target(
    python_parse_file, python_parse_str, tmp_path, source, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
    )


@pytest.mark.parametrize(
    "source, message, start, end",
    [
        ("a = (1+1 := 2)", "cannot use assignment expressions with expression", (1, 6), (1, 9)),
        ("a := raise", "invalid syntax", (None, None), (None, None)),
    ],
)
def test_named_expression(
    python_parse_file, python_parse_str, tmp_path, source, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
    )


@pytest.mark.parametrize(
    "source, message, start, end",
    [
        ("a = (*b)", "cannot use starred expression here", (1, 6), (1, 8)),
        ("a = (**b)", "cannot use double starred expression here", (1, 6), (1, 8)),
    ],
)
def test_invalid_group(python_parse_file, python_parse_str, tmp_path, source, message, start, end):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
    )


@pytest.mark.parametrize(
    "source, message, start, end",
    [
        (
            "from a import b,",
            "trailing comma not allowed without surrounding parentheses",
            (1, 17),
            (1, 18),
        ),
        ("from a import b, and 3", "invalid syntax", (None, None), (None, None)),
        ("from a import raise", "invalid syntax", (None, None), (None, None)),
    ],
)
def test_invalid_import_from_as_names(
    python_parse_file, python_parse_str, tmp_path, source, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, SyntaxError, message, start, end
    )


@pytest.mark.parametrize(
    "source, exception, message, start, end",
    [
        (
            "with open(a) as f, b as d:\npass",
            IndentationError,
            "expected an indented block after 'with' statement on line 1",
            None,
            None,
        ),
        (
            "\nasync with (open(a) as f, b as d):\npass",
            IndentationError,
            "expected an indented block after 'with' statement on line 2",
            None,
            None,
        ),
        ("with open(a) as f, b as d\npass", SyntaxError, "expected ':'", (1, 26), (1, 27)),
        (
            "\nasync with (open(a) as f, b as d)\npass",
            SyntaxError,
            "expected ':'",
            (2, 34),
            (2, 35),
        ),
    ],
)
def test_invalid_with_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )


@pytest.mark.parametrize(
    "source, exception, message, start, end",
    [
        (
            "try:\npass",
            IndentationError,
            "expected an indented block after 'try' statement on line 1",
            None,
            None,
        ),
        ("try\n\tpass", SyntaxError, "expected ':'", (1, 4), (1, 5)),
        (
            "try:\n\tpass\na = 1",
            SyntaxError,
            "expected 'except' or 'finally' block",
            (3, 1),
            (3, 2),
        ),
    ],
)
def test_invalid_try_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )


@pytest.mark.parametrize(
    "source, exception, message, start, end",
    [
        (
            "try:\n\tpass\nexcept:\npass",
            IndentationError,
            "expected an indented block after 'except' statement on line 3",
            None,
            None,
        ),
        (
            "try:\n\tpass\nexcept Exception:\npass",
            IndentationError,
            "expected an indented block after 'except' statement on line 3",
            None,
            None,
        ),
        (
            "try:\n\tpass\nexcept Exception as e:\npass",
            IndentationError,
            "expected an indented block after 'except' statement on line 3",
            None,
            None,
        ),
        (
            "try:\n\tpass\nexcept ValueError, IndexError as e:",
            SyntaxError,
            "exception group must be parenthesized",
            (3, 8),
            (3, 36),
        ),
        (
            "try:\n\tpass\nexcept ValueError, IndexError:",
            SyntaxError,
            "exception group must be parenthesized",
            (3, 8),
            (3, 31),
        ),
        (
            "try:\n\tpass\nexcept ValueError, IndexError,:",
            SyntaxError,
            "exception group must be parenthesized",
            (3, 8),
            (3, 32),
        ),
        (
            "try:\n\tpass\nexcept ValueError, IndexError, a=1:",
            SyntaxError,
            "invalid syntax",
            (None, None),
            (None, None),
        ),
        ("try:\n\tpass\nexcept Exception\npass", SyntaxError, "expected ':'", (3, 17), (3, 18)),
        (
            "try:\n\tpass\nexcept Exception as e\npass",
            SyntaxError,
            "expected ':'",
            (3, 22),
            (3, 23),
        ),
        ("try:\n\tpass\nexcept\npass", SyntaxError, "expected ':'", (3, 7), (3, 8)),
    ],
)
def test_invalid_except_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )


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
    "source, exception, message, start, end",
    [
        ("match a\n\tpass", SyntaxError, "expected ':'", (1, 8), (1, 9)),
        (
            "match a:\npass",
            IndentationError,
            "expected an indented block after 'match' statement on line 1",
            None,
            None,
        ),
    ],
)
def test_invalid_match_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Valid only in Python 3.10+")
@pytest.mark.parametrize(
    "source, exception, message, start, end",
    [
        ("match a:\n\tcase 1\n\t\tpass", SyntaxError, "expected ':'", (2, 8), (2, 9)),
        (
            "match a:\n\tcase 1:\n\tpass",
            IndentationError,
            "expected an indented block after 'case' statement on line 2",
            None,
            None,
        ),
    ],
)
def test_invalid_case_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Valid only in Python 3.10+")
@pytest.mark.parametrize(
    "source, exception, message, start, end",
    [
        # As pattern
        (
            "match a:\n\tcase 1 as _:\n\t\tpass",
            SyntaxError,
            "cannot use '_' as a target",
            (2, 12),
            (2, 13),
        ),
        (
            "match a:\n\tcase 1 as 1+1:\n\t\tpass",
            SyntaxError,
            "invalid pattern target",
            (2, 12),
            (2, 15),
        ),
        # Class pattern
        (
            "match a:\n\tcase Foo(z=1, y=2, x):\n\t\tpass",
            SyntaxError,
            "positional patterns follow keyword patterns",
            (2, 21),
            (2, 22),
        ),
        (
            "match a:\n\tcase Foo(a, z=1, y=2, x):\n\t\tpass",
            SyntaxError,
            "positional patterns follow keyword patterns",
            (2, 24),
            (2, 25),
        ),
        (
            "match a:\n\tcase Foo(z=1, x, y=2):\n\t\tpass",
            SyntaxError,
            "positional patterns follow keyword patterns",
            (2, 16),
            (2, 17),
        ),
        (
            "match a:\n\tcase Foo(a=b, c, d=e, f, g=h, i, j=k, ...):\n\t\tpass",
            SyntaxError,
            "positional patterns follow keyword patterns",
            (2, 16),
            (2, 17),
        ),
        (
            "match x:\n\tcase -1j + 1j:\n\t\tpass",
            SyntaxError,
            "real number required in complex literal",
        ),
        (
            "match x:\n\tcase -1 + 1:\n\t\tpass",
            SyntaxError,
            "imaginary number required in complex literal",
        )
    ],
)
def test_invalid_case_pattern(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )


@pytest.mark.parametrize(
    "source, exception, message, start, end",
    [
        ("if a\n\tpass", SyntaxError, "expected ':'", (1, 5), (1, 6)),
        (
            "if a:\npass",
            IndentationError,
            "expected an indented block after 'if' statement on line 1",
            None,
            None,
        ),
    ],
)
def test_invalid_if_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )


@pytest.mark.parametrize(
    "source, exception, message, start, end",
    [
        ("if a:\n\tpass\nelif a\n\tpass", SyntaxError, "expected ':'", (3, 7), (3, 8)),
        (
            "if a:\n\tpass\nelif b:\npass",
            IndentationError,
            "expected an indented block after 'elif' statement on line 3",
            None,
            None,
        ),
    ],
)
def test_invalid_elif_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )


@pytest.mark.parametrize(
    "source, exception, message, start, end",
    [
        ("if a:\n\tpass\nelse\n\tpass", SyntaxError, "expected ':'", (3, 5), (3, 6)),
        (
            "if a:\n\tpass\nelse:\npass",
            IndentationError,
            "expected an indented block after 'else' statement on line 3",
            None,
            None,
        ),
    ],
)
def test_invalid_else_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )


@pytest.mark.parametrize(
    "source, exception, message, start, end",
    [
        ("while a\n\tpass", SyntaxError, "expected ':'", (1, 8), (1, 9)),
        (
            "while a:\npass",
            IndentationError,
            "expected an indented block after 'while' statement on line 1",
            None,
            None,
        ),
    ],
)
def test_invalid_while_stmt(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )


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
    "source, exception, message, start, end",
    [
        ("{a: 1, b}", SyntaxError, "':' expected after dictionary key", (1, 7), (1, 9)),
        ("{a: 1, c: 2, b}", SyntaxError, "':' expected after dictionary key", (1, 13), (1, 15)),
        (
            "{a: 1, b:}",
            SyntaxError,
            "expression expected after dictionary key and ':'",
            (1, 9),
            (1, 10),
        ),
        (
            "{c: 1, a: *b}",
            SyntaxError,
            "cannot use a starred expression in a dictionary value",
            (1, 11),
            (1, 14),
        ),
        ("{b:}", SyntaxError, "expression expected after dictionary key and ':'", (1, 3), (1, 4)),
        (
            "{b:, c}",
            SyntaxError,
            "expression expected after dictionary key and ':'",
            (1, 3),
            (1, 4),
        ),
        (
            "{a: *b}",
            SyntaxError,
            "cannot use a starred expression in a dictionary value",
            (1, 5),
            (1, 8),
        ),
        (
            "{**c, a: *b}",
            SyntaxError,
            "cannot use a starred expression in a dictionary value",
            (1, 10),
            (1, 13),
        ),
    ],
)
def test_invalid_dict_key_value(
    python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
):
    parse_invalid_syntax(
        python_parse_file, python_parse_str, tmp_path, source, exception, message, start, end
    )
