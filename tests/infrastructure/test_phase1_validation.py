"""
Phase 1 Validation Module Tests

Tests for infrastructure validation functions.
"""
from src.types import ActorId

import unittest
from dataclasses import dataclass, field
from typing import Any

from src.infrastructure_types import TemperatureZone, TurnNumber, WaterLevel
from src.infrastructure_utils import (
    validate_commitment_configs,
    validate_companion_restrictions,
    validate_gossip_references,
    validate_infrastructure,
    validate_spreads,
    validate_state_machines,
    validate_zone_consistency,
)


@dataclass
class MockActor:
    """Mock actor for testing."""

    id: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class MockLocation:
    """Mock location for testing."""

    id: str
    properties: dict[str, Any] = field(default_factory=dict)


class MockState:
    """Mock game state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}
        self.actors: dict[str, MockActor] = {}
        self.locations: list[MockLocation] = []


class TestValidateCommitmentConfigs(unittest.TestCase):
    """Test commitment config validation."""

    def test_valid_config(self) -> None:
        """Valid config produces no errors."""
        state = MockState()
        state.extra["commitment_configs"] = {
            "save_garrett": {
                "id": "save_garrett",
                "target_npc": "garrett",
                "goal": "Save Garrett",
                "trigger_phrases": ["I'll save you"],
            }
        }

        errors = validate_commitment_configs(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])

    def test_missing_id(self) -> None:
        """Missing id field produces error."""
        state = MockState()
        state.extra["commitment_configs"] = {
            "save_garrett": {
                "target_npc": "garrett",
                "goal": "Save Garrett",
                "trigger_phrases": ["I'll save you"],
            }
        }

        errors = validate_commitment_configs(state)  # type: ignore[arg-type]
        self.assertEqual(len(errors), 1)
        self.assertIn("missing 'id'", errors[0])

    def test_mismatched_id(self) -> None:
        """Mismatched id produces error."""
        state = MockState()
        state.extra["commitment_configs"] = {
            "save_garrett": {
                "id": "different_id",
                "target_npc": "garrett",
                "goal": "Save Garrett",
                "trigger_phrases": ["I'll save you"],
            }
        }

        errors = validate_commitment_configs(state)  # type: ignore[arg-type]
        self.assertEqual(len(errors), 1)
        self.assertIn("mismatched id", errors[0])

    def test_missing_target_npc(self) -> None:
        """Missing target_npc produces error."""
        state = MockState()
        state.extra["commitment_configs"] = {
            "test": {
                "id": "test",
                "goal": "Test",
                "trigger_phrases": ["test"],
            }
        }

        errors = validate_commitment_configs(state)  # type: ignore[arg-type]
        self.assertIn("missing 'target_npc'", errors[0])

    def test_empty_trigger_phrases(self) -> None:
        """Empty trigger_phrases produces error."""
        state = MockState()
        state.extra["commitment_configs"] = {
            "test": {
                "id": "test",
                "target_npc": "npc",
                "goal": "Test",
                "trigger_phrases": [],
            }
        }

        errors = validate_commitment_configs(state)  # type: ignore[arg-type]
        self.assertIn("cannot be empty", errors[0])

    def test_invalid_base_timer(self) -> None:
        """Invalid base_timer produces error."""
        state = MockState()
        state.extra["commitment_configs"] = {
            "test": {
                "id": "test",
                "target_npc": "npc",
                "goal": "Test",
                "trigger_phrases": ["test"],
                "base_timer": -5,
            }
        }

        errors = validate_commitment_configs(state)  # type: ignore[arg-type]
        self.assertIn("positive integer", errors[0])

    def test_no_configs(self) -> None:
        """No configs produces no errors."""
        state = MockState()

        errors = validate_commitment_configs(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])


class TestValidateStateMachines(unittest.TestCase):
    """Test state machine validation."""

    def test_valid_state_machine(self) -> None:
        """Valid state machine produces no errors."""
        state = MockState()
        state.actors[ActorId("npc")] = MockActor(
            id="npc",
            properties={
                "state_machine": {
                    "states": ["alive", "injured", "dead"],
                    "initial": "alive",
                }
            },
        )

        errors = validate_state_machines(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])

    def test_missing_states(self) -> None:
        """Missing states field produces error."""
        state = MockState()
        state.actors[ActorId("npc")] = MockActor(
            id="npc",
            properties={"state_machine": {"initial": "alive"}},
        )

        errors = validate_state_machines(state)  # type: ignore[arg-type]
        self.assertIn("missing 'states'", errors[0])

    def test_missing_initial(self) -> None:
        """Missing initial field produces error."""
        state = MockState()
        state.actors[ActorId("npc")] = MockActor(
            id="npc",
            properties={"state_machine": {"states": ["alive", "dead"]}},
        )

        errors = validate_state_machines(state)  # type: ignore[arg-type]
        self.assertIn("missing 'initial'", errors[0])

    def test_initial_not_in_states(self) -> None:
        """Initial state not in states list produces error."""
        state = MockState()
        state.actors[ActorId("npc")] = MockActor(
            id="npc",
            properties={
                "state_machine": {
                    "states": ["alive", "dead"],
                    "initial": "sleeping",
                }
            },
        )

        errors = validate_state_machines(state)  # type: ignore[arg-type]
        self.assertIn("not in states", errors[0])

    def test_current_not_in_states(self) -> None:
        """Current state not in states list produces error."""
        state = MockState()
        state.actors[ActorId("npc")] = MockActor(
            id="npc",
            properties={
                "state_machine": {
                    "states": ["alive", "dead"],
                    "initial": "alive",
                    "current": "invisible",
                }
            },
        )

        errors = validate_state_machines(state)  # type: ignore[arg-type]
        self.assertIn("'current' state", errors[0])

    def test_actor_without_state_machine(self) -> None:
        """Actor without state machine produces no errors."""
        state = MockState()
        state.actors[ActorId("npc")] = MockActor(id="npc", properties={})

        errors = validate_state_machines(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])


class TestValidateSpreads(unittest.TestCase):
    """Test spread validation."""

    def test_valid_spread(self) -> None:
        """Valid spread produces no errors."""
        state = MockState()
        state.extra["environmental_spreads"] = {
            "cold": {
                "halt_flag": "cold_halted",
                "milestones": [
                    {"turn": TurnNumber(10), "effects": []},
                    {"turn": TurnNumber(20), "effects": []},
                ],
                "active": True,
            }
        }

        errors = validate_spreads(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])

    def test_missing_halt_flag(self) -> None:
        """Missing halt_flag produces error."""
        state = MockState()
        state.extra["environmental_spreads"] = {
            "cold": {
                "milestones": [],
                "active": True,
            }
        }

        errors = validate_spreads(state)  # type: ignore[arg-type]
        self.assertIn("missing 'halt_flag'", errors[0])

    def test_missing_milestones(self) -> None:
        """Missing milestones produces error."""
        state = MockState()
        state.extra["environmental_spreads"] = {
            "cold": {"halt_flag": "cold_halted", "active": True}
        }

        errors = validate_spreads(state)  # type: ignore[arg-type]
        self.assertIn("missing 'milestones'", errors[0])

    def test_milestones_not_ascending(self) -> None:
        """Non-ascending milestones produce error."""
        state = MockState()
        state.extra["environmental_spreads"] = {
            "cold": {
                "halt_flag": "cold_halted",
                "milestones": [
                    {"turn": TurnNumber(20), "effects": []},
                    {"turn": TurnNumber(10), "effects": []},  # Out of order
                ],
                "active": True,
            }
        }

        errors = validate_spreads(state)  # type: ignore[arg-type]
        self.assertIn("not in ascending order", errors[0])

    def test_milestone_missing_turn(self) -> None:
        """Milestone missing turn produces error."""
        state = MockState()
        state.extra["environmental_spreads"] = {
            "cold": {
                "halt_flag": "cold_halted",
                "milestones": [{"effects": []}],
                "active": True,
            }
        }

        errors = validate_spreads(state)  # type: ignore[arg-type]
        self.assertIn("missing 'turn'", errors[0])

    def test_milestone_missing_effects(self) -> None:
        """Milestone missing effects produces error."""
        state = MockState()
        state.extra["environmental_spreads"] = {
            "cold": {
                "halt_flag": "cold_halted",
                "milestones": [{"turn": TurnNumber(10)}],
                "active": True,
            }
        }

        errors = validate_spreads(state)  # type: ignore[arg-type]
        self.assertIn("missing 'effects'", errors[0])


class TestValidateGossipReferences(unittest.TestCase):
    """Test gossip validation."""

    def test_valid_point_to_point_gossip(self) -> None:
        """Valid point-to-point gossip produces no errors."""
        state = MockState()
        state.extra["gossip_queue"] = [
            {
                "id": "gossip_1",
                "content": "Player did something",
                "source_npc": "witness",
                "target_npcs": ["guard"],
                "type": "point_to_point",
            }
        ]

        errors = validate_gossip_references(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])

    def test_valid_broadcast_gossip(self) -> None:
        """Valid broadcast gossip produces no errors."""
        state = MockState()
        state.extra["gossip_queue"] = [
            {
                "id": "gossip_1",
                "content": "Major event",
                "source_npc": "herald",
                "target_regions": ["region_a", "region_b"],
                "type": "broadcast",
            }
        ]

        errors = validate_gossip_references(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])

    def test_missing_content(self) -> None:
        """Missing content produces error."""
        state = MockState()
        state.extra["gossip_queue"] = [
            {"id": "gossip_1", "source_npc": "npc", "target_npcs": ["other"]}
        ]

        errors = validate_gossip_references(state)  # type: ignore[arg-type]
        self.assertIn("missing 'content'", errors[0])

    def test_missing_target_npcs(self) -> None:
        """Missing target_npcs for point-to-point produces error."""
        state = MockState()
        state.extra["gossip_queue"] = [
            {"id": "gossip_1", "content": "Test", "source_npc": "npc"}
        ]

        errors = validate_gossip_references(state)  # type: ignore[arg-type]
        self.assertIn("missing 'target_npcs'", errors[0])

    def test_missing_target_regions_broadcast(self) -> None:
        """Missing target_regions for broadcast produces error."""
        state = MockState()
        state.extra["gossip_queue"] = [
            {
                "id": "gossip_1",
                "content": "Test",
                "source_npc": "npc",
                "type": "broadcast",
            }
        ]

        errors = validate_gossip_references(state)  # type: ignore[arg-type]
        self.assertIn("missing 'target_regions'", errors[0])

    def test_missing_network_id_network(self) -> None:
        """Missing network_id for network gossip produces error."""
        state = MockState()
        state.extra["gossip_queue"] = [
            {
                "id": "gossip_1",
                "content": "Test",
                "source_npc": "npc",
                "type": "network",
            }
        ]

        errors = validate_gossip_references(state)  # type: ignore[arg-type]
        self.assertIn("missing 'network_id'", errors[0])


class TestValidateCompanionRestrictions(unittest.TestCase):
    """Test companion validation."""

    def test_valid_companion(self) -> None:
        """Valid companion produces no errors."""
        state = MockState()
        state.actors[ActorId("echo")] = MockActor(id="echo")
        state.extra["companions"] = [{"actor_id": "echo", "status": "following"}]

        errors = validate_companion_restrictions(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])

    def test_missing_actor_id(self) -> None:
        """Missing actor_id produces error."""
        state = MockState()
        state.extra["companions"] = [{"status": "following"}]

        errors = validate_companion_restrictions(state)  # type: ignore[arg-type]
        self.assertIn("missing 'actor_id'", errors[0])

    def test_nonexistent_actor(self) -> None:
        """Reference to non-existent actor produces error."""
        state = MockState()
        state.extra["companions"] = [{"actor_id": "ghost", "status": "following"}]

        errors = validate_companion_restrictions(state)  # type: ignore[arg-type]
        self.assertIn("non-existent actor", errors[0])

    def test_invalid_status(self) -> None:
        """Invalid status produces error."""
        state = MockState()
        state.actors[ActorId("echo")] = MockActor(id="echo")
        state.extra["companions"] = [{"actor_id": "echo", "status": "dancing"}]

        errors = validate_companion_restrictions(state)  # type: ignore[arg-type]
        self.assertIn("invalid status", errors[0])


class TestValidateZoneConsistency(unittest.TestCase):
    """Test zone consistency validation."""

    def test_valid_temperature_zone(self) -> None:
        """Valid temperature zone produces no errors."""
        state = MockState()
        state.locations = [
            MockLocation(
                id="loc_cold", properties={"temperature_zone": TemperatureZone.COLD}
            )
        ]

        errors = validate_zone_consistency(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])

    def test_valid_water_level(self) -> None:
        """Valid water level produces no errors."""
        state = MockState()
        state.locations = [
            MockLocation(id="loc_wet", properties={"water_level": WaterLevel.SUBMERGED})
        ]

        errors = validate_zone_consistency(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])

    def test_invalid_temperature_zone(self) -> None:
        """Invalid temperature zone produces error."""
        state = MockState()
        state.locations = [
            MockLocation(id="loc_bad", properties={"temperature_zone": "boiling"})
        ]

        errors = validate_zone_consistency(state)  # type: ignore[arg-type]
        self.assertIn("invalid temperature_zone", errors[0])

    def test_invalid_water_level(self) -> None:
        """Invalid water level produces error."""
        state = MockState()
        state.locations = [
            MockLocation(id="loc_bad", properties={"water_level": "tsunami"})
        ]

        errors = validate_zone_consistency(state)  # type: ignore[arg-type]
        self.assertIn("invalid water_level", errors[0])


class TestValidateInfrastructure(unittest.TestCase):
    """Test main validation entry point."""

    def test_valid_state_returns_empty(self) -> None:
        """Valid state returns empty error list."""
        state = MockState()
        state.actors = {}
        state.locations = []

        errors = validate_infrastructure(state)  # type: ignore[arg-type]
        self.assertEqual(errors, [])

    def test_combines_all_errors(self) -> None:
        """validate_infrastructure combines errors from all validators."""
        state = MockState()
        # Add an invalid commitment config
        state.extra["commitment_configs"] = {
            "bad": {"id": "bad"}  # Missing required fields
        }
        # Add an invalid spread
        state.extra["environmental_spreads"] = {
            "bad_spread": {"active": True}  # Missing halt_flag and milestones
        }

        errors = validate_infrastructure(state)  # type: ignore[arg-type]
        # Should have errors from both validators
        self.assertTrue(len(errors) >= 2)


if __name__ == "__main__":
    unittest.main()
