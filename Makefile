PYTHON ?= python

.PHONY: mypy test check

mypy:
	$(PYTHON) -m mypy src utilities

test:
	$(PYTHON) -m unittest

check: mypy test
