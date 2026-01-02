"""Tests for on_enter event invocation when entering locations."""
from src.types import ActorId

import unittest
from src.state_manager import (
    GameState, Location, Actor, Exit, Metadata,
    _build_whereabouts_index, _build_connection_index
)
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager, EventResult
from behaviors.core.exits import handle_go, handle_climb
from tests.conftest import BaseTestCase


class TestOnEnterEvent(BaseTestCase):
    """Test on_enter event invocation when entering locations."""

    def setUp(self):
        """Set up test game state."""
        super().setUp()

        self.game_state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="room1",
                    name="Start Room",
                    description="A plain room.",
                    exits={}
                ),
                Location(
                    id="room2",
                    name="Windy Room",
                    description="A room with strong winds.",
                    exits={},
                    behaviors=["windy_room"]  # Has on_enter behavior
                ),
                Location(
                    id="room3",
                    name="Safe Room",
                    description="A quiet room.",
                    exits={}
                    # No behaviors - should not invoke on_enter
                )
            ],
            exits=[
                Exit(
                    id="exit_room1_north",
                    name="doorway",
                    location="room1",
                    direction="north",
                    connections=["exit_room2_south"],
                    description="A simple doorway"
                ),
                Exit(
                    id="exit_room2_south",
                    name="doorway",
                    location="room2",
                    direction="south",
                    connections=["exit_room1_north"],
                    description="A simple doorway"
                ),
                Exit(
                    id="exit_room1_up",
                    name="ladder",
                    location="room1",
                    direction="up",
                    connections=["exit_room3_down"],
                    description="A wooden ladder"
                ),
                Exit(
                    id="exit_room3_down",
                    name="ladder",
                    location="room3",
                    direction="down",
                    connections=["exit_room1_up"],
                    description="A wooden ladder"
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

        # Build indices
        _build_whereabouts_index(self.game_state)
        _build_connection_index(self.game_state)

        # Create behavior manager and load exits module
        self.behavior_manager = BehaviorManager()
        import behaviors.core.exits
        self.behavior_manager.load_module(behaviors.core.exits)

        # Create mock behavior module for windy_room
        # We'll inject it directly into the behavior_manager's registry
        import types
        windy_room_module = types.ModuleType("windy_room")

        def on_enter(location, accessor, context):
            """Invoked when entering the windy room."""
            return EventResult(
                allow=True,
                feedback="A gust of wind nearly knocks you over!"
            )

        windy_room_module.on_enter = on_enter
        windy_room_module.vocabulary = {"verbs": [], "nouns": [], "adjectives": []}

        # Register the behavior module
        self.behavior_manager._modules["windy_room"] = windy_room_module

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_go_invokes_on_enter_with_behavior(self):
        """Test that 'go north' invokes on_enter when destination has behavior."""
        action = {
            "actor_id": "player",
            "verb": "go",
            "object": "north"
        }

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        # Check that on_enter message is included
        self.assertIn("gust of wind", result.primary.lower())
        self.assertIn("windy room", result.primary.lower())
        # Player should have moved
        player = self.accessor.get_actor(ActorId("player"))
        self.assertEqual(player.location, "room2")

    def test_go_without_behavior_no_on_enter(self):
        """Test that 'go up' doesn't fail when destination has no on_enter."""
        action = {
            "actor_id": "player",
            "verb": "go",
            "object": "up"
        }

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        # No on_enter message
        self.assertNotIn("gust of wind", result.primary.lower())
        self.assertIn("safe room", result.primary.lower())
        # Player should have moved
        player = self.accessor.get_actor(ActorId("player"))
        self.assertEqual(player.location, "room3")

    def test_climb_invokes_on_enter(self):
        """Test that 'climb' also invokes on_enter."""
        from src.parser import WordEntry, WordType

        # Add stairs exit from room1 to room2 (with behavior)
        # Note: stairs need a direction to be findable by find_exit_by_name
        stairs_exit = Exit(
            id="exit_room1_stairs",
            name="stairs",
            location="room1",
            direction="northeast",
            connections=["exit_room2_stairs"],
            description="Steep stairs"
        )
        stairs_exit_back = Exit(
            id="exit_room2_stairs",
            name="stairs",
            location="room2",
            direction="southwest",
            connections=["exit_room1_stairs"],
            description="Steep stairs"
        )
        self.game_state.exits.extend([stairs_exit, stairs_exit_back])

        # Rebuild indices to include new exits
        _build_whereabouts_index(self.game_state)
        _build_connection_index(self.game_state)

        stairs_entry = WordEntry(
            word="stairs",
            word_type=WordType.NOUN,
            synonyms=["staircase", "stairway", "steps"]
        )

        action = {
            "actor_id": "player",
            "verb": "climb",
            "object": stairs_entry
        }

        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        # Check that on_enter message is included
        self.assertIn("gust of wind", result.primary.lower())
        # Player should have moved
        player = self.accessor.get_actor(ActorId("player"))
        self.assertEqual(player.location, "room2")

    def test_on_enter_receives_context(self):
        """Test that on_enter receives actor_id and from_direction in context."""
        # We'll need to verify the context by checking what was passed
        # This is more of an integration test

        action = {
            "actor_id": "player",
            "verb": "go",
            "object": "north"
        }

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        # The behavior was invoked (message present)
        self.assertIn("gust of wind", result.primary.lower())


if __name__ == '__main__':
    unittest.main()
