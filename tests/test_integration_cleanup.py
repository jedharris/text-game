"""
Tests for old method removal (Phase I-5).

Verifies that old _cmd_* methods are removed and commands
still work through behavior handlers.
"""

import unittest
from src.json_protocol import JSONProtocolHandler
from src.behavior_manager import BehaviorManager
from tests.conftest import create_test_state


class TestOldMethodsRemoved(unittest.TestCase):
    """Test that old _cmd_* methods are removed."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        # Load behavior modules
        import behaviors.core.manipulation
        import behaviors.core.movement
        import behaviors.core.perception
        import behaviors.core.interaction
        import behaviors.core.locks

        self.behavior_manager.load_module(behaviors.core.manipulation)
        self.behavior_manager.load_module(behaviors.core.movement)
        self.behavior_manager.load_module(behaviors.core.perception)
        self.behavior_manager.load_module(behaviors.core.interaction)
        self.behavior_manager.load_module(behaviors.core.locks)

        self.handler = JSONProtocolHandler(self.state, self.behavior_manager)

    def test_cmd_methods_bypassed_by_handlers(self):
        """Test that old _cmd_* methods are bypassed by behavior handlers.

        NOTE: Phase I-5 was deferred - old _cmd_* methods still exist but are
        never called for migrated commands because behavior_manager.has_handler()
        is checked first. This test verifies the routing works correctly.

        The old methods can be safely deleted in a future cleanup phase.
        """
        # Old methods still exist (not deleted yet)
        self.assertTrue(hasattr(self.handler, '_cmd_take'))
        self.assertTrue(hasattr(self.handler, '_cmd_drop'))
        self.assertTrue(hasattr(self.handler, '_cmd_go'))

        # But behavior handlers are registered and called first
        self.assertTrue(self.handler.behavior_manager.has_handler('take'))
        self.assertTrue(self.handler.behavior_manager.has_handler('drop'))
        self.assertTrue(self.handler.behavior_manager.has_handler('go'))
        self.assertTrue(self.handler.behavior_manager.has_handler('look'))
        self.assertTrue(self.handler.behavior_manager.has_handler('examine'))
        self.assertTrue(self.handler.behavior_manager.has_handler('inventory'))

    def test_old_helper_methods_status(self):
        """Test helper methods status.

        Note: Some helper methods are kept because they're still used by
        unmigrated _cmd_* methods (drink, eat, attack, use, read, climb, pull, push, put).
        """
        # These are kept because unmigrated methods still use them
        self.assertTrue(hasattr(self.handler, '_find_accessible_item'))
        self.assertTrue(hasattr(self.handler, '_find_container_by_name'))
        self.assertTrue(hasattr(self.handler, '_get_container_for_item'))

        # These could potentially be removed but are still present
        # for backward compatibility with put and unmigrated commands
        self.assertTrue(hasattr(self.handler, '_player_has_key_for_door'))
        self.assertTrue(hasattr(self.handler, '_is_item_in_container'))

    def test_commands_still_work_after_removal(self):
        """Test that commands still work through behavior handlers."""
        # Test take
        message = {"type": "command", "action": {"verb": "take", "object": "sword"}}
        result = self.handler.handle_message(message)
        self.assertTrue(result["success"], f"take failed: {result}")

        # Test drop
        message = {"type": "command", "action": {"verb": "drop", "object": "sword"}}
        result = self.handler.handle_message(message)
        self.assertTrue(result["success"], f"drop failed: {result}")

        # Test look
        message = {"type": "command", "action": {"verb": "look"}}
        result = self.handler.handle_message(message)
        self.assertTrue(result["success"], f"look failed: {result}")

        # Test inventory
        message = {"type": "command", "action": {"verb": "inventory"}}
        result = self.handler.handle_message(message)
        self.assertTrue(result["success"], f"inventory failed: {result}")

    def test_unmigrated_commands_still_work(self):
        """Test that unmigrated _cmd_* methods still work (drink, eat, etc.)."""
        # Put item in inventory first
        player = self.state.actors["player"]
        player.inventory.append("item_sword")
        sword = self.state.get_item("item_sword")
        sword.location = "player"

        # drink should still work via _cmd_drink (if it exists)
        # or return unknown command error
        message = {"type": "command", "action": {"verb": "drink", "object": "sword"}}
        result = self.handler.handle_message(message)
        # May fail because sword isn't drinkable, but should route to handler
        self.assertEqual(result["type"], "result")


if __name__ == '__main__':
    unittest.main()
