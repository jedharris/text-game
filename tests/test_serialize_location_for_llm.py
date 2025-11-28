"""Tests for serialize_location_for_llm function.

Verifies that the unified location serialization produces consistent output
suitable for LLM consumption, matching what _query_location returns.
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_manager import load_game_state, Location
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from utilities.location_serializer import serialize_location_for_llm


class TestSerializeLocationForLlmStructure(unittest.TestCase):
    """Test the structure of serialize_location_for_llm output."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "llm_interaction" / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_returns_dict_with_location_key(self):
        """Test that result has location key with full entity fields."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        self.assertIn("location", result)
        self.assertIn("id", result["location"])
        self.assertIn("name", result["location"])
        self.assertEqual(result["location"]["id"], "loc_start")
        self.assertEqual(result["location"]["name"], "Small Room")

    def test_location_includes_llm_context(self):
        """Test that location includes llm_context when present."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        self.assertIn("location", result)
        self.assertIn("llm_context", result["location"])

    def test_returns_items_list(self):
        """Test that result includes items list."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        # Should always have items key (may be empty list)
        self.assertIn("items", result)
        self.assertIsInstance(result["items"], list)

    def test_returns_actors_list(self):
        """Test that result includes actors list."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        # Should always have actors key (may be empty list)
        self.assertIn("actors", result)
        self.assertIsInstance(result["actors"], list)

    def test_returns_doors_list(self):
        """Test that result includes doors list."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        # Should always have doors key (may be empty list)
        self.assertIn("doors", result)
        self.assertIsInstance(result["doors"], list)

    def test_returns_exits_dict(self):
        """Test that result includes exits dict."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        # Should always have exits key (may be empty dict)
        self.assertIn("exits", result)
        self.assertIsInstance(result["exits"], dict)


class TestSerializeLocationForLlmItems(unittest.TestCase):
    """Test item serialization in serialize_location_for_llm."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "llm_interaction" / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_items_have_full_entity_fields(self):
        """Test that items have all standard entity fields."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        if result["items"]:
            for item in result["items"]:
                self.assertIn("id", item, f"Item missing 'id': {item}")
                self.assertIn("name", item, f"Item missing 'name': {item}")

    def test_items_include_llm_context(self):
        """Test that items include llm_context when present."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        # At least one item should have llm_context if fixture has items with traits
        items_with_context = [i for i in result["items"] if "llm_context" in i]
        # This depends on fixture - just verify structure is correct
        for item in items_with_context:
            self.assertIsInstance(item["llm_context"], dict)


class TestSerializeLocationForLlmActors(unittest.TestCase):
    """Test actor serialization in serialize_location_for_llm."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "llm_interaction" / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_actors_have_full_entity_fields(self):
        """Test that actors have all standard entity fields."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        # Actors list may exclude the player (viewer)
        for actor in result["actors"]:
            self.assertIn("id", actor, f"Actor missing 'id': {actor}")
            self.assertIn("name", actor, f"Actor missing 'name': {actor}")


class TestSerializeLocationForLlmDoors(unittest.TestCase):
    """Test door serialization in serialize_location_for_llm."""

    def setUp(self):
        """Set up test fixtures with doors."""
        fixture_path = Path(__file__).parent / "llm_interaction" / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_doors_include_direction(self):
        """Test that doors include direction field."""
        # Need to find a location with doors
        for location in self.state.locations:
            result = serialize_location_for_llm(self.accessor, location, "player")
            if result["doors"]:
                for door in result["doors"]:
                    self.assertIn("direction", door,
                                  f"Door missing 'direction': {door}")
                return  # Found doors, test passed

        # If no doors in fixture, skip this test
        self.skipTest("No doors in test fixture")


class TestSerializeLocationForLlmExits(unittest.TestCase):
    """Test exit serialization in serialize_location_for_llm."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "llm_interaction" / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_exits_keyed_by_direction(self):
        """Test that exits are keyed by direction."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        # Exits should be a dict with direction keys
        if result["exits"]:
            for direction, exit_data in result["exits"].items():
                self.assertIsInstance(direction, str)
                self.assertIn("type", exit_data)
                self.assertIn("to", exit_data)

    def test_exits_include_door_id_when_present(self):
        """Test that exits include door_id when there's a door."""
        # Look for an exit with a door
        for location in self.state.locations:
            result = serialize_location_for_llm(self.accessor, location, "player")
            for direction, exit_data in result["exits"].items():
                if "door_id" in exit_data:
                    # Found one - verify structure
                    self.assertIsInstance(exit_data["door_id"], str)
                    return

        # If no door exits in fixture, that's ok
        pass


class TestSerializeLocationConsistentWithQueryLocation(unittest.TestCase):
    """Test that serialize_location_for_llm matches _query_location output."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "llm_interaction" / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_same_top_level_keys_as_query(self):
        """Test that result has same top-level keys as _query_location."""
        location = self.state.get_location("loc_start")

        result = serialize_location_for_llm(self.accessor, location, "player")

        # _query_location returns: location, items, doors, exits, actors
        expected_keys = {"location", "items", "doors", "exits", "actors"}
        self.assertEqual(set(result.keys()), expected_keys)


if __name__ == '__main__':
    unittest.main()
