"""
Tests for universal surface fallback in handle_examine.

Following TDD approach - these tests are written first before implementation.
"""
from src.types import ActorId
import unittest
from src.state_manager import GameState, Metadata, Location, Item, Actor, Part
from src.state_accessor import StateAccessor
from behaviors.core.perception import handle_examine
from tests.conftest import make_action


class TestUniversalSurfaceFallback(unittest.TestCase):
    """Test examine command falls back to universal surfaces when entity not found."""

    def setUp(self):
        """Set up test game without explicit ceiling/floor parts."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Simple Room",
            description="A simple room"
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[],
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
            parts=[]  # No parts defined
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_examine_ceiling_without_part_uses_fallback(self):
        """Test examining ceiling without explicit part uses fallback."""
        action = make_action(verb="examine", object="ceiling")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("ceiling", result.primary.lower())
        # Should not say "don't see"
        self.assertNotIn("don't see", result.primary.lower())

    def test_examine_floor_without_part_uses_fallback(self):
        """Test examining floor without explicit part uses fallback."""
        action = make_action(verb="examine", object="floor")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("floor", result.primary.lower())
        self.assertNotIn("don't see", result.primary.lower())

    def test_examine_sky_without_part_uses_fallback(self):
        """Test examining sky without explicit part uses fallback."""
        action = make_action(verb="examine", object="sky")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("sky", result.primary.lower())
        self.assertNotIn("don't see", result.primary.lower())

    def test_examine_walls_without_part_uses_fallback(self):
        """Test examining walls without explicit part uses fallback."""
        action = make_action(verb="examine", object="walls")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("walls", result.primary.lower())
        self.assertNotIn("don't see", result.primary.lower())

    def test_examine_ground_synonym_uses_fallback(self):
        """Test examining ground (synonym for floor) uses fallback."""
        action = make_action(verb="examine", object="ground")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should mention floor or ground
        self.assertTrue(
            "floor" in result.primary.lower() or "ground" in result.primary.lower()
        )
        self.assertNotIn("don't see", result.primary.lower())

    def test_examine_nonexistent_non_surface_still_fails(self):
        """Test examining non-existent non-surface still fails."""
        action = make_action(verb="examine", object="unicorn")
        result = handle_examine(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_universal_surface_fallback_does_not_set_focus(self):
        """Test examining universal surface fallback doesn't set focus."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="examine", object="ceiling")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Universal surface fallback should not set focus (no real entity)
        self.assertIsNone(player.properties.get("focused_on"))

    def test_universal_surface_fallback_no_movement_message(self):
        """Test universal surface fallback doesn't generate movement message."""
        action = make_action(verb="examine", object="floor")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should not include movement message
        self.assertNotIn("move", result.primary.lower())
        self.assertNotIn("closer", result.primary.lower())


class TestExplicitPartOverridesUniversalSurface(unittest.TestCase):
    """Test explicit parts override universal surface fallbacks."""

    def setUp(self):
        """Set up test game with explicit ceiling part."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Ornate Room",
            description="A room with detailed decorations"
        )

        # Add explicit ceiling part with custom description
        self.ceiling_part = Part(
            id="part_room_ceiling",
            name="ceiling",
            part_of="loc_room",
            properties={
                "description": "A magnificent vaulted ceiling with colorful frescoes depicting ancient battles."
            }
        )

        # Add explicit floor part
        self.floor_part = Part(
            id="part_room_floor",
            name="floor",
            part_of="loc_room",
            properties={
                "description": "Polished marble tiles arranged in intricate geometric patterns.",
                "interaction_distance": "any"
            }
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[],
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
            parts=[self.ceiling_part, self.floor_part]
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_explicit_ceiling_part_overrides_fallback(self):
        """Test explicit ceiling part overrides universal fallback."""
        action = make_action(verb="examine", object="ceiling")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should use explicit description, not fallback
        self.assertIn("vaulted", result.primary.lower())
        self.assertIn("frescoes", result.primary.lower())
        # Should NOT contain fallback text
        self.assertNotIn("nothing remarkable", result.primary.lower())

    def test_explicit_floor_part_overrides_fallback(self):
        """Test explicit floor part overrides universal fallback."""
        action = make_action(verb="examine", object="floor")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should use explicit description
        self.assertIn("marble", result.primary.lower())
        self.assertIn("geometric", result.primary.lower())
        # Should NOT contain fallback text
        self.assertNotIn("nothing remarkable", result.primary.lower())

    def test_explicit_part_sets_focus(self):
        """Test examining explicit part sets focus."""
        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="examine", object="ceiling")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Explicit part should set focus
        self.assertEqual(player.properties.get("focused_on"), "part_room_ceiling")

    def test_explicit_part_with_near_distance_moves_player(self):
        """Test explicit part with 'near' distance triggers positioning."""
        # Add a part with "near" distance
        wall_part = Part(
            id="part_room_wall",
            name="wall",
            part_of="loc_room",
            properties={
                "description": "The wall has intricate carvings.",
                "interaction_distance": "near"
            }
        )
        self.game_state.parts.append(wall_part)

        player = self.accessor.get_actor(ActorId("player"))

        action = make_action(verb="examine", object="wall")
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should include movement message
        self.assertIn("move", result.primary.lower())
        # Should set focus
        self.assertEqual(player.properties.get("focused_on"), "part_room_wall")


if __name__ == '__main__':
    unittest.main()
