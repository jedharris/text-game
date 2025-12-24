"""Unit tests for event delegation logic in StateAccessor."""

import unittest
from unittest.mock import MagicMock, Mock
from src.behavior_manager import BehaviorManager
from src.state_accessor import StateAccessor, EventResult
from tests.conftest import create_test_state


class TestEventDelegationLogic(unittest.TestCase):
    """Test event delegation logic in StateAccessor.update()."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = create_test_state()
        self.behavior_manager = MagicMock(spec=BehaviorManager)
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_single_event_success(self):
        """Single event that succeeds (backward compat)."""
        # Mock get_events_for_verb to return single event
        self.behavior_manager.get_events_for_verb.return_value = [(1, "on_test")]

        # Mock invoke_behavior to succeed
        self.behavior_manager.invoke_behavior.return_value = EventResult(
            allow=True, feedback="Success"
        )

        # Create mock entity
        entity = Mock()
        entity.id = "test"

        # Call update
        result = self.accessor.update(entity, {}, verb="test")

        # Should succeed
        self.assertTrue(result.success)
        self.assertEqual(result.detail, "Success")

        # Should only invoke once
        self.assertEqual(self.behavior_manager.invoke_behavior.call_count, 1)

    def test_tier1_success_stops_delegation(self):
        """Tier 1 succeeds, doesn't try Tier 2."""
        # Mock get_events_for_verb to return two tiers
        self.behavior_manager.get_events_for_verb.return_value = [
            (1, "on_test_specific"),
            (2, "on_test_general")
        ]

        # Mock invoke_behavior to succeed on first call
        self.behavior_manager.invoke_behavior.return_value = EventResult(
            allow=True, feedback="Tier 1"
        )

        entity = Mock()
        entity.id = "test"

        result = self.accessor.update(entity, {}, verb="test")

        # Should succeed with Tier 1 message
        self.assertTrue(result.success)
        self.assertEqual(result.detail, "Tier 1")

        # Should only invoke Tier 1 event (first call)
        self.assertEqual(self.behavior_manager.invoke_behavior.call_count, 1)
        call_args = self.behavior_manager.invoke_behavior.call_args[0]
        self.assertEqual(call_args[1], "on_test_specific")  # First event

    def test_tier1_blocks_tries_tier2(self):
        """Tier 1 blocks (allow=False), tries Tier 2."""
        # Mock get_events_for_verb to return two tiers
        self.behavior_manager.get_events_for_verb.return_value = [
            (1, "on_test_specific"),
            (2, "on_test_general")
        ]

        # Mock invoke_behavior to block first, succeed second
        self.behavior_manager.invoke_behavior.side_effect = [
            EventResult(allow=False, feedback="Tier 1 blocked"),
            EventResult(allow=True, feedback="Tier 2 allowed")
        ]

        entity = Mock()
        entity.id = "test"

        result = self.accessor.update(entity, {}, verb="test")

        # Should succeed with Tier 2 message
        self.assertTrue(result.success)
        self.assertEqual(result.detail, "Tier 2 allowed")

        # Should invoke both events
        self.assertEqual(self.behavior_manager.invoke_behavior.call_count, 2)

    def test_tier1_none_tries_tier2(self):
        """Tier 1 returns None, falls through to Tier 2."""
        # Mock get_events_for_verb to return two tiers
        self.behavior_manager.get_events_for_verb.return_value = [
            (1, "on_test_specific"),
            (2, "on_test_general")
        ]

        # Mock invoke_behavior to return None first, succeed second
        self.behavior_manager.invoke_behavior.side_effect = [
            None,  # Tier 1 doesn't handle
            EventResult(allow=True, feedback="Tier 2 handled")
        ]

        entity = Mock()
        entity.id = "test"

        result = self.accessor.update(entity, {}, verb="test")

        # Should succeed with Tier 2 message
        self.assertTrue(result.success)
        self.assertEqual(result.detail, "Tier 2 handled")

        # Should invoke both events
        self.assertEqual(self.behavior_manager.invoke_behavior.call_count, 2)

    def test_all_tiers_block_returns_last_message(self):
        """All tiers block, returns last tier's message."""
        # Mock get_events_for_verb to return two tiers
        self.behavior_manager.get_events_for_verb.return_value = [
            (1, "on_test_specific"),
            (2, "on_test_general")
        ]

        # Mock invoke_behavior to block both times
        self.behavior_manager.invoke_behavior.side_effect = [
            EventResult(allow=False, feedback="Tier 1 blocked"),
            EventResult(allow=False, feedback="Tier 2 also blocked")
        ]

        entity = Mock()
        entity.id = "test"

        result = self.accessor.update(entity, {}, verb="test")

        # Should fail with Tier 2 message
        self.assertFalse(result.success)
        self.assertEqual(result.detail, "Tier 2 also blocked")

        # Should invoke both events
        self.assertEqual(self.behavior_manager.invoke_behavior.call_count, 2)

    def test_no_events_returns_success(self):
        """No events for verb, update succeeds (no behaviors to check)."""
        # Mock get_events_for_verb to return None
        self.behavior_manager.get_events_for_verb.return_value = None

        entity = Mock()
        entity.id = "test"
        entity.location = "room1"

        result = self.accessor.update(entity, {"location": "room2"}, verb="test")

        # Should succeed (no behaviors to check)
        self.assertTrue(result.success)

        # invoke_behavior should not be called
        self.assertEqual(self.behavior_manager.invoke_behavior.call_count, 0)


if __name__ == '__main__':
    unittest.main()
