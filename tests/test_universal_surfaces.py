"""
Tests for universal surface vocabulary and helper functions.

Following TDD approach - these tests are written first before implementation.
"""
import unittest
from behaviors.core.spatial import (
    get_universal_surface_nouns,
    is_universal_surface,
    get_default_description,
    vocabulary
)
from src.word_entry import WordEntry


class TestUniversalSurfaceVocabulary(unittest.TestCase):
    """Test universal surface vocabulary is correctly defined."""

    def test_universal_surface_vocabulary_loaded(self):
        """Test universal surface vocabulary is present in spatial module."""
        nouns = vocabulary.get("nouns", [])

        # Should have ceiling, floor, sky, walls
        words = [n["word"] for n in nouns]
        self.assertIn("ceiling", words)
        self.assertIn("floor", words)
        self.assertIn("sky", words)
        self.assertIn("walls", words)

    def test_universal_surfaces_have_properties(self):
        """Test universal surfaces have required properties."""
        for entry in vocabulary["nouns"]:
            if entry.get("properties", {}).get("universal_surface"):
                # Should have default_description
                self.assertIn("default_description", entry["properties"])
                # Description should not be empty
                self.assertTrue(len(entry["properties"]["default_description"]) > 0)

    def test_floor_has_ground_synonym(self):
        """Test floor has ground as synonym."""
        floor_entry = None
        for entry in vocabulary["nouns"]:
            if entry["word"] == "floor":
                floor_entry = entry
                break

        self.assertIsNotNone(floor_entry)
        self.assertIn("ground", floor_entry.get("synonyms", []))


class TestGetUniversalSurfaceNouns(unittest.TestCase):
    """Test getting list of universal surface nouns."""

    def test_get_universal_surface_nouns_returns_list(self):
        """Test function returns a list."""
        surfaces = get_universal_surface_nouns()
        self.assertIsInstance(surfaces, list)

    def test_get_universal_surface_nouns_includes_expected(self):
        """Test function includes all expected surfaces."""
        surfaces = get_universal_surface_nouns()

        self.assertIn("ceiling", surfaces)
        self.assertIn("floor", surfaces)
        self.assertIn("sky", surfaces)
        self.assertIn("walls", surfaces)

    def test_get_universal_surface_nouns_only_surfaces(self):
        """Test function only returns surfaces, not other nouns."""
        surfaces = get_universal_surface_nouns()

        # Should only have 4 surfaces
        self.assertEqual(len(surfaces), 4)


class TestIsUniversalSurface(unittest.TestCase):
    """Test recognizing universal surfaces."""

    def test_is_universal_surface_recognizes_ceiling(self):
        """Test ceiling is recognized as universal surface."""
        self.assertTrue(is_universal_surface(WordEntry(word="ceiling", word_type=None, synonyms=[])))
        self.assertTrue(is_universal_surface("ceiling"))

    def test_is_universal_surface_recognizes_floor(self):
        """Test floor is recognized as universal surface."""
        self.assertTrue(is_universal_surface(WordEntry(word="floor", word_type=None, synonyms=[])))
        self.assertTrue(is_universal_surface("floor"))

    def test_is_universal_surface_recognizes_sky(self):
        """Test sky is recognized as universal surface."""
        self.assertTrue(is_universal_surface(WordEntry(word="sky", word_type=None, synonyms=[])))
        self.assertTrue(is_universal_surface("sky"))

    def test_is_universal_surface_recognizes_walls(self):
        """Test walls is recognized as universal surface."""
        self.assertTrue(is_universal_surface(WordEntry(word="walls", word_type=None, synonyms=[])))
        self.assertTrue(is_universal_surface("walls"))

    def test_is_universal_surface_recognizes_ground_synonym(self):
        """Test ground (synonym for floor) is recognized."""
        self.assertTrue(is_universal_surface(WordEntry(word="ground", word_type=None, synonyms=[])))
        self.assertTrue(is_universal_surface("ground"))

    def test_is_universal_surface_case_insensitive(self):
        """Test recognition is case insensitive."""
        self.assertTrue(is_universal_surface("CEILING"))
        self.assertTrue(is_universal_surface("Floor"))
        self.assertTrue(is_universal_surface("GROUND"))

    def test_is_universal_surface_rejects_non_surfaces(self):
        """Test non-surfaces are rejected."""
        self.assertFalse(is_universal_surface(WordEntry(word="table", word_type=None, synonyms=[])))
        self.assertFalse(is_universal_surface(WordEntry(word="door", word_type=None, synonyms=[])))
        self.assertFalse(is_universal_surface(WordEntry(word="bench", word_type=None, synonyms=[])))
        self.assertFalse(is_universal_surface("unicorn"))


class TestGetDefaultDescription(unittest.TestCase):
    """Test getting default descriptions for universal surfaces."""

    def test_get_default_description_returns_string(self):
        """Test function returns a string."""
        desc = get_default_description("ceiling")
        self.assertIsInstance(desc, str)
        self.assertTrue(len(desc) > 0)

    def test_get_default_description_for_ceiling(self):
        """Test getting description for ceiling."""
        desc = get_default_description(WordEntry(word="ceiling", word_type=None, synonyms=[]))
        self.assertIn("ceiling", desc.lower())

    def test_get_default_description_for_floor(self):
        """Test getting description for floor."""
        desc = get_default_description(WordEntry(word="floor", word_type=None, synonyms=[]))
        self.assertIn("floor", desc.lower())

    def test_get_default_description_for_sky(self):
        """Test getting description for sky."""
        desc = get_default_description(WordEntry(word="sky", word_type=None, synonyms=[]))
        self.assertIn("sky", desc.lower())

    def test_get_default_description_for_walls(self):
        """Test getting description for walls."""
        desc = get_default_description(WordEntry(word="walls", word_type=None, synonyms=[]))
        self.assertIn("walls", desc.lower())

    def test_get_default_description_for_ground_synonym(self):
        """Test getting description for ground (synonym for floor)."""
        desc = get_default_description(WordEntry(word="ground", word_type=None, synonyms=[]))
        # Should return floor's default description
        self.assertIn("floor", desc.lower())

    def test_get_default_description_accepts_string(self):
        """Test function accepts string input."""
        desc = get_default_description("ceiling")
        self.assertIn("ceiling", desc.lower())

    def test_get_default_description_fallback(self):
        """Test fallback description for unknown surface."""
        desc = get_default_description("unknown")
        self.assertIn("unknown", desc.lower())


if __name__ == '__main__':
    unittest.main()
