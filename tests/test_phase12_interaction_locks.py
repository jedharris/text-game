"""
Phase 12: Interaction and Lock Handlers

Tests for handle_open, handle_close, handle_lock, and handle_unlock.
Critical: Each handler must have NPC tests to validate actor_id threading.
"""
from src.types import ActorId

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Any, Dict, Optional

from src.state_accessor import StateAccessor, HandlerResult
from src.behavior_manager import BehaviorManager
from src.state_manager import Actor, Lock, Item, Location, ExitDescriptor
from src.types import ItemId
from tests.conftest import create_test_state, make_action


def create_door_item(door_id: str, location_id: str, direction: str,
                     open: bool = False, locked: bool = False, lock_id: Optional[str] = None,
                     description: str = "A door") -> Item:
    """Helper to create a door item in the new unified format."""
    door_props: Dict[str, Any] = {"open": open, "locked": locked}
    if lock_id:
        door_props["lock_id"] = lock_id
    return Item(
        id=ItemId(door_id),
        name="door",
        description=description,
        location=f"exit:{location_id}:{direction}",
        _properties={"door": door_props}
    )


class TestPhase12InteractionLocks(unittest.TestCase):
    """Tests for interaction and lock handlers."""

    # ========== INTERACTION TESTS (OPEN/CLOSE) ==========

    def test_handle_open_container(self):
        """Test opening a container item."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.interaction
        behavior_manager.load_module(behaviors.core.interaction)
        accessor = StateAccessor(state, behavior_manager)

        # Create a closed container
        chest = Item(
            id="item_chest",
            name="chest",
            description="A wooden chest",
            location="location_room",
            _properties={"container": {"open": False, "capacity": 10}}
        )
        state.items.append(chest)

        from behaviors.core.interaction import handle_open
        action = make_action(object="chest", actor_id="player")
        result = handle_open(accessor, action)

        self.assertTrue(result.success)
        self.assertTrue(chest.container.open)

    def test_handle_open_door(self):
        """Test opening a door."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.interaction
        behavior_manager.load_module(behaviors.core.interaction)
        accessor = StateAccessor(state, behavior_manager)

        # Add a second room with exit back
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)

        # Add exit to existing room
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="location_hall", door_id="door_main")

        # Create a door item
        door = create_door_item("door_main", "location_room", "north",
                                open=False, description="A wooden door")
        state.items.append(door)

        from behaviors.core.interaction import handle_open
        action = make_action(object="door", actor_id="player")
        result = handle_open(accessor, action)

        self.assertTrue(result.success)
        self.assertTrue(door.door_open)

    def test_handle_open_already_open(self):
        """Test that opening an already open container reports appropriately."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.interaction
        behavior_manager.load_module(behaviors.core.interaction)
        accessor = StateAccessor(state, behavior_manager)

        # Create an already open container
        chest = Item(
            id="item_chest",
            name="chest",
            description="A wooden chest",
            location="location_room",
            _properties={"container": {"open": True, "capacity": 10}}
        )
        state.items.append(chest)

        from behaviors.core.interaction import handle_open
        action = make_action(object="chest", actor_id="player")
        result = handle_open(accessor, action)

        self.assertTrue(result.success)
        self.assertIn("already open", result.primary.lower())

    def test_handle_open_npc(self):
        """Test NPC opening something (critical for actor_id threading)."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.interaction
        behavior_manager.load_module(behaviors.core.interaction)
        accessor = StateAccessor(state, behavior_manager)

        # Create a closed container
        chest = Item(
            id="item_chest",
            name="chest",
            description="A wooden chest",
            location="location_room",
            _properties={"container": {"open": False, "capacity": 10}}
        )
        state.items.append(chest)

        # Add NPC
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=[]
        )
        state.actors[ActorId("npc_guard")] = guard

        from behaviors.core.interaction import handle_open
        action = make_action(object="chest", actor_id="npc_guard")
        result = handle_open(accessor, action)

        self.assertTrue(result.success, f"NPC open failed: {result.primary}")
        self.assertTrue(chest.container.open)

    def test_handle_close_container(self):
        """Test closing a container item."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.interaction
        behavior_manager.load_module(behaviors.core.interaction)
        accessor = StateAccessor(state, behavior_manager)

        # Create an open container
        chest = Item(
            id="item_chest",
            name="chest",
            description="A wooden chest",
            location="location_room",
            _properties={"container": {"open": True, "capacity": 10}}
        )
        state.items.append(chest)

        from behaviors.core.interaction import handle_close
        action = make_action(object="chest", actor_id="player")
        result = handle_close(accessor, action)

        self.assertTrue(result.success)
        self.assertFalse(chest.container.open)

    def test_handle_close_door(self):
        """Test closing a door."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.interaction
        behavior_manager.load_module(behaviors.core.interaction)
        accessor = StateAccessor(state, behavior_manager)

        # Add a second room with exit back
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)

        # Add exit to existing room
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="location_hall", door_id="door_main")

        # Create an open door item
        door = create_door_item("door_main", "location_room", "north",
                                open=True, description="A wooden door")
        state.items.append(door)

        from behaviors.core.interaction import handle_close
        action = make_action(object="door", actor_id="player")
        result = handle_close(accessor, action)

        self.assertTrue(result.success)
        self.assertFalse(door.door_open)

    def test_handle_close_npc(self):
        """Test NPC closing something (critical for actor_id threading)."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.interaction
        behavior_manager.load_module(behaviors.core.interaction)
        accessor = StateAccessor(state, behavior_manager)

        # Create an open container
        chest = Item(
            id="item_chest",
            name="chest",
            description="A wooden chest",
            location="location_room",
            _properties={"container": {"open": True, "capacity": 10}}
        )
        state.items.append(chest)

        # Add NPC
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=[]
        )
        state.actors[ActorId("npc_guard")] = guard

        from behaviors.core.interaction import handle_close
        action = make_action(object="chest", actor_id="npc_guard")
        result = handle_close(accessor, action)

        self.assertTrue(result.success, f"NPC close failed: {result.primary}")
        self.assertFalse(chest.container.open)

    # ========== LOCK TESTS ==========

    def test_handle_unlock_with_key(self):
        """Test unlocking with correct key."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.locks
        behavior_manager.load_module(behaviors.core.locks)
        accessor = StateAccessor(state, behavior_manager)

        # Add a second room with exit back
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)

        # Add exit to existing room
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="location_hall", door_id="door_main")

        # Create a lock
        lock = Lock(
            id="lock_door",
            name="Door Lock",
            description="A sturdy lock.",
            _properties={"opens_with": ["item_key"]}
        )
        state.locks.append(lock)

        # Create a locked door item
        door = create_door_item("door_main", "location_room", "north",
                                open=False, locked=True, lock_id="lock_door",
                                description="A locked door")
        state.items.append(door)

        # Create key and give to player
        key = Item(
            id="item_key",
            name="key",
            description="A brass key",
            location="player",
            _properties={"portable": True}
        )
        state.items.append(key)
        player = state.get_actor(ActorId("player"))
        player.inventory.append("item_key")

        from behaviors.core.locks import handle_unlock
        action = make_action(object="door", actor_id="player")
        result = handle_unlock(accessor, action)

        self.assertTrue(result.success)
        self.assertFalse(door.door_locked)

    def test_handle_unlock_without_key(self):
        """Test that unlocking fails without key."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.locks
        behavior_manager.load_module(behaviors.core.locks)
        accessor = StateAccessor(state, behavior_manager)

        # Add a second room with exit back
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)

        # Add exit to existing room
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="location_hall", door_id="door_main")

        # Create a lock
        lock = Lock(
            id="lock_door",
            name="Door Lock",
            description="A sturdy lock.",
            _properties={"opens_with": ["item_key"]}
        )
        state.locks.append(lock)

        # Create a locked door item (no key in player inventory)
        door = create_door_item("door_main", "location_room", "north",
                                open=False, locked=True, lock_id="lock_door",
                                description="A locked door")
        state.items.append(door)

        from behaviors.core.locks import handle_unlock
        action = make_action(object="door", actor_id="player")
        result = handle_unlock(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("key", result.primary.lower())

    def test_handle_unlock_npc(self):
        """Test NPC unlocking with their key (critical for actor_id threading)."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.locks
        behavior_manager.load_module(behaviors.core.locks)
        accessor = StateAccessor(state, behavior_manager)

        # Add a second room with exit back
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)

        # Add exit to existing room
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="location_hall", door_id="door_main")

        # Create a lock
        lock = Lock(
            id="lock_door",
            name="Door Lock",
            description="A sturdy lock.",
            _properties={"opens_with": ["item_key"]}
        )
        state.locks.append(lock)

        # Create a locked door item
        door = create_door_item("door_main", "location_room", "north",
                                open=False, locked=True, lock_id="lock_door",
                                description="A locked door")
        state.items.append(door)

        # Create key and give to NPC (not player)
        key = Item(
            id="item_key",
            name="key",
            description="A brass key",
            location="npc_guard",
            _properties={"portable": True}
        )
        state.items.append(key)

        # Add NPC with key
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=["item_key"]
        )
        state.actors[ActorId("npc_guard")] = guard

        from behaviors.core.locks import handle_unlock
        action = make_action(object="door", actor_id="npc_guard")
        result = handle_unlock(accessor, action)

        self.assertTrue(result.success, f"NPC unlock failed: {result.primary}")
        self.assertFalse(door.door_locked)

    def test_handle_lock_with_key(self):
        """Test locking with correct key."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.locks
        behavior_manager.load_module(behaviors.core.locks)
        accessor = StateAccessor(state, behavior_manager)

        # Add a second room with exit back
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)

        # Add exit to existing room
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="location_hall", door_id="door_main")

        # Create a lock
        lock = Lock(
            id="lock_door",
            name="Door Lock",
            description="A sturdy lock.",
            _properties={"opens_with": ["item_key"]}
        )
        state.locks.append(lock)

        # Create an unlocked door item
        door = create_door_item("door_main", "location_room", "north",
                                open=False, locked=False, lock_id="lock_door",
                                description="A door")
        state.items.append(door)

        # Create key and give to player
        key = Item(
            id="item_key",
            name="key",
            description="A brass key",
            location="player",
            _properties={"portable": True}
        )
        state.items.append(key)
        player = state.get_actor(ActorId("player"))
        player.inventory.append("item_key")

        from behaviors.core.locks import handle_lock
        action = make_action(object="door", actor_id="player")
        result = handle_lock(accessor, action)

        self.assertTrue(result.success)
        self.assertTrue(door.door_locked)

    def test_handle_lock_door_open(self):
        """Test that locking fails if door is open."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.locks
        behavior_manager.load_module(behaviors.core.locks)
        accessor = StateAccessor(state, behavior_manager)

        # Add a second room with exit back
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)

        # Add exit to existing room
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="location_hall", door_id="door_main")

        # Create a lock
        lock = Lock(
            id="lock_door",
            name="Door Lock",
            description="A sturdy lock.",
            _properties={"opens_with": ["item_key"]}
        )
        state.locks.append(lock)

        # Create an open door item
        door = create_door_item("door_main", "location_room", "north",
                                open=True, locked=False, lock_id="lock_door",
                                description="A door")
        state.items.append(door)

        # Create key and give to player
        key = Item(
            id="item_key",
            name="key",
            description="A brass key",
            location="player",
            _properties={"portable": True}
        )
        state.items.append(key)
        player = state.get_actor(ActorId("player"))
        player.inventory.append("item_key")

        from behaviors.core.locks import handle_lock
        action = make_action(object="door", actor_id="player")
        result = handle_lock(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("close", result.primary.lower())

    def test_handle_lock_npc(self):
        """Test NPC locking with their key (critical for actor_id threading)."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.locks
        behavior_manager.load_module(behaviors.core.locks)
        accessor = StateAccessor(state, behavior_manager)

        # Add a second room with exit back
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)

        # Add exit to existing room
        room = accessor.get_location("location_room")
        room.exits["north"] = ExitDescriptor(type="door", to="location_hall", door_id="door_main")

        # Create a lock
        lock = Lock(
            id="lock_door",
            name="Door Lock",
            description="A sturdy lock.",
            _properties={"opens_with": ["item_key"]}
        )
        state.locks.append(lock)

        # Create an unlocked door item
        door = create_door_item("door_main", "location_room", "north",
                                open=False, locked=False, lock_id="lock_door",
                                description="A door")
        state.items.append(door)

        # Create key and give to NPC (not player)
        key = Item(
            id="item_key",
            name="key",
            description="A brass key",
            location="npc_guard",
            _properties={"portable": True}
        )
        state.items.append(key)

        # Add NPC with key
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=["item_key"]
        )
        state.actors[ActorId("npc_guard")] = guard

        from behaviors.core.locks import handle_lock
        action = make_action(object="door", actor_id="npc_guard")
        result = handle_lock(accessor, action)

        self.assertTrue(result.success, f"NPC lock failed: {result.primary}")
        self.assertTrue(door.door_locked)


class TestWordEntryHandling(unittest.TestCase):
    """Tests that handlers correctly handle WordEntry objects as object names.

    Issue #47: Handlers were calling .lower() directly on object_name without
    checking if it was a WordEntry object first.
    """

    def test_handle_open_with_word_entry(self):
        """Test handle_open works when object is a WordEntry."""
        from src.parser import WordEntry, WordType

        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.interaction
        behavior_manager.load_module(behaviors.core.interaction)
        accessor = StateAccessor(state, behavior_manager)

        # Create a container (umbrella that can be opened)
        umbrella = Item(
            id="item_umbrella",
            name="umbrella",
            description="A dusty umbrella",
            location="location_room",
            _properties={"container": {"open": False, "capacity": 1}}
        )
        state.items.append(umbrella)

        # Parser produces WordEntry for "umbrella"
        umbrella_entry = WordEntry(
            word="umbrella",
            word_type=WordType.NOUN,
            synonyms=["parasol", "brolly"]
        )

        from behaviors.core.interaction import handle_open
        action = {"actor_id": "player", "object": umbrella_entry}
        result = handle_open(accessor, action)

        self.assertTrue(result.success, f"Failed: {result.primary}")
        self.assertTrue(umbrella.container.open)

    def test_handle_close_with_word_entry(self):
        """Test handle_close works when object is a WordEntry."""
        from src.parser import WordEntry, WordType

        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.interaction
        behavior_manager.load_module(behaviors.core.interaction)
        accessor = StateAccessor(state, behavior_manager)

        # Create an open container
        umbrella = Item(
            id="item_umbrella",
            name="umbrella",
            description="A dusty umbrella",
            location="location_room",
            _properties={"container": {"open": True, "capacity": 1}}
        )
        state.items.append(umbrella)

        umbrella_entry = WordEntry(
            word="umbrella",
            word_type=WordType.NOUN,
            synonyms=["parasol", "brolly"]
        )

        from behaviors.core.interaction import handle_close
        action = {"actor_id": "player", "object": umbrella_entry}
        result = handle_close(accessor, action)

        self.assertTrue(result.success, f"Failed: {result.primary}")
        self.assertFalse(umbrella.container.open)

    def test_handle_lock_with_word_entry(self):
        """Test handle_lock works when object is a WordEntry."""
        from src.parser import WordEntry, WordType

        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.locks
        behavior_manager.load_module(behaviors.core.locks)
        accessor = StateAccessor(state, behavior_manager)

        # Add a second room
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)

        # Update room to have exit north
        state.locations[0].exits["north"] = ExitDescriptor(
            type="door", to="location_hall", door_id="door_main"
        )

        # Create a closed, unlocked door with a lock
        door = create_door_item("door_main", "location_room", "north",
                                open=False, locked=False, lock_id="lock_main")
        state.items.append(door)

        # Add lock and key
        state.locks = [Lock(id="lock_main", name="Main Lock", description="Lock",
                           _properties={"opens_with": ["item_key"]})]
        key = Item(id="item_key", name="key", description="A key",
                   location="player", _properties={"portable": True})
        state.items.append(key)
        # Add key to player's inventory
        state.get_actor(ActorId("player")).inventory.append("item_key")

        door_entry = WordEntry(
            word="door",
            word_type=WordType.NOUN,
            synonyms=["gate", "entrance"]
        )

        from behaviors.core.locks import handle_lock
        action = {"actor_id": "player", "object": door_entry}
        result = handle_lock(accessor, action)

        self.assertTrue(result.success, f"Failed: {result.primary}")
        self.assertTrue(door.door_locked)

    def test_handle_unlock_with_word_entry(self):
        """Test handle_unlock works when object is a WordEntry."""
        from src.parser import WordEntry, WordType

        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.locks
        behavior_manager.load_module(behaviors.core.locks)
        accessor = StateAccessor(state, behavior_manager)

        # Add a second room
        hall = Location(
            id="location_hall",
            name="Hall",
            description="A hallway",
            exits={"south": ExitDescriptor(type="door", to="location_room", door_id="door_main")}
        )
        state.locations.append(hall)

        # Update room to have exit north
        state.locations[0].exits["north"] = ExitDescriptor(
            type="door", to="location_hall", door_id="door_main"
        )

        # Create a closed, locked door with a lock
        door = create_door_item("door_main", "location_room", "north",
                                open=False, locked=True, lock_id="lock_main")
        state.items.append(door)

        # Add lock and key
        state.locks = [Lock(id="lock_main", name="Main Lock", description="Lock",
                           _properties={"opens_with": ["item_key"]})]
        key = Item(id="item_key", name="key", description="A key",
                   location="player", _properties={"portable": True})
        state.items.append(key)
        # Add key to player's inventory
        state.get_actor(ActorId("player")).inventory.append("item_key")

        door_entry = WordEntry(
            word="door",
            word_type=WordType.NOUN,
            synonyms=["gate", "entrance"]
        )

        from behaviors.core.locks import handle_unlock
        action = {"actor_id": "player", "object": door_entry}
        result = handle_unlock(accessor, action)

        self.assertTrue(result.success, f"Failed: {result.primary}")
        self.assertFalse(door.door_locked)


if __name__ == '__main__':
    unittest.main()
