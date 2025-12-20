"""Scenario tests for Sunken District region.

Tests multi-step gameplay scenarios including:
- Dual rescue (Delvan vs Garrett impossible choice)
- Drowning mechanics
- Water level hazards
"""
from src.types import ActorId

import unittest
from typing import Any

from examples.big_game.behaviors.infrastructure.dispatcher_utils import clear_handler_cache
from behaviors.regions.sunken_district.drowning import (
    MAX_BREATH,
    WARNING_BREATH,
    CRITICAL_BREATH,
    DROWN_DAMAGE,
    on_surface,
    on_underwater_turn,
    on_water_entry,
)
from behaviors.regions.sunken_district.dual_rescue import (
    on_delvan_encounter,
    on_garrett_encounter,
    on_npc_death,
    on_rescue_success,
)
from src.behavior_manager import EventResult
from src.infrastructure_utils import get_pending_gossip_about
from tests.infrastructure.test_scenario_framework import (
    MockEntity,
    MockItem,
    MockLocation,
    ScenarioAccessor,
    ScenarioState,
    ScenarioTestCase,
)


class TestDualRescueScenarios(ScenarioTestCase):
    """Tests for Delvan and Garrett dual rescue scenarios."""

    def setUp(self) -> None:
        """Set up dual rescue test fixtures."""
        super().setUp()
        self.setup_player(location="loc_sunken_district_entrance")

        # Create Delvan (trapped merchant)
        self.delvan = self.state.add_actor(
            "merchant_delvan",
            name="Merchant Delvan",
            properties={
                "state_machine": {
                    "states": ["trapped", "freed", "mobile", "dead"],
                    "initial": "trapped",
                    "current": "trapped",
                },
                "conditions": {"bleeding": {"severity": 60, "type": "bleeding"}},
            },
            location="loc_sunken_collapsed_hall",
        )

        # Create Garrett (drowning sailor)
        self.garrett = self.state.add_actor(
            "sailor_garrett",
            name="Sailor Garrett",
            properties={
                "state_machine": {
                    "states": ["drowning", "rescued", "dead"],
                    "initial": "drowning",
                    "current": "drowning",
                },
                "conditions": {"drowning": {"severity": 80, "type": "drowning"}},
            },
            location="loc_sunken_rising_water",
        )

        # Create locations
        self.delvan_room = self.state.add_location(
            "loc_sunken_collapsed_hall",
            name="Collapsed Hall",
        )
        self.garrett_room = self.state.add_location(
            "loc_sunken_rising_water",
            name="Rising Water Chamber",
        )

        # Add commitment configs
        self.state.add_commitment_config(
            "commit_delvan_rescue",
            duration=15,
            success_condition="delvan_rescued",
        )
        self.state.add_commitment_config(
            "commit_garrett_rescue",
            duration=8,  # Much shorter!
            success_condition="garrett_rescued",
        )

    def test_delvan_encounter_starts_commitment(self) -> None:
        """Finding Delvan starts rescue commitment."""
        result = on_delvan_encounter(self.delvan, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("pinned beneath", (result.feedback or "").lower())
        self.assertIn("morse code", (result.feedback or "").lower())
        self.assert_flag_set("delvan_commitment_created")
        self.assert_flag_set("delvan_encounter_turn")

    def test_delvan_encounter_idempotent(self) -> None:
        """Subsequent encounters don't create duplicate commitments."""
        on_delvan_encounter(self.delvan, self.accessor, {})
        initial_turn = self.state.extra["delvan_encounter_turn"]

        self.state.advance_turns(5)
        result = on_delvan_encounter(self.delvan, self.accessor, {})

        # Should not update turn
        self.assertEqual(self.state.extra["delvan_encounter_turn"], initial_turn)

    def test_garrett_encounter_starts_commitment(self) -> None:
        """Entering Garrett's room starts rescue commitment."""
        result = on_garrett_encounter(self.garrett_room, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("filling with water", (result.feedback or "").lower())
        self.assertIn("minutes, not hours", (result.feedback or "").lower())
        self.assert_flag_set("garrett_commitment_created")

    def test_delvan_rescue_success(self) -> None:
        """Successfully rescuing Delvan sets flags."""
        on_delvan_encounter(self.delvan, self.accessor, {})

        result = on_rescue_success(
            self.delvan, self.accessor, {"condition_type": "bleeding"}
        )

        self.assertTrue(result.allow)
        self.assertIn("stop", (result.feedback or "").lower())
        self.assertIn("tapping stops", (result.feedback or "").lower())
        self.assert_flag_set("delvan_rescued")

    def test_garrett_rescue_success(self) -> None:
        """Successfully rescuing Garrett sets flags."""
        on_garrett_encounter(self.garrett_room, self.accessor, {})

        result = on_rescue_success(
            self.garrett, self.accessor, {"condition_type": "drowning"}
        )

        self.assertTrue(result.allow)
        self.assertIn("pull", (result.feedback or "").lower())
        self.assert_flag_set("garrett_rescued")

    def test_delvan_death_creates_gossip(self) -> None:
        """Delvan dying creates gossip."""
        on_delvan_encounter(self.delvan, self.accessor, {})

        result = on_npc_death(self.delvan, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("tapping stops", (result.feedback or "").lower())
        self.assert_flag_set("delvan_died")
        self.assert_gossip_pending("Delvan")

    def test_garrett_death_creates_gossip(self) -> None:
        """Garrett dying creates gossip."""
        on_garrett_encounter(self.garrett_room, self.accessor, {})

        result = on_npc_death(self.garrett, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("water closes", (result.feedback or "").lower())
        self.assertIn("chose", (result.feedback or "").lower())
        self.assert_flag_set("garrett_died")
        self.assert_gossip_pending("Garrett")


class TestDrowningScenarios(ScenarioTestCase):
    """Tests for drowning mechanics."""

    def setUp(self) -> None:
        """Set up drowning test fixtures."""
        super().setUp()
        player = self.setup_player(location="loc_sunken_dock")
        player.properties["health"] = 100
        player.properties["conditions"] = []

        # Create locations
        self.dock = self.state.add_location(
            "loc_sunken_dock",
            name="Flooded Dock",
            properties={"water_level": "knee"},
        )
        self.flooded = self.state.add_location(
            "loc_sunken_passage",
            name="Flooded Passage",
            properties={"water_level": "flooded"},
        )
        self.surface = self.state.add_location(
            "loc_sunken_platform",
            name="Raised Platform",
            properties={"water_level": "none"},
        )

    def test_water_entry_starts_breath_timer(self) -> None:
        """Entering flooded area marks player underwater."""
        player = self.state.actors[ActorId("player")]

        result = on_water_entry(player, self.accessor, {"destination": self.flooded})

        self.assertTrue(result.allow)
        self.assertIn("hold your breath", (result.feedback or "").lower())
        self.assertIn(str(MAX_BREATH), result.feedback or "")
        self.assertTrue(player.properties.get("underwater"))

    def test_breathing_equipment_prevents_timer(self) -> None:
        """Breathing equipment allows safe underwater travel."""
        player = self.state.actors[ActorId("player")]
        player.properties["equipment"] = {"breathing": "diving_mask"}

        result = on_water_entry(player, self.accessor, {"destination": self.flooded})

        self.assertTrue(result.allow)
        self.assertIn("breathing mask", (result.feedback or "").lower())

    def test_breath_warning_at_threshold(self) -> None:
        """Warning appears when breath gets low."""
        player = self.state.actors[ActorId("player")]
        player.properties["underwater"] = True

        # Initialize breath close to warning
        player.properties["conditions"] = [
            {"type": "held_breath", "current": WARNING_BREATH - 1, "max": MAX_BREATH}
        ]

        result = on_underwater_turn(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("burning", (result.feedback or "").lower())

    def test_breath_critical_warning(self) -> None:
        """Critical warning appears when near drowning."""
        player = self.state.actors[ActorId("player")]
        player.properties["underwater"] = True

        # Initialize breath close to critical
        player.properties["conditions"] = [
            {"type": "held_breath", "current": CRITICAL_BREATH - 1, "max": MAX_BREATH}
        ]

        result = on_underwater_turn(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("suffocating", (result.feedback or "").lower())

    def test_drowning_damage_at_max(self) -> None:
        """Drowning causes damage when breath exceeds max."""
        player = self.state.actors[ActorId("player")]
        player.properties["underwater"] = True
        player.properties["health"] = 100

        # Initialize breath at max
        player.properties["conditions"] = [
            {"type": "held_breath", "current": MAX_BREATH - 1, "max": MAX_BREATH}
        ]

        result = on_underwater_turn(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("drowning", (result.feedback or "").lower())
        self.assertEqual(player.properties["health"], 100 - DROWN_DAMAGE)

    def test_surfacing_resets_breath(self) -> None:
        """Reaching surface resets breath counter."""
        player = self.state.actors[ActorId("player")]
        player.properties["underwater"] = True
        player.properties["conditions"] = [
            {"type": "held_breath", "current": 8, "max": MAX_BREATH}
        ]

        result = on_surface(player, self.accessor, {"destination": self.surface})

        self.assertTrue(result.allow)
        self.assertIn("gasping", (result.feedback or "").lower())
        self.assertFalse(player.properties.get("underwater"))

        # Breath should be reset
        for cond in player.properties["conditions"]:
            if cond.get("type") == "held_breath":
                self.assertEqual(cond["current"], 0)


class TestDualRescueImpossibleChoiceScenarios(ScenarioTestCase):
    """Tests demonstrating the designed impossible choice."""

    def setUp(self) -> None:
        """Set up impossible choice scenario."""
        super().setUp()
        self.setup_player(location="loc_sunken_entrance")

        # Both NPCs
        self.delvan = self.state.add_actor(
            "merchant_delvan",
            properties={
                "conditions": {"bleeding": {"severity": 60, "type": "bleeding"}}
            },
        )
        self.garrett = self.state.add_actor(
            "sailor_garrett",
            properties={
                "conditions": {"drowning": {"severity": 80, "type": "drowning"}}
            },
        )

        # Locations
        self.garrett_room = self.state.add_location(
            "loc_garrett_chamber",
            name="Rising Water Chamber",
        )

        # Commitment configs with different durations
        self.state.add_commitment_config(
            "commit_delvan_rescue", duration=15, success_condition="delvan_rescued"
        )
        self.state.add_commitment_config(
            "commit_garrett_rescue", duration=8, success_condition="garrett_rescued"
        )

    def test_save_garrett_delvan_dies(self) -> None:
        """Choosing to save Garrett first leaves Delvan to die."""
        # Find both
        on_delvan_encounter(self.delvan, self.accessor, {})
        on_garrett_encounter(self.garrett_room, self.accessor, {})

        # Save Garrett
        on_rescue_success(self.garrett, self.accessor, {"condition_type": "drowning"})

        # Delvan dies (simulated by time running out)
        result = on_npc_death(self.delvan, self.accessor, {})

        self.assert_flag_set("garrett_rescued")
        self.assert_flag_set("delvan_died")
        self.assertIn("too late", (result.feedback or "").lower())

    def test_save_delvan_garrett_drowns(self) -> None:
        """Choosing to save Delvan first leaves Garrett to drown."""
        # Find both
        on_delvan_encounter(self.delvan, self.accessor, {})
        on_garrett_encounter(self.garrett_room, self.accessor, {})

        # Save Delvan
        on_rescue_success(self.delvan, self.accessor, {"condition_type": "bleeding"})

        # Garrett drowns (shorter timer)
        result = on_npc_death(self.garrett, self.accessor, {})

        self.assert_flag_set("delvan_rescued")
        self.assert_flag_set("garrett_died")
        self.assertIn("chose", (result.feedback or "").lower())

    def test_both_die_if_delayed(self) -> None:
        """Both die if player doesn't act quickly enough."""
        # Find both
        on_delvan_encounter(self.delvan, self.accessor, {})
        on_garrett_encounter(self.garrett_room, self.accessor, {})

        # Both die (player took too long)
        on_npc_death(self.garrett, self.accessor, {})
        on_npc_death(self.delvan, self.accessor, {})

        self.assert_flag_set("garrett_died")
        self.assert_flag_set("delvan_died")

        # Both should create gossip
        self.assert_gossip_pending("Garrett")
        self.assert_gossip_pending("Delvan")


if __name__ == "__main__":
    unittest.main()
