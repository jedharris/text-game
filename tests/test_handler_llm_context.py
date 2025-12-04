"""Tests for llm_context in behavior handlers.

Verifies that all handlers return llm_context with trait randomization
for the entities they operate on.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.state_manager import (
    Item, Location, Actor, Lock, GameState
)
from src.state_accessor import StateAccessor, HandlerResult
from tests.conftest import make_action


def create_test_game_state():
    """Create a minimal game state for testing."""
    return GameState(
        metadata=MagicMock(),
        locations=[
            Location(
                id="loc_room",
                name="Test Room",
                description="A test room.",
                exits={}
            )
        ],
        items=[
            Item(
                id="item_sword",
                name="sword",
                description="A rusty sword.",
                location="loc_room",
                properties={
                    "portable": True,
                    "llm_context": {
                        "traits": ["rusty", "ancient", "battle-worn"]
                    }
                }
            ),
            Item(
                id="item_chest",
                name="chest",
                description="A wooden chest.",
                location="loc_room",
                properties={
                    "container": {"open": False, "is_surface": False},
                    "llm_context": {
                        "traits": ["wooden", "ornate", "heavy"]
                    }
                }
            ),
            Item(
                id="item_key",
                name="key",
                description="A brass key.",
                location="player",
                properties={
                    "llm_context": {
                        "traits": ["brass", "small", "intricate"]
                    }
                }
            ),
            Item(
                id="door_north",
                name="door",
                description="A wooden door.",
                location="exit:loc_room:north",
                properties={
                    "door": {"open": False, "locked": True, "lock_id": "lock_door"},
                    "llm_context": {
                        "traits": ["wooden", "sturdy", "old"]
                    }
                }
            ),
            Item(
                id="item_book",
                name="book",
                description="An old book.",
                location="loc_room",
                properties={
                    "readable": True,
                    "text": "Ancient secrets within.",
                    "llm_context": {
                        "traits": ["leather-bound", "dusty", "mysterious"]
                    }
                }
            ),
            Item(
                id="item_ladder",
                name="ladder",
                description="A wooden ladder.",
                location="loc_room",
                properties={
                    "climbable": True,
                    "llm_context": {
                        "traits": ["rickety", "tall", "wooden"]
                    }
                }
            ),
            Item(
                id="item_lever",
                name="lever",
                description="A metal lever.",
                location="loc_room",
                properties={
                    "llm_context": {
                        "traits": ["rusty", "mechanical", "heavy"]
                    }
                }
            )
        ],
        actors={
            "player": Actor(
                id="player",
                name="Adventurer",
                description="The player.",
                location="loc_room",
                inventory=["item_key"]
            ),
            "npc_guard": Actor(
                id="npc_guard",
                name="Guard",
                description="A stern guard.",
                location="loc_room",
                inventory=[],
                properties={
                    "llm_context": {
                        "traits": ["vigilant", "armored", "suspicious"]
                    }
                }
            )
        },
        locks=[
            Lock(
                id="lock_door",
                name="Door Lock",
                description="An iron lock.",
                properties={
                    "opens_with": ["item_key"],
                    "llm_context": {
                        "traits": ["iron", "ornate", "ancient"]
                    }
                }
            )
        ]
    )


class TestManipulationHandlersLlmContext(unittest.TestCase):
    """Test llm_context in manipulation handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = create_test_game_state()
        self.accessor = StateAccessor(self.game_state, MagicMock())

    def test_handle_take_returns_llm_context(self):
        """Test handle_take returns item llm_context."""
        from behaviors.core.manipulation import handle_take

        action = make_action(object="sword", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)
        self.assertIn("traits", result.data["llm_context"])

    def test_handle_drop_returns_llm_context(self):
        """Test handle_drop returns item llm_context."""
        from behaviors.core.manipulation import handle_drop

        # First take the sword so we can drop it
        sword = self.accessor.get_item("item_sword")
        sword.location = "player"
        self.game_state.actors["player"].inventory.append("item_sword")

        action = make_action(object="sword", actor_id="player")
        result = handle_drop(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)

    def test_handle_give_returns_llm_context(self):
        """Test handle_give returns item llm_context."""
        from behaviors.core.manipulation import handle_give

        action = make_action(object="key", indirect_object="guard", actor_id="player")
        result = handle_give(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)

    def test_handle_put_returns_llm_context(self):
        """Test handle_put returns item llm_context."""
        from behaviors.core.manipulation import handle_put

        # Open the chest first
        chest = self.accessor.get_item("item_chest")
        chest.properties["container"]["open"] = True

        action = make_action(object="key", indirect_object="chest", actor_id="player")
        result = handle_put(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)


class TestInteractionHandlersLlmContext(unittest.TestCase):
    """Test llm_context in interaction handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = create_test_game_state()
        self.accessor = StateAccessor(self.game_state, MagicMock())

    def test_handle_open_returns_llm_context(self):
        """Test handle_open returns container llm_context."""
        from behaviors.core.interaction import handle_open

        action = make_action(object="chest", actor_id="player")
        result = handle_open(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)

    def test_handle_close_returns_llm_context(self):
        """Test handle_close returns container llm_context."""
        from behaviors.core.interaction import handle_close

        # Open the chest first
        chest = self.accessor.get_item("item_chest")
        chest.properties["container"]["open"] = True

        action = make_action(object="chest", actor_id="player")
        result = handle_close(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)

    def test_handle_use_returns_llm_context(self):
        """Test handle_use returns item llm_context."""
        from behaviors.core.interaction import handle_use

        action = make_action(object="sword", actor_id="player")
        result = handle_use(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)

    def test_handle_read_returns_llm_context(self):
        """Test handle_read returns item llm_context."""
        from behaviors.core.interaction import handle_read

        action = make_action(object="book", actor_id="player")
        result = handle_read(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)

    def test_handle_climb_returns_llm_context(self):
        """Test handle_climb returns item llm_context."""
        from behaviors.core.spatial import handle_climb

        action = make_action(object="ladder", actor_id="player")
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)

    def test_handle_pull_returns_llm_context(self):
        """Test handle_pull returns item llm_context."""
        from behaviors.core.interaction import handle_pull

        action = make_action(object="lever", actor_id="player")
        result = handle_pull(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)

    def test_handle_push_returns_llm_context(self):
        """Test handle_push returns item llm_context."""
        from behaviors.core.interaction import handle_push

        action = make_action(object="lever", actor_id="player")
        result = handle_push(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)


class TestLockHandlersLlmContext(unittest.TestCase):
    """Test llm_context in lock handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = create_test_game_state()
        self.accessor = StateAccessor(self.game_state, MagicMock())

    def test_handle_unlock_returns_llm_context(self):
        """Test handle_unlock returns door llm_context."""
        from behaviors.core.locks import handle_unlock

        action = make_action(object="door", actor_id="player")
        result = handle_unlock(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)

    def test_handle_lock_returns_llm_context(self):
        """Test handle_lock returns door llm_context."""
        from behaviors.core.locks import handle_lock

        # Unlock the door first
        door = self.accessor.get_item("door_north")
        door.properties["door"]["locked"] = False

        action = make_action(object="door", actor_id="player")
        result = handle_lock(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)


class TestInventoryHandlerLlmContext(unittest.TestCase):
    """Test llm_context in inventory handler."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = create_test_game_state()
        self.accessor = StateAccessor(self.game_state, MagicMock())

    def test_handle_inventory_returns_llm_context(self):
        """Test handle_inventory returns item llm_context for carried items."""
        from behaviors.core.perception import handle_inventory

        action = make_action(actor_id="player")
        result = handle_inventory(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        # Inventory should include items array
        self.assertIn("items", result.data)
        # Each item should have llm_context
        self.assertTrue(len(result.data["items"]) > 0)
        for item_data in result.data["items"]:
            self.assertIn("llm_context", item_data)


if __name__ == '__main__':
    unittest.main()
