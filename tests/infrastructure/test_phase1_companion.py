"""
Phase 1 Companion System Tests

Tests for companion management, following, waiting, and comfort levels.
"""

import unittest

from src.infrastructure_types import CompanionComfort, CompanionState
from src.infrastructure_utils import (
    add_companion,
    check_companion_comfort,
    get_active_companions,
    get_companion,
    get_following_companions,
    remove_companion,
    set_companion_following,
    set_companion_waiting,
    update_companion_comfort,
)


class MockState:
    """Mock game state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}


class MockActor:
    """Mock actor for testing."""

    def __init__(self, properties: dict | None = None) -> None:
        self.properties = properties or {}


class TestAddCompanion(unittest.TestCase):
    """Test adding companions."""

    def test_add_companion_basic(self) -> None:
        """Add a basic companion."""
        state = MockState()
        companion = add_companion(state, "sira")  # type: ignore[arg-type]

        self.assertIsNotNone(companion)
        assert companion is not None
        self.assertEqual(companion["actor_id"], "sira")
        self.assertTrue(companion["following"])
        self.assertEqual(companion["comfort_in_current"], CompanionComfort.COMFORTABLE)

    def test_add_companion_appears_in_list(self) -> None:
        """Added companion appears in companions list."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]

        companions = get_active_companions(state)  # type: ignore[arg-type]
        self.assertEqual(len(companions), 1)
        self.assertEqual(companions[0]["actor_id"], "sira")

    def test_add_duplicate_companion_fails(self) -> None:
        """Cannot add the same companion twice."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]
        result = add_companion(state, "sira")  # type: ignore[arg-type]

        self.assertIsNone(result)
        companions = get_active_companions(state)  # type: ignore[arg-type]
        self.assertEqual(len(companions), 1)

    def test_add_multiple_companions(self) -> None:
        """Can add multiple different companions."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]
        add_companion(state, "salamander")  # type: ignore[arg-type]

        companions = get_active_companions(state)  # type: ignore[arg-type]
        self.assertEqual(len(companions), 2)


class TestGetCompanion(unittest.TestCase):
    """Test finding companions."""

    def test_get_existing_companion(self) -> None:
        """Find companion that exists."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]

        companion = get_companion(state, "sira")  # type: ignore[arg-type]
        self.assertIsNotNone(companion)
        assert companion is not None
        self.assertEqual(companion["actor_id"], "sira")

    def test_get_missing_companion(self) -> None:
        """Find companion that doesn't exist returns None."""
        state = MockState()

        companion = get_companion(state, "nonexistent")  # type: ignore[arg-type]
        self.assertIsNone(companion)


class TestRemoveCompanion(unittest.TestCase):
    """Test removing companions."""

    def test_remove_existing_companion(self) -> None:
        """Remove companion that exists."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]

        result = remove_companion(state, "sira")  # type: ignore[arg-type]
        self.assertTrue(result)

        companion = get_companion(state, "sira")  # type: ignore[arg-type]
        self.assertIsNone(companion)

    def test_remove_nonexistent_companion(self) -> None:
        """Remove companion that doesn't exist returns False."""
        state = MockState()

        result = remove_companion(state, "nonexistent")  # type: ignore[arg-type]
        self.assertFalse(result)


class TestSetCompanionFollowing(unittest.TestCase):
    """Test setting companion following state."""

    def test_set_following_true(self) -> None:
        """Set companion to following."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]
        set_companion_following(state, "sira", False)  # type: ignore[arg-type]

        result = set_companion_following(state, "sira", True)  # type: ignore[arg-type]
        self.assertTrue(result)

        companion = get_companion(state, "sira")  # type: ignore[arg-type]
        assert companion is not None
        self.assertTrue(companion["following"])

    def test_set_following_false(self) -> None:
        """Set companion to not following."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]

        result = set_companion_following(state, "sira", False)  # type: ignore[arg-type]
        self.assertTrue(result)

        companion = get_companion(state, "sira")  # type: ignore[arg-type]
        assert companion is not None
        self.assertFalse(companion["following"])

    def test_set_following_nonexistent(self) -> None:
        """Set following for nonexistent companion returns False."""
        state = MockState()

        result = set_companion_following(state, "nonexistent", True)  # type: ignore[arg-type]
        self.assertFalse(result)


class TestSetCompanionWaiting(unittest.TestCase):
    """Test setting companion to wait."""

    def test_set_waiting(self) -> None:
        """Set companion to wait at location."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]

        result = set_companion_waiting(state, "sira", "beast_wilds_clearing")  # type: ignore[arg-type]
        self.assertTrue(result)

        companion = get_companion(state, "sira")  # type: ignore[arg-type]
        assert companion is not None
        self.assertFalse(companion["following"])
        self.assertEqual(companion["waiting_at"], "beast_wilds_clearing")

    def test_set_waiting_nonexistent(self) -> None:
        """Set waiting for nonexistent companion returns False."""
        state = MockState()

        result = set_companion_waiting(state, "nonexistent", "anywhere")  # type: ignore[arg-type]
        self.assertFalse(result)


class TestUpdateCompanionComfort(unittest.TestCase):
    """Test updating companion comfort level."""

    def test_update_comfort(self) -> None:
        """Update companion comfort level."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]

        result = update_companion_comfort(state, "sira", CompanionComfort.UNCOMFORTABLE)  # type: ignore[arg-type]
        self.assertTrue(result)

        companion = get_companion(state, "sira")  # type: ignore[arg-type]
        assert companion is not None
        self.assertEqual(companion["comfort_in_current"], CompanionComfort.UNCOMFORTABLE)

    def test_update_comfort_nonexistent(self) -> None:
        """Update comfort for nonexistent companion returns False."""
        state = MockState()

        result = update_companion_comfort(state, "nonexistent", CompanionComfort.IMPOSSIBLE)  # type: ignore[arg-type]
        self.assertFalse(result)


class TestGetFollowingCompanions(unittest.TestCase):
    """Test getting following companions."""

    def test_get_following_all_following(self) -> None:
        """Get companions when all are following."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]
        add_companion(state, "salamander")  # type: ignore[arg-type]

        following = get_following_companions(state)  # type: ignore[arg-type]
        self.assertEqual(len(following), 2)

    def test_get_following_some_waiting(self) -> None:
        """Get companions when some are waiting."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]
        add_companion(state, "salamander")  # type: ignore[arg-type]
        set_companion_following(state, "sira", False)  # type: ignore[arg-type]

        following = get_following_companions(state)  # type: ignore[arg-type]
        self.assertEqual(len(following), 1)
        self.assertEqual(following[0]["actor_id"], "salamander")

    def test_get_following_none_following(self) -> None:
        """Get companions when none are following."""
        state = MockState()
        add_companion(state, "sira")  # type: ignore[arg-type]
        set_companion_following(state, "sira", False)  # type: ignore[arg-type]

        following = get_following_companions(state)  # type: ignore[arg-type]
        self.assertEqual(len(following), 0)


class TestCheckCompanionComfort(unittest.TestCase):
    """Test checking companion comfort at locations."""

    def test_comfortable_by_default(self) -> None:
        """Actor without restrictions is comfortable everywhere."""
        actor = MockActor()

        comfort = check_companion_comfort(actor, "anywhere")  # type: ignore[arg-type]
        self.assertEqual(comfort, CompanionComfort.COMFORTABLE)

    def test_impossible_location(self) -> None:
        """Actor refuses to go to impossible locations."""
        actor = MockActor({
            "comfort_restrictions": {
                "impossible": ["frozen_reaches/*", "sunken_district/*"],
            }
        })

        comfort = check_companion_comfort(actor, "frozen_reaches_glacier")  # type: ignore[arg-type]
        self.assertEqual(comfort, CompanionComfort.IMPOSSIBLE)

    def test_uncomfortable_location(self) -> None:
        """Actor is uncomfortable in certain locations."""
        actor = MockActor({
            "comfort_restrictions": {
                "uncomfortable": ["fungal_depths/*"],
            }
        })

        comfort = check_companion_comfort(actor, "fungal_depths_cavern")  # type: ignore[arg-type]
        self.assertEqual(comfort, CompanionComfort.UNCOMFORTABLE)

    def test_impossible_takes_precedence(self) -> None:
        """Impossible takes precedence over uncomfortable."""
        actor = MockActor({
            "comfort_restrictions": {
                "impossible": ["frozen_reaches/*"],
                "uncomfortable": ["frozen_reaches/*"],
            }
        })

        comfort = check_companion_comfort(actor, "frozen_reaches_peak")  # type: ignore[arg-type]
        self.assertEqual(comfort, CompanionComfort.IMPOSSIBLE)

    def test_comfortable_when_not_matching(self) -> None:
        """Actor is comfortable when no patterns match."""
        actor = MockActor({
            "comfort_restrictions": {
                "impossible": ["frozen_reaches/*"],
                "uncomfortable": ["fungal_depths/*"],
            }
        })

        comfort = check_companion_comfort(actor, "beast_wilds_clearing")  # type: ignore[arg-type]
        self.assertEqual(comfort, CompanionComfort.COMFORTABLE)


if __name__ == "__main__":
    unittest.main()
