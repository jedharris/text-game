"""
Tests for take cover command.

Following TDD approach - these tests are written first before implementation.
"""
from src.types import ActorId
import unittest
from src.state_manager import GameState, Metadata, Location, Item, Actor, Part
from src.state_accessor import StateAccessor
from behaviors.core.spatial import handle_cover
from tests.conftest import make_action


class TestTakeCover(unittest.TestCase):
    """Test take cover command for tactical positioning."""

    def setUp(self):
        """Set up test game with cover objects."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A room"
        )

        # Item that provides cover
        self.cover_item = Item(
            id="item_pillar",
            name="pillar",
            description="A stone pillar",
            location="loc_room",
            _properties={
                "portable": False,
                "provides_cover": True
            }
        )

        # Item that doesn't provide cover
        self.no_cover_item = Item(
            id="item_chair",
            name="chair",
            description="A wooden chair",
            location="loc_room",
            _properties={"portable": False}
        )

        # Part that provides cover
        self.cover_part = Part(
            id="part_room_wall",
            name="wall",
            part_of="loc_room",
            _properties={
                "description": "A stone wall",
                "provides_cover": True
            }
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.cover_item, self.no_cover_item],
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
            parts=[self.cover_part]
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_take_cover_behind_item_succeeds(self):
        """Test taking cover behind item with provides_cover."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="cover", object="pillar")
        result = handle_cover(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("take cover", result.primary.lower())
        self.assertEqual(player.properties.get("focused_on"), "item_pillar")
        self.assertEqual(player.properties.get("posture"), "cover")

    def test_take_cover_behind_part_succeeds(self):
        """Test taking cover behind part with provides_cover."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="cover", object="wall")
        result = handle_cover(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("take cover", result.primary.lower())
        self.assertEqual(player.properties.get("focused_on"), "part_room_wall")
        self.assertEqual(player.properties.get("posture"), "cover")

    def test_take_cover_behind_non_cover_object_fails(self):
        """Test taking cover behind object without provides_cover fails."""
        action = make_action(verb="cover", object="chair")
        result = handle_cover(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("doesn't provide cover", result.primary.lower())

    def test_take_cover_behind_nonexistent_object_fails(self):
        """Test taking cover behind non-existent object fails."""
        action = make_action(verb="cover", object="boulder")
        result = handle_cover(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_take_cover_without_object_fails(self):
        """Test take cover without specifying object fails."""
        action = make_action(verb="cover")
        result = handle_cover(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("behind what", result.primary.lower())

    def test_take_cover_replaces_existing_posture(self):
        """Test taking cover replaces existing posture."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["posture"] = "climbing"

        action = make_action(verb="cover", object="pillar")
        result = handle_cover(self.accessor, action)

        self.assertTrue(result.success)
        # Posture should be replaced
        self.assertEqual(player.properties.get("posture"), "cover")

    def test_take_cover_includes_cover_in_data(self):
        """Test take cover includes cover entity in result data."""
        action = make_action(verb="cover", object="pillar")
        result = handle_cover(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data["id"], "item_pillar")
        self.assertEqual(result.data["posture"], "cover")

    def test_already_in_cover_at_same_object(self):
        """Test taking cover when already at same cover object."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_pillar"
        player.properties["posture"] = "cover"

        action = make_action(verb="cover", object="pillar")
        result = handle_cover(self.accessor, action)

        self.assertTrue(result.success)
        # Should still succeed (confirming cover position)
        self.assertEqual(player.properties.get("posture"), "cover")


if __name__ == '__main__':
    unittest.main()
