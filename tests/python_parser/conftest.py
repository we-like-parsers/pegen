""""Conftest for pure python parser."""
from pathlib import Path

import pytest

from pegen.build import build_parser
from ..utils import generate_parser


@pytest.fixture(scope="session")
def python_parser_cls():
    grammar_path = Path(__file__).parent.parent.parent / "data/python.gram"
    grammar = build_parser(grammar_path)[0]
    source_path = str(Path(__file__).parent / "parser_cache" / "py_parser.py")
    parser_cls = generate_parser(grammar, source_path, "PythonParser")

    return parser_cls
