PYTHON ?= python
PIP_INSTALL=$(PYTHON) -m pip install
python_files := $(shell find src tests -name \*.py -not -path '*/\.*')

# Use this to inject arbitrary commands before the make targets (e.g. docker)
ENV :=

.PHONY: dist
dist:  ## Generate Python distribution files
	$(PYTHON) -m pep517.build .

.PHONY: install-sdist
install-sdist: dist  ## Install from source distribution
	$(ENV) $(PIP_INSTALL) $(wildcard dist/*.tar.gz)

.PHONY: install
test-install:  ## Install with test dependencies
	$(ENV) $(PIP_INSTALL) -e .[test]

.PHONY: test
check:  ## Run the test suite
	$(PYTHON) -m pytest -vvv --log-cli-level=info -s --color=yes $(PYTEST_ARGS) tests

.PHONY: pycoverage
pycoverage:  ## Run the test suite, with Python code coverage
	$(PYTHON) -m pytest \
		-vvv \
		--log-cli-level=info \
		-s \
		--color=yes \
		--cov=pegen \
		--cov-config=tox.ini \
		--cov-report=term \
		--cov-append $(PYTEST_ARGS) \
		tests

.PHONY: format
format: 
	$(PYTHON) -m black $(python_files)

.PHONY: lint
lint: ## Lint all files
	$(PYTHON) -m black --check $(python_files)
	$(PYTHON) -m mypy src/pegen 

.PHONY: clean
clean:  ## Clean any built/generated artifacts
	find . | grep -E '(\.o|\.so|\.gcda|\.gcno|\.gcov\.json\.gz)' | xargs rm -rf
	find . | grep -E '(__pycache__|\.pyc|\.pyo)' | xargs rm -rf

.PHONY: regen-metaparser
regen-metaparser: src/pegen/metagrammar.gram src/pegen/*.py # Regenerate the metaparser
	$(PYTHON) -m pegen -q src/pegen/metagrammar.gram -o src/pegen/grammar_parser.py

.PHONY: help
help:  ## Print this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
