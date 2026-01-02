"""Tests for exit passage and door_at fields.

Tests the passage/door_at fields stored in Exit properties that allow
proper narration of exits with both doors and passages (e.g., a door
leading to stairs).
"""

import unittest
from src.state_manager import (
    GameState, Location, Actor, Item, Exit, Metadata,
    _build_whereabouts_index, _build_connection_index
)
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.types import LocationId, ActorId
from behaviors.core.exits import handle_go, handle_up, handle_down
from tests.conftest import BaseTestCase


class TestExitPassageMovementMessages(BaseTestCase):
    """Test movement message generation with passage/door_at properties."""

    def setUp(self):
        """Set up test game state with door+passage exits."""
        super().setUp()

        self.game_state = GameState(
            metadata=Metadata(title="Test", start_location="library"),
            locations=[
                Location(
                    id=LocationId("library"),
                    name="Library",
                    description="A room full of books.",
                    exits={}
                ),
                Location(
                    id=LocationId("sanctum"),
                    name="Sanctum",
                    description="A magical room.",
                    exits={}
                )
            ],
            exits=[
                Exit(
                    id="exit_library_up",
                    name="ornate door",
                    location="library",
                    direction="up",
                    connections=["exit_sanctum_down"],
                    door_id="door_sanctum",  # Direct attribute
                    passage="narrow stone stairs",  # Direct attribute
                    door_at="library"  # Direct attribute - door at library end
                ),
                Exit(
                    id="exit_sanctum_down",
                    name="ornate door",
                    location="sanctum",
                    direction="down",
                    connections=["exit_library_up"],
                    door_id="door_sanctum",  # Direct attribute
                    passage="narrow stone stairs",  # Direct attribute
                    door_at="library"  # Direct attribute - same door, still at library end
                )
            ],
            items=[
                Item(
                    id="door_sanctum",
                    name="door",
                    description="An ornate door covered in glowing runes.",
                    location="exit:library:up",
                    _properties={"door": {"open": True, "locked": False}}
                )
            ],
            actors={"player": Actor(
                id="player",
                name="Adventurer",
                description="The player",
                location="library",
                inventory=[]
            )}
        )
        _build_whereabouts_index(self.game_state)
        _build_connection_index(self.game_state)

        # Build indices
        _build_whereabouts_index(self.game_state)
        _build_connection_index(self.game_state)

        self.behavior_manager = BehaviorManager()
        import behaviors.core.exits
        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.exits)
        self.behavior_manager.load_module(behaviors.core.interaction)
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_door_first_when_at_current_location(self):
        """When door_at == current location, message mentions door first."""
        # Player is at library, door_at is library
        # So: door first, then passage
        action = {"actor_id": "player"}
        result = handle_up(self.accessor, action)

        self.assertTrue(result.success)
        # Message should mention going through door, then climbing stairs
        self.assertIn("ornate door", result.primary)
        self.assertIn("narrow stone stairs", result.primary)
        # Door should come before stairs in the message
        door_pos = result.primary.find("ornate door")
        stairs_pos = result.primary.find("narrow stone stairs")
        self.assertLess(door_pos, stairs_pos,
                       f"Door should be mentioned before stairs: {result.primary}")

    def test_passage_first_when_door_at_destination(self):
        """When door_at == destination, message mentions passage first."""
        # Move player to sanctum first
        self.accessor.set_entity_where("player", "sanctum")

        # Player is at sanctum, door_at is library (the destination)
        # So: passage first, then door
        action = {"actor_id": "player"}
        result = handle_down(self.accessor, action)

        self.assertTrue(result.success)
        # Message should mention descending stairs, then going through door
        self.assertIn("ornate door", result.primary)
        self.assertIn("narrow stone stairs", result.primary)
        # Stairs should come before door in the message
        door_pos = result.primary.find("ornate door")
        stairs_pos = result.primary.find("narrow stone stairs")
        self.assertLess(stairs_pos, door_pos,
                       f"Stairs should be mentioned before door: {result.primary}")

    def test_no_passage_uses_exit_name_only(self):
        """When no passage field, message uses exit name only (backward compatible)."""
        # Create state with simple door exit (no passage)
        state = GameState(
            metadata=Metadata(title="Test", start_location="room1"),
            locations=[
                Location(
                    id=LocationId("room1"),
                    name="Room 1",
                    description="A room.",
                    exits={}
                ),
                Location(
                    id=LocationId("room2"),
                    name="Room 2",
                    description="Another room.",
                    exits={}
                )
            ],
            exits=[
                Exit(
                    id="exit_room1_east",
                    name="wooden door",
                    location="room1",
                    direction="east",
                    connections=["exit_room2_west"],
                    properties={
                        "type": "door",
                        "door_id": "door1"
                        # No passage field
                    }
                ),
                Exit(
                    id="exit_room2_west",
                    name="wooden door",
                    location="room2",
                    direction="west",
                    connections=["exit_room1_east"],
                    properties={
                        "type": "door",
                        "door_id": "door1"
                    }
                )
            ],
            items=[
                Item(
                    id="door1",
                    name="door",
                    description="A wooden door.",
                    location="exit:room1:east",
                    _properties={"door": {"open": True, "locked": False}}
                )
            ],
            actors={"player": Actor(
                id="player",
                name="Adventurer",
                description="The player",
                location="room1",
                inventory=[]
            )}
        )
        _build_whereabouts_index(state)
        _build_connection_index(state)

        # Build indices
        _build_whereabouts_index(state)
        _build_connection_index(state)

        behavior_manager = BehaviorManager()
        import behaviors.core.exits
        import behaviors.core.interaction
        behavior_manager.load_module(behaviors.core.exits)
        behavior_manager.load_module(behaviors.core.interaction)
        accessor = StateAccessor(state, behavior_manager)

        action = {"actor_id": "player", "object": "east"}
        result = handle_go(accessor, action)

        self.assertTrue(result.success)
        # Should mention door but not any "passage" or "stairs"
        self.assertIn("wooden door", result.primary)
        self.assertNotIn("stairs", result.primary.lower())


if __name__ == '__main__':
    unittest.main()
