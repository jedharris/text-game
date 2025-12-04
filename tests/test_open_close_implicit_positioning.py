"""
Tests for implicit positioning in handle_open and handle_close.

Following TDD approach - these tests are written first before implementation.
"""
import unittest
from src.state_manager import GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor
from behaviors.core.interaction import handle_open, handle_close
from tests.conftest import make_action


class TestOpenCloseImplicitPositioning(unittest.TestCase):
    """Test implicit positioning with open and close commands."""

    def setUp(self):
        """Set up test game with containers at different distances."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A test room"
        )

        # Container with "any" distance (default)
        self.item_bag = Item(
            id="item_bag",
            name="bag",
            description="A leather bag",
            location="loc_room",
            properties={
                "portable": True,
                "container": {
                    "is_surface": False,
                    "open": False,
                    "capacity": 5
                }
            }
        )

        # Container with "near" distance
        self.item_chest = Item(
            id="item_chest",
            name="chest",
            description="A large chest",
            location="loc_room",
            properties={
                "portable": False,
                "interaction_distance": "near",
                "container": {
                    "is_surface": False,
                    "open": False,
                    "capacity": 20
                }
            }
        )

        # Another "near" container for focus testing
        self.item_cabinet = Item(
            id="item_cabinet",
            name="cabinet",
            description="A wooden cabinet",
            location="loc_room",
            properties={
                "portable": False,
                "interaction_distance": "near",
                "container": {
                    "is_surface": False,
                    "open": False,
                    "capacity": 10
                }
            }
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item_bag, self.item_chest, self.item_cabinet],
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

    def test_open_any_distance_no_movement(self):
        """Test opening 'any' distance container doesn't move player."""
        player = self.accessor.get_actor("player")

        action = make_action(verb="open", object="bag")
        result = handle_open(self.accessor, action)

        self.assertTrue(result.success)
        # Should not include movement message
        self.assertNotIn("move", result.message.lower())
        self.assertNotIn("closer", result.message.lower())
        # Should set focus
        self.assertEqual(player.properties.get("focused_on"), "item_bag")
        # Container should be open
        bag = self.accessor.get_item("item_bag")
        self.assertTrue(bag.properties["container"]["open"])

    def test_open_near_distance_moves_player(self):
        """Test opening 'near' container moves player to it."""
        player = self.accessor.get_actor("player")

        action = make_action(verb="open", object="chest")
        result = handle_open(self.accessor, action)

        self.assertTrue(result.success)
        # Should include movement message
        self.assertIn("move", result.message.lower())
        # Should also include action result
        self.assertIn("open", result.message.lower())
        # Should set focus
        self.assertEqual(player.properties.get("focused_on"), "item_chest")
        # Container should be open
        chest = self.accessor.get_item("item_chest")
        self.assertTrue(chest.properties["container"]["open"])

    def test_open_already_focused_no_movement(self):
        """Test opening container when already there doesn't repeat movement."""
        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_chest"

        action = make_action(verb="open", object="chest")
        result = handle_open(self.accessor, action)

        self.assertTrue(result.success)
        # Should NOT include movement message
        self.assertNotIn("move", result.message.lower())

    def test_open_clears_posture_when_moving(self):
        """Test opening container clears posture when moving."""
        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_cabinet"
        player.properties["posture"] = "cover"

        # Open different container
        action = make_action(verb="open", object="chest")
        result = handle_open(self.accessor, action)

        self.assertTrue(result.success)
        # Posture should be cleared
        self.assertIsNone(player.properties.get("posture"))
        # Focus should change
        self.assertEqual(player.properties.get("focused_on"), "item_chest")

    def test_close_near_distance_moves_player(self):
        """Test closing 'near' container moves player to it."""
        player = self.accessor.get_actor("player")
        # Open it first
        chest = self.accessor.get_item("item_chest")
        chest.properties["container"]["open"] = True

        action = make_action(verb="close", object="chest")
        result = handle_close(self.accessor, action)

        self.assertTrue(result.success)
        # Should include movement message
        self.assertIn("move", result.message.lower())
        # Should set focus
        self.assertEqual(player.properties.get("focused_on"), "item_chest")
        # Container should be closed
        self.assertFalse(chest.properties["container"]["open"])

    def test_close_already_focused_no_movement(self):
        """Test closing container when already there doesn't repeat movement."""
        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_chest"
        # Open it first
        chest = self.accessor.get_item("item_chest")
        chest.properties["container"]["open"] = True

        action = make_action(verb="close", object="chest")
        result = handle_close(self.accessor, action)

        self.assertTrue(result.success)
        # Should NOT include movement message
        self.assertNotIn("move", result.message.lower())

    def test_close_any_distance_no_movement(self):
        """Test closing 'any' distance container doesn't move player."""
        player = self.accessor.get_actor("player")
        # Open it first
        bag = self.accessor.get_item("item_bag")
        bag.properties["container"]["open"] = True

        action = make_action(verb="close", object="bag")
        result = handle_close(self.accessor, action)

        self.assertTrue(result.success)
        # Should not include movement message
        self.assertNotIn("move", result.message.lower())
        # Should set focus
        self.assertEqual(player.properties.get("focused_on"), "item_bag")


if __name__ == '__main__':
    unittest.main()
