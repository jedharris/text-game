# Makefile for state manager tests

.PHONY: help test test-verbose test-loader test-validators test-serializer test-models test-errors test-regressions clean

help:
	@echo "State Manager Test Suite"
	@echo ""
	@echo "Available targets:"
	@echo "  make test              - Run all tests"
	@echo "  make test-verbose      - Run all tests with verbose output"
	@echo "  make test-loader       - Run loader tests only"
	@echo "  make test-validators   - Run validator tests only"
	@echo "  make test-serializer   - Run serializer tests only"
	@echo "  make test-models       - Run model tests only"
	@echo "  make test-errors       - Run error handling tests only"
	@echo "  make test-regressions  - Run regression tests only"
	@echo "  make clean             - Remove Python cache files"

test:
	python -m unittest discover . -v

test-verbose:
	python -m unittest discover . -v 2

test-loader:
	python -m unittest test_loader -v

test-validators:
	python -m unittest test_validators -v

test-serializer:
	python -m unittest test_serializer -v

test-models:
	python -m unittest test_models -v

test-errors:
	python -m unittest test_error_handling -v

test-regressions:
	python -m unittest test_regressions -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
