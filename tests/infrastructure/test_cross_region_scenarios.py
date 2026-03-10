"""Cross-region scenario tests.

Tests multi-step gameplay scenarios that span multiple regions,
demonstrating how actions in one region affect others:
- Gossip propagation (e.g., Sira death reaching Elara)
- Death mark effects (fungal kills affecting Myconid trust)
- Echo commentary on player choices
- Bee Queen flower collection across regions
"""

import unittest
from pathlib import Path
from typing import Any

from examples.big_game.behaviors.regions.beast_wilds.bee_queen import on_receive_item as on_flower_offer
from examples.big_game.behaviors.regions.beast_wilds.sira_rescue import on_sira_death, on_sira_encounter
from examples.big_game.behaviors.regions.fungal_depths.fungal_death_mark import (
    on_fungal_kill,
    on_myconid_first_meeting,
)
from examples.big_game.behaviors.regions.fungal_depths.spore_mother import on_spore_mother_death
from examples.big_game.behaviors.regions.meridian_nexus.echo import on_echo_dialog, on_echo_gossip
from examples.big_game.behaviors.regions.sunken_district.dual_rescue import (
    on_delvan_encounter,
    on_npc_death,
)
from src.game_engine import GameEngine
from src.state_accessor import StateAccessor
from tests.conftest import BaseTestCase

GAME_DIR = (Path(__file__).parent.parent.parent / 'examples' / 'big_game').resolve()


class CrossRegionTestCase(BaseTestCase):
    """Base test case that loads real big_game state."""

    def setUp(self) -> None:
        self.engine = GameEngine(GAME_DIR)
        self.state = self.engine.game_state
        self.accessor = StateAccessor(self.state, self.engine.behavior_manager)

    def get_actor_trust(self, actor_id: str) -> int:
        """Get current trust value for an actor."""
        actor = self.state.actors.get(actor_id)
        self.assertIsNotNone(actor, f"Actor {actor_id} not found")
        assert actor is not None
        return actor.properties.get("trust_state", {}).get("current", 0)

    def assert_flag_set(self, flag_name: str) -> None:
        """Assert a flag is set in game state extra."""
        self.assertTrue(
            self.state.extra.get(flag_name),
            f"Expected flag '{flag_name}' to be set",
        )

    def assert_gossip_pending(self, content_substring: str) -> None:
        """Assert gossip containing substring is in the queue."""
        gossip_queue = self.state.extra.get("gossip_queue", [])
        found = any(
            content_substring.lower() in g.get("content", "").lower()
            for g in gossip_queue
        )
        self.assertTrue(
            found,
            f"No gossip containing '{content_substring}' found in queue: {gossip_queue}",
        )


class TestGossipPropagationScenarios(CrossRegionTestCase):
    """Tests for cross-region gossip propagation."""

    def test_sira_death_gossip_reaches_elara(self) -> None:
        """Sira dying creates gossip that targets Elara."""
        sira = self.state.actors.get("hunter_sira")
        self.assertIsNotNone(sira)
        assert sira is not None

        # Player encounters Sira (starts commitment)
        on_sira_encounter(sira, self.accessor, {})

        # Sira dies
        result = on_sira_death(sira, self.accessor, {})

        self.assertTrue(result.allow)
        self.assert_flag_set("sira_died_with_player")

        # Gossip should be pending about Sira
        self.assert_gossip_pending("Sira")

        # Verify gossip targets Elara
        gossip_queue = self.state.extra.get("gossip_queue", [])
        sira_gossip = next(
            (g for g in gossip_queue if "Sira" in g.get("content", "")),
            None,
        )
        self.assertIsNotNone(sira_gossip)
        assert sira_gossip is not None
        self.assertIn("npc_healer_elara", sira_gossip.get("target_npcs", []))

    def test_delvan_death_gossip_reaches_echo(self) -> None:
        """Delvan dying creates gossip that targets Echo."""
        delvan = self.state.actors.get("merchant_delvan")
        self.assertIsNotNone(delvan)
        assert delvan is not None

        # Player encounters Delvan
        on_delvan_encounter(delvan, self.accessor, {})

        # Delvan dies
        result = on_npc_death(delvan, self.accessor, {})

        self.assertTrue(result.allow)
        self.assert_flag_set("delvan_died")
        self.assert_gossip_pending("Delvan")


class TestDeathMarkCrossRegionScenarios(CrossRegionTestCase):
    """Tests for fungal death mark affecting cross-region trust."""

    def test_kill_minor_fungus_then_meet_myconid(self) -> None:
        """Killing minor fungal creatures affects Myconid first meeting."""
        # Use a sporeling as the fungal creature to kill
        sporeling = self.state.actors.get("npc_sporeling_1")
        self.assertIsNotNone(sporeling)
        assert sporeling is not None

        player = self.state.actors.get("player")
        self.assertIsNotNone(player)

        # Kill a fungal creature
        on_fungal_kill(sporeling, self.accessor, {"killer": player})
        self.assert_flag_set("has_killed_fungi")

        # Now meet Myconid Elder
        myconid = self.state.actors.get("npc_myconid_elder")
        self.assertIsNotNone(myconid)
        assert myconid is not None

        result = on_myconid_first_meeting(myconid, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("death of our kin", (result.feedback or "").lower())
        self.assertEqual(self.get_actor_trust("npc_myconid_elder"), -3)

    def test_kill_spore_mother_gossip_reaches_echo(self) -> None:
        """Killing Spore Mother creates gossip to Echo."""
        spore_mother = self.state.actors.get("npc_spore_mother")
        self.assertIsNotNone(spore_mother)
        assert spore_mother is not None

        result = on_spore_mother_death(spore_mother, self.accessor, {})

        self.assertTrue(result.allow)
        self.assert_flag_set("spore_mother_dead")
        self.assert_flag_set("has_killed_fungi")

        # Gossip should target Echo
        self.assert_gossip_pending("killed")

        gossip_queue = self.state.extra.get("gossip_queue", [])
        spore_gossip = next(
            (g for g in gossip_queue if "killed" in g.get("content", "").lower()),
            None,
        )
        self.assertIsNotNone(spore_gossip)
        assert spore_gossip is not None
        self.assertIn("echo", spore_gossip.get("target_npcs", []))


class TestEchoCrossRegionCommentaryScenarios(CrossRegionTestCase):
    """Tests for Echo's commentary on events across regions."""

    def test_echo_comments_on_spore_mother_healed(self) -> None:
        """Echo provides positive commentary when Spore Mother is healed."""
        echo = self.state.actors.get("the_echo")
        self.assertIsNotNone(echo)
        assert echo is not None

        result = on_echo_gossip(
            echo,
            self.accessor,
            {"content": "spore_mother healed by the player"},
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("chose healing", (result.feedback or "").lower())
        # Trust should increase
        trust = echo.properties.get("trust_state", {}).get("current", 0)
        self.assertGreater(trust, 0)

    def test_echo_comments_on_spore_mother_killed(self) -> None:
        """Echo provides negative commentary when Spore Mother is killed."""
        echo = self.state.actors.get("the_echo")
        self.assertIsNotNone(echo)
        assert echo is not None

        result = on_echo_gossip(
            echo,
            self.accessor,
            {"content": "spore_mother killed by player"},
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("violence", (result.feedback or "").lower())
        trust = echo.properties.get("trust_state", {}).get("current", 0)
        self.assertLess(trust, 0)

    def test_echo_comments_on_sira_death(self) -> None:
        """Echo comments on Sira's death."""
        echo = self.state.actors.get("the_echo")
        self.assertIsNotNone(echo)
        assert echo is not None

        result = on_echo_gossip(
            echo,
            self.accessor,
            {"content": "hunter sira died in the beast wilds"},
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("sira", (result.feedback or "").lower())
        self.assertIn("elara", (result.feedback or "").lower())

    def test_echo_comments_on_salamander_death(self) -> None:
        """Echo comments negatively on salamander deaths."""
        echo = self.state.actors.get("the_echo")
        self.assertIsNotNone(echo)
        assert echo is not None

        result = on_echo_gossip(
            echo,
            self.accessor,
            {"content": "salamander killed by the player"},
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("fire elementals", (result.feedback or "").lower())
        trust = echo.properties.get("trust_state", {}).get("current", 0)
        self.assertLess(trust, 0)

    def test_echo_provides_hints(self) -> None:
        """Echo provides hints about urgent situations."""
        echo = self.state.actors.get("the_echo")
        self.assertIsNotNone(echo)
        assert echo is not None

        result = on_echo_dialog(
            echo,
            self.accessor,
            {"keyword": "help"},
        )

        self.assertTrue(result.allow)
        # Should hint about something urgent (hunter Sira bleeds)
        self.assertIn("hunter", (result.feedback or "").lower())

    def test_echo_tracks_progress(self) -> None:
        """Echo can report on player progress."""
        echo = self.state.actors.get("the_echo")
        self.assertIsNotNone(echo)
        assert echo is not None

        # Set up some progress flags
        self.state.extra["sira_healed"] = True
        self.state.extra["aldric_died"] = True
        self.state.extra["waystone_fragments"] = ["fragment_1", "fragment_2"]

        result = on_echo_dialog(
            echo,
            self.accessor,
            {"keyword": "status"},
        )

        self.assertTrue(result.allow)
        self.assertIn("saved", (result.feedback or "").lower())
        self.assertIn("lost", (result.feedback or "").lower())
        self.assertIn("2 of 5", result.feedback or "")


class TestBeeQueenCrossRegionCollectionScenarios(CrossRegionTestCase):
    """Tests for Bee Queen flower collection across regions."""

    def _get_flower(self, substring: str) -> Any:
        """Find a flower item by ID substring."""
        for item in self.state.items:
            if substring in item.id:
                return item
        self.fail(f"No item found matching '{substring}'")

    def test_trading_flowers_from_all_regions(self) -> None:
        """Trading flowers from all three regions creates alliance."""
        bee_queen = self.state.actors.get("bee_queen")
        self.assertIsNotNone(bee_queen)
        assert bee_queen is not None

        moonpetal = self._get_flower("moonpetal")
        frost_lily = self._get_flower("frost_lily")
        water_bloom = self._get_flower("water_bloom")

        # Bee queen starts defensive; transition to neutral for trading
        sm = bee_queen.properties.get("state_machine", {})
        sm["current"] = "neutral"

        # Trade moonpetal (from Civilized Remnants)
        result1 = on_flower_offer(
            bee_queen,
            self.accessor,
            {"item": moonpetal, "item_id": moonpetal.id, "giver_id": "player"},
        )
        self.assertIn("accepts", (result1.feedback or "").lower())

        # After first flower, should be in trading state
        current_state = sm.get("current", sm.get("initial"))
        self.assertEqual(current_state, "trading")

        # Trade frost lily (from Frozen Reaches)
        result2 = on_flower_offer(
            bee_queen,
            self.accessor,
            {"item": frost_lily, "item_id": frost_lily.id, "giver_id": "player"},
        )
        self.assertIn("1 more", result2.feedback or "")

        # Trade water bloom (from Sunken District) - completes collection
        result3 = on_flower_offer(
            bee_queen,
            self.accessor,
            {"item": water_bloom, "item_id": water_bloom.id, "giver_id": "player"},
        )

        self.assertIn("ally", (result3.feedback or "").lower())

        current_state = sm.get("current", sm.get("initial"))
        self.assertEqual(current_state, "allied")

        # Should have received 3 honey
        self.assertEqual(self.state.extra.get("bee_queen_honey_count"), 3)

    def test_flowers_must_be_unique_types(self) -> None:
        """Same flower type cannot be traded twice."""
        bee_queen = self.state.actors.get("bee_queen")
        self.assertIsNotNone(bee_queen)
        assert bee_queen is not None

        moonpetal = self._get_flower("moonpetal")

        # Set queen to neutral so trading can begin
        sm = bee_queen.properties.get("state_machine", {})
        sm["current"] = "neutral"

        # Trade moonpetal once
        on_flower_offer(
            bee_queen,
            self.accessor,
            {"item": moonpetal, "item_id": moonpetal.id, "giver_id": "player"},
        )

        # Try to trade the same moonpetal again
        result = on_flower_offer(
            bee_queen,
            self.accessor,
            {"item": moonpetal, "item_id": moonpetal.id, "giver_id": "player"},
        )

        self.assertIn("already received", (result.feedback or "").lower())

        # Should only have 1 honey
        self.assertEqual(self.state.extra.get("bee_queen_honey_count"), 1)


class TestMultiRegionConsequenceChainScenarios(CrossRegionTestCase):
    """Tests for complex consequence chains spanning multiple regions."""

    def test_killing_spore_mother_chain_reaction(self) -> None:
        """Killing Spore Mother causes cascading effects across regions."""
        spore_mother = self.state.actors.get("npc_spore_mother")
        self.assertIsNotNone(spore_mother)
        assert spore_mother is not None

        initial_myconid_trust = self.get_actor_trust("npc_myconid_elder")

        # Kill Spore Mother
        on_spore_mother_death(spore_mother, self.accessor, {})

        # 1. Sets death mark
        self.assert_flag_set("has_killed_fungi")

        # 2. Myconid trust drops (spore_mother_death applies -5)
        new_myconid_trust = self.get_actor_trust("npc_myconid_elder")
        self.assertLess(new_myconid_trust, initial_myconid_trust)

        # 3. Creates gossip to Echo
        self.assert_gossip_pending("killed")

        # 4. When Echo receives gossip, trust drops
        echo = self.state.actors.get("the_echo")
        self.assertIsNotNone(echo)
        assert echo is not None

        initial_echo_trust = echo.properties.get("trust_state", {}).get("current", 0)
        on_echo_gossip(
            echo, self.accessor, {"content": "spore_mother killed"}
        )

        echo_trust = echo.properties.get("trust_state", {}).get("current", 0)
        self.assertLess(echo_trust, initial_echo_trust)

    def test_violent_path_accumulates_negative_trust(self) -> None:
        """Taking violent path in multiple regions accumulates penalties."""
        spore_mother = self.state.actors.get("npc_spore_mother")
        self.assertIsNotNone(spore_mother)
        assert spore_mother is not None

        myconid = self.state.actors.get("npc_myconid_elder")
        self.assertIsNotNone(myconid)
        assert myconid is not None

        echo = self.state.actors.get("the_echo")
        self.assertIsNotNone(echo)
        assert echo is not None

        # Kill Spore Mother (sets death mark, applies -5 myconid trust)
        on_spore_mother_death(spore_mother, self.accessor, {})

        # Meet Myconid with death mark (sets trust to -3, but already at -5)
        on_myconid_first_meeting(myconid, self.accessor, {})

        # Echo hears about spore mother killing (-2 trust)
        on_echo_gossip(
            echo, self.accessor, {"content": "spore_mother killed"}
        )

        # Echo hears about salamander death (-1 trust)
        on_echo_gossip(
            echo, self.accessor, {"content": "salamander killed"}
        )

        # Myconid should have severe trust penalty
        myconid_trust = self.get_actor_trust("npc_myconid_elder")
        self.assertLessEqual(myconid_trust, -3)

        # Echo should have reduced trust from both events (-2 for spore_mother, -1 for salamander)
        echo_trust = echo.properties.get("trust_state", {}).get("current", 0)
        self.assertLessEqual(echo_trust, -3)  # Started at 0, lost 3 total


if __name__ == "__main__":
    unittest.main()
