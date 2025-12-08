"""Integration tests for UC3: Hungry Wolf Pack scenario.

These tests play through actual game scenarios to catch bugs that
unit tests miss. They test the full stack from command to output.

Each test class runs in its own subprocess for complete isolation,
avoiding Python module caching issues between test runs.

The tests verify:
- Pack followers sync with alpha disposition
- Giving food pacifies wolves
- Damaged wolves flee when morale drops
- Repeated feeding builds gratitude relationship
- High gratitude makes wolves friendly (domesticated)
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class TestUC3WolfPackScenarios(unittest.TestCase):
    """Run UC3 Wolf Pack scenario tests in isolated subprocesses."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._uc3_wolf_pack_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_uc3_pack_sync(self):
        """Test pack followers sync with alpha."""
        result = self._run_test_class('TestUC3PackSync')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc3_feeding(self):
        """Test giving food pacifies wolves."""
        result = self._run_test_class('TestUC3Feeding')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc3_morale_flee(self):
        """Test damaged wolves flee when morale drops."""
        result = self._run_test_class('TestUC3MoraleFlee')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc3_relationship(self):
        """Test repeated feeding builds gratitude."""
        result = self._run_test_class('TestUC3Relationship')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")

    def test_uc3_domestication(self):
        """Test high gratitude makes wolves friendly."""
        result = self._run_test_class('TestUC3Domestication')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
