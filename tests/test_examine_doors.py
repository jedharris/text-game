"""Tests for examining doors.

Verifies that handle_examine can find and describe doors, not just items.

Updated for Phase 4 (Narration API) to handle NarrationResult format.
"""
from src.types import ActorId
from typing import Any, Dict

import unittest
from tests.conftest import make_action, create_test_state
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.state_manager import Item, Location, ExitDescriptor


def get_result_message(result: Dict[str, Any]) -> str:
    """
    Extract message text from result, handling both old and new formats.

    New format (Phase 4): result["narration"]["primary_text"]
    Old format: result["message"] or result["error"]["message"]

    For the new format, also concatenates secondary_beats.
    """
    # New format: NarrationResult
    if "narration" in result:
        narration = result["narration"]
        parts = [narration.get("primary_text", "")]
        if "secondary_beats" in narration:
            parts.extend(narration["secondary_beats"])
        return "\n".join(parts)

    # Old format - success case
    if result.get("success") and "message" in result:
        return result["message"]

    # Old format - error case
    if "error" in result and "message" in result["error"]:
        return result["error"]["message"]

    return result.get("message", "")


class TestExamineDoor(unittest.TestCase):
    """Test that handle_examine works for doors."""

    def setUp(self):
        """Set up test state with doors."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Get player's location
        player = self.game_state.get_actor(ActorId("player"))
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
        self.game_state.locations.append(other_room)
        self.game_state.locations.append(another_room)

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
            _properties={"door": {"open": False, "locked": False}}
        )
        iron_door = Item(
            id="door_iron",
            name="door",
            description="A heavy iron door with a sturdy lock.",
            location=f"exit:{location_id}:east",
            _properties={"door": {"open": False, "locked": True}}
        )
        self.game_state.items.append(wooden_door)
        self.game_state.items.append(iron_door)

    def test_examine_door_finds_door(self):
        """Test that examine door finds a door in the location."""
        from behaviors.core.perception import handle_examine

        action = make_action(object="door", actor_id="player")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should find first door (wooden)
        self.assertIn("wooden", result.primary.lower())

    def test_examine_door_with_adjective(self):
        """Test that examine with adjective finds specific door."""
        from behaviors.core.perception import handle_examine

        # Use "heavy" which only appears in the iron door description
        action = make_action(object="door", adjective="heavy", actor_id="player")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("heavy", result.primary.lower())
        self.assertIn("sturdy lock", result.primary.lower())

    def test_examine_wooden_door(self):
        """Test examining the wooden door specifically."""
        from behaviors.core.perception import handle_examine

        action = make_action(object="door", adjective="wooden", actor_id="player")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("wooden", result.primary.lower())
        self.assertIn("iron hinges", result.primary.lower())

    def test_examine_nonexistent_door_fails(self):
        """Test that examining nonexistent door fails."""
        from behaviors.core.perception import handle_examine

        # No golden door exists
        action = make_action(object="door", adjective="golden", actor_id="player")
        result = handle_examine(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_examine_door_in_connected_location(self):
        """Test that door is found from connected location."""
        from behaviors.core.perception import handle_examine

        # Move player to other_room which has exit with door_wooden
        self.game_state.actors[ActorId("player")].location = "other_room"

        action = make_action(object="door", actor_id="player")
        result = handle_examine(self.accessor, action)

        # The wooden door connects to other_room via the south exit, so it should be found there
        self.assertTrue(result.success)

    def test_examine_item_still_works(self):
        """Test that examining items still works after door support."""
        from behaviors.core.perception import handle_examine

        # Sword is in the test state
        action = make_action(object="sword", actor_id="player")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("sword", result.primary.lower())

    def test_examine_prefers_item_over_door(self):
        """Test that items are found before doors with same name."""
        from behaviors.core.perception import handle_examine
        from src.state_manager import Item

        # Add an item named "door" (unusual but possible)
        player = self.game_state.get_actor(ActorId("player"))
        door_item = Item(
            id="item_door",
            name="door",
            description="A small decorative door ornament.",
            location=player.location,
            _properties={"portable": True}
        )
        self.game_state.items.append(door_item)

        action = make_action(object="door", actor_id="player")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should find the item first, not the actual door
        self.assertIn("ornament", result.primary.lower())


class TestExamineDoorWithDirectionAdjective(unittest.TestCase):
    """Test examining doors using direction as adjective.

    Tests the pattern "examine <direction> door" where the direction
    acts as an adjective to select the specific door.
    """

    def setUp(self):
        """Set up test state with doors."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Get player's location
        player = self.game_state.get_actor(ActorId("player"))
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
        self.game_state.locations.append(other_room)
        self.game_state.locations.append(another_room)

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
            _properties={"door": {"open": False, "locked": False}}
        )
        iron_door = Item(
            id="door_iron",
            name="door",
            description="A heavy iron door with a sturdy lock.",
            location=f"exit:{location_id}:east",
            _properties={"door": {"open": False, "locked": True}}
        )
        self.game_state.items.append(wooden_door)
        self.game_state.items.append(iron_door)

    def test_examine_north_door(self):
        """Test 'examine north door' finds the north door."""
        from behaviors.core.perception import handle_examine

        action = make_action(object="door", adjective="north", actor_id="player")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("wooden", result.primary.lower())

    def test_examine_east_door(self):
        """Test 'examine east door' finds the east door."""
        from behaviors.core.perception import handle_examine

        action = make_action(object="door", adjective="east", actor_id="player")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("iron", result.primary.lower())

    def test_examine_nonexistent_direction_door(self):
        """Test 'examine west door' fails when no west door exists."""
        from behaviors.core.perception import handle_examine

        action = make_action(object="door", adjective="west", actor_id="player")
        result = handle_examine(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())


class TestExamineDoorIntegration(unittest.TestCase):
    """Integration tests using LLMProtocolHandler."""

    def setUp(self):
        """Set up with protocol handler."""
        from pathlib import Path
        from src.state_manager import load_game_state
        from src.llm_protocol import LLMProtocolHandler

        # Load actual game state
        fixture_path = Path(__file__).parent.parent / "examples" / "simple_game" / "game_state.json"
        self.game_state = load_game_state(fixture_path)

        self.behavior_manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        self.handler = LLMProtocolHandler(self.game_state, behavior_manager=self.behavior_manager)

    def test_examine_door_in_hallway(self):
        """Test examining door when in hallway with two doors."""
        # Move to hallway
        self.game_state.actors[ActorId("player")].location = "loc_hallway"

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "door"}
        })

        self.assertTrue(result.get("success"))
        # Should find one of the doors
        self.assertIn("door", get_result_message(result).lower())

    def test_examine_iron_door_in_hallway(self):
        """Test examining iron door specifically."""
        self.game_state.actors[ActorId("player")].location = "loc_hallway"

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "door", "adjective": "iron"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("iron", get_result_message(result).lower())

    def test_examine_wooden_door_in_hallway(self):
        """Test examining wooden door specifically."""
        self.game_state.actors[ActorId("player")].location = "loc_hallway"

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "door", "adjective": "wooden"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("wooden", get_result_message(result).lower())

    def test_examine_table_still_works(self):
        """Test that examining items still works."""
        self.game_state.actors[ActorId("player")].location = "loc_hallway"

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "table"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("table", get_result_message(result).lower())


if __name__ == '__main__':
    unittest.main()
