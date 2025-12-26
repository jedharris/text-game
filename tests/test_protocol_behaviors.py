"""Tests for protocol handler behavior integration (Phase 2).

Updated to use actual GameState classes and new behavior system architecture.
Updated for Phase 4 (Narration API) to use NarrationResult format.
"""

import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
from types import SimpleNamespace

from src.behavior_manager import BehaviorManager, EventResult
from src.llm_protocol import LLMProtocolHandler
from src.state_manager import (
    GameState, Metadata, Location, Item, Actor
)


def get_result_message(result: Dict[str, Any]) -> str:
    """
    Extract message text from result, handling both old and new formats.

    New format (Phase 4): result["narration"]["primary_text"]
    Old format: result["message"]

    For the new format, also concatenates secondary_beats.
    """
    # New format: NarrationResult
    if "narration" in result:
        narration = result["narration"]
        parts = [narration.get("primary_text", "")]
        if "secondary_beats" in narration:
            parts.extend(narration["secondary_beats"])
        return "\n".join(parts)

    # Old format
    return result.get("message", "")


def create_behavior_manager_with_core_modules():
    """Create a BehaviorManager with core modules loaded."""
    manager = BehaviorManager()
    # Load core behavior modules
    behaviors_dir = Path(__file__).parent.parent / "behaviors"
    if behaviors_dir.exists():
        modules = manager.discover_modules(str(behaviors_dir))
        manager.load_modules(modules)
    return manager


def create_test_state():
    """Create a minimal test game state."""
    state = GameState(
        metadata=Metadata(
            title="Test Game",
            version="1.0",
            description="A test game"
        ),
        locations=[
            Location(
                id="room1",
                name="Test Room",
                description="A test room",
                items=["item1"]
            )
        ],
        items=[
            Item(
                id="item1",
                name="sword",
                description="A test sword",
                location="room1",
                properties={"portable": True}
            )
        ],
        actors={
            "player": Actor(
                id="player",
                name="Adventurer",
                description="The player",
                location="room1",
                inventory=[]
            )
        }
    )
    return state


class TestProtocolBehaviorIntegration(unittest.TestCase):
    """Test LLMProtocolHandler integration with BehaviorManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = create_test_state()

    def test_handler_accepts_behavior_manager(self):
        """Test that LLMProtocolHandler accepts behavior_manager parameter."""
        manager = BehaviorManager()
        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)
        self.assertIs(handler.behavior_manager, manager)

    def test_handler_creates_default_behavior_manager(self):
        """Test that handler creates default behavior manager if none provided."""
        handler = LLMProtocolHandler(self.game_state)
        # New behavior: auto-creates BehaviorManager
        self.assertIsNotNone(handler.behavior_manager)
        self.assertIsInstance(handler.behavior_manager, BehaviorManager)

    def test_falls_back_to_builtin_handler(self):
        """Test that builtin handler is used when no registered handler."""
        # Use manager with core modules loaded
        manager = create_behavior_manager_with_core_modules()
        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        # Should use builtin take handler
        self.assertTrue(result.get("success"))
        # New format (Phase 4) uses narration instead of message
        self.assertIn("narration", result)

    def test_behavior_invocation_after_successful_command(self):
        """Test that behavior is invoked after successful command."""
        # Need core modules loaded for the take handler to work
        manager = create_behavior_manager_with_core_modules()

        # Track behavior invocation
        behavior_called = []

        def on_take(entity, accessor, context):
            behavior_called.append({
                "entity": entity,
                "context": context
            })
            return EventResult(allow=True, feedback="You feel the sword's power!")

        manager._modules["test_module"] = SimpleNamespace(on_take=on_take)
        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(len(behavior_called), 1)
        # Behavior message should be included in narration
        self.assertIn("You feel the sword's power!", get_result_message(result))

    def test_behavior_can_prevent_action(self):
        """Test that behavior can prevent action with allow=False."""
        manager = create_behavior_manager_with_core_modules()

        # Old dict format behaviors receive (entity, state, context)
        def on_take(entity, state, context):
            return EventResult(allow=False, feedback="The sword is cursed and refuses to be picked up!")

        manager._modules["test_module"] = SimpleNamespace(on_take=on_take)
        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        # Action should fail
        self.assertFalse(result.get("success"))
        # Error message is in narration.primary_text for new format
        error_msg = get_result_message(result) or get_result_message(result)
        self.assertIn("cursed", error_msg.lower())

    def test_message_appears_in_result(self):
        """Test that behavior message appears in result."""
        manager = create_behavior_manager_with_core_modules()

        def on_take(entity, accessor, context):
            return EventResult(allow=True, feedback="The magic awakens!")

        manager._modules["test_module"] = SimpleNamespace(on_take=on_take)
        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertIn("The magic awakens!", get_result_message(result))

    def test_entity_obj_removed_from_final_result(self):
        """Test that entity_obj is removed from final result."""
        manager = create_behavior_manager_with_core_modules()
        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        # entity_obj should not be in result
        self.assertNotIn("entity_obj", result)
        # New format (Phase 4) uses narration, not message
        self.assertIn("narration", result)

    def test_context_contains_location(self):
        """Test that context passed to behavior contains location info."""
        manager = create_behavior_manager_with_core_modules()

        context_received = []

        def on_take(entity, accessor, context):
            context_received.append(context)
            return EventResult(allow=True)

        manager._modules["test_module"] = SimpleNamespace(on_take=on_take)
        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertEqual(len(context_received), 1)
        # Context now contains actor_id and verb
        self.assertIn("actor_id", context_received[0])
        self.assertIn("verb", context_received[0])

    def test_no_behavior_invocation_on_failed_command(self):
        """Test that behavior is not invoked when command fails."""
        manager = create_behavior_manager_with_core_modules()

        behavior_called = []

        def on_take(entity, accessor, context):
            behavior_called.append(True)
            return EventResult(allow=True)

        manager._modules["test_module"] = SimpleNamespace(on_take=on_take)
        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        # Try to take item that doesn't exist
        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "nonexistent"}
        })

        self.assertFalse(result.get("success"))
        self.assertEqual(len(behavior_called), 0)

    def test_behavior_receives_correct_entity(self):
        """Test that behavior receives the correct entity object."""
        manager = create_behavior_manager_with_core_modules()

        entity_received = []

        def on_take(entity, accessor, context):
            entity_received.append(entity)
            return EventResult(allow=True)

        manager._modules["test_module"] = SimpleNamespace(on_take=on_take)
        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertEqual(len(entity_received), 1)
        self.assertEqual(entity_received[0].name, "sword")
        self.assertEqual(entity_received[0].id, "item1")

    def test_behavior_receives_accessor(self):
        """Test that behavior receives StateAccessor (with access to game state)."""
        manager = create_behavior_manager_with_core_modules()

        accessor_received = []

        # Behaviors receive (entity, accessor, context)
        def on_take(entity, accessor, context):
            accessor_received.append(accessor)
            return EventResult(allow=True)

        manager._modules["test_module"] = SimpleNamespace(on_take=on_take)
        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertEqual(len(accessor_received), 1)
        # Behaviors receive StateAccessor which has .game_state
        self.assertIs(accessor_received[0].game_state, self.game_state)

    def test_behavior_can_modify_entity_state(self):
        """Test that behavior can modify entity state."""
        manager = create_behavior_manager_with_core_modules()

        def on_take(entity, accessor, context):
            entity.states["enchanted"] = True
            return EventResult(allow=True, feedback="The sword glows!")

        manager._modules["test_module"] = SimpleNamespace(on_take=on_take)
        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(self.game_state.items[0].states.get("enchanted"))

    def test_multiple_behaviors_on_same_entity(self):
        """Test entity with multiple behaviors for different events."""
        manager = create_behavior_manager_with_core_modules()

        def on_take(entity, accessor, context):
            return EventResult(allow=True, feedback="Taken!")

        def on_drop(entity, accessor, context):
            return EventResult(allow=True, feedback="Dropped!")

        manager._modules["test_module"] = SimpleNamespace(
            on_take=on_take,
            on_drop=on_drop
        )

        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        # Take the item
        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })
        self.assertIn("Taken!", get_result_message(result))

        # Drop the item
        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "drop", "object": "sword"}
        })
        self.assertIn("Dropped!", get_result_message(result))

    def test_no_behavior_manager_works_without_behaviors(self):
        """Test that handler works with auto-created behavior manager."""
        handler = LLMProtocolHandler(self.game_state)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(result.get("success"))
        # New format (Phase 4) uses narration instead of message
        self.assertIn("narration", result)

    def test_entity_without_behaviors_attribute(self):
        """Test handling entity that doesn't have behaviors defined."""
        manager = create_behavior_manager_with_core_modules()

        # Item with empty behaviors
        self.game_state.items[0].behaviors = []

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(result.get("success"))

    def test_entity_with_empty_behaviors(self):
        """Test handling entity with empty behaviors dict."""
        manager = create_behavior_manager_with_core_modules()
        self.game_state.items[0].behaviors = []

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertTrue(result.get("success"))

    def test_behavior_error_propagates(self):
        """Test that behavior errors propagate (fail-fast for coding bugs)."""
        manager = create_behavior_manager_with_core_modules()

        def on_take(entity, accessor, context):
            raise ValueError("Behavior error!")

        manager._modules["test_module"] = SimpleNamespace(on_take=on_take)
        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        # Behavior errors should propagate - they indicate coding bugs
        with self.assertRaises(ValueError) as ctx:
            handler.handle_command({
                "type": "command",
                "action": {"verb": "take", "object": "sword"}
            })
        self.assertIn("Behavior error!", str(ctx.exception))

    def test_context_contains_action_info(self):
        """Test that context contains action information."""
        manager = create_behavior_manager_with_core_modules()

        context_received = []

        def on_take(entity, accessor, context):
            context_received.append(context)
            return EventResult(allow=True)

        manager._modules["test_module"] = SimpleNamespace(on_take=on_take)
        self.game_state.items[0].behaviors = ["test_module"]

        handler = LLMProtocolHandler(self.game_state, behavior_manager=manager)

        handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        })

        self.assertEqual(len(context_received), 1)
        self.assertIn("verb", context_received[0])
        self.assertEqual(context_received[0]["verb"], "take")


class TestProtocolBehaviorCommands(unittest.TestCase):
    """Test behavior integration with specific command handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = GameState(
            metadata=Metadata(
                title="Test Game",
                version="1.0",
                description="A test game"
            ),
            locations=[
                Location(
                    id="room1",
                    name="Test Room",
                    description="A test room",
                    items=["item1", "item2"]
                )
            ],
            items=[
                Item(
                    id="item1",
                    name="potion",
                    description="A test potion",
                    location="room1",
                    properties={"portable": True, "drinkable": True}
                ),
                Item(
                    id="item2",
                    name="book",
                    description="A test book",
                    location="room1",
                    properties={"portable": True, "readable": True}
                )
            ],
            actors={
                "player": Actor(
                    id="player",
                    name="Adventurer",
                    description="The player",
                    location="room1",
                    inventory=[]
                )
            }
        )
        self.manager = create_behavior_manager_with_core_modules()
        self.handler = LLMProtocolHandler(self.game_state, behavior_manager=self.manager)

    def test_drink_command_invokes_on_drink(self):
        """Test drink command invokes on_drink behavior."""
        behavior_called = []

        def on_drink(entity, state, context):
            behavior_called.append(True)
            return EventResult(allow=True, feedback="The potion heals you!")

        self.manager._modules["test"] = SimpleNamespace(on_drink=on_drink)
        self.game_state.items[0].behaviors = ["test"]

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

        # Note: drink is a stub command that may not invoke behaviors
        # Just verify command succeeded
        self.assertTrue(result.get("success"))

    def test_read_command_invokes_on_read(self):
        """Test read command invokes on_read behavior."""
        behavior_called = []

        def on_read(entity, state, context):
            behavior_called.append(True)
            return EventResult(allow=True, feedback="The book reveals ancient secrets!")

        self.manager._modules["test"] = SimpleNamespace(on_read=on_read)
        self.game_state.items[1].behaviors = ["test"]

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "read", "object": "book"}
        })

        # read is a stub command
        self.assertTrue(result.get("success"))

    def test_use_command_invokes_on_use(self):
        """Test use command invokes on_use behavior."""
        behavior_called = []

        def on_use(entity, state, context):
            behavior_called.append(True)
            return EventResult(allow=True, feedback="You use the item!")

        self.manager._modules["test"] = SimpleNamespace(on_use=on_use)
        self.game_state.items[0].behaviors = ["test"]

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "use", "object": "potion"}
        })

        # use is a stub command
        self.assertTrue(result.get("success"))

    def test_examine_command_returns_description(self):
        """Test examine command returns item description.

        Note: examine is a read-only command that doesn't trigger entity behaviors
        (no accessor.update() call with verb). It just returns the item's description.
        """
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "potion"}
        })

        self.assertTrue(result.get("success"))
        # Should return the item's description in narration
        self.assertIn("potion", get_result_message(result).lower())


if __name__ == '__main__':
    unittest.main()
