"""
Tests for StateAccessor part query methods.

Following TDD approach - these tests are written first before implementation.
"""
from src.types import ActorId
import unittest
from src.state_manager import Part, GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor


class TestStateAccessorParts(unittest.TestCase):
    """Test StateAccessor part query methods."""

    def setUp(self):
        """Set up test game state with parts."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Room",
            description="A test room"
        )

        self.part_wall = Part(
            id="part_room_north_wall",
            name="north wall",
            part_of="loc_room",
            _properties={"material": "stone"}
        )

        self.item = Item(
            id="item_bench",
            name="bench",
            description="A bench",
            location="loc_room"
        )

        self.part_bench = Part(
            id="part_bench_left",
            name="left side",
            part_of="item_bench"
        )

        self.item_at_part = Item(
            id="item_mortar",
            name="mortar",
            description="A stone mortar",
            location="part_bench_left"
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item, self.item_at_part],
            actors={"player": Actor(id="player", name="Player", description="The player", location="loc_room", inventory=[])},
            locks=[],
            parts=[self.part_wall, self.part_bench]
        )

        self.behavior_manager = None  # Not needed for these tests
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_get_part_by_id(self):
        """Test getting part by ID."""
        part = self.accessor.get_part("part_room_north_wall")

        self.assertIsNotNone(part)
        self.assertEqual(part.id, "part_room_north_wall")
        self.assertEqual(part.name, "north wall")

    def test_get_part_nonexistent(self):
        """Test getting non-existent part returns None."""
        part = self.accessor.get_part("part_nonexistent")
        self.assertIsNone(part)

    def test_get_parts_of_location(self):
        """Test getting all parts of a location."""
        parts = self.accessor.get_parts_of("loc_room")

        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0].id, "part_room_north_wall")

    def test_get_parts_of_item(self):
        """Test getting all parts of an item."""
        parts = self.accessor.get_parts_of("item_bench")

        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0].id, "part_bench_left")

    def test_get_parts_of_entity_with_no_parts(self):
        """Test getting parts of entity with no parts returns empty list."""
        parts = self.accessor.get_parts_of("item_mortar")
        self.assertEqual(parts, [])

    def test_get_items_at_part(self):
        """Test getting items located at a part."""
        items = self.accessor.get_items_at_part("part_bench_left")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "item_mortar")

    def test_get_items_at_part_with_no_items(self):
        """Test getting items at part with no items returns empty list."""
        items = self.accessor.get_items_at_part("part_room_north_wall")
        self.assertEqual(items, [])

    def test_get_entity_finds_part(self):
        """Test get_entity can find parts."""
        entity = self.accessor.get_entity("part_room_north_wall")

        self.assertIsNotNone(entity)
        self.assertIsInstance(entity, Part)
        self.assertEqual(entity.id, "part_room_north_wall")

    def test_get_entity_searches_all_types(self):
        """Test get_entity searches all entity types."""
        # Can find location
        self.assertIsNotNone(self.accessor.get_entity("loc_room"))

        # Can find item
        self.assertIsNotNone(self.accessor.get_entity("item_bench"))

        # Can find part
        self.assertIsNotNone(self.accessor.get_entity("part_room_north_wall"))

        # Can find actor
        self.assertIsNotNone(self.accessor.get_entity("player"))

    def test_get_focused_entity_returns_part(self):
        """Test get_focused_entity can return part."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "part_bench_left"

        focused = self.accessor.get_focused_entity("player")

        self.assertIsNotNone(focused)
        self.assertIsInstance(focused, Part)
        self.assertEqual(focused.id, "part_bench_left")

    def test_get_focused_entity_returns_item(self):
        """Test get_focused_entity can return item."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_bench"

        focused = self.accessor.get_focused_entity("player")

        self.assertIsNotNone(focused)
        self.assertIsInstance(focused, Item)
        self.assertEqual(focused.id, "item_bench")

    def test_get_focused_entity_no_focus(self):
        """Test get_focused_entity when actor not focused returns None."""
        focused = self.accessor.get_focused_entity("player")
        self.assertIsNone(focused)


if __name__ == '__main__':
    unittest.main()
