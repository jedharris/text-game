"""Scenario tests for Fungal Depths region.

Tests multi-step gameplay scenarios including:
- Aldric rescue (commitment + optional teaching)
- Spore Mother heal/kill choice
- Fungal death mark system
- Myconid trust dynamics
"""
from src.types import ActorId

import unittest
from typing import Any

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import clear_handler_cache
from examples.big_game.behaviors.regions.fungal_depths.aldric_rescue import (
    on_aldric_commitment,
    on_aldric_heal,
    on_aldric_teach,
)
from examples.big_game.behaviors.regions.fungal_depths.fungal_death_mark import (
    on_fungal_kill,
    on_myconid_first_meeting,
)
from examples.big_game.behaviors.regions.fungal_depths.spore_mother import (
    on_spore_mother_death,
    on_spore_mother_heal,
    on_spore_mother_presence,
)
from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    get_pending_gossip_about,
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


class TestAldricRescueScenarios(ScenarioTestCase):
    """Tests for Scholar Aldric rescue scenarios."""

    def setUp(self) -> None:
        """Set up Aldric rescue test fixtures."""
        super().setUp()
        self.setup_player(location="loc_fungal_depths_camp")

        # Create Aldric with fungal infection
        self.aldric = self.state.add_actor(
            "npc_aldric",
            name="Scholar Aldric",
            properties={
                "state_machine": {
                    "states": ["critical", "stabilized", "recovering", "dead"],
                    "initial": "critical",
                    "current": "critical",
                },
                "trust_state": {"current": 0, "floor": -3, "ceiling": 5},
                "conditions": {
                    "fungal_infection": {
                        "severity": 80,
                        "type": "fungal_infection",
                        "progression_rate": 2,
                    }
                },
            },
            location="loc_fungal_depths_camp",
        )

        # Create silvermoss item
        self.silvermoss = self.state.add_item(
            "item_silvermoss",
            name="Silvermoss",
            location="actor:player",
        )

        # Add commitment config
        self.state.add_commitment_config(
            "commit_aldric_help",
            duration=25,
            success_condition="aldric_helped",
        )

    def test_commitment_triggers_on_help_keyword(self) -> None:
        """Asking to help Aldric creates commitment."""
        result = on_aldric_commitment(
            self.aldric, self.accessor, {"keyword": "help", "dialog_text": ""}
        )

        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("silvermoss", (result.feedback or "").lower())
        self.assert_flag_set("aldric_commitment_created")

        # Trust should increase from hope
        self.assertGreater(self.get_actor_trust("npc_aldric"), 0)

    def test_commitment_triggers_on_silvermoss_keyword(self) -> None:
        """Mentioning silvermoss to Aldric creates commitment."""
        result = on_aldric_commitment(
            self.aldric, self.accessor, {"keyword": "silvermoss", "dialog_text": ""}
        )

        self.assertTrue(result.allow)
        self.assert_flag_set("aldric_commitment_created")

    def test_commitment_idempotent(self) -> None:
        """Can't create duplicate commitments."""
        on_aldric_commitment(
            self.aldric, self.accessor, {"keyword": "help", "dialog_text": ""}
        )

        result = on_aldric_commitment(
            self.aldric, self.accessor, {"keyword": "help", "dialog_text": ""}
        )

        self.assertIn("already promised", (result.feedback or "").lower())

    def test_first_silvermoss_stabilizes(self) -> None:
        """First silvermoss use stabilizes Aldric."""
        result = on_aldric_heal(
            self.silvermoss, self.accessor, {"target": self.aldric}
        )

        self.assertTrue(result.allow)
        self.assertIn("sit up", (result.feedback or "").lower())
        self.assert_flag_set("aldric_stabilized")
        self.assert_actor_state("npc_aldric", "stabilized")

        # Infection should stop progressing
        conditions = self.aldric.properties["conditions"]
        infection = conditions["fungal_infection"]
        self.assertEqual(infection["progression_rate"], 0)

    def test_second_silvermoss_fully_heals(self) -> None:
        """Second silvermoss use fully heals Aldric."""
        # First silvermoss
        on_aldric_heal(self.silvermoss, self.accessor, {"target": self.aldric})

        # Second silvermoss
        silvermoss2 = self.state.add_item("item_silvermoss_2", name="Silvermoss")
        result = on_aldric_heal(silvermoss2, self.accessor, {"target": self.aldric})

        self.assertTrue(result.allow)
        self.assertIn("whole again", (result.feedback or "").lower())
        self.assert_flag_set("aldric_helped")
        self.assert_flag_set("aldric_fully_healed")
        self.assert_actor_state("npc_aldric", "recovering")

        # Infection should be cleared
        conditions = self.aldric.properties.get("conditions", {})
        self.assertNotIn("fungal_infection", conditions)

    def test_teaching_requires_recovery(self) -> None:
        """Can't learn from Aldric while critical."""
        result = on_aldric_teach(
            self.aldric, self.accessor, {"keyword": "teach", "dialog_text": ""}
        )

        self.assertTrue(result.allow)
        self.assertIn("barely breathe", (result.feedback or "").lower())
        self.assert_flag_not_set("learned_mycology")

    def test_teaching_requires_trust(self) -> None:
        """Can't learn from Aldric without enough trust."""
        # Stabilize Aldric but don't increase trust enough
        self.aldric.properties["state_machine"]["current"] = "stabilized"
        self.aldric.properties["trust_state"]["current"] = 1

        result = on_aldric_teach(
            self.aldric, self.accessor, {"keyword": "teach", "dialog_text": ""}
        )

        self.assertTrue(result.allow)
        self.assertIn("trust you more", (result.feedback or "").lower())
        self.assert_flag_not_set("learned_mycology")

    def test_teaching_requires_gift(self) -> None:
        """Teaching requires an exchange gift."""
        # Fully heal and max trust
        self.aldric.properties["state_machine"]["current"] = "recovering"
        self.aldric.properties["trust_state"]["current"] = 5

        result = on_aldric_teach(
            self.aldric, self.accessor, {"keyword": "teach", "dialog_text": ""}
        )

        self.assertTrue(result.allow)
        self.assertIn("research notes", (result.feedback or "").lower())
        self.assert_flag_not_set("learned_mycology")

    def test_teaching_succeeds_with_notes(self) -> None:
        """Can learn mycology with proper conditions and gift."""
        # Set up player
        player = self.state.actors[ActorId("player")]
        player.properties["skills"] = {}

        # Fully heal and max trust
        self.aldric.properties["state_machine"]["current"] = "recovering"
        self.aldric.properties["trust_state"]["current"] = 5

        # Provide research notes
        result = on_aldric_teach(
            self.aldric,
            self.accessor,
            {"keyword": "teach", "item": "research_notes", "dialog_text": ""},
        )

        self.assertTrue(result.allow)
        self.assertIn("mycology", (result.feedback or "").lower())
        self.assert_flag_set("learned_mycology")
        self.assertTrue(player.properties.get("skills", {}).get("mycology"))


class TestSporeMotherScenarios(ScenarioTestCase):
    """Tests for Spore Mother heal/kill scenarios."""

    def setUp(self) -> None:
        """Set up Spore Mother test fixtures."""
        super().setUp()
        player = self.setup_player(location="spore_heart")
        player.properties["location"] = "spore_heart"

        # Create Spore Mother with blight condition
        self.mother = self.state.add_actor(
            "npc_spore_mother",
            name="Spore Mother",
            properties={
                "state_machine": {
                    "states": ["hostile", "wary", "allied", "dead", "confused"],
                    "initial": "hostile",
                    "current": "hostile",
                },
                "conditions": {"fungal_blight": {"severity": 50, "type": "fungal_blight"}},
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": ["npc_sporeling_1", "npc_sporeling_2"],
                },
            },
            location="spore_heart",
        )

        # Create sporelings
        self.sporeling1 = self.state.add_actor(
            "npc_sporeling_1",
            name="Sporeling",
            properties={
                "state_machine": {
                    "states": ["hostile", "wary", "allied", "confused"],
                    "initial": "hostile",
                    "current": "hostile",
                },
            },
            location="spore_heart",
        )
        self.sporeling2 = self.state.add_actor(
            "npc_sporeling_2",
            name="Sporeling",
            properties={
                "state_machine": {
                    "states": ["hostile", "wary", "allied", "confused"],
                    "initial": "hostile",
                    "current": "hostile",
                },
            },
            location="spore_heart",
        )

        # Create Myconid Elder for trust effects
        self.myconid = self.state.add_actor(
            "npc_myconid_elder",
            name="Myconid Elder",
            properties={
                "trust_state": {"current": 0, "floor": -5, "ceiling": 5},
                "fungal": True,
            },
            location="loc_fungal_depths_colony",
        )

        # Create heartmoss item
        self.heartmoss = self.state.add_item(
            "item_heartmoss",
            name="Heartmoss",
            location="actor:player",
        )

    def test_passive_presence_transitions_to_wary(self) -> None:
        """Three turns without attacking transitions Mother to wary."""
        # Simulate 3 turns of presence
        for _ in range(2):
            result = on_spore_mother_presence(None, self.accessor, {})
            self.assertIsNone(result.feedback)  # Not yet

        # Third turn should trigger
        result = on_spore_mother_presence(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("curiosity", (result.feedback or "").lower())
        self.assert_actor_state("npc_spore_mother", "wary")

    def test_attack_resets_presence_counter(self) -> None:
        """Attacking resets the passive presence counter."""
        # Two turns of presence
        on_spore_mother_presence(None, self.accessor, {})
        on_spore_mother_presence(None, self.accessor, {})

        # Attack!
        self.state.extra["player_attacked_this_turn"] = True
        on_spore_mother_presence(None, self.accessor, {})

        # Should need 3 more turns now
        self.assert_actor_state("npc_spore_mother", "hostile")
        self.assertEqual(self.state.extra.get("spore_mother_presence_turns", 0), 0)

    def test_healing_with_heartmoss(self) -> None:
        """Heartmoss heals Spore Mother and grants waystone fragment."""
        result = on_spore_mother_heal(
            self.heartmoss, self.accessor, {"target": self.mother}
        )

        self.assertTrue(result.allow)
        self.assertIn("gratitude", (result.feedback or "").lower())
        self.assertIn("spore heart", (result.feedback or "").lower())

        self.assert_flag_set("spore_mother_healed")
        self.assert_flag_set("has_spore_heart")
        self.assert_actor_state("npc_spore_mother", "allied")

        # Sporelings should mirror
        self.assert_actor_state("npc_sporeling_1", "allied")
        self.assert_actor_state("npc_sporeling_2", "allied")

        # Blight should be cleared
        conditions = self.mother.properties.get("conditions", {})
        self.assertNotIn("fungal_blight", conditions)

        # Should create positive gossip
        self.assert_gossip_pending("healed")

    def test_killing_spore_mother(self) -> None:
        """Killing Spore Mother has severe consequences."""
        result = on_spore_mother_death(self.mother, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("death cry", (result.feedback or "").lower())
        self.assertIn("horror", (result.feedback or "").lower())

        self.assert_flag_set("spore_mother_dead")
        self.assert_flag_set("has_killed_fungi")  # Death mark!
        self.assert_flag_set("has_mother_heart")

        # Sporelings should be confused
        self.assert_actor_state("npc_sporeling_1", "confused")
        self.assert_actor_state("npc_sporeling_2", "confused")

        # Myconid trust should drop
        trust = self.get_actor_trust("npc_myconid_elder")
        self.assertEqual(trust, -5)  # 0 - 5 = -5

        # Should create negative gossip
        self.assert_gossip_pending("killed")


class TestFungalDeathMarkScenarios(ScenarioTestCase):
    """Tests for fungal death mark system."""

    def setUp(self) -> None:
        """Set up fungal death mark test fixtures."""
        super().setUp()
        self.setup_player(location="loc_fungal_depths")

        # Create a fungal creature
        self.fungal_creature = self.state.add_actor(
            "npc_fungal_shambler",
            name="Fungal Shambler",
            properties={"fungal": True},
            location="loc_fungal_depths",
        )

        # Non-fungal creature
        self.beast = self.state.add_actor(
            "npc_beast",
            name="Beast",
            properties={"fungal": False},
            location="loc_fungal_depths",
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

        # Player as killer
        self.player = self.state.actors[ActorId("player")]

    def test_killing_fungal_creature_sets_mark(self) -> None:
        """Killing a fungal creature sets the death mark."""
        result = on_fungal_kill(
            self.fungal_creature, self.accessor, {"killer": self.player}
        )

        self.assertTrue(result.allow)
        self.assertIn("ripple", (result.feedback or "").lower())
        self.assertIn("learned what you did", (result.feedback or "").lower())
        self.assert_flag_set("has_killed_fungi")

    def test_killing_non_fungal_no_mark(self) -> None:
        """Killing non-fungal creatures doesn't set mark."""
        result = on_fungal_kill(self.beast, self.accessor, {"killer": self.player})

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)
        self.assert_flag_not_set("has_killed_fungi")

    def test_myconid_detects_death_mark(self) -> None:
        """First meeting with Myconid detects death mark."""
        # Set the death mark
        self.state.extra["has_killed_fungi"] = True

        result = on_myconid_first_meeting(self.myconid, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("recoils", (result.feedback or "").lower())
        self.assertIn("death of our kin", (result.feedback or "").lower())

        # Trust should start at -3
        self.assert_actor_trust("npc_myconid_elder", -3)
        self.assert_flag_set("myconid_detected_death_mark")

    def test_myconid_neutral_without_mark(self) -> None:
        """First meeting without mark has no special reaction."""
        result = on_myconid_first_meeting(self.myconid, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)
        self.assert_flag_not_set("myconid_detected_death_mark")


class TestCombinedFungalScenarios(ScenarioTestCase):
    """Tests combining multiple fungal mechanics."""

    def setUp(self) -> None:
        """Set up combined scenario fixtures."""
        super().setUp()
        self.setup_player(location="loc_fungal_depths_entrance")

        # Create Aldric
        self.aldric = self.state.add_actor(
            "npc_aldric",
            name="Scholar Aldric",
            properties={
                "state_machine": {
                    "states": ["critical", "stabilized", "recovering", "dead"],
                    "initial": "critical",
                    "current": "critical",
                },
                "trust_state": {"current": 0, "floor": -3, "ceiling": 5},
            },
            location="loc_fungal_depths_camp",
        )

        # Create Spore Mother
        self.mother = self.state.add_actor(
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

        # Create Myconid
        self.myconid = self.state.add_actor(
            "npc_myconid_elder",
            name="Myconid Elder",
            properties={
                "trust_state": {"current": 0, "floor": -5, "ceiling": 5},
                "fungal": True,
            },
            location="loc_fungal_depths_colony",
        )

    def test_kill_spore_mother_then_meet_myconid(self) -> None:
        """Killing Spore Mother then meeting Myconid shows cumulative effects."""
        player = self.state.actors[ActorId("player")]

        # Kill Spore Mother - sets has_killed_fungi
        on_spore_mother_death(self.mother, self.accessor, {})

        # Now meet Myconid
        result = on_myconid_first_meeting(self.myconid, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIn("recoils", (result.feedback or "").lower())

        # Trust penalty from death (applied by on_spore_mother_death) AND mark detection
        # Death gave -5, then first meeting sets to -3 (the mark penalty)
        self.assert_actor_trust("npc_myconid_elder", -3)

    def test_heal_spore_mother_then_meet_myconid(self) -> None:
        """Healing Spore Mother then meeting Myconid has no mark penalty."""
        # Create heartmoss
        heartmoss = self.state.add_item("item_heartmoss", name="Heartmoss")

        # Heal Spore Mother
        on_spore_mother_heal(heartmoss, self.accessor, {"target": self.mother})

        # Now meet Myconid - no death mark
        result = on_myconid_first_meeting(self.myconid, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)  # No hostile reaction
        self.assert_flag_not_set("has_killed_fungi")

        # Trust should be unchanged
        self.assert_actor_trust("npc_myconid_elder", 0)


if __name__ == "__main__":
    unittest.main()
