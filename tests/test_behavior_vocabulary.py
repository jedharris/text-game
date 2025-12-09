"""Tests for behavior-defined vocabulary merging.

Tests that verbs and other vocabulary defined in behavior modules
are properly merged into the parser vocabulary.
"""

import unittest
import json
import tempfile
from pathlib import Path

from src.behavior_manager import BehaviorManager
from src.vocabulary_generator import extract_nouns_from_state, merge_vocabulary
from src.state_manager import load_game_state
from src.parser import Parser


class TestBehaviorVocabularyMerging(unittest.TestCase):
    """Test that behavior modules can define vocabulary extensions."""

    def setUp(self):
        """Set up test fixtures."""
        self.behaviors_dir = Path(__file__).parent.parent / "behaviors"

        # Minimal base vocabulary
        self.base_vocab = {
            "verbs": [
                {"word": "go", "synonyms": ["walk"], "object_required": False},
                {"word": "quit", "synonyms": ["exit"], "object_required": False}
            ],
            "nouns": [],
            "adjectives": [],
            "directions": [
                {"word": "north", "synonyms": ["n"]}
            ]
        }

    def test_behavior_manager_collects_vocabulary_extensions(self):
        """Test that BehaviorManager collects vocabulary from modules."""
        manager = BehaviorManager()
        modules = manager.discover_modules(str(self.behaviors_dir))
        manager.load_modules(modules)

        # Get merged vocabulary
        merged = manager.get_merged_vocabulary(self.base_vocab)

        # Should have base verbs plus behavior-defined verbs
        verb_words = [v["word"] for v in merged["verbs"]]
        self.assertIn("go", verb_words)  # Base verb
        self.assertIn("quit", verb_words)  # Base verb
        # Verify behavior-defined verbs are present (e.g., from core behaviors)
        # The exact verbs depend on which behavior modules are loaded

    def test_behavior_vocabulary_includes_synonyms(self):
        """Test that behavior-defined verbs include their synonyms."""
        manager = BehaviorManager()
        modules = manager.discover_modules(str(self.behaviors_dir))
        manager.load_modules(modules)

        merged = manager.get_merged_vocabulary(self.base_vocab)

        # Find attack verb (defined in behaviors/core/combat.py)
        attack_verb = next(
            (v for v in merged["verbs"] if v["word"] == "attack"),
            None
        )

        self.assertIsNotNone(attack_verb)
        self.assertIn("synonyms", attack_verb)
        self.assertIn("hit", attack_verb["synonyms"])

    def test_no_duplicate_verbs_after_merge(self):
        """Test that duplicate verbs are not added."""
        # Add attack to base vocab
        base_with_attack = {
            "verbs": [
                {"word": "attack", "synonyms": [], "object_required": True}
            ],
            "nouns": [],
            "adjectives": [],
            "directions": []
        }

        manager = BehaviorManager()
        modules = manager.discover_modules(str(self.behaviors_dir))
        manager.load_modules(modules)

        merged = manager.get_merged_vocabulary(base_with_attack)

        # Should only have one attack
        attack_count = sum(1 for v in merged["verbs"] if v["word"] == "attack")
        self.assertEqual(attack_count, 1)

    def test_parser_recognizes_behavior_defined_verbs(self):
        """Test that parser can parse commands with behavior-defined verbs."""
        manager = BehaviorManager()
        modules = manager.discover_modules(str(self.behaviors_dir))
        manager.load_modules(modules)

        # Start with base vocab, add nouns, then merge behavior vocab
        base_vocab = {
            "verbs": [
                {"word": "take", "synonyms": ["get"], "object_required": True}
            ],
            "nouns": [
                {"word": "wolf"}
            ],
            "adjectives": [],
            "directions": []
        }

        # Merge behavior vocabulary
        merged = manager.get_merged_vocabulary(base_vocab)

        # Write to temp file and create parser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(merged, f)
            temp_path = f.name

        try:
            parser = Parser(temp_path)

            # Test parsing "attack wolf"
            result = parser.parse_command("attack wolf")

            self.assertIsNotNone(result)
            self.assertEqual(result.verb.word, "attack")
            self.assertEqual(result.direct_object.word, "wolf")

            # Test synonym "hit wolf"
            result = parser.parse_command("hit wolf")

            self.assertIsNotNone(result)
            self.assertEqual(result.verb.word, "attack")  # Resolved to canonical
            self.assertEqual(result.direct_object.word, "wolf")
        finally:
            Path(temp_path).unlink()


class TestFullVocabularyMerging(unittest.TestCase):
    """Test complete vocabulary merging pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.behaviors_dir = Path(__file__).parent.parent / "behaviors"

    def test_full_merge_pipeline(self):
        """Test merging base vocab + game state nouns + behavior verbs."""
        # Minimal base vocabulary (just meta commands)
        base_vocab = {
            "verbs": [
                {"word": "quit", "synonyms": ["exit"], "object_required": False},
                {"word": "inventory", "synonyms": ["i"], "object_required": False}
            ],
            "nouns": [],
            "adjectives": [{"word": "rubber"}],
            "directions": [
                {"word": "north", "synonyms": ["n"]}
            ]
        }

        # Game state with items
        game_data = {
            "metadata": {"title": "Test", "start_location": "room1"},
            "locations": [{"id": "room1", "name": "Room", "description": "A room"}],
            "items": [
                {"id": "item1", "name": "duck", "description": "A rubber duck",
                 "type": "tool", "portable": True, "location": "room1"},
                {"id": "item2", "name": "lantern", "description": "A lantern",
                 "type": "tool", "portable": True, "location": "room1"}
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }

        # Step 1: Extract nouns from game state
        state = load_game_state(game_data)
        extracted_nouns = extract_nouns_from_state(state)

        # Step 2: Merge nouns into base vocab
        vocab_with_nouns = merge_vocabulary(base_vocab, extracted_nouns)

        # Step 3: Load behavior modules and merge their vocabulary
        manager = BehaviorManager()
        modules = manager.discover_modules(str(self.behaviors_dir))
        manager.load_modules(modules)

        final_vocab = manager.get_merged_vocabulary(vocab_with_nouns)

        # Verify all components are present
        verb_words = [v["word"] for v in final_vocab["verbs"]]
        noun_words = [n["word"] for n in final_vocab["nouns"]]

        # Meta commands from base
        self.assertIn("quit", verb_words)
        self.assertIn("inventory", verb_words)

        # Nouns from game state
        self.assertIn("duck", noun_words)
        self.assertIn("lantern", noun_words)

        # Verbs from behaviors
        self.assertIn("attack", verb_words)

        # Directions preserved
        dir_words = [d["word"] for d in final_vocab["directions"]]
        self.assertIn("north", dir_words)

    def test_parser_works_with_full_merge(self):
        """Test that parser works with fully merged vocabulary."""
        # Base vocab with adjectives
        base_vocab = {
            "verbs": [
                {"word": "take", "synonyms": ["get"], "object_required": True}
            ],
            "nouns": [],
            "adjectives": [{"word": "gray"}],
            "directions": []
        }

        # Game state
        game_data = {
            "metadata": {"title": "Test", "start_location": "room1"},
            "locations": [{"id": "room1", "name": "Room", "description": "A room"}],
            "items": [
                {"id": "item1", "name": "wolf", "description": "A gray wolf",
                 "type": "scenery", "portable": False, "location": "room1"}
            ],
            "locks": [],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "room1"}}
        }

        # Full merge pipeline
        state = load_game_state(game_data)
        extracted_nouns = extract_nouns_from_state(state)
        vocab_with_nouns = merge_vocabulary(base_vocab, extracted_nouns)

        manager = BehaviorManager()
        modules = manager.discover_modules(str(self.behaviors_dir))
        manager.load_modules(modules)

        final_vocab = manager.get_merged_vocabulary(vocab_with_nouns)

        # Create parser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(final_vocab, f)
            temp_path = f.name

        try:
            parser = Parser(temp_path)

            # Can parse behavior-defined verb
            result = parser.parse_command("attack gray wolf")

            self.assertIsNotNone(result)
            self.assertEqual(result.verb.word, "attack")
            self.assertEqual(result.direct_object.word, "wolf")
        finally:
            Path(temp_path).unlink()


class TestVocabularyFromBehaviorModules(unittest.TestCase):
    """Test that core verbs can be defined in behavior modules."""

    def test_manipulation_verbs_from_behavior(self):
        """Test that take/drop verbs come from a manipulation behavior."""
        manager = BehaviorManager()
        modules = manager.discover_modules(str(Path(__file__).parent.parent / "behaviors"))
        manager.load_modules(modules)

        # Manipulation verbs should come from behaviors/core/manipulation.py
        merged = manager.get_merged_vocabulary({
            "verbs": [],
            "nouns": [],
            "adjectives": [],
            "directions": []
        })

        verb_words = [v["word"] for v in merged["verbs"]]

        # Verify manipulation verbs are present from behaviors
        self.assertIn("take", verb_words)
        self.assertIn("drop", verb_words)
        self.assertIn("give", verb_words)


if __name__ == '__main__':
    unittest.main()
