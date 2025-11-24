"""Tests for protocol handler behavior integration (Phase 2)."""

import unittest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.behavior_manager import BehaviorManager, EventResult, get_behavior_manager
from src.json_protocol import JSONProtocolHandler


# Minimal test fixtures
@dataclass
class TestItem:
    id: str
    name: str
    description: str = ""
    location: str = "room1"
    portable: bool = True
    provides_light: bool = False
    states: Dict = field(default_factory=dict)
    behaviors: Dict = field(default_factory=dict)
    properties: Dict = field(default_factory=dict)

    def __post_init__(self):
        # Sync properties with attributes for compatibility
        if "portable" not in self.properties:
            self.properties["portable"] = self.portable
        if "provides_light" not in self.properties:
            self.properties["provides_light"] = self.provides_light
        if "states" not in self.properties:
            self.properties["states"] = self.states


@dataclass
class TestLocation:
    id: str
    name: str
    description: str = ""
    items: List[str] = field(default_factory=list)
    exits: Dict = field(default_factory=dict)
    llm_context: str = ""
    properties: Dict = field(default_factory=dict)


@dataclass
class TestPlayer:
    location: str = "room1"
    inventory: List[str] = field(default_factory=list)
    flags: Dict = field(default_factory=dict)


@dataclass
class TestMetadata:
    title: str = "Test Game"
    author: str = "Test"
    version: str = "1.0"
    description: str = ""


@dataclass
class TestVocabulary:
    aliases: Dict = field(default_factory=dict)
    verbs: List = field(default_factory=list)
    nouns: List = field(default_factory=list)
    adjectives: List = field(default_factory=list)


@dataclass
class TestGameState:
    player: TestPlayer = field(default_factory=TestPlayer)
    locations: List[TestLocation] = field(default_factory=list)
    items: List[TestItem] = field(default_factory=list)
    doors: List = field(default_factory=list)
    npcs: List = field(default_factory=list)
    locks: List = field(default_factory=list)
    metadata: TestMetadata = field(default_factory=TestMetadata)
    vocabulary: TestVocabulary = field(default_factory=TestVocabulary)


class TestProtocolBehaviorIntegration(unittest.TestCase):
    """Test JSONProtocolHandler integration with BehaviorManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = TestGameState()
        self.state.locations = [
            TestLocation(id="room1", name="Test Room", items=["item1"])
        ]
        self.state.items = [
            TestItem(id="item1", name="sword", location="room1")
        ]

    def test_handler_accepts_behavior_manager(self):
        """Test that JSONProtocolHandler accepts behavior_manager parameter."""
        manager = BehaviorManager()
        handler = JSONProtocolHandler(self.state, behavior_manager=manager)
        self.assertIs(handler.behavior_manager, manager)

    def test_handler_creates_default_behavior_manager(self):
        """Test that handler creates default behavior manager if none provided."""
        handler = JSONProtocolHandler(self.state)
        self.assertIsNone(handler.behavior_manager)

    def test_registered_handler_takes_precedence(self):
        """Test that registered handler takes precedence over builtin."""
        manager = BehaviorManager()

        # Register a custom handler for 'take'
        def custom_take(state, action, context):
            return {
                "type": "result",
                "success": True,
                "action": "take",
                "message": "Custom take handler"
            }

        manager._handlers["take"] = custom_take
        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("message"), "Custom take handler")

    def test_falls_back_to_builtin_handler(self):
        """Test that builtin handler is used when no registered handler."""
        manager = BehaviorManager()
        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        # Should use builtin take handler
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "take")

    def test_behavior_invocation_after_successful_command(self):
        """Test that behavior is invoked after successful command."""
        manager = BehaviorManager()

        # Track behavior invocation
        behavior_called = []

        def on_take_behavior(entity, state, context):
            behavior_called.append({
                "entity": entity,
                "context": context
            })
            return EventResult(allow=True, message="You feel the sword's power!")

        # Cache the behavior
        manager._behavior_cache["test_module:on_take"] = on_take_behavior

        # Add behavior to item
        self.state.items[0].behaviors = {"on_take": "test_module:on_take"}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(len(behavior_called), 1)
        self.assertEqual(result.get("message"), "You feel the sword's power!")

    def test_behavior_can_prevent_action(self):
        """Test that behavior can prevent action with allow=False."""
        manager = BehaviorManager()

        def on_take_behavior(entity, state, context):
            return EventResult(allow=False, message="The sword is cursed and refuses to be picked up!")

        manager._behavior_cache["test_module:on_take"] = on_take_behavior
        self.state.items[0].behaviors = {"on_take": "test_module:on_take"}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        # Action should be reverted
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("message"), "The sword is cursed and refuses to be picked up!")

    def test_message_appears_in_result(self):
        """Test that behavior message appears in result."""
        manager = BehaviorManager()

        def on_take_behavior(entity, state, context):
            return EventResult(allow=True, message="The magic awakens!")

        manager._behavior_cache["test_module:on_take"] = on_take_behavior
        self.state.items[0].behaviors = {"on_take": "test_module:on_take"}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertEqual(result.get("message"), "The magic awakens!")

    def test_entity_obj_removed_from_final_result(self):
        """Test that entity_obj is removed from final result."""
        manager = BehaviorManager()
        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertNotIn("entity_obj", result)
        self.assertIn("entity", result)  # entity dict should still be there

    def test_context_contains_location(self):
        """Test that context passed to behavior contains location."""
        manager = BehaviorManager()

        context_received = []

        def on_take_behavior(entity, state, context):
            context_received.append(context)
            return EventResult(allow=True)

        manager._behavior_cache["test_module:on_take"] = on_take_behavior
        self.state.items[0].behaviors = {"on_take": "test_module:on_take"}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertEqual(len(context_received), 1)
        self.assertEqual(context_received[0].get("location"), "room1")

    def test_no_behavior_invocation_on_failed_command(self):
        """Test that behavior is not invoked when command fails."""
        manager = BehaviorManager()

        behavior_called = []

        def on_take_behavior(entity, state, context):
            behavior_called.append(True)
            return EventResult(allow=True)

        manager._behavior_cache["test_module:on_take"] = on_take_behavior
        self.state.items[0].behaviors = {"on_take": "test_module:on_take"}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        # Try to take item that doesn't exist
        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "nonexistent"}
        })

        self.assertFalse(result.get("success"))
        self.assertEqual(len(behavior_called), 0)

    def test_behavior_receives_correct_entity(self):
        """Test that behavior receives the correct entity object."""
        manager = BehaviorManager()

        entity_received = []

        def on_take_behavior(entity, state, context):
            entity_received.append(entity)
            return EventResult(allow=True)

        manager._behavior_cache["test_module:on_take"] = on_take_behavior
        self.state.items[0].behaviors = {"on_take": "test_module:on_take"}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertEqual(len(entity_received), 1)
        self.assertEqual(entity_received[0].name, "sword")
        self.assertEqual(entity_received[0].id, "item1")

    def test_behavior_receives_game_state(self):
        """Test that behavior receives the game state."""
        manager = BehaviorManager()

        state_received = []

        def on_take_behavior(entity, state, context):
            state_received.append(state)
            return EventResult(allow=True)

        manager._behavior_cache["test_module:on_take"] = on_take_behavior
        self.state.items[0].behaviors = {"on_take": "test_module:on_take"}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertEqual(len(state_received), 1)
        self.assertIs(state_received[0], self.state)

    def test_behavior_can_modify_entity_state(self):
        """Test that behavior can modify entity state."""
        manager = BehaviorManager()

        def on_take_behavior(entity, state, context):
            entity.states["enchanted"] = True
            return EventResult(allow=True, message="The sword glows!")

        manager._behavior_cache["test_module:on_take"] = on_take_behavior
        self.state.items[0].behaviors = {"on_take": "test_module:on_take"}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(self.state.items[0].states.get("enchanted"))

    def test_multiple_behaviors_on_same_entity(self):
        """Test entity with multiple behaviors for different events."""
        manager = BehaviorManager()

        def on_take_behavior(entity, state, context):
            return EventResult(allow=True, message="Taken!")

        def on_drop_behavior(entity, state, context):
            return EventResult(allow=True, message="Dropped!")

        manager._behavior_cache["test_module:on_take"] = on_take_behavior
        manager._behavior_cache["test_module:on_drop"] = on_drop_behavior

        self.state.items[0].behaviors = {
            "on_take": "test_module:on_take",
            "on_drop": "test_module:on_drop"
        }

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        # Take the item
        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })
        self.assertEqual(result.get("message"), "Taken!")

        # Drop the item
        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "drop", "object": "sword"}
        })
        self.assertEqual(result.get("message"), "Dropped!")

    def test_no_behavior_manager_works_without_behaviors(self):
        """Test that handler works without behavior manager."""
        handler = JSONProtocolHandler(self.state)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "take")

    def test_entity_without_behaviors_attribute(self):
        """Test handling entity that doesn't have behaviors attribute."""
        manager = BehaviorManager()

        # Remove behaviors attribute
        delattr(self.state.items[0], 'behaviors')

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(result.get("success"))

    def test_entity_with_empty_behaviors(self):
        """Test handling entity with empty behaviors dict."""
        manager = BehaviorManager()
        self.state.items[0].behaviors = {}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(result.get("success"))

    def test_behavior_error_does_not_break_command(self):
        """Test that behavior error doesn't break command execution."""
        manager = BehaviorManager()

        def on_take_behavior(entity, state, context):
            raise ValueError("Behavior error!")

        manager._behavior_cache["test_module:on_take"] = on_take_behavior
        self.state.items[0].behaviors = {"on_take": "test_module:on_take"}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        # Command should still succeed even if behavior errors
        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        # The command succeeded, but behavior failed
        self.assertTrue(result.get("success"))

    def test_context_contains_action_info(self):
        """Test that context contains action information."""
        manager = BehaviorManager()

        context_received = []

        def on_take_behavior(entity, state, context):
            context_received.append(context)
            return EventResult(allow=True)

        manager._behavior_cache["test_module:on_take"] = on_take_behavior
        self.state.items[0].behaviors = {"on_take": "test_module:on_take"}

        handler = JSONProtocolHandler(self.state, behavior_manager=manager)

        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertIn("verb", context_received[0])
        self.assertEqual(context_received[0]["verb"], "take")


class TestProtocolBehaviorCommands(unittest.TestCase):
    """Test behavior integration with specific command handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = TestGameState()
        self.state.locations = [
            TestLocation(id="room1", name="Test Room", items=["item1", "item2"])
        ]
        self.state.items = [
            TestItem(id="item1", name="potion", location="room1", behaviors={}),
            TestItem(id="item2", name="book", location="room1", behaviors={})
        ]
        self.manager = BehaviorManager()
        self.handler = JSONProtocolHandler(self.state, behavior_manager=self.manager)

    def test_drink_command_invokes_on_drink(self):
        """Test drink command invokes on_drink behavior."""
        behavior_called = []

        def on_drink(entity, state, context):
            behavior_called.append(True)
            # Consume the potion
            state.player.inventory.remove(entity.id)
            return EventResult(allow=True, message="The potion heals you!")

        self.manager._behavior_cache["test:on_drink"] = on_drink
        self.state.items[0].behaviors = {"on_drink": "test:on_drink"}

        # First take the potion
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "potion"}
        })

        # Then drink it
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "drink", "object": "potion"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(len(behavior_called), 1)
        self.assertEqual(result.get("message"), "The potion heals you!")

    def test_read_command_invokes_on_read(self):
        """Test read command invokes on_read behavior."""
        behavior_called = []

        def on_read(entity, state, context):
            behavior_called.append(True)
            return EventResult(allow=True, message="The book reveals ancient secrets!")

        self.manager._behavior_cache["test:on_read"] = on_read
        self.state.items[1].behaviors = {"on_read": "test:on_read"}

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "read", "object": "book"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(len(behavior_called), 1)

    def test_use_command_invokes_on_use(self):
        """Test use command invokes on_use behavior."""
        behavior_called = []

        def on_use(entity, state, context):
            behavior_called.append(True)
            return EventResult(allow=True, message="You use the item!")

        self.manager._behavior_cache["test:on_use"] = on_use
        self.state.items[0].behaviors = {"on_use": "test:on_use"}

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "use", "object": "potion"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(len(behavior_called), 1)

    def test_examine_command_invokes_on_examine(self):
        """Test examine command invokes on_examine behavior."""
        behavior_called = []

        def on_examine(entity, state, context):
            behavior_called.append(True)
            return EventResult(allow=True, message="You notice something special!")

        self.manager._behavior_cache["test:on_examine"] = on_examine
        self.state.items[0].behaviors = {"on_examine": "test:on_examine"}

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "potion"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(len(behavior_called), 1)


if __name__ == '__main__':
    unittest.main()
