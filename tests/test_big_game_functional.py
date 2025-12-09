"""Big Game functional tests - subprocess wrapper.

This module runs the functional tests from _big_game_functional_impl.py
in separate subprocesses to avoid module pollution issues.

The tests verify:
- Game loading and data validation
- Movement mechanics
- Query mechanics
- Region/faction/world event system integration
- Data consistency
"""

import subprocess
import sys
import unittest
from pathlib import Path


# Get paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
IMPL_MODULE = "_big_game_functional_impl"


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


class TestBigGameFunctional(unittest.TestCase):
    """Run big_game functional tests in subprocesses."""

    def test_big_game_loading(self):
        """Test game loading."""
        success, output = run_test_in_subprocess("TestBigGameLoading")
        self.assertTrue(success, f"TestBigGameLoading failed:\n{output}")

    def test_big_game_movement(self):
        """Test movement mechanics."""
        success, output = run_test_in_subprocess("TestBigGameMovement")
        self.assertTrue(success, f"TestBigGameMovement failed:\n{output}")

    def test_big_game_queries(self):
        """Test query mechanics."""
        success, output = run_test_in_subprocess("TestBigGameQueries")
        self.assertTrue(success, f"TestBigGameQueries failed:\n{output}")

    def test_big_game_regions(self):
        """Test region configuration."""
        success, output = run_test_in_subprocess("TestBigGameRegions")
        self.assertTrue(success, f"TestBigGameRegions failed:\n{output}")

    def test_big_game_actors(self):
        """Test actor configuration."""
        success, output = run_test_in_subprocess("TestBigGameActors")
        self.assertTrue(success, f"TestBigGameActors failed:\n{output}")

    def test_big_game_items(self):
        """Test item configuration."""
        success, output = run_test_in_subprocess("TestBigGameItems")
        self.assertTrue(success, f"TestBigGameItems failed:\n{output}")

    def test_big_game_behavior_modules(self):
        """Test behavior module loading."""
        success, output = run_test_in_subprocess("TestBigGameBehaviorModules")
        self.assertTrue(success, f"TestBigGameBehaviorModules failed:\n{output}")

    def test_big_game_region_behaviors(self):
        """Test region behavior functionality."""
        success, output = run_test_in_subprocess("TestBigGameRegionBehaviors")
        self.assertTrue(success, f"TestBigGameRegionBehaviors failed:\n{output}")

    def test_big_game_actor_behaviors(self):
        """Test actor behavior functionality."""
        success, output = run_test_in_subprocess("TestBigGameActorBehaviors")
        self.assertTrue(success, f"TestBigGameActorBehaviors failed:\n{output}")

    def test_region_system_integration(self):
        """Test region system integration."""
        success, output = run_test_in_subprocess("TestRegionSystemIntegration")
        self.assertTrue(success, f"TestRegionSystemIntegration failed:\n{output}")

    def test_faction_system_integration(self):
        """Test faction system integration."""
        success, output = run_test_in_subprocess("TestFactionSystemIntegration")
        self.assertTrue(success, f"TestFactionSystemIntegration failed:\n{output}")

    def test_world_events_integration(self):
        """Test world events integration."""
        success, output = run_test_in_subprocess("TestWorldEventsIntegration")
        self.assertTrue(success, f"TestWorldEventsIntegration failed:\n{output}")

    def test_echo_integration(self):
        """Test The Echo NPC mechanics."""
        success, output = run_test_in_subprocess("TestEchoIntegration")
        self.assertTrue(success, f"TestEchoIntegration failed:\n{output}")

    def test_cross_system_integration(self):
        """Test cross-system integration."""
        success, output = run_test_in_subprocess("TestCrossSystemIntegration")
        self.assertTrue(success, f"TestCrossSystemIntegration failed:\n{output}")

    def test_game_state_consistency(self):
        """Test game state data consistency."""
        success, output = run_test_in_subprocess("TestGameStateConsistency")
        self.assertTrue(success, f"TestGameStateConsistency failed:\n{output}")

    # Phase 3: Extended tests

    def test_movement_edge_cases(self):
        """Test movement edge cases."""
        success, output = run_test_in_subprocess("TestMovementEdgeCases")
        self.assertTrue(success, f"TestMovementEdgeCases failed:\n{output}")

    def test_region_system_extended(self):
        """Test extended region system functionality."""
        success, output = run_test_in_subprocess("TestRegionSystemExtended")
        self.assertTrue(success, f"TestRegionSystemExtended failed:\n{output}")

    def test_faction_system_extended(self):
        """Test extended faction system functionality."""
        success, output = run_test_in_subprocess("TestFactionSystemExtended")
        self.assertTrue(success, f"TestFactionSystemExtended failed:\n{output}")

    def test_world_events_extended(self):
        """Test extended world events functionality."""
        success, output = run_test_in_subprocess("TestWorldEventsExtended")
        self.assertTrue(success, f"TestWorldEventsExtended failed:\n{output}")

    def test_echo_extended(self):
        """Test extended Echo NPC mechanics."""
        success, output = run_test_in_subprocess("TestEchoExtended")
        self.assertTrue(success, f"TestEchoExtended failed:\n{output}")

    def test_actor_configuration_extended(self):
        """Test extended actor configuration."""
        success, output = run_test_in_subprocess("TestActorConfigurationExtended")
        self.assertTrue(success, f"TestActorConfigurationExtended failed:\n{output}")

    def test_item_configuration_extended(self):
        """Test extended item configuration."""
        success, output = run_test_in_subprocess("TestItemConfigurationExtended")
        self.assertTrue(success, f"TestItemConfigurationExtended failed:\n{output}")

    def test_dialog_system_extended(self):
        """Test extended dialog system."""
        success, output = run_test_in_subprocess("TestDialogSystemExtended")
        self.assertTrue(success, f"TestDialogSystemExtended failed:\n{output}")

    def test_query_system_extended(self):
        """Test extended query system."""
        success, output = run_test_in_subprocess("TestQuerySystemExtended")
        self.assertTrue(success, f"TestQuerySystemExtended failed:\n{output}")

    def test_data_consistency_extended(self):
        """Test extended data consistency."""
        success, output = run_test_in_subprocess("TestDataConsistencyExtended")
        self.assertTrue(success, f"TestDataConsistencyExtended failed:\n{output}")


if __name__ == "__main__":
    unittest.main()
