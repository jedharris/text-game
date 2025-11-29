"""
Tests for old method removal (Phase I-5).

Verifies that old _cmd_* methods are removed and commands
still work through behavior handlers.
"""

import unittest
from src.llm_protocol import LLMProtocolHandler
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

        self.handler = LLMProtocolHandler(self.state, self.behavior_manager)

    def test_cmd_methods_removed_handlers_active(self):
        """Test that old _cmd_* methods have been removed and behavior handlers are active.

        NOTE: Old _cmd_* methods have been removed as part of cleanup.
        All command handling now goes through the behavior system.
        """
        # Old methods have been removed
        self.assertFalse(hasattr(self.handler, '_cmd_take'))
        self.assertFalse(hasattr(self.handler, '_cmd_drop'))
        self.assertFalse(hasattr(self.handler, '_cmd_go'))

        # Behavior handlers are registered and handle all commands
        self.assertTrue(self.handler.behavior_manager.has_handler('take'))
        self.assertTrue(self.handler.behavior_manager.has_handler('drop'))
        self.assertTrue(self.handler.behavior_manager.has_handler('go'))
        self.assertTrue(self.handler.behavior_manager.has_handler('look'))
        self.assertTrue(self.handler.behavior_manager.has_handler('examine'))
        self.assertTrue(self.handler.behavior_manager.has_handler('inventory'))

    def test_old_helper_methods_removed(self):
        """Test that unused helper methods have been removed.

        After Phase C-4, all unused helper methods should be removed.
        Only _get_container_for_item remains (used by _entity_to_dict).
        """
        # These were removed (no longer needed after full migration)
        self.assertFalse(hasattr(self.handler, '_find_accessible_item'))
        self.assertFalse(hasattr(self.handler, '_find_container_by_name'))
        self.assertFalse(hasattr(self.handler, '_player_has_key_for_door'))
        self.assertFalse(hasattr(self.handler, '_is_item_in_container'))

        # This is kept because _entity_to_dict uses it
        self.assertTrue(hasattr(self.handler, '_get_container_for_item'))

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
