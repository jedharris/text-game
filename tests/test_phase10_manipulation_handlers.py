"""
Phase 10: Complete Manipulation Handlers

Tests for handle_drop, handle_put, and handle_give command handlers.
Critical: Each handler must have NPC tests to validate actor_id threading.
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


class TestPhase10ManipulationHandlers(unittest.TestCase):
    """Tests for drop, put, and give handlers."""

    # ========== DROP TESTS ==========

    def test_handle_drop_success(self):
        """Test player dropping an item."""
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

        from behaviors.core.manipulation import handle_drop
        action = {"actor_id": "player", "object": "sword"}
        result = handle_drop(accessor, action)

        self.assertTrue(result.success)
        self.assertIn("sword", result.message.lower())

        # Verify state changes
        self.assertNotIn("item_sword", player.inventory)
        self.assertEqual(sword.location, "location_room")

    def test_handle_drop_not_in_inventory(self):
        """Test that drop fails if item not in inventory."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.manipulation import handle_drop
        action = {"actor_id": "player", "object": "sword"}
        result = handle_drop(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't have", result.message.lower())

    def test_handle_drop_npc(self):
        """Test NPC dropping an item (critical for actor_id threading)."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        # Add NPC with item in inventory
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=["item_sword"]
        )
        state.actors["npc_guard"] = guard

        # Set sword location to NPC
        sword = state.get_item("item_sword")
        sword.location = "npc_guard"

        from behaviors.core.manipulation import handle_drop
        action = {"actor_id": "npc_guard", "object": "sword"}
        result = handle_drop(accessor, action)

        self.assertTrue(result.success, f"NPC drop failed: {result.message}")
        self.assertNotIn("item_sword", guard.inventory)
        self.assertEqual(sword.location, "location_room")

    # ========== GIVE TESTS ==========

    def test_handle_give_success(self):
        """Test player giving an item to an NPC."""
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

        # Add NPC in same location
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=[]
        )
        state.actors["npc_guard"] = guard

        from behaviors.core.manipulation import handle_give
        action = {"actor_id": "player", "object": "sword", "indirect_object": "guard"}
        result = handle_give(accessor, action)

        self.assertTrue(result.success)

        # Verify state changes
        self.assertNotIn("item_sword", player.inventory)
        self.assertIn("item_sword", guard.inventory)
        self.assertEqual(sword.location, "npc_guard")

    def test_handle_give_not_in_inventory(self):
        """Test that give fails if item not in inventory."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        # Add NPC in same location
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=[]
        )
        state.actors["npc_guard"] = guard

        from behaviors.core.manipulation import handle_give
        action = {"actor_id": "player", "object": "sword", "indirect_object": "guard"}
        result = handle_give(accessor, action)

        self.assertFalse(result.success)

    def test_handle_give_recipient_not_present(self):
        """Test that give fails if recipient not in same location."""
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

        from behaviors.core.manipulation import handle_give
        action = {"actor_id": "player", "object": "sword", "indirect_object": "nonexistent"}
        result = handle_give(accessor, action)

        self.assertFalse(result.success)

    def test_handle_give_npc_to_player(self):
        """Test NPC giving an item to player (critical for actor_id threading)."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        # Add NPC with item
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=["item_sword"]
        )
        state.actors["npc_guard"] = guard

        sword = state.get_item("item_sword")
        sword.location = "npc_guard"

        from behaviors.core.manipulation import handle_give
        # Use player's actual name ("Adventurer") not the ID ("player")
        action = {"actor_id": "npc_guard", "object": "sword", "indirect_object": "Adventurer"}
        result = handle_give(accessor, action)

        self.assertTrue(result.success, f"NPC give failed: {result.message}")
        player = state.actors["player"]
        self.assertNotIn("item_sword", guard.inventory, "Item should be removed from NPC")
        self.assertIn("item_sword", player.inventory, "Item should be in player inventory")
        self.assertEqual(sword.location, "player")


if __name__ == '__main__':
    unittest.main()
