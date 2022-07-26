import token
from abc import ABC, abstractmethod
from typing import Dict, Generic, Iterator, List, Protocol, Sequence, Tuple, TypeVar

Mark = int  # NewType('Mark', int)


TokenType = TypeVar(
    "TokenType",
)


class TokenInfo(Protocol[TokenType]):
    """Expected interface for element yielded by the token generator."""

    type: TokenType
    string: str
    start: Tuple[int, int]
    end: Tuple[int, int]
    line: str


class TokenTypes(ABC, Generic[TokenType]):
    """Token types that the system requires to know to operate.

    In addition to the token types listed below, we expect all hard keyword and
    any token used as is in the grammar to be associated with a unique token type
    listed in the subclass used by the parser.

    Among the five tokens listed below, any token that is not used in the grammar
    and hence never looked up by the parser can be omitted or given an arbitrary
    value.

    """

    NAME: TokenType
    NUMBER: TokenType
    STRING: TokenType
    OP: TokenType
    TYPE_COMMENT: TokenType

    def __init__(self) -> None:
        ttype = type(self.NAME)
        self.__dict__ |= {k: v for k, v in type(self).__dict__.items() if isinstance(v, ttype)}

    @abstractmethod
    def get_name_from_type(self, ttype: TokenType) -> str:
        pass

    @abstractmethod
    def is_whitespace_token(self, tok: TokenInfo[TokenType]) -> bool:
        pass

    @abstractmethod
    def is_relevant_token(
        self, tok: TokenInfo[TokenType], seen_tokens: Sequence[TokenInfo[TokenType]]
    ) -> bool:
        """Is the token relevant to the parser."""
        pass

    def format_tok(self, tok: TokenInfo[TokenType]) -> str:
        return f"{tok.start[0]}.{tok.start[1]}: {self.get_name_from_type(tok.type)}:{tok.string!r}"

    def shorttok(self, tok: TokenInfo[TokenType]) -> str:
        return "%-25.25s" % self.format_tok(tok)


class PythonTokenTypes(TokenTypes[int]):
    """Token types corresponding to the Python lexers."""

    NAME = token.NAME
    NUMBER = token.NUMBER
    STRING = token.STRING
    OP = token.OP
    TYPE_COMMENT = token.TYPE_COMMENT
    ENDMARKER = token.ENDMARKER
    NEWLINE = token.NEWLINE
    INDENT = token.INDENT
    DEDENT = token.DEDENT

    def get_name_from_type(self, ttype: int) -> str:
        return token.tok_name[ttype]

    def is_whitespace_token(self, tok: TokenInfo[int]) -> bool:
        return tok.type == self.ENDMARKER or (tok.type >= self.NEWLINE and tok.type <= self.DEDENT)

    def is_relevant_token(
        self, tok: TokenInfo[TokenType], seen_tokens: Sequence[TokenInfo[TokenType]]
    ) -> bool:
        if tok.type in (token.NL, token.COMMENT):
            return False
        if tok.type == token.ERRORTOKEN and tok.string.isspace():
            return False
        if tok.type == self.NEWLINE and seen_tokens and seen_tokens[-1].type == self.NEWLINE:
            return False
        return True


class Tokenizer(Generic[TokenType]):
    """Caching wrapper for the token generator.

    The peek method makes some assumptions on which tokens should be skipped
    based on their types. On should overwrite it in a subclass if those
    hypothesis do not match the parsed language.

    """

    _tokens: List[TokenInfo[TokenType]]

    def __init__(
        self,
        tokengen: Iterator[TokenInfo[TokenType]],
        token_types: TokenTypes[TokenType],
        *,
        path: str = "",
        verbose: bool = False,
    ):
        self.token_types = token_types
        self._tokengen = tokengen
        self._tokens = []
        self._index = 0
        self._verbose = verbose
        self._lines: Dict[int, str] = {}
        self._path = path
        if verbose:
            self.report(False, False)

    def getnext(self) -> TokenInfo[TokenType]:
        """Return the next token and updates the index."""
        cached = not self._index == len(self._tokens)
        tok = self.peek()
        self._index += 1
        if self._verbose:
            self.report(cached, False)
        return tok

    def peek(self) -> TokenInfo[TokenType]:
        """Return the next token *without* updating the index."""
        while self._index == len(self._tokens):
            tok = next(self._tokengen)
            if not self.token_types.is_relevant_token(tok, self._tokens):
                continue
            self._tokens.append(tok)
            if not self._path and tok.start[0] not in self._lines:
                self._lines[tok.start[0]] = tok.line
        return self._tokens[self._index]

    def diagnose(self) -> TokenInfo[TokenType]:
        if not self._tokens:
            self.getnext()
        return self._tokens[-1]

    def get_last_non_whitespace_token(self) -> TokenInfo[TokenType]:
        for tok in reversed(self._tokens[: self._index]):
            if not self.token_types.is_whitespace_token(tok):
                break
        return tok

    def get_lines(self, line_numbers: List[int]) -> List[str]:
        """Retrieve source lines corresponding to line numbers."""
        if self._lines:
            lines = self._lines
        else:
            n = len(line_numbers)
            lines = {}
            count = 0
            seen = 0
            with open(self._path) as f:
                for line in f:
                    count += 1
                    if count in line_numbers:
                        seen += 1
                        lines[count] = line
                        if seen == n:
                            break

        return [lines[n] for n in line_numbers]

    def mark(self) -> Mark:
        return self._index

    def reset(self, index: Mark) -> None:
        if index == self._index:
            return
        assert 0 <= index <= len(self._tokens), (index, len(self._tokens))
        old_index = self._index
        self._index = index
        if self._verbose:
            self.report(True, index < old_index)

    def report(self, cached: bool, back: bool) -> None:
        if back:
            fill = "-" * self._index + "-"
        elif cached:
            fill = "-" * self._index + ">"
        else:
            fill = "-" * self._index + "*"
        if self._index == 0:
            print(f"{fill} (Bof)")
        else:
            tok = self._tokens[self._index - 1]
            print(f"{fill} {self.token_types.shorttok(tok)}")
