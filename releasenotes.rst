Release notes
==============

2023-11-14: Version 0.3.0
-------------------------

- Replace nullable_visit with NullableVisitor (#86)
- Implement nullable detection via NullableVisitor (#91)
- Support Python 3.11 and 3.12 (#95)
- Support Python 3.12 f-strings in grammar actions (#94, #96)
- Fix typing in parser class and minor f-string fix (#97)
- Improve CI/CD workflows (#98)

2023-01-18: Version 0.2.0
-------------------------

- add delayed error inspection, invalid rules pass and recursive detection of
  invalid rules PR #60
- remove generated file data/python_parser.py, and add demo target in Makefile PR #62
- refactor dependencies to avoid extraneous dependencies by default PR #59
- add documentation PR #43 #52
- sort KEYWORDS to make output deterministic PR #44
- update grammar_grapher with the new forced (&&) directive PR #57
- fixed bug where tokenizer reported the last line of source as empty #77

2021-09-06: Version 0.1.0
-------------------------

First numbered release