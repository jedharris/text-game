"""Tests for thermal shock combat mechanics.

Tests the temperature-based damage system for stone golems attacked
with fire and cold weapons.

Runs in subprocess for module isolation to prevent conflicts with
other example games' behavior modules.
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class TestThermalShockWrapper(unittest.TestCase):
    """Run thermal shock tests in isolated subprocess."""

    def test_thermal_shock(self):
        """Test thermal shock mechanics."""
        result = subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                'tests._thermal_shock_impl.TestThermalShock',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
