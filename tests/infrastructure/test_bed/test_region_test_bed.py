"""
Tests for the Region Test Bed Framework

Verifies the test bed itself works correctly.
"""

import unittest
from pathlib import Path

from tests.infrastructure.test_bed.context_loaders import (
    CustomContextLoader,
    FreshContextLoader,
    InMemoryContextLoader,
)
from tests.infrastructure.test_bed.logger import InteractionLogger, LogEntry, LogLevel
from tests.infrastructure.test_bed.region_test_bed import AssertionError, RegionTestBed
from src.types import ActorId


# Path to a simple game for testing
SIMPLE_GAME_DIR = Path(__file__).parent.parent.parent.parent / "examples" / "simple_game"


class TestInteractionLogger(unittest.TestCase):
    """Test interaction logger."""

    def test_log_entry_creation(self) -> None:
        """Create and inspect log entry."""
        entry = LogEntry(
            turn=5,
            phase="command",
            action="take sword",
            state_before={"turn": 4},
            state_after={"turn": 5},
            result=None,
            issues=[],
        )

        self.assertEqual(entry.turn, 5)
        self.assertEqual(entry.action, "take sword")
        self.assertFalse(entry.has_issues())
        self.assertTrue(entry.has_state_change())

    def test_log_entry_with_issues(self) -> None:
        """Log entry with issues."""
        entry = LogEntry(
            turn=1,
            phase="turn_phase",
            action="npc_action",
            state_before={},
            state_after={},
            result=None,
            issues=["Invariant violated: trust < -6"],
        )

        self.assertTrue(entry.has_issues())
        self.assertFalse(entry.has_state_change())

    def test_logger_filters_by_level(self) -> None:
        """Logger filters entries based on level."""
        logger = InteractionLogger(LogLevel.ERRORS)

        # Add entry without issues
        logger.log(
            LogEntry(
                turn=1,
                phase="cmd",
                action="look",
                state_before={},
                state_after={"x": 1},
                result=None,
                issues=[],
            )
        )

        # Add entry with issues
        logger.log(
            LogEntry(
                turn=2,
                phase="cmd",
                action="bad",
                state_before={},
                state_after={},
                result=None,
                issues=["Error!"],
            )
        )

        # Only errors level should show 1 entry
        self.assertEqual(len(logger.get_entries()), 1)

        # Change level to see all
        logger.level = LogLevel.ALL
        self.assertEqual(len(logger.get_entries()), 2)

    def test_logger_get_issues(self) -> None:
        """Logger extracts issues."""
        logger = InteractionLogger()

        logger.log(
            LogEntry(
                turn=1,
                phase="cmd",
                action="x",
                state_before={},
                state_after={},
                result=None,
                issues=["Error 1"],
            )
        )
        logger.log(
            LogEntry(
                turn=2,
                phase="cmd",
                action="y",
                state_before={},
                state_after={},
                result=None,
                issues=["Error 2", "Error 3"],
            )
        )

        issues = logger.get_issues()
        self.assertEqual(len(issues), 3)
        self.assertEqual(issues[0], (1, "Error 1"))
        self.assertEqual(issues[1], (2, "Error 2"))


class TestFreshContextLoader(unittest.TestCase):
    """Test fresh context loader."""

    def test_load_simple_game(self) -> None:
        """Load simple game state."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        loader = FreshContextLoader(SIMPLE_GAME_DIR / "game_state.json")
        state = loader.load()

        self.assertIsNotNone(state)
        self.assertIn("player", state.actors)

    def test_missing_file_raises(self) -> None:
        """Missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            FreshContextLoader("/nonexistent/game_state.json")


class TestCustomContextLoader(unittest.TestCase):
    """Test custom context loader."""

    def test_modify_flags(self) -> None:
        """Apply custom flags."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        base = FreshContextLoader(SIMPLE_GAME_DIR / "game_state.json")
        loader = CustomContextLoader(base, flags={"custom_flag": True, "int_flag": 42})

        state = loader.load()

        self.assertEqual(state.extra["flags"]["custom_flag"], True)
        self.assertEqual(state.extra["flags"]["int_flag"], 42)

    def test_modify_trust(self) -> None:
        """Apply custom trust values."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        base = FreshContextLoader(SIMPLE_GAME_DIR / "game_state.json")
        loader = CustomContextLoader(base, trust_values={"player": 5})

        state = loader.load()

        player = state.actors[ActorId("player")]
        self.assertEqual(player.properties["trust"]["current"], 5)

    def test_modify_actor_location(self) -> None:
        """Apply custom actor locations."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        base = FreshContextLoader(SIMPLE_GAME_DIR / "game_state.json")

        # Get a valid location from the game
        state = base.load()
        if not state.locations:
            self.skipTest("No locations in simple_game")

        loc_id = state.locations[0].id
        loader = CustomContextLoader(base, actor_locations={"player": loc_id})

        state = loader.load()
        self.assertEqual(state.actors[ActorId("player")].location, loc_id)

    def test_description_includes_mods(self) -> None:
        """Description includes modification summary."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        base = FreshContextLoader(SIMPLE_GAME_DIR / "game_state.json")
        loader = CustomContextLoader(base, flags={"a": True}, trust_values={"player": 1})

        desc = loader.get_description()
        self.assertIn("1 flags", desc)
        self.assertIn("1 trust values", desc)


class TestInMemoryContextLoader(unittest.TestCase):
    """Test in-memory context loader."""

    def test_load_minimal_state(self) -> None:
        """Load minimal state from dict."""
        state_dict = {
            "metadata": {"title": "Test", "start_location": "loc_start"},
            "locations": [{"id": "loc_start", "name": "Start", "description": "Test"}],
            "items": [],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "Adventurer",  # Can't use "Player" - it's reserved
                    "description": "You",
                    "location": "loc_start",
                    "inventory": [],
                }
            },
            "locks": [],
        }

        loader = InMemoryContextLoader(state_dict, "Test state")
        state = loader.load()

        self.assertEqual(state.metadata.title, "Test")
        self.assertIn("player", state.actors)
        self.assertEqual(loader.get_description(), "Test state")


class TestRegionTestBed(unittest.TestCase):
    """Test the main test bed class."""

    def test_init_with_game_dir(self) -> None:
        """Initialize with game directory."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        bed = RegionTestBed(game_dir=SIMPLE_GAME_DIR)
        self.assertIsNotNone(bed._context_loader)

    def test_load_context(self) -> None:
        """Load context and access state."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        bed = RegionTestBed(game_dir=SIMPLE_GAME_DIR)
        bed.load_context()

        self.assertIsNotNone(bed.state)
        self.assertIn("player", bed.state.actors)

    def test_state_raises_without_context(self) -> None:
        """Accessing state without loading raises error."""
        bed = RegionTestBed()

        with self.assertRaises(RuntimeError):
            _ = bed.state

    def test_assert_flag_success(self) -> None:
        """assert_flag succeeds when flag matches."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        base = FreshContextLoader(SIMPLE_GAME_DIR / "game_state.json")
        loader = CustomContextLoader(base, flags={"test_flag": True})

        bed = RegionTestBed(context_loader=loader)
        bed.load_context()

        # Should not raise
        bed.assert_flag("test_flag", True)

    def test_assert_flag_failure(self) -> None:
        """assert_flag fails when flag doesn't match."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        base = FreshContextLoader(SIMPLE_GAME_DIR / "game_state.json")
        loader = CustomContextLoader(base, flags={"test_flag": False})

        bed = RegionTestBed(context_loader=loader)
        bed.load_context()

        with self.assertRaises(AssertionError):
            bed.assert_flag("test_flag", True)

    def test_assert_location(self) -> None:
        """assert_location works correctly."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        bed = RegionTestBed(game_dir=SIMPLE_GAME_DIR)
        bed.load_context()

        # Get player's actual location
        player_loc = bed.state.actors[ActorId("player")].location

        # Should pass
        bed.assert_location("player", player_loc)

        # Should fail
        with self.assertRaises(AssertionError):
            bed.assert_location("player", "nonexistent_location")

    def test_get_current_turn(self) -> None:
        """get_current_turn returns turn count."""
        if not SIMPLE_GAME_DIR.exists():
            self.skipTest("simple_game not found")

        bed = RegionTestBed(game_dir=SIMPLE_GAME_DIR)
        bed.load_context()

        # Should return 0 or whatever initial turn is
        turn = bed.get_current_turn()
        self.assertIsInstance(turn, int)
        self.assertGreaterEqual(turn, 0)

    def test_logger_available(self) -> None:
        """Logger is available on test bed."""
        bed = RegionTestBed(log_level="all")

        self.assertIsNotNone(bed.logger)
        self.assertEqual(bed.logger.level, LogLevel.ALL)


if __name__ == "__main__":
    unittest.main()
