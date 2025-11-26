"""Tests for examining doors.

Verifies that handle_examine can find and describe doors, not just items.
"""

import unittest
from tests.conftest import create_test_state
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.state_manager import Door


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

        # Add doors to the location
        wooden_door = Door(
            id="door_wooden",
            locations=(location_id, "other_room"),
            properties={
                "open": False,
                "locked": False,
                "description": "A simple wooden door with iron hinges."
            }
        )
        iron_door = Door(
            id="door_iron",
            locations=(location_id, "another_room"),
            properties={
                "open": False,
                "locked": True,
                "description": "A heavy iron door with a sturdy lock."
            }
        )
        self.state.doors.append(wooden_door)
        self.state.doors.append(iron_door)

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

    def test_examine_door_in_wrong_location_fails(self):
        """Test that door in different location isn't found."""
        from behaviors.core.perception import handle_examine

        # Move player to a location with no doors
        self.state.actors["player"].location = "other_room"

        # Add a location for the player
        from src.state_manager import Location
        other_room = Location(
            id="other_room",
            name="Other Room",
            description="An empty room.",
            exits={},
            items=[],
            npcs=[],
            properties={},
            behaviors=[]
        )
        self.state.locations.append(other_room)

        action = {"actor_id": "player", "object": "door"}
        result = handle_examine(self.accessor, action)

        # The wooden door connects to other_room, so it should be found there
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


class TestExamineDoorIntegration(unittest.TestCase):
    """Integration tests using JSONProtocolHandler."""

    def setUp(self):
        """Set up with protocol handler."""
        from pathlib import Path
        from src.state_manager import load_game_state
        from src.llm_protocol import JSONProtocolHandler

        # Load actual game state
        fixture_path = Path(__file__).parent.parent / "examples" / "simple_game_state.json"
        self.state = load_game_state(fixture_path)

        self.behavior_manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        self.handler = JSONProtocolHandler(self.state, behavior_manager=self.behavior_manager)

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
