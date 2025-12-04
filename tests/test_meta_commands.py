"""Unit tests for meta command handlers.

Tests the signal-returning handlers in behaviors/core/meta.py that
control game session operations (quit, save, load).
"""

import unittest
from src.word_entry import WordEntry, WordType
from src.state_accessor import StateAccessor, HandlerResult
from src.state_manager import GameState, Actor, Location, Metadata
from src.behavior_manager import BehaviorManager
import behaviors.core.meta as meta


class TestMetaCommandHandlers(unittest.TestCase):
    """Test meta command handler functions."""

    def setUp(self):
        """Set up test fixtures with minimal game state."""
        self.state = GameState(
            metadata=Metadata(title="Test"),
            locations=[Location(id="room1", name="Room", description="A room")],
            actors={"player": Actor(id="player", name="Player", description="Test player", location="room1", inventory=[])}
        )
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_handle_quit_returns_signal(self):
        """Test that handle_quit returns proper signal format."""
        action = {"actor_id": "player"}

        result = meta.handle_quit(self.accessor, action)

        self.assertIsInstance(result, HandlerResult)
        self.assertTrue(result.success)
        self.assertIn("playing", result.message.lower())
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data.get("signal"), "quit")

    def test_handle_save_no_filename(self):
        """Test save command without filename returns signal with no filename."""
        action = {"actor_id": "player"}

        result = meta.handle_save(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(result.data.get("signal"), "save")
        self.assertIsNone(result.data.get("filename"))
        self.assertIn("raw_input", result.data)

    def test_handle_save_with_wordentry_filename(self):
        """Test save command with WordEntry object extracts filename."""
        filename_entry = WordEntry(word="savegame.json", word_type=WordType.NOUN)
        action = {
            "actor_id": "player",
            "object": filename_entry
        }

        result = meta.handle_save(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(result.data.get("signal"), "save")
        self.assertEqual(result.data.get("filename"), "savegame.json")

    def test_handle_save_with_string_filename(self):
        """Test save command with string object extracts filename."""
        action = {
            "actor_id": "player",
            "object": "mygame.json"
        }

        result = meta.handle_save(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(result.data.get("signal"), "save")
        self.assertEqual(result.data.get("filename"), "mygame.json")

    def test_handle_save_includes_raw_input(self):
        """Test save command includes raw_input in signal for fallback parsing."""
        action = {
            "actor_id": "player",
            "raw_input": "save mysave.json"
        }

        result = meta.handle_save(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(result.data.get("raw_input"), "save mysave.json")

    def test_handle_load_no_filename(self):
        """Test load command without filename returns signal with no filename."""
        action = {"actor_id": "player"}

        result = meta.handle_load(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(result.data.get("signal"), "load")
        self.assertIsNone(result.data.get("filename"))
        self.assertIn("raw_input", result.data)

    def test_handle_load_with_wordentry_filename(self):
        """Test load command with WordEntry object extracts filename."""
        filename_entry = WordEntry(word="savegame.json", word_type=WordType.NOUN)
        action = {
            "actor_id": "player",
            "object": filename_entry
        }

        result = meta.handle_load(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(result.data.get("signal"), "load")
        self.assertEqual(result.data.get("filename"), "savegame.json")

    def test_handle_load_with_string_filename(self):
        """Test load command with string object extracts filename."""
        action = {
            "actor_id": "player",
            "object": "existing.json"
        }

        result = meta.handle_load(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(result.data.get("signal"), "load")
        self.assertEqual(result.data.get("filename"), "existing.json")

    def test_handle_load_includes_raw_input(self):
        """Test load command includes raw_input in signal for fallback parsing."""
        action = {
            "actor_id": "player",
            "raw_input": "load oldgame.json"
        }

        result = meta.handle_load(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(result.data.get("raw_input"), "load oldgame.json")


class TestMetaVocabulary(unittest.TestCase):
    """Test meta commands vocabulary structure."""

    def test_vocabulary_has_required_keys(self):
        """Test vocabulary dict has all required keys."""
        vocab = meta.vocabulary

        self.assertIn("verbs", vocab)
        self.assertIn("nouns", vocab)
        self.assertIn("adjectives", vocab)
        self.assertIn("directions", vocab)

    def test_vocabulary_has_quit_verb(self):
        """Test vocabulary includes quit verb with synonyms."""
        verbs = meta.vocabulary["verbs"]
        quit_verb = next((v for v in verbs if v["word"] == "quit"), None)

        self.assertIsNotNone(quit_verb)
        self.assertIn("exit", quit_verb["synonyms"])
        self.assertEqual(quit_verb["object_required"], False)
        self.assertIn("llm_context", quit_verb)
        self.assertIn("meta-command", quit_verb["llm_context"]["traits"])

    def test_vocabulary_has_save_verb(self):
        """Test vocabulary includes save verb."""
        verbs = meta.vocabulary["verbs"]
        save_verb = next((v for v in verbs if v["word"] == "save"), None)

        self.assertIsNotNone(save_verb)
        self.assertEqual(save_verb["object_required"], "optional")
        self.assertIn("llm_context", save_verb)
        self.assertIn("meta-command", save_verb["llm_context"]["traits"])

    def test_vocabulary_has_load_verb(self):
        """Test vocabulary includes load verb with synonyms."""
        verbs = meta.vocabulary["verbs"]
        load_verb = next((v for v in verbs if v["word"] == "load"), None)

        self.assertIsNotNone(load_verb)
        self.assertIn("restore", load_verb["synonyms"])
        self.assertEqual(load_verb["object_required"], "optional")
        self.assertIn("llm_context", load_verb)
        self.assertIn("meta-command", load_verb["llm_context"]["traits"])

    def test_vocabulary_empty_other_sections(self):
        """Test vocabulary has empty arrays for non-verb sections."""
        vocab = meta.vocabulary

        self.assertEqual(vocab["nouns"], [])
        self.assertEqual(vocab["adjectives"], [])
        self.assertEqual(vocab["directions"], [])


class TestMetaBehaviorLoading(unittest.TestCase):
    """Test that meta behavior module can be loaded by BehaviorManager."""

    def test_behavior_module_loads(self):
        """Test that meta module can be loaded into BehaviorManager."""
        manager = BehaviorManager()

        # Load the meta module
        manager.load_module(meta)

        # Verify handlers are registered
        self.assertTrue(manager.has_handler("quit"))
        self.assertTrue(manager.has_handler("save"))
        self.assertTrue(manager.has_handler("load"))

    def test_behavior_vocabulary_merges(self):
        """Test that meta vocabulary merges with base vocabulary."""
        manager = BehaviorManager()
        manager.load_module(meta)

        base_vocab = {
            "verbs": [],
            "nouns": [],
            "adjectives": [],
            "prepositions": ["with", "to"],
            "articles": ["the", "a"]
        }

        merged = manager.get_merged_vocabulary(base_vocab)

        # Verify meta verbs are included
        verb_words = [v["word"] for v in merged["verbs"]]
        self.assertIn("quit", verb_words)
        self.assertIn("save", verb_words)
        self.assertIn("load", verb_words)

        # Verify base vocabulary preserved
        self.assertIn("with", merged["prepositions"])
        self.assertIn("the", merged["articles"])


class TestMetaSignalFormat(unittest.TestCase):
    """Test that signal format is consistent and complete."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = GameState(
            metadata=Metadata(title="Test"),
            locations=[Location(id="room1", name="Room", description="A room")],
            actors={"player": Actor(id="player", name="Player", description="Test player", location="room1", inventory=[])}
        )
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_all_signals_have_signal_field(self):
        """Test that all handlers return data with 'signal' field."""
        handlers = [
            ("quit", meta.handle_quit),
            ("save", meta.handle_save),
            ("load", meta.handle_load)
        ]

        for signal_name, handler in handlers:
            action = {"actor_id": "player"}
            result = handler(self.accessor, action)

            self.assertIn("signal", result.data, f"{signal_name} missing signal field")
            self.assertIsNotNone(result.data["signal"])

    def test_save_load_have_filename_field(self):
        """Test that save/load signals include filename field (may be None)."""
        for handler in [meta.handle_save, meta.handle_load]:
            action = {"actor_id": "player"}
            result = handler(self.accessor, action)

            self.assertIn("filename", result.data)
            # Filename can be None when not provided

    def test_save_load_have_raw_input_field(self):
        """Test that save/load signals include raw_input field."""
        for handler in [meta.handle_save, meta.handle_load]:
            action = {"actor_id": "player"}
            result = handler(self.accessor, action)

            self.assertIn("raw_input", result.data)
            # raw_input defaults to empty string if not in action


if __name__ == '__main__':
    unittest.main()
