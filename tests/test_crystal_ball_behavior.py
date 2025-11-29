"""Tests for the crystal ball behavior in extended_game.

Tests that the crystal ball behavior correctly uses the states.hidden mechanism
to reveal the sanctum key.
"""

import unittest
from unittest.mock import Mock

from src.state_manager import GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor, EventResult
from src.behavior_manager import BehaviorManager


class TestCrystalBallRevealHiddenItem(unittest.TestCase):
    """Test crystal ball behavior reveals hidden item via states.hidden."""

    def setUp(self):
        """Set up test fixtures with crystal ball and hidden key."""
        self.state = GameState(
            metadata=Metadata(title="Crystal Ball Test"),
            locations=[
                Location(
                    id="library",
                    name="Library",
                    description="A library with a crystal ball.",
                    exits={}
                )
            ],
            items=[
                Item(
                    id="item_crystal_ball",
                    name="ball",
                    description="A crystal ball on a silver stand.",
                    location="library",
                    properties={"magical": True},
                    behaviors=["behaviors.crystal_ball"]
                ),
                Item(
                    id="item_sanctum_key",
                    name="key",
                    description="A golden key that glows faintly with magic.",
                    location="library",
                    properties={"portable": True, "magical": True, "states": {"hidden": True}}
                )
            ],
            actors={
                "player": Actor(
                    id="player",
                    name="Adventurer",
                    description="The player",
                    location="library",
                    inventory=[]
                )
            }
        )

        self.behavior_manager = BehaviorManager()
        # Load the crystal ball behavior module
        import examples.extended_game.behaviors.crystal_ball
        self.behavior_manager.load_module(examples.extended_game.behaviors.crystal_ball)
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_hidden_key_not_visible_before_reveal(self):
        """Hidden key is not visible before peering into crystal ball."""
        from utilities.utils import find_accessible_item

        # Key should not be found because it's hidden
        key = find_accessible_item(self.accessor, "key", "player")
        self.assertIsNone(key)

    def test_crystal_ball_reveals_hidden_key(self):
        """Peering into crystal ball sets key's hidden state to False."""
        from examples.extended_game.behaviors.crystal_ball import on_peer

        crystal_ball = self.accessor.get_item("item_crystal_ball")
        sanctum_key = self.accessor.get_item("item_sanctum_key")

        # Key starts hidden
        self.assertTrue(sanctum_key.states.get("hidden", False))

        # Peer into the crystal ball
        context = {"actor_id": "player", "verb": "peer"}
        result = on_peer(crystal_ball, self.accessor, context)

        # Result should be successful with reveal message
        self.assertTrue(result.allow)
        self.assertIn("golden key", result.message.lower())
        self.assertIn("materializes", result.message.lower())

        # Key should now be revealed
        self.assertFalse(sanctum_key.states.get("hidden", True))

    def test_second_peer_shows_already_claimed_message(self):
        """Peering again after reveal shows 'already claimed' message."""
        from examples.extended_game.behaviors.crystal_ball import on_peer

        crystal_ball = self.accessor.get_item("item_crystal_ball")
        sanctum_key = self.accessor.get_item("item_sanctum_key")

        context = {"actor_id": "player", "verb": "peer"}

        # First peer reveals the key
        on_peer(crystal_ball, self.accessor, context)

        # Second peer should show already claimed message
        result = on_peer(crystal_ball, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("already claimed", result.message.lower())

    def test_revealed_key_becomes_accessible(self):
        """After reveal, key can be found by find_accessible_item."""
        from utilities.utils import find_accessible_item
        from examples.extended_game.behaviors.crystal_ball import on_peer

        crystal_ball = self.accessor.get_item("item_crystal_ball")
        context = {"actor_id": "player", "verb": "peer"}

        # Reveal the key
        on_peer(crystal_ball, self.accessor, context)

        # Key should now be accessible
        key = find_accessible_item(self.accessor, "key", "player")
        self.assertIsNotNone(key)
        self.assertEqual(key.id, "item_sanctum_key")

    def test_key_stays_in_same_location(self):
        """Key stays in library location after reveal (not moved)."""
        from examples.extended_game.behaviors.crystal_ball import on_peer

        crystal_ball = self.accessor.get_item("item_crystal_ball")
        sanctum_key = self.accessor.get_item("item_sanctum_key")

        # Key starts in library
        self.assertEqual(sanctum_key.location, "library")

        # Peer into crystal ball
        context = {"actor_id": "player", "verb": "peer"}
        on_peer(crystal_ball, self.accessor, context)

        # Key should still be in library (not moved)
        self.assertEqual(sanctum_key.location, "library")


class TestCrystalBallMissingKey(unittest.TestCase):
    """Test crystal ball behavior when key doesn't exist."""

    def setUp(self):
        """Set up test fixtures without the sanctum key."""
        self.state = GameState(
            metadata=Metadata(title="Crystal Ball Test - No Key"),
            locations=[
                Location(
                    id="library",
                    name="Library",
                    description="A library with a crystal ball.",
                    exits={}
                )
            ],
            items=[
                Item(
                    id="item_crystal_ball",
                    name="ball",
                    description="A crystal ball on a silver stand.",
                    location="library",
                    properties={"magical": True},
                    behaviors=["behaviors.crystal_ball"]
                )
                # No sanctum key
            ],
            actors={
                "player": Actor(
                    id="player",
                    name="Adventurer",
                    description="The player",
                    location="library",
                    inventory=[]
                )
            }
        )

        self.behavior_manager = BehaviorManager()
        import examples.extended_game.behaviors.crystal_ball
        self.behavior_manager.load_module(examples.extended_game.behaviors.crystal_ball)
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_peer_without_key_shows_nothing_revealed(self):
        """Peering when key doesn't exist shows nothing revealed message."""
        from examples.extended_game.behaviors.crystal_ball import on_peer

        crystal_ball = self.accessor.get_item("item_crystal_ball")

        context = {"actor_id": "player", "verb": "peer"}
        result = on_peer(crystal_ball, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("reveal nothing", result.message.lower())


if __name__ == "__main__":
    unittest.main()
