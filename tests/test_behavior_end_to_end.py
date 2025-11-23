"""End-to-end tests for behavior system (Phase 4)."""

import unittest
import json
from pathlib import Path

from src.state_manager import load_game_state
from src.json_protocol import JSONProtocolHandler
from src.behavior_manager import BehaviorManager, get_behavior_manager


class TestRubberDuckBehavior(unittest.TestCase):
    """Test the rubber duck behavior module end-to-end."""

    def setUp(self):
        """Set up test fixtures."""
        # Load test game state
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_with_behaviors.json"
        self.state = load_game_state(fixture_path)

        # Create behavior manager and discover modules
        self.manager = BehaviorManager()

        # Discover and load behavior modules
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        # Create handler with behavior manager
        self.handler = JSONProtocolHandler(self.state, behavior_manager=self.manager)

    def test_squeeze_verb_registered(self):
        """Test that squeeze verb handler is registered."""
        self.assertTrue(self.manager.has_handler("squeeze"))

    def test_squeeze_vocabulary_merged(self):
        """Test that squeeze verb is added to vocabulary."""
        base_vocab = {"verbs": [], "directions": []}
        merged = self.manager.get_merged_vocabulary(base_vocab)

        verb_words = [v["word"] for v in merged["verbs"]]
        self.assertIn("squeeze", verb_words)

    def test_squeeze_command_works(self):
        """Test that squeeze command works on rubber duck."""
        # First take the duck
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "rubber duck"}
        })

        # Then squeeze it
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "squeeze", "object": "rubber duck"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "squeeze")

    def test_squeeze_invokes_behavior(self):
        """Test that squeeze command invokes on_squeeze behavior."""
        # Take the duck
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "rubber duck"}
        })

        # Squeeze it
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "squeeze", "object": "rubber duck"}
        })

        # Check behavior message
        self.assertIn("message", result)
        self.assertIn("squeak", result["message"].lower())

    def test_squeeze_modifies_entity_state(self):
        """Test that squeezing modifies the duck's state."""
        # Get initial squeak count
        duck = self.state.get_item("rubber_duck")
        initial_squeaks = duck.states.get("squeaks", 0)

        # Take and squeeze the duck
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "rubber duck"}
        })
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "squeeze", "object": "rubber duck"}
        })

        # Check squeak count increased
        self.assertEqual(duck.states["squeaks"], initial_squeaks + 1)

    def test_squeeze_multiple_times(self):
        """Test squeezing multiple times increments counter."""
        duck = self.state.get_item("rubber_duck")

        # Take the duck
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "rubber duck"}
        })

        # Squeeze multiple times
        for i in range(3):
            self.handler.handle_command({
                "type": "command",
                "action": {"verb": "squeeze", "object": "rubber duck"}
            })

        self.assertEqual(duck.states["squeaks"], 3)

    def test_squeeze_non_squeezable_item(self):
        """Test squeezing an item without squeeze behavior."""
        # Take the rock
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "rock"}
        })

        # Try to squeeze it
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "squeeze", "object": "rock"}
        })

        # Should succeed but with default message (no behavior)
        self.assertTrue(result.get("success"))

    def test_squeeze_item_not_in_inventory(self):
        """Test squeezing item that's not in inventory."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "squeeze", "object": "rubber duck"}
        })

        # Should fail - not carrying it
        self.assertFalse(result.get("success"))

    def test_squeeze_nonexistent_item(self):
        """Test squeezing item that doesn't exist."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "squeeze", "object": "unicorn"}
        })

        self.assertFalse(result.get("success"))


class TestLoadingGameWithBehaviors(unittest.TestCase):
    """Test loading and setting up a game with behaviors."""

    def test_load_game_state_with_behaviors(self):
        """Test that game state loads correctly with behaviors."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_with_behaviors.json"
        state = load_game_state(fixture_path)

        duck = state.get_item("rubber_duck")
        self.assertEqual(duck.behaviors["on_squeeze"], "behaviors.items.rubber_duck:on_squeeze")

    def test_item_without_behaviors_has_empty_dict(self):
        """Test that items without behaviors have empty dict."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_with_behaviors.json"
        state = load_game_state(fixture_path)

        rock = state.get_item("plain_rock")
        self.assertEqual(rock.behaviors, {})

    def test_discover_rubber_duck_module(self):
        """Test that rubber duck module is discovered."""
        manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = manager.discover_modules(str(behaviors_dir))

        # Should find the rubber duck module
        self.assertTrue(
            any("rubber_duck" in m for m in modules),
            f"rubber_duck not found in modules: {modules}"
        )


class TestBehaviorModuleStructure(unittest.TestCase):
    """Test the structure of behavior modules."""

    def test_rubber_duck_module_has_vocabulary(self):
        """Test that rubber duck module defines vocabulary."""
        from behaviors.items import rubber_duck

        self.assertTrue(hasattr(rubber_duck, 'vocabulary'))
        self.assertIn("verbs", rubber_duck.vocabulary)

        verb_words = [v["word"] for v in rubber_duck.vocabulary["verbs"]]
        self.assertIn("squeeze", verb_words)

    def test_rubber_duck_module_has_handler(self):
        """Test that rubber duck module has squeeze handler."""
        from behaviors.items import rubber_duck

        self.assertTrue(hasattr(rubber_duck, 'handle_squeeze'))
        self.assertTrue(callable(rubber_duck.handle_squeeze))

    def test_rubber_duck_module_has_behavior(self):
        """Test that rubber duck module has on_squeeze behavior."""
        from behaviors.items import rubber_duck

        self.assertTrue(hasattr(rubber_duck, 'on_squeeze'))
        self.assertTrue(callable(rubber_duck.on_squeeze))


if __name__ == '__main__':
    unittest.main()
