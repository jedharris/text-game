"""
Tests for Phase 4: BehaviorManager - Module Loading & Vocabulary

These tests validate:
- Module loading with vocabulary
- Handler registration
- Conflict detection (handler and vocabulary)
- Vocabulary validation
- Verb-to-event mappings
"""
import unittest
import sys
from pathlib import Path
from types import ModuleType

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.behavior_manager import BehaviorManager
from src.state_accessor import HandlerResult, EventResult


class TestPhase4ModuleLoading(unittest.TestCase):
    """Tests for Phase 4: Module loading with vocabulary and handlers."""

    def test_load_module_with_vocabulary(self):
        """Test loading a module with vocabulary."""
        behavior_manager = BehaviorManager()

        module = ModuleType("test_module")
        module.vocabulary = {
            "verbs": [
                {"word": "test", "synonyms": ["try"], "event": "on_test"}
            ]
        }

        behavior_manager.load_module(module)

        # Verify verb-to-event mapping
        self.assertEqual(behavior_manager.get_event_for_verb("test"), "on_test")
        self.assertEqual(behavior_manager.get_event_for_verb("try"), "on_test")

    def test_load_module_with_handler(self):
        """Test loading a module with handler."""
        behavior_manager = BehaviorManager()

        module = ModuleType("test_module")
        def handle_test(accessor, action):
            return HandlerResult(success=True, message="test")
        module.handle_test = handle_test

        behavior_manager.load_module(module)

        # Verify handler registered
        handler = behavior_manager.get_handler("test")
        self.assertIsNotNone(handler)
        self.assertTrue(callable(handler))

    def test_vocabulary_validation_not_dict(self):
        """Test that vocabulary must be a dict."""
        behavior_manager = BehaviorManager()

        module = ModuleType("test_module")
        module.vocabulary = "not a dict"

        with self.assertRaises(ValueError) as cm:
            behavior_manager.load_module(module)

        self.assertIn("must be a dict", str(cm.exception))

    def test_vocabulary_validation_verbs_not_list(self):
        """Test that verbs must be a list."""
        behavior_manager = BehaviorManager()

        module = ModuleType("test_module")
        module.vocabulary = {"verbs": "not a list"}

        with self.assertRaises(ValueError) as cm:
            behavior_manager.load_module(module)

        self.assertIn("must be a list", str(cm.exception))

    def test_vocabulary_validation_missing_word(self):
        """Test that verb spec must have 'word' field."""
        behavior_manager = BehaviorManager()

        module = ModuleType("test_module")
        module.vocabulary = {
            "verbs": [
                {"synonyms": ["test"]}  # Missing 'word'
            ]
        }

        with self.assertRaises(ValueError) as cm:
            behavior_manager.load_module(module)

        self.assertIn("missing required field 'word'", str(cm.exception))

    def test_handler_conflict_same_source_type(self):
        """Test that duplicate handlers from same source type raise error."""
        behavior_manager = BehaviorManager()

        # First module
        first_module = ModuleType("first_module")
        def first_handle_test(accessor, action):
            return HandlerResult(success=True, message="first")
        first_module.handle_test = first_handle_test

        # Second module with same verb
        second_module = ModuleType("second_module")
        def second_handle_test(accessor, action):
            return HandlerResult(success=True, message="second")
        second_module.handle_test = second_handle_test

        # Load first module
        behavior_manager.load_module(first_module, source_type="regular")

        # Load second module - should raise ValueError
        with self.assertRaises(ValueError) as cm:
            behavior_manager.load_module(second_module, source_type="regular")

        self.assertIn("Handler conflict", str(cm.exception))
        self.assertIn("first_module", str(cm.exception))
        self.assertIn("second_module", str(cm.exception))

    def test_handler_no_conflict_different_source_types(self):
        """Test that same verb from different source types is allowed."""
        behavior_manager = BehaviorManager()

        # Regular module
        game_module = ModuleType("game_module")
        def game_handle_test(accessor, action):
            return HandlerResult(success=True, message="game")
        game_module.handle_test = game_handle_test

        # Symlink module
        core_module = ModuleType("core_module")
        def core_handle_test(accessor, action):
            return HandlerResult(success=True, message="core")
        core_module.handle_test = core_handle_test

        # Load both - should succeed
        behavior_manager.load_module(game_module, source_type="regular")
        behavior_manager.load_module(core_module, source_type="symlink")

        # Both should be registered
        self.assertEqual(len(behavior_manager._handlers["test"]), 2)

    def test_vocabulary_conflict_different_events(self):
        """Test that same verb mapping to different events raises error."""
        behavior_manager = BehaviorManager()

        # First module maps "test" -> "on_test"
        first_module = ModuleType("first_module")
        first_module.vocabulary = {
            "verbs": [{"word": "test", "event": "on_test"}]
        }

        # Second module maps "test" -> "on_different"
        second_module = ModuleType("second_module")
        second_module.vocabulary = {
            "verbs": [{"word": "test", "event": "on_different"}]
        }

        behavior_manager.load_module(first_module)

        # Should raise ValueError
        with self.assertRaises(ValueError) as cm:
            behavior_manager.load_module(second_module)

        self.assertIn("Vocabulary conflict", str(cm.exception))
        self.assertIn("test", str(cm.exception))

    def test_vocabulary_same_event_allowed(self):
        """Test that same verb mapping to same event is allowed."""
        behavior_manager = BehaviorManager()

        # First module maps "test" -> "on_test"
        first_module = ModuleType("first_module")
        first_module.vocabulary = {
            "verbs": [{"word": "test", "event": "on_test"}]
        }

        # Second module also maps "test" -> "on_test"
        second_module = ModuleType("second_module")
        second_module.vocabulary = {
            "verbs": [{"word": "test", "event": "on_test"}]
        }

        behavior_manager.load_module(first_module)
        behavior_manager.load_module(second_module)  # Should not raise

        # Mapping should work
        self.assertEqual(behavior_manager.get_event_for_verb("test"), "on_test")

    def test_handler_load_order(self):
        """Test that handlers are called in load order (first loaded = first called)."""
        behavior_manager = BehaviorManager()

        # Create mock module objects with handler functions
        first_module = ModuleType("first_module")
        def first_handle_test(accessor, action):
            return HandlerResult(success=True, message="first")
        first_module.handle_test = first_handle_test

        second_module = ModuleType("second_module")
        def second_handle_test(accessor, action):
            return HandlerResult(success=True, message="second")
        second_module.handle_test = second_handle_test

        # Load in order with different source types (for chaining)
        behavior_manager.load_module(first_module, source_type="regular")
        behavior_manager.load_module(second_module, source_type="symlink")

        # Verify first loaded is returned by get_handler()
        handler = behavior_manager.get_handler("test")
        result = handler(None, {})
        self.assertTrue(result.success and result.message == "first",
                       "First loaded handler should be called")

        # Verify handlers list is in load order
        self.assertEqual(len(behavior_manager._handlers["test"]), 2)
        # Now handlers are tuples (handler, module_name)
        handler0, _ = behavior_manager._handlers["test"][0]
        handler1, _ = behavior_manager._handlers["test"][1]
        result0 = handler0(None, {})
        result1 = handler1(None, {})
        self.assertTrue(result0.success and result0.message == "first")
        self.assertTrue(result1.success and result1.message == "second")

    def test_get_event_for_verb_unknown(self):
        """Test that get_event_for_verb returns None for unknown verb."""
        behavior_manager = BehaviorManager()

        # No modules loaded
        self.assertIsNone(behavior_manager.get_event_for_verb("nonexistent"))

    def test_vocabulary_with_synonyms(self):
        """Test that synonyms are registered correctly."""
        behavior_manager = BehaviorManager()

        module = ModuleType("test_module")
        module.vocabulary = {
            "verbs": [
                {"word": "take", "synonyms": ["get", "grab"], "event": "on_take"}
            ]
        }

        behavior_manager.load_module(module)

        # All synonyms should map to same event
        self.assertEqual(behavior_manager.get_event_for_verb("take"), "on_take")
        self.assertEqual(behavior_manager.get_event_for_verb("get"), "on_take")
        self.assertEqual(behavior_manager.get_event_for_verb("grab"), "on_take")

    def test_module_without_vocabulary(self):
        """Test that modules without vocabulary work fine."""
        behavior_manager = BehaviorManager()

        module = ModuleType("test_module")
        # No vocabulary attribute

        # Should not raise
        behavior_manager.load_module(module)

    def test_module_with_empty_vocabulary(self):
        """Test that modules with empty vocabulary work fine."""
        behavior_manager = BehaviorManager()

        module = ModuleType("test_module")
        module.vocabulary = {}

        # Should not raise
        behavior_manager.load_module(module)

    def test_get_handler_unknown_verb(self):
        """Test that get_handler returns None for unknown verb."""
        behavior_manager = BehaviorManager()

        # No modules loaded
        self.assertIsNone(behavior_manager.get_handler("nonexistent"))


if __name__ == '__main__':
    unittest.main()
