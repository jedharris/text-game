"""Tests for migration from pre-versioned game state to v_0.01."""

import json
import tempfile
import unittest
from pathlib import Path

from tools.migrations.migrate_to_v_0_01 import (
    detect_version,
    migrate_to_v_0_01,
    migrate_file,
    VERSION_TARGET,
)


class TestDetectVersion(unittest.TestCase):
    """Tests for version detection."""

    def test_detects_pre_versioned_when_no_schema_version(self):
        """Files without schema_version are pre-versioned."""
        state = {
            "metadata": {
                "title": "Test Game",
                "version": "1.0",
            },
            "locations": [],
            "items": [],
        }
        self.assertIsNone(detect_version(state))

    def test_detects_pre_versioned_when_no_metadata(self):
        """Files without metadata are pre-versioned."""
        state = {
            "locations": [],
            "items": [],
        }
        self.assertIsNone(detect_version(state))

    def test_detects_v_0_01(self):
        """Files with schema_version v_0.01 are detected."""
        state = {
            "metadata": {
                "title": "Test Game",
                "schema_version": "v_0.01",
            },
            "locations": [],
        }
        self.assertEqual(detect_version(state), "v_0.01")


class TestMigrateToV001(unittest.TestCase):
    """Tests for migration logic."""

    def test_adds_schema_version_to_metadata(self):
        """Migration adds schema_version to existing metadata."""
        state = {
            "metadata": {
                "title": "Test Game",
                "version": "1.0",
                "description": "A test game.",
            },
            "locations": [],
            "items": [],
        }
        result = migrate_to_v_0_01(state)
        self.assertEqual(result["metadata"]["schema_version"], VERSION_TARGET)

    def test_preserves_existing_metadata_fields(self):
        """Migration preserves all existing metadata fields."""
        state = {
            "metadata": {
                "title": "Test Game",
                "version": "1.0",
                "description": "A test game.",
                "author": "Test Author",
                "start_location": "loc_start",
            },
            "locations": [],
        }
        result = migrate_to_v_0_01(state)
        self.assertEqual(result["metadata"]["title"], "Test Game")
        self.assertEqual(result["metadata"]["version"], "1.0")
        self.assertEqual(result["metadata"]["description"], "A test game.")
        self.assertEqual(result["metadata"]["author"], "Test Author")
        self.assertEqual(result["metadata"]["start_location"], "loc_start")

    def test_creates_metadata_if_missing(self):
        """Migration creates metadata dict if missing."""
        state = {
            "locations": [],
            "items": [],
        }
        result = migrate_to_v_0_01(state)
        self.assertIn("metadata", result)
        self.assertEqual(result["metadata"]["schema_version"], VERSION_TARGET)

    def test_preserves_all_other_top_level_keys(self):
        """Migration preserves locations, items, locks, actors."""
        state = {
            "metadata": {"title": "Test"},
            "locations": [{"id": "loc_1"}],
            "items": [{"id": "item_1"}],
            "locks": [{"id": "lock_1"}],
            "actors": {"player": {"id": "player"}},
        }
        result = migrate_to_v_0_01(state)
        self.assertEqual(result["locations"], [{"id": "loc_1"}])
        self.assertEqual(result["items"], [{"id": "item_1"}])
        self.assertEqual(result["locks"], [{"id": "lock_1"}])
        self.assertEqual(result["actors"], {"player": {"id": "player"}})

    def test_does_not_modify_original_state(self):
        """Migration returns a new dict, doesn't modify original."""
        state = {
            "metadata": {"title": "Test"},
            "locations": [],
        }
        result = migrate_to_v_0_01(state)
        self.assertIsNot(result, state)
        self.assertNotIn("schema_version", state["metadata"])

    def test_raises_if_already_v_0_01(self):
        """Migration raises error if already at target version."""
        state = {
            "metadata": {
                "title": "Test",
                "schema_version": "v_0.01",
            },
            "locations": [],
        }
        with self.assertRaises(ValueError) as ctx:
            migrate_to_v_0_01(state)
        self.assertIn("already at version", str(ctx.exception))


class TestMigrateFile(unittest.TestCase):
    """Tests for file-based migration."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_migrates_file_in_place(self):
        """migrate_file updates file in place by default."""
        state = {
            "metadata": {"title": "Test Game"},
            "locations": [],
        }
        input_path = Path(self.temp_dir) / "game.json"
        input_path.write_text(json.dumps(state, indent=2))

        migrate_file(str(input_path))

        result = json.loads(input_path.read_text())
        self.assertEqual(result["metadata"]["schema_version"], VERSION_TARGET)

    def test_migrates_file_to_output_path(self):
        """migrate_file writes to output_path when specified."""
        state = {
            "metadata": {"title": "Test Game"},
            "locations": [],
        }
        input_path = Path(self.temp_dir) / "game.json"
        output_path = Path(self.temp_dir) / "game_v001.json"
        input_path.write_text(json.dumps(state, indent=2))

        migrate_file(str(input_path), str(output_path))

        # Original unchanged
        original = json.loads(input_path.read_text())
        self.assertNotIn("schema_version", original.get("metadata", {}))

        # Output has migration applied
        result = json.loads(output_path.read_text())
        self.assertEqual(result["metadata"]["schema_version"], VERSION_TARGET)

    def test_creates_backup_when_in_place(self):
        """migrate_file creates .bak backup when modifying in place."""
        state = {
            "metadata": {"title": "Test Game"},
            "locations": [],
        }
        input_path = Path(self.temp_dir) / "game.json"
        input_path.write_text(json.dumps(state, indent=2))

        migrate_file(str(input_path))

        backup_path = Path(self.temp_dir) / "game.json.bak"
        self.assertTrue(backup_path.exists())
        backup = json.loads(backup_path.read_text())
        self.assertNotIn("schema_version", backup.get("metadata", {}))

    def test_preserves_json_formatting(self):
        """migrate_file preserves 2-space indentation."""
        state = {
            "metadata": {"title": "Test Game"},
            "locations": [],
        }
        input_path = Path(self.temp_dir) / "game.json"
        input_path.write_text(json.dumps(state, indent=2))

        migrate_file(str(input_path))

        content = input_path.read_text()
        # Check for 2-space indentation
        self.assertIn('  "metadata"', content)


if __name__ == "__main__":
    unittest.main()
