"""
Tests for command routing integration (Phase I-1).

Verifies that commands route through behavior_manager.invoke_handler()
instead of the old _cmd_* methods.

Reference: behavior_refactoring_testing.md lines 113-153 (basic handler tests)
"""

import unittest
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from tests.conftest import create_test_state


class TestCommandRouting(unittest.TestCase):
    """Test that commands route through behavior handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        # Load behavior modules
        import behaviors.core.manipulation
        import behaviors.core.exits
        import behaviors.core.perception
        import behaviors.core.interaction
        import behaviors.core.locks

        self.behavior_manager.load_module(behaviors.core.manipulation)
        self.behavior_manager.load_module(behaviors.core.exits)
        self.behavior_manager.load_module(behaviors.core.perception)
        self.behavior_manager.load_module(behaviors.core.interaction)
        self.behavior_manager.load_module(behaviors.core.locks)

        self.handler = LLMProtocolHandler(self.state, self.behavior_manager)

    def test_take_routes_to_behavior_handler(self):
        """Test that 'take' command uses behavior handler."""
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertTrue(result["success"], f"take failed: {result}")
        # Verify state changed (item in inventory)
        self.assertIn("item_sword", self.state.actors["player"].inventory)

    def test_drop_routes_to_behavior_handler(self):
        """Test that 'drop' command uses behavior handler."""
        # Put item in inventory first
        player = self.state.actors["player"]
        player.inventory.append("item_sword")
        sword = self.state.get_item("item_sword")
        sword.location = "player"

        message = {
            "type": "command",
            "action": {"verb": "drop", "object": "sword"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertTrue(result["success"], f"drop failed: {result}")
        self.assertNotIn("item_sword", player.inventory)

    def test_go_routes_to_behavior_handler(self):
        """Test that 'go' command uses behavior handler."""
        message = {
            "type": "command",
            "action": {"verb": "go", "object": "north"}
        }

        result = self.handler.handle_message(message)

        # Should fail (no exit) but route through handler
        self.assertEqual(result["type"], "result")
        self.assertFalse(result["success"])
        # Should get error about direction, not "unknown command"
        error_msg = result.get("error", {}).get("message", "").lower()
        self.assertTrue(
            "can't go" in error_msg or "no exit" in error_msg or "north" in error_msg,
            f"Expected direction-related error, got: {error_msg}"
        )

    def test_look_routes_to_behavior_handler(self):
        """Test that 'look' command uses behavior handler."""
        message = {
            "type": "command",
            "action": {"verb": "look"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertTrue(result["success"], f"look failed: {result}")
        self.assertIn("message", result)

    def test_inventory_routes_to_behavior_handler(self):
        """Test that 'inventory' command uses behavior handler."""
        message = {
            "type": "command",
            "action": {"verb": "inventory"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertTrue(result["success"], f"inventory failed: {result}")

    def test_command_error_returns_proper_format(self):
        """Test that handler errors are formatted correctly."""
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "nonexistent"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_unknown_verb_returns_error(self):
        """Test that unknown verbs get proper error."""
        message = {
            "type": "command",
            "action": {"verb": "xyzzy"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertFalse(result["success"])


if __name__ == '__main__':
    unittest.main()
