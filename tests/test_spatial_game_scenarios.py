"""Integration tests for spatial_game scenarios.

These tests play through actual game scenarios to catch bugs that
unit tests miss. They test the full stack from command to output.

Each test class runs in its own subprocess for complete isolation,
avoiding Python module caching issues between test runs.

The tests verify:
- Magic staircase visibility based on having the magic star
- Star retrieval puzzle (stand on bench -> climb tree -> take star)
- Exit descriptions appearing in all locations
- Full puzzle solution walkthrough
"""

import subprocess
import sys
import unittest
from pathlib import Path

try:
    import wx  # type: ignore[unused-import]
    WX_AVAILABLE = True
except ModuleNotFoundError:
    WX_AVAILABLE = False


# Path to the project root
PROJECT_ROOT = Path(__file__).parent.parent


@unittest.skipUnless(WX_AVAILABLE, "wxPython not installed")
class TestSpatialGameScenarios(unittest.TestCase):
    """Run spatial_game scenario tests in isolated subprocesses."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._spatial_game_scenarios_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_magic_staircase_visibility(self):
        """Test the magic staircase visibility puzzle."""
        result = self._run_test_class('TestMagicStaircaseVisibility')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_magic_star_puzzle(self):
        """Test the magic star retrieval puzzle."""
        result = self._run_test_class('TestMagicStarPuzzle')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_exit_descriptions(self):
        """Test that exits are properly displayed in all locations."""
        result = self._run_test_class('TestExitDescriptions')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_full_puzzle_solution(self):
        """Test playing through the complete star/staircase puzzle."""
        result = self._run_test_class('TestFullPuzzleSolution')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
