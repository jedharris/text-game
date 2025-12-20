"""Tests for pack_mirroring infrastructure dispatcher."""
from src.types import ActorId

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from examples.big_game.behaviors.infrastructure.dispatcher_utils import clear_handler_cache
from examples.big_game.behaviors.infrastructure.pack_mirroring import on_leader_state_change
from src.behavior_manager import EventResult


class MockEntity:
    """Mock entity for testing."""

    def __init__(self, entity_id: str, properties: dict | None = None) -> None:
        self.id = entity_id
        self.properties = properties or {}


class MockState:
    """Mock state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}
        self.actors: dict = {}


class MockAccessor:
    """Mock accessor for testing."""

    def __init__(self) -> None:
        self.state = MockState()


class TestPackMirroringBasic(unittest.TestCase):
    """Tests for basic pack mirroring behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_entity_without_properties(self) -> None:
        """Entity without properties returns allow with no message."""
        entity = "string_entity"
        context = {"new_state": "hostile"}

        result = on_leader_state_change(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_entity_without_pack_behavior(self) -> None:
        """Entity without pack_behavior returns allow with no message."""
        entity = MockEntity("npc_guard", {})
        context = {"new_state": "hostile"}

        result = on_leader_state_change(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_pack_behavior_without_mirroring(self) -> None:
        """Pack without mirroring enabled returns allow with no message."""
        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "followers": ["npc_beta_wolf"],
                    # pack_follows_leader_state not set
                }
            },
        )
        context = {"new_state": "hostile"}

        result = on_leader_state_change(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_no_new_state_in_context(self) -> None:
        """No new_state in context returns allow with no message."""
        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": ["npc_beta_wolf"],
                }
            },
        )
        context: dict[str, Any] = {}

        result = on_leader_state_change(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_empty_followers_list(self) -> None:
        """Empty followers list returns allow with no message."""
        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": [],
                }
            },
        )
        context = {"new_state": "hostile"}

        result = on_leader_state_change(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)


class TestPackMirroringDataDriven(unittest.TestCase):
    """Tests for data-driven pack mirroring."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_single_follower_mirrors_state(self) -> None:
        """Single follower mirrors leader state."""
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {
                "state_machine": {
                    "initial": "neutral",
                    "current": "neutral",
                    "states": ["neutral", "hostile"],
                }
            },
        )
        self.accessor.state.actors[ActorId("npc_beta_wolf")] = beta_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": ["npc_beta_wolf"],
                }
            },
        )
        context = {"new_state": "hostile"}

        on_leader_state_change(entity, self.accessor, context)

        self.assertEqual(beta_wolf.properties["state_machine"]["current"], "hostile")

    def test_multiple_followers_mirror_state(self) -> None:
        """Multiple followers all mirror leader state."""
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {
                "state_machine": {
                    "initial": "neutral",
                    "current": "neutral",
                    "states": ["neutral", "hostile"],
                }
            },
        )
        gamma_wolf = MockEntity(
            "npc_gamma_wolf",
            {
                "state_machine": {
                    "initial": "neutral",
                    "current": "neutral",
                    "states": ["neutral", "hostile"],
                }
            },
        )
        self.accessor.state.actors[ActorId("npc_beta_wolf")] = beta_wolf
        self.accessor.state.actors[ActorId("npc_gamma_wolf")] = gamma_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": ["npc_beta_wolf", "npc_gamma_wolf"],
                }
            },
        )
        context = {"new_state": "hostile"}

        on_leader_state_change(entity, self.accessor, context)

        self.assertEqual(beta_wolf.properties["state_machine"]["current"], "hostile")
        self.assertEqual(gamma_wolf.properties["state_machine"]["current"], "hostile")

    def test_dynamic_state_added_to_follower(self) -> None:
        """New states are added to follower state machine if missing."""
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {
                "state_machine": {
                    "initial": "neutral",
                    "current": "neutral",
                    "states": ["neutral", "hostile"],
                }
            },
        )
        self.accessor.state.actors[ActorId("npc_beta_wolf")] = beta_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": ["npc_beta_wolf"],
                }
            },
        )
        context = {"new_state": "confused"}  # Not in original states

        on_leader_state_change(entity, self.accessor, context)

        self.assertIn("confused", beta_wolf.properties["state_machine"]["states"])
        self.assertEqual(beta_wolf.properties["state_machine"]["current"], "confused")

    def test_pack_follows_alpha_state_legacy(self) -> None:
        """Legacy pack_follows_alpha_state property works."""
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {
                "state_machine": {
                    "initial": "neutral",
                    "current": "neutral",
                    "states": ["neutral", "hostile"],
                }
            },
        )
        self.accessor.state.actors[ActorId("npc_beta_wolf")] = beta_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "pack_follows_alpha_state": True,  # Legacy name
                    "followers": ["npc_beta_wolf"],
                }
            },
        )
        context = {"new_state": "hostile"}

        on_leader_state_change(entity, self.accessor, context)

        self.assertEqual(beta_wolf.properties["state_machine"]["current"], "hostile")

    def test_missing_follower_ignored(self) -> None:
        """Missing followers are silently ignored."""
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {
                "state_machine": {
                    "initial": "neutral",
                    "current": "neutral",
                    "states": ["neutral", "hostile"],
                }
            },
        )
        self.accessor.state.actors[ActorId("npc_beta_wolf")] = beta_wolf
        # npc_gamma_wolf is NOT in actors

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": ["npc_beta_wolf", "npc_gamma_wolf"],
                }
            },
        )
        context = {"new_state": "hostile"}

        # Should not raise
        on_leader_state_change(entity, self.accessor, context)

        self.assertEqual(beta_wolf.properties["state_machine"]["current"], "hostile")

    def test_follower_without_state_machine_ignored(self) -> None:
        """Followers without state_machine are silently ignored."""
        beta_wolf = MockEntity("npc_beta_wolf", {})  # No state_machine
        self.accessor.state.actors[ActorId("npc_beta_wolf")] = beta_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": ["npc_beta_wolf"],
                }
            },
        )
        context = {"new_state": "hostile"}

        # Should not raise
        result = on_leader_state_change(entity, self.accessor, context)

        self.assertTrue(result.allow)


class TestPackMirroringHandlerEscapeHatch(unittest.TestCase):
    """Tests for handler escape hatch in pack_mirroring."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_handler_called(self) -> None:
        """When handler is specified, it is called."""
        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "handler": "examples.big_game.behaviors.regions.beast_wilds.wolf_pack:on_alpha_state_change"
                }
            },
        )
        context = {"new_state": "hostile"}

        handler_result = EventResult(allow=True, feedback="Handler response")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "examples.big_game.behaviors.infrastructure.pack_mirroring.load_handler",
            return_value=mock_handler,
        ):
            result = on_leader_state_change(entity, self.accessor, context)

        self.assertEqual(result.feedback, "Handler response")
        mock_handler.assert_called_once_with(entity, self.accessor, context)

    def test_handler_load_failure_falls_through(self) -> None:
        """When handler fails to load, data-driven processing continues."""
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {
                "state_machine": {
                    "initial": "neutral",
                    "current": "neutral",
                    "states": ["neutral", "hostile"],
                }
            },
        )
        self.accessor.state.actors[ActorId("npc_beta_wolf")] = beta_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "pack_behavior": {
                    "handler": "invalid.module:nonexistent",
                    "pack_follows_leader_state": True,
                    "followers": ["npc_beta_wolf"],
                }
            },
        )
        context = {"new_state": "hostile"}

        on_leader_state_change(entity, self.accessor, context)

        self.assertEqual(beta_wolf.properties["state_machine"]["current"], "hostile")


if __name__ == "__main__":
    unittest.main()
