#!/usr/bin/env python3
"""
Test runner script for the text adventure game parser.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py word_entry   # Run WordEntry tests only
    python run_tests.py -v           # Verbose output
"""

import sys
import unittest

# Test suites organized by category
TEST_SUITES = {
    'word_entry': 'tests.test_word_entry',
    'vocabulary': 'tests.test_vocabulary_loading',
    'parser': 'tests.test_parser',
    'patterns': 'tests.test_pattern_matching',
    'edge_cases': 'tests.test_edge_cases',
    'performance': 'tests.test_performance',
}


def run_test_suite(suite_name, verbose=False):
    """Run a specific test suite."""
    if suite_name not in TEST_SUITES:
        print(f"Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(TEST_SUITES.keys())}")
        return False

    module_name = TEST_SUITES[suite_name]

    try:
        # Load the test module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(module_name)

        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(suite)

        return result.wasSuccessful()

    except ModuleNotFoundError:
        print(f"Test module not found: {module_name}")
        print("Make sure the test file has been created.")
        return False


def run_all_tests(verbose=False):
    """Run all available test suites."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Load all test modules that exist
    for module_name in TEST_SUITES.values():
        try:
            tests = loader.loadTestsFromName(module_name)
            suite.addTests(tests)
        except ModuleNotFoundError:
            # Skip modules that haven't been created yet
            pass

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)

    return result.wasSuccessful()


def main():
    """Main entry point for test runner."""
    verbose = '-v' in sys.argv or '--verbose' in sys.argv

    # Filter out flags
    args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]

    if not args:
        # Run all tests
        print("Running all tests...\n")
        success = run_all_tests(verbose)
    else:
        # Run specific suite
        suite_name = args[0]
        print(f"Running {suite_name} tests...\n")
        success = run_test_suite(suite_name, verbose)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
