"""Scenario tests for Beast Wilds region.

Tests multi-step gameplay scenarios including:
- Sira rescue (time-sensitive commitment)
- Bear cubs healing (commitment with promise trigger)
- Wolf pack feeding (trust building)
- Bee Queen trading (cross-region collection)
- Spider nest combat
"""

import unittest
from typing import Any

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import clear_handler_cache
from examples.big_game.behaviors.regions.beast_wilds.bear_cubs import (
    on_bear_commitment,
    on_cubs_died,
    on_cubs_healed,
)
from examples.big_game.behaviors.regions.beast_wilds.bee_queen import on_flower_offer, on_honey_theft
from examples.big_game.behaviors.regions.beast_wilds.sira_rescue import (
    on_sira_death,
    on_sira_encounter,
    on_sira_healed,
)
from examples.big_game.behaviors.regions.beast_wilds.spider_nest import (
    on_spider_queen_death,
    on_spider_respawn_check,
    on_web_movement,
)
from examples.big_game.behaviors.regions.beast_wilds.wolf_pack import on_wolf_feed
from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    get_pending_gossip_about,
    modify_trust,
    transition_state,
)
from tests.infrastructure.test_scenario_framework import (
    MockEntity,
    MockItem,
    MockLocation,
    ScenarioAccessor,
    ScenarioState,
    ScenarioTestCase,
)


class TestSiraRescueScenarios(ScenarioTestCase):
    """Tests for Hunter Sira rescue scenarios."""

    def setUp(self) -> None:
        """Set up Sira rescue test fixtures."""
        super().setUp()
        self.setup_player(location="loc_beast_wilds_clearing")

        # Create Sira with bleeding and leg injury
        self.sira = self.state.add_actor(
            "npc_hunter_sira",
            name="Hunter Sira",
            properties={
                "state_machine": {
                    "states": ["critical", "stabilized", "recovering", "dead"],
                    "initial": "critical",
                    "current": "critical",
                },
                "conditions": {
                    "bleeding": {"severity": 50, "type": "bleeding"},
                    "leg_injury": {"severity": 70, "type": "leg_injury"},
                },
            },
            location="loc_beast_wilds_trail",
        )

        # Add commitment config
        self.state.add_commitment_config(
            "commit_sira_rescue",
            duration=20,
            success_condition="sira_healed",
        )

    def test_sira_encounter_starts_commitment(self) -> None:
        """First encounter with Sira starts the rescue commitment."""
        result = on_sira_encounter(self.sira, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("critical", (result.feedback or "").lower())
        self.assert_flag_set("sira_commitment_created")
        self.assert_flag_set("sira_first_encounter_turn")

    def test_sira_encounter_idempotent(self) -> None:
        """Subsequent encounters don't create duplicate commitments."""
        # First encounter
        on_sira_encounter(self.sira, self.accessor, {})
        first_turn = self.state.extra["sira_first_encounter_turn"]

        # Advance time and encounter again
        self.state.advance_turns(5)
        result = on_sira_encounter(self.sira, self.accessor, {})

        # Should not change the turn
        self.assertEqual(self.state.extra["sira_first_encounter_turn"], first_turn)

    def test_sira_healing_bleeding_first(self) -> None:
        """Healing Sira's bleeding is tracked."""
        on_sira_encounter(self.sira, self.accessor, {})

        result = on_sira_healed(
            self.sira, self.accessor, {"condition_type": "bleeding"}
        )

        self.assertTrue(result.allow)
        self.assertIn("bleeding stops", (result.feedback or "").lower())
        self.assert_flag_set("sira_bleeding_stopped")

    def test_sira_healing_leg_after_bleeding(self) -> None:
        """Healing both conditions fulfills the rescue."""
        on_sira_encounter(self.sira, self.accessor, {})

        # Heal bleeding first
        on_sira_healed(self.sira, self.accessor, {"condition_type": "bleeding"})

        # Then heal leg
        result = on_sira_healed(
            self.sira, self.accessor, {"condition_type": "leg_injury"}
        )

        self.assertTrue(result.allow)
        self.assertIn("saved my life", (result.feedback or "").lower())
        self.assert_flag_set("sira_healed")
        self.assert_flag_set("sira_leg_healed")

    def test_sira_death_creates_gossip(self) -> None:
        """Sira dying after commitment creates gossip to Elara."""
        # Start commitment
        on_sira_encounter(self.sira, self.accessor, {})

        # Sira dies (commitment failed)
        result = on_sira_death(self.sira, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("travel", (result.feedback or "").lower())
        self.assert_flag_set("sira_died_with_player")
        self.assert_gossip_pending("Sira")

    def test_sira_death_without_encounter_no_gossip(self) -> None:
        """Sira dying without player encounter creates no gossip."""
        # No encounter - Sira dies elsewhere
        result = on_sira_death(self.sira, self.accessor, {})

        self.assertTrue(result.allow)
        self.assert_flag_not_set("sira_died_with_player")
        self.assert_no_gossip_pending("Sira")


class TestBearCubsScenarios(ScenarioTestCase):
    """Tests for bear cubs healing scenarios."""

    def setUp(self) -> None:
        """Set up bear cubs test fixtures."""
        super().setUp()
        self.setup_player(location="loc_beast_wilds_den")

        # Create dire bear
        self.bear = self.state.add_actor(
            "npc_dire_bear",
            name="Dire Bear",
            properties={
                "state_machine": {
                    "states": ["aggressive", "wary", "grateful", "vengeful"],
                    "initial": "aggressive",
                    "current": "aggressive",
                },
                "trust_state": {"current": -2, "floor": -5, "ceiling": 5},
            },
            location="loc_beast_wilds_den",
        )

        # Create sick cubs
        self.cub1 = self.state.add_actor(
            "npc_bear_cub_1",
            name="Bear Cub",
            properties={"sick": True},
            location="loc_beast_wilds_den",
        )
        self.cub2 = self.state.add_actor(
            "npc_bear_cub_2",
            name="Bear Cub",
            properties={"sick": True},
            location="loc_beast_wilds_den",
        )

        # Create healing herbs item
        self.herbs = self.state.add_item(
            "item_healing_herbs",
            name="Healing Herbs",
            location="actor:player",
        )

        # Add commitment config
        self.state.add_commitment_config(
            "commit_bear_cubs",
            duration=30,
            success_condition="cubs_healed",
        )

    def test_commitment_requires_keyword(self) -> None:
        """Commitment only triggers with appropriate keywords."""
        # Random dialog shouldn't trigger
        result = on_bear_commitment(
            self.bear, self.accessor, {"keyword": "hello", "dialog_text": ""}
        )

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)
        self.assert_flag_not_set("bear_cubs_commitment_created")

    def test_commitment_triggers_on_help_keyword(self) -> None:
        """Saying 'help' to bear creates commitment."""
        result = on_bear_commitment(
            self.bear, self.accessor, {"keyword": "help", "dialog_text": ""}
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("southern", (result.feedback or "").lower())
        self.assert_flag_set("bear_cubs_commitment_created")

    def test_commitment_idempotent(self) -> None:
        """Can't create duplicate commitments."""
        on_bear_commitment(
            self.bear, self.accessor, {"keyword": "help", "dialog_text": ""}
        )

        result = on_bear_commitment(
            self.bear, self.accessor, {"keyword": "help", "dialog_text": ""}
        )

        self.assertIn("already promised", (result.feedback or "").lower())

    def test_healing_cubs_with_herbs(self) -> None:
        """Using healing herbs on cubs heals them."""
        result = on_cubs_healed(
            self.herbs, self.accessor, {"target": self.cub1}
        )

        self.assertTrue(result.allow)
        self.assertIn("cubs eagerly consume", (result.feedback or "").lower())
        self.assert_flag_set("cubs_healed")

        # Cubs should be recovering
        self.assertTrue(self.cub1.properties.get("recovering"))
        self.assertFalse(self.cub1.properties.get("sick"))

        # Bear should be grateful
        self.assert_actor_state("npc_dire_bear", "grateful")
        # Trust should increase
        trust = self.get_actor_trust("npc_dire_bear")
        self.assertGreater(trust, -2)

    def test_commitment_failure_kills_cubs(self) -> None:
        """Failed commitment causes cubs to die and bear to become vengeful."""
        result = on_cubs_died(
            None, self.accessor, {"commitment_id": "commit_bear_cubs"}
        )

        self.assertTrue(result.allow)
        self.assertIn("breathing has stopped", (result.feedback or "").lower())
        self.assert_flag_set("cubs_died")

        # Bear should be vengeful
        self.assert_actor_state("npc_dire_bear", "vengeful")
        # Trust should be minimum
        self.assert_actor_trust("npc_dire_bear", -5)
        # Bear should hunt player
        self.assertTrue(self.bear.properties.get("hunts_player"))


class TestWolfPackScenarios(ScenarioTestCase):
    """Tests for wolf pack feeding and trust scenarios."""

    def setUp(self) -> None:
        """Set up wolf pack test fixtures."""
        super().setUp()
        self.setup_player(location="loc_beast_wilds_clearing")

        # Create alpha wolf
        self.alpha = self.state.add_actor(
            "npc_alpha_wolf",
            name="Alpha Wolf",
            properties={
                "state_machine": {
                    "states": ["hostile", "wary", "neutral", "friendly", "allied"],
                    "initial": "hostile",
                    "current": "hostile",
                },
                "trust_state": {"current": 0, "floor": -3, "ceiling": 6},
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": ["frost_wolf_1", "frost_wolf_2"],
                },
            },
            location="loc_beast_wilds_clearing",
        )

        # Create pack followers
        self.wolf1 = self.state.add_actor(
            "frost_wolf_1",
            name="Frost Wolf",
            properties={
                "state_machine": {
                    "states": ["hostile", "wary", "neutral", "friendly", "allied"],
                    "initial": "hostile",
                    "current": "hostile",
                },
            },
            location="loc_beast_wilds_clearing",
        )
        self.wolf2 = self.state.add_actor(
            "frost_wolf_2",
            name="Frost Wolf",
            properties={
                "state_machine": {
                    "states": ["hostile", "wary", "neutral", "friendly", "allied"],
                    "initial": "hostile",
                    "current": "hostile",
                },
            },
            location="loc_beast_wilds_clearing",
        )

        # Create meat item
        self.meat = self.state.add_item("item_venison", name="Venison")

    def test_feeding_wolf_increases_trust(self) -> None:
        """Giving meat to wolf increases trust."""
        initial_trust = self.get_actor_trust("npc_alpha_wolf")

        result = on_wolf_feed(
            self.meat, self.accessor, {"target_actor": self.alpha, "item": self.meat}
        )

        self.assertTrue(result.allow)
        self.assertIn("accepts", (result.feedback or "").lower())
        self.assertGreater(self.get_actor_trust("npc_alpha_wolf"), initial_trust)

    def test_feeding_transitions_state_at_threshold(self) -> None:
        """Feeding enough times transitions alpha from hostile to wary."""
        # Start hostile at trust 0
        self.alpha.properties["trust_state"]["current"] = 0

        # First feeding brings trust to 1
        on_wolf_feed(
            self.meat, self.accessor, {"target_actor": self.alpha, "item": self.meat}
        )

        # Should transition to wary at trust 1
        self.assert_actor_state("npc_alpha_wolf", "wary")

    def test_feeding_non_food_rejected(self) -> None:
        """Non-food items don't affect wolf."""
        stone = self.state.add_item("item_stone", name="Stone")

        result = on_wolf_feed(
            stone, self.accessor, {"target_actor": self.alpha, "item": stone}
        )

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)  # No reaction

    def test_trust_progression_to_neutral(self) -> None:
        """Multiple feedings can progress wolf through states."""
        # Set initial trust to 1 (wary threshold) and state to wary
        self.alpha.properties["trust_state"]["current"] = 1
        self.alpha.properties["state_machine"]["current"] = "wary"

        # Feed once to reach trust 2
        on_wolf_feed(
            self.meat, self.accessor, {"target_actor": self.alpha, "item": self.meat}
        )

        # Should be neutral now (transition at trust 2 when wary)
        self.assert_actor_state("npc_alpha_wolf", "neutral")
        self.assertEqual(self.get_actor_trust("npc_alpha_wolf"), 2)

        # Feed again to reach trust 3
        on_wolf_feed(
            self.meat, self.accessor, {"target_actor": self.alpha, "item": self.meat}
        )

        # Should be friendly now (transition at trust 3 when neutral)
        self.assert_actor_state("npc_alpha_wolf", "friendly")
        self.assertEqual(self.get_actor_trust("npc_alpha_wolf"), 3)


class TestBeeQueenScenarios(ScenarioTestCase):
    """Tests for Bee Queen trading scenarios."""

    def setUp(self) -> None:
        """Set up Bee Queen test fixtures."""
        super().setUp()
        self.setup_player(location="loc_bee_grove")

        # Create Bee Queen
        self.queen = self.state.add_actor(
            "bee_queen",
            name="Bee Queen",
            properties={
                "state_machine": {
                    "states": ["defensive", "neutral", "trading", "allied", "hostile"],
                    "initial": "neutral",
                    "current": "neutral",
                },
                "trust_state": {"current": 0, "floor": -3, "ceiling": 5},
            },
            location="loc_bee_grove",
        )

        # Create flower items
        self.moonpetal = self.state.add_item(
            "item_moonpetal", name="Moonpetal Flower"
        )
        self.frost_lily = self.state.add_item(
            "item_frost_lily", name="Frost Lily"
        )
        self.water_bloom = self.state.add_item(
            "item_water_bloom", name="Water Bloom"
        )

    def test_first_flower_trade(self) -> None:
        """First flower trade transitions queen to trading state."""
        result = on_flower_offer(
            self.moonpetal,
            self.accessor,
            {"target_actor": self.queen, "item": self.moonpetal},
        )

        self.assertTrue(result.allow)
        self.assertIn("accepts", (result.feedback or "").lower())
        self.assertIn("2 more", result.feedback or "")

        # Should track flower
        traded = self.state.extra.get("bee_queen_flowers_traded", [])
        self.assertIn("moonpetal", traded)

        # Should transition to trading
        self.assert_actor_state("bee_queen", "trading")

        # Should increase trust
        self.assertGreater(self.get_actor_trust("bee_queen"), 0)

    def test_duplicate_flower_type_rejected(self) -> None:
        """Same flower type cannot be traded twice."""
        # Trade moonpetal first
        on_flower_offer(
            self.moonpetal,
            self.accessor,
            {"target_actor": self.queen, "item": self.moonpetal},
        )

        # Try to trade moonpetal again
        result = on_flower_offer(
            self.moonpetal,
            self.accessor,
            {"target_actor": self.queen, "item": self.moonpetal},
        )

        self.assertIn("already received", (result.feedback or "").lower())

    def test_three_flowers_allies_queen(self) -> None:
        """Trading three different flowers transitions to allied."""
        # Trade all three flowers
        on_flower_offer(
            self.moonpetal,
            self.accessor,
            {"target_actor": self.queen, "item": self.moonpetal},
        )
        on_flower_offer(
            self.frost_lily,
            self.accessor,
            {"target_actor": self.queen, "item": self.frost_lily},
        )
        result = on_flower_offer(
            self.water_bloom,
            self.accessor,
            {"target_actor": self.queen, "item": self.water_bloom},
        )

        self.assertIn("ally", (result.feedback or "").lower())
        self.assert_actor_state("bee_queen", "allied")
        self.assert_flag_set("bee_queen_honey_count")
        self.assertEqual(self.state.extra["bee_queen_honey_count"], 3)

    def test_non_flower_rejected(self) -> None:
        """Non-flower items are rejected by queen."""
        stone = self.state.add_item("item_stone", name="Stone")

        result = on_flower_offer(
            stone, self.accessor, {"target_actor": self.queen, "item": stone}
        )

        self.assertIn("not what she seeks", (result.feedback or "").lower())

    def test_honey_theft_makes_hostile(self) -> None:
        """Taking honey without permission makes queen hostile."""
        honey = self.state.add_item("item_royal_honey", name="Royal Honey")
        beehive = self.state.add_location("loc_beehive_chamber", name="Beehive Chamber")

        result = on_honey_theft(
            honey, self.accessor, {"location": beehive}
        )

        self.assertTrue(result.allow)
        self.assertIn("hatred", (result.feedback or "").lower())
        self.assert_actor_state("bee_queen", "hostile")
        self.assert_flag_set("bee_grove_hostile")
        self.assert_flag_set("bee_trade_destroyed")

    def test_honey_take_allowed_when_allied(self) -> None:
        """Taking honey is allowed when queen is allied."""
        # Make queen allied first
        sm = self.queen.properties["state_machine"]
        sm["current"] = "allied"

        honey = self.state.add_item("item_royal_honey", name="Royal Honey")
        beehive = self.state.add_location("loc_beehive_chamber", name="Beehive Chamber")

        result = on_honey_theft(
            honey, self.accessor, {"location": beehive}
        )

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)  # No hostile reaction
        self.assert_flag_not_set("bee_grove_hostile")


class TestSpiderNestScenarios(ScenarioTestCase):
    """Tests for spider nest combat scenarios."""

    def setUp(self) -> None:
        """Set up spider nest test fixtures."""
        super().setUp()
        self.setup_player(location="loc_spider_nest_entrance")

        # Create spider queen
        self.queen = self.state.add_actor(
            "spider_matriarch",
            name="Spider Matriarch",
            properties={
                "state_machine": {
                    "states": ["hostile", "wary", "dead"],
                    "initial": "hostile",
                    "current": "hostile",
                },
            },
            location="loc_spider_nest_gallery",
        )

        # Create some spiders
        self.spider1 = self.state.add_actor(
            "npc_giant_spider_1",
            name="Giant Spider",
            properties={
                "state_machine": {
                    "states": ["hostile", "dead"],
                    "initial": "hostile",
                    "current": "hostile",
                },
                "location": "loc_spider_nest_gallery",
            },
        )
        self.spider2 = self.state.add_actor(
            "npc_giant_spider_2",
            name="Giant Spider",
            properties={
                "state_machine": {
                    "states": ["hostile", "dead"],
                    "initial": "hostile",
                    "current": "hostile",
                },
                "location": "loc_spider_nest_gallery",
            },
        )

        # Location with web effects
        self.gallery = self.state.add_location(
            "loc_spider_nest_gallery",
            name="Spider Gallery",
            properties={"web_effects": True},
        )

    def test_web_movement_slows_player(self) -> None:
        """Moving through webs displays warning message."""
        result = on_web_movement(
            None, self.accessor, {"destination": self.gallery}
        )

        self.assertTrue(result.allow)
        self.assertIn("webs cling", (result.feedback or "").lower())
        self.assertIn("vibrations", (result.feedback or "").lower())

    def test_queen_death_stops_respawns(self) -> None:
        """Killing queen sets flag to stop future respawns."""
        result = on_spider_queen_death(self.queen, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("broken", (result.feedback or "").lower())
        self.assert_flag_set("spider_queen_dead")

    def test_respawn_requires_living_queen(self) -> None:
        """Spiders don't respawn if queen is dead."""
        # Kill queen first
        self.queen.properties["state_machine"]["current"] = "dead"

        # Advance time past respawn interval
        self.state.extra["spider_last_respawn"] = 0
        self.state.advance_turns(15)

        result = on_spider_respawn_check(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)  # No respawn message

    def test_respawn_happens_with_living_queen(self) -> None:
        """Spiders respawn periodically while queen lives."""
        # Kill one spider
        self.spider1.properties["state_machine"]["current"] = "dead"

        # Set up respawn timing
        self.state.extra["spider_last_respawn"] = 0
        self.state.advance_turns(15)  # Past the 10-turn interval

        result = on_spider_respawn_check(None, self.accessor, {})

        self.assertTrue(result.allow)
        # With only 1 living spider, 1 should respawn
        self.assertIsNotNone(result.feedback)
        self.assertIn("emerge", (result.feedback or "").lower())

    def test_no_respawn_if_enough_spiders_alive(self) -> None:
        """No respawn if 2+ spiders are already alive."""
        # Both spiders alive
        self.state.extra["spider_last_respawn"] = 0
        self.state.advance_turns(15)

        result = on_spider_respawn_check(None, self.accessor, {})

        self.assertTrue(result.allow)
        # No message because no respawn needed
        self.assertIsNone(result.feedback)


if __name__ == "__main__":
    unittest.main()
