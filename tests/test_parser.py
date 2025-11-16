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


class TestParserIntegration(unittest.TestCase):
    """Integration tests for full game scenarios."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join('tests', 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_full_game_scenario_1(self):
        """
        Test IT-001: Complete game scenario.

        Test a series of commands that might occur in a real game.
        """
        commands = [
            ("north", lambda r: r.direction and r.direction.word == "north"),
            ("take sword", lambda r: r.verb.word == "take" and r.direct_object.word == "sword"),
            ("examine the sword", lambda r: r.verb.word == "examine" and r.direct_object.word == "sword"),
            ("go west", lambda r: r.verb.word == "go" and r.direction.word == "west"),
            ("unlock door with key", lambda r: r.verb.word == "unlock" and r.direct_object.word == "door" and r.indirect_object.word == "key"),
        ]

        for command_str, validator in commands:
            result = self.parser.parse_command(command_str)
            self.assertIsNotNone(result, f"Failed to parse: {command_str}")
            self.assertTrue(validator(result), f"Validation failed for: {command_str}")

    def test_full_game_scenario_2(self):
        """
        Test IT-002: Combat scenario.

        Test combat-related commands.
        """
        commands = [
            "attack goblin",
            "hit the goblin",
            "strike goblin with sword",
            "kill goblin",
        ]

        for command_str in commands:
            result = self.parser.parse_command(command_str)
            self.assertIsNotNone(result, f"Failed to parse: {command_str}")
            # All should have attack verb (or synonym)
            self.assertIsNotNone(result.verb)
            self.assertEqual(result.verb.word, "attack")

    def test_exploration_scenario(self):
        """
        Test IT-003: Exploration commands.

        Test movement and examination commands.
        """
        commands = [
            ("north", "direction"),
            ("n", "direction"),
            ("go south", "verb_direction"),
            ("examine door", "verb_noun"),
            ("look in chest", "verb_prep_noun"),
            ("examine the red potion", "verb_adj_noun"),
        ]

        for command_str, expected_type in commands:
            result = self.parser.parse_command(command_str)
            self.assertIsNotNone(result, f"Failed to parse: {command_str}")
            self.assertEqual(result.raw, command_str)

    def test_inventory_scenario(self):
        """
        Test IT-004: Inventory management.

        Test taking, dropping, and using items.
        """
        # Take various items
        take_commands = [
            "take key",
            "get the sword",
            "grab potion",
            "pick rusty key",
            "take the golden coin",
        ]

        for command_str in take_commands:
            result = self.parser.parse_command(command_str)
            self.assertIsNotNone(result, f"Failed to parse: {command_str}")
            self.assertEqual(result.verb.word, "take")
            self.assertIsNotNone(result.direct_object)

        # Drop items
        drop_result = self.parser.parse_command("drop sword")
        self.assertIsNotNone(drop_result)
        self.assertEqual(drop_result.verb.word, "drop")

        # Use items
        use_result = self.parser.parse_command("use key")
        self.assertIsNotNone(use_result)
        self.assertEqual(use_result.verb.word, "use")

    def test_puzzle_scenario(self):
        """
        Test IT-005: Puzzle solving.

        Test complex multi-word commands for puzzles.
        """
        complex_commands = [
            "unlock rusty door with iron key",
            "put the red potion on table",
            "examine ancient book",
            "open wooden chest",
            "look under small table",
            "take golden key from chest",
        ]

        for command_str in complex_commands:
            result = self.parser.parse_command(command_str)
            self.assertIsNotNone(result, f"Failed to parse: {command_str}")
            self.assertIsNotNone(result.verb)

    def test_parser_reuse(self):
        """
        Test IT-006: Reuse parser instance.

        Verify that the same parser can be used for multiple
        parse calls without state corruption.
        """
        # Parse same command multiple times
        for _ in range(10):
            result = self.parser.parse_command("take sword")
            self.assertIsNotNone(result)
            self.assertEqual(result.verb.word, "take")
            self.assertEqual(result.direct_object.word, "sword")

        # Parse different commands
        commands = [
            "north",
            "take key",
            "examine door",
            "unlock door with key",
            "go south",
        ]

        for command_str in commands:
            result = self.parser.parse_command(command_str)
            self.assertIsNotNone(result, f"Failed to parse: {command_str}")

        # Verify word table hasn't changed size
        original_size = len(self.parser.word_table)
        for _ in range(5):
            self.parser.parse_command("take sword")
        self.assertEqual(len(self.parser.word_table), original_size)

    def test_synonym_consistency(self):
        """
        Test IT-007: Synonym consistency.

        Verify that synonyms produce consistent results with
        their main words.
        """
        # Test verb synonyms
        synonym_pairs = [
            ("take sword", "grab sword"),
            ("take sword", "get sword"),
            ("take sword", "pick sword"),
            ("examine door", "look door"),
            ("examine door", "inspect door"),
            ("attack goblin", "hit goblin"),
            ("attack goblin", "strike goblin"),
            ("attack goblin", "kill goblin"),
            ("drop key", "put key"),
            ("drop key", "place key"),
            ("eat flask", "consume flask"),
        ]

        for main_cmd, synonym_cmd in synonym_pairs:
            result_main = self.parser.parse_command(main_cmd)
            result_synonym = self.parser.parse_command(synonym_cmd)

            self.assertIsNotNone(result_main, f"Failed to parse: {main_cmd}")
            self.assertIsNotNone(result_synonym, f"Failed to parse: {synonym_cmd}")

            # Both should resolve to the same verb
            self.assertEqual(result_main.verb.word, result_synonym.verb.word,
                           f"{main_cmd} and {synonym_cmd} should have same verb")

            # Both should have same direct object
            if result_main.direct_object:
                self.assertEqual(result_main.direct_object.word,
                               result_synonym.direct_object.word,
                               f"{main_cmd} and {synonym_cmd} should have same object")

        # Test direction synonyms
        direction_pairs = [
            ("north", "n"),
            ("south", "s"),
            ("east", "e"),
            ("west", "w"),
            ("up", "u"),
            ("down", "d"),
        ]

        for main_cmd, synonym_cmd in direction_pairs:
            result_main = self.parser.parse_command(main_cmd)
            result_synonym = self.parser.parse_command(synonym_cmd)

            self.assertIsNotNone(result_main)
            self.assertIsNotNone(result_synonym)
            self.assertEqual(result_main.direction.word, result_synonym.direction.word)


if __name__ == '__main__':
    unittest.main()
