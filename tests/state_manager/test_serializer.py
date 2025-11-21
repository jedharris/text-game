"""
Tests for state manager serialization functionality.

Covers: TS-001 through TS-005 from state_manager_testing.md
"""
import unittest
import json
import tempfile
from pathlib import Path

from .test_helpers import load_fixture, json_equal, normalize_json, get_fixture_path


class TestSerializer(unittest.TestCase):
    """Test cases for game state serialization."""

    def test_TS001_serialize_to_dict(self):
        """TS-001: Serialize GameState to dict matches loaded JSON."""
        from src.state_manager.loader import parse_game_state
        from src.state_manager.serializer import game_state_to_dict

        original_data = load_fixture("valid_world.json")
        game_state = parse_game_state(original_data)
        serialized = game_state_to_dict(game_state)

        # Should be semantically equal (after canonical sorting)
        self.assertTrue(json_equal(original_data, serialized))

    def test_TS002_serialize_to_json_string(self):
        """TS-002: Serialize to JSON string with pretty-print."""
        from src.state_manager.loader import load_game_state
        from src.state_manager.serializer import game_state_to_dict

        game_state = load_game_state(get_fixture_path("valid_world.json"))
        serialized_dict = game_state_to_dict(game_state)

        # Serialize to pretty-printed JSON
        json_str = json.dumps(serialized_dict, indent=2, sort_keys=True)

        # Verify formatting
        self.assertIn('\n', json_str)  # Has newlines between elements
        self.assertTrue(json_str.endswith('}'))  # Ends with closing brace (no trailing newline from json.dumps)

        # Verify parseable
        reparsed = json.loads(json_str)
        self.assertTrue(json_equal(serialized_dict, reparsed))

    def test_TS003_save_to_file_and_reload(self):
        """TS-003: Save to file and re-load confirms round-trip."""
        from src.state_manager.loader import load_game_state
        from src.state_manager.serializer import save_game_state

        original_state = load_game_state(get_fixture_path("valid_world.json"))

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            save_game_state(original_state, temp_path)

            # Reload and compare
            reloaded_state = load_game_state(temp_path)

            # Should have same structure
            self.assertEqual(len(reloaded_state.locations), len(original_state.locations))
            self.assertEqual(len(reloaded_state.items), len(original_state.items))
        finally:
            Path(temp_path).unlink()

    def test_TS004_preserve_unknown_fields(self):
        """TS-004: Serialization preserves unknown/extra fields."""
        from src.state_manager.loader import parse_game_state
        from src.state_manager.serializer import game_state_to_dict

        data = load_fixture("minimal_world.json")
        data["custom_field"] = "custom_value"
        data["future_extension"] = {"nested": "data"}

        game_state = parse_game_state(data)
        serialized = game_state_to_dict(game_state)

        # Extra fields should be preserved
        self.assertIn("custom_field", serialized)
        self.assertEqual(serialized["custom_field"], "custom_value")
        self.assertIn("future_extension", serialized)

    def test_TS005_serialize_invalid_state_raises_error(self):
        """TS-005: Serializing invalid GameState raises ValidationError if enabled."""
        from src.state_manager.models import GameState, Metadata
        from src.state_manager.serializer import save_game_state
        from src.state_manager.exceptions import ValidationError

        # Create intentionally invalid state
        invalid_state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_999"),
            locations=[],
            doors=[],
            items=[],
            locks=[],
            npcs=[],
            scripts=[],
            player=None
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
            with self.assertRaises(ValidationError):
                save_game_state(invalid_state, f.name, validate=True)


if __name__ == '__main__':
    unittest.main()
