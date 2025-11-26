"""Tests for game_engine module.

These tests verify that game_engine.py correctly formats JSON protocol
responses as text output, including behavior messages.
"""

import unittest
import json
from pathlib import Path

from src.game_engine import format_command_result, format_location_query, format_inventory_query
from src.state_manager import load_game_state
from src.llm_protocol import JSONProtocolHandler
from src.behavior_manager import BehaviorManager


class TestBehaviorMessageDisplay(unittest.TestCase):
    """Test that behavior messages are displayed correctly via JSON protocol."""

    def setUp(self):
        """Set up test fixtures with lantern that has on_take/on_drop behaviors."""
        # Load game state with lantern
        fixture_path = Path(__file__).parent.parent / "examples" / "simple_game_state.json"
        self.state = load_game_state(fixture_path)

        # Create behavior manager and load modules
        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        # Create handler with behavior manager
        self.handler = JSONProtocolHandler(self.state, behavior_manager=self.manager)

        # Move player to hallway where lantern is
        self.state.player.location = "loc_hallway"

    def test_take_command_includes_behavior_message(self):
        """Test that take command includes behavior message from on_take."""
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        output = format_command_result(result)
        # Check that the behavior message was included
        self.assertIn("runes", output.lower())
        self.assertIn("glow", output.lower())

    def test_drop_command_includes_behavior_message(self):
        """Test that drop command includes behavior message from on_drop."""
        # First take the lantern
        self.handler.handle_message({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        # Then drop it
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "drop", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        output = format_command_result(result)
        # Check that the behavior message was included
        self.assertIn("runes", output.lower())
        self.assertIn("fade", output.lower())

    def test_take_item_without_behavior_basic_message(self):
        """Test that items without behaviors have basic message."""
        # Key is in loc_hallway and has no on_take behavior
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "take", "object": "key"}
        })

        self.assertTrue(result.get("success"))
        output = format_command_result(result)
        # Should have the basic "You take the key" message
        self.assertIn("take", output.lower())
        self.assertIn("key", output.lower())
        # Should not have behavior-specific text (like lantern runes)
        self.assertNotIn("runes", output.lower())


class TestMessageKeyConsistency(unittest.TestCase):
    """Test that behavior messages use consistent key names."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent.parent / "examples" / "simple_game_state.json"
        self.state = load_game_state(fixture_path)

        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        self.handler = JSONProtocolHandler(self.state, behavior_manager=self.manager)
        self.state.player.location = "loc_hallway"

    def test_take_result_uses_message_key(self):
        """Test that take command result uses 'message' key, not 'behavior_message'."""
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        # Should use 'message' key
        self.assertIn("message", result)
        # Should NOT use old 'behavior_message' key
        self.assertNotIn("behavior_message", result)

    def test_drop_result_uses_message_key(self):
        """Test that drop command result uses 'message' key, not 'behavior_message'."""
        # First take
        self.handler.handle_message({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        # Then drop
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "drop", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("message", result)
        self.assertNotIn("behavior_message", result)


class TestLLMGameSetup(unittest.TestCase):
    """Test that llm_game properly configures behavior manager."""

    def test_llm_game_handler_has_behavior_manager(self):
        """Test that llm_game creates handler with behavior manager."""
        # Replicate llm_game setup
        from pathlib import Path
        project_root = Path(__file__).parent.parent

        fixture_path = project_root / "examples" / "simple_game_state.json"
        state = load_game_state(fixture_path)

        # Create behavior manager like llm_game does
        behavior_manager = BehaviorManager()
        behaviors_dir = project_root / "behaviors"
        modules = behavior_manager.discover_modules(str(behaviors_dir))
        behavior_manager.load_modules(modules)

        # Create handler with behavior manager
        json_handler = JSONProtocolHandler(state, behavior_manager=behavior_manager)

        # Verify behavior manager is attached
        self.assertIsNotNone(json_handler.behavior_manager)

    def test_llm_game_behaviors_are_invoked(self):
        """Test that behaviors are actually invoked in llm_game setup."""
        from pathlib import Path
        project_root = Path(__file__).parent.parent

        fixture_path = project_root / "examples" / "simple_game_state.json"
        state = load_game_state(fixture_path)

        behavior_manager = BehaviorManager()
        behaviors_dir = project_root / "behaviors"
        modules = behavior_manager.discover_modules(str(behaviors_dir))
        behavior_manager.load_modules(modules)

        json_handler = JSONProtocolHandler(state, behavior_manager=behavior_manager)

        # Move to hallway and take lantern
        state.player.location = "loc_hallway"
        result = json_handler.handle_message({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        # Verify behavior was invoked (message present and lit state changed)
        self.assertTrue(result.get("success"))
        self.assertIn("message", result, "Behavior message missing - behavior not invoked")
        # Behavior sets lit=True via entity.states["lit"]
        # Check actual state, not response format
        lantern = next((i for i in state.items if i.name == "lantern"), None)
        self.assertIsNotNone(lantern, "Lantern not found in state")
        self.assertTrue(
            lantern.states.get("lit"),
            "Lantern not lit - behavior not invoked"
        )


class TestFormatFunctions(unittest.TestCase):
    """Test the format functions used to convert JSON responses to text."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent.parent / "examples" / "simple_game_state.json"
        self.state = load_game_state(fixture_path)

        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        self.handler = JSONProtocolHandler(self.state, behavior_manager=self.manager)

    def test_format_command_result_success(self):
        """Test formatting successful command result."""
        result = {"success": True, "message": "You did the thing."}
        output = format_command_result(result)
        self.assertEqual(output, "You did the thing.")

    def test_format_command_result_failure(self):
        """Test formatting failed command result."""
        result = {"success": False, "error": {"code": "NOTFOUND", "message": "Item not found."}}
        output = format_command_result(result)
        self.assertEqual(output, "Item not found.")

    def test_format_location_query_basic(self):
        """Test formatting basic location query."""
        self.state.player.location = "loc_hallway"
        response = self.handler.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["items", "doors"]
        })
        output = format_location_query(response)
        self.assertIn("Hallway", output)

    def test_format_inventory_query_empty(self):
        """Test formatting empty inventory."""
        response = {"success": True, "data": {"items": []}}
        output = format_inventory_query(response)
        self.assertIn("not carrying anything", output.lower())

    def test_format_inventory_query_with_items(self):
        """Test formatting inventory with items."""
        response = {"success": True, "data": {"items": [{"name": "key"}, {"name": "sword"}]}}
        output = format_inventory_query(response)
        self.assertIn("key", output)
        self.assertIn("sword", output)


if __name__ == '__main__':
    unittest.main()
