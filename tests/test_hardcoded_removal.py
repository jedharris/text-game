"""Tests for Phase 6: Removal of hardcoded behaviors.

These tests verify that:
1. Light sources without behaviors are NOT auto-lit (hardcoded logic removed)
2. Light sources WITH behaviors ARE lit by the behavior system
3. Items with on_open behavior are openable regardless of name
4. The "chest" name is no longer hardcoded as openable
"""

import unittest
from pathlib import Path

from src.state_manager import load_game_state
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager


class TestHardcodedLightSourceRemoval(unittest.TestCase):
    """Test that hardcoded light source logic has been removed."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a minimal game state with light sources
        self.game_data = {
            "metadata": {
                "title": "Test Game",
                "start_location": "room1"
            },
            "locations": [
                {
                    "id": "room1",
                    "name": "Test Room",
                    "description": "A test room."
                }
            ],
            "items": [
                {
                    "id": "plain_lantern",
                    "name": "plain lantern",
                    "description": "A plain lantern without behaviors.",
                    "type": "tool",
                    "portable": True,
                    "location": "room1",
                    "provides_light": True,
                    "states": {"lit": False}
                    # No behaviors - should NOT auto-light
                },
                {
                    "id": "magic_lantern",
                    "name": "magic lantern",
                    "description": "A magic lantern with behaviors.",
                    "type": "tool",
                    "portable": True,
                    "location": "room1",
                    "provides_light": True,
                    "states": {"lit": False},
                    "behaviors": {
                        "on_take": "behaviors.core.light_sources:on_take",
                        "on_drop": "behaviors.core.light_sources:on_drop"
                    }
                }
            ],
            "doors": [],
            "npcs": [],
            "locks": []
        }

        self.state = load_game_state(self.game_data)

        # Create behavior manager and load core modules
        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        # Create handler with behavior manager
        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_plain_lantern_not_auto_lit_on_take(self):
        """Test that plain lantern (no behavior) is NOT auto-lit on take."""
        plain_lantern = self.state.get_item("plain_lantern")

        # Verify it starts unlit
        self.assertFalse(plain_lantern.states.get("lit", True))

        # Take the plain lantern
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "plain lantern"}
        })

        self.assertTrue(result.get("success"))
        # Should NOT be lit (no behavior attached)
        self.assertFalse(plain_lantern.states.get("lit", True))

    def test_magic_lantern_auto_lit_on_take(self):
        """Test that magic lantern (with behavior) IS auto-lit on take."""
        magic_lantern = self.state.get_item("magic_lantern")

        # Verify it starts unlit
        self.assertFalse(magic_lantern.states.get("lit", True))

        # Take the magic lantern
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "magic lantern"}
        })

        self.assertTrue(result.get("success"))
        # Should be lit (behavior attached)
        self.assertTrue(magic_lantern.states.get("lit", False))

    def test_plain_lantern_not_extinguished_on_drop(self):
        """Test that plain lantern (no behavior) is NOT extinguished on drop."""
        plain_lantern = self.state.get_item("plain_lantern")

        # Take the plain lantern and manually set it to lit
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "plain lantern"}
        })
        plain_lantern.states["lit"] = True

        # Drop it
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drop", "object": "plain lantern"}
        })

        self.assertTrue(result.get("success"))
        # Should still be lit (no behavior to extinguish)
        self.assertTrue(plain_lantern.states.get("lit", False))

    def test_magic_lantern_extinguished_on_drop(self):
        """Test that magic lantern (with behavior) IS extinguished on drop."""
        magic_lantern = self.state.get_item("magic_lantern")

        # Take the magic lantern (will be lit by behavior)
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "magic lantern"}
        })
        self.assertTrue(magic_lantern.states.get("lit", False))

        # Drop it
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drop", "object": "magic lantern"}
        })

        self.assertTrue(result.get("success"))
        # Should be extinguished (behavior attached)
        self.assertFalse(magic_lantern.states.get("lit", True))


class TestHardcodedChestRemoval(unittest.TestCase):
    """Test that hardcoded chest logic has been removed."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_data = {
            "metadata": {
                "title": "Test Game",
                "start_location": "room1"
            },
            "locations": [
                {
                    "id": "room1",
                    "name": "Test Room",
                    "description": "A test room."
                }
            ],
            "items": [
                {
                    "id": "plain_chest",
                    "name": "chest",
                    "description": "A plain chest without behaviors.",
                    "type": "furniture",
                    "portable": False,
                    "location": "room1",
                    "container": {
                        "is_surface": False,
                        "open": False,
                        "capacity": 10
                    }
                    # No behaviors - should still be openable but no special effect
                },
                {
                    "id": "treasure_chest",
                    "name": "treasure chest",
                    "description": "A treasure chest with behaviors.",
                    "type": "furniture",
                    "portable": False,
                    "location": "room1",
                    "container": {
                        "is_surface": False,
                        "open": False,
                        "capacity": 10
                    },
                    "behaviors": {
                        "on_open": "behaviors.core.containers:on_open"
                    }
                },
                {
                    "id": "magic_box",
                    "name": "magic box",
                    "description": "A magic box with open behavior.",
                    "type": "furniture",
                    "portable": False,
                    "location": "room1",
                    "container": {
                        "is_surface": False,
                        "open": False,
                        "capacity": 5
                    },
                    "behaviors": {
                        "on_open": "behaviors.core.containers:on_open"
                    }
                },
                {
                    "id": "rock",
                    "name": "rock",
                    "description": "A plain rock.",
                    "type": "scenery",
                    "portable": True,
                    "location": "room1"
                    # Not a container, no behavior - should NOT be openable
                }
            ],
            "doors": [],
            "npcs": [],
            "locks": []
        }

        self.state = load_game_state(self.game_data)

        # Create behavior manager and load core modules
        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        # Create handler with behavior manager
        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_plain_chest_openable_no_win(self):
        """Test that plain chest is openable but doesn't set win flag."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "chest"}
        })

        # Should succeed (it's a container)
        self.assertTrue(result.get("success"))
        # Should NOT set win flag (no behavior)
        self.assertFalse(self.state.actors["player"].flags.get("won", False))

    def test_treasure_chest_sets_win_flag(self):
        """Test that treasure chest with behavior sets win flag."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "treasure chest"}
        })

        self.assertTrue(result.get("success"))
        # Should set win flag (behavior attached)
        self.assertTrue(self.state.actors["player"].flags.get("won", False))
        # Should have behavior message
        self.assertIn("message", result)

    def test_magic_box_with_behavior_openable(self):
        """Test that non-chest item with on_open behavior is openable."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "magic box"}
        })

        # Should succeed because it has on_open behavior
        self.assertTrue(result.get("success"))
        # Should invoke behavior
        self.assertIn("message", result)

    def test_rock_not_openable(self):
        """Test that rock without behavior/container is not openable."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "rock"}
        })

        # Should fail
        self.assertFalse(result.get("success"))


class TestBehaviorDrivenApproach(unittest.TestCase):
    """Test that behaviors are now the source of truth for special effects."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_data = {
            "metadata": {
                "title": "Test Game",
                "start_location": "room1"
            },
            "locations": [
                {
                    "id": "room1",
                    "name": "Test Room",
                    "description": "A test room."
                }
            ],
            "items": [
                {
                    "id": "potion",
                    "name": "potion",
                    "description": "A potion with drink behavior.",
                    "type": "tool",
                    "portable": True,
                    "drinkable": True,
                    "location": "room1",
                    "behaviors": {
                        "on_drink": "behaviors.core.consumables:on_drink"
                    }
                },
                {
                    "id": "water",
                    "name": "water",
                    "description": "Plain water without behavior.",
                    "type": "tool",
                    "portable": True,
                    "drinkable": True,
                    "location": "room1"
                    # No behavior - but still drinkable
                }
            ],
            "doors": [],
            "npcs": [],
            "locks": [],
            "player": {
                "location": "room1",
                "inventory": [],
                "flags": {},
                "stats": {"health": 50, "max_health": 100}
            }
        }

        self.state = load_game_state(self.game_data)

        # Create behavior manager and load core modules
        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        # Create handler with behavior manager
        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_potion_with_behavior_heals(self):
        """Test that potion with behavior heals player."""
        initial_health = self.state.actors["player"].stats["health"]

        # Take and drink
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "potion"}
        })
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink", "object": "potion"}
        })

        # Should have healed
        self.assertGreater(self.state.actors["player"].stats["health"], initial_health)

    def test_water_without_behavior_no_heal(self):
        """Test that water without behavior doesn't heal."""
        initial_health = self.state.actors["player"].stats["health"]

        # Take and drink
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "water"}
        })
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink", "object": "water"}
        })

        # Should succeed but no healing
        self.assertTrue(result.get("success"))
        self.assertEqual(self.state.actors["player"].stats["health"], initial_health)
        # Handler provides message (entity behavior may add to it)
        self.assertIn("message", result)
        self.assertIn("drink", result.get("message", "").lower())


if __name__ == '__main__':
    unittest.main()
