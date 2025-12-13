"""Cross-region scenario tests.

Tests multi-step gameplay scenarios that span multiple regions,
demonstrating how actions in one region affect others:
- Gossip propagation (e.g., Sira death reaching Elara)
- Death mark effects (fungal kills affecting Myconid trust)
- Echo commentary on player choices
- Bee Queen flower collection across regions
"""

import unittest
from typing import Any

from examples.big_game.behaviors.infrastructure.dispatcher_utils import clear_handler_cache
from behaviors.regions.beast_wilds.bee_queen import on_flower_offer
from behaviors.regions.beast_wilds.sira_rescue import on_sira_death, on_sira_encounter
from behaviors.regions.fungal_depths.fungal_death_mark import (
    on_fungal_kill,
    on_myconid_first_meeting,
)
from behaviors.regions.fungal_depths.spore_mother import on_spore_mother_death
from behaviors.regions.meridian_nexus.echo import on_echo_dialog, on_echo_gossip
from behaviors.regions.sunken_district.dual_rescue import (
    on_delvan_encounter,
    on_npc_death,
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


class TestGossipPropagationScenarios(ScenarioTestCase):
    """Tests for cross-region gossip propagation."""

    def setUp(self) -> None:
        """Set up gossip test fixtures."""
        super().setUp()
        self.setup_player(location="loc_beast_wilds")

        # Create Sira in Beast Wilds
        self.sira = self.state.add_actor(
            "npc_hunter_sira",
            name="Hunter Sira",
            properties={
                "state_machine": {
                    "states": ["critical", "stabilized", "recovering", "dead"],
                    "initial": "critical",
                    "current": "critical",
                },
            },
            location="loc_beast_wilds_clearing",
        )

        # Create Elara in Civilized Remnants
        self.elara = self.state.add_actor(
            "npc_healer_elara",
            name="Healer Elara",
            properties={
                "trust_state": {"current": 2, "floor": -5, "ceiling": 5},
            },
            location="loc_civilized_remnants_clinic",
        )

        # Create Echo in Meridian Nexus
        self.echo = self.state.add_actor(
            "the_echo",
            name="The Echo",
            properties={
                "trust_state": {"current": 0, "floor": -6, "ceiling": 6},
            },
            location="loc_meridian_nexus",
        )

        # Create Delvan in Sunken District
        self.delvan = self.state.add_actor(
            "merchant_delvan",
            name="Merchant Delvan",
            properties={
                "conditions": {"bleeding": {"severity": 60, "type": "bleeding"}}
            },
            location="loc_sunken_collapsed_hall",
        )

    def test_sira_death_gossip_reaches_elara(self) -> None:
        """Sira dying creates gossip that targets Elara."""
        # Player encounters Sira (starts commitment)
        on_sira_encounter(self.sira, self.accessor, {})

        # Sira dies
        result = on_sira_death(self.sira, self.accessor, {})

        self.assertTrue(result.allow)
        self.assert_flag_set("sira_died_with_player")

        # Gossip should be pending to Elara
        self.assert_gossip_pending("Sira")

        # Verify gossip targets
        gossip_queue = self.state.extra.get("gossip_queue", [])
        sira_gossip = None
        for g in gossip_queue:
            if "Sira" in g.get("content", ""):
                sira_gossip = g
                break

        self.assertIsNotNone(sira_gossip)
        assert sira_gossip is not None
        self.assertIn("npc_healer_elara", sira_gossip.get("target_npcs", []))

    def test_delvan_death_gossip_reaches_echo(self) -> None:
        """Delvan dying creates gossip that targets Echo."""
        # Player encounters Delvan
        on_delvan_encounter(self.delvan, self.accessor, {})

        # Delvan dies
        result = on_npc_death(self.delvan, self.accessor, {})

        self.assertTrue(result.allow)
        self.assert_flag_set("delvan_died")
        self.assert_gossip_pending("Delvan")


class TestDeathMarkCrossRegionScenarios(ScenarioTestCase):
    """Tests for fungal death mark affecting cross-region trust."""

    def setUp(self) -> None:
        """Set up death mark test fixtures."""
        super().setUp()
        self.setup_player(location="loc_fungal_depths")

        # Create fungal creatures
        self.shambler = self.state.add_actor(
            "npc_fungal_shambler",
            name="Fungal Shambler",
            properties={"fungal": True},
            location="loc_fungal_depths_outer",
        )

        # Create Spore Mother
        self.spore_mother = self.state.add_actor(
            "npc_spore_mother",
            name="Spore Mother",
            properties={
                "state_machine": {
                    "states": ["hostile", "wary", "allied", "dead"],
                    "initial": "hostile",
                    "current": "hostile",
                },
                "fungal": True,
            },
            location="spore_heart",
        )

        # Create Myconid Elder
        self.myconid = self.state.add_actor(
            "npc_myconid_elder",
            name="Myconid Elder",
            properties={
                "trust_state": {"current": 0, "floor": -5, "ceiling": 5},
                "fungal": True,
            },
            location="loc_fungal_depths_colony",
        )

        # Create Echo
        self.echo = self.state.add_actor(
            "the_echo",
            name="The Echo",
            properties={
                "trust_state": {"current": 0, "floor": -6, "ceiling": 6},
            },
            location="loc_meridian_nexus",
        )

    def test_kill_minor_fungus_then_meet_myconid(self) -> None:
        """Killing minor fungal creatures affects Myconid first meeting."""
        player = self.state.actors["player"]

        # Kill a fungal creature
        on_fungal_kill(self.shambler, self.accessor, {"killer": player})

        self.assert_flag_set("has_killed_fungi")

        # Now meet Myconid Elder
        result = on_myconid_first_meeting(self.myconid, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("death of our kin", (result.message or "").lower())
        self.assert_actor_trust("npc_myconid_elder", -3)

    def test_kill_spore_mother_gossip_reaches_echo(self) -> None:
        """Killing Spore Mother creates gossip to Echo."""
        # Kill Spore Mother
        result = on_spore_mother_death(self.spore_mother, self.accessor, {})

        self.assertTrue(result.allow)
        self.assert_flag_set("spore_mother_dead")
        self.assert_flag_set("has_killed_fungi")

        # Gossip should target Echo
        self.assert_gossip_pending("killed")

        gossip_queue = self.state.extra.get("gossip_queue", [])
        spore_gossip = None
        for g in gossip_queue:
            if "killed" in g.get("content", ""):
                spore_gossip = g
                break

        self.assertIsNotNone(spore_gossip)
        assert spore_gossip is not None
        self.assertIn("echo", spore_gossip.get("target_npcs", []))


class TestEchoCrossRegionCommentaryScenarios(ScenarioTestCase):
    """Tests for Echo's commentary on events across regions."""

    def setUp(self) -> None:
        """Set up Echo commentary fixtures."""
        super().setUp()
        self.setup_player(location="loc_meridian_nexus")

        # Create Echo
        self.echo = self.state.add_actor(
            "the_echo",
            name="The Echo",
            properties={
                "trust_state": {"current": 0, "floor": -6, "ceiling": 6},
            },
            location="loc_meridian_nexus",
        )

        # Create relevant NPCs for context
        self.state.add_actor(
            "npc_hunter_sira",
            name="Hunter Sira",
            location="loc_beast_wilds",
        )
        self.state.add_actor(
            "npc_aldric",
            name="Scholar Aldric",
            location="loc_fungal_depths",
        )

    def test_echo_comments_on_spore_mother_healed(self) -> None:
        """Echo provides positive commentary when Spore Mother is healed."""
        # Gossip content must contain both "spore_mother" and "healed"
        result = on_echo_gossip(
            self.echo,
            self.accessor,
            {"content": "spore_mother healed by the player"},
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.message)
        self.assertIn("chose healing", (result.message or "").lower())
        # Trust should increase (check echo's trust_state directly)
        trust = self.echo.properties.get("trust_state", {}).get("current", 0)
        self.assertGreater(trust, 0)

    def test_echo_comments_on_spore_mother_killed(self) -> None:
        """Echo provides negative commentary when Spore Mother is killed."""
        # Gossip content must contain both "spore_mother" and "killed"
        result = on_echo_gossip(
            self.echo,
            self.accessor,
            {"content": "spore_mother killed by player"},
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.message)
        self.assertIn("violence", (result.message or "").lower())
        # Trust should decrease
        trust = self.echo.properties.get("trust_state", {}).get("current", 0)
        self.assertLess(trust, 0)

    def test_echo_comments_on_sira_death(self) -> None:
        """Echo comments on Sira's death."""
        # Gossip content must contain "sira" and "died"
        result = on_echo_gossip(
            self.echo,
            self.accessor,
            {"content": "hunter sira died in the beast wilds"},
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.message)
        self.assertIn("sira", (result.message or "").lower())
        self.assertIn("elara", (result.message or "").lower())

    def test_echo_comments_on_salamander_death(self) -> None:
        """Echo comments negatively on salamander deaths."""
        # Gossip content must contain "salamander" and "killed" or "died"
        result = on_echo_gossip(
            self.echo,
            self.accessor,
            {"content": "salamander killed by the player"},
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.message)
        self.assertIn("fire elementals", (result.message or "").lower())
        # Trust should decrease
        trust = self.echo.properties.get("trust_state", {}).get("current", 0)
        self.assertLess(trust, 0)

    def test_echo_provides_hints(self) -> None:
        """Echo provides hints about urgent situations."""
        result = on_echo_dialog(
            self.echo,
            self.accessor,
            {"keyword": "help"},
        )

        self.assertTrue(result.allow)
        # Should hint about something
        self.assertIn("hunter", (result.message or "").lower())  # Sira hint

    def test_echo_tracks_progress(self) -> None:
        """Echo can report on player progress."""
        # Set up some progress flags
        self.state.extra["sira_healed"] = True
        self.state.extra["aldric_died"] = True
        self.state.extra["waystone_fragments"] = ["fragment_1", "fragment_2"]

        result = on_echo_dialog(
            self.echo,
            self.accessor,
            {"keyword": "status"},
        )

        self.assertTrue(result.allow)
        self.assertIn("saved", (result.message or "").lower())
        self.assertIn("lost", (result.message or "").lower())
        self.assertIn("2 of 5", result.message or "")


class TestBeeQueenCrossRegionCollectionScenarios(ScenarioTestCase):
    """Tests for Bee Queen flower collection across regions."""

    def setUp(self) -> None:
        """Set up Bee Queen collection fixtures."""
        super().setUp()
        self.setup_player(location="loc_bee_grove")

        # Create Bee Queen
        self.bee_queen = self.state.add_actor(
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

        # Create flowers from different regions
        self.moonpetal = self.state.add_item(
            "item_moonpetal",
            name="Moonpetal Flower",
            properties={"source_region": "civilized_remnants"},
        )
        self.frost_lily = self.state.add_item(
            "item_frost_lily",
            name="Frost Lily",
            properties={"source_region": "frozen_reaches"},
        )
        self.water_bloom = self.state.add_item(
            "item_water_bloom",
            name="Water Bloom",
            properties={"source_region": "sunken_district"},
        )

    def test_trading_flowers_from_all_regions(self) -> None:
        """Trading flowers from all three regions creates alliance."""
        # Trade moonpetal (from Civilized Remnants)
        result1 = on_flower_offer(
            self.moonpetal,
            self.accessor,
            {"target_actor": self.bee_queen, "item": self.moonpetal},
        )
        self.assertIn("accepts", (result1.message or "").lower())
        self.assert_actor_state("bee_queen", "trading")

        # Trade frost lily (from Frozen Reaches)
        result2 = on_flower_offer(
            self.frost_lily,
            self.accessor,
            {"target_actor": self.bee_queen, "item": self.frost_lily},
        )
        self.assertIn("1 more", result2.message or "")

        # Trade water bloom (from Sunken District) - completes collection
        result3 = on_flower_offer(
            self.water_bloom,
            self.accessor,
            {"target_actor": self.bee_queen, "item": self.water_bloom},
        )

        self.assertIn("ally", (result3.message or "").lower())
        self.assert_actor_state("bee_queen", "allied")

        # Should have received 3 honey
        self.assertEqual(self.state.extra.get("bee_queen_honey_count"), 3)

    def test_flowers_must_be_unique_types(self) -> None:
        """Same flower type cannot be traded twice."""
        # Trade moonpetal once
        on_flower_offer(
            self.moonpetal,
            self.accessor,
            {"target_actor": self.bee_queen, "item": self.moonpetal},
        )

        # Try to trade another moonpetal
        moonpetal2 = self.state.add_item("item_moonpetal_2", name="Moonpetal Flower")
        result = on_flower_offer(
            moonpetal2,
            self.accessor,
            {"target_actor": self.bee_queen, "item": moonpetal2},
        )

        self.assertIn("already received", (result.message or "").lower())

        # Should only have 1 honey
        self.assertEqual(self.state.extra.get("bee_queen_honey_count"), 1)


class TestMultiRegionConsequenceChainScenarios(ScenarioTestCase):
    """Tests for complex consequence chains spanning multiple regions."""

    def setUp(self) -> None:
        """Set up multi-region scenario."""
        super().setUp()
        self.setup_player(location="loc_fungal_depths")

        # Spore Mother (Fungal Depths)
        self.spore_mother = self.state.add_actor(
            "npc_spore_mother",
            name="Spore Mother",
            properties={
                "state_machine": {"states": ["hostile", "dead"], "current": "hostile"},
                "fungal": True,
            },
        )

        # Myconid Elder (Fungal Depths)
        self.myconid = self.state.add_actor(
            "npc_myconid_elder",
            name="Myconid Elder",
            properties={
                "trust_state": {"current": 3, "floor": -5, "ceiling": 5},
                "fungal": True,
            },
        )

        # Echo (Meridian Nexus)
        self.echo = self.state.add_actor(
            "the_echo",
            name="The Echo",
            properties={
                "trust_state": {"current": 2, "floor": -6, "ceiling": 6},
            },
        )

    def test_killing_spore_mother_chain_reaction(self) -> None:
        """Killing Spore Mother causes cascading effects across regions."""
        # Initial trust states
        initial_myconid_trust = self.get_actor_trust("npc_myconid_elder")

        # Kill Spore Mother
        on_spore_mother_death(self.spore_mother, self.accessor, {})

        # 1. Sets death mark
        self.assert_flag_set("has_killed_fungi")

        # 2. Myconid trust drops
        new_myconid_trust = self.get_actor_trust("npc_myconid_elder")
        self.assertLess(new_myconid_trust, initial_myconid_trust)

        # 3. Creates gossip to Echo
        self.assert_gossip_pending("killed")

        # 4. When Echo receives gossip, trust drops
        # Need to match pattern "spore_mother" + "killed"
        result = on_echo_gossip(
            self.echo, self.accessor, {"content": "spore_mother killed"}
        )

        # Check trust directly on entity since handler modifies trust_state
        echo_trust = self.echo.properties.get("trust_state", {}).get("current", 0)
        self.assertLess(echo_trust, 2)  # Started at 2

    def test_violent_path_accumulates_negative_trust(self) -> None:
        """Taking violent path in multiple regions accumulates penalties."""
        # Kill Spore Mother
        on_spore_mother_death(self.spore_mother, self.accessor, {})

        # Meet Myconid with death mark
        on_myconid_first_meeting(self.myconid, self.accessor, {})

        # Echo hears about killing (must use correct pattern)
        on_echo_gossip(
            self.echo, self.accessor, {"content": "spore_mother killed"}
        )

        # Echo hears about salamander death (must use correct pattern)
        on_echo_gossip(
            self.echo, self.accessor, {"content": "salamander killed"}
        )

        # Myconid should have death mark penalty (-3)
        myconid_trust = self.get_actor_trust("npc_myconid_elder")
        self.assertLessEqual(myconid_trust, -3)

        # Echo should have reduced trust from both events (-2 for spore_mother, -1 for salamander)
        echo_trust = self.echo.properties.get("trust_state", {}).get("current", 0)
        self.assertLessEqual(echo_trust, -1)  # Started at 2, lost at least 3


if __name__ == "__main__":
    unittest.main()
