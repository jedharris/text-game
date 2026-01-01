"""Contract tests for LLM parser integration.

These tests validate that the parser and adapter components conform to
the expected contracts for integration with the game engine.

The contract is an evolving specification - tests may change as implementation proceeds.
"""

import unittest
from typing import Dict, Any

from src.contract_validators import (
    validate_action_dict,
    validate_word_entry,
    validate_parser_output,
    validate_adapter_contract,
    ValidationError
)
from src.action_types import ActionDict
from src.word_entry import WordEntry, WordType
from src.types import ActorId


class TestWordEntryContract(unittest.TestCase):
    """Test that WordEntry validation works correctly."""

    def test_valid_word_entry(self):
        """Valid WordEntry passes validation."""
        entry = WordEntry(
            word="sword",
            word_type=WordType.NOUN,
            synonyms=["blade", "weapon"]
        )
        # Should not raise
        validate_word_entry(entry)

    def test_word_entry_with_multi_type(self):
        """WordEntry with multiple types passes validation."""
        entry = WordEntry(
            word="open",
            word_type={WordType.VERB, WordType.ADJECTIVE},
            synonyms=[]
        )
        # Should not raise
        validate_word_entry(entry)

    def test_empty_word_fails(self):
        """Empty word string raises ValidationError."""
        entry = WordEntry(
            word="",
            word_type=WordType.NOUN
        )
        with self.assertRaises(ValidationError) as cm:
            validate_word_entry(entry)
        self.assertIn("empty", str(cm.exception).lower())

    def test_invalid_word_type_fails(self):
        """Invalid word_type raises ValidationError."""
        entry = WordEntry(
            word="test",
            word_type="invalid"  # Intentionally invalid for testing
        )
        with self.assertRaises(ValidationError):
            validate_word_entry(entry)


class TestActionDictContract(unittest.TestCase):
    """Test that ActionDict validation works correctly."""

    def test_minimal_action_dict(self):
        """Minimal ActionDict with just verb passes."""
        action: ActionDict = {"verb": "look"}
        # Should not raise
        validate_action_dict(action)

    def test_action_dict_with_object(self):
        """ActionDict with WordEntry object passes."""
        action: ActionDict = {
            "verb": "take",
            "object": WordEntry(word="sword", word_type=WordType.NOUN)
        }
        # Should not raise
        validate_action_dict(action)

    def test_action_dict_with_actor_id(self):
        """ActionDict with ActorId passes."""
        action: ActionDict = {
            "verb": "look",
            "actor_id": ActorId("player")
        }
        # Should not raise
        validate_action_dict(action)

    def test_action_dict_full_fields(self):
        """ActionDict with all optional fields passes."""
        action: ActionDict = {
            "verb": "use",
            "actor_id": ActorId("player"),
            "object": WordEntry(word="wand", word_type=WordType.NOUN),
            "adjective": "ice",
            "indirect_object": WordEntry(word="crystal", word_type=WordType.NOUN),
            "indirect_adjective": "frozen",
            "preposition": "on",
            "raw_input": "use ice wand on frozen crystal"
        }
        # Should not raise
        validate_action_dict(action)

    def test_missing_verb_fails(self):
        """ActionDict without verb raises ValidationError."""
        action: Dict[str, Any] = {}
        with self.assertRaises(ValidationError) as cm:
            validate_action_dict(action)
        self.assertIn("verb", str(cm.exception).lower())

    def test_invalid_verb_type_fails(self):
        """ActionDict with non-string verb raises ValidationError."""
        action: Dict[str, Any] = {"verb": 123}
        with self.assertRaises(ValidationError) as cm:
            validate_action_dict(action)
        self.assertIn("verb", str(cm.exception).lower())

    def test_invalid_object_type_fails(self):
        """ActionDict with non-WordEntry object raises ValidationError."""
        action: Dict[str, Any] = {
            "verb": "take",
            "object": "sword"  # Should be WordEntry, not string
        }
        with self.assertRaises(ValidationError) as cm:
            validate_action_dict(action)
        self.assertIn("object", str(cm.exception).lower())


class TestParserOutputContract(unittest.TestCase):
    """Test that parser output validation works correctly."""

    def test_valid_command_output(self):
        """Valid command output passes validation."""
        output = {
            "type": "command",
            "action": {
                "verb": "take",
                "object": "sword"
            }
        }
        # Should not raise
        validate_parser_output(output)

    def test_valid_error_output(self):
        """Valid error output passes validation."""
        output = {
            "type": "error",
            "message": "I don't understand that command."
        }
        # Should not raise
        validate_parser_output(output)

    def test_command_with_all_fields(self):
        """Command output with all optional fields passes."""
        output = {
            "type": "command",
            "action": {
                "verb": "use",
                "object": "wand",
                "adjective": "ice",
                "indirect_object": "crystal",
                "indirect_adjective": "frozen",
                "preposition": "on"
            },
            "raw_input": "use ice wand on frozen crystal"
        }
        # Should not raise
        validate_parser_output(output)

    def test_missing_type_fails(self):
        """Parser output without type raises ValidationError."""
        output = {"action": {"verb": "look"}}
        with self.assertRaises(ValidationError) as cm:
            validate_parser_output(output)
        self.assertIn("type", str(cm.exception).lower())

    def test_invalid_type_fails(self):
        """Parser output with invalid type raises ValidationError."""
        output = {"type": "invalid"}
        with self.assertRaises(ValidationError) as cm:
            validate_parser_output(output)
        self.assertIn("type", str(cm.exception).lower())

    def test_command_missing_action_fails(self):
        """Command output without action raises ValidationError."""
        output = {"type": "command"}
        with self.assertRaises(ValidationError) as cm:
            validate_parser_output(output)
        self.assertIn("action", str(cm.exception).lower())

    def test_command_missing_verb_fails(self):
        """Command action without verb raises ValidationError."""
        output = {
            "type": "command",
            "action": {"object": "sword"}
        }
        with self.assertRaises(ValidationError) as cm:
            validate_parser_output(output)
        self.assertIn("verb", str(cm.exception).lower())

    def test_error_missing_message_fails(self):
        """Error output without message raises ValidationError."""
        output = {"type": "error"}
        with self.assertRaises(ValidationError) as cm:
            validate_parser_output(output)
        self.assertIn("message", str(cm.exception).lower())


class TestAdapterContract(unittest.TestCase):
    """Test the full adapter contract: parser output → ActionDict.

    These tests validate the contract without implementing the adapter yet.
    They serve as specifications for what Phase 4's adapter must do.
    """

    def test_valid_conversion(self):
        """Valid parser output → valid ActionDict passes contract."""
        parser_output = {
            "type": "command",
            "action": {
                "verb": "take",
                "object": "sword"
            }
        }

        action_dict: ActionDict = {
            "verb": "take",
            "actor_id": ActorId("player"),
            "object": WordEntry(word="sword", word_type=WordType.NOUN),
            "raw_input": "take sword"
        }

        # Should not raise
        validate_adapter_contract(parser_output, action_dict)

    def test_error_output_to_none(self):
        """Error parser output → None is valid contract."""
        parser_output = {
            "type": "error",
            "message": "I don't understand."
        }

        # Adapter returns None for error output
        validate_adapter_contract(parser_output, None)

    def test_command_rejection_allowed(self):
        """Adapter can reject valid parser output (e.g., invalid verb)."""
        parser_output = {
            "type": "command",
            "action": {
                "verb": "dance",  # Not in vocabulary
                "object": "sword"
            }
        }

        # Adapter rejects invalid verb, returns None
        validate_adapter_contract(parser_output, None)

    def test_invalid_action_dict_fails(self):
        """Invalid ActionDict violates contract."""
        parser_output = {
            "type": "command",
            "action": {"verb": "take"}
        }

        # Invalid ActionDict (object is string, not WordEntry)
        invalid_action: Dict[str, Any] = {
            "verb": "take",
            "object": "sword"  # Wrong type
        }

        with self.assertRaises(ValidationError):
            validate_adapter_contract(parser_output, invalid_action)  # Intentionally invalid for testing


if __name__ == "__main__":
    unittest.main()
