"""
Phase 1 Scheduled Event Tests

Tests for scheduling, cancelling, rescheduling, and firing events.
"""

import unittest

from src.infrastructure_types import ScheduledEventId, TurnNumber
from src.infrastructure_utils import (
    cancel_scheduled_event,
    fire_due_events,
    get_due_events,
    get_scheduled_events,
    reschedule_event,
    schedule_event,
)


class MockState:
    """Mock game state for testing."""

    def __init__(self, turn_count: int = 0) -> None:
        self.extra: dict = {"turn_count": turn_count}


class TestScheduleEvent(unittest.TestCase):
    """Test event scheduling."""

    def test_schedule_basic_event(self) -> None:
        """Schedule a basic event."""
        state = MockState(turn_count=10)
        event_id = schedule_event(
            state,  # type: ignore[arg-type]
            event_type="garrett_warning",
            turns_from_now=5,
        )

        events = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "garrett_warning")
        self.assertEqual(events[0]["trigger_turn"], 15)  # 10 + 5
        self.assertIsNotNone(event_id)

    def test_schedule_event_with_custom_id(self) -> None:
        """Schedule event with custom ID."""
        state = MockState(turn_count=5)
        event_id = schedule_event(
            state,  # type: ignore[arg-type]
            event_type="cold_spread",
            turns_from_now=10,
            event_id=ScheduledEventId("custom_cold_event"),
        )

        self.assertEqual(event_id, "custom_cold_event")
        events = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(events[0]["id"], "custom_cold_event")

    def test_schedule_event_with_data(self) -> None:
        """Schedule event with additional data."""
        state = MockState(turn_count=0)
        schedule_event(
            state,  # type: ignore[arg-type]
            event_type="npc_leaves",
            turns_from_now=3,
            data={"actor_id": "garrett", "destination": "sunken_district"},
        )

        events = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(events[0]["data"]["actor_id"], "garrett")
        self.assertEqual(events[0]["data"]["destination"], "sunken_district")

    def test_schedule_multiple_events(self) -> None:
        """Multiple events can be scheduled."""
        state = MockState(turn_count=0)
        schedule_event(state, "event_a", 5)  # type: ignore[arg-type]
        schedule_event(state, "event_b", 3)  # type: ignore[arg-type]
        schedule_event(state, "event_c", 10)  # type: ignore[arg-type]

        events = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(events), 3)


class TestCancelScheduledEvent(unittest.TestCase):
    """Test event cancellation."""

    def test_cancel_existing_event(self) -> None:
        """Cancel an existing event."""
        state = MockState(turn_count=0)
        event_id = schedule_event(
            state,  # type: ignore[arg-type]
            "test_event",
            5,
            event_id=ScheduledEventId("cancel_me"),
        )

        result = cancel_scheduled_event(state, event_id)  # type: ignore[arg-type]
        self.assertTrue(result)

        events = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(events), 0)

    def test_cancel_nonexistent_event(self) -> None:
        """Cancelling nonexistent event returns False."""
        state = MockState()
        result = cancel_scheduled_event(
            state,  # type: ignore[arg-type]
            ScheduledEventId("nonexistent"),
        )
        self.assertFalse(result)

    def test_cancel_preserves_other_events(self) -> None:
        """Cancelling one event doesn't affect others."""
        state = MockState()
        schedule_event(state, "event_a", 5, event_id=ScheduledEventId("a"))  # type: ignore[arg-type]
        schedule_event(state, "event_b", 5, event_id=ScheduledEventId("b"))  # type: ignore[arg-type]
        schedule_event(state, "event_c", 5, event_id=ScheduledEventId("c"))  # type: ignore[arg-type]

        cancel_scheduled_event(state, ScheduledEventId("b"))  # type: ignore[arg-type]

        events = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(events), 2)
        event_ids = [e["id"] for e in events]
        self.assertIn("a", event_ids)
        self.assertIn("c", event_ids)
        self.assertNotIn("b", event_ids)


class TestRescheduleEvent(unittest.TestCase):
    """Test event rescheduling."""

    def test_reschedule_existing_event(self) -> None:
        """Reschedule an existing event."""
        state = MockState(turn_count=0)
        event_id = schedule_event(
            state,  # type: ignore[arg-type]
            "test_event",
            5,
            event_id=ScheduledEventId("reschedule_me"),
        )

        result = reschedule_event(state, event_id, TurnNumber(20))  # type: ignore[arg-type]
        self.assertTrue(result)

        events = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(events[0]["trigger_turn"], 20)

    def test_reschedule_nonexistent_event(self) -> None:
        """Rescheduling nonexistent event returns False."""
        state = MockState()
        result = reschedule_event(
            state,  # type: ignore[arg-type]
            ScheduledEventId("nonexistent"),
            TurnNumber(10),
        )
        self.assertFalse(result)


class TestGetDueEvents(unittest.TestCase):
    """Test getting due events."""

    def test_get_due_events_none_due(self) -> None:
        """No events due when all are in the future."""
        state = MockState(turn_count=5)
        # Fires at turn 15
        schedule_event(state, "event_a", 10)  # type: ignore[arg-type]
        # Fires at turn 10
        schedule_event(state, "event_b", 5)  # type: ignore[arg-type]

        due = get_due_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(due), 0)

    def test_get_due_events_some_due(self) -> None:
        """Get events that are due."""
        state = MockState(turn_count=10)
        # Fired at turn 5
        schedule_event(state, "past", -5)  # type: ignore[arg-type]
        # Fires at turn 10
        schedule_event(state, "now", 0)  # type: ignore[arg-type]
        # Fires at turn 15
        schedule_event(state, "future", 5)  # type: ignore[arg-type]

        due = get_due_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(due), 2)  # past and now
        event_types = [e["event_type"] for e in due]
        self.assertIn("past", event_types)
        self.assertIn("now", event_types)
        self.assertNotIn("future", event_types)

    def test_get_due_events_does_not_remove(self) -> None:
        """get_due_events doesn't remove events."""
        state = MockState(turn_count=10)
        schedule_event(state, "due_event", 0)  # type: ignore[arg-type]

        get_due_events(state)  # type: ignore[arg-type]

        events = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(events), 1)  # Still there


class TestFireDueEvents(unittest.TestCase):
    """Test firing due events."""

    def test_fire_due_events_returns_and_removes(self) -> None:
        """fire_due_events returns due events and removes them."""
        state = MockState(turn_count=10)
        schedule_event(state, "past", -5)  # type: ignore[arg-type]
        schedule_event(state, "now", 0)  # type: ignore[arg-type]
        schedule_event(state, "future", 5)  # type: ignore[arg-type]

        fired = fire_due_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(fired), 2)

        remaining = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["event_type"], "future")

    def test_fire_due_events_empty_when_none_due(self) -> None:
        """fire_due_events returns empty list when nothing due."""
        state = MockState(turn_count=0)
        schedule_event(state, "future", 10)  # type: ignore[arg-type]

        fired = fire_due_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(fired), 0)


if __name__ == "__main__":
    unittest.main()
