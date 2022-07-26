import io
from tokenize import NEWLINE, NUMBER, TokenInfo, generate_tokens

import pytest

from pegen.tokenizer import Tokenizer


def test_peek_getnext():
    source = io.StringIO("# test\n1")
    t = Tokenizer(generate_tokens(source.readline))
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1")
    assert t.peek() == TokenInfo(NEWLINE, "", (2, 1), (2, 2), "")
    assert t.getnext() == TokenInfo(NEWLINE, "", (2, 1), (2, 2), "")


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


if __name__ == "__main__":
    pytest.main([__file__])
