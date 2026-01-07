"""Tests for passage visibility behind closed doors.

Tests that passages (exits with both passage and door_id fields) are properly
hidden when viewed from the door_at location when the door is closed, but
remain visible from the opposite end.
"""
import unittest
from src.state_manager import (
    GameState, Metadata, Location, Item, Exit, load_game_state
)
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.types import LocationId, ItemId, ActorId


class TestPassageVisibilityFromDoorLocation(unittest.TestCase):
    """Tests for passage visibility from door_at location."""

    def setUp(self):
        """Create a test game with door and passage."""
        self.game_data = {
            "metadata": {
                "title": "Test",
                "version": "1.0",
                "start_location": "loc_library"
            },
            "locations": [
                {
                    "id": "loc_library",
                    "name": "Library",
                    "description": "A library",
                    "items": [],
                    "exits": {}
                },
                {
                    "id": "loc_sanctum",
                    "name": "Sanctum",
                    "description": "A sanctum",
                    "items": [],
                    "exits": {}
                }
            ],
            "exits": [
                {
                    "id": "exit_library_up",
                    "name": "ornate door",
                    "location": "loc_library",
                    "connections": ["exit_sanctum_down"],
                    "direction": "up",
                    "door_id": "door_test",
                    "passage": "narrow stone stairs",
                    "door_at": "loc_library"
                },
                {
                    "id": "exit_sanctum_down",
                    "name": "stairs",
                    "location": "loc_sanctum",
                    "connections": ["exit_library_up"],
                    "direction": "down",
                    "door_id": "door_test",
                    "passage": "narrow stone stairs",
                    "door_at": "loc_library"
                }
            ],
            "items": [
                {
                    "id": "door_test",
                    "name": "door",
                    "description": "A door",
                    "location": "exit:loc_library:up",
                    "door": {
                        "open": False,
                        "locked": False
                    },
                    "properties": {}
                }
            ],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "you",
                    "description": "You",
                    "location": "loc_library",
                    "inventory": [],
                    "properties": {}
                }
            }
        }

    def test_passage_hidden_from_door_location_when_closed(self):
        """Exit with passage is hidden from door_at location when door is closed."""
        state = load_game_state(self.game_data)
        accessor = StateAccessor(state, BehaviorManager())

        # From library (door_at location), door is closed
        visible = accessor.get_visible_exits(LocationId("loc_library"), ActorId("player"))

        # Passage should NOT be visible
        self.assertNotIn("up", visible)

    def test_passage_visible_from_door_location_when_open(self):
        """Exit with passage is visible from door_at location when door is open."""
        state = load_game_state(self.game_data)
        # Open the door
        door = state.get_item(ItemId("door_test"))
        door.properties["door"]["open"] = True

        accessor = StateAccessor(state, BehaviorManager())

        # From library (door_at location), door is open
        visible = accessor.get_visible_exits(LocationId("loc_library"), ActorId("player"))

        # Passage SHOULD be visible
        self.assertIn("up", visible)
        self.assertEqual(visible["up"].id, "exit_library_up")


class TestPassageVisibilityFromOppositeLocation(unittest.TestCase):
    """Tests for passage visibility from non-door_at location."""

    def setUp(self):
        """Create a test game with door and passage."""
        self.game_data = {
            "metadata": {
                "title": "Test",
                "version": "1.0",
                "start_location": "loc_sanctum"
            },
            "locations": [
                {
                    "id": "loc_library",
                    "name": "Library",
                    "description": "A library",
                    "items": [],
                    "exits": {}
                },
                {
                    "id": "loc_sanctum",
                    "name": "Sanctum",
                    "description": "A sanctum",
                    "items": [],
                    "exits": {}
                }
            ],
            "exits": [
                {
                    "id": "exit_library_up",
                    "name": "ornate door",
                    "location": "loc_library",
                    "connections": ["exit_sanctum_down"],
                    "direction": "up",
                    "door_id": "door_test",
                    "passage": "narrow stone stairs",
                    "door_at": "loc_library"
                },
                {
                    "id": "exit_sanctum_down",
                    "name": "stairs",
                    "location": "loc_sanctum",
                    "connections": ["exit_library_up"],
                    "direction": "down",
                    "door_id": "door_test",
                    "passage": "narrow stone stairs",
                    "door_at": "loc_library"
                }
            ],
            "items": [
                {
                    "id": "door_test",
                    "name": "door",
                    "description": "A door",
                    "location": "exit:loc_library:up",
                    "door": {
                        "open": False,
                        "locked": False
                    },
                    "properties": {}
                }
            ],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "you",
                    "description": "You",
                    "location": "loc_sanctum",
                    "inventory": [],
                    "properties": {}
                }
            }
        }

    def test_passage_always_visible_from_opposite_location_door_closed(self):
        """Exit with passage is always visible from non-door_at location, even when door closed."""
        state = load_game_state(self.game_data)
        accessor = StateAccessor(state, BehaviorManager())

        # From sanctum (NOT door_at location), door is closed
        visible = accessor.get_visible_exits(LocationId("loc_sanctum"), ActorId("player"))

        # Passage SHOULD still be visible (stairs don't disappear)
        self.assertIn("down", visible)
        self.assertEqual(visible["down"].id, "exit_sanctum_down")

    def test_passage_always_visible_from_opposite_location_door_open(self):
        """Exit with passage is visible from non-door_at location when door open."""
        state = load_game_state(self.game_data)
        # Open the door
        door = state.get_item(ItemId("door_test"))
        door.properties["door"]["open"] = True

        accessor = StateAccessor(state, BehaviorManager())

        # From sanctum (NOT door_at location), door is open
        visible = accessor.get_visible_exits(LocationId("loc_sanctum"), ActorId("player"))

        # Passage SHOULD be visible
        self.assertIn("down", visible)
        self.assertEqual(visible["down"].id, "exit_sanctum_down")


class TestNonPassageExits(unittest.TestCase):
    """Tests for exits without passage field."""

    def setUp(self):
        """Create test game with simple door (no passage)."""
        self.game_data = {
            "metadata": {
                "title": "Test",
                "version": "1.0",
                "start_location": "loc_entrance"
            },
            "locations": [
                {
                    "id": "loc_entrance",
                    "name": "Entrance",
                    "description": "An entrance",
                    "items": [],
                    "exits": {}
                },
                {
                    "id": "loc_storage",
                    "name": "Storage",
                    "description": "A storage room",
                    "items": [],
                    "exits": {}
                }
            ],
            "exits": [
                {
                    "id": "exit_entrance_east",
                    "name": "wooden door",
                    "location": "loc_entrance",
                    "connections": ["exit_storage_west"],
                    "direction": "east",
                    "door_id": "door_simple"
                    # No passage field
                },
                {
                    "id": "exit_storage_west",
                    "name": "wooden door",
                    "location": "loc_storage",
                    "connections": ["exit_entrance_east"],
                    "direction": "west",
                    "door_id": "door_simple"
                }
            ],
            "items": [
                {
                    "id": "door_simple",
                    "name": "door",
                    "description": "A simple door",
                    "location": "exit:loc_entrance:east",
                    "door": {
                        "open": False,
                        "locked": False
                    },
                    "properties": {}
                }
            ],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "you",
                    "description": "You",
                    "location": "loc_entrance",
                    "inventory": [],
                    "properties": {}
                }
            }
        }

    def test_exit_without_passage_always_visible(self):
        """Exit with door_id but no passage is always visible (it's just a door)."""
        state = load_game_state(self.game_data)
        accessor = StateAccessor(state, BehaviorManager())

        # Door is closed
        visible = accessor.get_visible_exits(LocationId("loc_entrance"), ActorId("player"))

        # Exit SHOULD be visible (it's the door itself, not a passage beyond)
        self.assertIn("east", visible)
        self.assertEqual(visible["east"].id, "exit_entrance_east")

    def test_passage_without_door_always_visible(self):
        """Exit with passage but no door_id is always visible (open passage)."""
        # Modify game to have passage without door
        self.game_data["exits"][0] = {
            "id": "exit_entrance_up",
            "name": "stone stairs",
            "location": "loc_entrance",
            "connections": ["exit_storage_west"],
            "direction": "up",
            "passage": "stone stairs"
            # No door_id
        }
        # Update return exit to match
        self.game_data["exits"][1]["connections"] = ["exit_entrance_up"]

        state = load_game_state(self.game_data)
        accessor = StateAccessor(state, BehaviorManager())

        visible = accessor.get_visible_exits(LocationId("loc_entrance"), ActorId("player"))

        # Passage SHOULD be visible (no door to block it)
        self.assertIn("up", visible)


class TestMovementThroughPassages(unittest.TestCase):
    """Tests that movement respects door state."""

    def setUp(self):
        """Create test game for movement tests."""
        self.game_data = {
            "metadata": {
                "title": "Test",
                "version": "1.0",
                "start_location": "loc_library"
            },
            "locations": [
                {
                    "id": "loc_library",
                    "name": "Library",
                    "description": "A library",
                    "items": [],
                    "exits": {}
                },
                {
                    "id": "loc_sanctum",
                    "name": "Sanctum",
                    "description": "A sanctum",
                    "items": [],
                    "exits": {}
                }
            ],
            "exits": [
                {
                    "id": "exit_library_up",
                    "name": "ornate door",
                    "location": "loc_library",
                    "connections": ["exit_sanctum_down"],
                    "direction": "up",
                    "door_id": "door_test",
                    "passage": "narrow stone stairs",
                    "door_at": "loc_library"
                },
                {
                    "id": "exit_sanctum_down",
                    "name": "stairs",
                    "location": "loc_sanctum",
                    "connections": ["exit_library_up"],
                    "direction": "down",
                    "door_id": "door_test",
                    "passage": "narrow stone stairs",
                    "door_at": "loc_library"
                }
            ],
            "items": [
                {
                    "id": "door_test",
                    "name": "door",
                    "description": "A door",
                    "location": "exit:loc_library:up",
                    "door": {
                        "open": False,
                        "locked": False
                    },
                    "properties": {}
                }
            ],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "you",
                    "description": "You",
                    "location": "loc_library",
                    "inventory": [],
                    "properties": {}
                }
            }
        }

    def test_cannot_see_passage_when_door_closed(self):
        """Passage not in visible exits when door is closed."""
        state = load_game_state(self.game_data)
        accessor = StateAccessor(state, BehaviorManager())

        # From library, door closed
        visible = accessor.get_visible_exits(LocationId("loc_library"), ActorId("player"))

        # Direction should not be in visible exits
        self.assertNotIn("up", visible)

    def test_can_see_passage_when_door_open(self):
        """Passage appears in visible exits when door is open."""
        state = load_game_state(self.game_data)
        # Open the door
        door = state.get_item(ItemId("door_test"))
        door.properties["door"]["open"] = True

        accessor = StateAccessor(state, BehaviorManager())

        # From library, door open
        visible = accessor.get_visible_exits(LocationId("loc_library"), ActorId("player"))

        # Direction should be in visible exits
        self.assertIn("up", visible)


if __name__ == '__main__':
    unittest.main()
