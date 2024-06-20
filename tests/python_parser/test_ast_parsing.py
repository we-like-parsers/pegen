"""Test pure Python parser against cpython parser."""

import ast
import difflib
import io
import sys
import textwrap
import tokenize
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "filename",
    [
        pytest.param(
            "advanced_decorators.py",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 9), reason="Valid only in Python 3.9+"
            ),
        ),
        "assignment.py",
        "async.py",
        "call.py",
        "comprehensions.py",
        "expressions.py",
        "fstrings.py",
        "function_def.py",
        "imports.py",
        "lambdas.py",
        pytest.param(
            "multi_statement_per_line.py",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 9), reason="Col offset match only on Python 3.9+"
            ),
        ),
        "no_newline_at_end_of_file.py",
        "no_newline_at_end_of_file_with_comment.py",
        pytest.param(
            "pattern_matching.py",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 10), reason="Valid only in Python 3.10+"
            ),
        ),
        "simple_decorators.py",
        "statements.py",
        pytest.param(
            "try_except_group.py",
            marks=pytest.mark.skipif(
                sys.version_info <= (3, 11), reason="except* allowed only in Python 3.11+"
            ),
        ),
        pytest.param(
            "type_params.py",
            marks=pytest.mark.skipif(
                sys.version_info <= (3, 12),
                reason="type declarations allowed only in Python 3.12+",
            ),
        ),
        pytest.param(
            "with_statement_multi_items.py",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 9),
                reason="Parenthesized with items allowed only in Python 3.9+",
            ),
        ),
    ],
)
def test_parser(python_parse_file, python_parse_str, filename):
    path = Path(__file__).parent / "data" / filename
    with open(path) as f:
        source = f.read()

    for part in source.split("\n\n\n"):
        original = ast.parse(part)

        kwargs = dict(include_attributes=True)
        if sys.version_info >= (3, 9):
            kwargs["indent"] = "  "

        try:
            pp_ast = python_parse_str(part, "exec")
        except Exception:
            temp = io.StringIO(part)
            print("Parsing failed:")
            print("Source is:")
            print(textwrap.indent(part, "  "))
            temp = io.StringIO(part)
            print("Token stream is:")
            for t in tokenize.generate_tokens(temp.readline):
                print(t)
            print()
            print("CPython ast is:")
            print(ast.dump(original, **kwargs))
            raise

        o = ast.dump(original, **kwargs)
        p = ast.dump(pp_ast, **kwargs)
        diff = "\n".join(
            difflib.unified_diff(o.split("\n"), p.split("\n"), "cpython", "python-pegen")
        )
        if diff:
            print(part)
            print(diff)
        assert not diff

    o = ast.dump(ast.parse(source), **kwargs)
    p = ast.dump(python_parse_file(path), **kwargs)
    diff = "\n".join(difflib.unified_diff(o.split("\n"), p.split("\n"), "cpython", "python-pegen"))
    assert not diff
