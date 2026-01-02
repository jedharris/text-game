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
    """Test thermal shock damage mechanics.

    Tests verify relationships between damage values rather than exact numbers,
    making them robust to game balance changes.
    """

    def setUp(self):
        """Set up test game with golems and wands."""
        # Add big_game to sys.path so behaviors can be loaded
        import sys
        if str(BIG_GAME_DIR) not in sys.path:
            sys.path.insert(0, str(BIG_GAME_DIR))

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

    def _create_test_golem(self, golem_id, temp_state="neutral", temp_counter=0):
        """Helper to create a test golem with specific temperature state."""
        golem = Actor(
            id=golem_id,
            name=f"{temp_state.title()} Golem",
            description="A test golem",
            location="loc_room",
            inventory=[],
            _properties={
                "health": 150,
                "max_health": 150,
                "armor": 10,
                "temperature_state": temp_state,
                "temperature_counter": temp_counter,
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
        self.game_state.actors[golem_id] = golem
        return golem

    def test_fire_attack_vs_neutral_normal_damage(self):
        """Fire attack vs neutral golem changes temperature state to hot."""
        from behavior_libraries.actor_lib.combat import execute_attack

        attack = self.fire_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        result = execute_attack(self.accessor, player, self.golem, attack)

        self.assertTrue(result.success)
        # Damage should be positive (base minus armor, clamped to 0)
        self.assertGreaterEqual(result.damage, 0)
        # Temperature state should change to match attack type
        self.assertEqual(self.golem.properties["temperature_state"], "hot")
        # Temperature counter should be set
        self.assertGreater(self.golem.properties["temperature_counter"], 0)

    def test_cold_attack_vs_neutral_normal_damage(self):
        """Cold attack vs neutral golem changes temperature state to cold."""
        from behavior_libraries.actor_lib.combat import execute_attack

        attack = self.ice_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        result = execute_attack(self.accessor, player, self.golem, attack)

        self.assertTrue(result.success)
        # Damage should be positive
        self.assertGreaterEqual(result.damage, 0)
        # Temperature state should change to match attack type
        self.assertEqual(self.golem.properties["temperature_state"], "cold")
        # Temperature counter should be set
        self.assertGreater(self.golem.properties["temperature_counter"], 0)

    def test_fire_attack_vs_hot_reduced_damage(self):
        """Fire attack vs hot golem (same temp) deals LESS damage than vs neutral."""
        from behavior_libraries.actor_lib.combat import execute_attack

        # Create baseline: neutral golem
        neutral_golem = self._create_test_golem("neutral_golem", "neutral", 0)

        # Create test golem: hot
        hot_golem = self._create_test_golem("hot_golem", "hot", 3)

        attack = self.fire_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        # Test both scenarios
        neutral_result = execute_attack(self.accessor, player, neutral_golem, attack)
        hot_result = execute_attack(self.accessor, player, hot_golem, attack)

        self.assertTrue(neutral_result.success)
        self.assertTrue(hot_result.success)
        # Same-temperature attack should deal LESS damage than neutral
        self.assertLess(hot_result.damage, neutral_result.damage,
                       "Fire vs hot (same temp) should deal less damage than fire vs neutral")
        # Temperature should stay hot
        self.assertEqual(hot_golem.properties["temperature_state"], "hot")

    def test_cold_attack_vs_cold_reduced_damage(self):
        """Cold attack vs cold golem (same temp) deals LESS damage than vs neutral."""
        from behavior_libraries.actor_lib.combat import execute_attack

        # Create baseline: neutral golem
        neutral_golem = self._create_test_golem("neutral_golem", "neutral", 0)

        # Create test golem: cold
        cold_golem = self._create_test_golem("cold_golem", "cold", 3)

        attack = self.ice_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        # Test both scenarios
        neutral_result = execute_attack(self.accessor, player, neutral_golem, attack)
        cold_result = execute_attack(self.accessor, player, cold_golem, attack)

        self.assertTrue(neutral_result.success)
        self.assertTrue(cold_result.success)
        # Same-temperature attack should deal LESS damage than neutral
        self.assertLess(cold_result.damage, neutral_result.damage,
                       "Cold vs cold (same temp) should deal less damage than cold vs neutral")
        # Temperature should stay cold
        self.assertEqual(cold_golem.properties["temperature_state"], "cold")

    def test_fire_attack_vs_cold_thermal_shock(self):
        """Fire attack vs cold golem (opposite temp) deals MORE damage and triggers thermal shock."""
        from behavior_libraries.actor_lib.combat import execute_attack

        # Create baseline: neutral golem
        neutral_golem = self._create_test_golem("neutral_golem", "neutral", 0)

        # Create test golem: cold (opposite of fire)
        cold_golem = self._create_test_golem("cold_golem", "cold", 3)

        attack = self.fire_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        # Test both scenarios
        neutral_result = execute_attack(self.accessor, player, neutral_golem, attack)
        thermal_shock_result = execute_attack(self.accessor, player, cold_golem, attack)

        self.assertTrue(neutral_result.success)
        self.assertTrue(thermal_shock_result.success)
        # Thermal shock should deal MORE damage than neutral
        self.assertGreater(thermal_shock_result.damage, neutral_result.damage,
                          "Fire vs cold (opposite temp) should deal more damage than fire vs neutral")
        # Should mention thermal shock in narration
        self.assertIn("THERMAL SHOCK", thermal_shock_result.narration)
        # Temperature should flip to hot
        self.assertEqual(cold_golem.properties["temperature_state"], "hot")

    def test_cold_attack_vs_hot_thermal_shock(self):
        """Cold attack vs hot golem (opposite temp) deals MORE damage and triggers thermal shock."""
        from behavior_libraries.actor_lib.combat import execute_attack

        # Create baseline: neutral golem
        neutral_golem = self._create_test_golem("neutral_golem", "neutral", 0)

        # Create test golem: hot (opposite of cold)
        hot_golem = self._create_test_golem("hot_golem", "hot", 3)

        attack = self.ice_wand.properties["attacks"][0]
        player = self.accessor.get_actor("player")

        # Test both scenarios
        neutral_result = execute_attack(self.accessor, player, neutral_golem, attack)
        thermal_shock_result = execute_attack(self.accessor, player, hot_golem, attack)

        self.assertTrue(neutral_result.success)
        self.assertTrue(thermal_shock_result.success)
        # Thermal shock should deal MORE damage than neutral
        self.assertGreater(thermal_shock_result.damage, neutral_result.damage,
                          "Cold vs hot (opposite temp) should deal more damage than cold vs neutral")
        # Should mention thermal shock in narration
        self.assertIn("THERMAL SHOCK", thermal_shock_result.narration)
        # Temperature should flip to cold
        self.assertEqual(hot_golem.properties["temperature_state"], "cold")

    def test_alternating_attacks_optimal_strategy(self):
        """Alternating fire and cold attacks deals more damage than repeating same attack."""
        from behavior_libraries.actor_lib.combat import execute_attack

        player = self.accessor.get_actor("player")
        fire_attack = self.fire_wand.properties["attacks"][0]
        cold_attack = self.ice_wand.properties["attacks"][0]

        # Strategy 1: Alternating attacks (fire, cold, fire, cold, fire)
        alternating_golem = self._create_test_golem("alternating_golem", "neutral", 0)
        alternating_damage = 0
        for i in range(5):
            attack = fire_attack if i % 2 == 0 else cold_attack
            result = execute_attack(self.accessor, player, alternating_golem, attack)
            alternating_damage += result.damage

        # Strategy 2: Repeated fire attacks
        repeated_golem = self._create_test_golem("repeated_golem", "neutral", 0)
        repeated_damage = 0
        for i in range(5):
            result = execute_attack(self.accessor, player, repeated_golem, fire_attack)
            repeated_damage += result.damage

        # Alternating should deal MORE total damage than repeated
        self.assertGreater(alternating_damage, repeated_damage,
                          "Alternating attacks should deal more total damage than repeated attacks")

    def test_melee_attack_ignores_temperature(self):
        """Melee attacks deal same damage regardless of target temperature."""
        from behavior_libraries.actor_lib.combat import execute_attack

        # Create golems at different temperatures
        neutral_golem = self._create_test_golem("neutral_golem", "neutral", 0)
        hot_golem = self._create_test_golem("hot_golem", "hot", 3)
        cold_golem = self._create_test_golem("cold_golem", "cold", 3)

        player = self.accessor.get_actor("player")
        melee_attack = {"name": "sword slash", "damage": 20, "type": "melee"}

        # Attack all three golems with melee
        neutral_result = execute_attack(self.accessor, player, neutral_golem, melee_attack)
        hot_result = execute_attack(self.accessor, player, hot_golem, melee_attack)
        cold_result = execute_attack(self.accessor, player, cold_golem, melee_attack)

        self.assertTrue(neutral_result.success)
        self.assertTrue(hot_result.success)
        self.assertTrue(cold_result.success)

        # All damage should be identical (melee ignores temperature)
        self.assertEqual(neutral_result.damage, hot_result.damage,
                        "Melee damage should be same vs hot golem")
        self.assertEqual(neutral_result.damage, cold_result.damage,
                        "Melee damage should be same vs cold golem")

        # Temperature states should not change
        self.assertEqual(neutral_golem.properties["temperature_state"], "neutral")
        self.assertEqual(hot_golem.properties["temperature_state"], "hot")
        self.assertEqual(cold_golem.properties["temperature_state"], "cold")


if __name__ == '__main__':
    unittest.main(verbosity=2)
