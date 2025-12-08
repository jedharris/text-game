"""UC7: Spider Swarm - Integration tests for pack, conditions, and web mechanics.

This wrapper module runs the actual tests in a subprocess to ensure
clean module isolation. Each test class is run separately to avoid
Python's module caching from causing cross-test pollution.

UC7 Tests (pack + conditions + complex):
- TestUC7SpiderPack: Spider pack configuration
- TestUC7VenomAttack: Venomous spider attacks
- TestUC7WebBurning: Torch burns webs
- TestUC7AlertPropagation: Alerting spider pack
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class TestUC7SpiderPackWrapper(unittest.TestCase):
    """Wrapper for TestUC7SpiderPack tests."""

    def test_spider_pack_in_subprocess(self):
        """Run spider pack tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc7_spider_swarm_impl.TestUC7SpiderPack', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC7VenomAttackWrapper(unittest.TestCase):
    """Wrapper for TestUC7VenomAttack tests."""

    def test_venom_attack_in_subprocess(self):
        """Run venom attack tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc7_spider_swarm_impl.TestUC7VenomAttack', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC7WebBurningWrapper(unittest.TestCase):
    """Wrapper for TestUC7WebBurning tests."""

    def test_web_burning_in_subprocess(self):
        """Run web burning tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc7_spider_swarm_impl.TestUC7WebBurning', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC7AlertPropagationWrapper(unittest.TestCase):
    """Wrapper for TestUC7AlertPropagation tests."""

    def test_alert_propagation_in_subprocess(self):
        """Run alert propagation tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc7_spider_swarm_impl.TestUC7AlertPropagation', '-v'],
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
