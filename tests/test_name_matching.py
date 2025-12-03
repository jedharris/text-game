"""Tests for the name_matches() helper function.

Verifies that name matching works correctly with vocabulary synonyms,
both for exact matches and phrase matching.
"""

import unittest
from src.word_entry import WordEntry, WordType
from utilities.utils import name_matches
from tests.conftest import make_word_entry


class TestNameMatchesBasic(unittest.TestCase):
    """Test name_matches() with basic WordEntry input."""

    def test_exact_match(self):
        """WordEntry exact match."""
        sword = make_word_entry("sword")
        self.assertTrue(name_matches(sword, "sword"))

    def test_exact_match_case_insensitive(self):
        """Matching is case insensitive."""
        sword = make_word_entry("sword")
        sword_upper = make_word_entry("Sword")
        sword_all_caps = make_word_entry("SWORD")
        self.assertTrue(name_matches(sword_upper, "sword"))
        self.assertTrue(name_matches(sword, "Sword"))
        self.assertTrue(name_matches(sword_all_caps, "sword"))

    def test_no_match(self):
        """Non-matching words return False."""
        sword = make_word_entry("sword")
        self.assertFalse(name_matches(sword, "key"))
        self.assertFalse(name_matches(sword, "swords"))  # Plural different

    def test_phrase_match_disabled_by_default(self):
        """Without match_in_phrase, partial match in phrase fails."""
        staircase = make_word_entry("staircase")
        self.assertFalse(name_matches(staircase, "spiral staircase"))

    def test_phrase_match_enabled(self):
        """With match_in_phrase, word in phrase matches."""
        staircase = make_word_entry("staircase")
        self.assertTrue(name_matches(staircase, "spiral staircase",
                                     match_in_phrase=True))

    def test_phrase_match_first_word(self):
        """match_in_phrase works for first word in phrase."""
        spiral = make_word_entry("spiral")
        self.assertTrue(name_matches(spiral, "spiral staircase",
                                     match_in_phrase=True))

    def test_phrase_match_requires_complete_word(self):
        """match_in_phrase only matches complete words, not substrings."""
        # "stair" is not a complete word in "spiral staircase"
        stair = make_word_entry("stair")
        self.assertFalse(name_matches(stair, "spiral staircase",
                                      match_in_phrase=True))


class TestNameMatchesWithWordEntry(unittest.TestCase):
    """Test name_matches() with WordEntry input."""

    def setUp(self):
        """Create test WordEntry objects."""
        self.stairs_entry = WordEntry(
            word="stairs",
            word_type=WordType.NOUN,
            synonyms=["staircase", "stairway", "steps"]
        )
        self.sword_entry = WordEntry(
            word="sword",
            word_type=WordType.NOUN,
            synonyms=["blade", "weapon"]
        )
        self.exit_entry = WordEntry(
            word="exit",
            word_type=WordType.NOUN,
            synonyms=["passage", "way", "path", "opening"]
        )

    def test_canonical_word_match(self):
        """WordEntry canonical word matches."""
        self.assertTrue(name_matches(self.stairs_entry, "stairs"))
        self.assertTrue(name_matches(self.sword_entry, "sword"))

    def test_synonym_match(self):
        """WordEntry synonyms match target."""
        self.assertTrue(name_matches(self.stairs_entry, "staircase"))
        self.assertTrue(name_matches(self.stairs_entry, "stairway"))
        self.assertTrue(name_matches(self.stairs_entry, "steps"))

    def test_synonym_match_case_insensitive(self):
        """Synonym matching is case insensitive."""
        self.assertTrue(name_matches(self.stairs_entry, "STAIRCASE"))
        self.assertTrue(name_matches(self.stairs_entry, "Stairway"))

    def test_no_match_with_synonyms(self):
        """Non-matching word not in synonyms returns False."""
        self.assertFalse(name_matches(self.stairs_entry, "ladder"))
        self.assertFalse(name_matches(self.sword_entry, "key"))

    def test_phrase_match_with_canonical(self):
        """match_in_phrase works with canonical word."""
        self.assertTrue(name_matches(self.stairs_entry, "grand stairs",
                                     match_in_phrase=True))

    def test_phrase_match_with_synonym(self):
        """match_in_phrase works with synonym - the key test case."""
        # This is the "examine stairs" -> "spiral staircase" case
        self.assertTrue(name_matches(self.stairs_entry, "spiral staircase",
                                     match_in_phrase=True))

    def test_phrase_match_multiple_synonyms(self):
        """All synonyms work for phrase matching."""
        self.assertTrue(name_matches(self.stairs_entry, "stone steps",
                                     match_in_phrase=True))
        self.assertTrue(name_matches(self.stairs_entry, "hidden stairway",
                                     match_in_phrase=True))

    def test_phrase_match_disabled_no_synonym_match(self):
        """Without match_in_phrase, synonyms don't match phrases."""
        self.assertFalse(name_matches(self.stairs_entry, "spiral staircase"))
        self.assertFalse(name_matches(self.stairs_entry, "stone steps"))


class TestNameMatchesEdgeCases(unittest.TestCase):
    """Test edge cases for name_matches()."""

    def test_empty_string_target(self):
        """Empty target name doesn't match."""
        entry = WordEntry(word="sword", word_type=WordType.NOUN, synonyms=[])
        self.assertFalse(name_matches(entry, ""))
        sword = make_word_entry("sword")
        self.assertFalse(name_matches(sword, ""))

    def test_empty_synonyms_list(self):
        """WordEntry with no synonyms still matches canonical word."""
        entry = WordEntry(word="sword", word_type=WordType.NOUN, synonyms=[])
        self.assertTrue(name_matches(entry, "sword"))
        self.assertFalse(name_matches(entry, "blade"))

    def test_whitespace_handling(self):
        """Whitespace in target is handled correctly."""
        entry = WordEntry(word="stairs", word_type=WordType.NOUN,
                         synonyms=["staircase"])
        # Extra spaces shouldn't break word splitting
        self.assertTrue(name_matches(entry, "spiral  staircase",
                                     match_in_phrase=True))

    def test_single_word_phrase_match(self):
        """Single word target works with match_in_phrase enabled."""
        entry = WordEntry(word="sword", word_type=WordType.NOUN, synonyms=[])
        self.assertTrue(name_matches(entry, "sword", match_in_phrase=True))

    def test_mixed_case_synonyms(self):
        """Synonyms with mixed case work correctly."""
        entry = WordEntry(
            word="NPC",
            word_type=WordType.NOUN,
            synonyms=["Character", "PERSON"]
        )
        self.assertTrue(name_matches(entry, "npc"))
        self.assertTrue(name_matches(entry, "character"))
        self.assertTrue(name_matches(entry, "person"))


class TestNameMatchesRealWorldCases(unittest.TestCase):
    """Test cases from actual game scenarios."""

    def test_examine_stairs_spiral_staircase(self):
        """The original bug: 'examine stairs' should find 'spiral staircase'."""
        # This matches vocabulary.json definition
        stairs_entry = WordEntry(
            word="stairs",
            word_type=WordType.NOUN,
            synonyms=["staircase", "stairway", "steps"]
        )
        self.assertTrue(name_matches(stairs_entry, "spiral staircase",
                                     match_in_phrase=True))

    def test_examine_archway_grand_archway(self):
        """'examine archway' should find 'grand archway'."""
        archway_entry = WordEntry(
            word="archway",
            word_type=WordType.NOUN,
            synonyms=["arch"]
        )
        self.assertTrue(name_matches(archway_entry, "grand archway",
                                     match_in_phrase=True))
        self.assertTrue(name_matches(archway_entry, "stone arch",
                                     match_in_phrase=True))

    def test_examine_exit_finds_passage(self):
        """'examine exit' with passage synonym."""
        exit_entry = WordEntry(
            word="exit",
            word_type=WordType.NOUN,
            synonyms=["passage", "way", "path", "opening"]
        )
        self.assertTrue(name_matches(exit_entry, "passage"))
        self.assertTrue(name_matches(exit_entry, "dark passage",
                                     match_in_phrase=True))

    def test_door_variations(self):
        """Door-related matching."""
        door_entry = WordEntry(
            word="door",
            word_type=WordType.NOUN,
            synonyms=["doorway", "entrance"]
        )
        self.assertTrue(name_matches(door_entry, "door"))
        self.assertTrue(name_matches(door_entry, "doorway"))
        self.assertTrue(name_matches(door_entry, "wooden doorway",
                                     match_in_phrase=True))


if __name__ == "__main__":
    unittest.main()
