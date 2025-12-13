"""Tests for turn counter helper functions."""

import unittest

from src.infrastructure_types import TurnNumber
from src.infrastructure_utils import get_current_turn, increment_turn


class MockState:
    """Mock game state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}


class TestGetCurrentTurn(unittest.TestCase):
    """Tests for get_current_turn."""

    def test_returns_zero_when_not_set(self) -> None:
        """Current turn is 0 when turn_count not in extra."""
        state = MockState()
        result = get_current_turn(state)  # type: ignore[arg-type]
        self.assertEqual(result, 0)

    def test_returns_value_when_set(self) -> None:
        """Current turn reflects turn_count value."""
        state = MockState()
        state.extra["turn_count"] = 42
        result = get_current_turn(state)  # type: ignore[arg-type]
        self.assertEqual(result, 42)


class TestIncrementTurn(unittest.TestCase):
    """Tests for increment_turn."""

    def test_increments_from_zero(self) -> None:
        """Increment from unset state starts at 1."""
        state = MockState()
        result = increment_turn(state)  # type: ignore[arg-type]
        self.assertEqual(result, 1)
        self.assertEqual(state.extra["turn_count"], 1)

    def test_increments_existing_value(self) -> None:
        """Increment adds 1 to existing value."""
        state = MockState()
        state.extra["turn_count"] = 10
        result = increment_turn(state)  # type: ignore[arg-type]
        self.assertEqual(result, 11)
        self.assertEqual(state.extra["turn_count"], 11)

    def test_multiple_increments(self) -> None:
        """Multiple increments work correctly."""
        state = MockState()
        increment_turn(state)  # type: ignore[arg-type]
        increment_turn(state)  # type: ignore[arg-type]
        result = increment_turn(state)  # type: ignore[arg-type]
        self.assertEqual(result, 3)


if __name__ == "__main__":
    unittest.main()
