"""Tests for virtual entity per-entity turn phase dispatch.

Runs turn phase tests in isolated subprocesses to avoid module caching issues.

Validates that turn phases correctly dispatch to individual entity handlers
and that each handler receives the correct entity instance.
"""
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestCommitmentTurnPhase(unittest.TestCase):
    """Run commitment turn phase tests in isolated subprocess."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._turn_phase_dispatch_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_commitment_turn_phase(self):
        """Test commitment turn phase."""
        result = self._run_test_class('TestCommitmentTurnPhase')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestScheduledEventTurnPhase(unittest.TestCase):
    """Run scheduled event turn phase tests in isolated subprocess."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._turn_phase_dispatch_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_scheduled_event_turn_phase(self):
        """Test scheduled event turn phase."""
        result = self._run_test_class('TestScheduledEventTurnPhase')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestGossipTurnPhase(unittest.TestCase):
    """Run gossip turn phase tests in isolated subprocess."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._turn_phase_dispatch_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_gossip_turn_phase(self):
        """Test gossip turn phase."""
        result = self._run_test_class('TestGossipTurnPhase')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


class TestSpreadTurnPhase(unittest.TestCase):
    """Run spread turn phase tests in isolated subprocess."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._turn_phase_dispatch_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_spread_turn_phase(self):
        """Test spread turn phase."""
        result = self._run_test_class('TestSpreadTurnPhase')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
