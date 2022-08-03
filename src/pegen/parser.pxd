cdef class Parser:
    cdef tuple KEYWORDS
    cdef tuple SOFT_KEYWORDS

    cdef object _tokenizer
    cdef bint _verbose
    cdef int _level
    cdef dict _cache
    cdef int in_recursive_rule
    cdef object _mark  # self._tokenizer.mark
    cdef object _reset  # self._tokenizer.reset
    cdef bint call_invalid_rules

    # cdef str showpeek(self)

    # cdef object name(self)
    # cdef object number(self)
    # cdef object string(self)
    # cdef object op(self)
    # cdef object type_comment(self)
    # cdef object soft_keyword(self)
    # cdef object expect(self, str type)
    # cdef object expect_forced(self, object res, str expectation)

    # @cython.locals(mark=cython.int, ok=cython.bint)
    # cdef bint positive_lookahead(self, object func, *args)

    # @cython.locals(mark=cython.int, ok=cython.bint)
    # cdef bint negative_lookahead(self, object func, *args)

    # cdef SyntaxError make_syntax_error(self, str message, str filename = "<unknown>"):
