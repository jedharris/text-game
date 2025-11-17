"""
Unit tests for WordEntry and WordType classes.

Tests the fundamental data structures used by the parser.
Corresponds to Test Category 1 in test-plan.md.
"""

import unittest
from src.word_entry import WordEntry, WordType


class TestWordEntry(unittest.TestCase):
    """Test WordEntry dataclass functionality."""

    def test_word_entry_creation(self):
        """
        Test WE-001: Create WordEntry with all fields.

        Verify that a WordEntry can be created with all fields populated
        and that all values are accessible.
        """
        # Create entry with all fields
        entry = WordEntry(
            word="take",
            word_type=WordType.VERB,
            synonyms=["get", "grab"],
            value=1
        )

        # Verify all fields are set correctly
        self.assertEqual(entry.word, "take")
        self.assertEqual(entry.word_type, WordType.VERB)
        self.assertEqual(entry.synonyms, ["get", "grab"])
        self.assertEqual(entry.value, 1)

        # Verify synonyms is a list
        self.assertIsInstance(entry.synonyms, list)
        self.assertEqual(len(entry.synonyms), 2)

    def test_word_entry_no_synonyms(self):
        """
        Test WE-002: Create WordEntry without synonyms.

        Verify that when synonyms are not provided, the field defaults
        to an empty list rather than None.
        """
        # Create entry without synonyms
        entry = WordEntry(
            word="door",
            word_type=WordType.NOUN,
            value=101
        )

        # Verify synonyms defaults to empty list
        self.assertIsNotNone(entry.synonyms)
        self.assertEqual(entry.synonyms, [])
        self.assertIsInstance(entry.synonyms, list)

        # Verify other fields
        self.assertEqual(entry.word, "door")
        self.assertEqual(entry.word_type, WordType.NOUN)
        self.assertEqual(entry.value, 101)

    def test_word_entry_no_value(self):
        """
        Test WE-003: Create WordEntry without value.

        Verify that the value field is optional and defaults to None.
        This is common for prepositions and articles which don't need
        numeric identifiers.
        """
        # Create entry without value
        entry = WordEntry(
            word="with",
            word_type=WordType.PREPOSITION
        )

        # Verify value is None
        self.assertIsNone(entry.value)

        # Verify other fields
        self.assertEqual(entry.word, "with")
        self.assertEqual(entry.word_type, WordType.PREPOSITION)
        self.assertEqual(entry.synonyms, [])

    def test_word_type_enum(self):
        """
        Test WE-004: Verify WordType enum values.

        Verify that all expected word types are defined in the enum
        and that they have the correct string values.
        """
        # Test all enum values exist and have correct string values
        self.assertEqual(WordType.VERB.value, "VERB")
        self.assertEqual(WordType.NOUN.value, "NOUN")
        self.assertEqual(WordType.ADJECTIVE.value, "ADJECTIVE")
        self.assertEqual(WordType.PREPOSITION.value, "PREPOSITION")
        self.assertEqual(WordType.DIRECTION.value, "DIRECTION")
        self.assertEqual(WordType.ARTICLE.value, "ARTICLE")

        # Verify enum membership
        self.assertIn(WordType.VERB, WordType)
        self.assertIn(WordType.NOUN, WordType)
        self.assertIn(WordType.ADJECTIVE, WordType)
        self.assertIn(WordType.PREPOSITION, WordType)
        self.assertIn(WordType.DIRECTION, WordType)
        self.assertIn(WordType.ARTICLE, WordType)

        # Verify we can compare enum values
        verb_type = WordType.VERB
        self.assertEqual(verb_type, WordType.VERB)
        self.assertNotEqual(verb_type, WordType.NOUN)

    def test_word_entry_equality(self):
        """
        Test WE-005: Compare two WordEntry objects.

        Verify that two WordEntry objects with identical values
        are considered equal (dataclass equality).
        """
        # Create two identical entries
        entry1 = WordEntry(
            word="take",
            word_type=WordType.VERB,
            synonyms=["get", "grab"],
            value=1
        )

        entry2 = WordEntry(
            word="take",
            word_type=WordType.VERB,
            synonyms=["get", "grab"],
            value=1
        )

        # Verify they are equal
        self.assertEqual(entry1, entry2)

        # Create a different entry
        entry3 = WordEntry(
            word="drop",
            word_type=WordType.VERB,
            synonyms=["put", "place"],
            value=2
        )

        # Verify they are not equal
        self.assertNotEqual(entry1, entry3)

        # Test entries differing only in one field
        entry4 = WordEntry(
            word="take",
            word_type=WordType.VERB,
            synonyms=["get", "grab"],
            value=2  # Different value
        )

        self.assertNotEqual(entry1, entry4)

    def test_word_entry_string_repr(self):
        """
        Test WE-006: Test string representation.

        Verify that WordEntry has a readable string representation
        that can be used for debugging and logging.
        """
        # Create a word entry
        entry = WordEntry(
            word="take",
            word_type=WordType.VERB,
            synonyms=["get"],
            value=1
        )

        # Get string representation
        entry_str = str(entry)

        # Verify it contains key information
        self.assertIn("take", entry_str)
        self.assertIn("VERB", entry_str)

        # Verify repr also works
        entry_repr = repr(entry)
        self.assertIn("WordEntry", entry_repr)
        self.assertIn("take", entry_repr)

    def test_word_entry_synonyms_mutability(self):
        """
        Additional test: Verify synonyms list can be modified.

        This ensures that the synonyms list is mutable and can be
        updated if needed during runtime.
        """
        entry = WordEntry(
            word="examine",
            word_type=WordType.VERB,
            synonyms=["look"]
        )

        # Verify we can add to synonyms
        entry.synonyms.append("inspect")
        self.assertEqual(len(entry.synonyms), 2)
        self.assertIn("look", entry.synonyms)
        self.assertIn("inspect", entry.synonyms)

    def test_word_entry_explicit_none_synonyms(self):
        """
        Additional test: Verify __post_init__ handles explicit None.

        Tests that if synonyms is explicitly set to None, the
        __post_init__ method converts it to an empty list.
        """
        # Create entry with synonyms=None explicitly
        entry = WordEntry(
            word="north",
            word_type=WordType.DIRECTION,
            synonyms=None,
            value=1
        )

        # Verify it was converted to empty list
        self.assertIsNotNone(entry.synonyms)
        self.assertEqual(entry.synonyms, [])
        self.assertIsInstance(entry.synonyms, list)

    def test_word_entry_empty_synonyms_list(self):
        """
        Additional test: Verify empty list synonyms.

        Tests that an explicitly provided empty list is preserved.
        """
        entry = WordEntry(
            word="open",
            word_type=WordType.VERB,
            synonyms=[],
            value=5
        )

        self.assertEqual(entry.synonyms, [])
        self.assertIsInstance(entry.synonyms, list)

    def test_word_type_enum_iteration(self):
        """
        Additional test: Verify we can iterate over WordType enum.

        Useful for validation and documentation purposes.
        """
        # Get all word types
        all_types = list(WordType)

        # Verify we have exactly 7 types (added FILENAME)
        self.assertEqual(len(all_types), 7)

        # Verify specific types are present
        self.assertIn(WordType.VERB, all_types)
        self.assertIn(WordType.NOUN, all_types)
        self.assertIn(WordType.ADJECTIVE, all_types)
        self.assertIn(WordType.PREPOSITION, all_types)
        self.assertIn(WordType.DIRECTION, all_types)
        self.assertIn(WordType.FILENAME, all_types)
        self.assertIn(WordType.ARTICLE, all_types)

    def test_word_entry_different_word_types(self):
        """
        Additional test: Create WordEntry instances for each word type.

        Ensures WordEntry works correctly with all possible WordType values.
        """
        # Test each word type
        test_cases = [
            ("take", WordType.VERB, 1),
            ("sword", WordType.NOUN, 101),
            ("rusty", WordType.ADJECTIVE, 201),
            ("with", WordType.PREPOSITION, None),
            ("north", WordType.DIRECTION, 1),
            ("the", WordType.ARTICLE, None),
        ]

        for word, word_type, value in test_cases:
            with self.subTest(word=word, word_type=word_type):
                entry = WordEntry(
                    word=word,
                    word_type=word_type,
                    value=value
                )

                self.assertEqual(entry.word, word)
                self.assertEqual(entry.word_type, word_type)
                self.assertEqual(entry.value, value)
                self.assertEqual(entry.synonyms, [])

    def test_word_entry_multiple_synonyms(self):
        """
        Additional test: Test WordEntry with many synonyms.

        Verifies that the synonyms list can hold multiple values
        as needed for words with many alternatives.
        """
        entry = WordEntry(
            word="attack",
            word_type=WordType.VERB,
            synonyms=["hit", "strike", "fight", "kill", "slay"],
            value=7
        )

        self.assertEqual(len(entry.synonyms), 5)
        self.assertIn("hit", entry.synonyms)
        self.assertIn("strike", entry.synonyms)
        self.assertIn("fight", entry.synonyms)
        self.assertIn("kill", entry.synonyms)
        self.assertIn("slay", entry.synonyms)

    def test_word_entry_field_types(self):
        """
        Additional test: Verify field type constraints.

        Ensures that WordEntry fields accept the correct types.
        """
        # Valid entry with correct types
        entry = WordEntry(
            word="test",
            word_type=WordType.VERB,
            synonyms=["check"],
            value=99
        )

        # Verify types
        self.assertIsInstance(entry.word, str)
        self.assertIsInstance(entry.word_type, WordType)
        self.assertIsInstance(entry.synonyms, list)
        self.assertIsInstance(entry.value, int)

        # Entry with None value
        entry2 = WordEntry(
            word="test",
            word_type=WordType.VERB
        )

        self.assertIsNone(entry2.value)


class TestWordTypeEnum(unittest.TestCase):
    """Additional tests specifically for the WordType enum."""

    def test_word_type_comparison(self):
        """Test that WordType enum values can be compared."""
        self.assertEqual(WordType.VERB, WordType.VERB)
        self.assertNotEqual(WordType.VERB, WordType.NOUN)

    def test_word_type_in_list(self):
        """Test that WordType can be used in lists and sets."""
        word_types = [WordType.VERB, WordType.NOUN, WordType.ADJECTIVE]

        self.assertIn(WordType.VERB, word_types)
        self.assertIn(WordType.NOUN, word_types)
        self.assertNotIn(WordType.DIRECTION, word_types)

    def test_word_type_as_dict_key(self):
        """Test that WordType can be used as dictionary keys."""
        type_counts = {
            WordType.VERB: 10,
            WordType.NOUN: 15,
            WordType.ADJECTIVE: 8
        }

        self.assertEqual(type_counts[WordType.VERB], 10)
        self.assertEqual(type_counts[WordType.NOUN], 15)
        self.assertNotIn(WordType.DIRECTION, type_counts)

    def test_word_type_string_value(self):
        """Test accessing the string value of WordType."""
        self.assertEqual(WordType.VERB.value, "VERB")
        self.assertEqual(WordType.NOUN.value, "NOUN")

    def test_word_type_name(self):
        """Test accessing the name of WordType enum members."""
        self.assertEqual(WordType.VERB.name, "VERB")
        self.assertEqual(WordType.NOUN.name, "NOUN")


if __name__ == '__main__':
    unittest.main()
