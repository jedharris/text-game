"""Tests for Exit entity type and containment index integration."""
import unittest

from src.state_manager import GameState, Exit
from src.types import ActorId, LocationId
from tests.conftest import BaseTestCase


class TestExitEntity(BaseTestCase):
    """Test Exit entity type and containment index integration."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()

    def test_exit_creation_with_all_fields(self):
        """Test Exit entity can be created with all fields."""
        exit_entity = Exit(
            id="exit_forest_north",
            name="cave entrance",
            location="loc_forest",
            connections=["exit_cave_south"],
            direction="north",
            description="A dark narrow opening in the hillside",
            adjectives=["dark", "narrow"],
            synonyms=["opening", "passage"],
            properties={"hidden": False},
            behaviors=["behaviors.core.exits"],
            traits={"atmosphere": "foreboding"}
        )

        self.assertEqual(exit_entity.id, "exit_forest_north")
        self.assertEqual(exit_entity.name, "cave entrance")
        self.assertEqual(exit_entity.location, "loc_forest")
        self.assertEqual(exit_entity.connections, ["exit_cave_south"])
        self.assertEqual(exit_entity.direction, "north")
        self.assertEqual(exit_entity.description, "A dark narrow opening in the hillside")
        self.assertEqual(exit_entity.adjectives, ["dark", "narrow"])
        self.assertEqual(exit_entity.synonyms, ["opening", "passage"])
        self.assertEqual(exit_entity.properties, {"hidden": False})
        self.assertEqual(exit_entity.behaviors, ["behaviors.core.exits"])
        self.assertEqual(exit_entity.traits, {"atmosphere": "foreboding"})

    def test_exit_creation_with_minimal_fields(self):
        """Test Exit entity can be created with only required fields."""
        exit_entity = Exit(
            id="exit_room_a_north",
            name="doorway",
            location="loc_room_a",
            connections=["exit_room_b_south"]
        )

        self.assertEqual(exit_entity.id, "exit_room_a_north")
        self.assertEqual(exit_entity.name, "doorway")
        self.assertEqual(exit_entity.location, "loc_room_a")
        self.assertEqual(exit_entity.connections, ["exit_room_b_south"])
        self.assertIsNone(exit_entity.direction)
        self.assertEqual(exit_entity.description, "")
        self.assertEqual(exit_entity.adjectives, [])
        self.assertEqual(exit_entity.synonyms, [])
        self.assertEqual(exit_entity.properties, {})
        self.assertEqual(exit_entity.behaviors, [])
        self.assertEqual(exit_entity.traits, {})

    def test_exit_without_direction_portal_case(self):
        """Test exit works without direction (portal/non-directional case)."""
        exit_entity = Exit(
            id="exit_portal_1",
            name="shimmering portal",
            location="loc_wizard_tower",
            connections=["exit_portal_2"],
            direction=None
        )

        self.assertIsNone(exit_entity.direction)
        self.assertEqual(exit_entity.name, "shimmering portal")

    def test_exit_with_multiple_connections(self):
        """Test exit can have multiple connections (future doorway case)."""
        exit_entity = Exit(
            id="exit_hallway_east",
            name="wooden door",
            location="loc_hallway",
            connections=["exit_library_west", "doorway_123"]
        )

        self.assertEqual(len(exit_entity.connections), 2)
        self.assertIn("exit_library_west", exit_entity.connections)
        self.assertIn("doorway_123", exit_entity.connections)

    def test_exits_list_in_game_state(self):
        """Test GameState has exits list."""
        self.assertIsNotNone(self.game_state.exits)
        self.assertIsInstance(self.game_state.exits, list)

    def test_get_exit_by_id(self):
        """Test get_exit() returns correct exit."""
        # Add exit to game state
        exit_entity = Exit(
            id="exit_test_north",
            name="test exit",
            location="loc_test",
            connections=["exit_test_south"]
        )
        self.game_state.exits.append(exit_entity)

        # Retrieve it
        retrieved = self.game_state.get_exit("exit_test_north")
        self.assertEqual(retrieved.id, "exit_test_north")
        self.assertEqual(retrieved.name, "test exit")

    def test_get_exit_not_found_raises_keyerror(self):
        """Test get_exit() fails fast for missing exit."""
        with self.assertRaises(KeyError) as context:
            self.game_state.get_exit("exit_nonexistent")

        self.assertIn("Exit not found", str(context.exception))
        self.assertIn("exit_nonexistent", str(context.exception))

    def test_exit_in_containment_index(self):
        """Test exits are indexed in _entities_at."""
        # Add exit to game state
        exit_entity = Exit(
            id="exit_garden_north",
            name="garden gate",
            location="loc_garden",
            connections=["exit_meadow_south"]
        )
        self.game_state.exits.append(exit_entity)

        # Manually rebuild index (normally done at load time)
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Check index
        entities_at_garden = self.game_state._entities_at.get("loc_garden", set())
        self.assertIn("exit_garden_north", entities_at_garden)

        # Check reverse lookup
        where = self.game_state._entity_where.get("exit_garden_north")
        self.assertEqual(where, "loc_garden")

    def test_get_entities_at_filters_by_exit_type(self):
        """Test get_entities_at can filter by entity_type='exit'."""
        # Add exit and item to same location
        exit_entity = Exit(
            id="exit_hall_east",
            name="archway",
            location="loc_hall",
            connections=["exit_room_west"]
        )
        self.game_state.exits.append(exit_entity)

        # Rebuild index
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Get only exits
        exits_at_hall = self.accessor.get_entities_at("loc_hall", entity_type="exit")

        # Should find the exit
        exit_ids = [e.id for e in exits_at_hall]
        self.assertIn("exit_hall_east", exit_ids)

        # Verify it's an Exit instance
        self.assertTrue(all(isinstance(e, Exit) for e in exits_at_hall))


if __name__ == '__main__':
    unittest.main()
