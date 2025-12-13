"""
Phase 1 Commitment System Tests

Tests for commitment creation, state transitions, and queries.
"""

import unittest

from src.infrastructure_types import (
    ActiveCommitment,
    CommitmentConfig,
    CommitmentId,
    CommitmentState,
    TurnNumber,
)
from src.types import ActorId
from src.infrastructure_utils import (
    check_commitment_phrase,
    create_commitment,
    get_active_commitment,
    get_active_commitments,
    get_commitment_config,
    get_expired_commitments,
    transition_commitment_state,
)


class MockState:
    """Mock game state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}


def create_test_config() -> CommitmentConfig:
    """Create a test commitment config."""
    return {
        "id": CommitmentId("save_garrett"),
        "target_npc": ActorId("garrett"),
        "goal": "Find medicine for Garrett",
        "trigger_phrases": ["I'll save you", "I promise to help"],
        "hope_extends_survival": True,
        "hope_bonus": 10,
        "base_timer": 20,
    }


class TestGetCommitmentConfig(unittest.TestCase):
    """Test commitment config lookup."""

    def test_get_existing_config(self) -> None:
        """Get a config that exists."""
        state = MockState()
        config = create_test_config()
        state.extra["commitment_configs"] = {"save_garrett": config}

        result = get_commitment_config(state, "save_garrett")  # type: ignore[arg-type]
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["goal"], "Find medicine for Garrett")

    def test_get_missing_config(self) -> None:
        """Get a config that doesn't exist returns None."""
        state = MockState()
        state.extra["commitment_configs"] = {}

        result = get_commitment_config(state, "nonexistent")  # type: ignore[arg-type]
        self.assertIsNone(result)

    def test_get_config_no_configs_dict(self) -> None:
        """Get config when configs dict doesn't exist."""
        state = MockState()

        result = get_commitment_config(state, "anything")  # type: ignore[arg-type]
        self.assertIsNone(result)


class TestCreateCommitment(unittest.TestCase):
    """Test commitment creation."""

    def test_create_basic_commitment(self) -> None:
        """Create a commitment from config."""
        state = MockState()
        config = create_test_config()
        state.extra["commitment_configs"] = {"save_garrett": config}

        commitment = create_commitment(
            state,  # type: ignore[arg-type]
            "save_garrett",
            TurnNumber(5),
        )

        self.assertIsNotNone(commitment)
        assert commitment is not None
        self.assertEqual(commitment["id"], "save_garrett")
        self.assertEqual(commitment["config_id"], "save_garrett")
        self.assertEqual(commitment["state"], CommitmentState.ACTIVE)
        self.assertEqual(commitment["made_at_turn"], 5)
        self.assertFalse(commitment["hope_applied"])

    def test_create_timed_commitment(self) -> None:
        """Timed commitment has deadline set."""
        state = MockState()
        config = create_test_config()  # Has base_timer=20
        state.extra["commitment_configs"] = {"save_garrett": config}

        commitment = create_commitment(
            state,  # type: ignore[arg-type]
            "save_garrett",
            TurnNumber(5),
        )

        assert commitment is not None
        self.assertEqual(commitment["deadline_turn"], 25)  # 5 + 20

    def test_create_commitment_custom_id(self) -> None:
        """Create commitment with custom ID."""
        state = MockState()
        config = create_test_config()
        state.extra["commitment_configs"] = {"save_garrett": config}

        commitment = create_commitment(
            state,  # type: ignore[arg-type]
            "save_garrett",
            TurnNumber(0),
            commitment_id=CommitmentId("custom_id"),
        )

        assert commitment is not None
        self.assertEqual(commitment["id"], "custom_id")

    def test_create_commitment_missing_config(self) -> None:
        """Creating commitment with missing config returns None."""
        state = MockState()
        state.extra["commitment_configs"] = {}

        commitment = create_commitment(
            state,  # type: ignore[arg-type]
            "nonexistent",
            TurnNumber(0),
        )

        self.assertIsNone(commitment)

    def test_create_duplicate_commitment_fails(self) -> None:
        """Cannot create duplicate commitment."""
        state = MockState()
        config = create_test_config()
        state.extra["commitment_configs"] = {"save_garrett": config}

        # First creation succeeds
        first = create_commitment(
            state,  # type: ignore[arg-type]
            "save_garrett",
            TurnNumber(0),
        )
        self.assertIsNotNone(first)

        # Second creation fails
        second = create_commitment(
            state,  # type: ignore[arg-type]
            "save_garrett",
            TurnNumber(5),
        )
        self.assertIsNone(second)


class TestGetActiveCommitment(unittest.TestCase):
    """Test finding active commitments."""

    def test_find_existing_commitment(self) -> None:
        """Find a commitment that exists."""
        state = MockState()
        config = create_test_config()
        state.extra["commitment_configs"] = {"save_garrett": config}
        create_commitment(state, "save_garrett", TurnNumber(0))  # type: ignore[arg-type]

        result = get_active_commitment(state, CommitmentId("save_garrett"))  # type: ignore[arg-type]
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["id"], "save_garrett")

    def test_find_missing_commitment(self) -> None:
        """Find a commitment that doesn't exist returns None."""
        state = MockState()

        result = get_active_commitment(state, CommitmentId("nonexistent"))  # type: ignore[arg-type]
        self.assertIsNone(result)


class TestTransitionCommitmentState(unittest.TestCase):
    """Test commitment state transitions."""

    def test_transition_to_fulfilled(self) -> None:
        """Transition from ACTIVE to FULFILLED."""
        commitment: ActiveCommitment = {
            "id": CommitmentId("test"),
            "config_id": "test",
            "state": CommitmentState.ACTIVE,
            "made_at_turn": TurnNumber(0),
            "hope_applied": False,
        }

        result = transition_commitment_state(commitment, CommitmentState.FULFILLED)
        self.assertTrue(result)
        self.assertEqual(commitment["state"], CommitmentState.FULFILLED)

    def test_transition_to_withdrawn(self) -> None:
        """Transition from ACTIVE to WITHDRAWN."""
        commitment: ActiveCommitment = {
            "id": CommitmentId("test"),
            "config_id": "test",
            "state": CommitmentState.ACTIVE,
            "made_at_turn": TurnNumber(0),
            "hope_applied": False,
        }

        result = transition_commitment_state(commitment, CommitmentState.WITHDRAWN)
        self.assertTrue(result)
        self.assertEqual(commitment["state"], CommitmentState.WITHDRAWN)

    def test_transition_to_abandoned(self) -> None:
        """Transition from ACTIVE to ABANDONED."""
        commitment: ActiveCommitment = {
            "id": CommitmentId("test"),
            "config_id": "test",
            "state": CommitmentState.ACTIVE,
            "made_at_turn": TurnNumber(0),
            "hope_applied": False,
        }

        result = transition_commitment_state(commitment, CommitmentState.ABANDONED)
        self.assertTrue(result)
        self.assertEqual(commitment["state"], CommitmentState.ABANDONED)

    def test_transition_from_fulfilled_fails(self) -> None:
        """Cannot transition from terminal FULFILLED state."""
        commitment: ActiveCommitment = {
            "id": CommitmentId("test"),
            "config_id": "test",
            "state": CommitmentState.FULFILLED,
            "made_at_turn": TurnNumber(0),
            "hope_applied": True,
        }

        result = transition_commitment_state(commitment, CommitmentState.ABANDONED)
        self.assertFalse(result)
        self.assertEqual(commitment["state"], CommitmentState.FULFILLED)  # Unchanged

    def test_transition_to_active_fails(self) -> None:
        """Cannot transition to ACTIVE (only initial state)."""
        commitment: ActiveCommitment = {
            "id": CommitmentId("test"),
            "config_id": "test",
            "state": CommitmentState.ACTIVE,
            "made_at_turn": TurnNumber(0),
            "hope_applied": False,
        }

        result = transition_commitment_state(commitment, CommitmentState.ACTIVE)
        self.assertFalse(result)


class TestGetExpiredCommitments(unittest.TestCase):
    """Test finding expired commitments."""

    def test_no_expired_commitments(self) -> None:
        """No commitments expired when deadlines in future."""
        state = MockState()
        state.extra["active_commitments"] = [
            {
                "id": CommitmentId("test"),
                "config_id": "test",
                "state": CommitmentState.ACTIVE,
                "made_at_turn": TurnNumber(0),
                "deadline_turn": TurnNumber(20),
                "hope_applied": False,
            }
        ]

        expired = get_expired_commitments(state, TurnNumber(10))  # type: ignore[arg-type]
        self.assertEqual(len(expired), 0)

    def test_expired_commitment_found(self) -> None:
        """Find commitment past deadline."""
        state = MockState()
        state.extra["active_commitments"] = [
            {
                "id": CommitmentId("expired"),
                "config_id": "test",
                "state": CommitmentState.ACTIVE,
                "made_at_turn": TurnNumber(0),
                "deadline_turn": TurnNumber(10),
                "hope_applied": False,
            },
            {
                "id": CommitmentId("not_expired"),
                "config_id": "test",
                "state": CommitmentState.ACTIVE,
                "made_at_turn": TurnNumber(5),
                "deadline_turn": TurnNumber(25),
                "hope_applied": False,
            },
        ]

        expired = get_expired_commitments(state, TurnNumber(15))  # type: ignore[arg-type]
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0]["id"], "expired")

    def test_fulfilled_not_expired(self) -> None:
        """Fulfilled commitments are not returned even if past deadline."""
        state = MockState()
        state.extra["active_commitments"] = [
            {
                "id": CommitmentId("done"),
                "config_id": "test",
                "state": CommitmentState.FULFILLED,
                "made_at_turn": TurnNumber(0),
                "deadline_turn": TurnNumber(10),
                "hope_applied": True,
            }
        ]

        expired = get_expired_commitments(state, TurnNumber(20))  # type: ignore[arg-type]
        self.assertEqual(len(expired), 0)


class TestCheckCommitmentPhrase(unittest.TestCase):
    """Test commitment phrase detection."""

    def test_matching_phrase(self) -> None:
        """Detect matching trigger phrase."""
        state = MockState()
        config = create_test_config()
        state.extra["commitment_configs"] = {"save_garrett": config}

        result = check_commitment_phrase(
            "I'll save you, Garrett!",
            "sunken_district",
            state,  # type: ignore[arg-type]
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["id"], "save_garrett")

    def test_case_insensitive(self) -> None:
        """Phrase matching is case insensitive."""
        state = MockState()
        config = create_test_config()
        state.extra["commitment_configs"] = {"save_garrett": config}

        result = check_commitment_phrase(
            "I PROMISE TO HELP you",
            "anywhere",
            state,  # type: ignore[arg-type]
        )
        self.assertIsNotNone(result)

    def test_no_matching_phrase(self) -> None:
        """No match when phrase not in text."""
        state = MockState()
        config = create_test_config()
        state.extra["commitment_configs"] = {"save_garrett": config}

        result = check_commitment_phrase(
            "I don't care about you",
            "anywhere",
            state,  # type: ignore[arg-type]
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
