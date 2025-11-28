"""
Tests for Phase 6: Utility Functions

These tests validate utility functions for searching and visibility,
with special emphasis on actor_id threading to ensure NPCs work correctly.
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.state_manager import Actor, Item, Lock, Location, ExitDescriptor
from tests.conftest import create_test_state


def create_door_item(door_id: str, location_id: str, direction: str,
                     open: bool = False, locked: bool = False, lock_id: str = None,
                     description: str = "A door") -> Item:
    """Helper to create a door item in the new unified format."""
    door_props = {"open": open, "locked": locked}
    if lock_id:
        door_props["lock_id"] = lock_id
    return Item(
        id=door_id,
        name="door",
        description=description,
        location=f"exit:{location_id}:{direction}",
        properties={"door": door_props}
    )


from utilities.utils import (
    find_accessible_item,
    find_item_in_inventory,
    find_container_by_name,
    actor_has_key_for_door,
    get_visible_items_in_location,
    get_visible_actors_in_location,
    get_doors_in_location
)


class TestPhase6UtilityFunctions(unittest.TestCase):
    """Tests for utility functions with actor_id threading."""

    def test_find_accessible_item_in_location(self):
        """Test finding item in actor's current location."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        item = find_accessible_item(accessor, "sword", "player")

        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_sword")

    def test_find_accessible_item_in_inventory(self):
        """Test finding item in actor's inventory."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        # Put sword in player's inventory
        player = state.actors["player"]
        sword = state.get_item("item_sword")
        sword.location = "player"
        player.inventory.append("item_sword")

        item = find_accessible_item(accessor, "sword", "player")

        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_sword")

    def test_find_accessible_item_not_found(self):
        """Test that nonexistent item returns None."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        item = find_accessible_item(accessor, "nonexistent", "player")

        self.assertIsNone(item)

    def test_find_accessible_item_for_npc(self):
        """Test finding item accessible to NPC, not player."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        # Create location for NPC
        from src.state_manager import Location
        other_room = Location(id="other_room", name="Other Room",
                             description="Another room", exits={}, items=["item_key"],
                             properties={}, behaviors=[])
        state.locations.append(other_room)

        # Create NPC in different location
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="other_room", inventory=[])
        state.actors["npc_guard"] = npc

        # Create item in NPC's location
        key = Item(id="item_key", name="key", description="A key",
                  location="other_room")
        state.items.append(key)

        # NPC should find key in their location
        item = find_accessible_item(accessor, "key", "npc_guard")
        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_key")

        # Player should NOT find key (it's in different location)
        item = find_accessible_item(accessor, "key", "player")
        self.assertIsNone(item)

    def test_find_item_in_inventory_player(self):
        """Test finding item in player's inventory."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        player = state.actors["player"]
        player.inventory.append("item_sword")

        item = find_item_in_inventory(accessor, "sword", "player")

        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_sword")

    def test_find_item_in_inventory_npc(self):
        """Test finding item in NPC's inventory, not player's."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        # Create NPC with item
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="location_room", inventory=["item_key"])
        state.actors["npc_guard"] = npc

        key = Item(id="item_key", name="key", description="A key",
                  location="npc_guard")
        state.items.append(key)

        # NPC should find key in their inventory
        item = find_item_in_inventory(accessor, "key", "npc_guard")
        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_key")

        # Player should NOT find key
        item = find_item_in_inventory(accessor, "key", "player")
        self.assertIsNone(item)

    def test_find_container_by_name(self):
        """Test finding a container in a location."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        # Create a container
        chest = Item(id="item_chest", name="chest", description="A chest",
                    location="location_room",
                    properties={"is_container": True, "portable": False})
        state.items.append(chest)

        container = find_container_by_name(accessor, "chest", "location_room")

        self.assertIsNotNone(container)
        self.assertEqual(container.id, "item_chest")

    def test_find_container_not_found(self):
        """Test that nonexistent container returns None."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        container = find_container_by_name(accessor, "nonexistent", "location_room")

        self.assertIsNone(container)

    def test_actor_has_key_for_door_player(self):
        """Test checking if player has key."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        # Add hall location and exits
        hall = Location(
            id="hall",
            name="Hall",
            description="A hall",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="hall", door_id="door_main")

        # Create door item with lock
        door = create_door_item("door_main", "location_room", "north",
                                open=True, locked=False, lock_id="lock_main")
        state.items.append(door)

        lock = Lock(id="lock_main", name="main lock", description="The main lock", properties={"locked": True, "opens_with": ["item_key"]})
        state.locks.append(lock)

        key = Item(id="item_key", name="key", description="A key",
                  location="player")
        state.items.append(key)

        player = state.actors["player"]
        player.inventory.append("item_key")

        # Player has key
        self.assertTrue(actor_has_key_for_door(accessor, "player", door))

    def test_actor_has_key_for_door_npc(self):
        """Test checking if NPC has key, not player."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        # Add hall location and exits
        hall = Location(
            id="hall",
            name="Hall",
            description="A hall",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="hall", door_id="door_main")

        # Create door item with lock
        door = create_door_item("door_main", "location_room", "north",
                                open=True, locked=False, lock_id="lock_main")
        state.items.append(door)

        lock = Lock(id="lock_main", name="main lock", description="The main lock", properties={"locked": True, "opens_with": ["item_key"]})
        state.locks.append(lock)

        # Give key to NPC, not player
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="location_room", inventory=["item_key"])
        state.actors["npc_guard"] = npc

        key = Item(id="item_key", name="key", description="A key",
                  location="npc_guard")
        state.items.append(key)

        # NPC has key
        self.assertTrue(actor_has_key_for_door(accessor, "npc_guard", door))

        # Player does NOT have key
        self.assertFalse(actor_has_key_for_door(accessor, "player", door))

    def test_get_visible_items_in_location(self):
        """Test getting visible items in a location."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        items = get_visible_items_in_location(accessor, "location_room", "player")

        # Should find the sword
        item_ids = [item.id for item in items]
        self.assertIn("item_sword", item_ids)

    def test_get_visible_actors_excludes_self(self):
        """Test that get_visible_actors excludes the viewing actor."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        # Create NPC in same location as player
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="location_room", inventory=[])
        state.actors["npc_guard"] = npc

        actors = get_visible_actors_in_location(accessor, "location_room", "player")

        # Should find NPC but not player
        actor_ids = [actor.id for actor in actors]
        self.assertIn("npc_guard", actor_ids)
        self.assertNotIn("player", actor_ids)

    def test_get_visible_actors_npc_perspective(self):
        """Test get_visible_actors from NPC's perspective."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        # Create NPC in same location as player
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="location_room", inventory=[])
        state.actors["npc_guard"] = npc

        actors = get_visible_actors_in_location(accessor, "location_room", "npc_guard")

        # Should find player but not NPC itself
        actor_ids = [actor.id for actor in actors]
        self.assertIn("player", actor_ids)
        self.assertNotIn("npc_guard", actor_ids)

    def test_get_doors_in_location(self):
        """Test getting doors in a location."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        # Add hall location and exits
        hall = Location(
            id="hall",
            name="Hall",
            description="A hall",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="hall", door_id="door_main")

        # Create door item
        door = create_door_item("door_main", "location_room", "north", open=True)
        state.items.append(door)

        doors = get_doors_in_location(accessor, "location_room", "player")

        # Should find the door
        door_ids = [d.id for d in doors]
        self.assertIn("door_main", door_ids)

    def test_get_doors_in_location_no_doors(self):
        """Test getting doors when none exist."""
        state = create_test_state()
        accessor = StateAccessor(state, BehaviorManager())

        doors = get_doors_in_location(accessor, "location_room", "player")

        # Should return empty list
        self.assertEqual(len(doors), 0)


if __name__ == '__main__':
    unittest.main()
