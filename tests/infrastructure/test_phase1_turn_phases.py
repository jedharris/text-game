"""
Phase 1 Turn Phase Orchestration Tests

Tests for turn phase hook ordering and game-declared extra phases.
"""

import unittest
from unittest.mock import MagicMock, patch

from src import hooks
from src.llm_protocol import LLMProtocolHandler


class MockMetadata:
    """Mock metadata for testing."""

    def __init__(self, extra_turn_phases: list[str] | None = None) -> None:
        self.title = "Test"
        self.extra_turn_phases = extra_turn_phases or []


class MockGameState:
    """Mock game state for testing."""

    def __init__(self, extra_turn_phases: list[str] | None = None) -> None:
        self.metadata = MockMetadata(extra_turn_phases)
        self.extra: dict = {"turn_count": 0}

    def increment_turn(self) -> None:
        """Increment turn counter."""
        self.extra["turn_count"] = self.extra.get("turn_count", 0) + 1


class TestGetTurnPhaseHooks(unittest.TestCase):
    """Test turn phase hook ordering."""

    def test_base_phases_only(self) -> None:
        """Without extra phases, only base phases are returned."""
        state = MockGameState()
        handler = LLMProtocolHandler(state, MagicMock())  # type: ignore[arg-type]

        phases = handler._get_turn_phase_hooks()
        self.assertEqual(phases, [
            hooks.NPC_ACTION,
            hooks.ENVIRONMENTAL_EFFECT,
            hooks.CONDITION_TICK,
            hooks.DEATH_CHECK,
        ])

    def test_extra_phases_prepended(self) -> None:
        """Extra phases declared in metadata are prepended."""
        state = MockGameState(extra_turn_phases=[
            hooks.TURN_PHASE_SCHEDULED,
            hooks.TURN_PHASE_COMMITMENT,
        ])
        handler = LLMProtocolHandler(state, MagicMock())  # type: ignore[arg-type]

        phases = handler._get_turn_phase_hooks()
        self.assertEqual(phases, [
            hooks.TURN_PHASE_SCHEDULED,
            hooks.TURN_PHASE_COMMITMENT,
            hooks.NPC_ACTION,
            hooks.ENVIRONMENTAL_EFFECT,
            hooks.CONDITION_TICK,
            hooks.DEATH_CHECK,
        ])

    def test_all_infrastructure_phases(self) -> None:
        """All infrastructure phases can be declared."""
        state = MockGameState(extra_turn_phases=[
            hooks.TURN_PHASE_SCHEDULED,
            hooks.TURN_PHASE_COMMITMENT,
            hooks.TURN_PHASE_GOSSIP,
            hooks.TURN_PHASE_SPREAD,
        ])
        handler = LLMProtocolHandler(state, MagicMock())  # type: ignore[arg-type]

        phases = handler._get_turn_phase_hooks()
        self.assertEqual(len(phases), 8)  # 4 extra + 4 base
        # Extra phases come first
        self.assertEqual(phases[0], hooks.TURN_PHASE_SCHEDULED)
        self.assertEqual(phases[1], hooks.TURN_PHASE_COMMITMENT)
        self.assertEqual(phases[2], hooks.TURN_PHASE_GOSSIP)
        self.assertEqual(phases[3], hooks.TURN_PHASE_SPREAD)
        # Base phases follow
        self.assertEqual(phases[4], hooks.NPC_ACTION)

    def test_empty_extra_phases(self) -> None:
        """Empty extra_turn_phases list has no effect."""
        state = MockGameState(extra_turn_phases=[])
        handler = LLMProtocolHandler(state, MagicMock())  # type: ignore[arg-type]

        phases = handler._get_turn_phase_hooks()
        self.assertEqual(phases, handler.BASE_TURN_PHASE_HOOKS)


class TestHookConstants(unittest.TestCase):
    """Test hook constants are defined."""

    def test_base_hooks_defined(self) -> None:
        """Base turn phase hooks are defined."""
        self.assertEqual(hooks.NPC_ACTION, "npc_action")
        self.assertEqual(hooks.ENVIRONMENTAL_EFFECT, "environmental_effect")
        self.assertEqual(hooks.CONDITION_TICK, "condition_tick")
        self.assertEqual(hooks.DEATH_CHECK, "death_check")

    def test_infrastructure_hooks_defined(self) -> None:
        """Infrastructure turn phase hooks are defined."""
        self.assertEqual(hooks.TURN_PHASE_SCHEDULED, "turn_phase_scheduled")
        self.assertEqual(hooks.TURN_PHASE_COMMITMENT, "turn_phase_commitment")
        self.assertEqual(hooks.TURN_PHASE_GOSSIP, "turn_phase_gossip")
        self.assertEqual(hooks.TURN_PHASE_SPREAD, "turn_phase_spread")


if __name__ == "__main__":
    unittest.main()
