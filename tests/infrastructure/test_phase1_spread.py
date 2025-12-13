"""
Phase 1 Environmental Spread System Tests

Tests for spread creation, activation, milestones, and halt flags.
"""

import unittest

from src.infrastructure_types import SpreadMilestone, SpreadState, TurnNumber
from src.infrastructure_utils import (
    activate_spread,
    check_spread_active,
    check_spread_halt_flag,
    create_spread,
    get_due_milestones,
    get_environmental_spreads,
    get_global_flags,
    get_spread,
    get_spread_progress,
    halt_spread,
    mark_milestone_reached,
    set_bool_flag,
)


class MockState:
    """Mock game state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}


def create_test_milestones() -> list[SpreadMilestone]:
    """Create test milestones for cold spread."""
    return [
        {
            "turn": TurnNumber(25),
            "effects": [
                {
                    "locations": ["frozen_reaches/*"],
                    "property_name": "temperature_zone",
                    "property_value": "cold",
                }
            ],
        },
        {
            "turn": TurnNumber(50),
            "effects": [
                {
                    "locations": ["frozen_reaches/*"],
                    "property_name": "temperature_zone",
                    "property_value": "freezing",
                }
            ],
        },
        {
            "turn": TurnNumber(75),
            "effects": [
                {
                    "locations": ["frozen_reaches/*"],
                    "property_name": "temperature_zone",
                    "property_value": "extreme_cold",
                }
            ],
        },
    ]


class TestCreateSpread(unittest.TestCase):
    """Test spread creation."""

    def test_create_basic_spread(self) -> None:
        """Create a basic spread."""
        state = MockState()
        milestones = create_test_milestones()

        spread = create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=milestones,
        )

        self.assertTrue(spread["active"])
        self.assertEqual(spread["halt_flag"], "cold_halted")
        self.assertEqual(len(spread["milestones"]), 3)

    def test_create_inactive_spread(self) -> None:
        """Create a spread that starts inactive."""
        state = MockState()
        milestones = create_test_milestones()

        spread = create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=milestones,
            active=False,
        )

        self.assertFalse(spread["active"])

    def test_spread_appears_in_dict(self) -> None:
        """Created spread appears in spreads dict."""
        state = MockState()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=[],
        )

        spreads = get_environmental_spreads(state)  # type: ignore[arg-type]
        self.assertIn("cold_spread", spreads)


class TestGetSpread(unittest.TestCase):
    """Test spread lookup."""

    def test_get_existing_spread(self) -> None:
        """Find spread that exists."""
        state = MockState()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=[],
        )

        spread = get_spread(state, "cold_spread")  # type: ignore[arg-type]
        self.assertIsNotNone(spread)

    def test_get_missing_spread(self) -> None:
        """Find spread that doesn't exist returns None."""
        state = MockState()

        spread = get_spread(state, "nonexistent")  # type: ignore[arg-type]
        self.assertIsNone(spread)


class TestCheckSpreadActive(unittest.TestCase):
    """Test checking spread active state."""

    def test_active_spread(self) -> None:
        """Check active spread returns True."""
        state = MockState()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=[],
            active=True,
        )

        self.assertTrue(check_spread_active(state, "cold_spread"))  # type: ignore[arg-type]

    def test_inactive_spread(self) -> None:
        """Check inactive spread returns False."""
        state = MockState()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=[],
            active=False,
        )

        self.assertFalse(check_spread_active(state, "cold_spread"))  # type: ignore[arg-type]

    def test_nonexistent_spread(self) -> None:
        """Check nonexistent spread returns False."""
        state = MockState()

        self.assertFalse(check_spread_active(state, "nonexistent"))  # type: ignore[arg-type]


class TestHaltSpread(unittest.TestCase):
    """Test halting spreads."""

    def test_halt_active_spread(self) -> None:
        """Halt an active spread."""
        state = MockState()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=[],
            active=True,
        )

        result = halt_spread(state, "cold_spread")  # type: ignore[arg-type]
        self.assertTrue(result)
        self.assertFalse(check_spread_active(state, "cold_spread"))  # type: ignore[arg-type]

    def test_halt_inactive_spread(self) -> None:
        """Halting inactive spread returns False."""
        state = MockState()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=[],
            active=False,
        )

        result = halt_spread(state, "cold_spread")  # type: ignore[arg-type]
        self.assertFalse(result)

    def test_halt_nonexistent_spread(self) -> None:
        """Halting nonexistent spread returns False."""
        state = MockState()

        result = halt_spread(state, "nonexistent")  # type: ignore[arg-type]
        self.assertFalse(result)


class TestActivateSpread(unittest.TestCase):
    """Test activating spreads."""

    def test_activate_inactive_spread(self) -> None:
        """Activate an inactive spread."""
        state = MockState()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=[],
            active=False,
        )

        result = activate_spread(state, "cold_spread")  # type: ignore[arg-type]
        self.assertTrue(result)
        self.assertTrue(check_spread_active(state, "cold_spread"))  # type: ignore[arg-type]

    def test_activate_active_spread(self) -> None:
        """Activating active spread returns False."""
        state = MockState()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=[],
            active=True,
        )

        result = activate_spread(state, "cold_spread")  # type: ignore[arg-type]
        self.assertFalse(result)


class TestGetSpreadProgress(unittest.TestCase):
    """Test getting spread progress."""

    def test_progress_no_milestones_reached(self) -> None:
        """Progress when no milestones reached."""
        state = MockState()
        milestones = create_test_milestones()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=milestones,
        )

        current, next_turn = get_spread_progress(state, "cold_spread")  # type: ignore[arg-type]
        self.assertIsNone(current)
        self.assertEqual(next_turn, 25)

    def test_progress_some_milestones_reached(self) -> None:
        """Progress when some milestones reached."""
        state = MockState()
        milestones = create_test_milestones()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=milestones,
        )
        mark_milestone_reached(state, "cold_spread", TurnNumber(25))  # type: ignore[arg-type]

        current, next_turn = get_spread_progress(state, "cold_spread")  # type: ignore[arg-type]
        self.assertEqual(current, 25)
        self.assertEqual(next_turn, 50)

    def test_progress_all_milestones_reached(self) -> None:
        """Progress when all milestones reached."""
        state = MockState()
        milestones = create_test_milestones()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=milestones,
        )
        mark_milestone_reached(state, "cold_spread", TurnNumber(75))  # type: ignore[arg-type]

        current, next_turn = get_spread_progress(state, "cold_spread")  # type: ignore[arg-type]
        self.assertEqual(current, 75)
        self.assertIsNone(next_turn)

    def test_progress_nonexistent_spread(self) -> None:
        """Progress for nonexistent spread."""
        state = MockState()

        current, next_turn = get_spread_progress(state, "nonexistent")  # type: ignore[arg-type]
        self.assertIsNone(current)
        self.assertIsNone(next_turn)


class TestGetDueMilestones(unittest.TestCase):
    """Test getting due milestones."""

    def test_no_due_milestones(self) -> None:
        """No milestones due when turn hasn't reached any."""
        state = MockState()
        milestones = create_test_milestones()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=milestones,
        )

        due = get_due_milestones(state, "cold_spread", TurnNumber(10))  # type: ignore[arg-type]
        self.assertEqual(len(due), 0)

    def test_one_milestone_due(self) -> None:
        """One milestone due."""
        state = MockState()
        milestones = create_test_milestones()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=milestones,
        )

        due = get_due_milestones(state, "cold_spread", TurnNumber(30))  # type: ignore[arg-type]
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0]["turn"], 25)

    def test_multiple_milestones_due(self) -> None:
        """Multiple milestones due at once."""
        state = MockState()
        milestones = create_test_milestones()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=milestones,
        )

        due = get_due_milestones(state, "cold_spread", TurnNumber(60))  # type: ignore[arg-type]
        self.assertEqual(len(due), 2)
        # Should be sorted by turn
        self.assertEqual(due[0]["turn"], 25)
        self.assertEqual(due[1]["turn"], 50)

    def test_due_milestones_respects_current(self) -> None:
        """Due milestones doesn't return already-reached milestones."""
        state = MockState()
        milestones = create_test_milestones()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=milestones,
        )
        mark_milestone_reached(state, "cold_spread", TurnNumber(25))  # type: ignore[arg-type]

        due = get_due_milestones(state, "cold_spread", TurnNumber(60))  # type: ignore[arg-type]
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0]["turn"], 50)

    def test_due_milestones_inactive_spread(self) -> None:
        """No due milestones for inactive spread."""
        state = MockState()
        milestones = create_test_milestones()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=milestones,
            active=False,
        )

        due = get_due_milestones(state, "cold_spread", TurnNumber(100))  # type: ignore[arg-type]
        self.assertEqual(len(due), 0)


class TestCheckSpreadHaltFlag(unittest.TestCase):
    """Test checking spread halt flag."""

    def test_halt_flag_not_set(self) -> None:
        """Halt flag not set returns False."""
        state = MockState()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=[],
        )

        result = check_spread_halt_flag(state, "cold_spread")  # type: ignore[arg-type]
        self.assertFalse(result)

    def test_halt_flag_set(self) -> None:
        """Halt flag set returns True."""
        state = MockState()
        create_spread(
            state,  # type: ignore[arg-type]
            "cold_spread",
            halt_flag="cold_halted",
            milestones=[],
        )

        # Set the halt flag
        flags = get_global_flags(state)  # type: ignore[arg-type]
        set_bool_flag(flags, "cold_halted", True)

        result = check_spread_halt_flag(state, "cold_spread")  # type: ignore[arg-type]
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
