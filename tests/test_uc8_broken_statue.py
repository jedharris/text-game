"""UC8: Broken Statue - Integration tests for construct repair mechanics.

This wrapper module runs the actual tests in a subprocess to ensure
clean module isolation. Each test class is run separately to avoid
Python's module caching from causing cross-test pollution.

UC8 Tests (construct mechanics):
- TestUC8Repair: Repair item restores statue health
- TestUC8Functional: Statue becomes functional at health threshold
- TestUC8GuardDuty: Activated statue guards location
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class TestUC8RepairWrapper(unittest.TestCase):
    """Wrapper for TestUC8Repair tests."""

    def test_repair_in_subprocess(self):
        """Run repair tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc8_broken_statue_impl.TestUC8Repair', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC8FunctionalWrapper(unittest.TestCase):
    """Wrapper for TestUC8Functional tests."""

    def test_functional_in_subprocess(self):
        """Run functional threshold tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc8_broken_statue_impl.TestUC8Functional', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC8GuardDutyWrapper(unittest.TestCase):
    """Wrapper for TestUC8GuardDuty tests."""

    def test_guard_duty_in_subprocess(self):
        """Run guard duty tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc8_broken_statue_impl.TestUC8GuardDuty', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
