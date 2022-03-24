Syntax
------

The grammar consists of a sequence of rules of the form:

::

   rule_name: expression

Optionally, a type can be included right after the rule name, which
specifies the return type of the Python function corresponding to the
rule:

::

   rule_name[return_type]: expression

If the return type is omitted, then the return type is ``Any``.

Grammar Expressions
~~~~~~~~~~~~~~~~~~~

``# comment``
'''''''''''''

Python-style comments.

``e1 e2``
'''''''''

Match e1, then match e2.

::

   rule_name: first_rule second_rule

.. _e1-e2-1:

``e1 | e2``
'''''''''''

Match e1 or e2.

The first alternative can also appear on the line after the rule name
for formatting purposes. In that case, a \| can also be used before the
first alternative, like so:

::

   rule_name[return_type]:
       | first_alt
       | second_alt

``( e )``
'''''''''

Match e.

::

   rule_name: (e)

A slightly more complex and useful example includes using the grouping
operator together with the repeat operators:

::

   rule_name: (e1 e2)*

``[ e ] or e?``
'''''''''''''''

Optionally match e.

::

   rule_name: [e]

A more useful example includes defining that a trailing comma is
optional:

::

   rule_name: e (',' e)* [',']

.. _e-1:

``e*``
''''''

Match zero or more occurrences of e.

::

   rule_name: (e1 e2)*

.. _e-2:

``e+``
''''''

Match one or more occurrences of e.

::

   rule_name: (e1 e2)+

``s.e+``
''''''''

Match one or more occurrences of e, separated by s. The generated parse
tree does not include the separator. This is otherwise identical to
``(e (s e)*)``.

::

   rule_name: ','.e+

.. _e-3:

``&e``
''''''

Succeed if e can be parsed, without consuming any input.

.. _e-4:

``!e``
''''''

Fail if e can be parsed, without consuming any input.

An example taken from ``data/python.gram`` specifies that a primary
consists of an atom, which is not followed by a ``.`` or a ``(`` or a
``[``:

::

   primary: atom !'.' !'(' !'['

.. _e-5:

``~e``
''''''

Commit to the current alternative, even if it fails to parse.

::

   rule_name: '(' ~ some_rule ')' | some_alt

In this example, if a left parenthesis is parsed, then the other
alternative won’t be considered, even if some_rule or ‘)’ fail to be
parsed.

.. _e-6:

``&&e``
'''''''

Fail immediately if e fails to parse by raising the exception built using
the ``make_syntax_error`` method.

This construct can help provide better error messages.

Keywords
~~~~~~~~

Keywords are identified in the grammar as quoted names. Single quotes
``'def'`` are used to identify hard keywords i.e. keywords that are
reserved in the grammar and cannot be used for any other purpose. Double
quotes ``"match"`` identify soft keywords that act as keyword only in
specific context. As a consequence a rule matching ``NAME`` may match a
soft keyword but never a hard keyword.

In some circumstances, it can desirable to match any soft keyword. For
those cases one can use ``SOFT_KEYWORD`` that will expand to
``"match" | "case"`` if ``match`` and ``case`` are the only two known
soft keywords.

Return Value
~~~~~~~~~~~~

Optionally, an alternative can be followed by a so-called action in
curly-braces, which specifies the return value of the alternative:

::

   rule_name[return_type]:
       | first_alt1 first_alt2 { first_alt1 }
       | second_alt1 second_alt2 { second_alt1 }

If the action is omitted, a list with all the parsed expressions gets
returned. However if the rule contains a single element it is returned
as is without being wrapped in a list. Rules allowing to match multiple
items (``+`` or ``*``) always return a list.

By default the parser does not track line number and col offset for
production each rule. If one desires to store the start line and offset
and the end line and offset of a rule, one can add ``LOCATIONS`` in the
action. It will be replaced in the generated parser by the value of the
``location_formatting`` argument of the parser generator, which defaults
to::

    lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset

The default is suitable to generate Python AST nodes.

Variables in the Grammar
~~~~~~~~~~~~~~~~~~~~~~~~

A subexpression can be named by preceding it with an identifier and an
``=`` sign. The name can then be used in the action, like this:

::

   rule_name[return_type]: '(' a=some_other_rule ')' { a }

Grammar actions
~~~~~~~~~~~~~~~

To avoid the intermediate steps that obscure the relationship between
the grammar and the AST generation the PEG parser allows directly
generating AST nodes for a rule via grammar actions. Grammar actions are
language-specific expressions that are evaluated when a grammar rule is
successfully parsed. These expressions can be written in Python. As an
example of a grammar with Python actions, the piece of the parser
generator that parses grammar files is bootstrapped from a meta-grammar
file with Python actions that generate the grammar tree as a result of
the parsing.

In the specific case of the PEG grammar for Python, having actions
allows directly describing how the AST is composed in the grammar
itself, making it more clear and maintainable. This AST generation
process is supported by the use of some helper functions that factor out
common AST object manipulations and some other required operations that
are not directly related to the grammar.

To indicate these actions, each alternative can be followed by an action
inside curly-braces, which specifies a Python expression to be evaluated
and returned for the alternative:

::

       rule_name[return_type]:
           | first_alt1 first_alt2 { first_alt1 }
           | second_alt1 second_alt2 { second_alt1 }

.. important::

   The code inside curly-braces can only be a Python expression (i.e. it
   can be assigned to a variable).

If the action is omitted, a default action is generated:

-  If there’s a single name in the rule in the rule, it gets returned.

-  If there is more than one name in the rule, a collection with all
   parsed expressions gets returned.

This default behaviour is primarily made for very simple situations and
for debugging purposes.

As an illustrative example this simple grammar file allows directly
generating a full parser that can parse simple arithmetic expressions
and that returns a valid Python AST:

::

       start[ast.Module]: a=expr_stmt* ENDMARKER { ast.Module(body=a or [] }
       expr_stmt: a=expr NEWLINE { ast.Expr(value=a, EXTRA) }

       expr:
           | l=expr '+' r=term { ast.BinOp(left=l, op=ast.Add(), right=r, EXTRA) }
           | l=expr '-' r=term { ast.BinOp(left=l, op=ast.Sub(), right=r, EXTRA) }
           | term

       term:
           | l=term '*' r=factor { ast.BinOp(left=l, op=ast.Mult(), right=r, EXTRA) }
           | l=term '/' r=factor { ast.BinOp(left=l, op=ast.Div(), right=r, EXTRA) }
           | factor

       factor:
           | '(' e=expr ')' { e }
           | atom

       atom:
           | NAME
           | NUMBER



Left recursion
~~~~~~~~~~~~~~

PEG parsers normally do not support left recursion but Pegen implements
a technique that allows left recursion using the memoization cache. This
allows us to write not only simple left-recursive rules but also more
complicated rules that involve indirect left-recursion like

::

     rule1: rule2 | 'a'
     rule2: rule3 | 'b'
     rule3: rule1 | 'c'

and “hidden left-recursion” like::

     rule: 'optional'? rule '@' some_other_rule

Syntax error related rules
~~~~~~~~~~~~~~~~~~~~~~~~~~

Rules starting with ``invalid`` are meant to provide better error reporting on
syntax error. They are ignored by the parser unless the ``call_invalid_rules``
attribute of the parser is set to ``True``. This allows for faster parsing on
the happy path and nicer errors can be generated in a second path as is done
in the Python parser.

.. note::

   Rule whose name ends in ``without_invalid`` will never call ``invalid``
   rules which avoids possibly infinite recursion.

.. note::

   When used in the alternative of another rule, this alternative will never
   evaluate its action. This can be annoying to measure the code coverage on
   the parser. To alleviate this issue, all rule alternatives making use of a
   rule whose name starts with ``'invalid'`` will have its action set to
   ``UNREACHABLE`` if no action was specified. ``UNREACHABLE`` is a special
   action which will be replaced by the value of the ``unreachable_formatting``
   which defaults to ``None  # pragma: no cover``.

.. note::
    Rules making use of the ``&&`` forced operator to generate syntax error
    will never run their action and need to be manually annotated.

Customizing the generated parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the generated parser inherits from the Parser class defined
in pegen/parser.py, and is named GeneratedParser. One can customize the
generated module by modifying the header and trailer of the module
generated by pegen. To do so one can add dedicated sections to the
grammar, which are discussed below:

@class NAME
'''''''''''

This allows to specify the name of the generated parser.

@header
'''''''

Specify the header of the module as a string (one can typically use
triple quoted string). This defaults to MODULE_PREFIX by default which
is defined in pegen.python_generator. In general you should not modify
the header since it defines necessary imports. If you need to add extra
imports use the next section. Note that the header is formatted using
``.format(filename=filename)`` allowing you to embed the grammar
filename in the header.

@subheader
''''''''''

Specify a subheader for the module as a string (one can typically use
triple quoted string). This is empty by default and is the safer to edit
to perform custom imports.

@trailer
''''''''

Specify a trailer for the module which is appended to the parser
definition. It defaults to MODULE_SUFFIX which is defined in
pegen.python_generator. Note that the trailer is formatted using
``.format(class_name=cls_name)`` allowing you to reference the created
parser in the trailer.

The following snippets illustrates naming the parser MyParser and making
the parser inherit from a custom base class.

::

   @class MyParser

   @subheader '''
   from my_package import BaseParser as Parser
   '''

Style
~~~~~

This is not a hard limit, but lines longer than 110 characters should
almost always be wrapped. Most lines should be wrapped after the opening
action curly brace, like:

::

   really_long_rule[expr_ty]: some_arbitrary_rule {
       _This_is_the_action }
