"""
Tests for Phase 7: First Command Handler (handle_take)

These tests validate the first end-to-end command handler implementation,
with critical emphasis on actor_id threading for NPC support.
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_accessor import StateAccessor, HandlerResult
from src.behavior_manager import BehaviorManager
from src.state_manager import Actor
from tests.conftest import create_test_state


class TestPhase7HandleTake(unittest.TestCase):
    """Tests for handle_take command handler."""

    def test_handle_take_success(self):
        """Test player taking an item."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        # Load manipulation module
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        # Get handler
        handle_take = behavior_manager.get_handler("take")
        self.assertIsNotNone(handle_take, "handle_take should be registered")

        action = {"actor_id": "player", "object": "sword"}
        result = handle_take(accessor, action)

        self.assertTrue(result.success)
        self.assertIn("sword", result.message.lower())

        # Verify state changes
        sword = state.get_item("item_sword")
        self.assertEqual(sword.location, "player")
        self.assertIn("item_sword", state.actors["player"].inventory)

    def test_handle_take_not_portable(self):
        """Test that non-portable items can't be taken."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        handle_take = behavior_manager.get_handler("take")

        action = {"actor_id": "player", "object": "table"}
        result = handle_take(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't take", result.message.lower())

    def test_handle_take_not_found(self):
        """Test taking item that doesn't exist."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        handle_take = behavior_manager.get_handler("take")

        action = {"actor_id": "player", "object": "nonexistent"}
        result = handle_take(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_handle_take_npc(self):
        """Test NPC taking an item (critical for actor_id threading)."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        # Add NPC to room
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="location_room", inventory=[])
        state.actors["npc_guard"] = npc

        handle_take = behavior_manager.get_handler("take")

        action = {"actor_id": "npc_guard", "object": "sword"}
        result = handle_take(accessor, action)

        self.assertTrue(result.success, f"NPC take failed: {result.message}")

        # Verify item went to NPC, not player
        sword = state.get_item("item_sword")
        self.assertEqual(sword.location, "npc_guard",
                        f"Sword location should be npc_guard, got {sword.location}")
        self.assertIn("item_sword", npc.inventory)
        self.assertNotIn("item_sword", state.actors["player"].inventory)

    def test_handle_take_with_missing_actor(self):
        """Test that missing actor is handled gracefully."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        handle_take = behavior_manager.get_handler("take")

        action = {"actor_id": "nonexistent_npc", "object": "sword"}
        result = handle_take(accessor, action)

        # Should return HandlerResult with error, not crash
        self.assertFalse(result.success)
        self.assertIsInstance(result, HandlerResult)

    def test_handle_take_vocabulary_registered(self):
        """Test that vocabulary is properly registered."""
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)

        # Check that "take" verb maps to "on_take" event
        event = behavior_manager.get_event_for_verb("take")
        self.assertEqual(event, "on_take")

        # Check synonyms
        self.assertEqual(behavior_manager.get_event_for_verb("get"), "on_take")
        self.assertEqual(behavior_manager.get_event_for_verb("grab"), "on_take")

    def test_handle_take_already_in_inventory(self):
        """Test taking item that's already in inventory."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        # Put sword in player's inventory
        player = state.actors["player"]
        sword = state.get_item("item_sword")
        sword.location = "player"
        player.inventory.append("item_sword")

        handle_take = behavior_manager.get_handler("take")

        action = {"actor_id": "player", "object": "sword"}
        result = handle_take(accessor, action)

        # Should succeed (item is accessible in inventory)
        self.assertTrue(result.success)


if __name__ == '__main__':
    unittest.main()
