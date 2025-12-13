"""Integration tests for cross-region entity-dispatcher wiring.

These tests verify that entity configurations in game_state.json
are properly wired to infrastructure dispatchers.
"""
from typing import Any

import unittest
from unittest.mock import MagicMock, patch

from examples.big_game.behaviors.infrastructure.dispatcher_utils import clear_handler_cache
from examples.big_game.behaviors.infrastructure.gift_reactions import on_gift_given
from examples.big_game.behaviors.infrastructure.dialog_reactions import on_dialog_received
from examples.big_game.behaviors.infrastructure.item_use_reactions import on_item_used
from examples.big_game.behaviors.infrastructure.death_reactions import on_entity_death
from examples.big_game.behaviors.infrastructure.pack_mirroring import on_leader_state_change
from src.behavior_manager import EventResult


class MockEntity:
    """Mock entity for testing."""

    def __init__(self, entity_id: str, properties: dict | None = None) -> None:
        self.id = entity_id
        self.properties = properties or {}


class MockState:
    """Mock state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}
        self.actors: dict = {}
        self.locations: list = []


class MockAccessor:
    """Mock accessor for testing."""

    def __init__(self) -> None:
        self.state = MockState()


class TestBeastWildsIntegration(unittest.TestCase):
    """Integration tests for Beast Wilds entity-dispatcher wiring."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_bee_queen_gift_handler_wiring(self) -> None:
        """Bee Queen gift_reactions handler is callable via dispatcher."""
        # Create bee queen entity with same config as game_state.json
        bee_queen = MockEntity(
            "bee_queen",
            {
                "state_machine": {
                    "states": ["defensive", "neutral", "trading", "allied", "hostile"],
                    "initial": "defensive",
                },
                "trust_state": {"current": 0, "floor": -3, "ceiling": 5},
                "gift_reactions": {
                    "handler": "behaviors.regions.beast_wilds.bee_queen:on_flower_offer"
                },
            },
        )
        self.accessor.state.actors["bee_queen"] = bee_queen

        # Create flower item
        flower = MockEntity("item_moonpetal", {})

        context = {"target_actor": bee_queen, "item": flower}

        # Call dispatcher - handler should be invoked
        result = on_gift_given(flower, self.accessor, context)

        # Verify handler was called and returned a message
        self.assertTrue(result.allow)
        # The handler should return a message about the trade
        self.assertIsNotNone(result.message)

    def test_wolf_pack_mirroring_wiring(self) -> None:
        """Wolf pack state mirroring via pack_behavior handler."""
        # Create follower wolves with state machines
        beta_wolf = MockEntity(
            "frost_wolf_1",
            {
                "state_machine": {
                    "states": ["hostile", "wary", "neutral", "friendly", "allied"],
                    "initial": "hostile",
                    "current": "hostile",
                },
            },
        )
        gamma_wolf = MockEntity(
            "frost_wolf_2",
            {
                "state_machine": {
                    "states": ["hostile", "wary", "neutral", "friendly", "allied"],
                    "initial": "hostile",
                    "current": "hostile",
                },
            },
        )
        self.accessor.state.actors["frost_wolf_1"] = beta_wolf
        self.accessor.state.actors["frost_wolf_2"] = gamma_wolf

        # Create alpha wolf with pack_behavior config
        alpha_wolf = MockEntity(
            "alpha_wolf",
            {
                "state_machine": {
                    "states": ["hostile", "wary", "neutral", "friendly", "allied"],
                    "initial": "hostile",
                },
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": ["frost_wolf_1", "frost_wolf_2"],
                },
            },
        )
        self.accessor.state.actors["alpha_wolf"] = alpha_wolf
        self.accessor.state.actors["npc_alpha_wolf"] = alpha_wolf

        context = {"new_state": "wary"}

        # Call pack mirroring dispatcher with data-driven config (no handler)
        result = on_leader_state_change(alpha_wolf, self.accessor, context)

        self.assertTrue(result.allow)
        # Verify follower states changed
        self.assertEqual(beta_wolf.properties["state_machine"]["current"], "wary")
        self.assertEqual(gamma_wolf.properties["state_machine"]["current"], "wary")


class TestFungalDepthsIntegration(unittest.TestCase):
    """Integration tests for Fungal Depths entity-dispatcher wiring."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_aldric_dialog_handler_wiring(self) -> None:
        """Aldric dialog_reactions handler is callable via dispatcher."""
        # Create Aldric with same config as game_state.json
        aldric = MockEntity(
            "npc_aldric",
            {
                "state_machine": {
                    "states": ["critical", "stabilized", "recovering", "dead"],
                    "initial": "critical",
                },
                "trust_state": {"current": 0, "floor": -3, "ceiling": 5},
                "dialog_reactions": {
                    "handler": "behaviors.regions.fungal_depths.aldric_rescue:on_aldric_commitment"
                },
            },
        )
        self.accessor.state.actors["npc_aldric"] = aldric

        context = {"keyword": "help", "dialog_text": ""}

        # Call dialog dispatcher
        result = on_dialog_received(aldric, self.accessor, context)

        self.assertTrue(result.allow)
        # Handler should return a message about commitment
        self.assertIsNotNone(result.message)

    def test_spore_mother_pack_mirroring(self) -> None:
        """Spore Mother pack mirroring to sporelings."""
        # Create sporeling followers
        sporeling1 = MockEntity(
            "npc_sporeling_1",
            {
                "state_machine": {
                    "states": ["hostile", "wary", "allied", "confused"],
                    "initial": "hostile",
                    "current": "hostile",
                },
            },
        )
        sporeling2 = MockEntity(
            "npc_sporeling_2",
            {
                "state_machine": {
                    "states": ["hostile", "wary", "allied", "confused"],
                    "initial": "hostile",
                    "current": "hostile",
                },
            },
        )
        self.accessor.state.actors["npc_sporeling_1"] = sporeling1
        self.accessor.state.actors["npc_sporeling_2"] = sporeling2

        # Create Spore Mother with pack_behavior
        spore_mother = MockEntity(
            "npc_spore_mother",
            {
                "state_machine": {
                    "states": ["hostile", "wary", "allied", "dead", "confused"],
                    "initial": "hostile",
                },
                "pack_behavior": {
                    "pack_follows_leader_state": True,
                    "followers": ["npc_sporeling_1", "npc_sporeling_2"],
                },
            },
        )
        self.accessor.state.actors["npc_spore_mother"] = spore_mother

        context = {"new_state": "wary"}

        # Call pack mirroring with data-driven config
        result = on_leader_state_change(spore_mother, self.accessor, context)

        self.assertTrue(result.allow)
        # Verify sporeling states changed
        self.assertEqual(sporeling1.properties["state_machine"]["current"], "wary")
        self.assertEqual(sporeling2.properties["state_machine"]["current"], "wary")


class TestSunkenDistrictIntegration(unittest.TestCase):
    """Integration tests for Sunken District entity-dispatcher wiring."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_merchant_delvan_death_handler_wiring(self) -> None:
        """Merchant Delvan death_reactions handler is callable via dispatcher."""
        # Create Delvan with death_reactions config
        delvan = MockEntity(
            "merchant_delvan",
            {
                "state_machine": {
                    "states": ["trapped", "freed", "mobile", "dead"],
                    "initial": "trapped",
                },
                "death_reactions": {
                    "handler": "behaviors.regions.sunken_district.dual_rescue:on_npc_death",
                    "set_flags": {"delvan_died": True},
                },
            },
        )

        context: dict[str, Any] = {}

        # Call death reactions dispatcher
        result = on_entity_death(delvan, self.accessor, context)

        self.assertTrue(result.allow)
        # Handler should return a message and set flags
        self.assertIsNotNone(result.message)
        self.assertTrue(self.accessor.state.extra.get("delvan_died"))


class TestFrozenReachesIntegration(unittest.TestCase):
    """Integration tests for Frozen Reaches entity-dispatcher wiring."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_salamander_gift_handler_wiring(self) -> None:
        """Salamander gift_reactions handler is callable via dispatcher."""
        # Create salamander with gift_reactions config
        salamander = MockEntity(
            "salamander",
            {
                "state_machine": {
                    "states": ["neutral", "friendly", "companion"],
                    "initial": "neutral",
                },
                "trust_state": {"current": 0, "floor": 0, "ceiling": 5},
                "gift_reactions": {
                    "handler": "behaviors.regions.frozen_reaches.salamanders:on_fire_gift"
                },
            },
        )
        self.accessor.state.actors["salamander"] = salamander

        # Create fire item
        fire_item = MockEntity("item_torch", {})

        context = {"target_actor": salamander, "item": fire_item}

        # Call gift dispatcher
        result = on_gift_given(fire_item, self.accessor, context)

        self.assertTrue(result.allow)
        # Handler should return a message about fire gift
        self.assertIsNotNone(result.message)
        # Trust should have increased
        self.assertGreater(salamander.properties["trust_state"]["current"], 0)


class TestHandlerLoadFallback(unittest.TestCase):
    """Tests verifying handler load failures fall through to data-driven."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_invalid_handler_falls_through_to_data_driven(self) -> None:
        """Invalid handler path falls through to data-driven processing."""
        # Create entity with invalid handler + valid data-driven config
        entity = MockEntity(
            "npc_test",
            {
                "gift_reactions": {
                    "handler": "invalid.module:nonexistent_handler",
                    "food": {
                        "accepted_items": ["meat"],
                        "accept_message": "Fallback data-driven response",
                    },
                },
            },
        )

        item = MockEntity("item_meat", {})
        context = {"target_actor": entity, "item": item}

        # Call dispatcher - should fall through to data-driven
        result = on_gift_given(item, self.accessor, context)

        self.assertTrue(result.allow)
        # Data-driven response should be returned
        self.assertEqual(result.message, "Fallback data-driven response")


if __name__ == "__main__":
    unittest.main()
