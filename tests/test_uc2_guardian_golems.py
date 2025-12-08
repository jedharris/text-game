"""UC2: Guardian Golems - Integration tests for combat mechanics.

This wrapper module runs the actual tests in a subprocess to ensure
clean module isolation. Each test class is run separately to avoid
Python's module caching from causing cross-test pollution.

UC2 Tests (combat mechanics):
- TestUC2GolemSetup: Golems exist with attacks and resistances
- TestUC2WeaponDamage: Weapons deal damage with type bonuses
- TestUC2CoverMechanics: Cover reduces incoming damage
- TestUC2Resistances: Damage resistances reduce incoming damage
- TestUC2Weaknesses: Damage weaknesses increase incoming damage
- TestUC2Counterattack: Golems counterattack when damaged
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class TestUC2GolemSetupWrapper(unittest.TestCase):
    """Wrapper for TestUC2GolemSetup tests."""

    def test_golems_setup_in_subprocess(self):
        """Run golem setup tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc2_guardian_golems_impl.TestUC2GolemSetup', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC2WeaponDamageWrapper(unittest.TestCase):
    """Wrapper for TestUC2WeaponDamage tests."""

    def test_weapon_damage_in_subprocess(self):
        """Run weapon damage tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc2_guardian_golems_impl.TestUC2WeaponDamage', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC2CoverMechanicsWrapper(unittest.TestCase):
    """Wrapper for TestUC2CoverMechanics tests."""

    def test_cover_mechanics_in_subprocess(self):
        """Run cover mechanics tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc2_guardian_golems_impl.TestUC2CoverMechanics', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC2ResistancesWrapper(unittest.TestCase):
    """Wrapper for TestUC2Resistances tests."""

    def test_resistances_in_subprocess(self):
        """Run resistance tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc2_guardian_golems_impl.TestUC2Resistances', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC2WeaknessesWrapper(unittest.TestCase):
    """Wrapper for TestUC2Weaknesses tests."""

    def test_weaknesses_in_subprocess(self):
        """Run weakness tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc2_guardian_golems_impl.TestUC2Weaknesses', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC2CounterattackWrapper(unittest.TestCase):
    """Wrapper for TestUC2Counterattack tests."""

    def test_counterattack_in_subprocess(self):
        """Run counterattack tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc2_guardian_golems_impl.TestUC2Counterattack', '-v'],
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
