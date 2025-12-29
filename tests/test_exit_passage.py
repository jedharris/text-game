"""Tests for exit passage and door_at fields.

Tests the new passage/door_at fields on ExitDescriptor that allow
proper narration of exits with both doors and passages (e.g., a door
leading to stairs).
"""

import unittest
from src.state_manager import (
    GameState, Location, Actor, Item, ExitDescriptor, Metadata
)
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.types import LocationId, ActorId
from behaviors.core.exits import handle_go, handle_up, handle_down


class TestExitDescriptorPassageFields(unittest.TestCase):
    """Test ExitDescriptor passage and door_at field definitions."""

    def test_passage_field_optional(self):
        """Exit without passage field works normally."""
        exit_desc = ExitDescriptor(
            type="door",
            to=LocationId("room2"),
            door_id="door1",
            name="wooden door"
        )
        self.assertIsNone(exit_desc.passage)
        self.assertIsNone(exit_desc.door_at)

    def test_passage_field_set(self):
        """Exit with passage field stores the value."""
        exit_desc = ExitDescriptor(
            type="door",
            to=LocationId("room2"),
            door_id="door1",
            name="ornate door",
            passage="narrow stone stairs"
        )
        self.assertEqual(exit_desc.passage, "narrow stone stairs")

    def test_door_at_field_set(self):
        """Exit with door_at field stores the location ID."""
        exit_desc = ExitDescriptor(
            type="door",
            to=LocationId("room2"),
            door_id="door1",
            name="ornate door",
            passage="narrow stone stairs",
            door_at=LocationId("room1")
        )
        self.assertEqual(exit_desc.door_at, LocationId("room1"))


class TestExitPassageValidation(unittest.TestCase):
    """Test validation of passage/door_at field combinations."""

    def test_door_at_required_when_passage_specified(self):
        """Validation fails if passage is set but door_at is not."""
        from src.validators import validate_game_state, ValidationError

        state = GameState(
            metadata=Metadata(title="Test", start_location="room1"),
            locations=[
                Location(
                    id=LocationId("room1"),
                    name="Room 1",
                    description="A room",
                    exits={
                        "up": ExitDescriptor(
                            type="door",
                            to=LocationId("room2"),
                            door_id="door1",
                            name="ornate door",
                            passage="narrow stairs"
                            # door_at missing - should fail
                        )
                    }
                ),
                Location(
                    id=LocationId("room2"),
                    name="Room 2",
                    description="Another room",
                    exits={}
                )
            ],
            items=[
                Item(
                    id="door1",
                    name="door",
                    description="An ornate door",
                    location="exit:room1:up",
                    _properties={"door": {"open": True, "locked": False}}
                )
            ],
            actors={"player": Actor(
                id="player",
                name="Test",
                description="Test",
                location="room1",
                inventory=[]
            )}
        )

        with self.assertRaises(ValidationError) as ctx:
            validate_game_state(state)

        self.assertIn("door_at", str(ctx.exception))

    def test_door_at_must_be_valid_location(self):
        """Validation fails if door_at is not current location or destination."""
        from src.validators import validate_game_state, ValidationError

        state = GameState(
            metadata=Metadata(title="Test", start_location="room1"),
            locations=[
                Location(
                    id=LocationId("room1"),
                    name="Room 1",
                    description="A room",
                    exits={
                        "up": ExitDescriptor(
                            type="door",
                            to=LocationId("room2"),
                            door_id="door1",
                            name="ornate door",
                            passage="narrow stairs",
                            door_at=LocationId("room3")  # Neither room1 nor room2
                        )
                    }
                ),
                Location(
                    id=LocationId("room2"),
                    name="Room 2",
                    description="Another room",
                    exits={}
                ),
                Location(
                    id=LocationId("room3"),
                    name="Room 3",
                    description="Unrelated room",
                    exits={}
                )
            ],
            items=[
                Item(
                    id="door1",
                    name="door",
                    description="An ornate door",
                    location="exit:room1:up",
                    _properties={"door": {"open": True, "locked": False}}
                )
            ],
            actors={"player": Actor(
                id="player",
                name="Test",
                description="Test",
                location="room1",
                inventory=[]
            )}
        )

        with self.assertRaises(ValidationError) as ctx:
            validate_game_state(state)

        self.assertIn("door_at", str(ctx.exception))

    def test_valid_passage_door_at_combination(self):
        """Validation passes with valid passage and door_at."""
        from src.validators import validate_game_state

        state = GameState(
            metadata=Metadata(title="Test", start_location="room1"),
            locations=[
                Location(
                    id=LocationId("room1"),
                    name="Room 1",
                    description="A room",
                    exits={
                        "up": ExitDescriptor(
                            type="door",
                            to=LocationId("room2"),
                            door_id="door1",
                            name="ornate door",
                            passage="narrow stairs",
                            door_at=LocationId("room1")  # Door at current location
                        )
                    }
                ),
                Location(
                    id=LocationId("room2"),
                    name="Room 2",
                    description="Another room",
                    exits={
                        "down": ExitDescriptor(
                            type="door",
                            to=LocationId("room1"),
                            door_id="door1",
                            name="ornate door",
                            passage="narrow stairs",
                            door_at=LocationId("room1")  # Same door, at room1 end
                        )
                    }
                )
            ],
            items=[
                Item(
                    id="door1",
                    name="door",
                    description="An ornate door",
                    location="exit:room1:up",
                    _properties={"door": {"open": True, "locked": False}}
                )
            ],
            actors={"player": Actor(
                id="player",
                name="Test",
                description="Test",
                location="room1",
                inventory=[]
            )}
        )

        # Should not raise
        validate_game_state(state)


class TestExitPassageMovementMessages(unittest.TestCase):
    """Test movement message generation with passage/door_at."""

    def setUp(self):
        """Set up test game state with door+passage exits."""
        self.game_state = GameState(
            metadata=Metadata(title="Test", start_location="library"),
            locations=[
                Location(
                    id=LocationId("library"),
                    name="Library",
                    description="A room full of books.",
                    exits={
                        "up": ExitDescriptor(
                            type="door",
                            to=LocationId("sanctum"),
                            door_id="door_sanctum",
                            name="ornate door",
                            passage="narrow stone stairs",
                            door_at=LocationId("library")  # Door at library end
                        )
                    }
                ),
                Location(
                    id=LocationId("sanctum"),
                    name="Sanctum",
                    description="A magical room.",
                    exits={
                        "down": ExitDescriptor(
                            type="door",
                            to=LocationId("library"),
                            door_id="door_sanctum",
                            name="ornate door",
                            passage="narrow stone stairs",
                            door_at=LocationId("library")  # Same door, still at library end
                        )
                    }
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
        self.game_state.actors[ActorId("player")].location = "sanctum"

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
                    exits={
                        "east": ExitDescriptor(
                            type="door",
                            to=LocationId("room2"),
                            door_id="door1",
                            name="wooden door"
                            # No passage field
                        )
                    }
                ),
                Location(
                    id=LocationId("room2"),
                    name="Room 2",
                    description="Another room.",
                    exits={}
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
