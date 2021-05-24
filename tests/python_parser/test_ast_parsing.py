"""Test pure Python parser against cpython parser."""
import ast
from pathlib import Path

import pytest
from deepdiff import DeepDiff


@pytest.mark.parametrize("filename",[])
def test_parser(parser, filename):
    path = Path(__file__).parent / filename
    with open(path) as f:
        source = f.read()
    original = ast.parse(source, str(path))
    pp_ast = parser.parse_file(source, str(path))
    diff = DeepDiff(original, pp_ast)
    print(diff)
    assert not diff
