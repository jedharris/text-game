"""
Phase 1 tests - StateAccessor Core (Read-Only)

These tests verify the getter methods of StateAccessor.
Following TDD: Write tests first, then implement to make them pass.
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import create_test_state
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager


class TestStateAccessorGetters(unittest.TestCase):
    """Test StateAccessor getter methods."""

    def test_get_item_found(self):
        """Test retrieving an item that exists."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = accessor.get_item("item_sword")
        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_sword")

    def test_get_item_not_found(self):
        """Test retrieving an item that doesn't exist returns None."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = accessor.get_item("nonexistent")
        self.assertIsNone(item)

    def test_get_actor_player(self):
        """Test retrieving the player actor."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        # Note: Currently returns PlayerState, will be unified Actor in Phase 3
        player = accessor.get_actor("player")
        self.assertIsNotNone(player)
        self.assertEqual(player.location, "location_room")

    def test_get_location_found(self):
        """Test retrieving a location that exists."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        location = accessor.get_location("location_room")
        self.assertIsNotNone(location)
        self.assertEqual(location.id, "location_room")

    def test_get_location_not_found(self):
        """Test retrieving a location that doesn't exist returns None."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        location = accessor.get_location("nonexistent")
        self.assertIsNone(location)

    def test_get_lock_found(self):
        """Test retrieving a lock that exists."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        # Add a lock to test with
        from src.state_manager import Lock
        lock = Lock(id="lock_test", properties={"opens_with": ["item_key"]})
        state.locks.append(lock)

        retrieved = accessor.get_lock("lock_test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "lock_test")

    def test_get_lock_not_found(self):
        """Test retrieving a lock that doesn't exist returns None."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        lock = accessor.get_lock("nonexistent")
        self.assertIsNone(lock)


class TestStateAccessorCollections(unittest.TestCase):
    """Test StateAccessor collection methods."""

    def test_get_current_location(self):
        """Test getting actor's current location."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        location = accessor.get_current_location("player")
        self.assertIsNotNone(location)
        self.assertEqual(location.id, "location_room")

    def test_get_items_in_location(self):
        """Test retrieving items in a location."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        items = accessor.get_items_in_location("location_room")
        self.assertGreater(len(items), 0)
        item_ids = [item.id for item in items]
        self.assertIn("item_sword", item_ids)

    def test_get_actors_in_location(self):
        """Test retrieving actors in a location."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        # Note: In current model, this returns NPCs only
        # In Phase 3 unified model, it will include player
        actors = accessor.get_actors_in_location("location_room")
        self.assertIsInstance(actors, list)

    def test_get_actors_in_location_with_npc(self):
        """Test that get_actors_in_location returns NPCs."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        # Add an NPC using unified model
        from src.state_manager import Actor
        npc = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=[],
            properties={},
            behaviors=[]
        )
        state.actors["npc_guard"] = npc

        actors = accessor.get_actors_in_location("location_room")
        self.assertGreater(len(actors), 0)
        actor_ids = [actor.id for actor in actors]
        self.assertIn("npc_guard", actor_ids)


if __name__ == '__main__':
    unittest.main()
