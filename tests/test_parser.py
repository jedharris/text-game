"""
Unit tests for Parser word lookup functionality.

Tests the Parser class's ability to look up words and synonyms.
Corresponds to Test Category 3 in test-plan.md.
"""

import unittest
import os
from src.parser import Parser
from src.word_entry import WordEntry, WordType


class TestWordLookup(unittest.TestCase):
    """Test word lookup functionality."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join('tests', 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_lookup_verb(self):
        """
        Test WL-001: Look up a verb.

        Verify that a verb can be looked up by its main word
        and returns the correct WordEntry.
        """
        result = self.parser._lookup_word("take")

        # Verify result is not None
        self.assertIsNotNone(result)

        # Verify it's a WordEntry
        self.assertIsInstance(result, WordEntry)

        # Verify it's the correct word
        self.assertEqual(result.word, "take")
        self.assertEqual(result.word_type, WordType.VERB)
        self.assertEqual(result.value, 1)

    def test_lookup_verb_synonym(self):
        """
        Test WL-002: Look up verb by synonym.

        Verify that a verb can be found using any of its synonyms
        and returns the main word's entry.
        """
        # "grab" is a synonym for "take"
        result = self.parser._lookup_word("grab")

        # Verify result is not None
        self.assertIsNotNone(result)

        # Verify it returns the main word entry
        self.assertEqual(result.word, "take")
        self.assertEqual(result.word_type, WordType.VERB)

        # Verify all synonyms are present
        self.assertIn("grab", result.synonyms)
        self.assertIn("get", result.synonyms)
        self.assertIn("pick", result.synonyms)

    def test_lookup_unknown_word(self):
        """
        Test WL-003: Look up non-existent word.

        Verify that looking up a word that doesn't exist
        in the vocabulary returns None.
        """
        result = self.parser._lookup_word("frobulate")

        # Verify result is None
        self.assertIsNone(result)

    def test_lookup_case_insensitive(self):
        """
        Test WL-004: Verify case handling.

        Note: The test plan specifies that words should be tokenized
        to lowercase before lookup. This test verifies lowercase lookup.
        """
        # Look up lowercase (expected usage)
        result_lower = self.parser._lookup_word("take")
        self.assertIsNotNone(result_lower)
        self.assertEqual(result_lower.word, "take")

        # Looking up uppercase should fail (since vocabulary is lowercase)
        result_upper = self.parser._lookup_word("TAKE")
        self.assertIsNone(result_upper)

        # Looking up mixed case should fail
        result_mixed = self.parser._lookup_word("Take")
        self.assertIsNone(result_mixed)

    def test_lookup_direction_synonym(self):
        """
        Test WL-005: Find direction by synonym.

        Verify that directions can be found using their
        short form synonyms (e.g., "n" for "north").
        """
        # Look up by synonym
        result = self.parser._lookup_word("n")

        # Verify result is not None
        self.assertIsNotNone(result)

        # Verify it returns the main direction entry
        self.assertEqual(result.word, "north")
        self.assertEqual(result.word_type, WordType.DIRECTION)
        self.assertEqual(result.value, 1)

        # Verify synonym is in the list
        self.assertIn("n", result.synonyms)

    def test_lookup_multiple_synonyms(self):
        """
        Test WL-006: Word with multiple synonyms.

        Verify that all synonyms for a word return the same
        WordEntry object.
        """
        # "take" has synonyms: "get", "grab", "pick"
        result_get = self.parser._lookup_word("get")
        result_grab = self.parser._lookup_word("grab")
        result_pick = self.parser._lookup_word("pick")
        result_take = self.parser._lookup_word("take")

        # All should be the same WordEntry
        self.assertIsNotNone(result_get)
        self.assertIsNotNone(result_grab)
        self.assertIsNotNone(result_pick)
        self.assertIsNotNone(result_take)

        # All should point to "take"
        self.assertEqual(result_get.word, "take")
        self.assertEqual(result_grab.word, "take")
        self.assertEqual(result_pick.word, "take")
        self.assertEqual(result_take.word, "take")

        # All should be the exact same object (not just equal)
        self.assertIs(result_get, result_take)
        self.assertIs(result_grab, result_take)
        self.assertIs(result_pick, result_take)

    def test_lookup_preposition(self):
        """
        Test WL-007: Look up preposition.

        Verify that prepositions can be looked up correctly,
        including those specified as simple strings.
        """
        result = self.parser._lookup_word("with")

        # Verify result is not None
        self.assertIsNotNone(result)

        # Verify it's the correct word
        self.assertEqual(result.word, "with")
        self.assertEqual(result.word_type, WordType.PREPOSITION)

    def test_lookup_article(self):
        """
        Test WL-008: Look up article.

        Verify that articles can be looked up correctly,
        including those specified as simple strings.
        """
        result = self.parser._lookup_word("the")

        # Verify result is not None
        self.assertIsNotNone(result)

        # Verify it's the correct word
        self.assertEqual(result.word, "the")
        self.assertEqual(result.word_type, WordType.ARTICLE)

    def test_lookup_adjective(self):
        """
        Test WL-009: Look up adjective.

        Verify that adjectives can be looked up correctly.
        """
        result = self.parser._lookup_word("rusty")

        # Verify result is not None
        self.assertIsNotNone(result)

        # Verify it's the correct word
        self.assertEqual(result.word, "rusty")
        self.assertEqual(result.word_type, WordType.ADJECTIVE)


class TestLookupTableOptimization(unittest.TestCase):
    """Test the lookup table optimization."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join('tests', 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_lookup_table_created(self):
        """Verify lookup table is created during initialization."""
        self.assertIsNotNone(self.parser.word_lookup)
        self.assertIsInstance(self.parser.word_lookup, dict)

    def test_lookup_table_contains_all_words(self):
        """Verify all main words are in lookup table."""
        for entry in self.parser.word_table:
            self.assertIn(entry.word, self.parser.word_lookup)
            self.assertEqual(self.parser.word_lookup[entry.word], entry)

    def test_lookup_table_contains_all_synonyms(self):
        """Verify all synonyms are in lookup table."""
        for entry in self.parser.word_table:
            for synonym in entry.synonyms:
                self.assertIn(synonym, self.parser.word_lookup)
                self.assertEqual(self.parser.word_lookup[synonym], entry)

    def test_lookup_table_size(self):
        """Verify lookup table has correct number of entries."""
        # Count main words + synonyms
        expected_count = 0
        for entry in self.parser.word_table:
            expected_count += 1  # The main word
            expected_count += len(entry.synonyms)  # All synonyms

        self.assertEqual(len(self.parser.word_lookup), expected_count)


class TestArticleFiltering(unittest.TestCase):
    """Test article filtering functionality."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join('tests', 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_filter_the(self):
        """
        Test AF-001: Filter "the".

        Verify that "the" is filtered from commands and the result
        is the same as without "the".
        """
        result = self.parser.parse_command("take the sword")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")
        self.assertEqual(result.raw, "take the sword")

    def test_filter_a(self):
        """
        Test AF-002: Filter "a".

        Verify that "a" is filtered from commands.
        """
        result = self.parser.parse_command("take a sword")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")

    def test_filter_an(self):
        """
        Test AF-003: Filter "an".

        Verify that "an" is filtered from commands.
        """
        result = self.parser.parse_command("take an sword")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")

    def test_multiple_articles(self):
        """
        Test AF-004: Multiple articles.

        Verify that multiple articles are all filtered.
        """
        result = self.parser.parse_command("take the a sword")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")

    def test_article_with_adjective(self):
        """
        Test AF-005: Article before adjective.

        Verify that articles are filtered correctly when
        adjectives are present.
        """
        result = self.parser.parse_command("take the rusty key")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_adjective.word, "rusty")
        self.assertEqual(result.direct_object.word, "key")

    def test_article_complex(self):
        """
        Test AF-006: Article in complex command.

        Verify that multiple articles are filtered from
        complex 6-word commands.
        """
        result = self.parser.parse_command("unlock the rusty door with the iron key")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "unlock")
        self.assertEqual(result.direct_adjective.word, "rusty")
        self.assertEqual(result.direct_object.word, "door")
        self.assertEqual(result.preposition.word, "with")
        self.assertEqual(result.indirect_adjective.word, "iron")
        self.assertEqual(result.indirect_object.word, "key")

    def test_no_article(self):
        """
        Test AF-007: No article present.

        Verify that commands without articles work correctly.
        """
        result = self.parser.parse_command("take sword")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")


if __name__ == '__main__':
    unittest.main()
