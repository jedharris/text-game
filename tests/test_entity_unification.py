"""
Tests for Entity Unification: Items and Doors.

This test module covers the unification of Items and Doors into a single Item type.
Doors become items with properties.door defined.

Phase 1: Tests for door properties, visibility, and find_accessible_item with doors.
"""

import unittest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_manager import Item, Location, ExitDescriptor, load_game_state
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager


class TestItemDoorProperties(unittest.TestCase):
    """Test door-related properties on Item dataclass."""

    def test_is_door_true_when_door_properties_present(self):
        """Item with properties.door is recognized as door."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"open": False}}
        )
        self.assertTrue(item.is_door)

    def test_is_door_false_for_regular_item(self):
        """Regular item is not a door."""
        item = Item(
            id="sword", name="sword", description="A sword",
            location="loc_room",
            properties={"portable": True}
        )
        self.assertFalse(item.is_door)

    def test_door_open_getter(self):
        """door_open returns door's open state."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"open": True}}
        )
        self.assertTrue(item.door_open)

    def test_door_open_false_when_not_door(self):
        """door_open returns False for non-doors."""
        item = Item(
            id="sword", name="sword", description="A sword",
            location="loc_room", properties={}
        )
        self.assertFalse(item.door_open)

    def test_door_open_setter(self):
        """door_open setter updates door state."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"open": False}}
        )
        item.door_open = True
        self.assertTrue(item.properties["door"]["open"])

    def test_door_open_setter_creates_door_dict(self):
        """door_open setter creates door dict if missing."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room", properties={}
        )
        item.door_open = True
        self.assertTrue(item.properties["door"]["open"])

    def test_door_locked_getter(self):
        """door_locked returns door's locked state."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"locked": True}}
        )
        self.assertTrue(item.door_locked)

    def test_door_locked_false_when_not_door(self):
        """door_locked returns False for non-doors."""
        item = Item(
            id="sword", name="sword", description="A sword",
            location="loc_room", properties={}
        )
        self.assertFalse(item.door_locked)

    def test_door_locked_setter(self):
        """door_locked setter updates door state."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"locked": True}}
        )
        item.door_locked = False
        self.assertFalse(item.properties["door"]["locked"])

    def test_door_locked_setter_creates_door_dict(self):
        """door_locked setter creates door dict if missing."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room", properties={}
        )
        item.door_locked = True
        self.assertTrue(item.properties["door"]["locked"])

    def test_door_lock_id_getter(self):
        """door_lock_id returns lock reference."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"lock_id": "lock_1"}}
        )
        self.assertEqual(item.door_lock_id, "lock_1")

    def test_door_lock_id_none_when_no_lock(self):
        """door_lock_id returns None when no lock."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"open": False}}
        )
        self.assertIsNone(item.door_lock_id)

    def test_door_lock_id_none_for_non_door(self):
        """door_lock_id returns None for non-doors."""
        item = Item(
            id="sword", name="sword", description="A sword",
            location="loc_room", properties={}
        )
        self.assertIsNone(item.door_lock_id)


class TestStateAccessorDoorMethods(unittest.TestCase):
    """Test StateAccessor door-related methods."""

    def setUp(self):
        """Create state with door item."""
        # Build state manually to avoid validation issues
        from src.state_manager import GameState, Metadata, Actor

        self.state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="loc_room",
                    name="Room",
                    description="A room",
                    exits={
                        "north": ExitDescriptor(type="door", to="loc_other", door_id="door_1")
                    }
                ),
                Location(
                    id="loc_other",
                    name="Other Room",
                    description="Another room",
                    exits={
                        "south": ExitDescriptor(type="door", to="loc_room", door_id="door_1")
                    }
                )
            ],
            items=[
                Item(
                    id="door_1",
                    name="door",
                    description="A door.",
                    location="exit:loc_room:north",
                    properties={"door": {"open": False}}
                ),
                Item(
                    id="item_sword",
                    name="sword",
                    description="A sword.",
                    location="loc_room",
                    properties={}
                )
            ],
            actors={"player": Actor(
                id="player", name="Player", description="The player",
                location="loc_room", inventory=[]
            )}
        )
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_get_door_item_returns_door(self):
        """get_door_item returns door item."""
        door = self.accessor.get_door_item("door_1")
        self.assertIsNotNone(door)
        self.assertEqual(door.id, "door_1")
        self.assertTrue(door.is_door)

    def test_get_door_item_returns_none_for_regular_item(self):
        """get_door_item returns None for non-door items."""
        result = self.accessor.get_door_item("item_sword")
        self.assertIsNone(result)

    def test_get_door_item_returns_none_for_missing(self):
        """get_door_item returns None for missing ID."""
        result = self.accessor.get_door_item("nonexistent")
        self.assertIsNone(result)

    def test_get_door_for_exit_returns_door(self):
        """get_door_for_exit returns door for exit with door."""
        door = self.accessor.get_door_for_exit("loc_room", "north")
        self.assertIsNotNone(door)
        self.assertEqual(door.id, "door_1")

    def test_get_door_for_exit_returns_none_for_open_exit(self):
        """get_door_for_exit returns None for exit without door."""
        # Add open exit
        self.state.locations[0].exits["south"] = ExitDescriptor(
            type="open", to="loc_south"
        )
        result = self.accessor.get_door_for_exit("loc_room", "south")
        self.assertIsNone(result)

    def test_get_door_for_exit_returns_none_for_invalid_direction(self):
        """get_door_for_exit returns None for invalid direction."""
        result = self.accessor.get_door_for_exit("loc_room", "west")
        self.assertIsNone(result)

    def test_get_door_for_exit_returns_none_for_invalid_location(self):
        """get_door_for_exit returns None for invalid location."""
        result = self.accessor.get_door_for_exit("nonexistent", "north")
        self.assertIsNone(result)


class TestDoorVisibility(unittest.TestCase):
    """Test door visibility from connected locations."""

    def setUp(self):
        """Create test state with door connecting two rooms."""
        from src.state_manager import GameState, Metadata, Actor

        self.state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="loc_room1",
                    name="Room 1",
                    description="First room",
                    exits={
                        "east": ExitDescriptor(type="door", to="loc_room2", door_id="door_connecting")
                    }
                ),
                Location(
                    id="loc_room2",
                    name="Room 2",
                    description="Second room",
                    exits={
                        "west": ExitDescriptor(type="door", to="loc_room1", door_id="door_connecting")
                    }
                ),
                Location(
                    id="loc_room3",
                    name="Room 3",
                    description="Third room with no connection",
                    exits={}
                )
            ],
            items=[
                Item(
                    id="door_connecting",
                    name="door",
                    description="A wooden door.",
                    location="exit:loc_room1:east",
                    properties={"door": {"open": False}}
                )
            ],
            actors={"player": Actor(
                id="player", name="Player", description="The player",
                location="loc_room1", inventory=[]
            )}
        )
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_door_visible_from_first_room(self):
        """Door is visible from room1 (has exit referencing it)."""
        from utilities.utils import gather_location_contents

        contents = gather_location_contents(self.accessor, "loc_room1", "player")
        item_ids = [item.id for item in contents["items"]]
        self.assertIn("door_connecting", item_ids)

    def test_door_visible_from_second_room(self):
        """Door is visible from room2 (has exit referencing it)."""
        from utilities.utils import gather_location_contents

        contents = gather_location_contents(self.accessor, "loc_room2", "player")
        item_ids = [item.id for item in contents["items"]]
        self.assertIn("door_connecting", item_ids)

    def test_door_not_visible_from_unconnected_room(self):
        """Door not visible from room with no exit to it."""
        from utilities.utils import gather_location_contents

        contents = gather_location_contents(self.accessor, "loc_room3", "player")
        item_ids = [item.id for item in contents["items"]]
        self.assertNotIn("door_connecting", item_ids)

    def test_decorative_door_visible_only_in_its_location(self):
        """Door without exit reference visible only in its location."""
        # Add decorative door directly in room1
        self.state.items.append(Item(
            id="door_decorative",
            name="door",
            description="An ornate door on the wall.",
            location="loc_room1",
            properties={"door": {"open": False}}
        ))

        from utilities.utils import gather_location_contents

        # Visible in room1 where it's located
        contents = gather_location_contents(self.accessor, "loc_room1", "player")
        door_ids = [item.id for item in contents["items"]]
        self.assertIn("door_decorative", door_ids)

        # Not visible in room2 (no exit references it)
        contents = gather_location_contents(self.accessor, "loc_room2", "player")
        door_ids = [item.id for item in contents["items"]]
        self.assertNotIn("door_decorative", door_ids)


class TestFindAccessibleItemWithDoors(unittest.TestCase):
    """Test that find_accessible_item finds door items."""

    def setUp(self):
        """Create state with doors and regular items."""
        from src.state_manager import GameState, Metadata, Actor

        self.state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="loc_room",
                    name="Room",
                    description="A room",
                    exits={
                        "north": ExitDescriptor(type="door", to="loc_other", door_id="door_iron"),
                        "south": ExitDescriptor(type="door", to="loc_other2", door_id="door_wooden")
                    }
                ),
                Location(id="loc_other", name="Other", description="", exits={}),
                Location(id="loc_other2", name="Other2", description="", exits={})
            ],
            items=[
                Item(
                    id="door_iron",
                    name="door",
                    description="A heavy iron door.",
                    location="exit:loc_room:north",
                    properties={"door": {"open": False}}
                ),
                Item(
                    id="door_wooden",
                    name="door",
                    description="A wooden door.",
                    location="exit:loc_room:south",
                    properties={"door": {"open": False}}
                ),
                Item(
                    id="item_key",
                    name="key",
                    description="A small key.",
                    location="loc_room",
                    properties={"portable": True}
                )
            ],
            actors={"player": Actor(
                id="player", name="Player", description="The player",
                location="loc_room", inventory=[]
            )}
        )
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_find_door_by_name(self):
        """find_accessible_item finds door by name 'door'."""
        from utilities.utils import find_accessible_item

        item = find_accessible_item(self.accessor, "door", "player")
        self.assertIsNotNone(item)
        self.assertTrue(item.is_door)

    def test_find_door_with_adjective(self):
        """find_accessible_item finds specific door with adjective."""
        from utilities.utils import find_accessible_item

        item = find_accessible_item(self.accessor, "door", "player", "iron")
        self.assertIsNotNone(item)
        self.assertEqual(item.id, "door_iron")

    def test_find_door_with_different_adjective(self):
        """find_accessible_item finds wooden door with adjective."""
        from utilities.utils import find_accessible_item

        item = find_accessible_item(self.accessor, "door", "player", "wooden")
        self.assertIsNotNone(item)
        self.assertEqual(item.id, "door_wooden")

    def test_find_regular_item_still_works(self):
        """find_accessible_item still finds regular items."""
        from utilities.utils import find_accessible_item

        item = find_accessible_item(self.accessor, "key", "player")
        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_key")


class TestHiddenDoors(unittest.TestCase):
    """Test hidden door (secret passage) support."""

    def setUp(self):
        """Create state with hidden and visible doors."""
        from src.state_manager import GameState, Metadata, Actor

        self.state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="loc_library",
                    name="Library",
                    description="A library",
                    exits={
                        "north": ExitDescriptor(type="door", to="loc_study", door_id="door_visible"),
                        "east": ExitDescriptor(type="door", to="loc_secret", door_id="door_secret")
                    }
                ),
                Location(id="loc_study", name="Study", description="", exits={}),
                Location(id="loc_secret", name="Secret Room", description="", exits={})
            ],
            items=[
                Item(
                    id="door_visible",
                    name="door",
                    description="A normal door.",
                    location="exit:loc_library:north",
                    properties={"door": {"open": False}}
                ),
                Item(
                    id="door_secret",
                    name="door",
                    description="A hidden door behind the bookshelf.",
                    location="exit:loc_library:east",
                    properties={"door": {"open": False}, "hidden": True}
                )
            ],
            actors={"player": Actor(
                id="player", name="Player", description="The player",
                location="loc_library", inventory=[]
            )}
        )
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_hidden_door_not_in_location_contents(self):
        """Hidden door excluded from gather_location_contents."""
        from utilities.utils import gather_location_contents

        contents = gather_location_contents(self.accessor, "loc_library", "player")
        door_ids = [item.id for item in contents["items"]]
        self.assertIn("door_visible", door_ids)
        self.assertNotIn("door_secret", door_ids)

    def test_hidden_door_not_found_by_find_accessible_item(self):
        """Hidden door not found by find_accessible_item."""
        from utilities.utils import find_accessible_item

        # Should find the visible door, not the hidden one
        item = find_accessible_item(self.accessor, "door", "player")
        self.assertEqual(item.id, "door_visible")

    def test_revealed_door_becomes_visible(self):
        """Door becomes visible after hidden=False."""
        from utilities.utils import gather_location_contents

        secret_door = self.accessor.get_item("door_secret")
        secret_door.properties["hidden"] = False

        contents = gather_location_contents(self.accessor, "loc_library", "player")
        door_ids = [item.id for item in contents["items"]]
        self.assertIn("door_secret", door_ids)


class TestOpenCloseDoorItems(unittest.TestCase):
    """Test open/close commands work with door items."""

    def setUp(self):
        """Create state with door item."""
        from src.state_manager import GameState, Metadata, Actor

        self.state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="loc_room",
                    name="Room",
                    description="A room",
                    exits={
                        "north": ExitDescriptor(type="door", to="loc_other", door_id="door_1")
                    }
                ),
                Location(
                    id="loc_other",
                    name="Other Room",
                    description="Another room",
                    exits={
                        "south": ExitDescriptor(type="door", to="loc_room", door_id="door_1")
                    }
                )
            ],
            items=[
                Item(
                    id="door_1",
                    name="door",
                    description="A wooden door.",
                    location="exit:loc_room:north",
                    properties={"door": {"open": False, "locked": False}}
                )
            ],
            actors={"player": Actor(
                id="player", name="Player", description="The player",
                location="loc_room", inventory=[]
            )}
        )
        self.behavior_manager = BehaviorManager()
        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_open_door_item(self):
        """open command works on door items."""
        from behaviors.core.interaction import handle_open

        action = {"verb": "open", "object": "door", "actor_id": "player"}
        result = handle_open(self.accessor, action)

        self.assertTrue(result.success)
        door = self.accessor.get_item("door_1")
        self.assertTrue(door.door_open)

    def test_close_door_item(self):
        """close command works on door items."""
        from behaviors.core.interaction import handle_close

        # First open the door
        door = self.accessor.get_item("door_1")
        door.door_open = True

        action = {"verb": "close", "object": "door", "actor_id": "player"}
        result = handle_close(self.accessor, action)

        self.assertTrue(result.success)
        self.assertFalse(door.door_open)

    def test_open_locked_door_fails(self):
        """Cannot open locked door item."""
        from behaviors.core.interaction import handle_open

        door = self.accessor.get_item("door_1")
        door.door_locked = True

        action = {"verb": "open", "object": "door", "actor_id": "player"}
        result = handle_open(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("locked", result.message.lower())

    def test_open_already_open_door(self):
        """Opening an already open door reports appropriately."""
        from behaviors.core.interaction import handle_open

        door = self.accessor.get_item("door_1")
        door.door_open = True

        action = {"verb": "open", "object": "door", "actor_id": "player"}
        result = handle_open(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("already open", result.message.lower())


class TestLockUnlockDoorItems(unittest.TestCase):
    """Test lock/unlock commands work with door items."""

    def setUp(self):
        """Create state with lockable door."""
        from src.state_manager import GameState, Metadata, Actor, Lock

        self.state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="loc_room",
                    name="Room",
                    description="A room",
                    exits={
                        "north": ExitDescriptor(type="door", to="loc_other", door_id="door_1")
                    }
                ),
                Location(id="loc_other", name="Other", description="", exits={})
            ],
            items=[
                Item(
                    id="door_1",
                    name="door",
                    description="An iron door.",
                    location="exit:loc_room:north",
                    properties={
                        "door": {"open": False, "locked": True, "lock_id": "lock_1"}
                    }
                ),
                Item(
                    id="item_key",
                    name="key",
                    description="An iron key.",
                    location="player",
                    properties={"portable": True}
                )
            ],
            locks=[
                Lock(id="lock_1", properties={"opens_with": ["item_key"]})
            ],
            actors={"player": Actor(
                id="player", name="Player", description="The player",
                location="loc_room", inventory=["item_key"]
            )}
        )
        self.behavior_manager = BehaviorManager()
        import behaviors.core.locks
        self.behavior_manager.load_module(behaviors.core.locks)
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_unlock_door_with_key(self):
        """unlock command works with key in inventory."""
        from behaviors.core.locks import handle_unlock

        action = {"verb": "unlock", "object": "door", "actor_id": "player"}
        result = handle_unlock(self.accessor, action)

        self.assertTrue(result.success)
        door = self.accessor.get_item("door_1")
        self.assertFalse(door.door_locked)

    def test_unlock_door_without_key_fails(self):
        """unlock command fails without correct key."""
        from behaviors.core.locks import handle_unlock

        # Remove key from inventory
        player = self.accessor.get_actor("player")
        player.inventory.remove("item_key")

        action = {"verb": "unlock", "object": "door", "actor_id": "player"}
        result = handle_unlock(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("key", result.message.lower())

    def test_lock_door_with_key(self):
        """lock command works with key."""
        from behaviors.core.locks import handle_lock

        # First unlock the door
        door = self.accessor.get_item("door_1")
        door.door_locked = False

        action = {"verb": "lock", "object": "door", "actor_id": "player"}
        result = handle_lock(self.accessor, action)

        self.assertTrue(result.success)
        self.assertTrue(door.door_locked)

    def test_lock_open_door_fails(self):
        """Cannot lock an open door."""
        from behaviors.core.locks import handle_lock

        door = self.accessor.get_item("door_1")
        door.door_open = True
        door.door_locked = False

        action = {"verb": "lock", "object": "door", "actor_id": "player"}
        result = handle_lock(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("close", result.message.lower())


class TestMovementThroughDoorItems(unittest.TestCase):
    """Test movement through door items."""

    def setUp(self):
        """Create state with door between rooms."""
        from src.state_manager import GameState, Metadata, Actor

        self.state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="loc_room1",
                    name="Room 1",
                    description="First room",
                    exits={
                        "north": ExitDescriptor(type="door", to="loc_room2", door_id="door_1")
                    }
                ),
                Location(
                    id="loc_room2",
                    name="Room 2",
                    description="Second room",
                    exits={
                        "south": ExitDescriptor(type="door", to="loc_room1", door_id="door_1")
                    }
                )
            ],
            items=[
                Item(
                    id="door_1",
                    name="door",
                    description="A heavy door.",
                    location="exit:loc_room1:north",
                    properties={"door": {"open": False, "locked": False}}
                )
            ],
            actors={"player": Actor(
                id="player", name="Player", description="The player",
                location="loc_room1", inventory=[]
            )}
        )
        self.behavior_manager = BehaviorManager()
        import behaviors.core.movement
        self.behavior_manager.load_module(behaviors.core.movement)
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_cannot_go_through_closed_door(self):
        """Movement blocked by closed door."""
        from behaviors.core.movement import handle_go

        action = {"verb": "go", "direction": "north", "actor_id": "player"}
        result = handle_go(self.accessor, action)

        self.assertFalse(result.success)
        # Should mention door is closed
        self.assertTrue("closed" in result.message.lower() or "door" in result.message.lower())

    def test_can_go_through_open_door(self):
        """Movement allowed through open door."""
        from behaviors.core.movement import handle_go

        door = self.accessor.get_item("door_1")
        door.door_open = True

        action = {"verb": "go", "direction": "north", "actor_id": "player"}
        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "loc_room2")


class TestDoorMigration(unittest.TestCase):
    """Test migration of legacy Door objects to Item format."""

    def test_migrate_simple_door(self):
        """Legacy door converts to item with door properties."""
        from src.state_manager import load_game_state

        # Create game data with old-style door
        data = {
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room1",
                    "name": "Room 1",
                    "description": "First room",
                    "exits": {"north": {"type": "door", "to": "loc_room2", "door_id": "door_1"}}
                },
                {
                    "id": "loc_room2",
                    "name": "Room 2",
                    "description": "Second room",
                    "exits": {"south": {"type": "door", "to": "loc_room1", "door_id": "door_1"}}
                }
            ],
            "doors": [
                {
                    "id": "door_1",
                    "locations": ["loc_room1", "loc_room2"],
                    "description": "A wooden door",
                    "open": False,
                    "locked": True,
                    "lock_id": "lock_1"
                }
            ],
            "items": [
                {"id": "item_key", "name": "key", "description": "A key", "location": "loc_room1"}
            ],
            "locks": [
                {"id": "lock_1", "opens_with": ["item_key"]}
            ],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "Player",
                    "description": "The player",
                    "location": "loc_room1",
                    "inventory": []
                }
            }
        }

        state = load_game_state(data)

        # Door should be migrated to items list
        door_items = [i for i in state.items if i.is_door]
        self.assertEqual(len(door_items), 1)

        door_item = door_items[0]
        self.assertEqual(door_item.id, "door_1")
        self.assertEqual(door_item.name, "door")
        self.assertEqual(door_item.description, "A wooden door")
        self.assertFalse(door_item.door_open)
        self.assertTrue(door_item.door_locked)
        self.assertEqual(door_item.door_lock_id, "lock_1")

        # Location should be exit:loc_room1:north (first location with exit to door)
        self.assertTrue(door_item.location.startswith("exit:"))

        # Old doors list should be empty after migration
        self.assertEqual(len(state.doors), 0)

    def test_migrate_door_preserves_behaviors(self):
        """Door behaviors are preserved during migration."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room",
                    "name": "Room",
                    "description": "A room",
                    "exits": {"east": {"type": "door", "to": "loc_other", "door_id": "door_1"}}
                },
                {"id": "loc_other", "name": "Other", "description": "", "exits": {}}
            ],
            "doors": [
                {
                    "id": "door_1",
                    "locations": ["loc_room"],
                    "description": "A magic door",
                    "behaviors": ["game.doors:on_open_magic"]
                }
            ],
            "actors": {
                "player": {"id": "player", "name": "Player", "description": "", "location": "loc_room", "inventory": []}
            }
        }

        state = load_game_state(data)

        door_items = [i for i in state.items if i.is_door]
        self.assertEqual(len(door_items), 1)
        self.assertEqual(door_items[0].behaviors, ["game.doors:on_open_magic"])

    def test_saved_state_has_no_old_doors(self):
        """Saving migrated state produces no doors list."""
        from src.state_manager import load_game_state, game_state_to_dict

        data = {
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room",
                    "name": "Room",
                    "description": "A room",
                    "exits": {"north": {"type": "door", "to": "loc_other", "door_id": "door_1"}}
                },
                {"id": "loc_other", "name": "Other", "description": "", "exits": {}}
            ],
            "doors": [
                {"id": "door_1", "locations": ["loc_room"], "description": "A door"}
            ],
            "actors": {
                "player": {"id": "player", "name": "Player", "description": "", "location": "loc_room", "inventory": []}
            }
        }

        state = load_game_state(data)
        saved_data = game_state_to_dict(state)

        # No doors in saved output
        self.assertEqual(len(saved_data.get("doors", [])), 0)

        # Door is in items
        door_items = [i for i in saved_data["items"] if "door" in i.get("properties", {}) or i.get("door")]
        self.assertEqual(len(door_items), 1)

    def test_reload_migrated_state_works(self):
        """Migrated state can be saved and reloaded."""
        from src.state_manager import load_game_state, game_state_to_dict

        # Original data with old-style door
        original_data = {
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room",
                    "name": "Room",
                    "description": "A room",
                    "exits": {"north": {"type": "door", "to": "loc_other", "door_id": "door_1"}}
                },
                {"id": "loc_other", "name": "Other", "description": "", "exits": {}}
            ],
            "doors": [
                {"id": "door_1", "locations": ["loc_room"], "description": "A door", "open": False}
            ],
            "actors": {
                "player": {"id": "player", "name": "Player", "description": "", "location": "loc_room", "inventory": []}
            }
        }

        # Load, save, reload
        state1 = load_game_state(original_data)
        saved_data = game_state_to_dict(state1)
        state2 = load_game_state(saved_data)

        # Door item should exist in reloaded state
        door_items = [i for i in state2.items if i.is_door]
        self.assertEqual(len(door_items), 1)
        self.assertEqual(door_items[0].id, "door_1")

    def test_no_migration_when_no_doors(self):
        """States without doors don't create spurious items."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test"},
            "locations": [
                {"id": "loc_room", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "item_sword", "name": "sword", "description": "A sword", "location": "loc_room"}
            ],
            "actors": {
                "player": {"id": "player", "name": "Player", "description": "", "location": "loc_room", "inventory": []}
            }
        }

        state = load_game_state(data)

        # Should only have the sword
        self.assertEqual(len(state.items), 1)
        self.assertEqual(state.items[0].id, "item_sword")

    def test_existing_door_items_not_duplicated(self):
        """If item already exists with door properties, don't duplicate."""
        from src.state_manager import load_game_state

        # Data that already has door as item (new format)
        data = {
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room",
                    "name": "Room",
                    "description": "A room",
                    "exits": {"north": {"type": "door", "to": "loc_other", "door_id": "door_1"}}
                },
                {"id": "loc_other", "name": "Other", "description": "", "exits": {}}
            ],
            "items": [
                {
                    "id": "door_1",
                    "name": "door",
                    "description": "A door",
                    "location": "exit:loc_room:north",
                    "door": {"open": False}
                }
            ],
            "actors": {
                "player": {"id": "player", "name": "Player", "description": "", "location": "loc_room", "inventory": []}
            }
        }

        state = load_game_state(data)

        # Should still only have one door item
        door_items = [i for i in state.items if i.is_door]
        self.assertEqual(len(door_items), 1)


if __name__ == "__main__":
    unittest.main()
