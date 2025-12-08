"""
Unit tests for vocabulary loading functionality.

Tests the Parser class's ability to load and parse vocabulary from JSON files.
Corresponds to Test Category 2 in test-plan.md.
"""

import unittest
import os
import json
from src.parser import Parser
from src.word_entry import WordEntry, WordType


class TestVocabularyLoading(unittest.TestCase):
    """Test vocabulary file loading functionality."""

    def setUp(self):
        """Set up test fixtures path."""
        self.fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')

    def test_load_complete_vocabulary(self):
        """
        Test VL-001: Load complete vocabulary file.

        Verify that a complete vocabulary file with all word types
        is loaded correctly and all entries are accessible.
        """
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        # Verify word table is populated
        self.assertIsNotNone(parser.word_table)
        self.assertGreater(len(parser.word_table), 0)

        # Count word types (note: directions have multi-valued type {NOUN, ADJECTIVE}, "open" has {VERB, ADJECTIVE})
        verbs = [w for w in parser.word_table if w.word_type == WordType.VERB or (isinstance(w.word_type, set) and WordType.VERB in w.word_type)]
        nouns = [w for w in parser.word_table if w.word_type == WordType.NOUN or (isinstance(w.word_type, set) and WordType.NOUN in w.word_type)]
        adjectives = [w for w in parser.word_table if w.word_type == WordType.ADJECTIVE or (isinstance(w.word_type, set) and WordType.ADJECTIVE in w.word_type)]
        prepositions = [w for w in parser.word_table if w.word_type == WordType.PREPOSITION]
        # Directions now have word_type = {NOUN, ADJECTIVE}
        directions = [w for w in parser.word_table if isinstance(w.word_type, set) and w.word_type == {WordType.NOUN, WordType.ADJECTIVE}]
        articles = [w for w in parser.word_table if w.word_type == WordType.ARTICLE]

        # Verify all types are present
        # Directions now have multi-valued type {NOUN, ADJECTIVE, VERB}
        self.assertEqual(len(verbs), 20)  # 10 regular verbs + 10 directions (multi-valued)
        self.assertEqual(len(nouns), 22)  # 12 regular nouns + 10 directions (multi-valued)
        self.assertEqual(len(adjectives), 21)  # 10 regular adjectives + 10 directions (multi-valued) + 1 "open" (multi-valued from verb)
        self.assertEqual(len(prepositions), 8)
        self.assertEqual(len(directions), 0)  # Directions now have {NOUN, ADJECTIVE, VERB}, not just {NOUN, ADJECTIVE}
        self.assertEqual(len(articles), 3)

        # Verify total count
        # 12 regular nouns + 10 directions + 10 verbs + 10 adjectives + 8 preps + 3 articles = 53
        self.assertEqual(len(parser.word_table), 53)

    def test_load_minimal_vocabulary(self):
        """
        Test VL-002: Load minimal vocabulary.

        Verify that a minimal vocabulary file with one entry per type
        is loaded correctly.
        """
        vocab_file = os.path.join(self.fixtures_path, 'minimal_vocabulary.json')
        parser = Parser(vocab_file)

        # Verify word table is populated
        self.assertIsNotNone(parser.word_table)
        self.assertEqual(len(parser.word_table), 6)

        # Verify one of each type (directions now have multi-valued type)
        verbs = [w for w in parser.word_table if w.word_type == WordType.VERB]
        nouns = [w for w in parser.word_table if w.word_type == WordType.NOUN or (isinstance(w.word_type, set) and WordType.NOUN in w.word_type)]
        adjectives = [w for w in parser.word_table if w.word_type == WordType.ADJECTIVE or (isinstance(w.word_type, set) and WordType.ADJECTIVE in w.word_type)]
        prepositions = [w for w in parser.word_table if w.word_type == WordType.PREPOSITION]
        directions = [w for w in parser.word_table if isinstance(w.word_type, set) and w.word_type == {WordType.NOUN, WordType.ADJECTIVE}]
        articles = [w for w in parser.word_table if w.word_type == WordType.ARTICLE]

        self.assertEqual(len(verbs), 1)
        self.assertEqual(len(nouns), 2)  # 1 regular noun + 1 direction
        self.assertEqual(len(adjectives), 2)  # 1 regular adjective + 1 direction
        self.assertEqual(len(prepositions), 1)
        self.assertEqual(len(directions), 1)
        self.assertEqual(len(articles), 1)

    def test_load_empty_vocabulary(self):
        """
        Test VL-003: Load empty vocabulary.

        Verify that an empty vocabulary file (with empty arrays)
        loads without error and creates an empty word table.
        """
        vocab_file = os.path.join(self.fixtures_path, 'empty_vocabulary.json')
        parser = Parser(vocab_file)

        # Verify word table exists but is empty
        self.assertIsNotNone(parser.word_table)
        self.assertEqual(len(parser.word_table), 0)

    def test_load_missing_file(self):
        """
        Test VL-004: Load non-existent file.

        Verify that attempting to load a non-existent file
        raises FileNotFoundError.
        """
        vocab_file = os.path.join(self.fixtures_path, 'nonexistent.json')

        with self.assertRaises(FileNotFoundError):
            Parser(vocab_file)

    def test_load_invalid_json(self):
        """
        Test VL-005: Load malformed JSON.

        Verify that attempting to load a file with invalid JSON
        raises JSONDecodeError.
        """
        vocab_file = os.path.join(self.fixtures_path, 'invalid_vocabulary.json')

        with self.assertRaises(json.JSONDecodeError):
            Parser(vocab_file)

    def test_verb_synonyms_loaded(self):
        """
        Test VL-006: Verify verb synonyms.

        Verify that verb synonyms are loaded correctly and
        accessible in the WordEntry.
        """
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        # Find the "take" verb
        take_verb = None
        for entry in parser.word_table:
            if entry.word == "take" and entry.word_type == WordType.VERB:
                take_verb = entry
                break

        # Verify it was found
        self.assertIsNotNone(take_verb)

        # Verify synonyms
        self.assertIn("get", take_verb.synonyms)
        self.assertIn("grab", take_verb.synonyms)
        self.assertIn("pick", take_verb.synonyms)
        self.assertEqual(len(take_verb.synonyms), 3)

        # Verify value
        self.assertEqual(take_verb.value, 1)

    def test_direction_synonyms_loaded(self):
        """
        Test VL-007: Verify direction synonyms.

        Verify that direction synonyms are loaded correctly,
        particularly the short forms like "n" for "north".
        """
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        # Find the "north" direction (now has multi-valued type {NOUN, ADJECTIVE, VERB})
        north_dir = None
        for entry in parser.word_table:
            if entry.word == "north" and isinstance(entry.word_type, set) and WordType.NOUN in entry.word_type:
                north_dir = entry
                break

        # Verify it was found
        self.assertIsNotNone(north_dir)

        # Verify it has NOUN, ADJECTIVE, and VERB types
        self.assertIn(WordType.NOUN, north_dir.word_type)
        self.assertIn(WordType.ADJECTIVE, north_dir.word_type)
        self.assertIn(WordType.VERB, north_dir.word_type)

        # Verify synonyms
        self.assertIn("n", north_dir.synonyms)
        self.assertEqual(len(north_dir.synonyms), 1)

        # Verify value and object_required
        self.assertEqual(north_dir.value, 1)
        self.assertFalse(north_dir.object_required)

    def test_preposition_loading(self):
        """
        Test VL-008: Load simple string prepositions.

        Verify that prepositions specified as simple strings
        (not objects) are loaded correctly.
        """
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        # Find prepositions
        prepositions = [w for w in parser.word_table if w.word_type == WordType.PREPOSITION]

        # Verify we have prepositions
        self.assertGreater(len(prepositions), 0)

        # Find specific preposition
        with_prep = None
        for entry in prepositions:
            if entry.word == "with":
                with_prep = entry
                break

        # Verify it was found
        self.assertIsNotNone(with_prep)

        # Verify it's a proper WordEntry
        self.assertEqual(with_prep.word_type, WordType.PREPOSITION)
        self.assertEqual(with_prep.word, "with")

        # Verify defaults for simple strings
        self.assertEqual(with_prep.synonyms, [])
        self.assertIsNone(with_prep.value)

    def test_article_loading(self):
        """
        Test VL-009: Load simple string articles.

        Verify that articles specified as simple strings
        are loaded correctly.
        """
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        # Find articles
        articles = [w for w in parser.word_table if w.word_type == WordType.ARTICLE]

        # Verify we have exactly 3 articles
        self.assertEqual(len(articles), 3)

        # Verify specific articles
        article_words = [a.word for a in articles]
        self.assertIn("the", article_words)
        self.assertIn("a", article_words)
        self.assertIn("an", article_words)

        # Verify defaults for simple strings
        for article in articles:
            self.assertEqual(article.synonyms, [])
            self.assertIsNone(article.value)

    def test_value_field_optional(self):
        """
        Test VL-010: Verify value field is optional.

        Verify that entries without a value field are loaded
        correctly with value=None.
        """
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        # Find a preposition (which shouldn't have values in our test file)
        prepositions = [w for w in parser.word_table if w.word_type == WordType.PREPOSITION]

        self.assertGreater(len(prepositions), 0)

        # Verify at least one has no value
        has_none_value = any(p.value is None for p in prepositions)
        self.assertTrue(has_none_value)

    def test_missing_sections(self):
        """
        Test VL-011: Handle missing JSON sections.

        Verify that missing sections in the JSON default to empty
        and don't cause errors.
        """
        # Create a temporary vocabulary file with missing sections
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "verbs": [{"word": "test", "value": 1}],
                # Missing: nouns, adjectives, prepositions, directions, articles
            }, f)
            temp_file = f.name

        try:
            # Load the vocabulary
            parser = Parser(temp_file)

            # Verify word table has only verbs
            self.assertEqual(len(parser.word_table), 1)
            verbs = [w for w in parser.word_table if w.word_type == WordType.VERB]
            self.assertEqual(len(verbs), 1)

            # Verify other types are empty
            nouns = [w for w in parser.word_table if w.word_type == WordType.NOUN]
            self.assertEqual(len(nouns), 0)

        finally:
            # Clean up temp file
            os.unlink(temp_file)

    def test_word_table_size(self):
        """
        Test VL-012: Verify correct number of entries.

        Verify that the word table contains exactly the expected
        number of entries based on the vocabulary file.
        """
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        # Count expected entries from the JSON file
        with open(vocab_file, 'r') as f:
            vocab = json.load(f)

        # Note: directions are now in nouns array, no separate directions array
        expected_count = (
            len(vocab['verbs']) +
            len(vocab['nouns']) +
            len(vocab['adjectives']) +
            len(vocab['prepositions']) +
            len(vocab['articles'])
        )

        # Verify word table size matches
        self.assertEqual(len(parser.word_table), expected_count)
        # 12 regular nouns + 10 directions + 10 verbs + 10 adjectives + 8 preps + 3 articles = 53
        self.assertEqual(len(parser.word_table), 53)


class TestVocabularyDetails(unittest.TestCase):
    """Additional tests for vocabulary loading details."""

    def setUp(self):
        """Set up test fixtures path."""
        self.fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')

    def test_all_word_types_are_word_entries(self):
        """Verify all loaded items are WordEntry instances."""
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        for entry in parser.word_table:
            self.assertIsInstance(entry, WordEntry)

    def test_no_duplicate_words(self):
        """Verify no duplicate words in word table (within same type)."""
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        # Group by word type and check for duplicates
        for word_type in WordType:
            words_of_type = [w.word for w in parser.word_table if w.word_type == word_type]
            # Check no duplicates
            self.assertEqual(len(words_of_type), len(set(words_of_type)),
                           f"Duplicate words found in {word_type}")

    def test_empty_synonyms_default(self):
        """Verify entries without synonyms have empty list, not None."""
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        for entry in parser.word_table:
            self.assertIsNotNone(entry.synonyms)
            self.assertIsInstance(entry.synonyms, list)

    def test_verb_with_empty_synonyms(self):
        """Verify verbs with empty synonym arrays work correctly."""
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        parser = Parser(vocab_file)

        # Find "go" verb which has empty synonyms
        go_verb = None
        for entry in parser.word_table:
            if entry.word == "go" and entry.word_type == WordType.VERB:
                go_verb = entry
                break

        self.assertIsNotNone(go_verb)
        self.assertEqual(go_verb.synonyms, [])
        self.assertEqual(go_verb.value, 4)


if __name__ == '__main__':
    unittest.main()
