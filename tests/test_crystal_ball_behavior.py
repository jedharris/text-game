from tests.conftest import make_word_entry
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
        self.game_state = GameState(
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
                    description="A crystal ball. Mist swirls within its depths.",
                    location="library",
                    _properties={"magical": True},
                    behaviors=["behaviors.crystal_ball"]
                ),
                Item(
                    id="item_sanctum_key",
                    name="key",
                    description="A golden key that glows faintly with magic.",
                    location="library",
                    _properties={"portable": True, "magical": True, "states": {"hidden": True}}
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
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_hidden_key_not_visible_before_reveal(self):
        """Hidden key is not visible before peering into crystal ball."""
        from utilities.utils import find_accessible_item

        # Key should not be found because it's hidden
        key_entry = make_word_entry("key")
        key = find_accessible_item(self.accessor, key_entry, "player")
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
        self.assertIn("golden key", result.feedback.lower())
        self.assertIn("materializes", result.feedback.lower())

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
        self.assertIn("already claimed", result.feedback.lower())

    def test_revealed_key_becomes_accessible(self):
        """After reveal, key can be found by find_accessible_item."""
        from utilities.utils import find_accessible_item
        from examples.extended_game.behaviors.crystal_ball import on_peer

        crystal_ball = self.accessor.get_item("item_crystal_ball")
        context = {"actor_id": "player", "verb": "peer"}

        # Reveal the key
        on_peer(crystal_ball, self.accessor, context)

        # Key should now be accessible
        key_entry = make_word_entry("key")
        key = find_accessible_item(self.accessor, key_entry, "player")
        self.assertIsNotNone(key)
        self.assertEqual(key.id, "item_sanctum_key")

    def test_key_appears_in_same_location_as_crystal_ball(self):
        """Key appears in the same location as the crystal ball after reveal."""
        from examples.extended_game.behaviors.crystal_ball import on_peer

        crystal_ball = self.accessor.get_item("item_crystal_ball")
        sanctum_key = self.accessor.get_item("item_sanctum_key")

        # Crystal ball is in library
        self.assertEqual(crystal_ball.location, "library")

        # Peer into crystal ball
        context = {"actor_id": "player", "verb": "peer"}
        on_peer(crystal_ball, self.accessor, context)

        # Key should now be in the same location as the crystal ball
        self.assertEqual(sanctum_key.location, crystal_ball.location)


class TestCrystalBallInContainers(unittest.TestCase):
    """Test crystal ball behavior when placed in/on containers and surfaces."""

    def setUp(self):
        """Set up test fixtures with various containers."""
        self.game_state = GameState(
            metadata=Metadata(title="Crystal Ball Container Test"),
            locations=[
                Location(
                    id="library",
                    name="Library",
                    description="A library with furniture.",
                    exits={}
                )
            ],
            items=[
                Item(
                    id="item_desk",
                    name="desk",
                    description="A large oak desk.",
                    location="library",
                    _properties={
                        "type": "furniture",
                        "portable": False,
                        "container": {
                            "is_container": True,
                            "is_surface": True,
                            "capacity": 10
                        }
                    }
                ),
                Item(
                    id="item_box",
                    name="box",
                    description="A wooden box.",
                    location="library",
                    _properties={
                        "type": "container",
                        "portable": False,
                        "container": {
                            "is_container": True,
                            "is_surface": False,
                            "capacity": 10,
                            "open": True
                        }
                    }
                ),
                Item(
                    id="item_crystal_ball",
                    name="ball",
                    description="A crystal ball. Mist swirls within its depths.",
                    location="library",
                    _properties={"magical": True, "portable": True},
                    behaviors=["behaviors.crystal_ball"]
                ),
                Item(
                    id="item_sanctum_key",
                    name="key",
                    description="A golden key that glows faintly with magic.",
                    location="library",
                    _properties={
                        "portable": True,
                        "magical": True,
                        "states": {"hidden": True}
                    }
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
        import examples.extended_game.behaviors.crystal_ball
        self.behavior_manager.load_module(examples.extended_game.behaviors.crystal_ball)
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_key_appears_on_surface_when_crystal_ball_on_surface(self):
        """When crystal ball is on a surface, key appears on same surface with 'on' preposition."""
        from examples.extended_game.behaviors.crystal_ball import on_peer

        crystal_ball = self.accessor.get_item("item_crystal_ball")
        sanctum_key = self.accessor.get_item("item_sanctum_key")

        # Place crystal ball on desk (a surface)
        crystal_ball.location = "item_desk"

        # Peer into crystal ball
        context = {"actor_id": "player", "verb": "peer"}
        result = on_peer(crystal_ball, self.accessor, context)

        # Key should be on the desk
        self.assertEqual(sanctum_key.location, "item_desk")
        self.assertEqual(sanctum_key.location, crystal_ball.location)

        # Message should use "on the desk"
        self.assertIn("on the desk", result.feedback.lower())
        self.assertNotIn("on the floor", result.feedback.lower())

    def test_key_appears_in_container_when_crystal_ball_in_container(self):
        """When crystal ball is in a non-surface container, key appears in same container with 'in' preposition."""
        from examples.extended_game.behaviors.crystal_ball import on_peer

        crystal_ball = self.accessor.get_item("item_crystal_ball")
        sanctum_key = self.accessor.get_item("item_sanctum_key")

        # Place crystal ball in box (a container but not a surface)
        crystal_ball.location = "item_box"

        # Peer into crystal ball
        context = {"actor_id": "player", "verb": "peer"}
        result = on_peer(crystal_ball, self.accessor, context)

        # Key should be in the box
        self.assertEqual(sanctum_key.location, "item_box")
        self.assertEqual(sanctum_key.location, crystal_ball.location)

        # Message should use "in the box"
        self.assertIn("in the box", result.feedback.lower())
        self.assertNotIn("on the floor", result.feedback.lower())


class TestCrystalBallMissingKey(unittest.TestCase):
    """Test crystal ball behavior when key doesn't exist."""

    def setUp(self):
        """Set up test fixtures without the sanctum key."""
        self.game_state = GameState(
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
                    description="A crystal ball. Mist swirls within its depths.",
                    location="library",
                    _properties={"magical": True},
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
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_peer_without_key_shows_nothing_revealed(self):
        """Peering when key doesn't exist shows nothing revealed message."""
        from examples.extended_game.behaviors.crystal_ball import on_peer

        crystal_ball = self.accessor.get_item("item_crystal_ball")

        context = {"actor_id": "player", "verb": "peer"}
        result = on_peer(crystal_ball, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("reveal nothing", result.feedback.lower())


if __name__ == "__main__":
    unittest.main()
