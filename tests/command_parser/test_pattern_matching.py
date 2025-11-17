"""
Unit tests for pattern matching functionality.

Tests the Parser class's ability to match command patterns.
Corresponds to Test Categories 4-7 in test-plan.md.
"""

import unittest
import os
from src.parser import Parser
from src.parsed_command import ParsedCommand
from src.word_entry import WordType


class TestPatternMatching12Words(unittest.TestCase):
    """Test pattern matching for 1-2 word commands."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_single_direction(self):
        """
        Test PM-001: Single direction word.

        Verify that a single direction word is parsed correctly
        with only the direction field populated.
        """
        # Look up the words
        north = self.parser._lookup_word("north")

        # Create list of entries (simulating tokenization)
        entries = [north]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ParsedCommand)
        self.assertEqual(result.direction, north)
        self.assertEqual(result.direction.word, "north")
        self.assertIsNone(result.verb)
        self.assertIsNone(result.direct_object)

    def test_direction_synonym(self):
        """
        Test PM-002: Direction synonym.

        Verify that a direction synonym (like "n" for "north")
        is resolved and parsed correctly.
        """
        # Look up by synonym
        n = self.parser._lookup_word("n")

        # Create list of entries
        entries = [n]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.direction, n)
        self.assertEqual(result.direction.word, "north")

    def test_verb_noun(self):
        """
        Test PM-003: Basic verb + noun.

        Verify that a simple verb-noun command like "take sword"
        is parsed correctly.
        """
        # Look up words
        take = self.parser._lookup_word("take")
        sword = self.parser._lookup_word("sword")

        # Create list of entries
        entries = [take, sword]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, take)
        self.assertEqual(result.direct_object, sword)
        self.assertIsNone(result.direction)

    def test_verb_direction(self):
        """
        Test PM-004: Verb + direction.

        Verify that "go north" style commands are parsed correctly
        with both verb and direction populated.
        """
        # Look up words
        go = self.parser._lookup_word("go")
        north = self.parser._lookup_word("north")

        # Create list of entries
        entries = [go, north]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, go)
        self.assertEqual(result.direction, north)
        self.assertIsNone(result.direct_object)

    def test_verb_direction_synonym(self):
        """
        Test PM-005: Verb + direction synonym.

        Verify that "go n" is parsed the same as "go north".
        """
        # Look up words
        go = self.parser._lookup_word("go")
        n = self.parser._lookup_word("n")

        # Create list of entries
        entries = [go, n]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, go)
        self.assertEqual(result.direction, n)
        self.assertEqual(result.direction.word, "north")

    def test_synonym_verb_noun(self):
        """
        Test PM-006: Synonym verb + noun.

        Verify that verb synonyms work in patterns.
        "grab sword" should parse the same as "take sword".
        """
        # Look up words (grab is synonym for take)
        grab = self.parser._lookup_word("grab")
        sword = self.parser._lookup_word("sword")

        # Create list of entries
        entries = [grab, sword]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, grab)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object, sword)


class TestPatternMatching3Words(unittest.TestCase):
    """Test pattern matching for 3 word commands."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_verb_adjective_noun(self):
        """
        Test PM-101: Verb + adjective + noun.

        Verify that "take rusty key" parses with adjective
        modifying the direct object.
        """
        # Look up words
        take = self.parser._lookup_word("take")
        rusty = self.parser._lookup_word("rusty")
        key = self.parser._lookup_word("key")

        # Create list of entries
        entries = [take, rusty, key]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, take)
        self.assertEqual(result.direct_adjective, rusty)
        self.assertEqual(result.direct_object, key)

    def test_verb_noun_noun(self):
        """
        Test PM-102: Verb + noun + noun (implicit with).

        Verify that "unlock door key" is parsed as
        unlock door with key (implicit preposition).
        """
        # Look up words
        unlock = self.parser._lookup_word("unlock")
        door = self.parser._lookup_word("door")
        key = self.parser._lookup_word("key")

        # Create list of entries
        entries = [unlock, door, key]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, unlock)
        self.assertEqual(result.direct_object, door)
        self.assertEqual(result.indirect_object, key)
        self.assertIsNone(result.preposition)

    def test_verb_prep_noun(self):
        """
        Test PM-103: Verb + preposition + noun.

        Verify that "look in chest" is parsed correctly
        with explicit preposition.
        """
        # Look up words
        look = self.parser._lookup_word("look")
        in_prep = self.parser._lookup_word("in")
        chest = self.parser._lookup_word("chest")

        # Create list of entries
        entries = [look, in_prep, chest]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, look)
        self.assertEqual(result.preposition, in_prep)
        self.assertEqual(result.direct_object, chest)

    def test_verb_adj_noun_colors(self):
        """
        Test PM-104: Adjective for color.

        Verify that color adjectives work correctly.
        "take red key" should parse with adjective.
        """
        # Look up words
        take = self.parser._lookup_word("take")
        red = self.parser._lookup_word("red")
        key = self.parser._lookup_word("key")

        # Create list of entries
        entries = [take, red, key]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, take)
        self.assertEqual(result.direct_adjective, red)
        self.assertEqual(result.direct_object, key)

    def test_verb_adj_noun_size(self):
        """
        Test PM-105: Adjective for size.

        Verify that size adjectives work correctly.
        "examine large door" should parse with adjective.
        """
        # Look up words
        examine = self.parser._lookup_word("examine")
        large = self.parser._lookup_word("large")
        door = self.parser._lookup_word("door")

        # Create list of entries
        entries = [examine, large, door]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, examine)
        self.assertEqual(result.direct_adjective, large)
        self.assertEqual(result.direct_object, door)


class TestPatternMatching4Words(unittest.TestCase):
    """Test pattern matching for 4 word commands."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_verb_adj_noun_noun(self):
        """
        Test PM-201: Verb + adj + noun + noun.

        Verify that "unlock rusty door key" parses with
        adjective on direct object and implicit preposition.
        """
        # Look up words
        unlock = self.parser._lookup_word("unlock")
        rusty = self.parser._lookup_word("rusty")
        door = self.parser._lookup_word("door")
        key = self.parser._lookup_word("key")

        # Create list of entries
        entries = [unlock, rusty, door, key]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, unlock)
        self.assertEqual(result.direct_adjective, rusty)
        self.assertEqual(result.direct_object, door)
        self.assertEqual(result.indirect_object, key)

    def test_verb_noun_prep_noun(self):
        """
        Test PM-202: Verb + noun + prep + noun.

        Verify that "unlock door with key" parses correctly
        with explicit preposition.
        """
        # Look up words
        unlock = self.parser._lookup_word("unlock")
        door = self.parser._lookup_word("door")
        with_prep = self.parser._lookup_word("with")
        key = self.parser._lookup_word("key")

        # Create list of entries
        entries = [unlock, door, with_prep, key]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, unlock)
        self.assertEqual(result.direct_object, door)
        self.assertEqual(result.preposition, with_prep)
        self.assertEqual(result.indirect_object, key)

    def test_verb_prep_adj_noun(self):
        """
        Test PM-203: Verb + prep + adj + noun.

        Verify that "look in wooden chest" parses correctly
        with adjective on direct object after preposition.
        """
        # Look up words
        look = self.parser._lookup_word("look")
        in_prep = self.parser._lookup_word("in")
        wooden = self.parser._lookup_word("wooden")
        chest = self.parser._lookup_word("chest")

        # Create list of entries
        entries = [look, in_prep, wooden, chest]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, look)
        self.assertEqual(result.preposition, in_prep)
        self.assertEqual(result.direct_adjective, wooden)
        self.assertEqual(result.direct_object, chest)


class TestPatternMatching56Words(unittest.TestCase):
    """Test pattern matching for 5-6 word commands."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_verb_adj_noun_prep_noun(self):
        """
        Test PM-301: 5 words, adj on direct obj.

        Verify that "unlock rusty door with key" parses with
        adjective on the direct object.
        """
        # Look up words
        unlock = self.parser._lookup_word("unlock")
        rusty = self.parser._lookup_word("rusty")
        door = self.parser._lookup_word("door")
        with_prep = self.parser._lookup_word("with")
        key = self.parser._lookup_word("key")

        # Create list of entries
        entries = [unlock, rusty, door, with_prep, key]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, unlock)
        self.assertEqual(result.direct_adjective, rusty)
        self.assertEqual(result.direct_object, door)
        self.assertEqual(result.preposition, with_prep)
        self.assertEqual(result.indirect_object, key)

    def test_verb_noun_prep_adj_noun(self):
        """
        Test PM-302: 5 words, adj on indirect obj.

        Verify that "unlock door with rusty key" parses with
        adjective on the indirect object.
        """
        # Look up words
        unlock = self.parser._lookup_word("unlock")
        door = self.parser._lookup_word("door")
        with_prep = self.parser._lookup_word("with")
        rusty = self.parser._lookup_word("rusty")
        key = self.parser._lookup_word("key")

        # Create list of entries
        entries = [unlock, door, with_prep, rusty, key]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, unlock)
        self.assertEqual(result.direct_object, door)
        self.assertEqual(result.preposition, with_prep)
        self.assertEqual(result.indirect_adjective, rusty)
        self.assertEqual(result.indirect_object, key)

    def test_verb_adj_noun_prep_adj_noun(self):
        """
        Test PM-303: 6 words, both adjectives.

        Verify that "unlock rusty door with iron key" parses
        with adjectives on both objects.
        """
        # Look up words
        unlock = self.parser._lookup_word("unlock")
        rusty = self.parser._lookup_word("rusty")
        door = self.parser._lookup_word("door")
        with_prep = self.parser._lookup_word("with")
        iron = self.parser._lookup_word("iron")
        key = self.parser._lookup_word("key")

        # Create list of entries
        entries = [unlock, rusty, door, with_prep, iron, key]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, unlock)
        self.assertEqual(result.direct_adjective, rusty)
        self.assertEqual(result.direct_object, door)
        self.assertEqual(result.preposition, with_prep)
        self.assertEqual(result.indirect_adjective, iron)
        self.assertEqual(result.indirect_object, key)

    def test_complex_color_adjectives(self):
        """
        Test PM-304: Complex with color adjectives.

        Verify that "take red potion with blue flask" parses
        correctly with color adjectives on both objects.
        """
        # Look up words
        take = self.parser._lookup_word("take")
        red = self.parser._lookup_word("red")
        potion = self.parser._lookup_word("potion")
        with_prep = self.parser._lookup_word("with")
        blue = self.parser._lookup_word("blue")
        flask = self.parser._lookup_word("flask")

        # Create list of entries
        entries = [take, red, potion, with_prep, blue, flask]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, take)
        self.assertEqual(result.direct_adjective, red)
        self.assertEqual(result.direct_object, potion)
        self.assertEqual(result.preposition, with_prep)
        self.assertEqual(result.indirect_adjective, blue)
        self.assertEqual(result.indirect_object, flask)

    def test_complex_size_adjectives(self):
        """
        Test PM-305: Complex with size adjectives.

        Verify that "open large chest with small key" parses
        correctly with size adjectives on both objects.
        """
        # Look up words
        open_verb = self.parser._lookup_word("open")
        large = self.parser._lookup_word("large")
        chest = self.parser._lookup_word("chest")
        with_prep = self.parser._lookup_word("with")
        small = self.parser._lookup_word("small")
        key = self.parser._lookup_word("key")

        # Create list of entries
        entries = [open_verb, large, chest, with_prep, small, key]

        # Match pattern
        result = self.parser._match_pattern(entries)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.verb, open_verb)
        self.assertEqual(result.direct_adjective, large)
        self.assertEqual(result.direct_object, chest)
        self.assertEqual(result.preposition, with_prep)
        self.assertEqual(result.indirect_adjective, small)
        self.assertEqual(result.indirect_object, key)


if __name__ == '__main__':
    unittest.main()
