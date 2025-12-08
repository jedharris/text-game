"""UC6: Injured Merchant - Integration tests for treatment, escort, and rewards.

This wrapper module runs the actual tests in a subprocess to ensure
clean module isolation. Each test class is run separately to avoid
Python's module caching from causing cross-test pollution.

UC6 Tests (treatment + escort + relationships):
- TestUC6Treatment: Bandages treat bleeding
- TestUC6Trading: Merchant trades while injured
- TestUC6Escort: Guiding merchant to town
- TestUC6Reward: Reward on successful escort
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class TestUC6TreatmentWrapper(unittest.TestCase):
    """Wrapper for TestUC6Treatment tests."""

    def test_treatment_in_subprocess(self):
        """Run treatment tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc6_injured_merchant_impl.TestUC6Treatment', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC6TradingWrapper(unittest.TestCase):
    """Wrapper for TestUC6Trading tests."""

    def test_trading_in_subprocess(self):
        """Run trading tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc6_injured_merchant_impl.TestUC6Trading', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC6EscortWrapper(unittest.TestCase):
    """Wrapper for TestUC6Escort tests."""

    def test_escort_in_subprocess(self):
        """Run escort tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc6_injured_merchant_impl.TestUC6Escort', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC6RewardWrapper(unittest.TestCase):
    """Wrapper for TestUC6Reward tests."""

    def test_reward_in_subprocess(self):
        """Run reward tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc6_injured_merchant_impl.TestUC6Reward', '-v'],
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
