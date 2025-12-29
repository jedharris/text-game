"""
Tests for implicit positioning in handle_examine.

Following TDD approach - these tests are written first before implementation.
"""
from src.types import ActorId
import unittest
from src.state_manager import Part, GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor
from behaviors.core.perception import handle_examine
from tests.conftest import make_action


class TestExamineImplicitPositioning(unittest.TestCase):
    """Test implicit positioning with examine command."""

    def setUp(self):
        """Set up test game with entities at different distances."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A test room"
        )

        # Item with "any" distance (default)
        self.item_far = Item(
            id="item_chandelier",
            name="chandelier",
            description="A crystal chandelier hanging from the ceiling",
            location="loc_room"
            # No interaction_distance = defaults to "any"
        )

        # Item with "near" distance
        self.item_near = Item(
            id="item_desk",
            name="desk",
            description="A wooden desk with carved legs",
            location="loc_room",
            _properties={"interaction_distance": "near"}
        )

        # Part with "near" distance
        self.part = Part(
            id="part_room_north_wall",
            name="wall",
            part_of="loc_room",
            _properties={
                "description": "A stone wall with ancient carvings",
                "interaction_distance": "near"
            }
        )

        # Part of item (bench with parts)
        self.item_bench = Item(
            id="item_bench",
            name="bench",
            description="A long wooden bench",
            location="loc_room",
            _properties={"interaction_distance": "near"}
        )

        self.part_bench_left = Part(
            id="part_bench_left",
            name="left side of bench",
            part_of="item_bench",
            _properties={
                "description": "The left end of the bench, worn smooth by use"
            }
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item_far, self.item_near, self.item_bench],
            actors={"player": Actor(id="player", name="Adventurer", description="The player", location="loc_room", inventory=[])},
            locks=[],
            parts=[self.part, self.part_bench_left]
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_examine_any_distance_no_movement(self):
        """Test examining 'any' distance entity doesn't move player."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="examine", object="chandelier")

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should not include movement prefix
        self.assertNotIn("move", result.primary.lower())
        self.assertNotIn("approach", result.primary.lower())
        self.assertNotIn("closer", result.primary.lower())
        # Player focused_on should be set (examining focuses even without movement)
        self.assertEqual(player.properties.get("focused_on"), "item_chandelier")

    def test_examine_near_distance_moves_player(self):
        """Test examining 'near' entity moves player to it."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="examine", object="desk")

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should include movement prefix
        self.assertIn("move", result.primary.lower())
        # Should also include actual description
        self.assertIn("desk", result.primary.lower())
        # Player focused_on should be set
        self.assertEqual(player.properties.get("focused_on"), "item_desk")

    def test_examine_near_already_focused_no_movement(self):
        """Test examining near entity when already there doesn't repeat movement."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_desk"

        action = make_action(verb="examine", object="desk")

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should NOT include movement prefix
        self.assertNotIn("move", result.primary.lower())

    def test_examine_part_with_near_moves_player(self):
        """Test examining part with 'near' moves player."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="examine", object="wall")

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("move", result.primary.lower())
        self.assertEqual(player.properties.get("focused_on"), "part_room_north_wall")

    def test_implicit_movement_clears_posture(self):
        """Test implicit movement clears posture."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_chandelier"
        player.properties["posture"] = "cover"

        # Examine different near entity
        action = make_action(verb="examine", object="desk")

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Posture should be cleared
        self.assertIsNone(player.properties.get("posture"))

    def test_examine_part_lists_items_at_part(self):
        """Test examining part lists items located at that part."""
        # Add item at part
        item_at_wall = Item(
            id="item_tapestry",
            name="tapestry",
            description="A faded tapestry",
            location="part_room_north_wall"
        )
        self.game_state.items.append(item_at_wall)

        action = make_action(verb="examine", object="wall")

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should mention the tapestry
        self.assertIn("tapestry", result.primary.lower())

    def test_examine_part_of_item(self):
        """Test examining part of an item (multi-sided object)."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="examine", object="left side of bench")

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("left end", result.primary.lower())
        # Player should be focused on the part
        self.assertEqual(player.properties.get("focused_on"), "part_bench_left")

    def test_examine_item_then_part_moves_focus(self):
        """Test examining item then its part updates focus."""
        player = self.accessor.get_actor(ActorId("player"))

        # First examine the bench
        action1 = make_action(verb="examine", object="bench")
        result1 = handle_examine(self.accessor, action1)
        self.assertTrue(result1.success)
        self.assertEqual(player.properties.get("focused_on"), "item_bench")

        # Then examine the part of the bench
        action2 = make_action(verb="examine", object="left side of bench")
        result2 = handle_examine(self.accessor, action2)
        self.assertTrue(result2.success)
        # Focus should change to the part
        self.assertEqual(player.properties.get("focused_on"), "part_bench_left")


if __name__ == '__main__':
    unittest.main()
