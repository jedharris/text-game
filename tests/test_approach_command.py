"""
Tests for approach command (explicit positioning).

Following TDD approach - these tests are written first before implementation.
"""
import unittest
from src.state_manager import Part, GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor
from behaviors.core.spatial import handle_approach
from tests.conftest import make_action


class TestApproachCommand(unittest.TestCase):
    """Test approach command for explicit positioning."""

    def setUp(self):
        """Set up test game with various entities."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A test room"
        )

        # Item to approach
        self.item_bench = Item(
            id="item_bench",
            name="bench",
            description="A wooden bench",
            location="loc_room"
        )

        # Another item for testing focus changes
        self.item_desk = Item(
            id="item_desk",
            name="desk",
            description="A desk",
            location="loc_room"
        )

        # Part of location
        self.part_wall = Part(
            id="part_room_north_wall",
            name="north wall",
            part_of="loc_room",
            properties={"description": "A stone wall"}
        )

        # Part of item
        self.part_bench_left = Part(
            id="part_bench_left",
            name="left side of bench",
            part_of="item_bench",
            properties={"description": "The left end of the bench"}
        )

        # NPC actor
        self.npc = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="loc_room",
            inventory=[]
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item_bench, self.item_desk],
            actors={
                "player": Actor(
                    id="player",
                    name="Adventurer",
                    description="The player",
                    location="loc_room",
                    inventory=[]
                ),
                "npc_guard": self.npc
            },
            locks=[],
            parts=[self.part_wall, self.part_bench_left]
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_approach_item_sets_focus(self):
        """Test approaching item sets focused_on."""
        player = self.accessor.get_actor("player")

        action = make_action(verb="approach", object="bench")
        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("move", result.message.lower())
        self.assertEqual(player.properties.get("focused_on"), "item_bench")

    def test_approach_already_there(self):
        """Test approaching when already focused gives 'already there' message."""
        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_bench"

        action = make_action(verb="approach", object="bench")
        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("already", result.message.lower())
        self.assertEqual(player.properties.get("focused_on"), "item_bench")

    def test_approach_part_of_location(self):
        """Test approaching part of location."""
        player = self.accessor.get_actor("player")

        action = make_action(verb="approach", object="north wall")
        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(player.properties.get("focused_on"), "part_room_north_wall")

    def test_approach_part_of_item(self):
        """Test approaching part of item."""
        player = self.accessor.get_actor("player")

        action = make_action(verb="approach", object="left side of bench")
        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(player.properties.get("focused_on"), "part_bench_left")

    def test_approach_actor(self):
        """Test approaching another actor (NPC)."""
        player = self.accessor.get_actor("player")

        action = make_action(verb="approach", object="guard")
        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(player.properties.get("focused_on"), "npc_guard")

    def test_approach_clears_posture(self):
        """Test approach clears posture when moving."""
        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_bench"
        player.properties["posture"] = "cover"

        # Approach different entity
        action = make_action(verb="approach", object="desk")
        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNone(player.properties.get("posture"))

    def test_approach_nonexistent_entity(self):
        """Test approach of non-existent entity fails."""
        action = make_action(verb="approach", object="unicorn")
        result = handle_approach(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_approach_no_object(self):
        """Test approach without object fails with helpful message."""
        action = make_action(verb="approach")
        result = handle_approach(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.message.lower())

    def test_approach_changes_focus_from_one_entity_to_another(self):
        """Test approach updates focus when moving between entities."""
        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_bench"

        action = make_action(verb="approach", object="desk")
        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(player.properties.get("focused_on"), "item_desk")
        self.assertNotEqual(player.properties.get("focused_on"), "item_bench")

    def test_approach_serializes_target_for_llm(self):
        """Test approach includes target data for LLM context."""
        action = make_action(verb="approach", object="bench")
        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data["id"], "item_bench")


if __name__ == '__main__':
    unittest.main()
