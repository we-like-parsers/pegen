"""Test pure Python parser against cpython parser."""
import ast
import difflib
import io
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

    for part in source.split("\n\n\n"):
        original = ast.parse(part)
        temp = io.StringIO(part)
        tokengen = tokenize.generate_tokens(temp.readline)
        tokenizer = Tokenizer(tokengen, verbose=False)
        pp_ast = python_parser_cls(tokenizer).parse("file")

        with_attr = True
        if sys.version_info >= (3, 9):
            o = ast.dump(original, include_attributes=with_attr, indent="  ")
            p = ast.dump(pp_ast, include_attributes=with_attr, indent="  ")
        else:
            # Python 3.8 does not have indent and also add a kind=None to Constant nodes
            # which is useless but cause the test to fail.
            o = ast.dump(original, include_attributes=with_attr)
            p = ast.dump(pp_ast, include_attributes=with_attr).replace(" kind=None,", "")
        diff = "\n".join(
            difflib.unified_diff(o.split("\n"), p.split("\n"), "cpython", "python-pegen")
        )
        if diff:
            print(part)
            print(diff)
        assert not diff
