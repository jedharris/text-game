"""Tests for the BehaviorManager class and EventResult dataclass."""

import unittest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.behavior_manager import (
    BehaviorManager,
    EventResult,
    get_behavior_manager
)


class TestEventResult(unittest.TestCase):
    """Tests for EventResult dataclass."""

    def test_default_values(self):
        """Test EventResult with allow=True has expected defaults."""
        # allow is now required, feedback defaults to None
        result = EventResult(allow=True)
        self.assertIs(result.allow, True)
        self.assertIsNone(result.feedback)

    def test_custom_values(self):
        """Test EventResult with custom values."""
        result = EventResult(allow=False, feedback="Action prevented")
        self.assertIs(result.allow, False)
        self.assertEqual(result.feedback, "Action prevented")

    def test_allow_only(self):
        """Test EventResult with only allow specified."""
        result = EventResult(allow=False)
        self.assertIs(result.allow, False)
        self.assertIsNone(result.feedback)

    def test_feedback_only(self):
        """Test EventResult with feedback and allow=True."""
        # allow is required, specify explicitly
        result = EventResult(allow=True, feedback="Custom message")
        self.assertIs(result.allow, True)
        self.assertEqual(result.feedback, "Custom message")


class TestBehaviorManagerLoadModule(unittest.TestCase):
    """Tests for BehaviorManager.load_module()."""

    def test_load_module_registers_handler(self):
        """Test that load_module registers handle_* functions."""
        manager = BehaviorManager()

        # Create a mock module with a handler
        mock_module = MagicMock()
        mock_handler = Mock()
        mock_module.handle_squeeze = mock_handler
        mock_module.vocabulary = None

        # Make dir() return the handler name
        mock_module.__dir__ = lambda self=None: ['handle_squeeze']

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        self.assertTrue(manager.has_handler("squeeze"))
        self.assertIs(manager.get_handler("squeeze"), mock_handler)

    def test_load_module_registers_vocabulary(self):
        """Test that load_module registers vocabulary extensions."""
        manager = BehaviorManager()

        mock_module = MagicMock()
        mock_module.vocabulary = {
            "verbs": [{"word": "squeeze", "synonyms": ["squish"]}]
        }
        mock_module.__dir__ = lambda self=None: []

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        base_vocab = {"verbs": []}
        merged = manager.get_merged_vocabulary(base_vocab)

        self.assertTrue(any(v["word"] == "squeeze" for v in merged["verbs"]))

    def test_load_module_handles_import_error(self):
        """Test that load_module handles missing modules gracefully."""
        manager = BehaviorManager()

        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            # Should not raise
            manager.load_module("nonexistent.module")

    def test_load_modules_multiple(self):
        """Test loading multiple modules at once."""
        manager = BehaviorManager()

        def create_mock_module(handler_name):
            mock = MagicMock()
            mock.vocabulary = None  # Avoid vocabulary validation
            handler = Mock()
            setattr(mock, f"handle_{handler_name}", handler)
            # Capture handler_name in closure
            mock.__dir__ = lambda self=None, h=handler_name: [f"handle_{h}"]
            return mock

        modules = {
            "module1": create_mock_module("action1"),
            "module2": create_mock_module("action2"),
        }

        with patch('importlib.import_module', side_effect=lambda name: modules[name]):
            # load_modules expects list of (module_path, source_type) tuples
            manager.load_modules([("module1", "regular"), ("module2", "regular")])

        self.assertTrue(manager.has_handler("action1"))
        self.assertTrue(manager.has_handler("action2"))


class TestBehaviorManagerLoadBehavior(unittest.TestCase):
    """Tests for BehaviorManager.load_behavior()."""

    def test_load_behavior_success(self):
        """Test loading a behavior function by path."""
        manager = BehaviorManager()

        mock_module = MagicMock()
        mock_func = Mock(return_value=EventResult(allow=True))
        mock_module.on_squeeze = mock_func

        with patch('importlib.import_module', return_value=mock_module):
            behavior = manager.load_behavior("test.module:on_squeeze")

        self.assertIs(behavior, mock_func)

    def test_load_behavior_caches_result(self):
        """Test that loaded behaviors are cached."""
        manager = BehaviorManager()

        mock_module = MagicMock()
        mock_func = Mock()
        mock_module.on_squeeze = mock_func

        with patch('importlib.import_module', return_value=mock_module) as mock_import:
            behavior1 = manager.load_behavior("test.module:on_squeeze")
            behavior2 = manager.load_behavior("test.module:on_squeeze")

        self.assertIs(behavior1, behavior2)
        # import_module should only be called once due to caching
        self.assertEqual(mock_import.call_count, 1)

    def test_load_behavior_invalid_path(self):
        """Test loading behavior with invalid path format."""
        manager = BehaviorManager()

        result = manager.load_behavior("invalid_path_no_colon")

        self.assertIsNone(result)

    def test_load_behavior_missing_module(self):
        """Test loading behavior from nonexistent module."""
        manager = BehaviorManager()

        with patch('importlib.import_module', side_effect=ImportError("Not found")):
            result = manager.load_behavior("missing.module:on_squeeze")

        self.assertIsNone(result)

    def test_load_behavior_missing_function(self):
        """Test loading nonexistent function from module."""
        manager = BehaviorManager()

        mock_module = MagicMock(spec=[])  # Empty spec means no attributes

        with patch('importlib.import_module', return_value=mock_module):
            result = manager.load_behavior("test.module:nonexistent")

        self.assertIsNone(result)

    def test_clear_cache(self):
        """Test that clear_cache empties the behavior cache."""
        manager = BehaviorManager()

        mock_module = MagicMock()
        mock_func = Mock()
        mock_module.on_squeeze = mock_func

        with patch('importlib.import_module', return_value=mock_module) as mock_import:
            manager.load_behavior("test.module:on_squeeze")
            manager.clear_cache()
            manager.load_behavior("test.module:on_squeeze")

        # After clearing cache, import_module should be called twice
        self.assertEqual(mock_import.call_count, 2)


class TestBehaviorManagerInvokeBehavior(unittest.TestCase):
    """Tests for BehaviorManager.invoke_behavior()."""

    def test_invoke_behavior_success(self):
        """Test invoking a behavior successfully."""
        manager = BehaviorManager()

        # Create entity with behavior
        entity = Mock()
        entity.behaviors = ["test.module"]

        # Mock accessor - dict format behaviors receive accessor.game_state
        accessor = Mock()
        game_state = Mock()
        accessor.game_state = game_state
        context = {"location": Mock()}

        expected_result = EventResult(allow=True, feedback="Squeaked!")
        mock_func = Mock(return_value=expected_result)
        mock_module = MagicMock()
        mock_module.on_squeeze = mock_func
        mock_module.vocabulary = {}

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        result = manager.invoke_behavior(entity, "on_squeeze", accessor, context)

        self.assertIsNotNone(result)
        self.assertEqual(result.allow, expected_result.allow)
        self.assertEqual(result.feedback, expected_result.feedback)
        # Behaviors receive (entity, accessor, context)
        mock_func.assert_called_once_with(entity, accessor, context)

    def test_invoke_behavior_no_behaviors_dict(self):
        """Test invoking behavior on entity without behaviors."""
        manager = BehaviorManager()

        entity = Mock(spec=[])  # No behaviors attribute
        state = Mock()
        context: dict[str, Any] = {}

        result = manager.invoke_behavior(entity, "on_squeeze", state, context)

        self.assertIsNone(result)

    def test_invoke_behavior_empty_behaviors(self):
        """Test invoking behavior on entity with empty behaviors dict."""
        manager = BehaviorManager()

        entity = Mock()
        entity.behaviors = []
        state = Mock()
        context: dict[str, Any] = {}

        result = manager.invoke_behavior(entity, "on_squeeze", state, context)

        self.assertIsNone(result)

    def test_invoke_behavior_event_not_registered(self):
        """Test invoking unregistered event on entity."""
        manager = BehaviorManager()

        entity = Mock()
        entity.behaviors = ["test.module"]
        state = Mock()
        context: dict[str, Any] = {}

        mock_module = MagicMock()
        mock_module.vocabulary = {}
        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        result = manager.invoke_behavior(entity, "on_squeeze", state, context)

        self.assertIsNone(result)

    def test_invoke_behavior_handles_exception(self):
        """Test that behavior exceptions are handled gracefully."""
        manager = BehaviorManager()

        entity = Mock()
        entity.behaviors = ["test.module"]
        state = Mock()
        context: dict[str, Any] = {}

        mock_func = Mock(side_effect=Exception("Behavior error"))
        mock_module = MagicMock()
        mock_module.on_squeeze = mock_func
        mock_module.vocabulary = {}

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        result = manager.invoke_behavior(entity, "on_squeeze", state, context)

        self.assertIsNone(result)

    def test_invoke_behavior_non_event_result(self):
        """Test invoking behavior that doesn't return EventResult."""
        manager = BehaviorManager()

        entity = Mock()
        entity.behaviors = ["test.module"]
        state = Mock()
        context: dict[str, Any] = {}

        # Return something other than EventResult
        mock_func = Mock(return_value="not an EventResult")
        mock_module = MagicMock()
        mock_module.on_squeeze = mock_func
        mock_module.vocabulary = {}

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        result = manager.invoke_behavior(entity, "on_squeeze", state, context)

        self.assertIsNone(result)


class TestBehaviorManagerVocabulary(unittest.TestCase):
    """Tests for vocabulary merging."""

    def test_merge_vocabulary_empty_base(self):
        """Test merging with empty base vocabulary."""
        manager = BehaviorManager()

        mock_module = MagicMock()
        mock_module.vocabulary = {
            "verbs": [{"word": "squeeze", "object_required": True}]
        }
        mock_module.__dir__ = lambda self=None: []

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        base = {"verbs": []}
        merged = manager.get_merged_vocabulary(base)

        self.assertEqual(len(merged["verbs"]), 1)
        self.assertEqual(merged["verbs"][0]["word"], "squeeze")

    def test_merge_vocabulary_preserves_base(self):
        """Test that base vocabulary is preserved."""
        manager = BehaviorManager()

        mock_module = MagicMock()
        mock_module.vocabulary = {
            "verbs": [{"word": "squeeze"}]
        }
        mock_module.__dir__ = lambda self=None: []

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        base = {
            "verbs": [{"word": "take"}, {"word": "drop"}]
        }
        merged = manager.get_merged_vocabulary(base)

        words = [v["word"] for v in merged["verbs"]]
        self.assertIn("take", words)
        self.assertIn("drop", words)
        self.assertIn("squeeze", words)

    def test_merge_vocabulary_no_duplicates(self):
        """Test that duplicate verbs are not added."""
        manager = BehaviorManager()

        mock_module = MagicMock()
        mock_module.vocabulary = {
            "verbs": [{"word": "take", "synonyms": ["grab"]}]  # Duplicate of base
        }
        mock_module.__dir__ = lambda self=None: []

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        base = {"verbs": [{"word": "take"}]}
        merged = manager.get_merged_vocabulary(base)

        # Should still only have one "take"
        take_count = sum(1 for v in merged["verbs"] if v["word"] == "take")
        self.assertEqual(take_count, 1)

    def test_merge_vocabulary_multiple_modules(self):
        """Test merging vocabulary from multiple modules."""
        manager = BehaviorManager()

        def create_mock_module(verb):
            mock = MagicMock()
            mock.vocabulary = {"verbs": [{"word": verb}]}
            mock.__dir__ = lambda self=None: []
            return mock

        modules = {
            "module1": create_mock_module("squeeze"),
            "module2": create_mock_module("shake"),
        }

        with patch('importlib.import_module', side_effect=lambda name: modules[name]):
            # load_modules expects list of (module_path, source_type) tuples
            manager.load_modules([("module1", "regular"), ("module2", "regular")])

        base = {"verbs": []}
        merged = manager.get_merged_vocabulary(base)

        words = [v["word"] for v in merged["verbs"]]
        self.assertIn("squeeze", words)
        self.assertIn("shake", words)


class TestBehaviorManagerHandlers(unittest.TestCase):
    """Tests for handler registration and retrieval."""

    def test_has_handler_false(self):
        """Test has_handler returns False for unregistered verb."""
        manager = BehaviorManager()
        self.assertFalse(manager.has_handler("nonexistent"))

    def test_has_handler_true(self):
        """Test has_handler returns True for registered verb."""
        manager = BehaviorManager()

        mock_module = MagicMock()
        mock_module.vocabulary = None  # Avoid vocabulary validation
        mock_module.handle_test = Mock()
        mock_module.__dir__ = lambda self=None: ['handle_test']

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        self.assertTrue(manager.has_handler("test"))

    def test_get_handler_none(self):
        """Test get_handler returns None for unregistered verb."""
        manager = BehaviorManager()
        self.assertIsNone(manager.get_handler("nonexistent"))

    def test_get_handler_returns_callable(self):
        """Test get_handler returns the registered callable."""
        manager = BehaviorManager()

        mock_module = MagicMock()
        mock_module.vocabulary = None  # Avoid vocabulary validation
        mock_handler = Mock()
        mock_module.handle_test = mock_handler
        mock_module.__dir__ = lambda self=None: ['handle_test']

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test.module")

        handler = manager.get_handler("test")
        self.assertIs(handler, mock_handler)
        self.assertTrue(callable(handler))


class TestBehaviorManagerDiscovery(unittest.TestCase):
    """Tests for module auto-discovery."""

    def test_discover_modules_finds_python_files(self):
        """Test that discover_modules finds .py files in directory."""
        manager = BehaviorManager()

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create test directory structure
            behaviors_dir = tmp_path / "behaviors"
            behaviors_dir.mkdir()
            core_dir = behaviors_dir / "core"
            core_dir.mkdir()

            # Create test module files
            (core_dir / "__init__.py").write_text("")
            (core_dir / "test_behavior.py").write_text(
                "vocabulary = {'verbs': []}\n"
                "def handle_test(handler, action): pass\n"
            )

            # Test discovery - returns list of (module_path, source_type) tuples
            modules = manager.discover_modules(str(behaviors_dir))

            # Should find the test_behavior module
            module_paths = [m[0] for m in modules]
            self.assertTrue(any("test_behavior" in m for m in module_paths))

    def test_discover_modules_follows_symlinks(self):
        """Test that discover_modules follows symlinks and marks them as symlink type."""
        manager = BehaviorManager()

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create source directory
            source_dir = tmp_path / "source"
            source_dir.mkdir()
            (source_dir / "__init__.py").write_text("")
            (source_dir / "shared.py").write_text(
                "def handle_shared(handler, action): pass\n"
            )

            # Create behaviors directory with symlink
            behaviors_dir = tmp_path / "behaviors"
            behaviors_dir.mkdir()
            (behaviors_dir / "__init__.py").write_text("")

            # Create symlink
            symlink = behaviors_dir / "core"
            symlink.symlink_to(source_dir)

            # Test discovery - returns list of (module_path, tier) tuples
            modules = manager.discover_modules(str(behaviors_dir))

            # Should find the shared module through symlink
            # The module path will include "core" since that's the symlink name
            module_paths = [m[0] for m in modules]
            self.assertTrue(any("shared" in m for m in module_paths), f"Modules found: {modules}")

            # Modules found through symlink at depth 1 should be Tier 2
            for module_path, tier in modules:
                if "shared" in module_path:
                    self.assertEqual(tier, 2, "Symlinked modules at depth 1 should be Tier 2")

    def test_discover_modules_skips_init(self):
        """Test that discover_modules skips __init__.py files."""
        manager = BehaviorManager()

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            behaviors_dir = tmp_path / "behaviors"
            behaviors_dir.mkdir()
            (behaviors_dir / "__init__.py").write_text("")

            # Returns list of (module_path, source_type) tuples
            modules = manager.discover_modules(str(behaviors_dir))

            # Should not include __init__
            module_paths = [m[0] for m in modules]
            self.assertFalse(any("__init__" in m for m in module_paths))

    def test_discover_modules_empty_directory(self):
        """Test discover_modules with empty directory."""
        manager = BehaviorManager()

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            empty_dir = tmp_path / "empty"
            empty_dir.mkdir()

            modules = manager.discover_modules(str(empty_dir))

            self.assertEqual(modules, [])

    def test_discover_modules_nonexistent_directory(self):
        """Test discover_modules with nonexistent directory."""
        manager = BehaviorManager()

        modules = manager.discover_modules("/nonexistent/path")

        self.assertEqual(modules, [])


class TestGetBehaviorManager(unittest.TestCase):
    """Tests for global behavior manager instance."""

    def test_get_behavior_manager_returns_instance(self):
        """Test that get_behavior_manager returns a BehaviorManager."""
        manager = get_behavior_manager()
        self.assertIsInstance(manager, BehaviorManager)

    def test_get_behavior_manager_singleton(self):
        """Test that get_behavior_manager returns same instance."""
        manager1 = get_behavior_manager()
        manager2 = get_behavior_manager()
        self.assertIs(manager1, manager2)


class TestBehaviorManagerIntegration(unittest.TestCase):
    """Integration tests for BehaviorManager."""

    def test_full_workflow(self):
        """Test complete workflow: load module, merge vocab, invoke behavior."""
        manager = BehaviorManager()

        # Create mock module with handler and behavior
        mock_module = MagicMock()
        mock_module.vocabulary = {
            "verbs": [{"word": "squeeze", "object_required": True}]
        }
        mock_handler = Mock(return_value={
            "type": "result",
            "success": True,
            "action": "squeeze",
            "entity_obj": Mock(behaviors=["test"])
        })
        mock_module.handle_squeeze = mock_handler

        mock_behavior = Mock(return_value=EventResult(
            allow=True,
            feedback="Squeak!"
        ))
        mock_module.on_squeeze = mock_behavior
        mock_module.__dir__ = lambda self=None: ['handle_squeeze', 'on_squeeze']

        with patch('importlib.import_module', return_value=mock_module):
            # Load module
            manager.load_module("test")

            # Verify handler registered
            self.assertTrue(manager.has_handler("squeeze"))

            # Verify vocabulary merged
            merged = manager.get_merged_vocabulary({"verbs": []})
            self.assertTrue(any(v["word"] == "squeeze" for v in merged["verbs"]))

            # Invoke behavior
            entity = Mock()
            entity.behaviors = ["test"]
            state = Mock()
            context = {"location": Mock()}

            result = manager.invoke_behavior(entity, "on_squeeze", state, context)

            self.assertTrue(result.allow)
            self.assertEqual(result.feedback, "Squeak!")

    def test_behavior_modifies_state(self):
        """Test that behaviors can modify state directly."""
        manager = BehaviorManager()

        # Behavior that modifies entity state
        def on_squeeze(entity, state, context):
            entity.states["squeeze_count"] = entity.states.get("squeeze_count", 0) + 1
            return EventResult(allow=True, feedback="Squeaked!")

        mock_module = MagicMock()
        mock_module.on_squeeze = on_squeeze
        mock_module.vocabulary = {}

        with patch('importlib.import_module', return_value=mock_module):
            manager.load_module("test")
            entity = Mock()
            entity.behaviors = ["test"]
            entity.states = {}
            state = Mock()
            context: dict[str, Any] = {}

            # First squeeze
            result = manager.invoke_behavior(entity, "on_squeeze", state, context)
            self.assertEqual(entity.states["squeeze_count"], 1)

            # Second squeeze
            result = manager.invoke_behavior(entity, "on_squeeze", state, context)
            self.assertEqual(entity.states["squeeze_count"], 2)


if __name__ == '__main__':
    unittest.main()
