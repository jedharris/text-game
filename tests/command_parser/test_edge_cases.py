"""
Unit tests for error handling and edge cases.

Tests the Parser class's handling of errors and edge cases.
Corresponds to Test Categories 9-10 in test-plan.md.
"""

import unittest
import os
from src.parser import Parser
from src.parsed_command import ParsedCommand


class TestErrorHandling(unittest.TestCase):
    """Test error handling functionality."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_unknown_word(self):
        """
        Test EH-001: Unknown word in command.

        Verify that commands with unknown words return None
        with appropriate error information.
        """
        result = self.parser.parse_command("frobulate sword")

        self.assertIsNone(result)

    def test_invalid_pattern(self):
        """
        Test EH-002: Invalid word pattern.

        Verify that commands with invalid patterns return None.
        """
        result = self.parser.parse_command("the with in")

        self.assertIsNone(result)

    def test_empty_input(self):
        """
        Test EH-003: Empty string.

        Verify that empty input returns None.
        """
        result = self.parser.parse_command("")

        self.assertIsNone(result)

    def test_whitespace_only(self):
        """
        Test EH-004: Only whitespace.

        Verify that whitespace-only input returns None.
        """
        result = self.parser.parse_command("   ")

        self.assertIsNone(result)

    def test_single_unknown(self):
        """
        Test EH-005: Single unknown word.

        Verify that a single unknown word returns None.
        """
        result = self.parser.parse_command("frobulate")

        self.assertIsNone(result)

    def test_partial_unknown(self):
        """
        Test EH-006: Known + unknown words.

        Unknown words are passed through as nouns for the handler to resolve.
        """
        result = self.parser.parse_command("take frobulate")

        # Unknown words are treated as nouns and passed to handler
        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "frobulate")

    def test_all_articles(self):
        """
        Test EH-007: Only articles.

        Verify that commands with only articles return None.
        """
        result = self.parser.parse_command("the a an")

        self.assertIsNone(result)

    def test_noun_only(self):
        """
        Test EH-008: Single noun.

        Verify that a single noun without verb returns None.
        """
        result = self.parser.parse_command("sword")

        self.assertIsNone(result)

    def test_adjective_only(self):
        """
        Test EH-009: Single adjective.

        Verify that a single adjective returns None.
        """
        result = self.parser.parse_command("rusty")

        self.assertIsNone(result)

    def test_preposition_only(self):
        """
        Test EH-010: Single preposition.

        Verify that a single preposition returns None.
        """
        result = self.parser.parse_command("with")

        self.assertIsNone(result)

    def test_two_verbs(self):
        """
        Test EH-011: Two verbs.

        Verify that commands with two verbs return None.
        """
        result = self.parser.parse_command("take drop")

        self.assertIsNone(result)

    def test_two_directions(self):
        """
        Test EH-012: Two directions.

        Verify that commands with two directions return None.
        """
        result = self.parser.parse_command("north south")

        self.assertIsNone(result)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and special input handling."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_extra_whitespace(self):
        """
        Test EC-001: Multiple spaces between words.

        Verify that extra whitespace is handled correctly.
        """
        result = self.parser.parse_command("take    sword")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")

    def test_leading_whitespace(self):
        """
        Test EC-002: Leading whitespace.

        Verify that leading whitespace is handled correctly.
        """
        result = self.parser.parse_command("  take sword")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")

    def test_trailing_whitespace(self):
        """
        Test EC-003: Trailing whitespace.

        Verify that trailing whitespace is handled correctly.
        """
        result = self.parser.parse_command("take sword  ")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")

    def test_mixed_case(self):
        """
        Test EC-004: Mixed case input.

        Verify that mixed case input is normalized to lowercase.
        """
        result = self.parser.parse_command("TaKe SwOrD")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")

    def test_uppercase_input(self):
        """
        Test EC-005: All uppercase.

        Verify that uppercase input is normalized to lowercase.
        """
        result = self.parser.parse_command("TAKE SWORD")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")

    def test_tab_characters(self):
        """
        Test EC-006: Tab separators.

        Verify that tabs are treated as whitespace.
        """
        result = self.parser.parse_command("take\tsword")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")

    def test_very_long_command(self):
        """
        Test EC-007: Command with max words.

        Verify that 6-word commands work correctly.
        """
        result = self.parser.parse_command("unlock rusty door with iron key")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "unlock")
        self.assertEqual(result.direct_adjective.word, "rusty")
        self.assertEqual(result.direct_object.word, "door")
        self.assertEqual(result.preposition.word, "with")
        self.assertEqual(result.indirect_adjective.word, "iron")
        self.assertEqual(result.indirect_object.word, "key")

    def test_too_many_words(self):
        """
        Test EC-008: More than 6 words.

        Verify that commands with more than 6 words return None.
        (No pattern matches more than 6 words)
        """
        result = self.parser.parse_command("take rusty sword with iron key now")

        # Should return None because no pattern matches 7 words
        self.assertIsNone(result)

    def test_special_characters(self):
        """
        Test EC-009: Special characters in input.

        Verify that special characters are handled gracefully.
        Note: Depends on tokenization implementation.
        """
        # Punctuation is typically not in vocabulary
        result = self.parser.parse_command("take sword!")

        # The "sword!" token won't match "sword" but is passed through as noun
        # Handler will fail to find "sword!" in game state
        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword!")

    def test_numbers_in_input(self):
        """
        Test EC-010: Numbers in input.

        Numbers are treated as unknown words and passed through as nouns.
        """
        result = self.parser.parse_command("take 123")

        # Unknown words (including numbers) are passed through as nouns
        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "123")

    def test_unicode_input(self):
        """
        Test EC-011: Unicode characters.

        Unicode characters in unknown words are passed through as nouns.
        """
        result = self.parser.parse_command("take sẃord")

        # Unknown words (including with unicode) are passed through as nouns
        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sẃord")

    def test_raw_field_preserved(self):
        """
        Test EC-012: Original input preserved.

        Verify that the raw field contains the original input.
        """
        result = self.parser.parse_command("TAKE  the SWORD")

        self.assertIsNotNone(result)
        self.assertEqual(result.raw, "TAKE  the SWORD")


if __name__ == '__main__':
    unittest.main()
