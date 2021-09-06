<p align="center">
<img src="https://github.com/we-like-parsers/pegen/raw/main/media/logo.svg" width="70%">
</p>

-----------------------------------

[![Downloads](https://pepy.tech/badge/pegen/month)](https://pepy.tech/project/pegen)
[![PyPI version](https://badge.fury.io/py/pegen.svg)](https://badge.fury.io/py/pegen)
![CI](https://github.com/we-like-parsers/pegen/actions/workflows/test.yml/badge.svg)

Pegen is the parser generator used in CPython to produce the parser used by the interpreter. It allows to
produce PEG parsers from a description of a formal Grammar. 

## Syntax

The grammar consists of a sequence of rules of the form:

```
    rule_name: expression
```

Optionally, a type can be included right after the rule name, which
specifies the return type of the Python function corresponding to
the rule:

```
    rule_name[return_type]: expression
```

If the return type is omitted, then ``Any`` is returned.

## Grammar Expressions

### `# comment`

Python-style comments.

### `e1 e2`

Match e1, then match e2.

```
    rule_name: first_rule second_rule
```

### `e1 | e2`

Match e1 or e2.

The first alternative can also appear on the line after the rule name
for formatting purposes. In that case, a \| must be used before the
first alternative, like so:

```
    rule_name[return_type]:
        | first_alt
        | second_alt
```

### `( e )`

Match e.

```
    rule_name: (e)
```

A slightly more complex and useful example includes using the grouping
operator together with the repeat operators:

```
    rule_name: (e1 e2)*
```

### `[ e ] or e?`

Optionally match e.


```
    rule_name: [e]
```

A more useful example includes defining that a trailing comma is
optional:

```
    rule_name: e (',' e)* [',']
```

### `e*`

Match zero or more occurrences of e.

```
    rule_name: (e1 e2)*
```

### `e+`

Match one or more occurrences of e.

```
    rule_name: (e1 e2)+
```

### `s.e+`

Match one or more occurrences of e, separated by s. The generated parse
tree does not include the separator. This is otherwise identical to
``(e (s e)*)``.

```
    rule_name: ','.e+
```

### `&e`

Succeed if e can be parsed, without consuming any input.

### `!e`

Fail if e can be parsed, without consuming any input.

An example taken from the Python grammar specifies that a primary
consists of an atom, which is not followed by a ``.`` or a ``(`` or a
``[``:

```
    primary: atom !'.' !'(' !'['
```

### `~`

Commit to the current alternative, even if it fails to parse.

```
    rule_name: '(' ~ some_rule ')' | some_alt
```

In this example, if a left parenthesis is parsed, then the other
alternative won’t be considered, even if some_rule or ‘)’ fail to be
parsed.

## Left recursion

PEG parsers normally do not support left recursion but Pegen implements a
technique that allows left recursion using the memoization cache. This allows
us to write not only simple left-recursive rules but also more complicated
rules that involve indirect left-recursion like

```
  rule1: rule2 | 'a'
  rule2: rule3 | 'b'
  rule3: rule1 | 'c'
```

and "hidden left-recursion" like::

```
  rule: 'optional'? rule '@' some_other_rule
```

## Variables in the Grammar

A sub-expression can be named by preceding it with an identifier and an
``=`` sign. The name can then be used in the action (see below), like this: ::

```
    rule_name[return_type]: '(' a=some_other_rule ')' { a }
```

## Grammar actions

To avoid the intermediate steps that obscure the relationship between the
grammar and the AST generation the PEG parser allows directly generating AST
nodes for a rule via grammar actions. Grammar actions are language-specific
expressions that are evaluated when a grammar rule is successfully parsed. These
expressions can be written in Python. As an example of a grammar with Python actions,
the piece of the parser generator that parses grammar files is bootstrapped from a
meta-grammar file with Python actions that generate the grammar tree as a result
of the parsing. 

In the specific case of the PEG grammar for Python, having actions allows
directly describing how the AST is composed in the grammar itself, making it
more clear and maintainable. This AST generation process is supported by the use
of some helper functions that factor out common AST object manipulations and
some other required operations that are not directly related to the grammar.

To indicate these actions each alternative can be followed by the action code
inside curly-braces, which specifies the return value of the alternative

```
    rule_name[return_type]:
        | first_alt1 first_alt2 { first_alt1 }
        | second_alt1 second_alt2 { second_alt1 }
```

If the action is ommited, a default action is generated: 

* If there's a single name in the rule in the rule, it gets returned.

* If there is more than one name in the rule, a collection with all parsed
  expressions gets returned.

This default behaviour is primarily made for very simple situations and for
debugging pourposes.

As an illustrative example this simple grammar file allows directly
generating a full parser that can parse simple arithmetic expressions and that
returns a valid Python AST:


```
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
```

## Differences with CPython's Pegen

**NOTE:** The official PEG generator for Python 3.9 and later is now
included in the CPython repo under
[Tools/peg_generator/](https://github.com/python/cpython/tree/master/Tools/peg_generator).

See also [PEP 617](https://www.python.org/dev/peps/pep-0617/).
