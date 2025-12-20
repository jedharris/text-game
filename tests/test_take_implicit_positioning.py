"""
Tests for implicit positioning in handle_take.

Following TDD approach - these tests are written first before implementation.
"""
from src.types import ActorId
import unittest
from src.state_manager import GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor
from behaviors.core.manipulation import handle_take
from tests.conftest import make_action


class TestTakeImplicitPositioning(unittest.TestCase):
    """Test implicit positioning with take command."""

    def setUp(self):
        """Set up test game with items at different distances."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A test room"
        )

        # Item with "any" distance (default)
        self.item_coin = Item(
            id="item_coin",
            name="coin",
            description="A gold coin",
            location="loc_room",
            properties={"portable": True}
        )

        # Item with "near" distance
        self.item_key = Item(
            id="item_key",
            name="key",
            description="A brass key",
            location="loc_room",
            properties={"portable": True, "interaction_distance": "near"}
        )

        # Item with "near" distance in container
        self.item_box = Item(
            id="item_box",
            name="box",
            description="A wooden box",
            location="loc_room",
            properties={
                "portable": False,
                "interaction_distance": "near",
                "container": {"open": True, "is_surface": False}
            }
        )

        self.item_gem = Item(
            id="item_gem",
            name="gem",
            description="A ruby gem",
            location="item_box",
            properties={"portable": True}
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item_coin, self.item_key, self.item_box, self.item_gem],
            actors={"player": Actor(id="player", name="Adventurer", description="The player", location="loc_room", inventory=[])},
            locks=[],
            parts=[]
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_take_any_distance_no_movement(self):
        """Test taking 'any' distance item doesn't move player."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="take", object="coin")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        # Should not include movement prefix
        self.assertNotIn("move", result.primary.lower())
        self.assertNotIn("closer", result.primary.lower())
        # Item should be taken
        self.assertIn("item_coin", player.inventory)
        # Focus should be set
        self.assertEqual(player.properties.get("focused_on"), "item_coin")

    def test_take_near_distance_moves_player(self):
        """Test taking 'near' item moves player to it."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="take", object="key")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        # Should include movement beat
        self.assertTrue(any("move" in beat.lower() for beat in result.beats))
        # Item should be taken
        self.assertIn("item_key", player.inventory)
        # Focus should be set
        self.assertEqual(player.properties.get("focused_on"), "item_key")

    def test_take_already_focused_no_movement(self):
        """Test taking item when already focused doesn't repeat movement."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_key"

        action = make_action(verb="take", object="key")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        # Should NOT include movement beat
        self.assertFalse(any("move" in beat.lower() for beat in result.beats))
        # Item should be taken
        self.assertIn("item_key", player.inventory)

    def test_take_clears_posture_when_moving(self):
        """Test taking item clears posture when moving."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_coin"
        player.properties["posture"] = "cover"

        action = make_action(verb="take", object="key")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        # Posture should be cleared
        self.assertIsNone(player.properties.get("posture"))

    def test_take_from_container_positions_to_container(self):
        """Test taking from container positions to container, not item."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="take", object="gem", preposition="from", indirect_object="box")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        # Should move to box (container), not gem (item being taken)
        self.assertTrue(any("move" in beat.lower() for beat in result.beats))
        self.assertEqual(player.properties.get("focused_on"), "item_box")
        # Item should be taken
        self.assertIn("item_gem", player.inventory)

    def test_take_from_container_already_at_container_no_movement(self):
        """Test taking from container when already at it doesn't move."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_box"

        action = make_action(verb="take", object="gem", preposition="from", indirect_object="box")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        # Should NOT move
        self.assertNotIn("move", result.primary.lower())
        # Item should be taken
        self.assertIn("item_gem", player.inventory)


if __name__ == '__main__':
    unittest.main()
