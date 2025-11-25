"""
Tests for Phase 8: Handler Chaining Infrastructure

These tests validate invoke_handler() and invoke_previous_handler() with
position list management for handler delegation.
"""
import unittest
import sys
from pathlib import Path
from types import ModuleType

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_accessor import StateAccessor, HandlerResult
from src.behavior_manager import BehaviorManager
from tests.conftest import create_test_state


class TestPhase8HandlerChaining(unittest.TestCase):
    """Tests for handler chaining infrastructure."""

    def test_invoke_handler_initializes_position_list(self):
        """Test that invoke_handler initializes position list."""
        behavior_manager = BehaviorManager()
        state = create_test_state()
        accessor = StateAccessor(state, behavior_manager)

        module = ModuleType("test_module")
        def handle_test(accessor, action):
            # Check position list is initialized
            self.assertGreater(len(behavior_manager._handler_position_list), 0)
            return HandlerResult(success=True, message="test")
        module.handle_test = handle_test

        behavior_manager.load_module(module)

        result = behavior_manager.invoke_handler("test", accessor, {})
        self.assertTrue(result.success)

    def test_invoke_handler_cleans_up_position_list(self):
        """Test that position list is cleaned up after handler."""
        behavior_manager = BehaviorManager()
        state = create_test_state()
        accessor = StateAccessor(state, behavior_manager)

        module = ModuleType("test_module")
        def handle_test(accessor, action):
            return HandlerResult(success=True, message="test")
        module.handle_test = handle_test

        behavior_manager.load_module(module)
        behavior_manager.invoke_handler("test", accessor, {})

        # Position list should be empty after return
        self.assertEqual(behavior_manager._handler_position_list, [])

    def test_invoke_handler_cleans_up_on_exception(self):
        """Test that position list is cleaned up even on exception."""
        behavior_manager = BehaviorManager()
        state = create_test_state()
        accessor = StateAccessor(state, behavior_manager)

        module = ModuleType("test_module")
        def handle_test(accessor, action):
            raise ValueError("Test error")
        module.handle_test = handle_test

        behavior_manager.load_module(module)

        with self.assertRaises(ValueError):
            behavior_manager.invoke_handler("test", accessor, {})

        # Position list should be cleaned up despite exception
        self.assertEqual(behavior_manager._handler_position_list, [])

    def test_invoke_previous_handler_walks_forward(self):
        """Test that invoke_previous_handler walks forward through list."""
        behavior_manager = BehaviorManager()
        state = create_test_state()
        accessor = StateAccessor(state, behavior_manager)

        # First handler delegates
        game_module = ModuleType("game_module")
        def game_handle_test(accessor, action):
            return accessor.invoke_previous_handler("test", action)
        game_module.handle_test = game_handle_test

        # Second handler does work
        core_module = ModuleType("core_module")
        def core_handle_test(accessor, action):
            return HandlerResult(success=True, message="core")
        core_module.handle_test = core_handle_test

        # Load in order (need different source types to avoid conflict)
        behavior_manager.load_module(game_module, source_type="regular")
        behavior_manager.load_module(core_module, source_type="symlink")

        result = behavior_manager.invoke_handler("test", accessor, {})

        self.assertTrue(result.success)
        self.assertEqual(result.message, "core")

    def test_two_layer_handler_chain(self):
        """Test handler chaining through two layers (game -> core)."""
        behavior_manager = BehaviorManager()
        state = create_test_state()
        accessor = StateAccessor(state, behavior_manager)

        # Game layer adds prefix
        game_module = ModuleType("game_module")
        def game_handle_test(accessor, action):
            result = accessor.invoke_previous_handler("test", action)
            if result.success:
                return HandlerResult(success=True, message=f"game:{result.message}")
            return result
        game_module.handle_test = game_handle_test

        # Core layer does work
        core_module = ModuleType("core_module")
        def core_handle_test(accessor, action):
            return HandlerResult(success=True, message="core")
        core_module.handle_test = core_handle_test

        # Load in order (different source types)
        behavior_manager.load_module(game_module, source_type="regular")
        behavior_manager.load_module(core_module, source_type="symlink")

        result = behavior_manager.invoke_handler("test", accessor, {})

        self.assertTrue(result.success)
        self.assertEqual(result.message, "game:core")

    def test_invoke_previous_handler_runtime_error(self):
        """Test that calling invoke_previous_handler incorrectly raises RuntimeError."""
        behavior_manager = BehaviorManager()
        state = create_test_state()
        accessor = StateAccessor(state, behavior_manager)

        # Try to invoke without initialization
        with self.assertRaises(RuntimeError) as cm:
            behavior_manager.invoke_previous_handler("test", accessor, {})

        self.assertIn("position list not initialized", str(cm.exception).lower())

    def test_invoke_handler_returns_none_for_unknown_verb(self):
        """Test that invoke_handler returns None for unknown verb."""
        behavior_manager = BehaviorManager()
        state = create_test_state()
        accessor = StateAccessor(state, behavior_manager)

        result = behavior_manager.invoke_handler("nonexistent", accessor, {})

        self.assertIsNone(result)

    def test_invoke_previous_handler_at_end_of_chain(self):
        """Test that invoke_previous_handler at end of chain returns None."""
        behavior_manager = BehaviorManager()
        state = create_test_state()
        accessor = StateAccessor(state, behavior_manager)

        # Single handler tries to delegate (but there's no next handler)
        module = ModuleType("test_module")
        def handle_test(accessor, action):
            return accessor.invoke_previous_handler("test", action)
        module.handle_test = handle_test

        behavior_manager.load_module(module)

        result = behavior_manager.invoke_handler("test", accessor, {})

        # Should return None (no next handler)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
