"""Integration tests for UC1: Infected Scholar scenario.

These tests play through actual game scenarios to catch bugs that
unit tests miss. They test the full stack from command to output.

Each test class runs in its own subprocess for complete isolation,
avoiding Python module caching issues between test runs.

The tests verify:
- Spore exposure applies fungal_infection condition
- Player resistance reduces condition severity
- Giving silvermoss cures the scholar
- Proximity to infected spreads condition
- Condition worsens over turns
"""

import subprocess
import sys
import unittest
from pathlib import Path


# Path to the project root
PROJECT_ROOT = Path(__file__).parent.parent


class TestUC1InfectedScholarScenarios(unittest.TestCase):
    """Run UC1 Infected Scholar scenario tests in isolated subprocesses."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._uc1_infected_scholar_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_uc1_infection(self):
        """Test spore exposure applies condition."""
        result = self._run_test_class('TestUC1Infection')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc1_resistance(self):
        """Test player resistance reduces severity."""
        result = self._run_test_class('TestUC1Resistance')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc1_cure(self):
        """Test giving silvermoss cures scholar."""
        result = self._run_test_class('TestUC1Cure')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc1_contagion(self):
        """Test proximity to infected spreads condition."""
        result = self._run_test_class('TestUC1Contagion')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc1_progression(self):
        """Test condition worsens over turns."""
        result = self._run_test_class('TestUC1Progression')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
