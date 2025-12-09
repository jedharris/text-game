"""Big Game integration tests - subprocess wrapper.

This module runs the integration tests from _big_game_integration_impl.py
in separate subprocesses to avoid module pollution issues.

The tests verify:
- Quest completion cascades
- Scheduled event triggers
- Deadline boundary conditions
- Ending condition paths
- Complete player journeys
- Cross-system interactions
"""

import subprocess
import sys
import unittest
from pathlib import Path


# Get paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
IMPL_MODULE = "_big_game_integration_impl"


def run_test_in_subprocess(test_class_name: str) -> tuple[bool, str]:
    """Run a test class in a subprocess and return (success, output)."""
    cmd = [
        sys.executable, "-m", "unittest",
        f"tests.{IMPL_MODULE}.{test_class_name}",
        "-v"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )

    output = result.stdout + result.stderr
    success = result.returncode == 0

    return success, output


class TestBigGameIntegration(unittest.TestCase):
    """Run big_game integration tests in subprocesses."""

    # Category 1: Quest Completion Cascades

    def test_quest_completion_cascades(self):
        """Test quest completion side effects."""
        success, output = run_test_in_subprocess("TestQuestCompletionCascades")
        self.assertTrue(success, f"TestQuestCompletionCascades failed:\n{output}")

    # Category 2: Scheduled Event Triggers

    def test_scheduled_event_triggers(self):
        """Test timed event mechanics."""
        success, output = run_test_in_subprocess("TestScheduledEventTriggers")
        self.assertTrue(success, f"TestScheduledEventTriggers failed:\n{output}")

    # Category 3: Deadline Boundaries

    def test_deadline_boundaries(self):
        """Test deadline edge cases."""
        success, output = run_test_in_subprocess("TestDeadlineBoundaries")
        self.assertTrue(success, f"TestDeadlineBoundaries failed:\n{output}")

    # Category 4: Ending Conditions

    def test_ending_condition_paths(self):
        """Test all four ending conditions."""
        success, output = run_test_in_subprocess("TestEndingConditionPaths")
        self.assertTrue(success, f"TestEndingConditionPaths failed:\n{output}")

    # Category 5: Complete Player Journeys

    def test_complete_player_journeys(self):
        """Test end-to-end journey tests."""
        success, output = run_test_in_subprocess("TestCompletePlayerJourneys")
        self.assertTrue(success, f"TestCompletePlayerJourneys failed:\n{output}")

    # Category 6: System Interactions

    def test_faction_reputation_cascades(self):
        """Test faction reputation propagation."""
        success, output = run_test_in_subprocess("TestFactionReputationCascades")
        self.assertTrue(success, f"TestFactionReputationCascades failed:\n{output}")

    def test_echo_integration_cascades(self):
        """Test Echo state-aware behavior."""
        success, output = run_test_in_subprocess("TestEchoIntegrationCascades")
        self.assertTrue(success, f"TestEchoIntegrationCascades failed:\n{output}")

    def test_region_state_cascades(self):
        """Test region state changes."""
        success, output = run_test_in_subprocess("TestRegionStateCascades")
        self.assertTrue(success, f"TestRegionStateCascades failed:\n{output}")


if __name__ == "__main__":
    unittest.main()
