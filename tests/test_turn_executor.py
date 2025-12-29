"""Tests for turn_executor module - bidirectional topological sort and execution."""

import unittest
from dataclasses import dataclass
from typing import List

from src.turn_executor import initialize, execute_turn_phases, _topological_sort
from src.behavior_manager import HookDefinition
from src.types import TurnHookId
from src.state_manager import GameState, Actor, Location, Item
from unittest.mock import Mock, MagicMock


class TestTopologicalSort(unittest.TestCase):
    """Test topological sort with bidirectional dependencies."""

    def test_empty_phases(self):
        """Empty phase list returns empty order."""
        result = _topological_sort({})
        self.assertEqual(result, [])

    def test_single_phase_no_dependencies(self):
        """Single phase with no dependencies."""
        from src.types import TurnHookId
        phases = {
            "turn_test": HookDefinition(
                hook_id=TurnHookId("turn_test"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="Test",
                defined_by="test"
            )
        }
        result = _topological_sort(phases)
        self.assertEqual(result, ["turn_test"])

    def test_linear_after_dependencies(self):
        """Linear chain using 'after' constraints: A → B → C."""
        phases = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="A",
                defined_by="test"
            ),
            "turn_b": HookDefinition(
                hook_id=TurnHookId("turn_b"),
                invocation="turn_phase",
                after=[TurnHookId("turn_a")],
                before=[],
                description="B",
                defined_by="test"
            ),
            "turn_c": HookDefinition(
                hook_id=TurnHookId("turn_c"),
                invocation="turn_phase",
                after=[TurnHookId("turn_b")],
                before=[],
                description="C",
                defined_by="test"
            ),
        }
        result = _topological_sort(phases)
        self.assertEqual(result, ["turn_a", "turn_b", "turn_c"])

    def test_linear_before_dependencies(self):
        """Linear chain using 'before' constraints: A → B → C."""
        phases = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_b")],
                description="A",
                defined_by="test"
            ),
            "turn_b": HookDefinition(
                hook_id=TurnHookId("turn_b"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_c")],
                description="B",
                defined_by="test"
            ),
            "turn_c": HookDefinition(
                hook_id=TurnHookId("turn_c"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="C",
                defined_by="test"
            ),
        }
        result = _topological_sort(phases)
        self.assertEqual(result, ["turn_a", "turn_b", "turn_c"])

    def test_mixed_after_and_before(self):
        """Mixed 'after' and 'before' constraints create same ordering."""
        phases = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_b")],  # A before B
                description="A",
                defined_by="test"
            ),
            "turn_b": HookDefinition(
                hook_id=TurnHookId("turn_b"),
                invocation="turn_phase",
                after=[],  # No after constraint
                before=[],
                description="B",
                defined_by="test"
            ),
            "turn_c": HookDefinition(
                hook_id=TurnHookId("turn_c"),
                invocation="turn_phase",
                after=[TurnHookId("turn_b")],  # C after B
                before=[],
                description="C",
                defined_by="test"
            ),
        }
        result = _topological_sort(phases)
        self.assertEqual(result, ["turn_a", "turn_b", "turn_c"])

    def test_diamond_dependency(self):
        """Diamond dependency: A → B, A → C, B → D, C → D."""
        phases = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_b"), TurnHookId("turn_c")],
                description="A",
                defined_by="test"
            ),
            "turn_b": HookDefinition(
                hook_id=TurnHookId("turn_b"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_d")],
                description="B",
                defined_by="test"
            ),
            "turn_c": HookDefinition(
                hook_id=TurnHookId("turn_c"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_d")],
                description="C",
                defined_by="test"
            ),
            "turn_d": HookDefinition(
                hook_id=TurnHookId("turn_d"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="D",
                defined_by="test"
            ),
        }
        result = _topological_sort(phases)
        # A must be first, D must be last, B and C can be in either order
        self.assertEqual(result[0], "turn_a")
        self.assertEqual(result[3], "turn_d")
        self.assertIn("turn_b", result)
        self.assertIn("turn_c", result)

    def test_game_before_library_pattern(self):
        """Game infrastructure can insert before library using 'before'."""
        phases = {
            # Game infrastructure
            "turn_condition_spread": HookDefinition(
                hook_id=TurnHookId("turn_condition_spread"),
                invocation="turn_phase",
                after=[TurnHookId("turn_gossip_spread")],
                before=[TurnHookId("turn_npc_action")],  # Game runs before library
                description="Spread conditions",
                defined_by="game.spreads"
            ),
            "turn_gossip_spread": HookDefinition(
                hook_id=TurnHookId("turn_gossip_spread"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="Gossip",
                defined_by="game.gossip"
            ),
            # Library infrastructure
            "turn_npc_action": HookDefinition(
                hook_id=TurnHookId("turn_npc_action"),
                invocation="turn_phase",
                after=[],  # No modifications to library code!
                before=[],
                description="NPC actions",
                defined_by="actor_lib.npc_actions"
            ),
            "turn_environmental_effect": HookDefinition(
                hook_id=TurnHookId("turn_environmental_effect"),
                invocation="turn_phase",
                after=[TurnHookId("turn_npc_action")],
                before=[],
                description="Environmental",
                defined_by="actor_lib.environment"
            ),
        }
        result = _topological_sort(phases)

        # Order should be: gossip → condition_spread → npc_action → environmental
        self.assertEqual(result[0], "turn_gossip_spread")
        self.assertEqual(result[1], "turn_condition_spread")
        self.assertEqual(result[2], "turn_npc_action")
        self.assertEqual(result[3], "turn_environmental_effect")

    def test_circular_dependency_simple(self):
        """Circular dependency detected: A → B → A."""
        phases = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_b")],
                description="A",
                defined_by="test.a"
            ),
            "turn_b": HookDefinition(
                hook_id=TurnHookId("turn_b"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_a")],  # Creates cycle
                description="B",
                defined_by="test.b"
            ),
        }
        with self.assertRaises(ValueError) as cm:
            _topological_sort(phases)

        error_msg = str(cm.exception)
        self.assertIn("Circular dependency", error_msg)
        self.assertIn("turn_a", error_msg)
        self.assertIn("turn_b", error_msg)

    def test_circular_dependency_complex(self):
        """Circular dependency detected: A → B → C → A."""
        phases = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_b")],
                description="A",
                defined_by="test.a"
            ),
            "turn_b": HookDefinition(
                hook_id=TurnHookId("turn_b"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_c")],
                description="B",
                defined_by="test.b"
            ),
            "turn_c": HookDefinition(
                hook_id=TurnHookId("turn_c"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_a")],  # Creates cycle
                description="C",
                defined_by="test.c"
            ),
        }
        with self.assertRaises(ValueError) as cm:
            _topological_sort(phases)

        error_msg = str(cm.exception)
        self.assertIn("Circular dependency", error_msg)
        self.assertIn("authoring error", error_msg.lower())

    def test_undefined_after_dependency(self):
        """Error when 'after' references undefined hook."""
        phases = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[TurnHookId("turn_nonexistent")],  # Undefined!
                before=[],
                description="A",
                defined_by="test.a"
            ),
        }
        with self.assertRaises(ValueError) as cm:
            _topological_sort(phases)

        error_msg = str(cm.exception)
        self.assertIn("turn_nonexistent", error_msg)
        self.assertIn("not a defined turn phase", error_msg)
        self.assertIn("test.a", error_msg)  # Shows where error is

    def test_undefined_before_dependency(self):
        """Error when 'before' references undefined hook."""
        phases = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_nonexistent")],  # Undefined!
                description="A",
                defined_by="test.a"
            ),
        }
        with self.assertRaises(ValueError) as cm:
            _topological_sort(phases)

        error_msg = str(cm.exception)
        self.assertIn("turn_nonexistent", error_msg)
        self.assertIn("not a defined turn phase", error_msg)


class TestInitialize(unittest.TestCase):
    """Test initialize function filters and caches turn phases."""

    def test_filters_to_turn_phases_only(self):
        """Only turn_phase hooks are included in sort."""
        hook_defs = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="A",
                defined_by="test"
            ),
            "entity_test": HookDefinition(
                hook_id=TurnHookId("entity_test"),
                invocation="entity",  # Not a turn phase
                after=[],
                before=[],
                description="Entity",
                defined_by="test"
            ),
            "turn_b": HookDefinition(
                hook_id=TurnHookId("turn_b"),
                invocation="turn_phase",
                after=[TurnHookId("turn_a")],
                before=[],
                description="B",
                defined_by="test"
            ),
        }

        initialize(hook_defs)

        # Check that turn_executor's internal state has correct phases
        from src import turn_executor
        self.assertEqual(turn_executor._ordered_turn_phases, ["turn_a", "turn_b"])

    def test_caches_order(self):
        """Topological sort cached and reused."""
        hook_defs = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_b")],
                description="A",
                defined_by="test"
            ),
            "turn_b": HookDefinition(
                hook_id=TurnHookId("turn_b"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="B",
                defined_by="test"
            ),
        }

        initialize(hook_defs)

        from src import turn_executor
        self.assertEqual(turn_executor._ordered_turn_phases, ["turn_a", "turn_b"])


class TestExecuteTurnPhases(unittest.TestCase):
    """Test execute_turn_phases invokes hooks in correct order."""

    def setUp(self):
        """Set up minimal game state and mocks."""
        from src.state_manager import Metadata
        self.state = GameState(
            locations=[Location(id="loc1", name="Test", description="Test")],
            actors={},
            items=[],
            metadata=Metadata(title="Test Game")
        )
        self.accessor = Mock()
        self.behavior_manager = Mock()
        self.action = {"actor_id": "player", "verb": "test"}

    def test_increments_turn_count(self):
        """Turn count incremented before phase execution."""
        from src import turn_executor

        # Initialize with empty phases
        initialize({})

        initial_turn = self.state.turn_count
        execute_turn_phases(self.state, self.behavior_manager, self.accessor, self.action)

        self.assertEqual(self.state.turn_count, initial_turn + 1)

    def test_invokes_phases_in_order(self):
        """Phases invoked in topological order."""
        from src import turn_executor

        # Set up phases
        hook_defs = {
            "turn_first": HookDefinition(
                hook_id=TurnHookId("turn_first"),
                invocation="turn_phase",
                after=[],
                before=[TurnHookId("turn_second")],
                description="First",
                defined_by="test"
            ),
            "turn_second": HookDefinition(
                hook_id=TurnHookId("turn_second"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="Second",
                defined_by="test"
            ),
        }
        initialize(hook_defs)

        # Mock behavior_manager to track invocations
        invoked_hooks = []

        def mock_get_event(hook_id):
            # Return event names for tracking
            return f"on_{hook_id}"

        def mock_invoke(entity, event, accessor, context):
            invoked_hooks.append(context["hook"])
            result = Mock()
            result.feedback = f"Message from {context['hook']}"
            return result

        self.behavior_manager.get_event_for_hook = mock_get_event
        self.behavior_manager.invoke_behavior = mock_invoke

        messages = execute_turn_phases(self.state, self.behavior_manager, self.accessor, self.action)

        # Check invocation order
        self.assertEqual(invoked_hooks, ["turn_first", "turn_second"])
        self.assertEqual(messages, ["Message from turn_first", "Message from turn_second"])

    def test_skips_hooks_without_events(self):
        """Hooks without registered events are skipped."""
        from src import turn_executor

        hook_defs = {
            "turn_with_event": HookDefinition(
                hook_id=TurnHookId("turn_with_event"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="Has event",
                defined_by="test"
            ),
            "turn_no_event": HookDefinition(
                hook_id=TurnHookId("turn_no_event"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="No event",
                defined_by="test"
            ),
        }
        initialize(hook_defs)

        invoked_hooks = []

        def mock_get_event(hook_id):
            # Only return event for one hook
            if str(hook_id) == "turn_with_event":
                return "on_with_event"
            return None

        def mock_invoke(entity, event, accessor, context):
            invoked_hooks.append(context["hook"])
            result = Mock()
            result.feedback = None
            return result

        self.behavior_manager.get_event_for_hook = mock_get_event
        self.behavior_manager.invoke_behavior = mock_invoke

        execute_turn_phases(self.state, self.behavior_manager, self.accessor, self.action)

        # Only the hook with an event should be invoked
        self.assertEqual(invoked_hooks, ["turn_with_event"])

    def test_collects_narration_messages(self):
        """Narration messages collected from all phases."""
        from src import turn_executor

        hook_defs = {
            "turn_a": HookDefinition(
                hook_id=TurnHookId("turn_a"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="A",
                defined_by="test"
            ),
            "turn_b": HookDefinition(
                hook_id=TurnHookId("turn_b"),
                invocation="turn_phase",
                after=[],
                before=[],
                description="B",
                defined_by="test"
            ),
        }
        initialize(hook_defs)

        def mock_get_event(hook_id):
            return f"on_{hook_id}"

        def mock_invoke(entity, event, accessor, context):
            result = Mock()
            if context["hook"] == "turn_a":
                result.feedback = "Message A"
            else:
                result.feedback = "Message B"
            return result

        self.behavior_manager.get_event_for_hook = mock_get_event
        self.behavior_manager.invoke_behavior = mock_invoke

        messages = execute_turn_phases(self.state, self.behavior_manager, self.accessor, self.action)

        self.assertEqual(messages, ["Message A", "Message B"])


if __name__ == "__main__":
    unittest.main()
