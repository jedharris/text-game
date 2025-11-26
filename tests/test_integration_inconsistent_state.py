"""
Tests for inconsistent state handling (Phase I-2).

Reference: behavior_refactoring_testing.md - test pattern for inconsistent state
Reference: behavior_refactoring_implementation.md lines 297-332
"""

import unittest
import sys
from io import StringIO
from src.llm_protocol import JSONProtocolHandler
from src.behavior_manager import BehaviorManager
from src.state_accessor import HandlerResult
from tests.conftest import create_test_state


class TestInconsistentStateHandling(unittest.TestCase):
    """Test inconsistent state detection and handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.handler = JSONProtocolHandler(self.state, self.behavior_manager)

    def test_state_corrupted_flag_starts_false(self):
        """Test that state_corrupted flag initializes to False."""
        self.assertFalse(self.handler.state_corrupted)

    def test_inconsistent_state_sets_flag(self):
        """Test that INCONSISTENT STATE message sets corruption flag."""
        from types import ModuleType
        module = ModuleType("test_module")

        def handle_test(accessor, action):
            return HandlerResult(
                success=False,
                message="INCONSISTENT STATE: Test corruption"
            )
        module.handle_test = handle_test
        self.behavior_manager.load_module(module)

        message = {
            "type": "command",
            "action": {"verb": "test"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(self.handler.state_corrupted)
        self.assertFalse(result["success"])
        self.assertTrue(result.get("error", {}).get("fatal", False))

    def test_corrupted_state_blocks_commands(self):
        """Test that commands are blocked after corruption."""
        self.handler.state_corrupted = True

        message = {
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("corrupted", result["error"]["message"].lower())

    def test_meta_commands_allowed_after_corruption(self):
        """Test that save/quit are allowed after corruption."""
        self.handler.state_corrupted = True

        # These should not be blocked (they're meta-commands)
        for verb in ["save", "quit", "help"]:
            message = {
                "type": "command",
                "action": {"verb": verb}
            }
            result = self.handler.handle_message(message)
            error_msg = result.get("error", {}).get("message", "")
            self.assertNotIn("corrupted", error_msg.lower(),
                           f"Meta-command '{verb}' should not be blocked")

    def test_inconsistent_state_logs_to_stderr(self):
        """Test that error details are logged to stderr."""
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            from types import ModuleType
            module = ModuleType("test_module2")

            def handle_test2(accessor, action):
                return HandlerResult(
                    success=False,
                    message="INCONSISTENT STATE: Detailed error info"
                )
            module.handle_test2 = handle_test2
            self.behavior_manager.load_module(module)

            message = {
                "type": "command",
                "action": {"verb": "test2"}
            }

            self.handler.handle_message(message)

            stderr_output = sys.stderr.getvalue()
            self.assertIn("INCONSISTENT STATE", stderr_output)
            self.assertIn("test2", stderr_output)
        finally:
            sys.stderr = old_stderr


if __name__ == '__main__':
    unittest.main()
