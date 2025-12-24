"""Tests for death_reactions infrastructure dispatcher."""
from src.types import ActorId

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import clear_handler_cache
from examples.big_game.behaviors.shared.infrastructure.death_reactions import on_entity_death
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
        self.game_state = MockState()


class TestDeathReactionsBasic(unittest.TestCase):
    """Tests for basic death reaction behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_entity_without_properties(self) -> None:
        """Entity without properties returns allow with no message."""
        entity = "string_entity"
        context: dict[str, Any] = {}

        result = on_entity_death(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_entity_without_death_reactions(self) -> None:
        """Entity without death_reactions returns allow with no message."""
        entity = MockEntity("npc_guard", {})
        context: dict[str, Any] = {}

        result = on_entity_death(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)


class TestDeathReactionsDataDriven(unittest.TestCase):
    """Tests for data-driven death reactions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_set_flags(self) -> None:
        """Death reaction sets flags in game state."""
        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "death_reactions": {
                    "set_flags": {"alpha_wolf_dead": True, "pack_leaderless": True}
                }
            },
        )
        context: dict[str, Any] = {}

        on_entity_death(entity, self.accessor, context)

        self.assertTrue(self.accessor.game_state.extra.get("alpha_wolf_dead"))
        self.assertTrue(self.accessor.game_state.extra.get("pack_leaderless"))

    def test_death_message(self) -> None:
        """Death reaction returns configured message."""
        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "death_reactions": {
                    "message": "The pack howls in mourning."
                }
            },
        )
        context: dict[str, Any] = {}

        result = on_entity_death(entity, self.accessor, context)

        self.assertEqual(result.feedback, "The pack howls in mourning.")

    def test_trust_changes_on_other_entities(self) -> None:
        """Death reaction applies trust changes to other entities."""
        # Set up the beta wolf in state
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {"trust_state": {"current": 2, "floor": -5, "ceiling": 5}},
        )
        self.accessor.game_state.actors[ActorId("npc_beta_wolf")] = beta_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "death_reactions": {
                    "trust_changes": {"npc_beta_wolf": -3}
                }
            },
        )
        context: dict[str, Any] = {}

        on_entity_death(entity, self.accessor, context)

        self.assertEqual(beta_wolf.properties["trust_state"]["current"], -1)

    def test_trust_changes_respects_floor(self) -> None:
        """Trust changes respect floor limit."""
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {"trust_state": {"current": 0, "floor": -2, "ceiling": 5}},
        )
        self.accessor.game_state.actors[ActorId("npc_beta_wolf")] = beta_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "death_reactions": {
                    "trust_changes": {"npc_beta_wolf": -10}
                }
            },
        )
        context: dict[str, Any] = {}

        on_entity_death(entity, self.accessor, context)

        self.assertEqual(beta_wolf.properties["trust_state"]["current"], -2)

    def test_trigger_state_changes(self) -> None:
        """Death reaction triggers state changes on other entities."""
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {
                "state_machine": {
                    "initial": "following",
                    "current": "following",
                    "states": ["following", "hostile", "mourning"],
                }
            },
        )
        self.accessor.game_state.actors[ActorId("npc_beta_wolf")] = beta_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "death_reactions": {
                    "trigger_state_changes": {"npc_beta_wolf": "hostile"}
                }
            },
        )
        context: dict[str, Any] = {}

        on_entity_death(entity, self.accessor, context)

        self.assertEqual(beta_wolf.properties["state_machine"]["current"], "hostile")

    def test_multiple_state_changes(self) -> None:
        """Death reaction can trigger multiple state changes."""
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {
                "state_machine": {
                    "initial": "following",
                    "current": "following",
                    "states": ["following", "hostile"],
                }
            },
        )
        gamma_wolf = MockEntity(
            "npc_gamma_wolf",
            {
                "state_machine": {
                    "initial": "following",
                    "current": "following",
                    "states": ["following", "fleeing"],
                }
            },
        )
        self.accessor.game_state.actors[ActorId("npc_beta_wolf")] = beta_wolf
        self.accessor.game_state.actors[ActorId("npc_gamma_wolf")] = gamma_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "death_reactions": {
                    "trigger_state_changes": {
                        "npc_beta_wolf": "hostile",
                        "npc_gamma_wolf": "fleeing",
                    }
                }
            },
        )
        context: dict[str, Any] = {}

        on_entity_death(entity, self.accessor, context)

        self.assertEqual(beta_wolf.properties["state_machine"]["current"], "hostile")
        self.assertEqual(gamma_wolf.properties["state_machine"]["current"], "fleeing")

    def test_combined_effects(self) -> None:
        """Death reaction can combine flags, trust, state changes, message."""
        beta_wolf = MockEntity(
            "npc_beta_wolf",
            {
                "trust_state": {"current": 3, "floor": -5, "ceiling": 5},
                "state_machine": {
                    "initial": "following",
                    "current": "following",
                    "states": ["following", "hostile"],
                },
            },
        )
        self.accessor.game_state.actors[ActorId("npc_beta_wolf")] = beta_wolf

        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "death_reactions": {
                    "set_flags": {"alpha_dead": True},
                    "trust_changes": {"npc_beta_wolf": -2},
                    "trigger_state_changes": {"npc_beta_wolf": "hostile"},
                    "message": "The alpha falls. The pack is changed forever.",
                }
            },
        )
        context: dict[str, Any] = {}

        result = on_entity_death(entity, self.accessor, context)

        self.assertTrue(self.accessor.game_state.extra.get("alpha_dead"))
        self.assertEqual(beta_wolf.properties["trust_state"]["current"], 1)
        self.assertEqual(beta_wolf.properties["state_machine"]["current"], "hostile")
        self.assertEqual(result.feedback, "The alpha falls. The pack is changed forever.")

    def test_missing_target_entity_ignored(self) -> None:
        """Trust/state changes for missing entities are ignored."""
        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "death_reactions": {
                    "trust_changes": {"npc_nonexistent": -5},
                    "trigger_state_changes": {"npc_nonexistent": "hostile"},
                    "message": "The alpha falls.",
                }
            },
        )
        context: dict[str, Any] = {}

        # Should not raise, just ignore missing entities
        result = on_entity_death(entity, self.accessor, context)

        self.assertEqual(result.feedback, "The alpha falls.")


class TestDeathReactionsHandlerEscapeHatch(unittest.TestCase):
    """Tests for handler escape hatch in death_reactions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_handler_called(self) -> None:
        """When handler is specified, it is called."""
        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "death_reactions": {
                    "handler": "examples.big_game.behaviors.regions.beast_wilds.wolf_pack:on_alpha_death"
                }
            },
        )
        context: dict[str, Any] = {}

        handler_result = EventResult(allow=True, feedback="Handler response")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "examples.big_game.behaviors.shared.infrastructure.death_reactions.load_handler",
            return_value=mock_handler,
        ):
            result = on_entity_death(entity, self.accessor, context)

        self.assertEqual(result.feedback, "Handler response")
        mock_handler.assert_called_once_with(entity, self.accessor, context)

    def test_handler_load_failure_falls_through(self) -> None:
        """When handler fails to load, data-driven processing continues."""
        entity = MockEntity(
            "npc_alpha_wolf",
            {
                "death_reactions": {
                    "handler": "invalid.module:nonexistent",
                    "set_flags": {"alpha_dead": True},
                    "message": "Fallback death message.",
                }
            },
        )
        context: dict[str, Any] = {}

        result = on_entity_death(entity, self.accessor, context)

        self.assertTrue(self.accessor.game_state.extra.get("alpha_dead"))
        self.assertEqual(result.feedback, "Fallback death message.")


if __name__ == "__main__":
    unittest.main()
