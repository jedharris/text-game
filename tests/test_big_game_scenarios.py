"""Integration tests for The Shattered Meridian (big_game) scenarios.

These tests play through actual game scenarios to catch bugs that
unit tests miss. They test the full stack from command to output.

Each test class runs in its own subprocess for complete isolation,
avoiding Python module caching issues between test runs.
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class TestBigGameScenarios(unittest.TestCase):
    """Run big_game scenario tests in isolated subprocesses."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._big_game_scenarios_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_game_loads(self):
        """Test that the game loads without errors."""
        result = self._run_test_class('TestGameLoads')
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_basic_navigation(self):
        """Test basic movement between locations."""
        result = self._run_test_class('TestBasicNavigation')
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_nexus_hub(self):
        """Test the Meridian Nexus hub area."""
        result = self._run_test_class('TestNexusHub')
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_dialog_system(self):
        """Test NPC dialog with topics."""
        result = self._run_test_class('TestDialogSystem')
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_region_system(self):
        """Test region definitions and lookups."""
        result = self._run_test_class('TestRegionSystem')
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
