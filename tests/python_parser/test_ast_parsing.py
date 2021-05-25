"""Test pure Python parser against cpython parser."""
import ast
import difflib
import sys
import tokenize
from pathlib import Path

import pytest

from pegen.tokenizer import Tokenizer


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
        "function_def.py",
        "imports.py",
        "lambdas.py",
        pytest.param(
            "pattern_matching.py",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 10), reason="Valid only in Python 3.10+"
            ),
        ),
        "simple_decorators.py",
        "statements.py",
    ],
)
def test_parser(python_parser_cls, filename):
    path = Path(__file__).parent / "data" / filename
    with open(path) as f:
        source = f.read()
    original = ast.parse(source, str(path))

    with open(path) as f:
        tokengen = tokenize.generate_tokens(f.readline)
        tokenizer = Tokenizer(tokengen, verbose=False)
        pp_ast = python_parser_cls(tokenizer, filename=str(path)).file()

    with_attr = True
    o = ast.dump(original, include_attributes=with_attr, indent="  ")
    p = ast.dump(pp_ast, include_attributes=with_attr, indent="  ")
    diff = "\n".join(difflib.unified_diff(o.split("\n"), p.split("\n"), "cpython", "python-pegen"))
    print(diff)
    assert not diff
