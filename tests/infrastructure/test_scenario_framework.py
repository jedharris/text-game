"""Scenario-based integration tests for region behaviors.

This framework tests complex multi-step scenarios that simulate
actual gameplay, verifying that handlers, dispatchers, and state
changes work together correctly.
"""

from __future__ import annotations

import unittest
from typing import Any, cast, TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from src.state_manager import GameState

from examples.big_game.behaviors.infrastructure.dispatcher_utils import clear_handler_cache
from src.behavior_manager import BehaviorManager, EventResult
from src.infrastructure_utils import (
    create_commitment,
    create_condition,
    create_gossip,
    get_active_commitment,
    get_current_turn,
    get_pending_gossip_about,
    modify_condition_severity,
    modify_trust,
    transition_commitment_state,
    transition_state,
)


class MockEntity:
    """Mock entity for scenario testing."""

    def __init__(
        self,
        entity_id: str,
        name: str | None = None,
        properties: dict | None = None,
        location: str | None = None,
    ) -> None:
        self.id = entity_id
        self.name = name or entity_id
        self.properties = properties or {}
        self.location = location
        self.inventory: list[str] = []


class MockItem:
    """Mock item for scenario testing."""

    def __init__(
        self,
        item_id: str,
        name: str | None = None,
        properties: dict | None = None,
        location: str | None = None,
    ) -> None:
        self.id = item_id
        self.name = name or item_id
        self.properties = properties or {}
        self.location = location


class MockLocation:
    """Mock location for scenario testing."""

    def __init__(
        self,
        loc_id: str,
        name: str | None = None,
        properties: dict | None = None,
    ) -> None:
        self.id = loc_id
        self.name = name or loc_id
        self.properties = properties or {}


class ScenarioState:
    """Game state for scenario testing.

    Provides a minimal state structure that handlers can operate on.
    """

    def __init__(self) -> None:
        self.extra: dict[str, Any] = {
            "turn_count": 0,
            "flags": {},
            "active_commitments": [],
            "gossip_queue": [],
            "commitment_configs": {},
        }
        self.actors: dict[str, MockEntity] = {}
        self.items: list[MockItem] = []
        self.locations: dict[str, MockLocation] = {}

    def add_actor(
        self,
        actor_id: str,
        name: str | None = None,
        properties: dict | None = None,
        location: str | None = None,
    ) -> MockEntity:
        """Add an actor to the state."""
        actor = MockEntity(actor_id, name, properties, location)
        self.actors[actor_id] = actor
        return actor

    def add_item(
        self,
        item_id: str,
        name: str | None = None,
        properties: dict | None = None,
        location: str | None = None,
    ) -> MockItem:
        """Add an item to the state."""
        item = MockItem(item_id, name, properties, location)
        self.items.append(item)
        return item

    def add_location(
        self,
        loc_id: str,
        name: str | None = None,
        properties: dict | None = None,
    ) -> MockLocation:
        """Add a location to the state."""
        location = MockLocation(loc_id, name, properties)
        self.locations[loc_id] = location
        return location

    def advance_turns(self, count: int = 1) -> None:
        """Advance the turn counter."""
        self.extra["turn_count"] += count

    def add_commitment_config(
        self,
        config_id: str,
        duration: int,
        success_condition: str | None = None,
        failure_effects: dict | None = None,
    ) -> None:
        """Add a commitment configuration."""
        self.extra["commitment_configs"][config_id] = {
            "id": config_id,
            "duration": duration,
            "success_condition": success_condition or f"{config_id}_fulfilled",
            "failure_effects": failure_effects or {},
        }


class ScenarioAccessor:
    """Mock accessor for scenario testing."""

    def __init__(self, state: ScenarioState) -> None:
        self.state = state


class ScenarioTestCase(unittest.TestCase):
    """Base class for scenario tests.

    Provides common setup and helper methods for testing scenarios.
    """

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.state = ScenarioState()
        self.accessor = ScenarioAccessor(self.state)

    # =========================================================================
    # Helper methods for common scenario operations
    # =========================================================================

    def setup_player(self, location: str | None = None) -> MockEntity:
        """Set up player entity."""
        return self.state.add_actor(
            "player",
            name="Player",
            properties={"inventory": []},
            location=location,
        )

    def create_npc_with_trust(
        self,
        actor_id: str,
        name: str,
        states: list[str],
        initial_state: str,
        trust_floor: int = -5,
        trust_ceiling: int = 5,
        initial_trust: int = 0,
        location: str | None = None,
        extra_props: dict | None = None,
    ) -> MockEntity:
        """Create an NPC with state machine and trust system."""
        properties = {
            "state_machine": {
                "states": states,
                "initial": initial_state,
                "current": initial_state,
            },
            "trust_state": {
                "current": initial_trust,
                "floor": trust_floor,
                "ceiling": trust_ceiling,
            },
        }
        if extra_props:
            properties.update(extra_props)

        return self.state.add_actor(actor_id, name, properties, location)

    def create_npc_with_condition(
        self,
        actor_id: str,
        name: str,
        condition_type: str,
        severity: int,
        states: list[str] | None = None,
        initial_state: str | None = None,
        location: str | None = None,
    ) -> MockEntity:
        """Create an NPC with a condition."""
        properties: dict[str, Any] = {
            "conditions": {
                condition_type: {"severity": severity, "type": condition_type}
            }
        }
        if states and initial_state:
            properties["state_machine"] = {
                "states": states,
                "initial": initial_state,
                "current": initial_state,
            }

        return self.state.add_actor(actor_id, name, properties, location)

    def get_actor_state(self, actor_id: str) -> str | None:
        """Get an actor's current state machine state."""
        actor = self.state.actors.get(actor_id)
        if not actor:
            return None
        sm = actor.properties.get("state_machine", {})
        return sm.get("current", sm.get("initial"))

    def get_actor_trust(self, actor_id: str) -> int:
        """Get an actor's current trust value."""
        actor = self.state.actors.get(actor_id)
        if not actor:
            return 0
        trust = actor.properties.get("trust_state", {})
        return trust.get("current", 0)

    def get_condition_severity(self, actor_id: str, condition_type: str) -> int | None:
        """Get the severity of an actor's condition."""
        actor = self.state.actors.get(actor_id)
        if not actor:
            return None
        conditions = actor.properties.get("conditions", {})
        condition = conditions.get(condition_type)
        if condition:
            return condition.get("severity")
        return None

    def transition_actor_state(self, actor_id: str, new_state: str) -> bool:
        """Transition an actor to a new state."""
        actor = self.state.actors.get(actor_id)
        if not actor:
            return False
        sm = actor.properties.get("state_machine")
        if not sm:
            return False
        success, _ = transition_state(sm, new_state)
        return success

    def modify_actor_trust(
        self, actor_id: str, delta: int, floor: int | None = None, ceiling: int | None = None
    ) -> int:
        """Modify an actor's trust value."""
        actor = self.state.actors.get(actor_id)
        if not actor:
            return 0
        trust = actor.properties.get("trust_state", {"current": 0})
        new_trust = modify_trust(
            current=trust.get("current", 0),
            delta=delta,
            floor=floor or trust.get("floor", -5),
            ceiling=ceiling or trust.get("ceiling", 5),
        )
        trust["current"] = new_trust
        actor.properties["trust_state"] = trust
        return new_trust

    def assert_actor_state(self, actor_id: str, expected_state: str) -> None:
        """Assert an actor is in the expected state."""
        actual = self.get_actor_state(actor_id)
        self.assertEqual(
            actual,
            expected_state,
            f"Actor '{actor_id}' state: expected '{expected_state}', got '{actual}'",
        )

    def assert_actor_trust(self, actor_id: str, expected_trust: int) -> None:
        """Assert an actor has the expected trust value."""
        actual = self.get_actor_trust(actor_id)
        self.assertEqual(
            actual,
            expected_trust,
            f"Actor '{actor_id}' trust: expected {expected_trust}, got {actual}",
        )

    def assert_flag_set(self, flag_name: str) -> None:
        """Assert a global flag is set (exists and not None/False)."""
        value = self.state.extra.get(flag_name)
        # Allow 0 as a valid value (e.g., turn numbers)
        if value is None or value is False:
            self.fail(f"Flag '{flag_name}' not set")
        # For booleans, ensure True
        if isinstance(value, bool):
            self.assertTrue(value, f"Flag '{flag_name}' is False")

    def assert_flag_not_set(self, flag_name: str) -> None:
        """Assert a global flag is not set."""
        value = self.state.extra.get(flag_name)
        self.assertFalse(value, f"Flag '{flag_name}' unexpectedly set to {value}")

    def assert_gossip_pending(self, content_substring: str) -> None:
        """Assert gossip containing substring is pending."""
        matches = get_pending_gossip_about(cast("GameState", self.state), content_substring)
        self.assertTrue(
            len(matches) > 0,
            f"No pending gossip containing '{content_substring}'",
        )

    def assert_no_gossip_pending(self, content_substring: str) -> None:
        """Assert no gossip containing substring is pending."""
        matches = get_pending_gossip_about(cast("GameState", self.state), content_substring)
        self.assertEqual(
            len(matches),
            0,
            f"Unexpected gossip containing '{content_substring}'",
        )


if __name__ == "__main__":
    unittest.main()
