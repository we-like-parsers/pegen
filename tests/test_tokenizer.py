import io
from tokenize import NEWLINE, NUMBER, ENDMARKER, TokenInfo, generate_tokens

from pegen.tokenizer import Tokenizer, PythonTokenTypes


def test_peek_getnext() -> None:
    source = io.StringIO("# test\n1")
    t = Tokenizer(generate_tokens(source.readline), PythonTokenTypes())
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1")
    assert t.peek() == TokenInfo(NEWLINE, "", (2, 1), (2, 2), "")
    assert t.getnext() == TokenInfo(NEWLINE, "", (2, 1), (2, 2), "")


def test_mark_reset() -> None:
    source = io.StringIO("\n1 2")
    t = Tokenizer(generate_tokens(source.readline), PythonTokenTypes())
    index = t.mark()
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")
    t.reset(index)
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")


def test_last_non_whitespace() -> None:
    source = io.StringIO("\n1\n2")
    t = Tokenizer(generate_tokens(source.readline), PythonTokenTypes())
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1\n")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1\n")
    assert t.getnext() == TokenInfo(NEWLINE, "\n", (2, 1), (2, 2), "1\n")
    assert t.get_last_non_whitespace_token() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1\n")


def test_get_lines():
    source = io.StringIO("1\n2\n3")
    t = Tokenizer(generate_tokens(source.readline), PythonTokenTypes())
    while True:
        if t.getnext().type == ENDMARKER:
            break
    assert t.get_lines([1, 2, 3]) == ["1\n", "2\n", "3"]
