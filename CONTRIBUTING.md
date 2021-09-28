# Contributing to Pegen

This project welcomes contributions in the form of Pull Requests.
For clear bug-fixes / typos etc. just submit a PR.
For new features or if there is any doubt in how to fix a bug, you might want
to open an issue prior to starting work to discuss it first.

### Tests

`pegen` uses [tox](https://pypi.org/project/tox/) to run the test suite. Make sure
you have `tox` installed and then you can run the tests with the following command:

```
python -m tox
```

This will check that all the test pass but also will make several checks on the code style
and type annotations of the package.

Additionally, if you want to just run the testes and you have `pytest` installed, you can run
the test directly by running:

```
python -m pytest tests
```

Or if you don't have `make`, run the following:

```
make check
```

New code should ideally have tests and not break existing tests.

### Type Checking

`pege` uses type annotations throughout, and `mypy` to do the checking.
Run the following to type check `pegen`:

```
python -m tox -e lint
```

Or if you don't have `make` and `mypy` is installed in your current Python environment:

```
make lint
```

Please add type annotations for all new code.

### Code Formatting

`pegen` uses [`black`](https://github.com/psf/black) for code formatting.
I recommend setting up black in your editor to format on save.

To run black from the command line, use `make format` to format and write to the files.
