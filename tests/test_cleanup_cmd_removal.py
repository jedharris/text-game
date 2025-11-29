"""
Tests for Phase C-3: Remove old _cmd_* methods.

These tests verify that:
1. Migrated _cmd_* methods are removed from LLMProtocolHandler
2. Commands still work through behavior handlers after removal
3. Stub _cmd_* methods remain until migrated in Phase C-8
"""

import unittest
from pathlib import Path

from src.state_manager import load_game_state
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager


class TestCmdMethodsRemoval(unittest.TestCase):
    """Test that migrated _cmd_* methods are removed."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = load_game_state(Path("examples/simple_game/game_state.json"))
        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)
        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_migrated_cmd_methods_removed(self):
        """Test that all migrated _cmd_* methods are removed."""
        # These methods should be removed (have behavior handlers)
        migrated_methods = [
            '_cmd_take',
            '_cmd_drop',
            '_cmd_give',
            '_cmd_look',
            '_cmd_examine',
            '_cmd_inventory',
            '_cmd_go',
            '_cmd_open',
            '_cmd_close',
            '_cmd_lock',
            '_cmd_unlock',
        ]

        for method in migrated_methods:
            self.assertFalse(
                hasattr(self.handler, method),
                f"Method {method} should be removed (has behavior handler)"
            )

    def test_stub_cmd_methods_removed(self):
        """Test that stub _cmd_* methods are removed after Phase C-8."""
        # These methods should now be removed (migrated in Phase C-8)
        stub_methods = [
            '_cmd_drink',
            '_cmd_eat',
            '_cmd_attack',
            '_cmd_use',
            '_cmd_read',
            '_cmd_climb',
            '_cmd_pull',
            '_cmd_push',
            '_cmd_put',
        ]

        for method in stub_methods:
            self.assertFalse(
                hasattr(self.handler, method),
                f"Method {method} should be removed (migrated in Phase C-8)"
            )


class TestCommandsStillWork(unittest.TestCase):
    """Test that commands still work after _cmd_* removal."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = load_game_state(Path("examples/simple_game/game_state.json"))
        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)
        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_take_command_works(self):
        """Test take command works through behavior handler."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "take")

    def test_drop_command_works(self):
        """Test drop command works through behavior handler."""
        # First take the sword
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        # Then drop it
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drop", "object": "sword"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "drop")

    def test_look_command_works(self):
        """Test look command works through behavior handler."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "look"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "look")

    def test_examine_command_works(self):
        """Test examine command works through behavior handler."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "sword"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "examine")

    def test_inventory_command_works(self):
        """Test inventory command works through behavior handler."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "inventory"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "inventory")

    def test_go_command_works(self):
        """Test go command works through behavior handler."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "direction": "north"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "go")

    def test_open_command_works(self):
        """Test open command works through behavior handler."""
        # Go to hallway first (where the locked door is)
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "direction": "north"}
        })

        # Close the wooden door first so we can open it (use adjective + object)
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "close", "object": "door", "adjective": "wooden"}
        })

        # Now open it (use adjective + object)
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "wooden"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "open")

    def test_close_command_works(self):
        """Test close command works through behavior handler."""
        # Go north first
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "direction": "north"}
        })

        # Close the wooden door (use adjective + object)
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "close", "object": "door", "adjective": "wooden"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "close")

    def test_unlock_command_works(self):
        """Test unlock command works through behavior handler."""
        # Go to hallway and take key
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "direction": "north"}
        })
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "key"}
        })

        # Unlock the treasure door (use adjective + object)
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "unlock")


if __name__ == '__main__':
    unittest.main()
