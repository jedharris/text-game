"""Scenario tests for Beast Wilds region using real game state.

Tests multi-step gameplay scenarios including:
- Sira rescue (time-sensitive commitment)
- Bear cubs healing (commitment with promise trigger)
- Wolf pack feeding (trust building)
- Bee Queen trading (cross-region collection)
- Spider nest combat
"""

import unittest
from pathlib import Path
from typing import Any

from tests.conftest import BaseTestCase
from src.game_engine import GameEngine
from src.state_accessor import StateAccessor
from src.infrastructure_utils import get_current_state, transition_state

from examples.big_game.behaviors.regions.beast_wilds.sira_rescue import (
    on_sira_death,
    on_sira_encounter,
    on_sira_healed,
)
from examples.big_game.behaviors.regions.beast_wilds.bear_cubs import (
    on_bear_commitment,
    on_cubs_died,
    on_cubs_healed,
)
from examples.big_game.behaviors.regions.beast_wilds.wolf_pack import (
    on_receive_item as on_wolf_feed,
)
from examples.big_game.behaviors.regions.beast_wilds.bee_queen import (
    on_receive_item as on_flower_offer,
    on_honey_theft,
)
from examples.big_game.behaviors.regions.beast_wilds.spider_nest import (
    on_spider_queen_death,
    on_spider_respawn_check,
    on_web_movement,
)

GAME_DIR = (Path(__file__).parent.parent.parent / 'examples' / 'big_game').resolve()


class BeastWildsScenariosTestCase(BaseTestCase):
    """Base class for beast wilds scenario tests with real game state."""

    def setUp(self) -> None:
        self.engine = GameEngine(GAME_DIR)
        self.state = self.engine.game_state
        self.accessor = StateAccessor(self.state, self.engine.behavior_manager)

    def _init_state_machine(self, actor_id: str) -> None:
        """Ensure state machine has 'current' set from 'initial'."""
        actor = self.state.actors.get(actor_id)
        if actor:
            sm = actor.properties.get("state_machine", {})
            if "current" not in sm:
                sm["current"] = sm["initial"]

    def _find_item(self, item_id: str) -> Any:
        """Find item by ID in state.items list."""
        for item in self.state.items:
            if item.id == item_id:
                return item
        self.fail(f"Item {item_id} not found in game state")

    def _get_actor_state(self, actor_id: str) -> str:
        """Get the current state machine state for an actor."""
        actor = self.state.actors.get(actor_id)
        self.assertIsNotNone(actor, f"Actor {actor_id} should exist")
        sm = actor.properties.get("state_machine", {})
        return sm.get("current", sm.get("initial", ""))

    def _get_actor_trust(self, actor_id: str) -> int:
        """Get the current trust value for an actor."""
        actor = self.state.actors.get(actor_id)
        self.assertIsNotNone(actor, f"Actor {actor_id} should exist")
        return actor.properties.get("trust_state", {}).get("current", 0)


# =============================================================================
# Sira Rescue Scenarios
# =============================================================================


class TestSiraRescueScenarios(BeastWildsScenariosTestCase):
    """Tests for Hunter Sira rescue scenarios."""

    def setUp(self) -> None:
        super().setUp()
        self.sira = self.state.actors.get("hunter_sira")
        self.assertIsNotNone(self.sira, "hunter_sira should exist in game state")
        self._init_state_machine("hunter_sira")

    def test_sira_encounter_starts_commitment(self) -> None:
        """First encounter with Sira starts the rescue commitment."""
        result = on_sira_encounter(self.sira, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("critical", (result.feedback or "").lower())
        self.assertTrue(self.state.extra.get("sira_commitment_created"))
        self.assertIsNotNone(self.state.extra.get("sira_first_encounter_turn"))

    def test_sira_encounter_idempotent(self) -> None:
        """Subsequent encounters don't create duplicate commitments."""
        on_sira_encounter(self.sira, self.accessor, {})
        first_turn = self.state.extra["sira_first_encounter_turn"]

        # Encounter again
        result = on_sira_encounter(self.sira, self.accessor, {})

        # Should not change the turn and should return no feedback
        self.assertEqual(self.state.extra["sira_first_encounter_turn"], first_turn)
        self.assertIsNone(result.feedback)

    def test_sira_healing_bleeding_first(self) -> None:
        """Healing Sira's bleeding is tracked."""
        on_sira_encounter(self.sira, self.accessor, {})

        result = on_sira_healed(
            self.sira, self.accessor, {"condition_type": "bleeding"}
        )

        self.assertTrue(result.allow)
        self.assertIn("bleeding stops", (result.feedback or "").lower())
        self.assertTrue(self.state.extra.get("sira_bleeding_stopped"))

    def test_sira_healing_leg_after_bleeding(self) -> None:
        """Healing both conditions fulfills the rescue."""
        on_sira_encounter(self.sira, self.accessor, {})

        # Heal bleeding first
        on_sira_healed(self.sira, self.accessor, {"condition_type": "bleeding"})

        # Then heal leg
        result = on_sira_healed(
            self.sira, self.accessor, {"condition_type": "broken_leg"}
        )

        self.assertTrue(result.allow)
        self.assertIn("saved my life", (result.feedback or "").lower())
        self.assertTrue(self.state.extra.get("sira_healed"))
        self.assertTrue(self.state.extra.get("sira_leg_healed"))

    def test_sira_death_creates_gossip(self) -> None:
        """Sira dying after commitment creates gossip."""
        # Start commitment
        on_sira_encounter(self.sira, self.accessor, {})
        self.assertTrue(self.state.extra.get("sira_commitment_created"))

        # Sira dies
        result = on_sira_death(self.sira, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("travel", (result.feedback or "").lower())
        self.assertTrue(self.state.extra.get("sira_died_with_player"))

    def test_sira_death_without_encounter_no_gossip(self) -> None:
        """Sira dying without player encounter creates no gossip flag."""
        result = on_sira_death(self.sira, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertFalse(self.state.extra.get("sira_died_with_player", False))


# =============================================================================
# Bear Cubs Scenarios
# =============================================================================


class TestBearCubsScenarios(BeastWildsScenariosTestCase):
    """Tests for bear cubs healing scenarios."""

    def setUp(self) -> None:
        super().setUp()
        self.bear = self.state.actors.get("dire_bear")
        self.assertIsNotNone(self.bear, "dire_bear should exist")
        self._init_state_machine("dire_bear")
        self._init_state_machine("bear_cub_1")
        self._init_state_machine("bear_cub_2")

        # Add commitment config for bear cubs (not in default game state)
        if "commitment_configs" not in self.state.extra:
            self.state.extra["commitment_configs"] = {}
        if "commit_bear_cubs" not in self.state.extra["commitment_configs"]:
            self.state.extra["commitment_configs"]["commit_bear_cubs"] = {
                "id": "commit_bear_cubs",
                "target_actor": "dire_bear",
                "description": "Heal the dire bear's sick cubs",
                "deadline_turns": 30,
            }
        if "active_commitments" not in self.state.extra:
            self.state.extra["active_commitments"] = []

    def test_commitment_triggers_on_help_keyword(self) -> None:
        """Saying 'help' to bear creates commitment."""
        result = on_bear_commitment(
            self.bear, self.accessor, {"keyword": "help"}
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("southern", (result.feedback or "").lower())
        self.assertTrue(self.state.extra.get("bear_cubs_commitment_created"))

    def test_commitment_requires_keyword(self) -> None:
        """Random dialog shouldn't trigger commitment."""
        result = on_bear_commitment(
            self.bear, self.accessor, {"keyword": "hello"}
        )

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)
        self.assertFalse(self.state.extra.get("bear_cubs_commitment_created", False))

    def test_commitment_idempotent(self) -> None:
        """Can't create duplicate commitments."""
        on_bear_commitment(
            self.bear, self.accessor, {"keyword": "help"}
        )

        result = on_bear_commitment(
            self.bear, self.accessor, {"keyword": "help"}
        )

        self.assertIn("already promised", (result.feedback or "").lower())

    def test_healing_cubs_with_herbs(self) -> None:
        """Using healing herbs on cubs heals them and transitions bear."""
        herbs = self._find_item("healing_herbs")
        cub1 = self.state.actors.get("bear_cub_1")
        self.assertIsNotNone(cub1)

        result = on_cubs_healed(herbs, self.accessor, {"target": cub1})

        self.assertTrue(result.allow)
        self.assertIn("cubs eagerly consume", (result.feedback or "").lower())
        self.assertTrue(self.state.extra.get("cubs_healed"))

        # Cubs should be recovering
        self.assertTrue(cub1.properties.get("recovering"))
        self.assertFalse(cub1.properties.get("sick"))

        # Bear should be grateful
        self.assertEqual(self._get_actor_state("dire_bear"), "grateful")
        # Trust should have increased from initial -2
        self.assertGreater(self._get_actor_trust("dire_bear"), -2)

    def test_commitment_failure_kills_cubs(self) -> None:
        """Failed commitment causes cubs to die and bear to become vengeful."""
        result = on_cubs_died(
            self.bear, self.accessor, {"commitment_id": "commit_bear_cubs"}
        )

        self.assertTrue(result.allow)
        self.assertIn("breathing has stopped", (result.feedback or "").lower())
        self.assertTrue(self.state.extra.get("cubs_died"))

        # Bear should be vengeful
        self.assertEqual(self._get_actor_state("dire_bear"), "vengeful")
        # Bear should hunt player
        self.assertTrue(self.bear.properties.get("hunts_player"))

        # Cubs should be marked dead
        cub1 = self.state.actors.get("bear_cub_1")
        self.assertTrue(cub1.properties.get("dead"))


# =============================================================================
# Wolf Pack Scenarios
# =============================================================================


class TestWolfPackScenarios(BeastWildsScenariosTestCase):
    """Tests for wolf pack feeding and trust scenarios."""

    def setUp(self) -> None:
        super().setUp()
        self.alpha = self.state.actors.get("alpha_wolf")
        self.assertIsNotNone(self.alpha, "alpha_wolf should exist")
        self._init_state_machine("alpha_wolf")
        self._init_state_machine("frost_wolf_1")
        self._init_state_machine("frost_wolf_2")

    def _feed_wolf(self) -> Any:
        """Feed venison to the alpha wolf and return result."""
        venison = self._find_item("venison")
        context = {"item": venison, "item_id": venison.id, "giver_id": "player"}
        return on_wolf_feed(self.alpha, self.accessor, context)

    def test_feeding_wolf_increases_trust(self) -> None:
        """Giving meat to wolf increases trust."""
        # Reset trust to 0 for clean measurement
        self.alpha.properties["trust_state"]["current"] = 0

        result = self._feed_wolf()

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("accepts", (result.feedback or "").lower())
        self.assertEqual(self.alpha.properties["trust_state"]["current"], 1)

    def test_feeding_transitions_state_at_threshold(self) -> None:
        """Feeding transitions hostile wolf to wary at trust 1."""
        self.alpha.properties["trust_state"]["current"] = 0
        sm = self.alpha.properties["state_machine"]
        sm["current"] = "hostile"

        self._feed_wolf()

        self.assertEqual(sm["current"], "wary")
        self.assertEqual(self.alpha.properties["trust_state"]["current"], 1)

    def test_feeding_non_food_rejected(self) -> None:
        """Non-food items don't affect wolf trust."""
        self.alpha.properties["trust_state"]["current"] = 0
        frost_lily = self._find_item("frost_lily")
        context = {"item": frost_lily, "item_id": frost_lily.id, "giver_id": "player"}

        result = on_wolf_feed(self.alpha, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)
        self.assertEqual(self.alpha.properties["trust_state"]["current"], 0)

    def test_trust_progression_to_neutral(self) -> None:
        """Multiple feedings progress wolf through states."""
        # Start at wary with trust 1
        self.alpha.properties["trust_state"]["current"] = 1
        sm = self.alpha.properties["state_machine"]
        sm["current"] = "wary"

        # Feed once: trust 1 -> 2, wary -> neutral
        self._feed_wolf()
        self.assertEqual(sm["current"], "neutral")
        self.assertEqual(self.alpha.properties["trust_state"]["current"], 2)

        # Feed again: trust 2 -> 3, neutral -> friendly
        self._feed_wolf()
        self.assertEqual(sm["current"], "friendly")
        self.assertEqual(self.alpha.properties["trust_state"]["current"], 3)

    def test_feeding_non_wolf_does_nothing(self) -> None:
        """Feeding non-wolf actor has no effect."""
        sira = self.state.actors.get("hunter_sira")
        venison = self._find_item("venison")
        context = {"item": venison, "item_id": venison.id, "giver_id": "player"}

        result = on_wolf_feed(sira, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)


# =============================================================================
# Bee Queen Scenarios
# =============================================================================


class TestBeeQueenScenarios(BeastWildsScenariosTestCase):
    """Tests for Bee Queen trading scenarios."""

    def setUp(self) -> None:
        super().setUp()
        self.queen = self.state.actors.get("bee_queen")
        self.assertIsNotNone(self.queen, "bee_queen should exist")
        self._init_state_machine("bee_queen")
        # Set queen to neutral for trading tests (initial is defensive)
        self.queen.properties["state_machine"]["current"] = "neutral"

    def _offer_flower(self, item_id: str) -> Any:
        """Offer a flower item to the bee queen."""
        flower = self._find_item(item_id)
        context = {"item": flower, "item_id": flower.id, "giver_id": "player"}
        return on_flower_offer(self.queen, self.accessor, context)

    def test_first_flower_trade(self) -> None:
        """First flower trade transitions queen to trading state."""
        result = self._offer_flower("moonpetal")

        self.assertTrue(result.allow)
        self.assertIn("accepts", (result.feedback or "").lower())
        self.assertIn("2 more", result.feedback or "")

        # Should track flower
        traded = self.state.extra.get("bee_queen_flowers_traded", [])
        self.assertIn("moonpetal", traded)

        # Should transition to trading
        self.assertEqual(self._get_actor_state("bee_queen"), "trading")

        # Should increase trust
        self.assertGreater(self._get_actor_trust("bee_queen"), 0)

    def test_duplicate_flower_type_rejected(self) -> None:
        """Same flower type cannot be traded twice."""
        self._offer_flower("moonpetal")

        result = self._offer_flower("moonpetal")

        self.assertIn("already received", (result.feedback or "").lower())

    def test_non_flower_rejected(self) -> None:
        """Non-flower items are rejected by queen."""
        venison = self._find_item("venison")
        context = {"item": venison, "item_id": venison.id, "giver_id": "player"}

        result = on_flower_offer(self.queen, self.accessor, context)

        self.assertIn("not what she seeks", (result.feedback or "").lower())

    def test_three_flowers_allies_queen(self) -> None:
        """Trading three different flowers transitions to allied."""
        self._offer_flower("moonpetal")
        self._offer_flower("frost_lily")
        result = self._offer_flower("water_bloom")

        self.assertIn("ally", (result.feedback or "").lower())
        self.assertEqual(self._get_actor_state("bee_queen"), "allied")
        self.assertEqual(self.state.extra.get("bee_queen_honey_count"), 3)

    def test_honey_theft_makes_hostile(self) -> None:
        """Taking honey without permission makes queen hostile."""
        honey = self._find_item("royal_honey")
        # honey.location is bee_queen_clearing which contains "bee"

        result = on_honey_theft(honey, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("hatred", (result.feedback or "").lower())
        self.assertEqual(self._get_actor_state("bee_queen"), "hostile")
        self.assertTrue(self.state.extra.get("bee_grove_hostile"))
        self.assertTrue(self.state.extra.get("bee_trade_destroyed"))

    def test_honey_take_allowed_when_allied(self) -> None:
        """Taking honey is allowed when queen is allied."""
        self.queen.properties["state_machine"]["current"] = "allied"
        honey = self._find_item("royal_honey")

        result = on_honey_theft(honey, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)
        self.assertFalse(self.state.extra.get("bee_grove_hostile", False))


# =============================================================================
# Spider Nest Scenarios
# =============================================================================


class TestSpiderNestScenarios(BeastWildsScenariosTestCase):
    """Tests for spider nest combat scenarios."""

    def setUp(self) -> None:
        super().setUp()
        self.queen = self.state.actors.get("spider_matriarch")
        self.assertIsNotNone(self.queen, "spider_matriarch should exist")
        self._init_state_machine("spider_matriarch")
        self._init_state_machine("giant_spider_1")
        self._init_state_machine("giant_spider_2")

    def test_queen_death_stops_respawns(self) -> None:
        """Killing queen sets flag to stop future respawns."""
        result = on_spider_queen_death(self.queen, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("broken", (result.feedback or "").lower())
        self.assertTrue(self.state.extra.get("spider_queen_dead"))

    def test_respawn_requires_living_queen(self) -> None:
        """Spiders don't respawn if queen is dead."""
        self.queen.properties["state_machine"]["current"] = "dead"
        self.state.extra["spider_last_respawn"] = 0
        self.state.extra["turn_count"] = 15

        result = on_spider_respawn_check(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_respawn_happens_with_living_queen(self) -> None:
        """Spiders respawn when queen lives and a spider is dead."""
        # Kill one spider
        spider1 = self.state.actors.get("giant_spider_1")
        spider1.properties["state_machine"]["current"] = "dead"

        # Set up respawn timing
        self.state.extra["spider_last_respawn"] = 0
        self.state.extra["turn_count"] = 15  # Past the 10-turn interval

        result = on_spider_respawn_check(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("emerge", (result.feedback or "").lower())
        # Spider should be respawned
        self.assertEqual(spider1.properties["state_machine"]["current"], "hostile")
        self.assertEqual(spider1.location, "spider_thicket")

    def test_no_respawn_if_enough_spiders_alive(self) -> None:
        """No respawn if 2+ spiders are already alive."""
        self.state.extra["spider_last_respawn"] = 0
        self.state.extra["turn_count"] = 15

        result = on_spider_respawn_check(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_web_movement_no_match_for_real_locations(self) -> None:
        """Web movement handler doesn't match real spider locations.

        Note: The handler checks for "spider_nest" in dest_id, but the
        real game locations are "spider_thicket" and "spider_matriarch_lair".
        This test documents that the handler returns no feedback for real
        locations. When the handler is fixed to match actual location IDs,
        this test should be updated to verify web warning feedback.
        """
        dest = None
        for loc in self.state.locations:
            if loc.id == "spider_thicket":
                dest = loc
                break
        self.assertIsNotNone(dest, "spider_thicket location should exist")

        result = on_web_movement(None, self.accessor, {"destination": dest})

        self.assertTrue(result.allow)
        # Handler doesn't match because "spider_nest" not in "spider_thicket"
        self.assertIsNone(result.feedback)


if __name__ == "__main__":
    unittest.main()
