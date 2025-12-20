"""Scenario tests for Frozen Reaches region.

Tests multi-step gameplay scenarios including:
- Salamander befriending
- Hypothermia system
- Cold gear and companions
"""
from src.types import ActorId

import unittest
from typing import Any

from examples.big_game.behaviors.infrastructure.dispatcher_utils import clear_handler_cache
from behaviors.regions.frozen_reaches.hypothermia import (
    COLD_RATES,
    GEAR_COLD_REDUCTION,
    on_cold_zone_turn,
    on_enter_hot_springs,
)
from behaviors.regions.frozen_reaches.salamanders import on_fire_gift
from src.behavior_manager import EventResult
from src.infrastructure_utils import transition_state
from tests.infrastructure.test_scenario_framework import (
    MockEntity,
    MockItem,
    MockLocation,
    ScenarioAccessor,
    ScenarioState,
    ScenarioTestCase,
)


class TestSalamanderScenarios(ScenarioTestCase):
    """Tests for salamander befriending scenarios."""

    def setUp(self) -> None:
        """Set up salamander test fixtures."""
        super().setUp()
        self.setup_player(location="loc_frozen_caves")

        # Create lead salamander
        self.salamander = self.state.add_actor(
            "salamander",
            name="Fire Salamander",
            properties={
                "state_machine": {
                    "states": ["neutral", "friendly", "companion"],
                    "initial": "neutral",
                    "current": "neutral",
                },
                "trust_state": {"current": 0, "floor": 0, "ceiling": 5},
            },
            location="loc_frozen_caves",
        )

        # Create fire items
        self.torch = self.state.add_item("item_torch", name="Torch")
        self.fire_crystal = self.state.add_item("item_fire_crystal", name="Fire Crystal")

    def test_fire_gift_increases_trust(self) -> None:
        """Giving fire items increases salamander trust."""
        initial_trust = self.get_actor_trust("salamander")

        result = on_fire_gift(
            self.torch,
            self.accessor,
            {"target_actor": self.salamander, "item": self.torch},
        )

        self.assertTrue(result.allow)
        self.assertIn("brightens", (result.feedback or "").lower())
        self.assertGreater(self.get_actor_trust("salamander"), initial_trust)

    def test_first_fire_gift_transitions_to_friendly(self) -> None:
        """First fire gift transitions salamander to friendly."""
        result = on_fire_gift(
            self.torch,
            self.accessor,
            {"target_actor": self.salamander, "item": self.torch},
        )

        self.assertTrue(result.allow)
        self.assertIn("approaches cautiously", (result.feedback or "").lower())
        self.assert_actor_state("salamander", "friendly")

    def test_non_fire_gift_rejected(self) -> None:
        """Non-fire items are rejected by salamander."""
        stone = self.state.add_item("item_stone", name="Stone")

        result = on_fire_gift(
            stone, self.accessor, {"target_actor": self.salamander, "item": stone}
        )

        self.assertTrue(result.allow)
        self.assertIn("shaking its head", (result.feedback or "").lower())
        self.assert_actor_state("salamander", "neutral")  # No change

    def test_high_trust_indicates_companion_ready(self) -> None:
        """High trust salamander indicates willingness to follow."""
        # Set up high trust
        self.salamander.properties["trust_state"]["current"] = 2
        self.salamander.properties["state_machine"]["current"] = "friendly"

        result = on_fire_gift(
            self.fire_crystal,
            self.accessor,
            {"target_actor": self.salamander, "item": self.fire_crystal},
        )

        self.assertTrue(result.allow)
        self.assertIn("willing to follow", (result.feedback or "").lower())
        self.assertEqual(self.get_actor_trust("salamander"), 3)


class TestHypothermiaScenarios(ScenarioTestCase):
    """Tests for hypothermia environmental hazard."""

    def setUp(self) -> None:
        """Set up hypothermia test fixtures."""
        super().setUp()
        player = self.setup_player(location="loc_frozen_entrance")
        player.properties["conditions"] = []

        # Create locations with different temperatures
        self.warm = self.state.add_location(
            "loc_frozen_entrance",
            name="Frozen Reaches Entrance",
            properties={"temperature": "warm"},
        )
        self.cold = self.state.add_location(
            "loc_frozen_path",
            name="Frozen Path",
            properties={"temperature": "cold"},
        )
        self.freezing = self.state.add_location(
            "loc_frozen_depths",
            name="Frozen Depths",
            properties={"temperature": "freezing"},
        )
        self.extreme = self.state.add_location(
            "loc_frozen_observatory",
            name="Ruined Observatory",
            properties={"temperature": "extreme"},
        )
        self.hot_springs = self.state.add_location(
            "loc_hot_springs",
            name="Hot Springs",
            properties={"temperature": "warm"},
        )

        # Store locations in a dict for handler access (by loc id)
        self.state.locations = {
            self.warm.id: self.warm,
            self.cold.id: self.cold,
            self.freezing.id: self.freezing,
            self.extreme.id: self.extreme,
            self.hot_springs.id: self.hot_springs,
        }

    def test_warm_zone_no_hypothermia(self) -> None:
        """Warm zones don't cause hypothermia."""
        player = self.state.actors[ActorId("player")]
        player.properties["location"] = "loc_frozen_entrance"

        result = on_cold_zone_turn(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_cold_zone_causes_hypothermia(self) -> None:
        """Cold zones cause gradual hypothermia."""
        player = self.state.actors[ActorId("player")]
        player.properties["location"] = "loc_frozen_path"

        # Run multiple turns to accumulate hypothermia
        for _ in range(5):
            on_cold_zone_turn(None, self.accessor, {})

        # Check hypothermia severity
        conditions = player.properties.get("conditions", [])
        hypothermia = None
        for cond in conditions:
            if cond.get("type") == "hypothermia":
                hypothermia = cond
                break

        self.assertIsNotNone(hypothermia)
        assert hypothermia is not None
        self.assertGreater(hypothermia["severity"], 0)

    def test_cold_gear_reduces_hypothermia(self) -> None:
        """Cold weather gear reduces hypothermia rate."""
        player = self.state.actors[ActorId("player")]
        player.properties["location"] = "loc_frozen_depths"
        player.properties["equipment"] = {"body": "cold_weather_gear"}

        # Run turns
        for _ in range(4):
            on_cold_zone_turn(None, self.accessor, {})

        # Check severity - should be lower than without gear
        conditions = player.properties.get("conditions", [])
        hypothermia = None
        for cond in conditions:
            if cond.get("type") == "hypothermia":
                hypothermia = cond
                break

        # With 50% reduction, 4 turns * 10 * 0.5 = 20
        self.assertIsNotNone(hypothermia)
        assert hypothermia is not None
        self.assertLessEqual(hypothermia["severity"], 20)

    def test_cloak_grants_cold_immunity(self) -> None:
        """Cold resistance cloak grants immunity in cold zones."""
        player = self.state.actors[ActorId("player")]
        player.properties["location"] = "loc_frozen_path"
        player.properties["equipment"] = {"cloak": "cold_resistance_cloak"}

        # Run turns
        for _ in range(3):
            result = on_cold_zone_turn(None, self.accessor, {})

        # Should have no hypothermia
        conditions = player.properties.get("conditions", [])
        hypothermia = None
        for cond in conditions:
            if cond.get("type") == "hypothermia":
                hypothermia = cond
                break

        self.assertIsNone(hypothermia)

    def test_salamander_companion_grants_immunity(self) -> None:
        """Salamander companion grants full hypothermia immunity."""
        player = self.state.actors[ActorId("player")]
        player.properties["location"] = "loc_frozen_observatory"  # Extreme cold
        player.properties["companions"] = [{"id": "salamander", "state": "following"}]

        # Run turns in extreme cold
        for _ in range(3):
            result = on_cold_zone_turn(None, self.accessor, {})
            self.assertIsNone(result.feedback)  # No warnings

    def test_hypothermia_severity_warnings(self) -> None:
        """Different severity levels show different warnings."""
        player = self.state.actors[ActorId("player")]
        player.properties["location"] = "loc_frozen_observatory"  # 20 per turn

        # First turn - severity 20
        result = on_cold_zone_turn(None, self.accessor, {})
        self.assertIn("getting cold", (result.feedback or "").lower())

        # After more turns - severity increases
        on_cold_zone_turn(None, self.accessor, {})  # 40
        result = on_cold_zone_turn(None, self.accessor, {})  # 60
        self.assertIn("shivers", (result.feedback or "").lower())

        result = on_cold_zone_turn(None, self.accessor, {})  # 80
        self.assertIn("freezing to death", (result.feedback or "").lower())


class TestHotSpringsScenarios(ScenarioTestCase):
    """Tests for hot springs healing."""

    def setUp(self) -> None:
        """Set up hot springs test fixtures."""
        super().setUp()
        player = self.setup_player(location="loc_frozen_path")
        player.properties["conditions"] = []

        self.hot_springs = self.state.add_location(
            "loc_hot_springs",
            name="Hot Springs",
            properties={"temperature": "warm"},
        )

    def test_hot_springs_cures_hypothermia(self) -> None:
        """Hot springs instantly cure hypothermia."""
        player = self.state.actors[ActorId("player")]

        # Give player hypothermia
        player.properties["conditions"] = [
            {"type": "hypothermia", "severity": 60}
        ]

        result = on_enter_hot_springs(
            player, self.accessor, {"destination": self.hot_springs}
        )

        self.assertTrue(result.allow)
        self.assertIn("fully restored", (result.feedback or "").lower())

        # Check hypothermia cured
        conditions = player.properties["conditions"]
        hypothermia = None
        for cond in conditions:
            if cond.get("type") == "hypothermia":
                hypothermia = cond
                break

        assert hypothermia is not None
        self.assertEqual(hypothermia["severity"], 0)

    def test_hot_springs_without_hypothermia(self) -> None:
        """Hot springs still give warmth message without hypothermia."""
        player = self.state.actors[ActorId("player")]

        result = on_enter_hot_springs(
            player, self.accessor, {"destination": self.hot_springs}
        )

        self.assertTrue(result.allow)
        self.assertIn("warmth envelops", (result.feedback or "").lower())


class TestCombinedFrozenScenarios(ScenarioTestCase):
    """Tests combining salamander and hypothermia mechanics."""

    def setUp(self) -> None:
        """Set up combined scenario fixtures."""
        super().setUp()
        player = self.setup_player(location="loc_frozen_entrance")
        player.properties["conditions"] = []

        # Create salamander
        self.salamander = self.state.add_actor(
            "salamander",
            name="Fire Salamander",
            properties={
                "state_machine": {
                    "states": ["neutral", "friendly", "companion"],
                    "initial": "neutral",
                    "current": "neutral",
                },
                "trust_state": {"current": 0, "floor": 0, "ceiling": 5},
            },
        )

        # Create extreme cold location
        extreme = MockLocation(
            "loc_frozen_observatory",
            name="Observatory",
            properties={"temperature": "extreme"},
        )
        self.state.locations = {extreme.id: extreme}

    def test_befriend_salamander_then_survive_extreme(self) -> None:
        """Befriending salamander allows survival in extreme cold."""
        player = self.state.actors[ActorId("player")]
        torch = self.state.add_item("item_torch", name="Torch")

        # Befriend salamander (3 gifts for high trust)
        for _ in range(3):
            on_fire_gift(
                torch,
                self.accessor,
                {"target_actor": self.salamander, "item": torch},
            )

        # Add salamander as companion
        player.properties["companions"] = [{"id": "salamander", "state": "following"}]

        # Enter extreme cold
        player.properties["location"] = "loc_frozen_observatory"

        # Should survive without hypothermia
        for _ in range(5):
            result = on_cold_zone_turn(None, self.accessor, {})
            self.assertIsNone(result.feedback)

        # No hypothermia condition
        conditions = player.properties.get("conditions", [])
        hypothermia = None
        for cond in conditions:
            if cond.get("type") == "hypothermia":
                hypothermia = cond
                break

        self.assertIsNone(hypothermia)


if __name__ == "__main__":
    unittest.main()
