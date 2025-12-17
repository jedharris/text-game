"""
Phase 0 tests - Infrastructure setup validation.

These tests verify that all the basic modules can be imported and
that the data structures are correct.
"""
from src.types import ActorId
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestPhase0Infrastructure(unittest.TestCase):
    """Test Phase 0 infrastructure setup."""

    def test_imports(self):
        """Verify all new modules can be imported."""
        from src.state_accessor import EventResult, UpdateResult, HandlerResult, StateAccessor
        from src.behavior_manager import BehaviorManager
        import utilities.utils

    def test_dataclass_structure(self):
        """Verify result dataclasses have expected fields."""
        from src.state_accessor import EventResult, UpdateResult, HandlerResult

        er = EventResult(allow=True, message="test")
        self.assertIs(er.allow, True)
        self.assertEqual(er.message, "test")

        ur = UpdateResult(success=True, message="test")
        self.assertIs(ur.success, True)

        hr = HandlerResult(success=True, message="test")
        self.assertIs(hr.success, True)

    def test_create_test_state(self):
        """Verify create_test_state() helper works."""
        from tests.conftest import create_test_state

        state = create_test_state()

        # Verify player exists
        player = state.actors.get(ActorId("player"))
        self.assertIsNotNone(player)
        self.assertEqual(player.location, "location_room")
        self.assertIsInstance(player.inventory, list)

        # Verify location exists
        self.assertEqual(len(state.locations), 1)
        self.assertEqual(state.locations[0].id, "location_room")

        # Verify test items exist
        self.assertEqual(len(state.items), 5)
        item_ids = {item.id for item in state.items}
        self.assertIn("item_sword", item_ids)
        self.assertIn("item_table", item_ids)
        self.assertIn("item_lantern", item_ids)
        self.assertIn("item_anvil", item_ids)
        self.assertIn("item_feather", item_ids)

        # Verify sword is portable
        sword = state.get_item("item_sword")
        self.assertTrue(sword.portable)

        # Verify table is not portable
        table = state.get_item("item_table")
        self.assertFalse(table.portable)


if __name__ == '__main__':
    unittest.main()
