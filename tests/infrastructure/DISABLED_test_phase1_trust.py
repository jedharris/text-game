"""
Phase 1 Trust Operation Tests

Tests for trust modification, threshold checking, and recovery operations.
"""

import unittest

from src.infrastructure_types import TrustState, TurnNumber
from src.infrastructure_utils import (
    attempt_trust_recovery,
    calculate_recovery_amount,
    check_trust_threshold,
    # modify_trust is now private (_modify_trust). Use apply_trust_change() instead.
)


class TestModifyTrust(unittest.TestCase):
    """Test trust modification function."""

    def test_modify_trust_positive_delta(self) -> None:
        """Positive delta increases trust."""
        result = modify_trust(5, 3)
        self.assertEqual(result, 8)

    def test_modify_trust_negative_delta(self) -> None:
        """Negative delta decreases trust."""
        result = modify_trust(5, -3)
        self.assertEqual(result, 2)

    def test_modify_trust_respects_floor(self) -> None:
        """Trust doesn't go below floor."""
        result = modify_trust(5, -10, floor=0)
        self.assertEqual(result, 0)

    def test_modify_trust_respects_ceiling(self) -> None:
        """Trust doesn't go above ceiling."""
        result = modify_trust(5, 10, ceiling=10)
        self.assertEqual(result, 10)

    def test_modify_trust_both_bounds(self) -> None:
        """Trust respects both floor and ceiling."""
        result = modify_trust(5, -10, floor=-5, ceiling=10)
        self.assertEqual(result, -5)
        result = modify_trust(5, 20, floor=-5, ceiling=10)
        self.assertEqual(result, 10)

    def test_modify_trust_no_bounds(self) -> None:
        """Trust can go negative without floor."""
        result = modify_trust(5, -10)
        self.assertEqual(result, -5)

    def test_modify_trust_zero_delta(self) -> None:
        """Zero delta leaves trust unchanged."""
        result = modify_trust(5, 0)
        self.assertEqual(result, 5)


class TestCheckTrustThreshold(unittest.TestCase):
    """Test trust threshold checking."""

    def test_check_threshold_at_least_true(self) -> None:
        """At least check passes when trust >= threshold."""
        self.assertTrue(check_trust_threshold(5, 3, at_least=True))
        self.assertTrue(check_trust_threshold(5, 5, at_least=True))

    def test_check_threshold_at_least_false(self) -> None:
        """At least check fails when trust < threshold."""
        self.assertFalse(check_trust_threshold(2, 3, at_least=True))

    def test_check_threshold_at_most_true(self) -> None:
        """At most check passes when trust <= threshold."""
        self.assertTrue(check_trust_threshold(3, 5, at_least=False))
        self.assertTrue(check_trust_threshold(5, 5, at_least=False))

    def test_check_threshold_at_most_false(self) -> None:
        """At most check fails when trust > threshold."""
        self.assertFalse(check_trust_threshold(6, 5, at_least=False))

    def test_negative_trust_thresholds(self) -> None:
        """Thresholds work with negative values."""
        # Echo trust threshold example: -6
        self.assertTrue(check_trust_threshold(-3, -6, at_least=True))  # -3 >= -6
        self.assertFalse(check_trust_threshold(-7, -6, at_least=True))  # -7 < -6


class TestCalculateRecoveryAmount(unittest.TestCase):
    """Test recovery amount calculation."""

    def test_recovery_amount_normal(self) -> None:
        """Normal recovery within cap."""
        result = calculate_recovery_amount(
            current=5, target=10, max_per_session=3, recovered_this_session=0
        )
        self.assertEqual(result, 3)  # Min(needed=5, cap=3)

    def test_recovery_amount_partial_cap(self) -> None:
        """Recovery limited by remaining cap."""
        result = calculate_recovery_amount(
            current=5, target=10, max_per_session=3, recovered_this_session=2
        )
        self.assertEqual(result, 1)  # Only 1 remaining in cap

    def test_recovery_amount_at_target(self) -> None:
        """No recovery needed when at target."""
        result = calculate_recovery_amount(
            current=10, target=10, max_per_session=3, recovered_this_session=0
        )
        self.assertEqual(result, 0)

    def test_recovery_amount_above_target(self) -> None:
        """No recovery when above target."""
        result = calculate_recovery_amount(
            current=12, target=10, max_per_session=3, recovered_this_session=0
        )
        self.assertEqual(result, 0)

    def test_recovery_amount_cap_exhausted(self) -> None:
        """No recovery when session cap exhausted."""
        result = calculate_recovery_amount(
            current=5, target=10, max_per_session=3, recovered_this_session=3
        )
        self.assertEqual(result, 0)


class TestAttemptTrustRecovery(unittest.TestCase):
    """Test trust recovery attempts with session tracking."""

    def test_recovery_within_cap(self) -> None:
        """Recovery works within session cap."""
        trust_state: TrustState = {"current": 5}
        actual, new_value = attempt_trust_recovery(
            trust_state, recovery_amount=2, current_turn=TurnNumber(10), recovery_cap=3
        )
        self.assertEqual(actual, 2)
        self.assertEqual(new_value, 7)
        self.assertEqual(trust_state["current"], 7)
        self.assertEqual(trust_state["recovered_this_visit"], 2)
        self.assertEqual(trust_state["last_recovery_turn"], 10)

    def test_recovery_limited_by_cap(self) -> None:
        """Recovery is limited by remaining cap."""
        trust_state: TrustState = {
            "current": 5,
            "recovery_cap": 3,
            "recovered_this_visit": 2,
            "last_recovery_turn": TurnNumber(8),
        }
        actual, new_value = attempt_trust_recovery(
            trust_state, recovery_amount=5, current_turn=TurnNumber(10), recovery_cap=3
        )
        self.assertEqual(actual, 1)  # Only 1 remaining in cap
        self.assertEqual(new_value, 6)

    def test_recovery_session_reset(self) -> None:
        """Session resets when enough turns have passed."""
        trust_state: TrustState = {
            "current": 5,
            "recovery_cap": 3,
            "recovered_this_visit": 3,  # Cap exhausted
            "last_recovery_turn": TurnNumber(5),  # Long ago
        }
        # More than 10 turns later, session resets
        actual, new_value = attempt_trust_recovery(
            trust_state, recovery_amount=2, current_turn=TurnNumber(20), recovery_cap=3
        )
        self.assertEqual(actual, 2)  # Full recovery possible now
        self.assertEqual(new_value, 7)
        self.assertEqual(trust_state["recovered_this_visit"], 2)

    def test_recovery_zero_when_cap_exhausted(self) -> None:
        """No recovery when session cap exhausted and not reset."""
        trust_state: TrustState = {
            "current": 5,
            "recovery_cap": 3,
            "recovered_this_visit": 3,
            "last_recovery_turn": TurnNumber(8),
        }
        # Within 10 turns, session not reset
        actual, new_value = attempt_trust_recovery(
            trust_state, recovery_amount=2, current_turn=TurnNumber(10), recovery_cap=3
        )
        self.assertEqual(actual, 0)
        self.assertEqual(new_value, 5)  # Unchanged


if __name__ == "__main__":
    unittest.main()
