"""Tests for text_game.py command handling.

These tests verify that commands like 'look', 'put X on Y', and 'examine'
work correctly through the JSON protocol interface.
"""

import unittest
import json
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.parser import Parser
from src.state_manager import load_game_state
from src.behavior_manager import BehaviorManager
from src.llm_protocol import JSONProtocolHandler
from src.vocabulary_generator import extract_nouns_from_state, merge_vocabulary
from src.text_game import format_location_query


class TestVocabularyMerging(unittest.TestCase):
    """Test that vocabulary merging preserves all required fields."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = load_game_state(str(project_root / "examples" / "simple_game_state.json"))
        self.behavior_manager = BehaviorManager()
        behaviors_dir = project_root / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        with open(project_root / "src" / "vocabulary.json", 'r') as f:
            self.base_vocab = json.load(f)

        extracted_nouns = extract_nouns_from_state(self.state)
        vocab_with_nouns = merge_vocabulary(self.base_vocab, extracted_nouns)
        self.merged_vocab = self.behavior_manager.get_merged_vocabulary(vocab_with_nouns)

    def test_merged_vocab_includes_prepositions(self):
        """Test that merged vocabulary includes prepositions from base vocab."""
        self.assertIn("prepositions", self.merged_vocab)
        prepositions = self.merged_vocab["prepositions"]
        self.assertIn("on", prepositions)
        self.assertIn("in", prepositions)

    def test_merged_vocab_includes_articles(self):
        """Test that merged vocabulary includes articles from base vocab."""
        self.assertIn("articles", self.merged_vocab)
        articles = self.merged_vocab["articles"]
        self.assertIn("the", articles)
        self.assertIn("a", articles)


class TestParserCommands(unittest.TestCase):
    """Test that the parser correctly handles various command formats."""

    def setUp(self):
        """Set up test fixtures with proper vocabulary."""
        self.state = load_game_state(str(project_root / "examples" / "simple_game_state.json"))
        self.behavior_manager = BehaviorManager()
        behaviors_dir = project_root / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        with open(project_root / "src" / "vocabulary.json", 'r') as f:
            base_vocab = json.load(f)

        extracted_nouns = extract_nouns_from_state(self.state)
        vocab_with_nouns = merge_vocabulary(base_vocab, extracted_nouns)
        merged_vocab = self.behavior_manager.get_merged_vocabulary(vocab_with_nouns)

        # Write to temp file for parser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(merged_vocab, f)
            self.temp_vocab_path = f.name

        self.parser = Parser(self.temp_vocab_path)

    def tearDown(self):
        """Clean up temp file."""
        Path(self.temp_vocab_path).unlink(missing_ok=True)

    def test_look_command_parses(self):
        """Test that 'look' command is recognized."""
        result = self.parser.parse_command("look")
        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "look")

    def test_look_alias_l_parses(self):
        """Test that 'l' alias for look is recognized."""
        result = self.parser.parse_command("l")
        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "look")

    def test_put_on_command_parses(self):
        """Test that 'put X on Y' command is recognized."""
        result = self.parser.parse_command("put lantern on table")
        self.assertIsNotNone(result, "'put lantern on table' should parse successfully")
        self.assertEqual(result.verb.word, "put")
        self.assertEqual(result.direct_object.word, "lantern")
        self.assertEqual(result.indirect_object.word, "table")

    def test_put_in_command_parses(self):
        """Test that 'put X in Y' command is recognized."""
        result = self.parser.parse_command("put key in chest")
        self.assertIsNotNone(result, "'put key in chest' should parse successfully")
        self.assertEqual(result.verb.word, "put")
        self.assertEqual(result.direct_object.word, "key")
        self.assertEqual(result.indirect_object.word, "chest")

    def test_examine_without_object_returns_none(self):
        """Test that 'examine' alone returns None (requires object)."""
        result = self.parser.parse_command("examine")
        # examine requires an object, so should return None
        self.assertIsNone(result)


class TestGameEngineIntegration(unittest.TestCase):
    """Integration tests for game engine command dispatch."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = load_game_state(str(project_root / "examples" / "simple_game_state.json"))
        self.behavior_manager = BehaviorManager()
        behaviors_dir = project_root / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

    def test_look_handler_exists(self):
        """Test that a look handler is registered."""
        self.assertTrue(self.behavior_manager.has_handler("look"))

    def test_put_handler_exists(self):
        """Test that a put handler is registered."""
        self.assertTrue(self.behavior_manager.has_handler("put"))


class TestLocationQuery(unittest.TestCase):
    """Test location query shows items on surfaces."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = load_game_state(str(project_root / "examples" / "simple_game_state.json"))
        self.behavior_manager = BehaviorManager()
        behaviors_dir = project_root / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)
        self.handler = JSONProtocolHandler(self.state, behavior_manager=self.behavior_manager)

        # Move player to hallway where table with lantern is
        self.state.actors["player"].location = "loc_hallway"

    def test_location_query_shows_items_on_surfaces(self):
        """Test that location query shows items on surface containers."""
        response = self.handler.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["items", "doors"]
        })

        output = format_location_query(response)

        # Should show the table
        self.assertIn("table", output.lower())
        # Should show the lantern on the table
        self.assertIn("lantern", output.lower())

    def test_location_query_raw_data_has_on_surface(self):
        """Test that location query raw data marks items on surfaces."""
        response = self.handler.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["items"]
        })

        items = response.get("data", {}).get("items", [])
        lantern = next((i for i in items if i.get("name") == "lantern"), None)

        self.assertIsNotNone(lantern)
        self.assertEqual(lantern.get("on_surface"), "table")


class TestExamineCommand(unittest.TestCase):
    """Test examine command via JSON protocol."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = load_game_state(str(project_root / "examples" / "simple_game_state.json"))
        self.behavior_manager = BehaviorManager()
        behaviors_dir = project_root / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)
        self.handler = JSONProtocolHandler(self.state, behavior_manager=self.behavior_manager)

        # Move player to hallway where table with lantern is
        self.state.actors["player"].location = "loc_hallway"

    def test_examine_command_finds_item_by_name(self):
        """Test that examine command finds items by name."""
        response = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "examine", "object": "table"}
        })

        self.assertTrue(response.get("success"))
        self.assertIn("table", response.get("message", "").lower())


if __name__ == "__main__":
    unittest.main()
