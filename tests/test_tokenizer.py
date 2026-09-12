import io
import sys
from tokenize import (
    NEWLINE,
    NUMBER,
    ENDMARKER,
    TokenInfo,
    generate_tokens,
    NAME,
    OP,
    INDENT,
    DEDENT,
    STRING,
)

from pegen.tokenizer import Tokenizer


def test_peek_getnext():
    source = io.StringIO("# test\n1")
    t = Tokenizer(generate_tokens(source.readline))
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1")
    assert t.peek() == TokenInfo(
        NEWLINE, "", (2, 1), (2, 2), "1" if sys.version_info >= (3, 12) else ""
    )
    assert t.getnext() == TokenInfo(
        NEWLINE, "", (2, 1), (2, 2), "1" if sys.version_info >= (3, 12) else ""
    )


def test_mark_reset():
    source = io.StringIO("\n1 2")
    t = Tokenizer(generate_tokens(source.readline))
    index = t.mark()
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")
    t.reset(index)
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")


def test_last_non_whitespace():
    source = io.StringIO("\n1\n2")
    t = Tokenizer(generate_tokens(source.readline))
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1\n")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1\n")
    assert t.getnext() == TokenInfo(NEWLINE, "\n", (2, 1), (2, 2), "1\n")
    assert t.get_last_non_whitespace_token() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1\n")


def test_get_lines():
    source = io.StringIO("1\n2\n3")
    t = Tokenizer(generate_tokens(source.readline))
    while True:
        if t.getnext().type == ENDMARKER:
            break
    assert t.get_lines([1, 2, 3]) == ["1\n", "2\n", "3"]


def test_dedent():
    source = io.StringIO(
        """
def test(num):
    a = pmatch num:
        1: "One"
        2: "Two"
        3: "Three"
        _: "Number not between 1 and 3"

    return a
"""
    )
    t = Tokenizer(generate_tokens(source.readline))
    expected = [
        NAME,
        NAME,
        OP,
        NAME,
        OP,
        OP,
        NEWLINE,
        INDENT,
        NAME,
        OP,
        NAME,
        NAME,
        OP,
        NEWLINE,
        INDENT,
        NUMBER,
        OP,
        STRING,
        NEWLINE,
        NUMBER,
        OP,
        STRING,
        NEWLINE,
        NUMBER,
        OP,
        STRING,
        NEWLINE,
        NAME,
        OP,
        STRING,
        NEWLINE,
        DEDENT,
        NAME,
        NAME,
        NEWLINE,
        DEDENT,
        ENDMARKER,
    ]
    for i in range(len(expected)):
        assert expected[i] == t.getnext().type
