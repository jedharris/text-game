"""UC4: Healer and Garden - Integration tests for services and knowledge.

This wrapper module runs the actual tests in a subprocess to ensure
clean module isolation. Each test class is run separately to avoid
Python's module caching from causing cross-test pollution.

UC4 Tests (services + knowledge):
- TestUC4ToxicPlant: Touching toxic plant applies poison
- TestUC4Knowledge: Knowledge gates plant descriptions
- TestUC4CureService: Healer cures for payment
- TestUC4TeachService: Healer teaches herbalism
- TestUC4TrustDiscount: Trust reduces service cost
"""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class TestUC4ToxicPlantWrapper(unittest.TestCase):
    """Wrapper for TestUC4ToxicPlant tests."""

    def test_toxic_plant_in_subprocess(self):
        """Run toxic plant tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc4_healer_garden_impl.TestUC4ToxicPlant', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC4KnowledgeWrapper(unittest.TestCase):
    """Wrapper for TestUC4Knowledge tests."""

    def test_knowledge_in_subprocess(self):
        """Run knowledge tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc4_healer_garden_impl.TestUC4Knowledge', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC4CureServiceWrapper(unittest.TestCase):
    """Wrapper for TestUC4CureService tests."""

    def test_cure_service_in_subprocess(self):
        """Run cure service tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc4_healer_garden_impl.TestUC4CureService', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC4TeachServiceWrapper(unittest.TestCase):
    """Wrapper for TestUC4TeachService tests."""

    def test_teach_service_in_subprocess(self):
        """Run teach service tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc4_healer_garden_impl.TestUC4TeachService', '-v'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestUC4TrustDiscountWrapper(unittest.TestCase):
    """Wrapper for TestUC4TrustDiscount tests."""

    def test_trust_discount_in_subprocess(self):
        """Run trust discount tests in subprocess."""
        result = subprocess.run(
            [sys.executable, '-m', 'unittest',
             'tests._uc4_healer_garden_impl.TestUC4TrustDiscount', '-v'],
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
