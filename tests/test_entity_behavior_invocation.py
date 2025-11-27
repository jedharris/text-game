"""
Tests for entity behavior invocation via handle_take/handle_drop.

Phase C-2 Part A: These tests verify that the manipulation handlers
properly invoke entity behaviors (on_take, on_drop) by passing the
verb parameter to accessor.update().
"""

import unittest
from pathlib import Path

from src.state_manager import GameState, Item, Actor, Location
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager, EventResult
from behaviors.core.manipulation import handle_take, handle_drop


def create_test_state_with_light_source():
    """Create a minimal game state with a light source item."""
    state = GameState(
        metadata={"title": "Test", "start_location": "room1"},
        locations=[
            Location(
                id="room1",
                name="Test Room",
                description="A test room.",
                exits={},
                items=["lantern"]
            )
        ],
        items=[
            Item(
                id="lantern",
                name="lantern",
                description="A magic lantern.",
                location="room1",
                properties={
                    "portable": True,
                    "provides_light": True,
                    "states": {"lit": False}
                },
                behaviors=["behaviors.core.light_sources"]
            )
        ],
        locks=[],
        actors={
            "player": Actor(
                id="player",
                name="player",
                description="",
                location="room1",
                inventory=[]
            )
        }
    )
    return state


class TestEntityBehaviorInvocationOnTake(unittest.TestCase):
    """Test that handle_take invokes entity on_take behaviors."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = create_test_state_with_light_source()
        self.manager = BehaviorManager()

        # Load behavior modules
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        self.accessor = StateAccessor(self.state, self.manager)

    def test_take_invokes_on_take_behavior(self):
        """Test that taking an item invokes its on_take behavior."""
        lantern = self.state.get_item("lantern")

        # Verify lantern starts unlit
        self.assertFalse(lantern.states.get("lit", True))

        # Take the lantern
        action = {"actor_id": "player", "object": "lantern"}
        result = handle_take(self.accessor, action)

        # Should succeed
        self.assertTrue(result.success)

        # on_take behavior should have set lit=True
        self.assertTrue(lantern.states.get("lit", False),
            "Entity on_take behavior was not invoked - lantern should be lit")

    def test_take_returns_behavior_message(self):
        """Test that taking an item returns the behavior message."""
        action = {"actor_id": "player", "object": "lantern"}
        result = handle_take(self.accessor, action)

        # Result message should include behavior message about runes
        self.assertIn("runes", result.message.lower(),
            "Behavior message not included in result")


class TestEntityBehaviorInvocationOnDrop(unittest.TestCase):
    """Test that handle_drop invokes entity on_drop behaviors."""

    def setUp(self):
        """Set up test fixtures with lantern in inventory."""
        self.state = create_test_state_with_light_source()
        self.manager = BehaviorManager()

        # Load behavior modules
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        self.accessor = StateAccessor(self.state, self.manager)

        # Put lantern in player inventory and set it lit
        lantern = self.state.get_item("lantern")
        lantern.location = "player"
        lantern.states["lit"] = True
        self.state.actors["player"].inventory = ["lantern"]

    def test_drop_invokes_on_drop_behavior(self):
        """Test that dropping an item invokes its on_drop behavior."""
        lantern = self.state.get_item("lantern")

        # Verify lantern starts lit (in inventory)
        self.assertTrue(lantern.states.get("lit", False))

        # Drop the lantern
        action = {"actor_id": "player", "object": "lantern"}
        result = handle_drop(self.accessor, action)

        # Should succeed
        self.assertTrue(result.success)

        # on_drop behavior should have set lit=False
        self.assertFalse(lantern.states.get("lit", True),
            "Entity on_drop behavior was not invoked - lantern should be unlit")

    def test_drop_returns_behavior_message(self):
        """Test that dropping an item returns the behavior message."""
        action = {"actor_id": "player", "object": "lantern"}
        result = handle_drop(self.accessor, action)

        # Result message should include behavior message about runes fading
        self.assertIn("runes", result.message.lower(),
            "Behavior message not included in result")


class TestEntityBehaviorInvocationNPC(unittest.TestCase):
    """Test that entity behaviors work for NPC actors too."""

    def setUp(self):
        """Set up test fixtures with NPC."""
        self.state = create_test_state_with_light_source()
        self.manager = BehaviorManager()

        # Load behavior modules
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        self.accessor = StateAccessor(self.state, self.manager)

        # Add NPC in same room
        self.state.actors["guard"] = Actor(
            id="guard",
            name="guard",
            description="A guard.",
            location="room1",
            inventory=[]
        )

    def test_npc_take_invokes_on_take_behavior(self):
        """Test that NPC taking an item invokes its on_take behavior."""
        lantern = self.state.get_item("lantern")

        # Verify lantern starts unlit
        self.assertFalse(lantern.states.get("lit", True))

        # NPC takes the lantern
        action = {"actor_id": "guard", "object": "lantern"}
        result = handle_take(self.accessor, action)

        # Should succeed
        self.assertTrue(result.success)

        # on_take behavior should have set lit=True
        self.assertTrue(lantern.states.get("lit", False),
            "Entity on_take behavior was not invoked for NPC")


if __name__ == '__main__':
    unittest.main()
