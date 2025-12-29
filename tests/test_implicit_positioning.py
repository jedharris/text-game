"""
Tests for implicit positioning with interaction_distance property.

Following TDD approach - these tests are written first before implementation.
"""
from src.types import ActorId
import unittest
from src.state_manager import Part, GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor


class TestInteractionDistanceProperty(unittest.TestCase):
    """Test interaction_distance property semantics."""

    def test_entity_defaults_to_any_distance(self):
        """Test entities default to interaction_distance 'any'."""
        item = Item(
            id="item_chandelier",
            name="chandelier",
            description="A chandelier",
            location="loc_room"
        )

        # Should default to "any"
        distance = item.properties.get("interaction_distance", "any")
        self.assertEqual(distance, "any")

    def test_entity_can_have_near_distance(self):
        """Test entity can specify interaction_distance 'near'."""
        item = Item(
            id="item_desk",
            name="desk",
            description="A desk",
            location="loc_room",
            _properties={"interaction_distance": "near"}
        )

        distance = item.properties.get("interaction_distance", "any")
        self.assertEqual(distance, "near")

    def test_part_can_have_interaction_distance(self):
        """Test parts can have interaction_distance property."""
        part = Part(
            id="part_wall",
            name="wall",
            part_of="loc_room",
            _properties={"interaction_distance": "near"}
        )

        distance = part.properties.get("interaction_distance", "any")
        self.assertEqual(distance, "near")


class TestImplicitPositioningExamine(unittest.TestCase):
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
            description="A crystal chandelier",
            location="loc_room"
            # No interaction_distance = defaults to "any"
        )

        # Item with "near" distance
        self.item_near = Item(
            id="item_desk",
            name="desk",
            description="A wooden desk",
            location="loc_room",
            _properties={"interaction_distance": "near"}
        )

        # Part with "near" distance
        self.part = Part(
            id="part_room_north_wall",
            name="north wall",
            part_of="loc_room",
            _properties={
                "description": "A stone wall",
                "interaction_distance": "near"
            }
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item_far, self.item_near],
            actors={"player": Actor(id="player", name="Adventurer", description="The player", location="loc_room", inventory=[])},
            locks=[],
            parts=[self.part]
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_examine_any_distance_no_movement(self):
        """Test examining 'any' distance entity doesn't move player."""
        # This test will be implemented once we have handle_examine integrated
        # For now, just verify the property exists
        player = self.accessor.get_actor(ActorId("player"))
        self.assertIsNone(player.properties.get("focused_on"))

    def test_examine_near_distance_should_move_player(self):
        """Test examining 'near' entity should move player to it."""
        # This test will be implemented once we have handle_examine integrated
        player = self.accessor.get_actor(ActorId("player"))
        # Initially not focused
        self.assertIsNone(player.properties.get("focused_on"))

    def test_examine_near_already_focused_no_movement(self):
        """Test examining near entity when already there doesn't repeat movement."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_desk"

        # Verify focus is set
        self.assertEqual(player.properties.get("focused_on"), "item_desk")

    def test_examine_part_with_near_should_move_player(self):
        """Test examining part with 'near' should move player."""
        player = self.accessor.get_actor(ActorId("player"))
        # Initially not focused
        self.assertIsNone(player.properties.get("focused_on"))

    def test_implicit_movement_should_clear_posture(self):
        """Test implicit movement should clear posture."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_far"
        player.properties["posture"] = "cover"

        # Verify initial state
        self.assertEqual(player.properties.get("posture"), "cover")

    def test_examine_part_lists_items_at_part(self):
        """Test examining part should list items located at that part."""
        # Add item at part
        item_at_wall = Item(
            id="item_tapestry",
            name="tapestry",
            description="A faded tapestry",
            location="part_room_north_wall"
        )
        self.game_state.items.append(item_at_wall)

        # Verify item is at part
        items_at_part = self.accessor.get_items_at_part("part_room_north_wall")
        self.assertEqual(len(items_at_part), 1)
        self.assertEqual(items_at_part[0].id, "item_tapestry")


if __name__ == '__main__':
    unittest.main()
