"""
Phase 9: Entity Behaviors - Infrastructure

Tests for behavior invocation in update() method.
"""

import unittest
import sys
from pathlib import Path
from types import ModuleType

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_accessor import StateAccessor, EventResult, UpdateResult
from src.behavior_manager import BehaviorManager
from src.state_manager import Item
from tests.conftest import create_test_state


class TestPhase9EntityBehaviors(unittest.TestCase):
    """Tests for entity behavior invocation infrastructure."""

    def test_entity_behavior_single(self):
        """Test invoking single entity behavior."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # Create behavior module with on_take
        behavior_module = ModuleType("test_behavior")
        def on_take(entity, accessor, context):
            return EventResult(allow=False, feedback="Can't take this!")
        behavior_module.on_take = on_take

        behavior_manager.load_module(behavior_module)
        behavior_manager._modules["test_behavior"] = behavior_module

        accessor = StateAccessor(state, behavior_manager)

        # Create item with behavior
        item = Item(
            id="test_item",
            name="test item",
            description="A test item",
            location="location_room",
            properties={"portable": True},
            behaviors=["test_behavior"]
        )
        state.items.append(item)

        # Invoke behavior
        context = {"actor_id": "player", "changes": {}, "verb": "take"}
        result = behavior_manager.invoke_behavior(item, "on_take", accessor, context)

        self.assertIsNotNone(result)
        self.assertFalse(result.allow)
        self.assertIn("Can't take", result.feedback)

    def test_entity_behavior_multiple(self):
        """Test that multiple behaviors are all invoked."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # First behavior
        behavior1 = ModuleType("behavior1")
        def on_take_1(entity, accessor, context):
            return EventResult(allow=True, feedback="Message from behavior1")
        behavior1.on_take = on_take_1

        # Second behavior
        behavior2 = ModuleType("behavior2")
        def on_take_2(entity, accessor, context):
            return EventResult(allow=True, feedback="Message from behavior2")
        behavior2.on_take = on_take_2

        behavior_manager.load_module(behavior1)
        behavior_manager.load_module(behavior2)
        behavior_manager._modules["behavior1"] = behavior1
        behavior_manager._modules["behavior2"] = behavior2

        accessor = StateAccessor(state, behavior_manager)

        # Item with both behaviors
        item = Item(
            id="test_item",
            name="test item",
            description="A test item",
            location="location_room",
            properties={"portable": True},
            behaviors=["behavior1", "behavior2"]
        )
        state.items.append(item)

        context = {"actor_id": "player", "changes": {}, "verb": "take"}
        result = behavior_manager.invoke_behavior(item, "on_take", accessor, context)

        self.assertIsNotNone(result)
        self.assertTrue(result.allow)
        # Both messages should be present
        self.assertIn("behavior1", result.feedback)
        self.assertIn("behavior2", result.feedback)

    def test_entity_behavior_any_deny_wins(self):
        """Test that if any behavior denies, action is denied."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # First behavior allows
        behavior1 = ModuleType("behavior1")
        def on_take_1(entity, accessor, context):
            return EventResult(allow=True, feedback="OK from behavior1")
        behavior1.on_take = on_take_1

        # Second behavior denies
        behavior2 = ModuleType("behavior2")
        def on_take_2(entity, accessor, context):
            return EventResult(allow=False, feedback="Denied by behavior2")
        behavior2.on_take = on_take_2

        behavior_manager.load_module(behavior1)
        behavior_manager.load_module(behavior2)
        behavior_manager._modules["behavior1"] = behavior1
        behavior_manager._modules["behavior2"] = behavior2

        accessor = StateAccessor(state, behavior_manager)

        item = Item(
            id="test_item",
            name="test item",
            description="A test item",
            location="location_room",
            properties={"portable": True},
            behaviors=["behavior1", "behavior2"]
        )
        state.items.append(item)

        context = {"actor_id": "player", "changes": {}, "verb": "take"}
        result = behavior_manager.invoke_behavior(item, "on_take", accessor, context)

        self.assertIsNotNone(result)
        self.assertFalse(result.allow)  # Denied

    def test_update_invokes_behavior(self):
        """Test that update() invokes entity behaviors."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # Create vocabulary mapping take -> on_take
        vocab_module = ModuleType("vocab_module")
        vocab_module.vocabulary = {
            "verbs": [{"word": "take", "event": "on_take"}]
        }
        behavior_manager.load_module(vocab_module)

        # Create behavior that denies
        behavior_module = ModuleType("test_behavior")
        def on_take(entity, accessor, context):
            return EventResult(allow=False, feedback="Behavior denies!")
        behavior_module.on_take = on_take

        behavior_manager.load_module(behavior_module)
        behavior_manager._modules["test_behavior"] = behavior_module

        accessor = StateAccessor(state, behavior_manager)

        # Item with behavior
        item = Item(
            id="test_item",
            name="test item",
            description="A test item",
            location="location_room",
            properties={"portable": True},
            behaviors=["test_behavior"]
        )
        state.items.append(item)

        # Try to update with verb that triggers behavior
        result = accessor.update(
            entity=item,
            changes={"location": "player"},
            verb="take",
            actor_id="player"
        )

        # Should be denied by behavior
        self.assertFalse(result.success)
        self.assertIn("Behavior denies", result.detail)

    def test_entity_no_behaviors_allows(self):
        """Test that entity with no behaviors allows changes."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Item with no behaviors
        item = Item(
            id="test_item",
            name="test item",
            description="A test item",
            location="location_room",
            properties={"portable": True},
            behaviors=[]
        )
        state.items.append(item)

        # Should succeed (no behaviors to block)
        result = accessor.update(
            entity=item,
            changes={"location": "player"},
            verb="take",
            actor_id="player"
        )

        self.assertTrue(result.success)

    def test_invoke_behavior_no_behaviors(self):
        """Test that invoke_behavior returns None when entity has no behaviors."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Item with empty behaviors list
        item = Item(
            id="test_item",
            name="test item",
            description="A test item",
            location="location_room",
            properties={"portable": True},
            behaviors=[]
        )
        state.items.append(item)

        context = {"actor_id": "player", "changes": {}, "verb": "take"}
        result = behavior_manager.invoke_behavior(item, "on_take", accessor, context)

        self.assertIsNone(result)

    def test_invoke_behavior_no_matching_event(self):
        """Test that invoke_behavior returns None when no behaviors define the event."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # Create behavior module without on_take
        behavior_module = ModuleType("test_behavior")
        def on_drop(entity, accessor, context):
            return EventResult(allow=True, feedback="Can drop")
        behavior_module.on_drop = on_drop

        behavior_manager.load_module(behavior_module)
        behavior_manager._modules["test_behavior"] = behavior_module

        accessor = StateAccessor(state, behavior_manager)

        # Item with behavior that doesn't define on_take
        item = Item(
            id="test_item",
            name="test item",
            description="A test item",
            location="location_room",
            properties={"portable": True},
            behaviors=["test_behavior"]
        )
        state.items.append(item)

        # Try to invoke on_take (not defined in behavior)
        context = {"actor_id": "player", "changes": {}, "verb": "take"}
        result = behavior_manager.invoke_behavior(item, "on_take", accessor, context)

        self.assertIsNone(result)

    def test_update_without_verb_skips_behavior(self):
        """Test that update() without a verb doesn't invoke behaviors."""
        state = create_test_state()
        behavior_manager = BehaviorManager()

        # Create behavior that would deny
        behavior_module = ModuleType("test_behavior")
        def on_take(entity, accessor, context):
            return EventResult(allow=False, feedback="Should not be called!")
        behavior_module.on_take = on_take

        behavior_manager.load_module(behavior_module)
        behavior_manager._modules["test_behavior"] = behavior_module

        accessor = StateAccessor(state, behavior_manager)

        # Item with behavior
        item = Item(
            id="test_item",
            name="test item",
            description="A test item",
            location="location_room",
            properties={"portable": True},
            behaviors=["test_behavior"]
        )
        state.items.append(item)

        # Update without verb - should not invoke behavior
        result = accessor.update(
            entity=item,
            changes={"location": "player"},
            verb=None,
            actor_id="player"
        )

        # Should succeed (behavior not invoked)
        self.assertTrue(result.success)


if __name__ == '__main__':
    unittest.main()
