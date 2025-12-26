"""
Phase 11: Movement and Perception Handlers

Tests for handle_go, handle_look, handle_examine, and handle_inventory.
Critical: Movement and perception must work from NPC perspective.
"""
from src.types import ActorId

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_accessor import StateAccessor, HandlerResult
from src.behavior_manager import BehaviorManager
from src.state_manager import Actor, Location
from tests.conftest import make_action, create_test_state


class TestPhase11MovementPerception(unittest.TestCase):
    """Tests for movement and perception handlers."""

    # ========== MOVEMENT TESTS ==========

    def test_handle_go_success(self):
        """Test player moving to adjacent location."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # Add a second room
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"west": "location_room"},
            items=[],
        )
        state.locations.append(hall)

        # Connect rooms
        room = state.get_location("location_room")
        room.exits["east"] = "location_hall"

        import behaviors.core.exits
        behavior_manager.load_module(behaviors.core.exits)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.exits import handle_go
        action = make_action(object="east", actor_id="player")
        result = handle_go(accessor, action)

        self.assertTrue(result.success)

        # Verify player moved
        player = state.get_actor(ActorId("player"))
        self.assertEqual(player.location, "location_hall")

    def test_handle_go_invalid_exit(self):
        """Test that going in invalid direction fails."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.exits
        behavior_manager.load_module(behaviors.core.exits)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.exits import handle_go
        action = make_action(object="north", actor_id="player")
        result = handle_go(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't go", result.primary.lower())

    def test_handle_go_npc(self):
        """Test NPC movement (critical for actor_id threading)."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # Add a second room
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"west": "location_room"},
            items=[],
        )
        state.locations.append(hall)

        # Connect rooms
        room = state.get_location("location_room")
        room.exits["east"] = "location_hall"

        # Add NPC
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=[]
        )
        state.actors[ActorId("npc_guard")] = guard

        import behaviors.core.exits
        behavior_manager.load_module(behaviors.core.exits)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.exits import handle_go
        action = make_action(object="east", actor_id="npc_guard")
        result = handle_go(accessor, action)

        self.assertTrue(result.success, f"NPC movement failed: {result.primary}")

        # Verify NPC moved (not player)
        self.assertEqual(guard.location, "location_hall")
        player = state.get_actor(ActorId("player"))
        self.assertEqual(player.location, "location_room", "Player should not have moved")

    # ========== PERCEPTION TESTS ==========

    def test_handle_look_lists_items(self):
        """Test that look shows visible items in location."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.perception
        behavior_manager.load_module(behaviors.core.perception)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.perception import handle_look
        action = make_action(actor_id="player")
        result = handle_look(accessor, action)

        self.assertTrue(result.success)
        # Should mention items in room
        self.assertIn("sword", result.primary.lower())

    def test_handle_look_npc_perspective(self):
        """Test look from NPC perspective in different location."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # Add a second room with different items
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={},
            items=["item_table"],  # Only table in hall
        )
        state.locations.append(hall)

        # Move table to hall
        table = state.get_item("item_table")
        table.location = "location_hall"

        # Add NPC in hall
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_hall",
            inventory=[]
        )
        state.actors[ActorId("npc_guard")] = guard

        import behaviors.core.perception
        behavior_manager.load_module(behaviors.core.perception)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.perception import handle_look
        action = make_action(actor_id="npc_guard")
        result = handle_look(accessor, action)

        self.assertTrue(result.success, f"NPC look failed: {result.primary}")
        # Should see table (in hall), not sword (in room)
        self.assertIn("table", result.primary.lower())
        self.assertNotIn("sword", result.primary.lower())

    def test_handle_examine_item(self):
        """Test examining an item."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.perception
        behavior_manager.load_module(behaviors.core.perception)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.perception import handle_examine
        action = make_action(object="sword", actor_id="player")
        result = handle_examine(accessor, action)

        self.assertTrue(result.success)
        # Should show item description
        self.assertIn("sword", result.primary.lower())

    def test_handle_examine_not_found(self):
        """Test examining non-existent item fails."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.perception
        behavior_manager.load_module(behaviors.core.perception)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.perception import handle_examine
        action = make_action(object="dragon", actor_id="player")
        result = handle_examine(accessor, action)

        self.assertFalse(result.success)

    def test_handle_inventory_player(self):
        """Test player inventory command."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # Give player an item
        player = state.get_actor(ActorId("player"))
        sword = state.get_item("item_sword")
        sword.location = "player"
        player.inventory.append("item_sword")

        import behaviors.core.perception
        behavior_manager.load_module(behaviors.core.perception)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.perception import handle_inventory
        action = make_action(actor_id="player")
        result = handle_inventory(accessor, action)

        self.assertTrue(result.success)
        self.assertIn("sword", result.primary.lower())

    def test_handle_inventory_npc(self):
        """Test NPC inventory command (critical for actor_id threading)."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # Give player an item
        player = state.get_actor(ActorId("player"))
        sword = state.get_item("item_sword")
        sword.location = "player"
        player.inventory.append("item_sword")

        # Add NPC with different item
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=["item_lantern"]
        )
        state.actors[ActorId("npc_guard")] = guard

        lantern = state.get_item("item_lantern")
        lantern.location = "npc_guard"

        import behaviors.core.perception
        behavior_manager.load_module(behaviors.core.perception)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.perception import handle_inventory
        action = make_action(actor_id="npc_guard")
        result = handle_inventory(accessor, action)

        self.assertTrue(result.success, f"NPC inventory failed: {result.primary}")
        # Should show NPC's items, not player's
        self.assertIn("lantern", result.primary.lower())
        self.assertNotIn("sword", result.primary.lower())

    def test_handle_inventory_empty(self):
        """Test inventory when empty."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.perception
        behavior_manager.load_module(behaviors.core.perception)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.perception import handle_inventory
        action = make_action(actor_id="player")
        result = handle_inventory(accessor, action)

        self.assertTrue(result.success)
        # Should indicate empty inventory (either "nothing" or "empty")
        self.assertTrue("nothing" in result.primary.lower() or "empty" in result.primary.lower())


if __name__ == '__main__':
    unittest.main()
