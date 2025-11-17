"""
Tests for state manager loader functionality.

Covers: TL-001 through TL-007 from state_manager_testing.md
"""
import unittest
import json
from io import StringIO
from pathlib import Path

from test_helpers import load_fixture, get_fixture_path


class TestLoader(unittest.TestCase):
    """Test cases for game state loader."""

    def test_TL001_load_full_fixture_from_file(self):
        """TL-001: Load full fixture from file path."""
        from src.state_manager.loader import load_game_state

        fixture_path = get_fixture_path("valid_world.json")
        game_state = load_game_state(fixture_path)

        # Verify correct counts
        self.assertEqual(len(game_state.locations), 3)
        self.assertEqual(len(game_state.items), 5)
        self.assertEqual(len(game_state.npcs), 1)
        self.assertEqual(len(game_state.doors), 1)
        self.assertEqual(len(game_state.locks), 2)
        self.assertEqual(len(game_state.scripts), 1)

        # Verify metadata
        self.assertEqual(game_state.metadata.title, "Test Adventure")
        self.assertEqual(game_state.metadata.start_location, "loc_1")

    def test_TL002_load_from_file_like_object(self):
        """TL-002: Load from file-like object (StringIO)."""
        from src.state_manager.loader import load_game_state

        data = load_fixture("minimal_world.json")
        json_str = json.dumps(data)
        file_like = StringIO(json_str)

        game_state = load_game_state(file_like)
        self.assertEqual(len(game_state.locations), 1)

    def test_TL003_load_minimal_world(self):
        """TL-003: Load minimal world with defaults."""
        from src.state_manager.loader import load_game_state

        fixture_path = get_fixture_path("minimal_world.json")
        game_state = load_game_state(fixture_path)

        # Should have defaults for optional sections
        self.assertEqual(len(game_state.doors), 0)
        self.assertEqual(len(game_state.items), 0)
        self.assertEqual(len(game_state.npcs), 0)
        self.assertEqual(len(game_state.locks), 0)
        self.assertEqual(len(game_state.scripts), 0)

        # Player state should be initialized from metadata
        self.assertEqual(game_state.player.location, "loc_1")

    def test_TL004_unknown_top_level_keys_preserved(self):
        """TL-004: Unknown top-level keys preserved via extra fields."""
        from src.state_manager.loader import load_game_state
        import tempfile

        data = load_fixture("minimal_world.json")
        data["custom_field"] = "custom_value"
        data["future_feature"] = {"data": [1, 2, 3]}

        # Save modified fixture temporarily
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            game_state = load_game_state(temp_path)
            # Extra fields should be accessible
            self.assertIn("custom_field", game_state.extra)
            self.assertEqual(game_state.extra["custom_field"], "custom_value")
        finally:
            Path(temp_path).unlink()

    def test_TL005_invalid_json_raises_schema_error(self):
        """TL-005: Invalid JSON format raises SchemaError."""
        from src.state_manager.loader import load_game_state
        from src.state_manager.exceptions import SchemaError

        invalid_json = "{invalid json syntax"
        file_like = StringIO(invalid_json)

        with self.assertRaises(SchemaError):
            load_game_state(file_like)

    def test_TL006_missing_file_raises_error(self):
        """TL-006: Missing file path triggers FileLoadError."""
        from src.state_manager.loader import load_game_state
        from src.state_manager.exceptions import FileLoadError

        nonexistent_path = "/path/to/nonexistent/file.json"

        with self.assertRaises(FileLoadError):
            load_game_state(nonexistent_path)

    def test_TL007_load_from_dict(self):
        """TL-007: Loader accepts already-parsed dict."""
        from src.state_manager.loader import parse_game_state

        data = load_fixture("minimal_world.json")
        game_state = parse_game_state(data)

        self.assertEqual(len(game_state.locations), 1)
        self.assertEqual(game_state.metadata.title, "Minimal World")


if __name__ == '__main__':
    unittest.main()
