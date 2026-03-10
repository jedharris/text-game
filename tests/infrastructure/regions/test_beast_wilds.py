"""Tests for Beast Wilds region behaviors using real game state.

Tests load big_game via GameEngine to use actual actor IDs, state machines,
and property structures. Each test gets a fresh engine instance.
"""

import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from tests.conftest import BaseTestCase
from src.game_engine import GameEngine
from src.state_accessor import StateAccessor
from src.infrastructure_utils import get_current_state, transition_state

GAME_DIR = (Path(__file__).parent.parent.parent.parent / 'examples' / 'big_game').resolve()


class BeastWildsTestCase(BaseTestCase):
    """Base class for beast wilds tests with real game state."""

    def setUp(self):
        self.engine = GameEngine(GAME_DIR)
        self.state = self.engine.game_state
        self.accessor = StateAccessor(
            self.state,
            self.engine.behavior_manager
        )


# =============================================================================
# Wolf Pack Tests
# =============================================================================


class TestWolfFeed(BeastWildsTestCase):
    """Tests for wolf feeding mechanics."""

    def setUp(self):
        super().setUp()
        from examples.big_game.behaviors.regions.beast_wilds.wolf_pack import on_receive_item
        self.on_wolf_feed = on_receive_item
        self.alpha = self.state.actors.get("alpha_wolf")
        # Reset trust to 0 for clean test
        self.alpha.properties["trust_state"]["current"] = 0
        # Ensure state machine has current state
        sm = self.alpha.properties["state_machine"]
        sm["current"] = sm.get("current", sm["initial"])

    def _feed_wolf(self):
        """Feed venison to the alpha wolf.

        on_receive_item is invoked via invoke_behavior(recipient, ...),
        so entity is the wolf (recipient), not the item.
        """
        venison = None
        for item in self.state.items:
            if item.id == "venison":
                venison = item
                break
        self.assertIsNotNone(venison, "venison item should exist in game state")
        context = {"item": venison, "item_id": venison.id, "giver_id": "player"}
        return self.on_wolf_feed(self.alpha, self.accessor, context)

    def test_feeding_wolf_increases_trust(self) -> None:
        """Feeding the alpha wolf increases trust."""
        result = self._feed_wolf()

        self.assertTrue(result.allow)
        self.assertEqual(self.alpha.properties["trust_state"]["current"], 1)

    def test_feeding_non_wolf_does_nothing(self) -> None:
        """Feeding non-wolf actor has no effect."""
        sira = self.state.actors.get("hunter_sira")
        venison = None
        for item in self.state.items:
            if item.id == "venison":
                venison = item
                break
        context = {"item": venison, "item_id": venison.id, "giver_id": "player"}

        result = self.on_wolf_feed(sira, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_feeding_hostile_wolf_transitions_to_wary(self) -> None:
        """First feeding transitions hostile wolf to wary."""
        sm = self.alpha.properties["state_machine"]
        sm["current"] = "hostile"

        result = self._feed_wolf()

        self.assertEqual(self.alpha.properties["trust_state"]["current"], 1)
        self.assertEqual(sm["current"], "wary")


# =============================================================================
# Sira Rescue Tests
# =============================================================================


class TestSiraEncounter(BeastWildsTestCase):
    """Tests for Sira first encounter mechanics."""

    def setUp(self):
        super().setUp()
        from examples.big_game.behaviors.regions.beast_wilds.sira_rescue import (
            on_sira_encounter,
            on_sira_death,
        )
        self.on_sira_encounter = on_sira_encounter
        self.on_sira_death = on_sira_death
        self.sira = self.state.actors.get("hunter_sira")

    def test_first_encounter_creates_commitment(self) -> None:
        """First encounter with Sira creates rescue commitment."""
        context: dict[str, Any] = {}

        result = self.on_sira_encounter(self.sira, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(self.state.extra.get("sira_commitment_created"))
        self.assertIsNotNone(result.feedback)

    def test_second_encounter_does_not_duplicate(self) -> None:
        """Second encounter doesn't create duplicate commitment."""
        self.state.extra["sira_commitment_created"] = True
        context: dict[str, Any] = {}

        result = self.on_sira_encounter(self.sira, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)


class TestSiraDeath(BeastWildsTestCase):
    """Tests for Sira death mechanics."""

    def test_sira_death_creates_gossip(self) -> None:
        """Sira's death creates gossip when commitment exists."""
        from examples.big_game.behaviors.regions.beast_wilds.sira_rescue import on_sira_death

        sira = self.state.actors.get("hunter_sira")
        self.state.extra["turn_count"] = 10
        self.state.extra["sira_commitment_created"] = True
        context: dict[str, Any] = {}

        result = on_sira_death(sira, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(self.state.extra.get("sira_died_with_player"))
        self.assertIsNotNone(result.feedback)


# =============================================================================
# Bear Cubs Tests
# =============================================================================


class TestBearCommitment(BeastWildsTestCase):
    """Tests for bear cubs commitment mechanics."""

    def setUp(self):
        super().setUp()
        from examples.big_game.behaviors.regions.beast_wilds.bear_cubs import on_bear_commitment
        self.on_bear_commitment = on_bear_commitment
        self.bear = self.state.actors.get("dire_bear")
        # Add commitment config if not present (handler expects it)
        if "commitment_configs" not in self.state.extra:
            self.state.extra["commitment_configs"] = {}
        if "commit_bear_cubs" not in self.state.extra["commitment_configs"]:
            self.state.extra["commitment_configs"]["commit_bear_cubs"] = {
                "id": "commit_bear_cubs",
                "target_npc": "dire_bear",
                "goal": "Give healing_herbs to bear cubs",
                "deadline_turns": 30,
            }
        if "active_commitments" not in self.state.extra:
            self.state.extra["active_commitments"] = []

    def test_commitment_keywords_create_commitment(self) -> None:
        """Commitment keywords create the cubs commitment."""
        context = {"keyword": "I'll find medicine for them"}

        result = self.on_bear_commitment(self.bear, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(self.state.extra.get("bear_cubs_commitment_created"))

    def test_non_commitment_keyword_ignored(self) -> None:
        """Non-commitment keywords don't create commitment."""
        context = {"keyword": "hello there"}

        result = self.on_bear_commitment(self.bear, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertFalse(self.state.extra.get("bear_cubs_commitment_created", False))


class TestCubsHealed(BeastWildsTestCase):
    """Tests for cubs healing mechanics."""

    def test_healing_herbs_heals_cubs(self) -> None:
        """Using healing herbs on cubs heals them."""
        from examples.big_game.behaviors.regions.beast_wilds.bear_cubs import on_cubs_healed

        bear = self.state.actors.get("dire_bear")
        cub1 = self.state.actors.get("bear_cub_1")
        self.assertIsNotNone(cub1, "bear_cub_1 should exist in game state")

        # Find healing herbs
        herbs = None
        for item in self.state.items:
            if item.id == "healing_herbs":
                herbs = item
                break
        self.assertIsNotNone(herbs, "healing_herbs should exist in game state")

        context = {"target": cub1}
        result = on_cubs_healed(herbs, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(self.state.extra.get("cubs_healed"))
        # Bear should transition to grateful
        sm = bear.properties.get("state_machine", {})
        current = sm.get("current", sm.get("initial"))
        self.assertEqual(current, "grateful")
        self.assertFalse(cub1.properties.get("sick", True))


class TestCubsDied(BeastWildsTestCase):
    """Tests for cubs death mechanics."""

    def test_cubs_death_makes_bear_vengeful(self) -> None:
        """Cubs dying makes bear vengeful."""
        from examples.big_game.behaviors.regions.beast_wilds.bear_cubs import on_cubs_died

        bear = self.state.actors.get("dire_bear")
        cub1 = self.state.actors.get("bear_cub_1")
        self.assertIsNotNone(cub1)

        entity = MagicMock()
        context = {"commitment_id": "commit_bear_cubs"}

        result = on_cubs_died(entity, self.accessor, context)

        self.assertTrue(result.allow)
        sm = bear.properties.get("state_machine", {})
        current = sm.get("current", sm.get("initial"))
        self.assertEqual(current, "vengeful")
        self.assertTrue(bear.properties.get("hunts_player"))
        self.assertTrue(cub1.properties.get("dead"))


# =============================================================================
# Bee Queen Tests
# =============================================================================


class TestFlowerOffer(BeastWildsTestCase):
    """Tests for bee queen flower trade mechanics."""

    def setUp(self):
        super().setUp()
        from examples.big_game.behaviors.regions.beast_wilds.bee_queen import (
            on_receive_item as on_flower_offer,
        )
        self.on_flower_offer = on_flower_offer
        self.queen = self.state.actors.get("bee_queen")
        # Set queen to neutral for trading tests
        sm = self.queen.properties["state_machine"]
        sm["current"] = "neutral"

    def _find_item(self, item_id: str):
        for item in self.state.items:
            if item.id == item_id:
                return item
        self.fail(f"Item {item_id} not found in game state")

    def test_valid_flower_accepted(self) -> None:
        """Valid flower type is accepted by queen."""
        moonpetal = self._find_item("moonpetal")
        context = {"item": moonpetal, "item_id": moonpetal.id, "giver_id": "player"}

        result = self.on_flower_offer(self.queen, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("moonpetal", self.state.extra.get("bee_queen_flowers_traded", []))
        sm = self.queen.properties["state_machine"]
        self.assertEqual(sm["current"], "trading")

    def test_invalid_item_rejected(self) -> None:
        """Non-flower items are rejected."""
        venison = self._find_item("venison")
        context = {"item": venison, "item_id": venison.id, "giver_id": "player"}

        result = self.on_flower_offer(self.queen, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("not what she seeks", result.feedback or "")

    def test_three_flowers_unlock_allied(self) -> None:
        """Trading three unique flowers unlocks allied state."""
        self.state.extra["bee_queen_flowers_traded"] = ["moonpetal", "frost_lily"]
        sm = self.queen.properties["state_machine"]
        sm["current"] = "trading"
        self.queen.properties["trust_state"]["current"] = 2

        water_bloom = self._find_item("water_bloom")
        context = {"item": water_bloom, "item_id": water_bloom.id, "giver_id": "player"}

        result = self.on_flower_offer(self.queen, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(sm["current"], "allied")


class TestHoneyTheft(BeastWildsTestCase):
    """Tests for honey theft mechanics."""

    def setUp(self):
        super().setUp()
        from examples.big_game.behaviors.regions.beast_wilds.bee_queen import on_honey_theft
        self.on_honey_theft = on_honey_theft
        self.queen = self.state.actors.get("bee_queen")

    def _find_honey(self):
        for item in self.state.items:
            if item.id == "royal_honey":
                return item
        self.fail("royal_honey not found in game state")

    def test_theft_makes_queen_hostile(self) -> None:
        """Taking honey without permission makes queen hostile."""
        sm = self.queen.properties["state_machine"]
        sm["current"] = "neutral"
        honey = self._find_honey()
        context = {"location": MagicMock()}

        result = self.on_honey_theft(honey, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(sm["current"], "hostile")
        self.assertTrue(self.state.extra.get("bee_trade_destroyed"))

    def test_allied_queen_allows_honey(self) -> None:
        """Allied queen allows taking honey."""
        sm = self.queen.properties["state_machine"]
        sm["current"] = "allied"
        honey = self._find_honey()
        context = {"location": MagicMock()}

        result = self.on_honey_theft(honey, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertFalse(self.state.extra.get("bee_trade_destroyed", False))


if __name__ == "__main__":
    unittest.main()
