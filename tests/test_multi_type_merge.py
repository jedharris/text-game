"""Tests for automatic multi-type vocabulary merging."""

import unittest
from src.behavior_manager import BehaviorManager


class TestMergeTypes(unittest.TestCase):
    """Test _merge_types helper function."""

    def test_merge_two_strings(self):
        """Merge two single type strings into list."""
        bm = BehaviorManager()
        result = bm._merge_types("verb", "noun")
        self.assertEqual(result, ["noun", "verb"])  # Sorted alphabetically

    def test_merge_string_and_list(self):
        """Merge string with existing list."""
        bm = BehaviorManager()
        result = bm._merge_types(["verb", "adjective"], "noun")
        self.assertEqual(result, ["adjective", "noun", "verb"])

    def test_merge_two_lists(self):
        """Merge two lists."""
        bm = BehaviorManager()
        result = bm._merge_types(["verb"], ["noun", "adjective"])
        self.assertEqual(result, ["adjective", "noun", "verb"])

    def test_merge_duplicate_types(self):
        """Merging same type twice returns single entry."""
        bm = BehaviorManager()
        result = bm._merge_types("noun", "noun")
        self.assertEqual(result, ["noun"])

    def test_merge_with_none(self):
        """None values are ignored."""
        bm = BehaviorManager()
        result = bm._merge_types("verb", None)
        self.assertEqual(result, ["verb"])

    def test_merge_empty_list(self):
        """Empty list is handled."""
        bm = BehaviorManager()
        result = bm._merge_types([], "noun")
        self.assertEqual(result, ["noun"])


class TestSectionToType(unittest.TestCase):
    """Test _section_to_type helper function."""

    def test_verbs_section(self):
        """Verbs section maps to 'verb'."""
        bm = BehaviorManager()
        self.assertEqual(bm._section_to_type("verbs"), "verb")

    def test_nouns_section(self):
        """Nouns section maps to 'noun'."""
        bm = BehaviorManager()
        self.assertEqual(bm._section_to_type("nouns"), "noun")

    def test_adjectives_section(self):
        """Adjectives section maps to 'adjective'."""
        bm = BehaviorManager()
        self.assertEqual(bm._section_to_type("adjectives"), "adjective")

    def test_directions_section(self):
        """Directions section maps to 'noun'."""
        bm = BehaviorManager()
        self.assertEqual(bm._section_to_type("directions"), "noun")

    def test_unknown_section(self):
        """Unknown section defaults to 'noun'."""
        bm = BehaviorManager()
        self.assertEqual(bm._section_to_type("unknown"), "noun")


class TestRebuildVocabFromMap(unittest.TestCase):
    """Test _rebuild_vocab_from_map helper function."""

    def test_single_type_words(self):
        """Single type words go to appropriate section."""
        bm = BehaviorManager()
        word_map = {
            "take": {"word": "take", "word_type": "verb", "synonyms": ["get"]},
            "sword": {"word": "sword", "word_type": "noun", "synonyms": []},
            "red": {"word": "red", "word_type": "adjective", "synonyms": []}
        }

        result = bm._rebuild_vocab_from_map(word_map)

        self.assertEqual(len(result["verbs"]), 1)
        self.assertEqual(result["verbs"][0]["word"], "take")
        self.assertEqual(len(result["nouns"]), 1)
        self.assertEqual(result["nouns"][0]["word"], "sword")
        self.assertEqual(len(result["adjectives"]), 1)
        self.assertEqual(result["adjectives"][0]["word"], "red")

    def test_multi_type_word(self):
        """Multi-type word goes to section of first type."""
        bm = BehaviorManager()
        word_map = {
            "stand": {
                "word": "stand",
                "word_type": ["noun", "verb"],  # First type is noun
                "synonyms": []
            }
        }

        result = bm._rebuild_vocab_from_map(word_map)

        # Should go to nouns section (first type)
        self.assertEqual(len(result["nouns"]), 1)
        self.assertEqual(result["nouns"][0]["word"], "stand")
        self.assertEqual(result["nouns"][0]["word_type"], ["noun", "verb"])
        self.assertEqual(len(result["verbs"]), 0)

    def test_preserves_other_fields(self):
        """Other fields like synonyms, event, etc. are preserved."""
        bm = BehaviorManager()
        word_map = {
            "take": {
                "word": "take",
                "word_type": "verb",
                "synonyms": ["get", "grab"],
                "event": "on_take",
                "object_required": True
            }
        }

        result = bm._rebuild_vocab_from_map(word_map)

        verb = result["verbs"][0]
        self.assertEqual(verb["synonyms"], ["get", "grab"])
        self.assertEqual(verb["event"], "on_take")
        self.assertEqual(verb["object_required"], True)


class TestGetMergedVocabulary(unittest.TestCase):
    """Test get_merged_vocabulary with multi-type detection."""

    def test_no_conflict_single_types(self):
        """Words with no conflicts remain single type."""
        bm = BehaviorManager()
        base_vocab = {
            "verbs": [{"word": "take", "synonyms": []}],
            "nouns": [{"word": "sword", "synonyms": []}],
            "adjectives": [],
            "directions": [],
            "prepositions": [],
            "articles": []
        }

        result = bm.get_merged_vocabulary(base_vocab)

        # Words should remain single type
        take_verb = next(v for v in result["verbs"] if v["word"] == "take")
        self.assertEqual(take_verb.get("word_type", "verb"), "verb")

        sword_noun = next(n for n in result["nouns"] if n["word"] == "sword")
        self.assertEqual(sword_noun.get("word_type", "noun"), "noun")

    def test_verb_noun_conflict(self):
        """Verb-noun conflict creates multi-type entry."""
        bm = BehaviorManager()

        # Base vocab has "stand" as noun (from game state extraction)
        base_vocab = {
            "verbs": [],
            "nouns": [{"word": "stand", "synonyms": []}],
            "adjectives": [],
            "directions": [],
            "prepositions": [],
            "articles": []
        }

        # Create mock module with "stand" as verb
        class MockModule:
            vocabulary = {
                "verbs": [{"word": "stand", "event": "on_stand", "synonyms": []}],
                "nouns": [],
                "adjectives": [],
                "directions": []
            }

        bm._modules = {"mock": MockModule()}

        result = bm.get_merged_vocabulary(base_vocab)

        # Should create multi-type entry
        stand_entry = next((n for n in result["nouns"] if n["word"] == "stand"), None)
        self.assertIsNotNone(stand_entry)
        self.assertEqual(stand_entry["word_type"], ["noun", "verb"])
        self.assertEqual(stand_entry["event"], "on_stand")  # Preserves verb properties

    def test_noun_adjective_conflict(self):
        """Noun-adjective conflict (directions) creates multi-type entry."""
        bm = BehaviorManager()

        base_vocab = {
            "verbs": [],
            "nouns": [],
            "adjectives": [],
            "directions": [],
            "prepositions": [],
            "articles": []
        }

        # Create mock module with "north" as both noun and adjective
        class MockModule:
            vocabulary = {
                "verbs": [],
                "nouns": [{"word": "north", "synonyms": ["n"]}],
                "adjectives": [{"word": "north", "synonyms": []}],
                "directions": []
            }

        bm._modules = {"mock": MockModule()}

        result = bm.get_merged_vocabulary(base_vocab)

        # Should create multi-type entry
        # Word appears first in nouns section, so stays in nouns
        # Types are merged and sorted alphabetically: ["adjective", "noun"]
        north_entry = next((n for n in result["nouns"] if n["word"] == "north"), None)
        self.assertIsNotNone(north_entry)
        self.assertEqual(north_entry["word_type"], ["adjective", "noun"])

        # Should not appear separately in adjectives
        north_adj = next((a for a in result["adjectives"] if a["word"] == "north"), None)
        self.assertIsNone(north_adj)

    def test_synonyms_merged(self):
        """Synonyms from both entries are merged."""
        bm = BehaviorManager()

        base_vocab = {
            "verbs": [],
            "nouns": [{"word": "stand", "synonyms": ["pedestal"]}],
            "adjectives": [],
            "directions": [],
            "prepositions": [],
            "articles": []
        }

        class MockModule:
            vocabulary = {
                "verbs": [{"word": "stand", "synonyms": ["get on"], "event": "on_stand"}],
                "nouns": [],
                "adjectives": [],
                "directions": []
            }

        bm._modules = {"mock": MockModule()}

        result = bm.get_merged_vocabulary(base_vocab)

        stand_entry = next(n for n in result["nouns"] if n["word"] == "stand")
        # Both synonyms should be present
        self.assertIn("pedestal", stand_entry["synonyms"])
        self.assertIn("get on", stand_entry["synonyms"])


if __name__ == '__main__':
    unittest.main()
