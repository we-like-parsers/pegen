"""Test identifying unsupported syntax construction in older Python versions.

Note that we can request the parser to apply stricter bounds on the parsing but
not broader since we would not be able to generate the proper ast nodes.

"""
import io
import sys
import tokenize

import pytest

from pegen.tokenizer import Tokenizer

# matrix mul 3.5
@pytest.mark.parametrize("source", ["a @ b", "a @= b"])
def test_mat_mult(python_parser_cls, source):
    temp = io.StringIO(source)
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer, py_version=(3, 4))
    with pytest.raises(SyntaxError) as e:
        pp.parse("file")

    assert "The '@' operator is" in e.exconly()


# await 3.5
def test_await(python_parser_cls):
    temp = io.StringIO("await b")
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer, py_version=(3, 4))
    with pytest.raises(SyntaxError) as e:
        pp.file()

    assert "Await expressions are" in e.exconly()


# async 3.5
@pytest.mark.parametrize(
    "source, message",
    [
        ("async def f():\n    pass", "Async functions are"),
        ("async with a:\n    pass", "Async with statements are"),
        ("async for a in b:\n    pass", "Async for loops are"),
    ],
)
def test_async(python_parser_cls, source, message):
    temp = io.StringIO(source)
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer, py_version=(3, 4))
    with pytest.raises(SyntaxError) as e:
        pp.file()

    assert message in e.exconly()


# async comprehension 3.6
def test_async_comprehension(python_parser_cls):
    temp = io.StringIO("""[a async for a in b if c]""")
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer, py_version=(3, 5))
    with pytest.raises(SyntaxError) as e:
        pp.file()
    assert "Async comprehensions are" in e.exconly()


# variable annotation 3.6
@pytest.mark.parametrize("source", ["a: int = 1", "(a): int "])
def test_variable_annotation(python_parser_cls, source):
    temp = io.StringIO(source)
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer, py_version=(3, 5))
    with pytest.raises(SyntaxError) as e:
        pp.file()

    assert "Variable annotation syntax is" in e.exconly()


# pos only args 3.8
@pytest.mark.parametrize("source", ["def f(a,/):\n\tpass", "def f(a=1,/):\n\tpass"])
def test_pos_only_args(python_parser_cls, source):
    temp = io.StringIO(source)
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer, py_version=(3, 7))
    with pytest.raises(SyntaxError) as e:
        pp.file()

    assert "Positional only arguments are" in e.exconly()


# assignment operator 3.8
@pytest.mark.parametrize("source", ["a := 1"])
def test_assignment_operator(python_parser_cls, source):
    temp = io.StringIO(source)
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer, py_version=(3, 7))
    with pytest.raises(SyntaxError) as e:
        pp.file()

    assert "The ':=' operator is" in e.exconly()


# generic decorators 3.9
@pytest.mark.parametrize("source", ["@f[1]\ndef f():\n\tpass"])
def test_generic_decorators(python_parser_cls, source):
    temp = io.StringIO(source)
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer, py_version=(3, 8))
    with pytest.raises(SyntaxError) as e:
        pp.file()

    assert "Generic decorator are" in e.exconly()


# parenthesized with items 3.9
@pytest.mark.parametrize("source", ["with (a, b):\n\tpass"])
def test_parenthesized_with_items(python_parser_cls, source):
    temp = io.StringIO(source)
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer, py_version=(3, 8))
    with pytest.raises(SyntaxError) as e:
        pp.file()

    assert "Parenthesized with items" in e.exconly()


# match 3.10
@pytest.mark.parametrize(
    "source", ["match a:\n\tcase 1:\n\t\tpass", "match a", "match a:\ncase b"]
)
def test_match_statement(python_parser_cls, source):
    temp = io.StringIO(source)
    tokengen = tokenize.generate_tokens(temp.readline)
    tokenizer = Tokenizer(tokengen, verbose=False)
    pp = python_parser_cls(tokenizer, py_version=(3, 9))
    with pytest.raises(SyntaxError) as e:
        pp.file()

    assert "Pattern matching is" in e.exconly()
