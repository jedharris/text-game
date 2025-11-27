"""
Phase 12: Interaction and Lock Handlers

Tests for handle_open, handle_close, handle_lock, and handle_unlock.
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
from src.state_manager import Actor, Lock, Item, Location, ExitDescriptor
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
            properties={"container": {"open": False, "capacity": 10}}
        )
        state.items.append(chest)

        from behaviors.core.interaction import handle_open
        action = {"actor_id": "player", "object": "chest"}
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
        action = {"actor_id": "player", "object": "door"}
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
            properties={"container": {"open": True, "capacity": 10}}
        )
        state.items.append(chest)

        from behaviors.core.interaction import handle_open
        action = {"actor_id": "player", "object": "chest"}
        result = handle_open(accessor, action)

        self.assertTrue(result.success)
        self.assertIn("already open", result.message.lower())

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
            properties={"container": {"open": False, "capacity": 10}}
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
        state.actors["npc_guard"] = guard

        from behaviors.core.interaction import handle_open
        action = {"actor_id": "npc_guard", "object": "chest"}
        result = handle_open(accessor, action)

        self.assertTrue(result.success, f"NPC open failed: {result.message}")
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
            properties={"container": {"open": True, "capacity": 10}}
        )
        state.items.append(chest)

        from behaviors.core.interaction import handle_close
        action = {"actor_id": "player", "object": "chest"}
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
        action = {"actor_id": "player", "object": "door"}
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
            properties={"container": {"open": True, "capacity": 10}}
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
        state.actors["npc_guard"] = guard

        from behaviors.core.interaction import handle_close
        action = {"actor_id": "npc_guard", "object": "chest"}
        result = handle_close(accessor, action)

        self.assertTrue(result.success, f"NPC close failed: {result.message}")
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
            properties={"opens_with": ["item_key"]}
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
            properties={"portable": True}
        )
        state.items.append(key)
        player = state.actors["player"]
        player.inventory.append("item_key")

        from behaviors.core.locks import handle_unlock
        action = {"actor_id": "player", "object": "door"}
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
            properties={"opens_with": ["item_key"]}
        )
        state.locks.append(lock)

        # Create a locked door item (no key in player inventory)
        door = create_door_item("door_main", "location_room", "north",
                                open=False, locked=True, lock_id="lock_door",
                                description="A locked door")
        state.items.append(door)

        from behaviors.core.locks import handle_unlock
        action = {"actor_id": "player", "object": "door"}
        result = handle_unlock(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("key", result.message.lower())

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
            properties={"opens_with": ["item_key"]}
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
            properties={"portable": True}
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
        state.actors["npc_guard"] = guard

        from behaviors.core.locks import handle_unlock
        action = {"actor_id": "npc_guard", "object": "door"}
        result = handle_unlock(accessor, action)

        self.assertTrue(result.success, f"NPC unlock failed: {result.message}")
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
            properties={"opens_with": ["item_key"]}
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
            properties={"portable": True}
        )
        state.items.append(key)
        player = state.actors["player"]
        player.inventory.append("item_key")

        from behaviors.core.locks import handle_lock
        action = {"actor_id": "player", "object": "door"}
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
            properties={"opens_with": ["item_key"]}
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
            properties={"portable": True}
        )
        state.items.append(key)
        player = state.actors["player"]
        player.inventory.append("item_key")

        from behaviors.core.locks import handle_lock
        action = {"actor_id": "player", "object": "door"}
        result = handle_lock(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("close", result.message.lower())

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
            properties={"opens_with": ["item_key"]}
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
            properties={"portable": True}
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
        state.actors["npc_guard"] = guard

        from behaviors.core.locks import handle_lock
        action = {"actor_id": "npc_guard", "object": "door"}
        result = handle_lock(accessor, action)

        self.assertTrue(result.success, f"NPC lock failed: {result.message}")
        self.assertTrue(door.door_locked)


if __name__ == '__main__':
    unittest.main()
