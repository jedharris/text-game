"""
Tests for hide and climb posture commands.

Following TDD approach - these tests are written first before implementation.
"""
from src.types import ActorId
import unittest
from src.state_manager import GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor
from behaviors.core.spatial import handle_hide_in, handle_climb
from tests.conftest import make_action


class TestHideCommand(unittest.TestCase):
    """Test hide command for concealment."""

    def setUp(self):
        """Set up test game with hiding spots."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A room"
        )

        # Container that allows concealment
        self.hiding_spot = Item(
            id="item_wardrobe",
            name="wardrobe",
            description="A large wardrobe",
            location="loc_room",
            properties={
                "portable": False,
                "allows_concealment": True
            }
        )

        # Item that doesn't allow concealment
        self.no_hiding = Item(
            id="item_table",
            name="table",
            description="A wooden table",
            location="loc_room",
            properties={"portable": False}
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.hiding_spot, self.no_hiding],
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

    def test_hide_in_wardrobe_succeeds(self):
        """Test hiding in object with allows_concealment."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="hide", indirect_object="wardrobe")
        result = handle_hide_in(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("hide", result.primary.lower())
        self.assertEqual(player.properties.get("focused_on"), "item_wardrobe")
        self.assertEqual(player.properties.get("posture"), "concealed")

    def test_hide_in_non_concealable_fails(self):
        """Test hiding in object without allows_concealment fails."""
        action = make_action(verb="hide", indirect_object="table")
        result = handle_hide_in(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't hide", result.primary.lower())

    def test_hide_in_nonexistent_fails(self):
        """Test hiding in non-existent object fails."""
        action = make_action(verb="hide", indirect_object="closet")
        result = handle_hide_in(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_hide_without_object_fails(self):
        """Test hide without specifying object fails."""
        action = make_action(verb="hide")
        result = handle_hide_in(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("hide in what", result.primary.lower())

    def test_hide_replaces_existing_posture(self):
        """Test hiding replaces existing posture."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["posture"] = "cover"

        action = make_action(verb="hide", indirect_object="wardrobe")
        result = handle_hide_in(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(player.properties.get("posture"), "concealed")

    def test_hide_includes_hiding_spot_in_data(self):
        """Test hide includes hiding spot in result data."""
        action = make_action(verb="hide", indirect_object="wardrobe")
        result = handle_hide_in(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data["id"], "item_wardrobe")
        self.assertEqual(result.data["posture"], "concealed")


class TestClimbCommand(unittest.TestCase):
    """Test climb command for vertical positioning."""

    def setUp(self):
        """Set up test game with climbable objects."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A room"
        )

        # Climbable object
        self.climbable = Item(
            id="item_ladder",
            name="ladder",
            description="A wooden ladder",
            location="loc_room",
            properties={
                "portable": False,
                "climbable": True
            }
        )

        # Non-climbable object
        self.not_climbable = Item(
            id="item_desk",
            name="desk",
            description="A wooden desk",
            location="loc_room",
            properties={"portable": False}
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.climbable, self.not_climbable],
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

    def test_climb_ladder_succeeds(self):
        """Test climbing object with climbable property."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="climb", object="ladder")
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("climb", result.primary.lower())
        self.assertEqual(player.properties.get("focused_on"), "item_ladder")
        self.assertEqual(player.properties.get("posture"), "climbing")

    def test_climb_non_climbable_fails(self):
        """Test climbing non-climbable object fails."""
        action = make_action(verb="climb", object="desk")
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't climb", result.primary.lower())

    def test_climb_nonexistent_fails(self):
        """Test climbing non-existent object fails."""
        action = make_action(verb="climb", object="tree")
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_climb_without_object_fails(self):
        """Test climb without specifying object fails."""
        action = make_action(verb="climb")
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what do you want to climb", result.primary.lower())

    def test_climb_replaces_existing_posture(self):
        """Test climbing replaces existing posture."""
        player = self.accessor.get_actor(ActorId("player"))
        player.properties["posture"] = "cover"

        action = make_action(verb="climb", object="ladder")
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(player.properties.get("posture"), "climbing")

    def test_climb_includes_object_in_data(self):
        """Test climb includes climbable object in result data."""
        action = make_action(verb="climb", object="ladder")
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data["id"], "item_ladder")
        self.assertEqual(result.data["posture"], "climbing")


if __name__ == '__main__':
    unittest.main()
