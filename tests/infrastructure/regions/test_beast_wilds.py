"""Tests for Beast Wilds region behaviors."""
from src.types import ActorId

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from examples.big_game.behaviors.regions.beast_wilds.wolf_pack import on_wolf_feed
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
from examples.big_game.behaviors.regions.beast_wilds.bee_queen import on_flower_offer, on_honey_theft


class MockActor:
    """Mock actor for testing."""

    def __init__(self, actor_id: str, properties: dict | None = None) -> None:
        self.id = actor_id
        self.properties: dict = properties or {}


class MockItem:
    """Mock item for testing."""

    def __init__(self, item_id: str) -> None:
        self.id = item_id


class MockState:
    """Mock game state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}
        self.actors: dict = {}
        self.locations: list = []


class MockAccessor:
    """Mock state accessor for testing."""

    def __init__(self, state: MockState) -> None:
        self.state = state


# =============================================================================
# Wolf Pack Tests
# =============================================================================


class TestWolfFeed(unittest.TestCase):
    """Tests for wolf feeding mechanics."""

    def test_feeding_wolf_increases_trust(self) -> None:
        """Feeding the alpha wolf increases trust."""
        state = MockState()
        alpha = MockActor(
            "npc_alpha_wolf",
            {
                "trust_state": {"current": 0, "floor": -3, "ceiling": 6},
                "state_machine": {"states": ["hostile", "wary"], "initial": "hostile"},
            },
        )
        state.actors[ActorId("npc_alpha_wolf")] = alpha
        accessor = MockAccessor(state)

        item = MockItem("item_venison")
        target = MockActor("npc_alpha_wolf", {})
        context = {"target_actor": target, "item": item}

        result = on_wolf_feed(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(alpha.properties["trust_state"]["current"], 1)

    def test_feeding_non_wolf_does_nothing(self) -> None:
        """Feeding non-wolf actor has no effect."""
        state = MockState()
        accessor = MockAccessor(state)

        item = MockItem("item_venison")
        target = MockActor("npc_sira", {})
        context = {"target_actor": target, "item": item}

        result = on_wolf_feed(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_feeding_hostile_wolf_transitions_to_wary(self) -> None:
        """First feeding transitions hostile wolf to wary."""
        state = MockState()
        alpha = MockActor(
            "npc_alpha_wolf",
            {
                "trust_state": {"current": 0, "floor": -3, "ceiling": 6},
                "state_machine": {
                    "states": ["hostile", "wary", "neutral", "friendly"],
                    "initial": "hostile",
                },
            },
        )
        state.actors[ActorId("npc_alpha_wolf")] = alpha
        accessor = MockAccessor(state)

        item = MockItem("item_venison")
        target = alpha
        context = {"target_actor": target, "item": item}

        on_wolf_feed(item, accessor, context)

        self.assertEqual(alpha.properties["trust_state"]["current"], 1)
        self.assertEqual(alpha.properties["state_machine"]["current"], "wary")


# =============================================================================
# Sira Rescue Tests
# =============================================================================


class TestSiraEncounter(unittest.TestCase):
    """Tests for Sira first encounter mechanics."""

    def test_first_encounter_creates_commitment(self) -> None:
        """First encounter with Sira creates rescue commitment."""
        state = MockState()
        state.extra["turn_count"] = 5
        # Setup commitment config (normally in game_state.json)
        state.extra["commitment_configs"] = {
            "commit_sira_rescue": {
                "id": "commit_sira_rescue",
                "target_npc": "npc_hunter_sira",
                "goal": "Stop Sira's bleeding and heal her leg",
                "base_timer": 8,
                "hope_bonus": 4,
            }
        }
        state.extra["active_commitments"] = []
        accessor = MockAccessor(state)

        sira = MockActor("npc_hunter_sira", {})
        context: dict[str, Any] = {}

        result = on_sira_encounter(sira, accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(state.extra.get("sira_commitment_created"))
        self.assertIsNotNone(result.feedback)

    def test_second_encounter_does_not_duplicate(self) -> None:
        """Second encounter doesn't create duplicate commitment."""
        state = MockState()
        state.extra["sira_commitment_created"] = True
        accessor = MockAccessor(state)

        sira = MockActor("npc_hunter_sira", {})
        context: dict[str, Any] = {}

        result = on_sira_encounter(sira, accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)


class TestSiraDeath(unittest.TestCase):
    """Tests for Sira death mechanics."""

    def test_sira_death_creates_gossip(self) -> None:
        """Sira's death creates gossip to Elara."""
        state = MockState()
        state.extra["turn_count"] = 10
        state.extra["sira_commitment_created"] = True
        accessor = MockAccessor(state)

        sira = MockActor("npc_hunter_sira", {})
        context: dict[str, Any] = {}

        result = on_sira_death(sira, accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(state.extra.get("sira_died_with_player"))
        self.assertIsNotNone(result.feedback)


# =============================================================================
# Bear Cubs Tests
# =============================================================================


class TestBearCommitment(unittest.TestCase):
    """Tests for bear cubs commitment mechanics."""

    def test_commitment_keywords_create_commitment(self) -> None:
        """Commitment keywords create the cubs commitment."""
        state = MockState()
        state.extra["turn_count"] = 0
        # Setup commitment config (normally in game_state.json)
        state.extra["commitment_configs"] = {
            "commit_bear_cubs": {
                "id": "commit_bear_cubs",
                "target_npc": "npc_dire_bear",
                "goal": "Give healing_herbs to bear cubs",
                "base_timer": 30,
                "hope_bonus": 5,
            }
        }
        state.extra["active_commitments"] = []
        accessor = MockAccessor(state)

        bear = MockActor("npc_dire_bear", {})
        state.actors[ActorId("npc_dire_bear")] = bear
        context = {"keyword": "I'll find medicine for them"}

        result = on_bear_commitment(bear, accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(state.extra.get("bear_cubs_commitment_created"))

    def test_non_commitment_keyword_ignored(self) -> None:
        """Non-commitment keywords don't create commitment."""
        state = MockState()
        accessor = MockAccessor(state)

        bear = MockActor("npc_dire_bear", {})
        context = {"keyword": "hello there"}

        result = on_bear_commitment(bear, accessor, context)

        self.assertTrue(result.allow)
        self.assertFalse(state.extra.get("bear_cubs_commitment_created", False))


class TestCubsHealed(unittest.TestCase):
    """Tests for cubs healing mechanics."""

    def test_healing_herbs_heals_cubs(self) -> None:
        """Using healing herbs on cubs heals them."""
        state = MockState()
        bear = MockActor(
            "npc_dire_bear",
            {
                "state_machine": {"states": ["hostile", "grateful"], "initial": "hostile"},
                "trust_state": {"current": 0, "floor": -5, "ceiling": 5},
            },
        )
        cub1 = MockActor("npc_bear_cub_1", {"sick": True})
        cub2 = MockActor("npc_bear_cub_2", {"sick": True})
        state.actors[ActorId("npc_dire_bear")] = bear
        state.actors[ActorId("npc_bear_cub_1")] = cub1
        state.actors[ActorId("npc_bear_cub_2")] = cub2
        accessor = MockAccessor(state)

        item = MockItem("item_healing_herbs")
        context = {"target": cub1}

        result = on_cubs_healed(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(state.extra.get("cubs_healed"))
        self.assertEqual(bear.properties["state_machine"]["current"], "grateful")
        self.assertFalse(cub1.properties.get("sick", True))


class TestCubsDied(unittest.TestCase):
    """Tests for cubs death mechanics."""

    def test_cubs_death_makes_bear_vengeful(self) -> None:
        """Cubs dying makes bear vengeful."""
        state = MockState()
        bear = MockActor(
            "npc_dire_bear",
            {
                "state_machine": {
                    "states": ["hostile", "vengeful"],
                    "initial": "hostile",
                },
                "trust_state": {"current": 0, "floor": -5, "ceiling": 5},
            },
        )
        cub1 = MockActor("npc_bear_cub_1", {})
        cub2 = MockActor("npc_bear_cub_2", {})
        state.actors[ActorId("npc_dire_bear")] = bear
        state.actors[ActorId("npc_bear_cub_1")] = cub1
        state.actors[ActorId("npc_bear_cub_2")] = cub2
        accessor = MockAccessor(state)

        entity = MagicMock()
        context = {"commitment_id": "commit_bear_cubs"}

        result = on_cubs_died(entity, accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(bear.properties["state_machine"]["current"], "vengeful")
        self.assertTrue(bear.properties.get("hunts_player"))
        self.assertTrue(cub1.properties.get("dead"))


# =============================================================================
# Bee Queen Tests
# =============================================================================


class TestFlowerOffer(unittest.TestCase):
    """Tests for bee queen flower trade mechanics."""

    def test_valid_flower_accepted(self) -> None:
        """Valid flower type is accepted by queen."""
        state = MockState()
        queen = MockActor(
            "bee_queen",
            {
                "state_machine": {
                    "states": ["neutral", "trading", "allied"],
                    "initial": "neutral",
                },
                "trust_state": {"current": 0},
            },
        )
        state.actors[ActorId("bee_queen")] = queen
        accessor = MockAccessor(state)

        item = MockItem("item_moonpetal")
        target = queen
        context = {"target_actor": target, "item": item}

        result = on_flower_offer(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("moonpetal", state.extra.get("bee_queen_flowers_traded", []))
        self.assertEqual(queen.properties["state_machine"]["current"], "trading")

    def test_invalid_item_rejected(self) -> None:
        """Non-flower items are rejected."""
        state = MockState()
        queen = MockActor("bee_queen", {})
        state.actors[ActorId("bee_queen")] = queen
        accessor = MockAccessor(state)

        item = MockItem("item_rock")
        context = {"target_actor": queen, "item": item}

        result = on_flower_offer(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("not what she seeks", result.feedback or "")

    def test_three_flowers_unlock_allied(self) -> None:
        """Trading three unique flowers unlocks allied state."""
        state = MockState()
        state.extra["bee_queen_flowers_traded"] = ["moonpetal", "frost_lily"]
        queen = MockActor(
            "bee_queen",
            {
                "state_machine": {
                    "states": ["neutral", "trading", "allied"],
                    "initial": "neutral",
                    "current": "trading",
                },
                "trust_state": {"current": 2},
            },
        )
        state.actors[ActorId("bee_queen")] = queen
        accessor = MockAccessor(state)

        item = MockItem("item_water_bloom")
        context = {"target_actor": queen, "item": item}

        result = on_flower_offer(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(queen.properties["state_machine"]["current"], "allied")


class TestHoneyTheft(unittest.TestCase):
    """Tests for honey theft mechanics."""

    def test_theft_makes_queen_hostile(self) -> None:
        """Taking honey without permission makes queen hostile."""
        state = MockState()
        queen = MockActor(
            "bee_queen",
            {
                "state_machine": {
                    "states": ["neutral", "hostile"],
                    "initial": "neutral",
                },
            },
        )
        state.actors[ActorId("bee_queen")] = queen
        accessor = MockAccessor(state)

        item = MockItem("item_royal_honey")
        location = MockActor("loc_beehive_grove", {})  # Using MockActor for location
        context = {"location": location}

        result = on_honey_theft(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(queen.properties["state_machine"]["current"], "hostile")
        self.assertTrue(state.extra.get("bee_trade_destroyed"))

    def test_allied_queen_allows_honey(self) -> None:
        """Allied queen allows taking honey."""
        state = MockState()
        queen = MockActor(
            "bee_queen",
            {
                "state_machine": {
                    "states": ["neutral", "allied"],
                    "initial": "neutral",
                    "current": "allied",
                },
            },
        )
        state.actors[ActorId("bee_queen")] = queen
        accessor = MockAccessor(state)

        item = MockItem("item_royal_honey")
        location = MockActor("loc_beehive_grove", {})
        context = {"location": location}

        result = on_honey_theft(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertFalse(state.extra.get("bee_trade_destroyed", False))


if __name__ == "__main__":
    unittest.main()
