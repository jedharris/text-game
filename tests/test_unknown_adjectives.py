"""Tests for treating unknown words as adjectives.

Tests that the parser passes unknown words before nouns as adjectives,
and that behaviors can use multiple adjectives to disambiguate objects.
"""

import unittest
import json
import tempfile
from pathlib import Path

from src.parser import Parser
from src.state_manager import load_game_state
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from src.vocabulary_generator import extract_nouns_from_state, merge_vocabulary


class TestParserUnknownAdjectives(unittest.TestCase):
    """Test that parser treats unknown words before nouns as adjectives."""

    def setUp(self):
        """Set up test fixtures with minimal vocabulary."""
        # Vocabulary with no adjectives defined
        self.vocab = {
            "verbs": [
                {"word": "take", "synonyms": ["get"], "object_required": True},
                {"word": "open", "synonyms": [], "object_required": True},
                {"word": "examine", "synonyms": ["look", "x"], "object_required": "optional"}
            ],
            "nouns": [
                {"word": "door"},
                {"word": "key"},
                {"word": "lantern"},
                {"word": "north", "word_type": ["noun", "adjective", "verb"], "synonyms": ["n"], "object_required": False}
            ],
            "adjectives": []  # No predefined adjectives
        }

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.vocab, f)
            self.vocab_path = f.name

        self.parser = Parser(self.vocab_path)

    def tearDown(self):
        """Clean up temp file."""
        Path(self.vocab_path).unlink()

    def test_single_unknown_word_before_noun_is_adjective(self):
        """Test that single unknown word before noun becomes adjective."""
        result = self.parser.parse_command("take iron key")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "key")
        self.assertIsNotNone(result.direct_adjective)
        self.assertEqual(result.direct_adjective.word, "iron")

    def test_multiple_unknown_words_before_noun(self):
        """Test that multiple unknown words before noun become adjectives."""
        result = self.parser.parse_command("open rough wooden door")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "open")
        self.assertEqual(result.direct_object.word, "door")
        # Should have adjectives captured (implementation dependent)
        self.assertIsNotNone(result.direct_adjective)

    def test_unknown_word_not_confused_with_noun(self):
        """Test that unknown word before noun is not treated as noun."""
        result = self.parser.parse_command("examine ancient lantern")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "examine")
        self.assertEqual(result.direct_object.word, "lantern")
        self.assertIsNotNone(result.direct_adjective)
        self.assertEqual(result.direct_adjective.word, "ancient")

    def test_completely_unknown_command_fails_gracefully(self):
        """Test that completely unknown words don't crash."""
        result = self.parser.parse_command("xyzzy plugh")

        # Should return None or partial result, not crash
        # The exact behavior depends on implementation

    def test_unknown_word_after_verb_without_noun_handled(self):
        """Test handling of unknown word when no noun follows."""
        result = self.parser.parse_command("take xyzzy")

        # Should handle gracefully - either treat as noun or fail
        # Should not crash

    def test_verb_only_still_works(self):
        """Test that verb-only commands still work."""
        result = self.parser.parse_command("north")

        self.assertIsNotNone(result)
        # Directions are now verbs with object_required=False
        self.assertEqual(result.verb.word, "north")

    def test_verb_noun_without_adjective_still_works(self):
        """Test that standard verb+noun still works."""
        result = self.parser.parse_command("take key")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "key")


class TestMultipleAdjectiveDisambiguation(unittest.TestCase):
    """Test that multiple adjectives correctly disambiguate objects."""

    def setUp(self):
        """Set up test with multiple similar doors."""
        self.game_data = {
            "metadata": {
                "title": "Test Game",
                "start_location": "room1"
            },
            "locations": [
                {
                    "id": "room1",
                    "name": "Test Room",
                    "description": "A room with multiple doors.",
                    "exits": {
                        "north": {"type": "door", "to": "room2", "door_id": "door1"},
                        "south": {"type": "door", "to": "room3", "door_id": "door2"}
                    }
                },
                {
                    "id": "room2",
                    "name": "North Room",
                    "description": "North room.",
                    "exits": {"south": {"type": "door", "to": "room1", "door_id": "door1"}}
                },
                {
                    "id": "room3",
                    "name": "South Room",
                    "description": "South room.",
                    "exits": {"north": {"type": "door", "to": "room1", "door_id": "door2"}}
                }
            ],
            "items": [
                {
                    "id": "door1",
                    "name": "door",
                    "description": "A rough wooden door with iron bands.",
                    "location": "exit:room1:north",
                    "door": {"open": False, "locked": False}
                },
                {
                    "id": "door2",
                    "name": "door",
                    "description": "A polished wooden door with brass fittings.",
                    "location": "exit:room1:south",
                    "door": {"open": False, "locked": False}
                }
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }

        self.state = load_game_state(self.game_data)
        self.handler = LLMProtocolHandler(self.state)

    def test_single_adjective_disambiguates(self):
        """Test that single adjective can disambiguate doors."""
        # Open "rough" door
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "rough"}
        })

        self.assertTrue(result.get("success"))
        # Verify correct door was opened (doors are migrated to items)
        door1 = next(i for i in self.state.items if i.id == "door1")
        door2 = next(i for i in self.state.items if i.id == "door2")
        self.assertTrue(door1.door_open)
        self.assertFalse(door2.door_open)

    def test_multiple_adjectives_disambiguate(self):
        """Test that multiple adjectives narrow down selection."""
        # Both doors are wooden, but only one is rough
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjectives": ["rough", "wooden"]}
        })

        self.assertTrue(result.get("success"))
        door1 = next(i for i in self.state.items if i.id == "door1")
        self.assertTrue(door1.door_open)

    def test_adjective_in_description_matches(self):
        """Test that adjectives match against description text."""
        # "iron" appears in door1's description
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        })

        self.assertTrue(result.get("success"))
        door1 = next(i for i in self.state.items if i.id == "door1")
        self.assertTrue(door1.door_open)

    def test_no_matching_adjective_handled_gracefully(self):
        """Test that non-matching adjectives are handled gracefully."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "golden"}
        })

        # Should either fail gracefully or open default door
        # Should not crash


class TestItemDisambiguation(unittest.TestCase):
    """Test adjective disambiguation for items."""

    def setUp(self):
        """Set up test with multiple similar items."""
        self.game_data = {
            "metadata": {
                "title": "Test Game",
                "start_location": "room1"
            },
            "locations": [
                {
                    "id": "room1",
                    "name": "Test Room",
                    "description": "A room with keys."
                }
            ],
            "items": [
                {
                    "id": "key1",
                    "name": "key",
                    "description": "A small iron key with rust spots.",
                    "type": "tool",
                    "portable": True,
                    "location": "room1"
                },
                {
                    "id": "key2",
                    "name": "key",
                    "description": "A large brass key with ornate handle.",
                    "type": "tool",
                    "portable": True,
                    "location": "room1"
                }
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }

        self.state = load_game_state(self.game_data)
        self.handler = LLMProtocolHandler(self.state)

    def test_adjective_selects_correct_item(self):
        """Test that adjective selects correct item from multiple."""
        # Take the iron key
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "key", "adjective": "iron"}
        })

        self.assertTrue(result.get("success"))
        # Verify correct key was taken
        self.assertIn("key1", self.state.actors["player"].inventory)
        self.assertNotIn("key2", self.state.actors["player"].inventory)

    def test_different_adjective_selects_other_item(self):
        """Test that different adjective selects other item."""
        # Take the brass key
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "key", "adjective": "brass"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("key2", self.state.actors["player"].inventory)
        self.assertNotIn("key1", self.state.actors["player"].inventory)

    def test_size_adjective_disambiguates(self):
        """Test that size adjectives work for disambiguation."""
        # Take the small key
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "key", "adjective": "small"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("key1", self.state.actors["player"].inventory)

    def test_ambiguous_adjective_picks_first(self):
        """Test behavior when adjective matches multiple items."""
        # Both keys have "key" in description, neither has "shiny"
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "key", "adjective": "shiny"}
        })

        # Should either fail with "which key?" or take first
        # Should not crash


class TestGracefulErrorHandling(unittest.TestCase):
    """Test graceful handling of edge cases."""

    def setUp(self):
        """Set up minimal test game."""
        self.game_data = {
            "metadata": {
                "title": "Test Game",
                "start_location": "room1"
            },
            "locations": [
                {
                    "id": "room1",
                    "name": "Test Room",
                    "description": "A simple room."
                }
            ],
            "items": [
                {
                    "id": "item1",
                    "name": "lantern",
                    "description": "A brass lantern.",
                    "type": "tool",
                    "portable": True,
                    "location": "room1"
                }
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }

        self.state = load_game_state(self.game_data)
        self.handler = LLMProtocolHandler(self.state)

    def test_nonexistent_object_with_adjective(self):
        """Test taking nonexistent object with adjective."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword", "adjective": "iron"}
        })

        self.assertFalse(result.get("success"))
        self.assertIn("error", result)

    def test_wrong_adjective_for_existing_object(self):
        """Test using wrong adjective for existing object."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "lantern", "adjective": "iron"}
        })

        # The lantern is brass, not iron
        # Should either fail or take it anyway (current behavior takes first match)

    def test_empty_adjective_ignored(self):
        """Test that empty adjective string is handled."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "lantern", "adjective": ""}
        })

        # Should work normally
        self.assertTrue(result.get("success"))

    def test_none_adjective_ignored(self):
        """Test that None adjective is handled."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "lantern", "adjective": None}
        })

        # Should work normally
        self.assertTrue(result.get("success"))


if __name__ == '__main__':
    unittest.main()
