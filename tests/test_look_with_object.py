"""
Tests for look command with object parameter.

When look is given an object, it should behave like examine.
"""
from src.types import ActorId
import unittest
from src.state_manager import GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor
from behaviors.core.perception import handle_look
from tests.conftest import make_action


class TestLookWithObject(unittest.TestCase):
    """Test look command with object redirects to examine behavior."""

    def setUp(self):
        """Set up test game with items at different distances."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A test room"
        )

        # Item with "any" distance
        self.item_chandelier = Item(
            id="item_chandelier",
            name="chandelier",
            description="A crystal chandelier hanging from the ceiling",
            location="loc_room"
        )

        # Item with "near" distance
        self.item_desk = Item(
            id="item_desk",
            name="desk",
            description="A wooden desk with carved legs",
            location="loc_room",
            _properties={"interaction_distance": "near"}
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item_chandelier, self.item_desk],
            actors={
                "player": Actor(
                    id="player",
                    name="Adventurer",
                    description="The player",
                    location="loc_room",
                    inventory=[]
                )
            },
            locks=[],
            parts=[]
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_look_no_object_describes_room(self):
        """Test look with no object describes the room."""
        action = make_action(verb="look")
        result = handle_look(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("test room", result.primary.lower())
        # Should not set focus when just looking at room
        player = self.accessor.get_actor(ActorId("player"))
        self.assertIsNone(player.properties.get("focused_on"))

    def test_look_at_object_shows_description(self):
        """Test look at object shows object description."""
        action = make_action(verb="look", object="chandelier")
        result = handle_look(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("chandelier", result.primary.lower())
        self.assertIn("crystal", result.primary.lower())

    def test_look_at_object_sets_focus(self):
        """Test look at object sets focus like examine."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="look", object="chandelier")
        result = handle_look(self.accessor, action)

        self.assertTrue(result.success)
        # Should set focus like examine does
        self.assertEqual(player.properties.get("focused_on"), "item_chandelier")

    def test_look_at_near_object_moves_player(self):
        """Test look at 'near' object triggers positioning like examine."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="look", object="desk")
        result = handle_look(self.accessor, action)

        self.assertTrue(result.success)
        # Should include movement message
        self.assertIn("move", result.primary.lower())
        # Should set focus
        self.assertEqual(player.properties.get("focused_on"), "item_desk")

    def test_look_at_nonexistent_object(self):
        """Test look at nonexistent object fails gracefully."""
        action = make_action(verb="look", object="unicorn")
        result = handle_look(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())


if __name__ == '__main__':
    unittest.main()
