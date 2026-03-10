"""Scenario tests for Sunken District region using real game state.

Tests multi-step gameplay scenarios including:
- Dual rescue (Delvan vs Garrett impossible choice)
- Drowning mechanics
- Water level hazards

Tests load big_game via GameEngine to use actual actor IDs, state machines,
and property structures. Each test gets a fresh engine instance.
"""

import unittest
from pathlib import Path
from typing import Any

from tests.conftest import BaseTestCase
from src.game_engine import GameEngine
from src.state_accessor import StateAccessor
from src.types import ActorId, LocationId
from src.infrastructure_utils import get_pending_gossip_about
from src.behavior_manager import EventResult
from examples.big_game.behaviors.regions.sunken_district.drowning import (
    MAX_BREATH,
    WARNING_THRESHOLD,
    CRITICAL_THRESHOLD,
    DROWN_DAMAGE,
    on_turn_drowning,
)
from examples.big_game.behaviors.regions.sunken_district.dual_rescue import (
    on_delvan_encounter,
    on_garrett_encounter,
    on_npc_death,
    on_rescue_success,
)

GAME_DIR = (Path(__file__).parent.parent.parent / 'examples' / 'big_game').resolve()


class SunkenDistrictTestCase(BaseTestCase):
    """Base class for sunken district tests with real game state."""

    def setUp(self) -> None:
        self.engine = GameEngine(GAME_DIR)
        self.state = self.engine.game_state
        self.accessor = StateAccessor(
            self.state,
            self.engine.behavior_manager,
        )

    def assert_flag_set(self, flag_name: str) -> None:
        """Assert a flag is set in game state extra (not None, not missing)."""
        self.assertIn(flag_name, self.state.extra,
                       f"Flag '{flag_name}' should exist in game state extra")
        self.assertIsNotNone(
            self.state.extra[flag_name],
            f"Flag '{flag_name}' should not be None in game state extra",
        )

    def assert_gossip_pending(self, content_substring: str) -> None:
        """Assert there is pending gossip containing the given substring."""
        matches = get_pending_gossip_about(self.state, content_substring)
        self.assertTrue(
            len(matches) > 0,
            f"Expected pending gossip containing '{content_substring}', found none",
        )


class TestDualRescueScenarios(SunkenDistrictTestCase):
    """Tests for Delvan and Garrett dual rescue scenarios."""

    def setUp(self) -> None:
        super().setUp()
        self.delvan = self.state.actors.get(ActorId("merchant_delvan"))
        self.garrett = self.state.actors.get(ActorId("sailor_garrett"))
        self.assertIsNotNone(self.delvan, "merchant_delvan should exist in game state")
        self.assertIsNotNone(self.garrett, "sailor_garrett should exist in game state")

        # Ensure commit_garrett_rescue config exists (not in default game state)
        configs = self.state.extra.setdefault("commitment_configs", {})
        if "commit_garrett_rescue" not in configs:
            configs["commit_garrett_rescue"] = {
                "id": "commit_garrett_rescue",
                "description": "Rescue Sailor Garrett from drowning",
                "deadline_turns": 5,
                "target_actor": "sailor_garrett",
            }

        # Get the sea_caves location for garrett encounter tests.
        # on_garrett_encounter checks for "garrett" or "rising_water" in loc id,
        # so we use the garrett actor's location and pass it with an id that matches.
        self.garrett_location = self.state.get_location(LocationId("sea_caves"))

    def _make_garrett_location_entity(self) -> Any:
        """Create a location-like object whose id triggers on_garrett_encounter.

        The handler checks for 'garrett' or 'rising_water' in the location id.
        The real sea_caves location doesn't match, so we wrap it.
        """
        loc = self.garrett_location

        class _GarrettRoom:
            id = "garrett_sea_caves"
            properties = loc.properties if hasattr(loc, 'properties') else {}

        return _GarrettRoom()

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

        # Advance turns by setting turn_count
        self.state.extra["turn_count"] = self.state.extra.get("turn_count", 0) + 5
        result = on_delvan_encounter(self.delvan, self.accessor, {})

        # Should not update turn
        self.assertEqual(self.state.extra["delvan_encounter_turn"], initial_turn)

    def test_garrett_encounter_starts_commitment(self) -> None:
        """Entering Garrett's room starts rescue commitment."""
        garrett_room = self._make_garrett_location_entity()
        result = on_garrett_encounter(garrett_room, self.accessor, {})

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
        garrett_room = self._make_garrett_location_entity()
        on_garrett_encounter(garrett_room, self.accessor, {})

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
        garrett_room = self._make_garrett_location_entity()
        on_garrett_encounter(garrett_room, self.accessor, {})

        result = on_npc_death(self.garrett, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("water closes", (result.feedback or "").lower())
        self.assertIn("chose", (result.feedback or "").lower())
        self.assert_flag_set("garrett_died")
        self.assert_gossip_pending("Garrett")


class TestDrowningScenarios(SunkenDistrictTestCase):
    """Tests for drowning mechanics."""

    def setUp(self) -> None:
        super().setUp()
        self.player = self.state.actors.get(ActorId("player"))
        self.assertIsNotNone(self.player, "player should exist in game state")
        # Ensure player has health
        self.player.properties["health"] = 100

    def test_water_entry_starts_breath_timer(self) -> None:
        """Entering non-breathable location marks player underwater."""
        self.player.location = "tidal_passage"

        result = on_turn_drowning(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("hold your breath", (result.feedback or "").lower())
        self.assertIn(str(MAX_BREATH), result.feedback or "")
        self.assertTrue(self.player.properties.get("underwater"))

    def test_breathing_item_prevents_timer(self) -> None:
        """Having a breathing_item in inventory allows safe underwater travel."""
        # Give player a breathing item
        air_bladder = next(i for i in self.state.items if i.id == "air_bladder")
        air_bladder.location = "player"
        self.player.location = "tidal_passage"

        result = on_turn_drowning(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("breathing equipment", (result.feedback or "").lower())

    def test_breath_warning_at_threshold(self) -> None:
        """Warning appears when breath gets low."""
        self.player.location = "tidal_passage"
        self.player.properties["underwater"] = True
        self.player.properties["breath_state"] = {
            "current": WARNING_THRESHOLD - 1,
            "max": MAX_BREATH,
        }

        result = on_turn_drowning(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("burning", (result.feedback or "").lower())

    def test_breath_critical_warning(self) -> None:
        """Critical warning appears when near drowning."""
        self.player.location = "tidal_passage"
        self.player.properties["underwater"] = True
        self.player.properties["breath_state"] = {
            "current": CRITICAL_THRESHOLD - 1,
            "max": MAX_BREATH,
        }

        result = on_turn_drowning(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("suffocating", (result.feedback or "").lower())

    def test_drowning_damage_at_max(self) -> None:
        """Drowning causes damage when breath exceeds max."""
        self.player.location = "tidal_passage"
        self.player.properties["underwater"] = True
        self.player.properties["health"] = 100
        self.player.properties["breath_state"] = {
            "current": MAX_BREATH - 1,
            "max": MAX_BREATH,
        }

        result = on_turn_drowning(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("drowning", (result.feedback or "").lower())
        self.assertEqual(self.player.properties["health"], 100 - DROWN_DAMAGE)

    def test_surfacing_resets_breath(self) -> None:
        """Moving to breathable location resets breath counter."""
        self.player.location = "survivor_camp"
        self.player.properties["underwater"] = True
        self.player.properties["breath_state"] = {
            "current": 8,
            "max": MAX_BREATH,
        }

        result = on_turn_drowning(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("gasping", (result.feedback or "").lower())
        self.assertFalse(self.player.properties.get("underwater"))

        # Breath should be reset
        breath = self.player.properties.get("breath_state")
        self.assertIsNotNone(breath)
        self.assertEqual(breath["current"], 0)


class TestDualRescueImpossibleChoiceScenarios(SunkenDistrictTestCase):
    """Tests demonstrating the designed impossible choice."""

    def setUp(self) -> None:
        super().setUp()
        self.delvan = self.state.actors.get(ActorId("merchant_delvan"))
        self.garrett = self.state.actors.get(ActorId("sailor_garrett"))
        self.assertIsNotNone(self.delvan)
        self.assertIsNotNone(self.garrett)

        # Ensure commit_garrett_rescue config exists
        configs = self.state.extra.setdefault("commitment_configs", {})
        if "commit_garrett_rescue" not in configs:
            configs["commit_garrett_rescue"] = {
                "id": "commit_garrett_rescue",
                "description": "Rescue Sailor Garrett from drowning",
                "deadline_turns": 5,
                "target_actor": "sailor_garrett",
            }

    def _make_garrett_location_entity(self) -> Any:
        """Create a location-like object whose id triggers on_garrett_encounter."""
        class _GarrettRoom:
            id = "garrett_sea_caves"
            properties = {}
        return _GarrettRoom()

    def test_save_garrett_delvan_dies(self) -> None:
        """Choosing to save Garrett first leaves Delvan to die."""
        garrett_room = self._make_garrett_location_entity()

        # Find both
        on_delvan_encounter(self.delvan, self.accessor, {})
        on_garrett_encounter(garrett_room, self.accessor, {})

        # Save Garrett
        on_rescue_success(self.garrett, self.accessor, {"condition_type": "drowning"})

        # Delvan dies (simulated by time running out)
        result = on_npc_death(self.delvan, self.accessor, {})

        self.assert_flag_set("garrett_rescued")
        self.assert_flag_set("delvan_died")
        self.assertIn("too late", (result.feedback or "").lower())

    def test_save_delvan_garrett_drowns(self) -> None:
        """Choosing to save Delvan first leaves Garrett to drown."""
        garrett_room = self._make_garrett_location_entity()

        # Find both
        on_delvan_encounter(self.delvan, self.accessor, {})
        on_garrett_encounter(garrett_room, self.accessor, {})

        # Save Delvan
        on_rescue_success(self.delvan, self.accessor, {"condition_type": "bleeding"})

        # Garrett drowns (shorter timer)
        result = on_npc_death(self.garrett, self.accessor, {})

        self.assert_flag_set("delvan_rescued")
        self.assert_flag_set("garrett_died")
        self.assertIn("chose", (result.feedback or "").lower())

    def test_both_die_if_delayed(self) -> None:
        """Both die if player doesn't act quickly enough."""
        garrett_room = self._make_garrett_location_entity()

        # Find both
        on_delvan_encounter(self.delvan, self.accessor, {})
        on_garrett_encounter(garrett_room, self.accessor, {})

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
