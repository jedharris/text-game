"""Tests for examining doors.

Verifies that handle_examine can find and describe doors, not just items.
"""

import unittest
from tests.conftest import create_test_state
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.state_manager import Item, Location, ExitDescriptor


class TestExamineDoor(unittest.TestCase):
    """Test that handle_examine works for doors."""

    def setUp(self):
        """Set up test state with doors."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Get player's location
        player = self.state.actors["player"]
        location_id = player.location

        # Add destination rooms
        other_room = Location(
            id="other_room",
            name="Other Room",
            description="Another room.",
            exits={"south": ExitDescriptor(type="door", to=location_id, door_id="door_wooden")}
        )
        another_room = Location(
            id="another_room",
            name="Another Room",
            description="Yet another room.",
            exits={"west": ExitDescriptor(type="door", to=location_id, door_id="door_iron")}
        )
        self.state.locations.append(other_room)
        self.state.locations.append(another_room)

        # Add exits from player's current location
        room = self.accessor.get_location(location_id)
        room.exits["north"] = ExitDescriptor(type="door", to="other_room", door_id="door_wooden")
        room.exits["east"] = ExitDescriptor(type="door", to="another_room", door_id="door_iron")

        # Add door items
        wooden_door = Item(
            id="door_wooden",
            name="door",
            description="A simple wooden door with iron hinges.",
            location=f"exit:{location_id}:north",
            properties={"door": {"open": False, "locked": False}}
        )
        iron_door = Item(
            id="door_iron",
            name="door",
            description="A heavy iron door with a sturdy lock.",
            location=f"exit:{location_id}:east",
            properties={"door": {"open": False, "locked": True}}
        )
        self.state.items.append(wooden_door)
        self.state.items.append(iron_door)

    def test_examine_door_finds_door(self):
        """Test that examine door finds a door in the location."""
        from behaviors.core.perception import handle_examine

        action = {"actor_id": "player", "object": "door"}
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should find first door (wooden)
        self.assertIn("wooden", result.message.lower())

    def test_examine_door_with_adjective(self):
        """Test that examine with adjective finds specific door."""
        from behaviors.core.perception import handle_examine

        # Use "heavy" which only appears in the iron door description
        action = {"actor_id": "player", "object": "door", "adjective": "heavy"}
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("heavy", result.message.lower())
        self.assertIn("sturdy lock", result.message.lower())

    def test_examine_wooden_door(self):
        """Test examining the wooden door specifically."""
        from behaviors.core.perception import handle_examine

        action = {"actor_id": "player", "object": "door", "adjective": "wooden"}
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("wooden", result.message.lower())
        self.assertIn("iron hinges", result.message.lower())

    def test_examine_nonexistent_door_fails(self):
        """Test that examining nonexistent door fails."""
        from behaviors.core.perception import handle_examine

        # No golden door exists
        action = {"actor_id": "player", "object": "door", "adjective": "golden"}
        result = handle_examine(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_examine_door_in_connected_location(self):
        """Test that door is found from connected location."""
        from behaviors.core.perception import handle_examine

        # Move player to other_room which has exit with door_wooden
        self.state.actors["player"].location = "other_room"

        action = {"actor_id": "player", "object": "door"}
        result = handle_examine(self.accessor, action)

        # The wooden door connects to other_room via the south exit, so it should be found there
        self.assertTrue(result.success)

    def test_examine_item_still_works(self):
        """Test that examining items still works after door support."""
        from behaviors.core.perception import handle_examine

        # Sword is in the test state
        action = {"actor_id": "player", "object": "sword"}
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("sword", result.message.lower())

    def test_examine_prefers_item_over_door(self):
        """Test that items are found before doors with same name."""
        from behaviors.core.perception import handle_examine
        from src.state_manager import Item

        # Add an item named "door" (unusual but possible)
        player = self.state.actors["player"]
        door_item = Item(
            id="item_door",
            name="door",
            description="A small decorative door ornament.",
            location=player.location,
            properties={"portable": True}
        )
        self.state.items.append(door_item)

        action = {"actor_id": "player", "object": "door"}
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should find the item first, not the actual door
        self.assertIn("ornament", result.message.lower())


class TestExamineDoorWithDirectionAdjective(unittest.TestCase):
    """Test examining doors using direction as adjective.

    Tests the pattern "examine <direction> door" where the direction
    acts as an adjective to select the specific door.
    """

    def setUp(self):
        """Set up test state with doors."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Get player's location
        player = self.state.actors["player"]
        location_id = player.location

        # Add destination rooms
        other_room = Location(
            id="other_room",
            name="Other Room",
            description="Another room.",
            exits={"south": ExitDescriptor(type="door", to=location_id, door_id="door_wooden")}
        )
        another_room = Location(
            id="another_room",
            name="Another Room",
            description="Yet another room.",
            exits={"west": ExitDescriptor(type="door", to=location_id, door_id="door_iron")}
        )
        self.state.locations.append(other_room)
        self.state.locations.append(another_room)

        # Add exits from player's current location
        room = self.accessor.get_location(location_id)
        room.exits["north"] = ExitDescriptor(type="door", to="other_room", door_id="door_wooden")
        room.exits["east"] = ExitDescriptor(type="door", to="another_room", door_id="door_iron")

        # Add door items
        wooden_door = Item(
            id="door_wooden",
            name="door",
            description="A simple wooden door with iron hinges.",
            location=f"exit:{location_id}:north",
            properties={"door": {"open": False, "locked": False}}
        )
        iron_door = Item(
            id="door_iron",
            name="door",
            description="A heavy iron door with a sturdy lock.",
            location=f"exit:{location_id}:east",
            properties={"door": {"open": False, "locked": True}}
        )
        self.state.items.append(wooden_door)
        self.state.items.append(iron_door)

    def test_examine_north_door(self):
        """Test 'examine north door' finds the north door."""
        from behaviors.core.perception import handle_examine

        action = {"actor_id": "player", "object": "door", "direction": "north"}
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("wooden", result.message.lower())

    def test_examine_east_door(self):
        """Test 'examine east door' finds the east door."""
        from behaviors.core.perception import handle_examine

        action = {"actor_id": "player", "object": "door", "direction": "east"}
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("iron", result.message.lower())

    def test_examine_nonexistent_direction_door(self):
        """Test 'examine west door' fails when no west door exists."""
        from behaviors.core.perception import handle_examine

        action = {"actor_id": "player", "object": "door", "direction": "west"}
        result = handle_examine(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())


class TestExamineDoorIntegration(unittest.TestCase):
    """Integration tests using LLMProtocolHandler."""

    def setUp(self):
        """Set up with protocol handler."""
        from pathlib import Path
        from src.state_manager import load_game_state
        from src.llm_protocol import LLMProtocolHandler

        # Load actual game state
        fixture_path = Path(__file__).parent.parent / "examples" / "simple_game" / "game_state.json"
        self.state = load_game_state(fixture_path)

        self.behavior_manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.behavior_manager)

    def test_examine_door_in_hallway(self):
        """Test examining door when in hallway with two doors."""
        # Move to hallway
        self.state.actors["player"].location = "loc_hallway"

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "door"}
        })

        self.assertTrue(result.get("success"))
        # Should find one of the doors
        self.assertIn("door", result.get("message", "").lower())

    def test_examine_iron_door_in_hallway(self):
        """Test examining iron door specifically."""
        self.state.actors["player"].location = "loc_hallway"

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "door", "adjective": "iron"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("iron", result.get("message", "").lower())

    def test_examine_wooden_door_in_hallway(self):
        """Test examining wooden door specifically."""
        self.state.actors["player"].location = "loc_hallway"

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "door", "adjective": "wooden"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("wooden", result.get("message", "").lower())

    def test_examine_table_still_works(self):
        """Test that examining items still works."""
        self.state.actors["player"].location = "loc_hallway"

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "table"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("table", result.get("message", "").lower())


if __name__ == '__main__':
    unittest.main()
