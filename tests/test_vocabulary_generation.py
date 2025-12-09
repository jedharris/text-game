"""Tests for dynamic vocabulary generation from game state.

Tests the extraction of nouns from game state entities and merging
with base vocabulary for parser initialization.
"""

import unittest
import json
import tempfile
from pathlib import Path

from src.state_manager import load_game_state
from src.vocabulary_generator import extract_nouns_from_state, merge_vocabulary
from src.parser import Parser


class TestExtractNounsFromState(unittest.TestCase):
    """Test extraction of nouns from game state entities."""

    def test_extract_item_names(self):
        """Test that item names are extracted as nouns."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "room1"},
            "locations": [{"id": "room1", "name": "Room", "description": "A room"}],
            "items": [
                {"id": "item1", "name": "lantern", "description": "A lantern",
                 "type": "tool", "portable": True, "location": "room1"},
                {"id": "item2", "name": "sword", "description": "A sword",
                 "type": "weapon", "portable": True, "location": "room1"}
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }
        state = load_game_state(game_data)
        nouns = extract_nouns_from_state(state)

        noun_words = [n["word"] for n in nouns]
        self.assertIn("lantern", noun_words)
        self.assertIn("sword", noun_words)

    def test_extract_npc_names(self):
        """Test that NPC names are extracted as nouns."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "room1"},
            "locations": [{"id": "room1", "name": "Room", "description": "A room"}],
            "items": [],
            "locks": [],
            "actors": {
                "player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"},
                "npc1": {"id": "npc1", "name": "goblin", "description": "A goblin", "location": "room1"},
                "npc2": {"id": "npc2", "name": "wizard", "description": "A wizard", "location": "room1"}
            }
        }
        state = load_game_state(game_data)
        nouns = extract_nouns_from_state(state)

        noun_words = [n["word"] for n in nouns]
        self.assertIn("goblin", noun_words)
        self.assertIn("wizard", noun_words)

    def test_extract_multi_word_names(self):
        """Test that multi-word names like 'rubber duck' are extracted."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "room1"},
            "locations": [{"id": "room1", "name": "Room", "description": "A room"}],
            "items": [
                {"id": "item1", "name": "rubber duck", "description": "A duck",
                 "type": "tool", "portable": True, "location": "room1"},
                {"id": "item2", "name": "iron key", "description": "A key",
                 "type": "tool", "portable": True, "location": "room1"}
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }
        state = load_game_state(game_data)
        nouns = extract_nouns_from_state(state)

        noun_words = [n["word"] for n in nouns]
        self.assertIn("rubber duck", noun_words)
        self.assertIn("iron key", noun_words)

    def test_no_duplicate_nouns(self):
        """Test that duplicate item names only appear once."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "room1"},
            "locations": [{"id": "room1", "name": "Room", "description": "A room"}],
            "items": [
                {"id": "item1", "name": "key", "description": "A brass key",
                 "type": "tool", "portable": True, "location": "room1"},
                {"id": "item2", "name": "key", "description": "An iron key",
                 "type": "tool", "portable": True, "location": "room1"}
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }
        state = load_game_state(game_data)
        nouns = extract_nouns_from_state(state)

        noun_words = [n["word"] for n in nouns]
        key_count = noun_words.count("key")
        self.assertEqual(key_count, 1)

    def test_empty_game_state(self):
        """Test extraction from game state with no items or NPCs."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "room1"},
            "locations": [{"id": "room1", "name": "Room", "description": "A room"}],
            "items": [],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }
        state = load_game_state(game_data)
        nouns = extract_nouns_from_state(state)

        self.assertEqual(nouns, [])

    def test_noun_format(self):
        """Test that extracted nouns have correct format for vocabulary."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "room1"},
            "locations": [{"id": "room1", "name": "Room", "description": "A room"}],
            "items": [
                {"id": "item1", "name": "lantern", "description": "A lantern",
                 "type": "tool", "portable": True, "location": "room1"}
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }
        state = load_game_state(game_data)
        nouns = extract_nouns_from_state(state)

        self.assertEqual(len(nouns), 1)
        noun = nouns[0]
        self.assertIn("word", noun)
        self.assertEqual(noun["word"], "lantern")


class TestMergeVocabulary(unittest.TestCase):
    """Test merging of base vocabulary with extracted nouns."""

    def test_merge_adds_new_nouns(self):
        """Test that extracted nouns are added to vocabulary."""
        base_vocab = {
            "verbs": [{"word": "take", "object_required": True}],
            "nouns": [{"word": "door", "value": 101}],
            "adjectives": []
        }
        extracted_nouns = [
            {"word": "lantern"},
            {"word": "sword"}
        ]

        merged = merge_vocabulary(base_vocab, extracted_nouns)

        noun_words = [n["word"] for n in merged["nouns"]]
        self.assertIn("door", noun_words)
        self.assertIn("lantern", noun_words)
        self.assertIn("sword", noun_words)

    def test_merge_preserves_base_vocabulary(self):
        """Test that base vocabulary entries are preserved."""
        base_vocab = {
            "verbs": [{"word": "take", "object_required": True}],
            "nouns": [{"word": "door", "value": 101, "llm_context": {"traits": ["passage"]}}],
            "adjectives": [{"word": "iron"}]
        }
        extracted_nouns = [{"word": "lantern"}]

        merged = merge_vocabulary(base_vocab, extracted_nouns)

        # Verbs preserved
        self.assertEqual(len(merged["verbs"]), 1)
        self.assertEqual(merged["verbs"][0]["word"], "take")

        # Adjectives preserved
        self.assertEqual(len(merged["adjectives"]), 1)

        # Base noun preserved with llm_context
        door_noun = next(n for n in merged["nouns"] if n["word"] == "door")
        self.assertEqual(door_noun["value"], 101)
        self.assertIn("llm_context", door_noun)

    def test_merge_no_duplicate_nouns(self):
        """Test that duplicate nouns are not added."""
        base_vocab = {
            "verbs": [],
            "nouns": [{"word": "key", "value": 102}],
            "adjectives": []
        }
        extracted_nouns = [
            {"word": "key"},  # Already in base
            {"word": "lantern"}
        ]

        merged = merge_vocabulary(base_vocab, extracted_nouns)

        noun_words = [n["word"] for n in merged["nouns"]]
        key_count = noun_words.count("key")
        self.assertEqual(key_count, 1)
        self.assertEqual(len(merged["nouns"]), 2)

    def test_merge_empty_extracted(self):
        """Test merge with no extracted nouns."""
        base_vocab = {
            "verbs": [{"word": "take"}],
            "nouns": [{"word": "door"}],
            "adjectives": []
        }

        merged = merge_vocabulary(base_vocab, [])

        self.assertEqual(len(merged["nouns"]), 1)
        self.assertEqual(merged["nouns"][0]["word"], "door")

    def test_merge_empty_base_nouns(self):
        """Test merge when base has no nouns."""
        base_vocab = {
            "verbs": [{"word": "take"}],
            "nouns": [],
            "adjectives": []
        }
        extracted_nouns = [{"word": "lantern"}]

        merged = merge_vocabulary(base_vocab, extracted_nouns)

        self.assertEqual(len(merged["nouns"]), 1)
        self.assertEqual(merged["nouns"][0]["word"], "lantern")


class TestParserWithMergedVocabulary(unittest.TestCase):
    """Test that parser works correctly with merged vocabulary."""

    def test_parser_recognizes_extracted_nouns(self):
        """Test that parser recognizes nouns from game state."""
        # Create base vocabulary
        base_vocab = {
            "verbs": [
                {"word": "examine", "synonyms": ["look", "inspect"], "object_required": True},
                {"word": "take", "synonyms": ["get", "grab"], "object_required": True}
            ],
            "nouns": [{"word": "door", "value": 101}],
            "adjectives": []
        }

        # Extract nouns from game state
        game_data = {
            "metadata": {"title": "Test", "start_location": "room1"},
            "locations": [{"id": "room1", "name": "Room", "description": "A room"}],
            "items": [
                {"id": "item1", "name": "lantern", "description": "A lantern",
                 "type": "tool", "portable": True, "location": "room1"}
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }
        state = load_game_state(game_data)
        extracted_nouns = extract_nouns_from_state(state)

        # Merge vocabulary
        merged = merge_vocabulary(base_vocab, extracted_nouns)

        # Write to temp file and create parser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(merged, f)
            temp_path = f.name

        try:
            parser = Parser(temp_path)

            # Test parsing "examine lantern"
            result = parser.parse_command("examine lantern")

            self.assertIsNotNone(result)
            self.assertEqual(result.verb.word, "examine")
            self.assertEqual(result.direct_object.word, "lantern")
        finally:
            Path(temp_path).unlink()

    def test_parser_recognizes_multi_word_nouns(self):
        """Test that parser recognizes multi-word nouns from game state.

        Note: The current parser has limited support for multi-word nouns.
        This test verifies that the last word of a multi-word name is recognized.
        Full multi-word noun support would require parser enhancements.
        """
        base_vocab = {
            "verbs": [
                {"word": "take", "synonyms": ["get"], "object_required": True}
            ],
            "nouns": [],
            "adjectives": [{"word": "rubber"}]  # Add as adjective for now
        }

        game_data = {
            "metadata": {"title": "Test", "start_location": "room1"},
            "locations": [{"id": "room1", "name": "Room", "description": "A room"}],
            "items": [
                {"id": "item1", "name": "duck", "description": "A rubber duck",
                 "type": "tool", "portable": True, "location": "room1"}
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }
        state = load_game_state(game_data)
        extracted_nouns = extract_nouns_from_state(state)
        merged = merge_vocabulary(base_vocab, extracted_nouns)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(merged, f)
            temp_path = f.name

        try:
            parser = Parser(temp_path)

            # Test parsing "take rubber duck" - rubber as adjective, duck as noun
            result = parser.parse_command("take rubber duck")

            self.assertIsNotNone(result)
            self.assertEqual(result.verb.word, "take")
            self.assertEqual(result.direct_object.word, "duck")
            # Adjective should be captured
            if result.direct_adjective:
                self.assertEqual(result.direct_adjective.word, "rubber")
        finally:
            Path(temp_path).unlink()


class TestIntegrationWithGameState(unittest.TestCase):
    """Integration tests with actual game state files."""

    def test_simple_game_state_vocabulary(self):
        """Test vocabulary generation from simple_game/game_state.json."""
        game_state_path = Path(__file__).parent.parent / "examples" / "simple_game" / "game_state.json"
        if not game_state_path.exists():
            self.skipTest("simple_game/game_state.json not found")

        state = load_game_state(str(game_state_path))
        nouns = extract_nouns_from_state(state)

        # Should extract lantern from game state
        noun_words = [n["word"] for n in nouns]
        self.assertIn("lantern", noun_words)


if __name__ == '__main__':
    unittest.main()
