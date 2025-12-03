"""
Tests for handler utility functions.

Tests the find_action_target() utility that provides the standard
preamble for item-targeting handlers.
"""

import unittest
from src.state_manager import GameState, Location, Item, Actor, Metadata
from src.behavior_manager import BehaviorManager
from src.state_accessor import StateAccessor
from tests.conftest import make_action


def create_test_state():
    """Create a minimal test state for handler utility tests."""
    return GameState(
        metadata=Metadata(title="Test"),
        locations=[
            Location(id="loc1", name="Room", description="A test room")
        ],
        items=[
            Item(
                id="item_sword",
                name="sword",
                description="A rusty sword",
                location="loc1",
                properties={"portable": True}
            ),
            Item(
                id="item_iron_key",
                name="key",
                description="An iron key",
                location="loc1",
                properties={"portable": True}
            ),
            Item(
                id="item_brass_key",
                name="key",
                description="A brass key",
                location="loc1",
                properties={"portable": True}
            )
        ],
        actors={
            "player": Actor(
                id="player",
                name="Adventurer",
                description="The player",
                location="loc1",
                inventory=[]
            )
        }
    )


class TestFindActionTarget(unittest.TestCase):
    """Test find_action_target utility function."""

    def setUp(self):
        """Set up test state."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_find_action_target_returns_item_when_found(self):
        """Test that find_action_target returns item when found."""
        from utilities.handler_utils import find_action_target

        action = make_action(verb="push", object="sword", actor_id="player")
        item, error = find_action_target(self.accessor, action)

        self.assertIsNotNone(item)
        self.assertIsNone(error)
        self.assertEqual(item.id, "item_sword")

    def test_find_action_target_error_when_no_object(self):
        """Test that find_action_target returns error when no object specified."""
        from utilities.handler_utils import find_action_target

        action = {
            "verb": "push",
            "actor_id": "player"
            # No "object" key
        }
        item, error = find_action_target(self.accessor, action)

        self.assertIsNone(item)
        self.assertIsNotNone(error)
        self.assertFalse(error.success)
        self.assertIn("push", error.message.lower())

    def test_find_action_target_error_when_actor_not_found(self):
        """Test that find_action_target returns error when actor not found."""
        from utilities.handler_utils import find_action_target

        action = make_action(verb="push", object="sword", actor_id="nonexistent_actor")
        item, error = find_action_target(self.accessor, action)

        self.assertIsNone(item)
        self.assertIsNotNone(error)
        self.assertFalse(error.success)
        self.assertIn("INCONSISTENT STATE", error.message)

    def test_find_action_target_error_when_item_not_found(self):
        """Test that find_action_target returns error when item not found."""
        from utilities.handler_utils import find_action_target

        action = make_action(verb="push", object="nonexistent_item", actor_id="player")
        item, error = find_action_target(self.accessor, action)

        self.assertIsNone(item)
        self.assertIsNotNone(error)
        self.assertFalse(error.success)
        self.assertIn("don't see", error.message.lower())

    def test_find_action_target_uses_adjective_for_disambiguation(self):
        """Test that find_action_target uses adjective to select correct item."""
        from utilities.handler_utils import find_action_target

        # Without adjective - gets first match
        action_no_adj = make_action(verb="take", object="key", actor_id="player")
        item1, error1 = find_action_target(self.accessor, action_no_adj)
        self.assertIsNotNone(item1)
        self.assertIsNone(error1)

        # With adjective "brass" - should get brass key
        action_brass = make_action(verb="take", object="key", adjective="brass", actor_id="player")
        item2, error2 = find_action_target(self.accessor, action_brass)
        self.assertIsNotNone(item2)
        self.assertIsNone(error2)
        self.assertEqual(item2.id, "item_brass_key")

        # With adjective "iron" - should get iron key
        action_iron = make_action(verb="take", object="key", adjective="iron", actor_id="player")
        item3, error3 = find_action_target(self.accessor, action_iron)
        self.assertIsNotNone(item3)
        self.assertIsNone(error3)
        self.assertEqual(item3.id, "item_iron_key")

    def test_find_action_target_uses_verb_in_error_message(self):
        """Test that find_action_target uses verb from action in error messages."""
        from utilities.handler_utils import find_action_target

        action = {
            "verb": "examine",
            "actor_id": "player"
            # No object
        }
        item, error = find_action_target(self.accessor, action)

        self.assertIsNone(item)
        self.assertIsNotNone(error)
        self.assertIn("examine", error.message.lower())

    def test_find_action_target_defaults_actor_to_player(self):
        """Test that find_action_target defaults actor_id to 'player'."""
        from utilities.handler_utils import find_action_target

        action = make_action(verb="push", object="sword")
        # No actor_id explicitly passed - make_action defaults to "player"
        item, error = find_action_target(self.accessor, action)

        self.assertIsNotNone(item)
        self.assertIsNone(error)
        self.assertEqual(item.id, "item_sword")

    def test_find_action_target_defaults_verb_for_error(self):
        """Test that find_action_target uses fallback verb if not provided."""
        from utilities.handler_utils import find_action_target

        action = {
            "actor_id": "player"
            # No verb, no object
        }
        item, error = find_action_target(self.accessor, action)

        self.assertIsNone(item)
        self.assertIsNotNone(error)
        # Should use fallback "interact with" in message
        self.assertIn("interact with", error.message.lower())


if __name__ == '__main__':
    unittest.main()
