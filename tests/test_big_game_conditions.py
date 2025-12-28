"""Integration tests for condition system in big_game.

Tests that conditions work correctly with regional behaviors:
- Fungal infection progression in Fungal Depths
- Hypothermia in Frozen Reaches
- Drowning in Sunken District
- Health regeneration

Also tests that existing game_state.json conditions work properly.

Each test class runs in its own subprocess for complete isolation,
avoiding Python module caching issues between test runs.
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class TestBigGameConditions(unittest.TestCase):
    """Run big_game condition tests in isolated subprocesses."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._big_game_conditions_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_condition_integration(self):
        """Test condition system integration with big_game."""
        result = self._run_test_class('TestBigGameConditionIntegration')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_regional_behavior_conditions(self):
        """Test regional behaviors that use conditions."""
        result = self._run_test_class('TestRegionalBehaviorConditions')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
