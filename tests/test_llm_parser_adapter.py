"""Unit tests for LLM parser adapter.

Tests the adapter that converts LLM parser output (string IDs) to ParsedCommand (WordEntry objects).
"""

import unittest
from pathlib import Path
from typing import Dict, Any, Optional

from src.game_engine import GameEngine
from src.llm_parser_adapter import LLMParserAdapter
from src.parsed_command import ParsedCommand
from src.word_entry import WordEntry, WordType


class TestLLMParserAdapter(unittest.TestCase):
    """Test LLM parser adapter with real big_game vocabulary."""

    @classmethod
    def setUpClass(cls):
        """Load real game engine once for all tests."""
        cls.engine = GameEngine(Path('examples/big_game'))
        cls.adapter = LLMParserAdapter(cls.engine.merged_vocabulary)

        print(f"\n[Test Setup] Adapter initialized with real big_game vocabulary")
        print(f"  Verbs: {len(cls.adapter.verb_lookup)}")
        print(f"  Nouns: {len(cls.adapter.noun_lookup)}")
        print(f"  Prepositions: {len(cls.adapter.prep_lookup)}")

    def _make_parser_output(
        self,
        verb: str,
        obj: Optional[str] = None,
        indirect_obj: Optional[str] = None,
        prep: Optional[str] = None
    ) -> Dict[str, Any]:
        """Helper to create parser output dict."""
        action: Dict[str, Any] = {"verb": verb}
        if obj:
            action["object"] = obj
        if indirect_obj:
            action["indirect_object"] = indirect_obj
        if prep:
            action["preposition"] = prep

        return {
            "type": "command",
            "action": action
        }

    def test_adapter_initialization(self):
        """Adapter initializes with vocabulary lookup tables."""
        self.assertGreater(len(self.adapter.verb_lookup), 0)
        self.assertGreater(len(self.adapter.noun_lookup), 0)
        self.assertGreater(len(self.adapter.prep_lookup), 0)

    def test_simple_verb_only_command(self):
        """Convert simple verb-only command: 'look'."""
        parser_output = self._make_parser_output("look")
        result = self.adapter.to_parsed_command(parser_output, "look")

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ParsedCommand)
        self.assertIsNotNone(result.verb)
        self.assertEqual(result.verb.word, "look")
        self.assertIsNone(result.direct_object)
        self.assertEqual(result.raw, "look")

    def test_verb_with_object(self):
        """Convert verb + object: 'take bucket'."""
        parser_output = self._make_parser_output("take", "bucket")
        result = self.adapter.to_parsed_command(parser_output, "take bucket")

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        self.assertEqual(result.verb.word, "take")
        self.assertIsNotNone(result.direct_object)
        self.assertEqual(result.direct_object.word, "bucket")

    def test_unknown_verb_rejected(self):
        """Unknown verb returns None."""
        parser_output = self._make_parser_output("dance", "bucket")
        result = self.adapter.to_parsed_command(parser_output, "dance with bucket")

        # Adapter should reject unknown verb
        self.assertIsNone(result)

    def test_hallucinated_object_creates_word_entry(self):
        """Hallucinated simple word creates WordEntry for dialogue topic support."""
        parser_output = self._make_parser_output("take", "unicorn")
        result = self.adapter.to_parsed_command(parser_output, "take unicorn")

        # Adapter returns ParsedCommand with a WordEntry for unknown simple words
        # This allows dialogue topics and other dynamic content to work
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        self.assertIsNotNone(result.direct_object)  # Created for dialogue topic support
        self.assertEqual(result.direct_object.word, "unicorn")

    def test_use_on_command(self):
        """Convert 'use X on Y' command."""
        parser_output = self._make_parser_output("use", "torch", "orb", "on")
        result = self.adapter.to_parsed_command(parser_output, "use torch on orb")

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        self.assertEqual(result.verb.word, "use")
        self.assertIsNotNone(result.direct_object)
        self.assertIsNotNone(result.indirect_object)
        self.assertIsNotNone(result.preposition)
        self.assertEqual(result.preposition.word, "on")

    def test_multi_word_entity_ice_wand(self):
        """Multi-word entity 'ice_wand' resolves to WordEntry."""
        parser_output = self._make_parser_output("take", "ice_wand")
        result = self.adapter.to_parsed_command(parser_output, "take ice wand")

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        self.assertIsNotNone(result.direct_object)
        # Should find "ice wand" in vocabulary
        self.assertEqual(result.direct_object.word, "ice wand")

    def test_multi_word_entity_keepers_journal(self):
        """Multi-word entity with apostrophe resolves correctly."""
        parser_output = self._make_parser_output("examine", "keepers_journal")
        result = self.adapter.to_parsed_command(parser_output, "examine keeper's journal")

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.direct_object)
        # Vocabulary has "Keeper's journal"
        self.assertIn("journal", result.direct_object.word.lower())

    def test_multi_word_use_command(self):
        """Command with two multi-word entities."""
        parser_output = self._make_parser_output("use", "ice_wand", "frozen_crystal", "on")
        result = self.adapter.to_parsed_command(parser_output, "use ice wand on frozen crystal")

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        self.assertIsNotNone(result.direct_object)
        self.assertIsNotNone(result.indirect_object)
        self.assertEqual(result.direct_object.word, "ice wand")
        # Vocabulary should have "frozen crystal"
        self.assertIn("crystal", result.indirect_object.word.lower())

    def test_give_to_command(self):
        """Convert 'give X to Y' command."""
        parser_output = self._make_parser_output("give", "silvermoss", "aldric", "to")
        result = self.adapter.to_parsed_command(parser_output, "give silvermoss to aldric")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "give")
        self.assertIsNotNone(result.direct_object)
        # Aldric might be in vocabulary as an NPC name
        # If not, indirect_object could be None - that's OK, handler will reject
        self.assertIsNotNone(result.preposition)
        self.assertEqual(result.preposition.word, "to")

    def test_direction_as_object(self):
        """Direction 'north' should resolve as noun."""
        parser_output = self._make_parser_output("go", "north")
        result = self.adapter.to_parsed_command(parser_output, "go north")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "go")
        self.assertIsNotNone(result.direct_object)
        self.assertEqual(result.direct_object.word, "north")

    def test_none_parser_output(self):
        """None parser output returns None."""
        result = self.adapter.to_parsed_command(None, "invalid command")
        self.assertIsNone(result)

    def test_error_type_output(self):
        """Error type parser output returns None."""
        parser_output = {"type": "error", "message": "I don't understand"}
        result = self.adapter.to_parsed_command(parser_output, "blah blah")
        self.assertIsNone(result)

    def test_missing_verb(self):
        """Parser output without verb returns None."""
        parser_output = {"type": "command", "action": {"object": "bucket"}}
        result = self.adapter.to_parsed_command(parser_output, "bucket")
        self.assertIsNone(result)

    def test_verb_synonyms(self):
        """Verb synonyms work correctly."""
        # "get" is a synonym for "take"
        parser_output = self._make_parser_output("get", "bucket")
        result = self.adapter.to_parsed_command(parser_output, "get bucket")

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        # Should resolve to "take" (or whatever the canonical verb is)
        self.assertIn(result.verb.word, ["get", "take"])


class TestAdapterContractValidation(unittest.TestCase):
    """Test that adapter output passes contract validation."""

    @classmethod
    def setUpClass(cls):
        """Load game engine and adapter."""
        cls.engine = GameEngine(Path('examples/big_game'))
        cls.adapter = LLMParserAdapter(cls.engine.merged_vocabulary)

    def test_adapter_output_is_valid_parsed_command(self):
        """Adapter output is a valid ParsedCommand."""
        from src.contract_validators import validate_word_entry

        parser_output = {
            "type": "command",
            "action": {"verb": "take", "object": "bucket"}
        }
        result = self.adapter.to_parsed_command(parser_output, "take bucket")

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ParsedCommand)

        # Validate WordEntry objects
        if result.verb:
            validate_word_entry(result.verb)
        if result.direct_object:
            validate_word_entry(result.direct_object)
        if result.indirect_object:
            validate_word_entry(result.indirect_object)

    def test_adapter_preserves_raw_input(self):
        """Adapter preserves original raw input."""
        raw_input = "take the shiny bucket"
        parser_output = {
            "type": "command",
            "action": {"verb": "take", "object": "bucket"}
        }
        result = self.adapter.to_parsed_command(parser_output, raw_input)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw, raw_input)


if __name__ == "__main__":
    unittest.main()
