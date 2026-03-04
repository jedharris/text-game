"""Tests for GameEngine class."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.game_engine import GameEngine
from src.state_manager import GameState


class TestGameEngineInitialization(unittest.TestCase):
    """Test GameEngine initialization."""

    def setUp(self):
        """Set up test fixtures."""
        # Use the simple_game as a known-good test case
        self.simple_game_dir = Path(__file__).parent.parent / "examples" / "simple_game"

    def test_init_with_valid_game_directory(self):
        """Test initialization with valid game directory."""
        engine = GameEngine(self.simple_game_dir)

        self.assertEqual(engine.game_dir, self.simple_game_dir.absolute())
        self.assertIsNotNone(engine.game_state)
        self.assertIsNotNone(engine.behavior_manager)
        self.assertIsNotNone(engine.merged_vocabulary)
        self.assertIsNotNone(engine.json_handler)

    def test_init_with_missing_directory(self):
        """Test initialization with missing directory raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError) as ctx:
            GameEngine(Path("/nonexistent/directory"))

        self.assertIn("Game directory not found", str(ctx.exception))

    def test_init_with_file_not_directory(self):
        """Test initialization with file path raises ValueError."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile() as f:
            with self.assertRaises(ValueError) as ctx:
                GameEngine(Path(f.name))

            self.assertIn("not a directory", str(ctx.exception))

    def test_init_with_missing_game_state(self):
        """Test initialization with missing game_state.json raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Create behaviors directory but no game_state.json
            (tmppath / "behaviors").mkdir()

            with self.assertRaises(FileNotFoundError) as ctx:
                GameEngine(tmppath)

            self.assertIn("game_state.json not found", str(ctx.exception))

    def test_init_with_invalid_game_state_json(self):
        """Test initialization with invalid JSON raises JSONDecodeError."""
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Write invalid JSON
            (tmppath / "game_state.json").write_text("{ invalid json }")
            (tmppath / "behaviors").mkdir()

            # Per exception handling policy: fail loudly, don't wrap in ValueError
            with self.assertRaises(json.JSONDecodeError) as ctx:
                GameEngine(tmppath)

            # Verify it's a JSON parsing error
            self.assertIn("Expecting property name", str(ctx.exception))

    def test_init_with_missing_behaviors_directory(self):
        """Test initialization with missing behaviors/ raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Create minimal valid game_state.json (actors is a dict, not list)
            game_state = {
                "metadata": {"title": "Test", "author": "Test", "version": "1.0"},
                "locations": [{"id": "loc_1", "name": "Room", "description": "A room"}],
                "items": [],
                "doors": [],
                "actors": {"player": {"id": "player", "location": "loc_1", "name": "Adventurer"}}
            }
            (tmppath / "game_state.json").write_text(json.dumps(game_state))

            with self.assertRaises(FileNotFoundError) as ctx:
                GameEngine(tmppath)

            self.assertIn("behaviors/", str(ctx.exception))

    def test_vocabulary_merging(self):
        """Test that vocabulary is properly merged."""
        engine = GameEngine(self.simple_game_dir)

        # Should have merged vocabulary from base + extracted nouns + behaviors
        self.assertIn("verbs", engine.merged_vocabulary)
        self.assertIn("nouns", engine.merged_vocabulary)
        self.assertIsInstance(engine.merged_vocabulary["verbs"], list)
        self.assertIsInstance(engine.merged_vocabulary["nouns"], list)


class TestGameEngineParser(unittest.TestCase):
    """Test GameEngine parser creation."""

    def setUp(self):
        """Set up test fixtures."""
        self.simple_game_dir = Path(__file__).parent.parent / "examples" / "simple_game"
        self.engine = GameEngine(self.simple_game_dir)

    def test_create_parser(self):
        """Test creating a parser."""
        parser = self.engine.create_parser()

        self.assertIsNotNone(parser)
        # Test that parser can parse a simple command
        result = parser.parse_command("north")
        self.assertIsNotNone(result)


class TestGameEngineNarrator(unittest.TestCase):
    """Test GameEngine narrator creation."""

    def setUp(self):
        """Set up test fixtures."""
        self.simple_game_dir = Path(__file__).parent.parent / "examples" / "simple_game"

    def test_create_narrator_without_prompt_file(self):
        """Test creating narrator when narrator_prompt.txt doesn't exist raises error."""
        # Create a temp game directory without narrator_prompt.txt
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Copy game_state.json from simple_game
            import shutil
            shutil.copy(self.simple_game_dir / "game_state.json", tmppath / "game_state.json")

            # Create behaviors directory with symlink to core
            behaviors_dir = tmppath / "behaviors"
            behaviors_dir.mkdir()
            core_behaviors = Path(__file__).parent.parent / "behaviors" / "core"
            (behaviors_dir / "core").symlink_to(core_behaviors)

            engine = GameEngine(tmppath)

            with self.assertRaises(FileNotFoundError) as ctx:
                engine.create_narrator("fake-api-key")

            self.assertIn("narrator_style.txt not found", str(ctx.exception))

    @patch('src.llm_narrator.HAS_ANTHROPIC', True)
    @unittest.skip("LLM narrator test disabled until anthropic client stub is available")
    @patch('src.llm_narrator.anthropic')
    def test_create_narrator_with_prompt_file(self, mock_anthropic):
        """Test creating narrator when narrator_style.txt exists."""
        # Note: This test will be fully functional once we distribute prompts in Phase 2
        # For now, we can test with a temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Copy game_state.json from simple_game
            import shutil
            shutil.copy(self.simple_game_dir / "game_state.json", tmppath / "game_state.json")

            # Create behaviors directory with symlink to core
            behaviors_dir = tmppath / "behaviors"
            behaviors_dir.mkdir()
            core_behaviors = Path(__file__).parent.parent / "behaviors" / "core"
            (behaviors_dir / "core").symlink_to(core_behaviors)

            # Create a narrator_style.txt file
            (tmppath / "narrator_style.txt").write_text("Test style guidance")

            engine = GameEngine(tmppath)
            narrator = engine.create_narrator("fake-api-key")

            self.assertIsNotNone(narrator)


class TestGameEngineStateReload(unittest.TestCase):
    """Test GameEngine state reloading."""

    def setUp(self):
        """Set up test fixtures."""
        self.simple_game_dir = Path(__file__).parent.parent / "examples" / "simple_game"
        self.engine = GameEngine(self.simple_game_dir)

    def test_reload_state(self):
        """Test reloading game state."""
        # Get original state
        original_state = self.engine.game_state
        original_title = original_state.metadata.title

        # Load a fresh copy of the state from file to use as new_state
        from src.state_manager import load_game_state
        new_state = load_game_state(str(self.simple_game_dir / "game_state.json"))

        # Modify the title
        new_state.metadata.title = "New Title"

        # Reload state
        self.engine.reload_state(new_state)

        # Verify state changed
        self.assertEqual(self.engine.game_state.metadata.title, "New Title")
        self.assertNotEqual(self.engine.game_state.metadata.title, original_title)

        # Verify json_handler was recreated
        self.assertIsNotNone(self.engine.json_handler)


if __name__ == '__main__':
    unittest.main()
