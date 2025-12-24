"""Tests for core behavior modules.

Tests consumable items, light sources, and container behaviors:
- consumables.py (drink, eat)
- light_sources.py (lantern auto-light)
- containers.py (chest win condition)

Updated for Phase 4 (Narration API) to handle NarrationResult format.
"""
from src.types import ActorId
from typing import Any, Dict

import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from src.state_manager import load_game_state
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager, EventResult


def get_result_message(result: Dict[str, Any]) -> str:
    """
    Extract message text from result, handling both old and new formats.

    New format (Phase 4): result["narration"]["primary_text"]
    Old format: result["message"] or result["error"]["message"]

    For the new format, also concatenates secondary_beats.
    """
    # New format: NarrationResult
    if "narration" in result:
        narration = result["narration"]
        parts = [narration.get("primary_text", "")]
        if "secondary_beats" in narration:
            parts.extend(narration["secondary_beats"])
        return "\n".join(parts)

    # Old format - success case
    if result.get("success") and "message" in result:
        return result["message"]

    # Old format - error case
    if "error" in result and "message" in result["error"]:
        return result["error"]["message"]

    return result.get("message", "")


class TestConsumablesBehaviors(unittest.TestCase):
    """Test consumables behavior module (drink, eat)."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_with_core_behaviors.json"
        self.game_state = load_game_state(fixture_path)

        # Create behavior manager and load core modules
        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        # Create handler with behavior manager
        self.handler = LLMProtocolHandler(self.game_state, behavior_manager=self.manager)

    def test_drink_potion_success(self):
        """Test drinking a potion successfully."""
        # Take the potion first
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "potion"}
        })

        # Drink the potion
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink", "object": "potion"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "drink")

    def test_drink_potion_heals(self):
        """Test that drinking health potion increases health."""
        initial_health = self.game_state.actors[ActorId("player")].stats.get("health", 100)

        # Take and drink the potion
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "potion"}
        })
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink", "object": "potion"}
        })

        # Health should have increased
        new_health = self.game_state.actors[ActorId("player")].stats.get("health", 100)
        self.assertGreater(new_health, initial_health)

    def test_drink_potion_removes_from_inventory(self):
        """Test that drinking potion removes it from inventory."""
        # Take the potion
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "potion"}
        })

        # Verify it's in inventory
        self.assertIn("health_potion", self.game_state.actors[ActorId("player")].inventory)

        # Drink the potion
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink", "object": "potion"}
        })

        # Should be removed from inventory
        self.assertNotIn("health_potion", self.game_state.actors[ActorId("player")].inventory)

    def test_drink_potion_has_message(self):
        """Test that drinking potion returns a behavior message."""
        # Take and drink
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "potion"}
        })
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink", "object": "potion"}
        })

        self.assertIn("narration", result)

    def test_drink_not_in_inventory(self):
        """Test drinking item not in inventory fails."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink", "object": "potion"}
        })

        self.assertFalse(result.get("success"))

    def test_drink_nonexistent_item(self):
        """Test drinking nonexistent item fails."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink", "object": "unicorn tears"}
        })

        self.assertFalse(result.get("success"))

    def test_drink_no_object(self):
        """Test drink command without object fails."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink"}
        })

        self.assertFalse(result.get("success"))

    def test_eat_food_success(self):
        """Test eating food successfully."""
        # Take the bread first
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "bread"}
        })

        # Eat the bread
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "eat", "object": "bread"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "eat")

    def test_eat_food_removes_from_inventory(self):
        """Test that eating food removes it from inventory."""
        # Take the bread
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "bread"}
        })

        # Verify it's in inventory
        self.assertIn("bread", self.game_state.actors[ActorId("player")].inventory)

        # Eat the bread
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "eat", "object": "bread"}
        })

        # Should be removed from inventory
        self.assertNotIn("bread", self.game_state.actors[ActorId("player")].inventory)

    def test_eat_food_has_message(self):
        """Test that eating food returns a behavior message."""
        # Take and eat
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "bread"}
        })
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "eat", "object": "bread"}
        })

        self.assertIn("narration", result)

    def test_eat_not_in_inventory(self):
        """Test eating item not in inventory fails."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "eat", "object": "bread"}
        })

        self.assertFalse(result.get("success"))

    def test_drink_item_without_behavior(self):
        """Test drinking item without drink behavior."""
        # Take water (no on_drink behavior)
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "water"}
        })

        # Should succeed with basic message (handler provides default)
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink", "object": "water"}
        })

        self.assertTrue(result.get("success"))
        # Handler always provides a message
        self.assertIn("narration", result)
        self.assertIn("drink", get_result_message(result).lower())


class TestLightSourcesBehaviors(unittest.TestCase):
    """Test light sources behavior module (auto-light on take/drop)."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_with_core_behaviors.json"
        self.game_state = load_game_state(fixture_path)

        # Create behavior manager and load core modules
        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        # Create handler with behavior manager
        self.handler = LLMProtocolHandler(self.game_state, behavior_manager=self.manager)

    def test_lantern_starts_unlit(self):
        """Test that lantern starts in unlit state."""
        lantern = self.game_state.get_item("magic_lantern")
        self.assertFalse(lantern.states.get("lit", True))

    def test_take_lantern_auto_lights(self):
        """Test that taking lantern automatically lights it."""
        lantern = self.game_state.get_item("magic_lantern")

        # Take the lantern
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        # Lantern should be lit
        self.assertTrue(lantern.states.get("lit", False))

    def test_take_lantern_has_message(self):
        """Test that taking lantern returns a behavior message."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("narration", result)

    def test_drop_lantern_extinguishes(self):
        """Test that dropping lantern extinguishes it."""
        lantern = self.game_state.get_item("magic_lantern")

        # Take then drop
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        # Should be lit after taking
        self.assertTrue(lantern.states.get("lit", False))

        # Drop it
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drop", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        # Should be extinguished
        self.assertFalse(lantern.states.get("lit", True))

    def test_drop_lantern_has_message(self):
        """Test that dropping lantern returns a behavior message."""
        # Take first
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        # Drop
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drop", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("narration", result)

    def test_take_non_light_item_no_behavior(self):
        """Test that taking non-light item has no special light behavior."""
        # Take rock (no light source behavior)
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "rock"}
        })

        self.assertTrue(result.get("success"))
        # Message present (all commands return message now)
        # but no light-specific behavior message
        msg = get_result_message(result)
        self.assertNotIn("rune", msg.lower())
        self.assertNotIn("glow", msg.lower())
        self.assertNotIn("lit", msg.lower())

    def test_put_lantern_extinguishes(self):
        """Test that putting lantern on surface extinguishes it."""
        # Use simple_game_state which has a table surface
        fixture_path = Path(__file__).parent.parent / "examples" / "simple_game" / "game_state.json"
        state = load_game_state(fixture_path)

        # Create handler with behavior manager
        handler = LLMProtocolHandler(state, behavior_manager=self.manager)

        # Move player to hallway where lantern and table are
        state.set_actor_location("loc_hallway")

        lantern = state.get_item("item_lantern")

        # Take the lantern (lights it)
        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })
        self.assertTrue(lantern.states.get("lit", False))

        # Put it on the table
        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "put", "object": "lantern", "indirect_object": "table"}
        })

        self.assertTrue(result.get("success"))
        # Should be extinguished
        self.assertFalse(lantern.states.get("lit", True))

    def test_examine_lantern_shows_unlit_state(self):
        """Test that examining unlit lantern shows it is unlit."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        msg = get_result_message(result).lower()
        self.assertIn("unlit", msg)

    def test_examine_lantern_shows_lit_state(self):
        """Test that examining lit lantern shows it is lit."""
        # Take the lantern (which lights it)
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        msg = get_result_message(result).lower()
        self.assertIn("lit", msg)
        self.assertNotIn("unlit", msg)


class TestContainersBehaviors(unittest.TestCase):
    """Test containers behavior module (chest win condition)."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_with_core_behaviors.json"
        self.game_state = load_game_state(fixture_path)

        # Move player to room2 where chest is
        self.game_state.actors[ActorId("player")].location = "room2"

        # Create behavior manager and load core modules
        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        # Create handler with behavior manager
        self.handler = LLMProtocolHandler(self.game_state, behavior_manager=self.manager)

    def test_open_chest_succeeds(self):
        """Test opening treasure chest succeeds."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "chest"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "open")

    def test_open_chest_sets_win_flag(self):
        """Test that opening chest sets win flag."""
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "chest"}
        })

        # Win flag should be set
        self.assertTrue(self.game_state.actors[ActorId("player")].flags.get("won", False))

    def test_open_chest_has_message(self):
        """Test that opening chest returns a behavior message."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "chest"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("narration", result)
        # Message should mention treasure or winning
        msg = get_result_message(result).lower()
        self.assertTrue("treasure" in msg or "win" in msg)

    def test_open_nonexistent_item(self):
        """Test opening nonexistent item fails."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "open", "object": "magic box"}
        })

        self.assertFalse(result.get("success"))


class TestCoreModulesLoading(unittest.TestCase):
    """Test that core behavior modules are properly discovered and loaded."""

    def test_discover_core_modules(self):
        """Test that core behavior modules are discovered."""
        manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        # Returns list of (module_path, source_type) tuples
        modules = manager.discover_modules(str(behaviors_dir))

        # Should find core modules
        module_names = [m[0].split(".")[-1] for m in modules]
        self.assertIn("consumables", module_names)
        self.assertIn("light_sources", module_names)
        self.assertIn("containers", module_names)

    def test_consumables_module_structure(self):
        """Test that consumables module has correct structure."""
        from behaviors.core import consumables

        # Should have behavior functions
        self.assertTrue(hasattr(consumables, 'on_drink'))
        self.assertTrue(callable(consumables.on_drink))
        self.assertTrue(hasattr(consumables, 'on_eat'))
        self.assertTrue(callable(consumables.on_eat))

    def test_light_sources_module_structure(self):
        """Test that light_sources module has correct structure."""
        from behaviors.core import light_sources

        # Should have behavior functions
        self.assertTrue(hasattr(light_sources, 'on_take'))
        self.assertTrue(callable(light_sources.on_take))
        self.assertTrue(hasattr(light_sources, 'on_drop'))
        self.assertTrue(callable(light_sources.on_drop))

    def test_containers_module_structure(self):
        """Test that containers module has correct structure."""
        from behaviors.core import containers

        # Should have behavior functions
        self.assertTrue(hasattr(containers, 'on_open'))
        self.assertTrue(callable(containers.on_open))


class TestBehaviorFunctionSignatures(unittest.TestCase):
    """Test that behavior functions return correct EventResult."""

    def test_on_drink_returns_event_result_for_drinkable(self):
        """Test that on_drink returns EventResult for drinkable items."""
        from behaviors.core.consumables import on_drink

        # Create mock entity and state
        entity = Mock()
        entity.id = "health_potion"
        entity.properties = {"drinkable": True}
        entity.states = {}

        player_mock = Mock()
        player_mock.inventory = ["health_potion"]
        player_mock.stats = {"health": 50, "max_health": 100}

        state = Mock()
        state.actors = {"player": player_mock}

        context = {"location": "room1", "verb": "drink"}

        result = on_drink(entity, state, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)

    def test_on_drink_returns_none_for_non_drinkable(self):
        """Test that on_drink returns None for non-drinkable entities."""
        from behaviors.core.consumables import on_drink

        entity = Mock()
        entity.id = "rock"
        entity.properties = {}
        entity.states = {}

        state = Mock()
        context = {"location": "room1", "verb": "drink"}

        result = on_drink(entity, state, context)

        # Should return None to allow other handlers to process
        self.assertIsNone(result)

    def test_on_eat_returns_event_result_for_edible(self):
        """Test that on_eat returns EventResult for edible items."""
        from behaviors.core.consumables import on_eat

        entity = Mock()
        entity.id = "bread"
        entity.properties = {"edible": True}
        entity.states = {}

        player_mock = Mock()
        player_mock.inventory = ["bread"]
        player_mock.stats = {}

        state = Mock()
        state.actors = {"player": player_mock}

        context = {"location": "room1", "verb": "eat"}

        result = on_eat(entity, state, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)

    def test_on_eat_returns_none_for_non_edible(self):
        """Test that on_eat returns None for non-edible entities."""
        from behaviors.core.consumables import on_eat

        entity = Mock()
        entity.id = "rock"
        entity.properties = {}
        entity.states = {}

        state = Mock()
        context = {"location": "room1", "verb": "eat"}

        result = on_eat(entity, state, context)

        # Should return None to allow other handlers to process
        self.assertIsNone(result)

    def test_on_take_light_source_returns_event_result(self):
        """Test that on_take returns EventResult."""
        from behaviors.core.light_sources import on_take

        entity = Mock()
        entity.states = {}

        state = Mock()
        context = {"location": "room1", "verb": "take"}

        result = on_take(entity, state, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)

    def test_on_drop_light_source_returns_event_result(self):
        """Test that on_drop returns EventResult."""
        from behaviors.core.light_sources import on_drop

        entity = Mock()
        entity.states = {"lit": True}

        state = Mock()
        context = {"location": "room1", "verb": "drop"}

        result = on_drop(entity, state, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)

    def test_on_open_returns_event_result_for_treasure_chest(self):
        """Test that on_open returns EventResult for treasure chest."""
        from behaviors.core.containers import on_open

        entity = Mock()
        entity.id = "treasure_chest"
        entity.states = {}

        player_mock = Mock()
        player_mock.flags = {}

        state = Mock()
        state.actors = {"player": player_mock}

        context = {"location": "room2", "verb": "open"}

        result = on_open(entity, state, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)

    def test_on_open_returns_none_for_non_treasure_chest(self):
        """Test that on_open returns None for non-treasure-chest entities."""
        from behaviors.core.containers import on_open

        entity = Mock()
        entity.id = "other_chest"
        entity.states = {}

        player_mock = Mock()
        player_mock.flags = {}

        state = Mock()
        state.actors = {"player": player_mock}

        context = {"location": "room2", "verb": "open"}

        result = on_open(entity, state, context)

        # Should return None to allow other handlers to process
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
