"""Integration tests for UC5: Drowning Sailor scenario.

These tests play through actual game scenarios to catch bugs that
unit tests miss. They test the full stack from command to output.

Each test class runs in its own subprocess for complete isolation,
avoiding Python module caching issues between test runs.

The tests verify:
- Breath decreases in non-breathable areas
- Actor takes damage when breath depleted
- Air bladder prevents breath loss
- Bringing sailor to surface restores breath
- Constructs don't need to breathe
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class TestUC5DrowningScenarios(unittest.TestCase):
    """Run UC5 Drowning Sailor scenario tests in isolated subprocesses."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._uc5_drowning_sailor_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_uc5_breath(self):
        """Test breath mechanics in water."""
        result = self._run_test_class('TestUC5Breath')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc5_drowning(self):
        """Test drowning damage."""
        result = self._run_test_class('TestUC5Drowning')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc5_breathing_item(self):
        """Test air bladder prevents breath loss."""
        result = self._run_test_class('TestUC5BreathingItem')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc5_rescue(self):
        """Test rescue mechanics."""
        result = self._run_test_class('TestUC5Rescue')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc5_construct_immune(self):
        """Test constructs don't need to breathe."""
        result = self._run_test_class('TestUC5ConstructImmune')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
