"""Scenario tests for Frozen Reaches region using real game state.

Tests multi-step gameplay scenarios including:
- Salamander befriending via fire gifts
- Hypothermia system with temperature zones
- Cold gear and companion mitigation
- Hot springs healing

Tests load big_game via GameEngine to use actual actor IDs, state machines,
and property structures. Each test gets a fresh engine instance.
"""

import unittest
from pathlib import Path
from typing import Any

from tests.conftest import BaseTestCase
from src.game_engine import GameEngine
from src.state_accessor import StateAccessor

GAME_DIR = (Path(__file__).parent.parent.parent / 'examples' / 'big_game').resolve()


class FrozenReachesTestCase(BaseTestCase):
    """Base class for Frozen Reaches tests with real game state."""

    def setUp(self) -> None:
        self.engine = GameEngine(GAME_DIR)
        self.state = self.engine.game_state
        self.accessor = StateAccessor(
            self.state,
            self.engine.behavior_manager
        )

    def _find_item(self, item_id: str) -> Any:
        """Find an item by ID in the game state items list."""
        for item in self.state.items:
            if item.id == item_id:
                return item
        self.fail(f"Item '{item_id}' not found in game state")

    def _get_hypothermia(self, player: Any) -> Any:
        """Get the hypothermia condition from the player, or None."""
        from behavior_libraries.actor_lib.conditions import get_condition
        return get_condition(player, "hypothermia")


# =============================================================================
# Salamander Tests
# =============================================================================


class TestSalamanderScenarios(FrozenReachesTestCase):
    """Tests for salamander befriending scenarios."""

    def setUp(self) -> None:
        super().setUp()
        from examples.big_game.behaviors.regions.frozen_reaches.salamanders import (
            on_receive_item,
        )
        self.on_fire_gift = on_receive_item
        self.salamander = self.state.actors.get("salamander")
        self.assertIsNotNone(self.salamander, "salamander actor must exist")

        # Reset trust to 0 and state to neutral for clean tests
        self.salamander.properties["trust_state"]["current"] = 0
        sm = self.salamander.properties["state_machine"]
        sm["current"] = "neutral"

    def _give_fire_item(self, item: Any = None) -> Any:
        """Give a fire item to the salamander. Defaults to fire_wand."""
        if item is None:
            item = self._find_item("fire_wand")
        context = {"item": item, "item_id": item.id, "giver_id": "player"}
        return self.on_fire_gift(self.salamander, self.accessor, context)

    def test_fire_gift_increases_trust(self) -> None:
        """Giving a fire item increases salamander trust."""
        initial_trust = self.salamander.properties["trust_state"]["current"]

        result = self._give_fire_item()

        self.assertTrue(result.allow)
        self.assertGreater(
            self.salamander.properties["trust_state"]["current"],
            initial_trust,
        )

    def test_first_fire_gift_transitions_to_friendly(self) -> None:
        """First fire gift transitions salamander to friendly state."""
        result = self._give_fire_item()

        self.assertTrue(result.allow)
        sm = self.salamander.properties["state_machine"]
        self.assertEqual(sm["current"], "friendly")
        # Trust should now be 1 (triggers friendly transition)
        self.assertEqual(self.salamander.properties["trust_state"]["current"], 1)

    def test_non_fire_gift_rejected(self) -> None:
        """Non-fire items are rejected by salamander."""
        # Use cold_weather_gear as a non-fire item
        gear = self._find_item("cold_weather_gear")
        context = {"item": gear, "item_id": gear.id, "giver_id": "player"}

        result = self.on_fire_gift(self.salamander, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("shaking its head", (result.feedback or "").lower())
        # State should remain neutral
        sm = self.salamander.properties["state_machine"]
        self.assertEqual(sm["current"], "neutral")
        # Trust should remain at 0
        self.assertEqual(self.salamander.properties["trust_state"]["current"], 0)

    def test_high_trust_indicates_companion_ready(self) -> None:
        """High trust salamander transitions to companion at trust 3."""
        # Set trust to 2 and state to friendly (pre-condition for companion)
        self.salamander.properties["trust_state"]["current"] = 2
        self.salamander.properties["state_machine"]["current"] = "friendly"

        result = self._give_fire_item()

        self.assertTrue(result.allow)
        self.assertEqual(self.salamander.properties["trust_state"]["current"], 3)
        # Should transition to companion state
        sm = self.salamander.properties["state_machine"]
        self.assertEqual(sm["current"], "companion")


# =============================================================================
# Hypothermia Tests
# =============================================================================


class TestHypothermiaScenarios(FrozenReachesTestCase):
    """Tests for hypothermia environmental hazard."""

    def setUp(self) -> None:
        super().setUp()
        from examples.big_game.behaviors.regions.frozen_reaches.hypothermia import (
            on_cold_zone_turn,
        )
        self.on_cold_zone_turn = on_cold_zone_turn
        self.player = self.state.actors.get("player")
        self.assertIsNotNone(self.player, "player actor must exist")

        # Ensure player has clean conditions (dict format per conditions library)
        self.player.properties["conditions"] = {}

    def test_warm_zone_no_hypothermia(self) -> None:
        """Warm zones don't cause hypothermia."""
        # hot_springs has temperature "warm"
        self.player.location = "hot_springs"

        result = self.on_cold_zone_turn(None, self.accessor, {})

        self.assertTrue(result.allow)
        self.assertIsNone(self._get_hypothermia(self.player))

    def test_cold_zone_causes_hypothermia(self) -> None:
        """Cold zones cause gradual hypothermia."""
        # frozen_pass has temperature "cold" (rate 5)
        self.player.location = "frozen_pass"

        for _ in range(5):
            self.on_cold_zone_turn(None, self.accessor, {})

        hypothermia = self._get_hypothermia(self.player)
        self.assertIsNotNone(hypothermia)
        self.assertGreater(hypothermia["severity"], 0)

    def test_cold_gear_reduces_hypothermia(self) -> None:
        """Cold weather gear reduces hypothermia rate by 50%."""
        # ice_caves has temperature "freezing" (rate 10)
        self.player.location = "ice_caves"
        self.player.properties["equipment"] = {"body": "cold_weather_gear"}

        for _ in range(4):
            self.on_cold_zone_turn(None, self.accessor, {})

        hypothermia = self._get_hypothermia(self.player)
        self.assertIsNotNone(hypothermia)
        # 4 turns * 10 * 0.5 = 20 max
        self.assertLessEqual(hypothermia["severity"], 20)

    def test_cloak_grants_cold_immunity(self) -> None:
        """Cold resistance cloak grants full immunity in cold zones."""
        # frozen_pass has temperature "cold"
        self.player.location = "frozen_pass"
        self.player.properties["equipment"] = {"cloak": "cold_resistance_cloak"}

        for _ in range(3):
            self.on_cold_zone_turn(None, self.accessor, {})

        # Should have no hypothermia (cloak gives full immunity in cold)
        hypothermia = self._get_hypothermia(self.player)
        self.assertIsNone(hypothermia)

    def test_salamander_companion_grants_immunity(self) -> None:
        """Salamander companion grants full hypothermia immunity."""
        # frozen_observatory has temperature "extreme" (rate 20)
        self.player.location = "frozen_observatory"

        # Make salamander a companion at same location
        salamander = self.state.actors.get("salamander")
        salamander.location = "frozen_observatory"
        salamander.properties["is_companion"] = True

        for _ in range(3):
            result = self.on_cold_zone_turn(None, self.accessor, {})
            self.assertIsNone(result.feedback)

        hypothermia = self._get_hypothermia(self.player)
        self.assertIsNone(hypothermia)

    def test_hypothermia_severity_warnings(self) -> None:
        """Different severity levels produce different warning feedback."""
        # frozen_observatory has temperature "extreme" (rate 20 per turn)
        self.player.location = "frozen_observatory"

        # First turn - severity 20 -> "getting cold"
        result = self.on_cold_zone_turn(None, self.accessor, {})
        self.assertIsNotNone(result.feedback)
        self.assertIn("getting cold", result.feedback.lower())

        # Turn 2 -> severity 40 -> "seeps into your bones"
        result = self.on_cold_zone_turn(None, self.accessor, {})
        self.assertIn("bones", result.feedback.lower())

        # Turn 3 -> severity 60 -> "shivers"
        result = self.on_cold_zone_turn(None, self.accessor, {})
        self.assertIn("shivers", result.feedback.lower())

        # Turn 4 -> severity 80 -> "freezing to death"
        result = self.on_cold_zone_turn(None, self.accessor, {})
        self.assertIn("freezing to death", result.feedback.lower())


# =============================================================================
# Hot Springs Tests
# =============================================================================


class TestHotSpringsScenarios(FrozenReachesTestCase):
    """Tests for hot springs healing."""

    def setUp(self) -> None:
        super().setUp()
        from examples.big_game.behaviors.regions.frozen_reaches.hypothermia import (
            on_enter_hot_springs,
        )
        self.on_enter_hot_springs = on_enter_hot_springs
        self.player = self.state.actors.get("player")
        self.assertIsNotNone(self.player, "player actor must exist")

        # Ensure clean conditions (dict format per conditions library)
        self.player.properties["conditions"] = {}

    def _get_hot_springs_location(self) -> Any:
        """Find the hot_springs location object."""
        for loc in self.state.locations:
            if loc.id == "hot_springs":
                return loc
        self.fail("hot_springs location not found in game state")

    def test_hot_springs_cures_hypothermia(self) -> None:
        """Hot springs instantly cure hypothermia."""
        from behavior_libraries.actor_lib.conditions import apply_condition
        apply_condition(self.player, "hypothermia", {"severity": 60})

        hot_springs = self._get_hot_springs_location()
        result = self.on_enter_hot_springs(
            self.player, self.accessor, {"destination": hot_springs}
        )

        self.assertTrue(result.allow)
        self.assertIn("fully restored", (result.feedback or "").lower())

        hypothermia = self._get_hypothermia(self.player)
        self.assertIsNotNone(hypothermia)
        self.assertEqual(hypothermia["severity"], 0)

    def test_hot_springs_without_hypothermia(self) -> None:
        """Hot springs still give warmth message without hypothermia."""
        hot_springs = self._get_hot_springs_location()
        result = self.on_enter_hot_springs(
            self.player, self.accessor, {"destination": hot_springs}
        )

        self.assertTrue(result.allow)
        self.assertIn("warmth envelops", (result.feedback or "").lower())


# =============================================================================
# Combined Scenario Tests
# =============================================================================


class TestCombinedFrozenScenarios(FrozenReachesTestCase):
    """Tests combining salamander and hypothermia mechanics."""

    def setUp(self) -> None:
        super().setUp()
        from examples.big_game.behaviors.regions.frozen_reaches.salamanders import (
            on_receive_item,
        )
        from examples.big_game.behaviors.regions.frozen_reaches.hypothermia import (
            on_cold_zone_turn,
        )
        self.on_fire_gift = on_receive_item
        self.on_cold_zone_turn = on_cold_zone_turn

        self.player = self.state.actors.get("player")
        self.assertIsNotNone(self.player, "player actor must exist")
        self.player.properties["conditions"] = {}

        self.salamander = self.state.actors.get("salamander")
        self.assertIsNotNone(self.salamander, "salamander actor must exist")
        # Reset salamander state
        self.salamander.properties["trust_state"]["current"] = 0
        self.salamander.properties["state_machine"]["current"] = "neutral"

    def test_befriend_salamander_then_survive_extreme(self) -> None:
        """Befriending salamander allows survival in extreme cold."""
        fire_wand = self._find_item("fire_wand")

        # Give 3 fire gifts to reach companion trust
        for _ in range(3):
            self.on_fire_gift(
                self.salamander,
                self.accessor,
                {"item": fire_wand, "item_id": fire_wand.id, "giver_id": "player"},
            )

        # Verify salamander reached companion state
        sm = self.salamander.properties["state_machine"]
        self.assertEqual(sm["current"], "companion")

        # Move both player and salamander to extreme cold location
        self.player.location = "frozen_observatory"
        self.salamander.location = "frozen_observatory"
        self.salamander.properties["is_companion"] = True

        # Should survive without hypothermia
        for _ in range(5):
            result = self.on_cold_zone_turn(None, self.accessor, {})
            self.assertIsNone(result.feedback)

        # No hypothermia condition
        hypothermia = self._get_hypothermia(self.player)
        self.assertIsNone(hypothermia)


if __name__ == "__main__":
    unittest.main()
