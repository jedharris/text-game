"""
Phase 1 Design Tests - Infrastructure Foundations

These tests are written against the designed API to validate interface usability.
They will not pass until implementation is complete.

Tests cover:
- Timer operations (TurnNumber typed)
- Flag operations (bool and int, typed accessors)
- State machine operations
- Collection accessors
"""
from src.types import ActorId

import unittest
from typing import cast

from src.infrastructure_types import (
    ScheduledEvent,
    ScheduledEventId,
    StateMachineConfig,
    TurnNumber,
)
from src.infrastructure_utils import (
    # Timer operations
    check_deadline,
    create_deadline,
    extend_deadline,
    turns_remaining,
    # Flag operations
    check_bool_flag,
    clear_flag,
    get_actor_flags,
    get_bool_flag,
    get_global_flags,
    get_int_flag,
    has_flag,
    increment_int_flag,
    set_bool_flag,
    set_int_flag,
    # State machine operations
    get_current_state,
    get_scheduled_events,
    transition_state,
    validate_state_machine,
)


class TestTimerOperations(unittest.TestCase):
    """Test timer utility functions."""

    def test_check_deadline_not_passed(self) -> None:
        """Deadline in future returns False."""
        current = TurnNumber(5)
        deadline = TurnNumber(10)
        result = check_deadline(current, deadline)
        self.assertFalse(result)

    def test_check_deadline_exactly_reached(self) -> None:
        """Deadline at current turn returns True (deadline has passed)."""
        current = TurnNumber(10)
        deadline = TurnNumber(10)
        result = check_deadline(current, deadline)
        self.assertTrue(result)

    def test_check_deadline_passed(self) -> None:
        """Deadline in past returns True."""
        current = TurnNumber(15)
        deadline = TurnNumber(10)
        result = check_deadline(current, deadline)
        self.assertTrue(result)

    def test_turns_remaining_positive(self) -> None:
        """Turns remaining when deadline is in future."""
        current = TurnNumber(5)
        deadline = TurnNumber(10)
        result = turns_remaining(current, deadline)
        self.assertEqual(result, 5)

    def test_turns_remaining_zero_when_passed(self) -> None:
        """Turns remaining returns 0 when deadline passed."""
        current = TurnNumber(15)
        deadline = TurnNumber(10)
        result = turns_remaining(current, deadline)
        self.assertEqual(result, 0)

    def test_extend_deadline(self) -> None:
        """Extending deadline adds turns."""
        deadline = TurnNumber(10)
        extension = 5
        new_deadline = extend_deadline(deadline, extension)
        self.assertEqual(new_deadline, TurnNumber(15))

    def test_create_deadline(self) -> None:
        """Creating deadline from current turn and duration."""
        current = TurnNumber(5)
        duration = 10
        deadline = create_deadline(current, duration)
        self.assertEqual(deadline, TurnNumber(15))


class TestBoolFlagOperations(unittest.TestCase):
    """Test boolean flag utility functions."""

    def test_get_bool_flag_exists(self) -> None:
        """Get bool flag that exists returns its value."""
        flags: dict[str, bool] = {"visited_nexus": True, "met_sira": False}
        result = get_bool_flag(flags, "visited_nexus")
        self.assertTrue(result)

    def test_get_bool_flag_missing_returns_default(self) -> None:
        """Get bool flag that doesn't exist returns default (False)."""
        flags: dict[str, bool] = {}
        result = get_bool_flag(flags, "visited_nexus")
        self.assertFalse(result)

    def test_get_bool_flag_custom_default(self) -> None:
        """Get bool flag with custom default."""
        flags: dict[str, bool] = {}
        result = get_bool_flag(flags, "visited_nexus", default=True)
        self.assertTrue(result)

    def test_set_bool_flag(self) -> None:
        """Set boolean flag."""
        flags: dict[str, bool] = {}
        set_bool_flag(flags, "visited_nexus", True)
        self.assertTrue(flags["visited_nexus"])

    def test_check_bool_flag_true(self) -> None:
        """Check bool flag returns True when flag is True."""
        flags: dict[str, bool] = {"visited_nexus": True}
        result = check_bool_flag(flags, "visited_nexus")
        self.assertTrue(result)

    def test_check_bool_flag_false(self) -> None:
        """Check bool flag returns False when flag is False."""
        flags: dict[str, bool] = {"visited_nexus": False}
        result = check_bool_flag(flags, "visited_nexus")
        self.assertFalse(result)

    def test_check_bool_flag_missing(self) -> None:
        """Check bool flag returns False when flag doesn't exist."""
        flags: dict[str, bool] = {}
        result = check_bool_flag(flags, "visited_nexus")
        self.assertFalse(result)


class TestIntFlagOperations(unittest.TestCase):
    """Test integer flag utility functions."""

    def test_get_int_flag_exists(self) -> None:
        """Get int flag that exists returns its value."""
        flags: dict[str, int] = {"wolves_befriended": 3, "times_died": 0}
        result = get_int_flag(flags, "wolves_befriended")
        self.assertEqual(result, 3)

    def test_get_int_flag_missing_returns_default(self) -> None:
        """Get int flag that doesn't exist returns default (0)."""
        flags: dict[str, int] = {}
        result = get_int_flag(flags, "wolves_befriended")
        self.assertEqual(result, 0)

    def test_get_int_flag_custom_default(self) -> None:
        """Get int flag with custom default."""
        flags: dict[str, int] = {}
        result = get_int_flag(flags, "wolves_befriended", default=5)
        self.assertEqual(result, 5)

    def test_set_int_flag(self) -> None:
        """Set integer flag."""
        flags: dict[str, int] = {}
        set_int_flag(flags, "wolves_befriended", 3)
        self.assertEqual(flags["wolves_befriended"], 3)

    def test_increment_int_flag_new(self) -> None:
        """Increment non-existent int flag starts from 0."""
        flags: dict[str, int] = {}
        result = increment_int_flag(flags, "times_died")
        self.assertEqual(result, 1)
        self.assertEqual(flags["times_died"], 1)

    def test_increment_int_flag_existing(self) -> None:
        """Increment existing int flag adds to current value."""
        flags: dict[str, int] = {"times_died": 2}
        result = increment_int_flag(flags, "times_died")
        self.assertEqual(result, 3)

    def test_increment_int_flag_custom_delta(self) -> None:
        """Increment with custom delta."""
        flags: dict[str, int] = {"wolves_befriended": 1}
        result = increment_int_flag(flags, "wolves_befriended", delta=2)
        self.assertEqual(result, 3)


class TestCommonFlagOperations(unittest.TestCase):
    """Test flag operations that work on any type."""

    def test_clear_flag_exists(self) -> None:
        """Clear existing flag returns True and removes it."""
        flags: dict[str, bool | int] = {"visited_nexus": True}
        result = clear_flag(flags, "visited_nexus")
        self.assertTrue(result)
        self.assertNotIn("visited_nexus", flags)

    def test_clear_flag_missing(self) -> None:
        """Clear missing flag returns False."""
        flags: dict[str, bool | int] = {}
        result = clear_flag(flags, "visited_nexus")
        self.assertFalse(result)

    def test_has_flag_exists(self) -> None:
        """Has flag returns True when flag exists."""
        flags: dict[str, bool | int] = {"visited_nexus": True}
        result = has_flag(flags, "visited_nexus")
        self.assertTrue(result)

    def test_has_flag_missing(self) -> None:
        """Has flag returns False when flag doesn't exist."""
        flags: dict[str, bool | int] = {}
        result = has_flag(flags, "visited_nexus")
        self.assertFalse(result)


class TestStateMachineOperations(unittest.TestCase):
    """Test state machine utility functions."""

    def test_validate_state_machine_valid(self) -> None:
        """Valid state machine returns empty error list."""
        config: StateMachineConfig = {
            "states": ["neutral", "friendly", "hostile"],
            "initial": "neutral"
        }
        errors = validate_state_machine(config)
        self.assertEqual(errors, [])

    def test_validate_state_machine_no_states(self) -> None:
        """State machine with no states returns error."""
        config: StateMachineConfig = {
            "states": [],
            "initial": "neutral"
        }
        errors = validate_state_machine(config)
        self.assertIn("State machine has no states", errors[0])

    def test_validate_state_machine_invalid_initial(self) -> None:
        """State machine with invalid initial state returns error."""
        config: StateMachineConfig = {
            "states": ["neutral", "friendly"],
            "initial": "hostile"
        }
        errors = validate_state_machine(config)
        self.assertIn("Initial state 'hostile' not in states list", errors[0])

    def test_validate_state_machine_invalid_current(self) -> None:
        """State machine with invalid current state returns error."""
        config: StateMachineConfig = {
            "states": ["neutral", "friendly"],
            "initial": "neutral",
            "current": "hostile"
        }
        errors = validate_state_machine(config)
        self.assertIn("Current state 'hostile' not in states list", errors[0])

    def test_get_current_state_explicit(self) -> None:
        """Get current state when explicitly set."""
        config: StateMachineConfig = {
            "states": ["neutral", "friendly", "hostile"],
            "initial": "neutral",
            "current": "friendly"
        }
        result = get_current_state(config)
        self.assertEqual(result, "friendly")

    def test_get_current_state_defaults_to_initial(self) -> None:
        """Get current state defaults to initial when not set."""
        config: StateMachineConfig = {
            "states": ["neutral", "friendly", "hostile"],
            "initial": "neutral"
        }
        result = get_current_state(config)
        self.assertEqual(result, "neutral")

    def test_transition_state_valid(self) -> None:
        """Valid state transition succeeds."""
        config: StateMachineConfig = {
            "states": ["neutral", "friendly", "hostile"],
            "initial": "neutral"
        }
        success, message = transition_state(config, "friendly")
        self.assertTrue(success)
        self.assertEqual(config["current"], "friendly")

    def test_transition_state_invalid(self) -> None:
        """Invalid state transition fails."""
        config: StateMachineConfig = {
            "states": ["neutral", "friendly"],
            "initial": "neutral"
        }
        success, message = transition_state(config, "hostile")
        self.assertFalse(success)
        self.assertIn("Invalid state", message)


class TestCollectionAccessors(unittest.TestCase):
    """Test collection accessor functions."""

    def test_get_scheduled_events_initializes_if_missing(self) -> None:
        """Getting scheduled events initializes empty list if missing."""
        # Mock GameState with empty extra
        class MockState:
            extra: dict = {}

        state = MockState()
        events = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(events, [])
        self.assertIn("scheduled_events", state.extra)

    def test_get_scheduled_events_returns_existing(self) -> None:
        """Getting scheduled events returns existing list."""
        class MockState:
            extra = {
                "scheduled_events": [
                    {"id": "event_1", "trigger_turn": 10, "event_type": "test"}
                ]
            }

        state = MockState()
        events = get_scheduled_events(state)  # type: ignore[arg-type]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["id"], "event_1")

    def test_get_scheduled_events_can_append(self) -> None:
        """Can append to returned scheduled events list."""
        class MockState:
            extra: dict = {}

        state = MockState()
        events = get_scheduled_events(state)  # type: ignore[arg-type]
        events.append({"id": ScheduledEventId("new_event"), "trigger_turn": TurnNumber(5), "event_type": "test"})
        self.assertEqual(len(state.extra["scheduled_events"]), 1)


class TestFlagScopeAccessors(unittest.TestCase):
    """Test flag scope accessor functions."""

    def test_get_global_flags_initializes(self) -> None:
        """Global flags accessor initializes if missing."""
        class MockState:
            extra: dict = {}

        state = MockState()
        flags = get_global_flags(state)  # type: ignore[arg-type]
        self.assertEqual(flags, {})
        self.assertIn("flags", state.extra)

    def test_get_actor_flags_for_player(self) -> None:
        """Actor flags accessor works for player actor."""
        class MockActor:
            flags = {"visited_nexus": True}

        class MockState:
            actors = {"player": MockActor()}

        state = MockState()
        player = state.actors.get(ActorId("player"))
        flags = get_actor_flags(player)  # type: ignore[arg-type]
        self.assertEqual(flags, {"visited_nexus": True})

    def test_get_actor_flags_returns_actor_flags(self) -> None:
        """Actor flags accessor returns the actor's flags."""
        class MockActor:
            flags = {"grateful": True, "trust": 5}

        actor = MockActor()
        flags = get_actor_flags(actor)  # type: ignore[arg-type]
        self.assertEqual(flags, {"grateful": True, "trust": 5})


if __name__ == "__main__":
    unittest.main()
