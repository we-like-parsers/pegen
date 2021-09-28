About PEG parsers
=================

.. highlight:: none

How PEG Parsers Work
--------------------

.. _how-peg-parsers-work:

A PEG (Parsing Expression Grammar) grammar (like the current one) differs from a
context-free grammar in that the way it is written more closely
reflects how the parser will operate when parsing it. The fundamental technical
difference is that the choice operator is ordered. This means that when writing::

  rule: A | B | C

a context-free-grammar parser (like an LL(1) parser) will generate constructions
that given an input string will *deduce* which alternative (``A``, ``B`` or ``C``)
must be expanded, while a PEG parser will check if the first alternative succeeds
and only if it fails, will it continue with the second or the third one in the
order in which they are written. This makes the choice operator not commutative.

Unlike LL(1) parsers, PEG-based parsers cannot be ambiguous: if a string parses,
it has exactly one valid parse tree. This means that a PEG-based parser cannot
suffer from the ambiguity problems that can arise with LL(1) parsers and with
context-free grammars in general.

PEG parsers are usually constructed as a recursive descent parser in which every
rule in the grammar corresponds to a function in the program implementing the
parser and the parsing expression (the "expansion" or "definition" of the rule)
represents the "code" in said function. Each parsing function conceptually takes
an input string as its argument, and yields one of the following results:

* A "success" result. This result indicates that the expression can be parsed by
  that rule and the function may optionally move forward or consume one or more
  characters of the input string supplied to it.
* A "failure" result, in which case no input is consumed.

Notice that "failure" results do not imply that the program is incorrect, nor do
they necessarily mean that the parsing has failed. Since the choice operator is
ordered, a failure very often merely indicates "try the following option".  A
direct implementation of a PEG parser as a recursive descent parser will present
exponential time performance in the worst case, because PEG parsers have
infinite lookahead (this means that they can consider an arbitrary number of
tokens before deciding for a rule).  Usually, PEG parsers avoid this exponential
time complexity with a technique called "packrat parsing" [1]_ which not only
loads the entire program in memory before parsing it but also allows the parser
to backtrack arbitrarily. This is made efficient by memoizing the rules already
matched for each position. The cost of the memoization cache is that the parser
will naturally use more memory than a simple LL(1) parser, which normally are
table-based. 


Key ideas
~~~~~~~~~

.. important::
    Don't try to reason about a PEG grammar in the same way you would to with an EBNF
    or context free grammar. PEG is optimized to describe **how** input strings will
    be parsed, while context-free grammars are optimized to generate strings of the
    language they describe (in EBNF, to know if a given string is in the language, you need
    to do work to find out as it is not immediately obvious from the grammar).

* Alternatives are ordered ( ``A | B`` is not the same as ``B | A`` ).
* If a rule returns a failure, it doesn't mean that the parsing has failed,
  it just means "try something else".
* By default PEG parsers run in exponential time, which can be optimized to linear by
  using memoization.
* If parsing fails completely (no rule succeeds in parsing all the input text), the
  PEG parser doesn't have a concept of "where the :exc:`SyntaxError` is".


Consequences or the ordered choice operator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _consequences-of-ordered-choice:

Although PEG may look like EBNF, its meaning is quite different. The fact
that in PEG parsers alternatives are ordered (which is at the core of how PEG
parsers work) has deep consequences, other than removing ambiguity.

If a rule has two alternatives and the first of them succeeds, the second one is
**not** attempted even if the caller rule fails to parse the rest of the input.
Thus the parser is said to be "eager". To illustrate this, consider
the following two rules (in these examples, a token is an individual character): ::

    first_rule:  ( 'a' | 'aa' ) 'a'
    second_rule: ('aa' | 'a'  ) 'a'

In a regular EBNF grammar, both rules specify the language ``{aa, aaa}`` but
in PEG, one of these two rules accepts the string ``aaa`` but not the string
``aa``. The other does the opposite -- it accepts the string the string ``aa``
but not the string ``aaa``. The rule ``('a'|'aa')'a'`` does
not accept ``aaa`` because ``'a'|'aa'`` consumes the first ``a``, letting the
final ``a`` in the rule consume the second, and leaving out the third ``a``.
As the rule has succeeded, no attempt is ever made to go back and let
``'a'|'aa'`` try the second alternative. The expression ``('aa'|'a')'a'`` does
not accept ``aa`` because ``'aa'|'a'`` accepts all of ``aa``, leaving nothing
for the final ``a``. Again, the second alternative of ``'aa'|'a'`` is not
tried.

.. caution::

    The effects of ordered choice, such as the ones illustrated above, may be hidden by many levels of rules.

For this reason, writing rules where an alternative is contained in the next one is in almost all cases a mistake,
for example: ::

    my_rule:
        | 'if' expression 'then' block
        | 'if' expression 'then' block 'else' block

In this example, the second alternative will never be tried because the first one will
succeed first (even if the input string has an ``'else' block`` that follows). To correctly
write this rule you can simply alter the order: ::

    my_rule:
        | 'if' expression 'then' block 'else' block
        | 'if' expression 'then' block

In this case, if the input string doesn't have an ``'else' block``, the first alternative
will fail and the second will be attempted without said part.

Grammatical elements and rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pegen has some special grammatical elements and rules:

* Strings with single quotes (') (e.g. ``'class'``) denote KEYWORDS.
* Strings with double quotes (") (e.g. ``"match"``) denote SOFT KEYWORDS.
* Upper case names (e.g. ``NAME``) denote tokens in the :file:`Grammar/Tokens` file.
* Rule names starting with `invalid_` are used for specialized syntax errors.

  - These rules are NOT used in the first pass of the parser.
  - Only if the first pass fails to parse, a second pass including the invalid
    rules will be executed.
  - If the parser fails in the second phase with a generic syntax error, the
    location of the generic failure of the first pass will be used (this avoids
    reporting incorrect locations due to the invalid rules).
  - The order of the alternatives involving invalid rules matter
    (like any rule in PEG).

Tokenization
~~~~~~~~~~~~

It is common among PEG parser frameworks that the parser does both the parsing and the tokenization,
but this does not happen in Pegen. The reason is that the Python language needs a custom tokenizer
to handle things like indentation boundaries, some special keywords like ``ASYNC`` and ``AWAIT``
(for compatibility purposes), backtracking errors (such as unclosed parenthesis), dealing with encoding,
interactive mode and much more. Some of these reasons are also there for historical purposes, and some
others are useful even today.

Tokens are restricted the the ones available in the ``tokenize`` module of the
Python interpreter that is used to generate the parser. This means that
tokenization of any parser generated by ``pegen`` must be a subset of the
tokenization that Python itself uses.

Memoization
~~~~~~~~~~~

As described previously, to avoid exponential time complexity in the parser, memoization is used. 

Memoization can be expensive both in memory and time. Although the memory cost
is obvious (the parser needs memory for storing previous results in the cache)
the execution time cost comes for continuously checking if the given rule has a
cache hit or not. In many situations, just parsing it again can be faster.
``pegen`` **disables memoization by default** except for rules with the special
marker `memo` after the rule name (and type, if present): ::

    rule_name[typr] (memo):
        ...

By selectively turning on memoization for a handful of rules, the parser becomes faster and uses less memory.

.. note::
    Left-recursive rules always use memoization, since the implementation of left-recursion depends on it.

To know if a new rule needs memoization or not, benchmarking is required
(comparing execution times and memory usage of some considerably big files with
and without memoization). 

Hard and Soft keywords
~~~~~~~~~~~~~~~~~~~~~~

.. note::
    In the grammar files, keywords are defined using **single quotes** (e.g. `'class'`) while soft
    keywords are defined using **double quotes** (e.g. `"match"`).

There are two kinds of keywords allowed in pegen grammars: *hard* and *soft*
keywords. The difference between hard and soft keywords is that hard keywords
are always reserved words, even in positions where they make no sense (e.g. ``x = class + 1``),
while soft keywords only get a special meaning in context. Trying to use a hard
keyword as a variable will always fail:

.. code-block::

    >>> class = 3
    File "<stdin>", line 1
        class = 3
            ^
    SyntaxError: invalid syntax
    >>> foo(class=3)
    File "<stdin>", line 1
        foo(class=3)
            ^^^^^
    SyntaxError: invalid syntax

While soft keywords don't have this limitation if used in a context other the one where they
are defined as keywords:

.. code-block:: python

    >>> match = 45
    >>> foo(match="Yeah!")

The ``match`` and ``case`` keywords are soft keywords, so that they are recognized as
keywords at the beginning of a match statement or case block respectively, but are
allowed to be used in other places as variable or argument names.

.. caution::
    Soft keywords can be a bit challenging to manage as they can be accepted in
    places you don't intend to, given how the order alternatives behave in PEG
    parsers (see :ref:`consequences of ordered choice section
    <consequences-of-ordered-choice>` for some background on this). In general,
    try to define them in places where there is not a lot of alternatives.

Error handling
~~~~~~~~~~~~~~

When a pegen-generated parser detects that an exception is raised, it will
**automatically stop parsing**, no matter what the current state of the parser
is and it will unwind the stack and report the exception. This means that if a
rule action raises an exception all parsing will stop at that exact point. This
is done to allow to correctly propagate any exception set by any Python
functions. This also includes `SyntaxError` exceptions and this is the main
mechanism the parser uses to report custom syntax error messages.

.. note::
    Tokenizer errors are normally reported by raising exceptions but some special
    tokenizer errors such as unclosed parenthesis will be reported only after the
    parser finishes without returning anything.

References
----------

.. [1] Ford, Bryan
   http://pdos.csail.mit.edu/~baford/packrat/thesis
