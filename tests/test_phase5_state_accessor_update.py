"""
Tests for Phase 5: StateAccessor.update() - Without Behaviors

These tests validate the update() method that applies state changes
without invoking behaviors (behaviors come in later phases).
"""
from src.types import ActorId
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_accessor import StateAccessor, UpdateResult
from src.behavior_manager import BehaviorManager
from tests.conftest import create_test_state


class TestPhase5StateAccessorUpdate(unittest.TestCase):
    """Tests for StateAccessor.update() without behavior invocation."""

    def test_update_simple_change(self):
        """Test update with a simple field change."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        item = state.get_item("item_sword")
        result = accessor.update(
            entity=item,
            changes={"location": "new_location"}
        )

        self.assertTrue(result.success)
        self.assertEqual(item.location, "new_location")

    def test_update_multiple_changes(self):
        """Test update with multiple changes."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        item = state.get_item("item_sword")
        result = accessor.update(
            entity=item,
            changes={
                "location": "new_location",
                "properties.visible": True
            }
        )

        self.assertTrue(result.success)
        self.assertEqual(item.location, "new_location")
        self.assertEqual(item.properties.get("visible"), True)

    def test_update_with_error(self):
        """Test that update returns error from _set_path."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        item = state.get_item("item_sword")
        result = accessor.update(
            entity=item,
            changes={"nonexistent_field": "value"}
        )

        self.assertFalse(result.success)
        self.assertIsNotNone(result.detail)
        self.assertIn("nonexistent_field", result.detail)

    def test_update_with_actor_id(self):
        """Test that update accepts actor_id parameter."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        actor = accessor.get_actor(ActorId("player"))
        result = accessor.update(
            entity=actor,
            changes={"location": "room2"},
            actor_id="player"
        )

        self.assertTrue(result.success)
        self.assertEqual(actor.location, "room2")

    def test_update_with_verb(self):
        """Test that update accepts verb parameter."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        item = state.get_item("item_sword")
        result = accessor.update(
            entity=item,
            changes={"location": "new_location"},
            verb="take"
        )

        self.assertTrue(result.success)
        self.assertEqual(item.location, "new_location")

    def test_update_list_append(self):
        """Test update with list append operation."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        actor = accessor.get_actor(ActorId("player"))
        result = accessor.update(
            entity=actor,
            changes={"+inventory": "item_sword"}
        )

        self.assertTrue(result.success)
        self.assertIn("item_sword", actor.inventory)

    def test_update_list_remove(self):
        """Test update with list remove operation."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        actor = accessor.get_actor(ActorId("player"))
        # First add an item
        actor.inventory.append("item_sword")

        # Now remove it
        result = accessor.update(
            entity=actor,
            changes={"-inventory": "item_sword"}
        )

        self.assertTrue(result.success)
        self.assertNotIn("item_sword", actor.inventory)

    def test_update_nested_field(self):
        """Test update with nested field path."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        item = state.get_item("item_sword")
        result = accessor.update(
            entity=item,
            changes={"properties.weight": 15}
        )

        self.assertTrue(result.success)
        self.assertEqual(item.properties.get("weight"), 15)

    def test_update_partial_failure(self):
        """Test that update stops on first error."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        item = state.get_item("item_sword")
        original_location = item.location

        result = accessor.update(
            entity=item,
            changes={
                "location": "new_location",
                "nonexistent_field": "value"  # This should fail
            }
        )

        self.assertFalse(result.success)
        self.assertIsNotNone(result.detail)

    def test_update_empty_changes(self):
        """Test update with empty changes dict."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        item = state.get_item("item_sword")
        result = accessor.update(
            entity=item,
            changes={}
        )

        self.assertTrue(result.success)

    def test_update_returns_update_result(self):
        """Test that update returns UpdateResult type."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        item = state.get_item("item_sword")
        result = accessor.update(
            entity=item,
            changes={"location": "new_location"}
        )

        self.assertIsInstance(result, UpdateResult)
        self.assertTrue(hasattr(result, 'success'))
        self.assertTrue(hasattr(result, 'detail'))


if __name__ == '__main__':
    unittest.main()
