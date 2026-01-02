"""Implementation of thermal shock tests.

Tests the temperature-based damage system for stone golems attacked
with fire and cold weapons.

This module contains the actual test implementations. Run via
test_thermal_shock.py wrapper to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.
"""
import sys
import unittest
from pathlib import Path
from tests.conftest import BaseTestCase


# Path setup
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BIG_GAME_DIR = PROJECT_ROOT / "examples" / "big_game"

# No need for _setup_paths() - GameEngine handles sys.path manipulation
# and BaseTestCase.tearDown() handles cleanup

from src.state_manager import GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from tests.conftest import make_action


class TestThermalShock(BaseTestCase):
    """Test thermal shock damage mechanics."""

    def setUp(self):
        """Set up test game with golems and wands."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A room"
        )

        # Fire wand with fire attack
        self.fire_wand = Item(
            id="fire_wand",
            name="fire wand",
            description="A wand of fire",
            location="loc_room",
            _properties={
                "portable": True,
                "fire_aspected": True,
                "attacks": [
                    {
                        "name": "fire blast",
                        "damage": 20,
                        "type": "fire"
                    }
                ]
            }
        )

        # Ice wand with cold attack
        self.ice_wand = Item(
            id="ice_wand",
            name="ice wand",
            description="A wand of ice",
            location="loc_room",
            _properties={
                "portable": True,
                "cold_aspected": True,
                "attacks": [
                    {
                        "name": "ice blast",
                        "damage": 20,
                        "type": "cold"
                    }
                ]
            }
        )

        # Stone golem with temperature properties
        self.golem = Actor(
            id="stone_golem",
            name="Stone Guardian",
            description="A stone golem",
            location="loc_room",
            inventory=[],
            _properties={
                "health": 150,
                "max_health": 150,
                "armor": 10,
                "temperature_state": "neutral",
                "temperature_counter": 0,
                "attacks": [
                    {
                        "name": "stone fist",
                        "damage": 30,
                        "type": "melee"
                    }
                ]
            },
            behaviors=["behaviors.regions.frozen_reaches.thermal_shock"]
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.fire_wand, self.ice_wand],
            actors={
                "player": Actor(
                    id="player",
                    name="Adventurer",
                    description="The player",
                    location="loc_room",
                    inventory=[]
                ),
                "stone_golem": self.golem
            },
            locks=[],
            parts=[]
        )

        # Load behaviors using module loading
        self.behavior_manager = BehaviorManager()

        # Load thermal_shock module (big_game already in sys.path from _setup_paths)
        self.behavior_manager.load_module("behaviors.regions.frozen_reaches.thermal_shock", tier=4)

        # Load combat module (PROJECT_ROOT already in sys.path from _setup_paths)
        self.behavior_manager.load_module("behavior_libraries.actor_lib.combat", tier=3)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_fire_attack_vs_neutral_normal_damage(self):
        """Fire attack vs neutral golem deals normal damage (20 base - 10 armor = 10)."""
        from behavior_libraries.actor_lib.combat import execute_attack

        attack = self.fire_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        result = execute_attack(self.accessor, player, self.golem, attack)

        self.assertTrue(result.success)
        self.assertEqual(result.damage, 10)  # 20 base - 10 armor
        self.assertEqual(self.golem.properties["temperature_state"], "hot")
        self.assertEqual(self.golem.properties["temperature_counter"], 3)

    def test_cold_attack_vs_neutral_normal_damage(self):
        """Cold attack vs neutral golem deals normal damage (20 base - 10 armor = 10)."""
        from behavior_libraries.actor_lib.combat import execute_attack

        attack = self.ice_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        result = execute_attack(self.accessor, player, self.golem, attack)

        self.assertTrue(result.success)
        self.assertEqual(result.damage, 10)  # 20 base - 10 armor
        self.assertEqual(self.golem.properties["temperature_state"], "cold")
        self.assertEqual(self.golem.properties["temperature_counter"], 3)

    def test_fire_attack_vs_hot_reduced_damage(self):
        """Fire attack vs hot golem deals reduced damage (5 base - 10 armor = 0)."""
        from behavior_libraries.actor_lib.combat import execute_attack

        # Set golem to hot
        self.golem.properties["temperature_state"] = "hot"
        self.golem.properties["temperature_counter"] = 3

        attack = self.fire_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        result = execute_attack(self.accessor, player, self.golem, attack)

        self.assertTrue(result.success)
        # 20 * 0.25 = 5, then 5 - 10 armor = 0 (clamped to 0)
        self.assertEqual(result.damage, 0)
        self.assertEqual(self.golem.properties["temperature_state"], "hot")
        self.assertEqual(self.golem.properties["temperature_counter"], 3)

    def test_cold_attack_vs_cold_reduced_damage(self):
        """Cold attack vs cold golem deals reduced damage (5 base - 10 armor = 0)."""
        from behavior_libraries.actor_lib.combat import execute_attack

        # Set golem to cold
        self.golem.properties["temperature_state"] = "cold"
        self.golem.properties["temperature_counter"] = 3

        attack = self.ice_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        result = execute_attack(self.accessor, player, self.golem, attack)

        self.assertTrue(result.success)
        # 20 * 0.25 = 5, then 5 - 10 armor = 0 (clamped to 0)
        self.assertEqual(result.damage, 0)
        self.assertEqual(self.golem.properties["temperature_state"], "cold")
        self.assertEqual(self.golem.properties["temperature_counter"], 3)

    def test_fire_attack_vs_cold_thermal_shock(self):
        """Fire attack vs cold golem deals thermal shock damage (40 base - 10 armor = 30)."""
        from behavior_libraries.actor_lib.combat import execute_attack

        # Set golem to cold
        self.golem.properties["temperature_state"] = "cold"
        self.golem.properties["temperature_counter"] = 3

        attack = self.fire_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        result = execute_attack(self.accessor, player, self.golem, attack)

        self.assertTrue(result.success)
        # 20 * 2.0 = 40, then 40 - 10 armor = 30
        self.assertEqual(result.damage, 30)
        self.assertEqual(self.golem.properties["temperature_state"], "hot")
        self.assertEqual(self.golem.properties["temperature_counter"], 3)
        self.assertIn("THERMAL SHOCK", result.narration)

    def test_cold_attack_vs_hot_thermal_shock(self):
        """Cold attack vs hot golem deals thermal shock damage (40 base - 10 armor = 30)."""
        from behavior_libraries.actor_lib.combat import execute_attack

        # Set golem to hot
        self.golem.properties["temperature_state"] = "hot"
        self.golem.properties["temperature_counter"] = 3

        attack = self.ice_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        result = execute_attack(self.accessor, player, self.golem, attack)

        self.assertTrue(result.success)
        # 20 * 2.0 = 40, then 40 - 10 armor = 30
        self.assertEqual(result.damage, 30)
        self.assertEqual(self.golem.properties["temperature_state"], "cold")
        self.assertEqual(self.golem.properties["temperature_counter"], 3)
        self.assertIn("THERMAL SHOCK", result.narration)

    def test_alternating_attacks_optimal_strategy(self):
        """Alternating fire and cold attacks is the optimal strategy."""
        from behavior_libraries.actor_lib.combat import execute_attack

        player = self.accessor.get_actor("player")
        fire_attack = self.fire_wand.properties["attacks"][0]
        cold_attack = self.ice_wand.properties["attacks"][0]

        # Attack 1: Fire vs neutral = 10 damage
        result = execute_attack(self.accessor, player, self.golem, fire_attack)
        self.assertEqual(result.damage, 10)
        self.assertEqual(self.golem.properties["temperature_state"], "hot")

        # Attack 2: Cold vs hot = 30 damage (THERMAL SHOCK!)
        result = execute_attack(self.accessor, player, self.golem, cold_attack)
        self.assertEqual(result.damage, 30)
        self.assertEqual(self.golem.properties["temperature_state"], "cold")

        # Attack 3: Fire vs cold = 30 damage (THERMAL SHOCK!)
        result = execute_attack(self.accessor, player, self.golem, fire_attack)
        self.assertEqual(result.damage, 30)
        self.assertEqual(self.golem.properties["temperature_state"], "hot")

        # Attack 4: Cold vs hot = 30 damage (THERMAL SHOCK!)
        result = execute_attack(self.accessor, player, self.golem, cold_attack)
        self.assertEqual(result.damage, 30)
        self.assertEqual(self.golem.properties["temperature_state"], "cold")

        # Attack 5: Fire vs cold = 30 damage (THERMAL SHOCK!)
        result = execute_attack(self.accessor, player, self.golem, fire_attack)
        self.assertEqual(result.damage, 30)

        # Total damage: 10 + 30 + 30 + 30 + 30 = 130 damage
        # Golem started at 150 HP, should have 20 HP left
        # (This test doesn't actually apply damage, just verifies calculation)

    def test_melee_attack_ignores_temperature(self):
        """Melee attacks ignore temperature state."""
        from behavior_libraries.actor_lib.combat import execute_attack

        # Set golem to cold
        self.golem.properties["temperature_state"] = "cold"

        player = self.accessor.get_actor("player")
        melee_attack = {"name": "sword slash", "damage": 20, "type": "melee"}

        result = execute_attack(self.accessor, player, self.golem, melee_attack)

        self.assertTrue(result.success)
        # 20 - 10 armor = 10, no temperature multiplier
        self.assertEqual(result.damage, 10)
        # Temperature state should not change
        self.assertEqual(self.golem.properties["temperature_state"], "cold")


if __name__ == '__main__':
    unittest.main(verbosity=2)
