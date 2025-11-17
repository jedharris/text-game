#!/usr/bin/env python3
"""
Test runner for state manager test suite.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py -v           # Verbose output
    python run_tests.py loader       # Run only loader tests
    python run_tests.py validators   # Run only validator tests
"""
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def run_all_tests(verbosity=1):
    """Run all state manager tests."""
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


def run_specific_module(module_name, verbosity=1):
    """Run tests from a specific module."""
    loader = unittest.TestLoader()

    # Map short names to full module names
    module_map = {
        'loader': 'test_loader',
        'serializer': 'test_serializer',
        'models': 'test_models',
        'validators': 'test_validators',
        'errors': 'test_error_handling',
        'error_handling': 'test_error_handling',
        'regressions': 'test_regressions'
    }

    full_name = module_map.get(module_name, module_name)
    if not full_name.startswith('test_'):
        full_name = f'test_{full_name}'

    try:
        suite = loader.loadTestsFromName(full_name)
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        return 0 if result.wasSuccessful() else 1
    except Exception as e:
        print(f"Error loading module '{module_name}': {e}")
        return 1


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Parse arguments
    verbosity = 1
    module = None

    for arg in args:
        if arg in ('-v', '--verbose'):
            verbosity = 2
        elif arg in ('-q', '--quiet'):
            verbosity = 0
        elif arg in ('-h', '--help'):
            print(__doc__)
            return 0
        else:
            module = arg

    # Run tests
    if module:
        return run_specific_module(module, verbosity)
    else:
        return run_all_tests(verbosity)


if __name__ == '__main__':
    sys.exit(main())
