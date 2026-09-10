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
        pytest.param(
            "comprehensions_unpacking.py",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 15),
                reason="Unpacking in comprehensions allowed only in Python 3.15+",
            ),
        ),
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


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="Pattern matching allowed only in Python 3.10+"
)
def test_pattern_matching_wildcard_ast(python_parse_str):
    source = "match x:\n    case _:\n        pass\n    case [*_]:\n        pass\n"
    tree = python_parse_str(source, "exec")
    assert isinstance(tree.body[0].cases[0].pattern, ast.MatchAs)
    assert tree.body[0].cases[0].pattern.name is None
    assert tree.body[0].cases[0].pattern.pattern is None
    assert isinstance(tree.body[0].cases[1].pattern, ast.MatchSequence)
    assert isinstance(tree.body[0].cases[1].pattern.patterns[0], ast.MatchStar)
    assert tree.body[0].cases[1].pattern.patterns[0].name is None


@pytest.mark.skipif(
    sys.version_info < (3, 11), reason="Star unpack in annotations allowed only in Python 3.11+"
)
def test_star_annotation_ast(python_parse_str):
    source = "def f(*args: *Ts):\n    pass\n"
    tree = python_parse_str(source, "exec")
    assert tree.body[0].args.vararg.annotation is not None


@pytest.mark.skipif(
    sys.version_info < (3, 14), reason="PEP 758 unparenthesized except only in Python 3.14+"
)
def test_unparenthesized_except_ast(python_parse_str):
    source = "try:\n    pass\nexcept ValueError, IndexError:\n    pass\n"
    tree = python_parse_str(source, "exec")
    handler = tree.body[0].handlers[0]
    assert isinstance(handler.type, ast.Tuple)
    assert len(handler.type.elts) == 2


@pytest.mark.skipif(
    sys.version_info < (3, 14), reason="PEP 758 unparenthesized except* only in Python 3.14+"
)
def test_unparenthesized_except_star_ast(python_parse_str):
    source = "try:\n    pass\nexcept* ValueError, IndexError:\n    pass\n"
    tree = python_parse_str(source, "exec")
    handler = tree.body[0].handlers[0]
    assert isinstance(handler.type, ast.Tuple)
    assert len(handler.type.elts) == 2


@pytest.mark.skipif(sys.version_info < (3, 15), reason="is_lazy added in Python 3.15+")
def test_lazy_imports_ast(python_parse_str):
    tree = python_parse_str("import foo\nfrom bar import baz\n", "exec")
    assert tree.body[0].is_lazy == 0
    assert tree.body[1].is_lazy == 0
