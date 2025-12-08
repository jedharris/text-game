"""
Tests for Part entity infrastructure.

Following TDD approach - these tests are written first before implementation.
"""
import unittest
import json
import tempfile
import os
from src.state_manager import Part, GameState, Metadata, Location, load_game_state


class TestPartEntity(unittest.TestCase):
    """Test Part dataclass functionality."""

    def test_part_creation(self):
        """Test basic Part entity creation."""
        part = Part(
            id="part_throne_north_wall",
            name="north wall",
            part_of="loc_throne_room",
            properties={"material": "stone"},
            behaviors=[]
        )

        self.assertEqual(part.id, "part_throne_north_wall")
        self.assertEqual(part.name, "north wall")
        self.assertEqual(part.part_of, "loc_throne_room")
        self.assertEqual(part.properties["material"], "stone")

    def test_part_states_property(self):
        """Test Part states property access."""
        part = Part(id="part_1", name="test", part_of="loc_1")

        # States auto-initializes
        self.assertEqual(part.states, {})

        # Can set states
        part.states["damaged"] = True
        self.assertTrue(part.states["damaged"])

    def test_part_llm_context_property(self):
        """Test Part llm_context property access."""
        part = Part(id="part_1", name="test", part_of="loc_1")

        # Initially None
        self.assertIsNone(part.llm_context)

        # Can set llm_context
        part.llm_context = {"traits": ["stone", "damp"]}
        self.assertEqual(part.llm_context["traits"], ["stone", "damp"])

    def test_gamestate_includes_parts(self):
        """Test GameState has parts collection."""
        metadata = Metadata(title="Test", start_location="loc_1")
        game_state = GameState(
            metadata=metadata,
            locations=[],
            items=[],
            actors={},
            locks=[],
            parts=[]
        )

        self.assertIsInstance(game_state.parts, list)
        self.assertEqual(len(game_state.parts), 0)

    def test_gamestate_with_parts(self):
        """Test GameState can contain Part entities."""
        metadata = Metadata(title="Test", start_location="loc_1")
        location = Location(id="loc_1", name="Room", description="A room")
        part = Part(id="part_1", name="wall", part_of="loc_1")

        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[],
            actors={},
            locks=[],
            parts=[part]
        )

        self.assertEqual(len(game_state.parts), 1)
        self.assertEqual(game_state.parts[0].id, "part_1")


class TestPartJSONLoading(unittest.TestCase):
    """Test loading Part entities from JSON."""

    def test_load_parts_from_json(self):
        """Test loading Part entities from JSON."""
        game_json = {
            "metadata": {
                "title": "Test Game",
                "start_location": "loc_room"
            },
            "locations": [
                {
                    "id": "loc_room",
                    "name": "Room",
                    "description": "A room"
                }
            ],
            "parts": [
                {
                    "id": "part_room_north_wall",
                    "name": "north wall",
                    "part_of": "loc_room",
                    "properties": {
                        "material": "stone"
                    },
                    "behaviors": []
                }
            ],
            "items": [],
            "actors": {
                "player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_room"}
            },
            "locks": []
        }

        # Write to temp file and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(game_json, f)
            temp_path = f.name

        try:
            game_state = load_game_state(temp_path)

            self.assertEqual(len(game_state.parts), 1)
            part = game_state.parts[0]
            self.assertEqual(part.id, "part_room_north_wall")
            self.assertEqual(part.name, "north wall")
            self.assertEqual(part.part_of, "loc_room")
            self.assertEqual(part.properties["material"], "stone")
        finally:
            os.unlink(temp_path)

    def test_load_empty_parts_list(self):
        """Test loading game with no parts defined."""
        game_json = {
            "metadata": {"title": "Test", "start_location": "loc_1"},
            "locations": [{"id": "loc_1", "name": "Room", "description": "A room"}],
            "items": [],
            "actors": {
                "player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_1"}
            },
            "locks": []
            # No parts field
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(game_json, f)
            temp_path = f.name

        try:
            game_state = load_game_state(temp_path)
            self.assertEqual(len(game_state.parts), 0)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
