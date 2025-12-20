"""Tests for Fungal Depths region behaviors."""
from src.types import ActorId

import unittest
from typing import Any

from examples.big_game.behaviors.regions.fungal_depths.fungal_death_mark import (
    on_fungal_kill,
    on_myconid_first_meeting,
)
from examples.big_game.behaviors.regions.fungal_depths.aldric_rescue import (
    on_aldric_commitment,
    on_aldric_heal,
)
from examples.big_game.behaviors.regions.fungal_depths.spore_mother import (
    on_spore_mother_heal,
    on_spore_mother_death,
)
from examples.big_game.behaviors.regions.fungal_depths.light_puzzle import (
    on_water_mushroom,
    on_examine_ceiling,
)


class MockActor:
    """Mock actor for testing."""

    def __init__(self, actor_id: str, properties: dict | None = None) -> None:
        self.id = actor_id
        self.name = actor_id
        self.properties: dict = properties or {}


class MockItem:
    """Mock item for testing."""

    def __init__(self, item_id: str) -> None:
        self.id = item_id


class MockLocation:
    """Mock location for testing."""

    def __init__(self, loc_id: str, properties: dict | None = None) -> None:
        self.id = loc_id
        self.properties: dict = properties or {}


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
# Fungal Death Mark Tests
# =============================================================================


class TestFungalDeathMark(unittest.TestCase):
    """Tests for fungal death mark mechanics."""

    def test_killing_fungal_sets_mark(self) -> None:
        """Killing a fungal creature sets the death mark."""
        state = MockState()
        accessor = MockAccessor(state)

        fungal_creature = MockActor("npc_sporeling_1", {"fungal": True})
        killer = MockActor("player", {})
        context = {"killer": killer}

        result = on_fungal_kill(fungal_creature, accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(state.extra.get("has_killed_fungi"))

    def test_killing_non_fungal_no_mark(self) -> None:
        """Killing a non-fungal creature doesn't set mark."""
        state = MockState()
        accessor = MockAccessor(state)

        creature = MockActor("npc_wolf", {"fungal": False})
        killer = MockActor("player", {})
        context = {"killer": killer}

        result = on_fungal_kill(creature, accessor, context)

        self.assertTrue(result.allow)
        self.assertFalse(state.extra.get("has_killed_fungi", False))


class TestMyconidFirstMeeting(unittest.TestCase):
    """Tests for Myconid death mark detection."""

    def test_myconid_detects_death_mark(self) -> None:
        """Myconid detects death mark and sets trust to -3."""
        state = MockState()
        state.extra["has_killed_fungi"] = True
        myconid = MockActor(
            "npc_myconid_elder",
            {"trust_state": {"current": 0}},
        )
        state.actors[ActorId("npc_myconid_elder")] = myconid
        accessor = MockAccessor(state)

        context: dict[str, Any] = {}
        result = on_myconid_first_meeting(myconid, accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(myconid.properties["trust_state"]["current"], -3)
        self.assertIn("crimson", result.feedback or "")

    def test_myconid_no_mark_normal_trust(self) -> None:
        """Myconid has normal trust without death mark."""
        state = MockState()
        state.extra["has_killed_fungi"] = False
        myconid = MockActor(
            "npc_myconid_elder",
            {"trust_state": {"current": 0}},
        )
        state.actors[ActorId("npc_myconid_elder")] = myconid
        accessor = MockAccessor(state)

        context: dict[str, Any] = {}
        result = on_myconid_first_meeting(myconid, accessor, context)

        self.assertTrue(result.allow)
        # Trust unchanged
        self.assertEqual(myconid.properties["trust_state"]["current"], 0)


# =============================================================================
# Aldric Rescue Tests
# =============================================================================


class TestAldricCommitment(unittest.TestCase):
    """Tests for Aldric commitment mechanics."""

    def test_commitment_keyword_creates_commitment(self) -> None:
        """Commitment keyword creates the Aldric commitment."""
        state = MockState()
        state.extra["turn_count"] = 0
        state.extra["commitment_configs"] = {
            "commit_aldric_help": {
                "id": "commit_aldric_help",
                "target_npc": "npc_aldric",
                "goal": "Give silvermoss to Aldric",
                "base_timer": 50,
                "hope_bonus": 10,
            }
        }
        state.extra["active_commitments"] = []
        aldric = MockActor("npc_aldric", {"trust_state": {"current": 0}})
        state.actors[ActorId("npc_aldric")] = aldric
        accessor = MockAccessor(state)

        context = {"keyword": "I'll find silvermoss for you"}
        result = on_aldric_commitment(aldric, accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(state.extra.get("aldric_commitment_created"))


class TestAldricHeal(unittest.TestCase):
    """Tests for Aldric healing mechanics."""

    def test_silvermoss_stabilizes_aldric(self) -> None:
        """First silvermoss stabilizes Aldric."""
        state = MockState()
        aldric = MockActor(
            "npc_aldric",
            {
                "state_machine": {
                    "states": ["critical", "stabilized", "recovering"],
                    "initial": "critical",
                },
                "conditions": {
                    "fungal_infection": {"severity": 80, "progression_rate": 2}
                },
            },
        )
        state.actors[ActorId("npc_aldric")] = aldric
        accessor = MockAccessor(state)

        item = MockItem("item_silvermoss")
        target = aldric
        context = {"target": target}

        result = on_aldric_heal(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(aldric.properties["state_machine"]["current"], "stabilized")
        self.assertTrue(state.extra.get("aldric_stabilized"))


# =============================================================================
# Spore Mother Tests
# =============================================================================


class TestSporeMother(unittest.TestCase):
    """Tests for Spore Mother mechanics."""

    def test_heartmoss_heals_spore_mother(self) -> None:
        """Heartmoss heals Spore Mother and clears spores."""
        state = MockState()
        state.extra["turn_count"] = 0
        mother = MockActor(
            "npc_spore_mother",
            {
                "state_machine": {
                    "states": ["hostile", "wary", "allied"],
                    "initial": "hostile",
                },
                "conditions": {"fungal_blight": {"severity": 70}},
            },
        )
        state.actors[ActorId("npc_spore_mother")] = mother
        state.locations = [
            MockLocation("spore_heart", {"spore_level": "high"}),
            MockLocation("luminous_grotto", {"spore_level": "medium"}),
        ]
        accessor = MockAccessor(state)

        item = MockItem("item_heartmoss")
        context = {"target": mother}

        result = on_spore_mother_heal(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(mother.properties["state_machine"]["current"], "allied")
        self.assertTrue(state.extra.get("spore_mother_healed"))
        # Spore levels cleared
        self.assertEqual(state.locations[0].properties["spore_level"], "none")

    def test_killing_spore_mother_sets_flags(self) -> None:
        """Killing Spore Mother sets negative flags."""
        state = MockState()
        state.extra["turn_count"] = 0
        mother = MockActor("npc_spore_mother", {})
        myconid = MockActor(
            "npc_myconid_elder",
            {"trust_state": {"current": 0}},
        )
        state.actors[ActorId("npc_spore_mother")] = mother
        state.actors[ActorId("npc_myconid_elder")] = myconid
        accessor = MockAccessor(state)

        context: dict[str, Any] = {}
        result = on_spore_mother_death(mother, accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(state.extra.get("spore_mother_dead"))
        self.assertTrue(state.extra.get("has_killed_fungi"))
        self.assertEqual(myconid.properties["trust_state"]["current"], -5)


# =============================================================================
# Light Puzzle Tests
# =============================================================================


class TestLightPuzzle(unittest.TestCase):
    """Tests for light puzzle mechanics."""

    def test_watering_gold_mushroom_increases_light(self) -> None:
        """Watering gold mushroom increases light by 2."""
        state = MockState()
        state.extra["bucket_water_charges"] = 3
        # Use inventory as list so behavior falls back to state.extra for water charges
        player = MockActor("player", {"inventory": []})
        state.actors[ActorId("player")] = player
        # Note: behavior uses state.extra as fallback if grotto not found
        state.extra["grotto_light_level"] = 2
        accessor = MockAccessor(state)

        item = MockItem("bucket")
        target = MockItem("mushroom_gold")
        context = {"target": target}

        result = on_water_mushroom(item, accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(state.extra["grotto_light_level"], 4)
        self.assertEqual(state.extra["bucket_water_charges"], 2)

    def test_examining_ceiling_requires_light(self) -> None:
        """Ceiling cannot be read without enough light."""
        state = MockState()
        state.locations = [MockLocation("luminous_grotto", {"light_level": 3})]
        accessor = MockAccessor(state)

        ceiling = MockItem("ceiling_inscription")
        context: dict[str, Any] = {}

        result = on_examine_ceiling(ceiling, accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("too dim", result.feedback or "")
        self.assertFalse(state.extra.get("safe_path_known", False))

    def test_examining_ceiling_with_light_grants_safe_path(self) -> None:
        """Reading ceiling with enough light grants safe path knowledge."""
        state = MockState()
        state.locations = [MockLocation("luminous_grotto", {"light_level": 6})]
        accessor = MockAccessor(state)

        ceiling = MockItem("ceiling_inscription")
        context: dict[str, Any] = {}

        result = on_examine_ceiling(ceiling, accessor, context)

        self.assertTrue(result.allow)
        self.assertTrue(state.extra.get("safe_path_known"))
        self.assertIn("memorize", result.feedback or "")


if __name__ == "__main__":
    unittest.main()
