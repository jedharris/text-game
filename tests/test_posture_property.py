"""
Tests for posture property semantics.

The posture property tracks an actor's special positioning mode
(cover, concealed, climbing, etc.) and is automatically cleared when moving.
"""
from src.types import ActorId
import unittest
from src.state_manager import GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor
from behaviors.core.perception import handle_examine
from tests.conftest import make_action


class TestPostureProperty(unittest.TestCase):
    """Test posture property semantics and behavior."""

    def test_actor_defaults_to_no_posture(self):
        """Test actors default to no posture."""
        actor = Actor(
            id="player",
            name="Player",
            description="Test player",
            location="loc_room",
            inventory=[]
        )

        posture = actor.properties.get("posture")
        self.assertIsNone(posture)

    def test_actor_can_have_posture(self):
        """Test actor can have posture property."""
        actor = Actor(
            id="player",
            name="Player",
            description="Test player",
            location="loc_room",
            inventory=[]
        )
        actor.properties["posture"] = "cover"

        self.assertEqual(actor.properties["posture"], "cover")

    def test_posture_can_be_cleared(self):
        """Test posture can be deleted/cleared."""
        actor = Actor(
            id="player",
            name="Player",
            description="Test player",
            location="loc_room",
            inventory=[]
        )
        actor.properties["posture"] = "cover"
        del actor.properties["posture"]

        self.assertIsNone(actor.properties.get("posture"))

    def test_posture_values_can_be_any_string(self):
        """Test posture supports standard and custom values."""
        actor = Actor(
            id="player",
            name="Player",
            description="Test player",
            location="loc_room",
            inventory=[]
        )

        # Standard values
        actor.properties["posture"] = "cover"
        self.assertEqual(actor.properties["posture"], "cover")

        actor.properties["posture"] = "concealed"
        self.assertEqual(actor.properties["posture"], "concealed")

        actor.properties["posture"] = "climbing"
        self.assertEqual(actor.properties["posture"], "climbing")

        # Custom values
        actor.properties["posture"] = "crouching"
        self.assertEqual(actor.properties["posture"], "crouching")


class TestPostureClearingOnMovement(unittest.TestCase):
    """Test posture is cleared when actor moves to different entity."""

    def setUp(self):
        """Set up test game with multiple entities."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A test room"
        )

        # Multiple items to move between
        self.item_desk = Item(
            id="item_desk",
            name="desk",
            description="A wooden desk",
            location="loc_room",
            properties={"interaction_distance": "near"}
        )

        self.item_shelf = Item(
            id="item_shelf",
            name="shelf",
            description="A bookshelf",
            location="loc_room",
            properties={"interaction_distance": "near"}
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item_desk, self.item_shelf],
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

    def test_posture_cleared_when_moving_between_entities(self):
        """Test posture cleared when examining different entity with movement."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_desk"
        player.properties["posture"] = "cover"

        # Move to different entity
        action = make_action(verb="examine", object="shelf")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Posture should be cleared
        self.assertIsNone(player.properties.get("posture"))
        # Focus should change
        self.assertEqual(player.properties.get("focused_on"), "item_shelf")

    def test_posture_preserved_when_reexamining_same_entity(self):
        """Test posture preserved when examining same focused entity."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["focused_on"] = "item_desk"
        player.properties["posture"] = "cover"

        # Examine same entity
        action = make_action(verb="examine", object="desk")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Posture should be preserved (no movement)
        self.assertEqual(player.properties.get("posture"), "cover")
        # Focus unchanged
        self.assertEqual(player.properties.get("focused_on"), "item_desk")

    def test_posture_preserved_when_no_movement_occurs(self):
        """Test posture preserved when examining 'any' distance item (no movement)."""
        player = self.accessor.get_actor(ActorId("player"))

        # Add item with "any" distance (no movement)
        item_chandelier = Item(
            id="item_chandelier",
            name="chandelier",
            description="A crystal chandelier",
            location="loc_room"
            # No interaction_distance = defaults to "any"
        )
        self.game_state.items.append(item_chandelier)

        # Set initial state with cover
        player.properties["focused_on"] = "item_desk"
        player.properties["posture"] = "cover"

        # Examine "any" distance item (focus changes but no movement)
        action = make_action(verb="examine", object="chandelier")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Posture should be PRESERVED since no movement occurred
        # (only cleared on actual movement to "near" entities)
        self.assertEqual(player.properties.get("posture"), "cover")
        # Focus should change
        self.assertEqual(player.properties.get("focused_on"), "item_chandelier")


if __name__ == '__main__':
    unittest.main()
