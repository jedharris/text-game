"""Implementation of UC2: Guardian Golems scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_uc2_guardian_golems.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.

UC2 Tests:
- TestUC2GolemSetup: Golems exist with attacks and resistances
- TestUC2WeaponDamage: Weapons deal damage with type bonuses
- TestUC2CoverMechanics: Cover reduces incoming damage
- TestUC2Resistances: Damage resistances reduce incoming damage
- TestUC2Weaknesses: Damage weaknesses increase incoming damage
- TestUC2Counterattack: Golems counterattack when damaged
"""

import sys
import unittest
from pathlib import Path


# Path to game - must be absolute before importing game modules
GAME_DIR = (Path(__file__).parent.parent / 'examples' / 'actor_interaction_test').resolve()
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def _setup_paths():
    """Ensure game directory is first in sys.path for behaviors imports."""
    while '' in sys.path:
        sys.path.remove('')

    game_dir_str = str(GAME_DIR)
    if game_dir_str not in sys.path:
        sys.path.insert(0, game_dir_str)

    project_str = str(PROJECT_ROOT)
    if project_str not in sys.path:
        sys.path.insert(1, project_str)


_setup_paths()

from src.game_engine import GameEngine
from src.state_accessor import StateAccessor


def _create_accessor(engine):
    """Create a StateAccessor from a GameEngine."""
    return StateAccessor(engine.game_state, engine.behavior_manager)


class TestUC2GolemSetup(unittest.TestCase):
    """Test golem actors are properly configured."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.stone_golem = self.engine.game_state.actors['npc_guardian_golem_1']
        self.iron_golem = self.engine.game_state.actors['npc_guardian_golem_2']

    def test_golems_exist(self):
        """Both guardian golems are loaded."""
        self.assertIsNotNone(self.stone_golem)
        self.assertIsNotNone(self.iron_golem)

    def test_golems_in_sanctum(self):
        """Golems are in temple sanctum."""
        self.assertEqual(self.stone_golem.location, 'loc_temple_sanctum')
        self.assertEqual(self.iron_golem.location, 'loc_temple_sanctum')

    def test_golems_are_constructs(self):
        """Golems have construct body form."""
        self.assertEqual(self.stone_golem.properties.get('body', {}).get('form'), 'construct')
        self.assertEqual(self.iron_golem.properties.get('body', {}).get('form'), 'construct')

    def test_golems_are_hostile(self):
        """Golems have hostile disposition."""
        self.assertEqual(self.stone_golem.properties.get('disposition'), 'hostile')
        self.assertEqual(self.iron_golem.properties.get('disposition'), 'hostile')

    def test_golems_have_attacks(self):
        """Golems have attacks defined."""
        from behavior_libraries.actor_lib.combat import get_attacks

        stone_attacks = get_attacks(self.stone_golem)
        iron_attacks = get_attacks(self.iron_golem)

        self.assertGreater(len(stone_attacks), 0)
        self.assertGreater(len(iron_attacks), 0)

    def test_stone_golem_has_area_attack(self):
        """Stone golem has area attack (ground_slam)."""
        from behavior_libraries.actor_lib.combat import get_attacks

        attacks = get_attacks(self.stone_golem)
        area_attacks = [a for a in attacks if a.get('area')]
        self.assertEqual(len(area_attacks), 1)
        self.assertEqual(area_attacks[0]['name'], 'ground_slam')

    def test_golems_have_resistances(self):
        """Golems have damage resistances."""
        stone_res = self.stone_golem.properties.get('resistances', {})
        iron_res = self.iron_golem.properties.get('resistances', {})

        self.assertGreater(stone_res.get('physical', 0), 0)
        self.assertGreater(iron_res.get('physical', 0), 0)


class TestUC2WeaponDamage(unittest.TestCase):
    """Test weapon damage calculation."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors['player']
        self.sword = None
        for item in self.engine.game_state.items:
            if item.id == 'item_rusty_sword':
                self.sword = item
                break

    def test_sword_exists(self):
        """Rusty sword item exists."""
        self.assertIsNotNone(self.sword)

    def test_sword_has_damage(self):
        """Sword has damage property."""
        damage = self.sword.properties.get('damage', 0)
        self.assertGreater(damage, 0)

    def test_calculate_weapon_damage(self):
        """Calculate damage from weapon."""
        from behaviors.uc2_combat import calculate_weapon_damage

        accessor = _create_accessor(self.engine)
        damage = calculate_weapon_damage(accessor, self.player, self.sword)
        self.assertEqual(damage, 15)  # Sword damage from game_state

    def test_calculate_weapon_damage_no_weapon(self):
        """Calculate damage with no weapon returns 0."""
        from behaviors.uc2_combat import calculate_weapon_damage

        accessor = _create_accessor(self.engine)
        damage = calculate_weapon_damage(accessor, self.player, None)
        self.assertEqual(damage, 0)


class TestUC2CoverMechanics(unittest.TestCase):
    """Test cover system mechanics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors['player']
        self.stone_golem = self.engine.game_state.actors['npc_guardian_golem_1']
        self.pillar = None
        for item in self.engine.game_state.items:
            if item.id == 'item_stone_pillar':
                self.pillar = item
                break
        # Move player to temple sanctum
        self.player.location = 'loc_temple_sanctum'

    def test_pillar_has_cover_value(self):
        """Stone pillar has cover_value property."""
        self.assertIsNotNone(self.pillar)
        self.assertEqual(self.pillar.properties.get('cover_value'), 50)

    def test_take_cover(self):
        """Player can take cover behind pillar."""
        from behaviors.uc2_combat import take_cover

        accessor = _create_accessor(self.engine)
        message = take_cover(accessor, self.player, self.pillar)

        self.assertIn('cover', message.lower())
        self.assertEqual(self.player.properties.get('posture'), 'cover')
        self.assertEqual(self.player.properties.get('focused_on'), 'item_stone_pillar')

    def test_leave_cover(self):
        """Player can leave cover."""
        from behaviors.uc2_combat import take_cover, leave_cover

        accessor = _create_accessor(self.engine)
        take_cover(accessor, self.player, self.pillar)
        message = leave_cover(accessor, self.player)

        self.assertIn('leave', message.lower())
        self.assertIsNone(self.player.properties.get('posture'))
        self.assertIsNone(self.player.properties.get('focused_on'))

    def test_leave_cover_not_in_cover(self):
        """Leaving cover when not in cover returns appropriate message."""
        from behaviors.uc2_combat import leave_cover

        accessor = _create_accessor(self.engine)
        message = leave_cover(accessor, self.player)

        self.assertIn('not in cover', message.lower())

    def test_cover_reduces_damage(self):
        """Being in cover reduces incoming damage."""
        from behavior_libraries.actor_lib.combat import calculate_damage
        from behaviors.uc2_combat import take_cover

        accessor = _create_accessor(self.engine)

        # Take cover first
        take_cover(accessor, self.player, self.pillar)

        # Create test attack
        attack = {'name': 'stone_fist', 'damage': 25}
        context = {'cover_value': 50}  # 50% cover

        # Calculate damage with cover
        damage = calculate_damage(attack, self.stone_golem, self.player, context)

        # Damage should be reduced by cover (25 * 0.5 = 12.5 -> 12)
        self.assertEqual(damage, 12)


class TestUC2Resistances(unittest.TestCase):
    """Test damage resistance mechanics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.stone_golem = self.engine.game_state.actors['npc_guardian_golem_1']
        self.iron_golem = self.engine.game_state.actors['npc_guardian_golem_2']

    def test_stone_golem_physical_resistance(self):
        """Stone golem has 30% physical resistance."""
        resistances = self.stone_golem.properties.get('resistances', {})
        self.assertEqual(resistances.get('physical'), 30)

    def test_stone_golem_fire_resistance(self):
        """Stone golem has 50% fire resistance."""
        resistances = self.stone_golem.properties.get('resistances', {})
        self.assertEqual(resistances.get('fire'), 50)

    def test_apply_resistance(self):
        """Resistance reduces incoming damage."""
        from behaviors.uc2_combat import apply_damage_resistance

        # 100 damage with 30% physical resistance = 70 damage
        damage = apply_damage_resistance(100, self.stone_golem, 'physical')
        self.assertEqual(damage, 70)

    def test_apply_high_resistance(self):
        """High resistance significantly reduces damage."""
        from behaviors.uc2_combat import apply_damage_resistance

        # 100 fire damage with 50% fire resistance = 50 damage
        damage = apply_damage_resistance(100, self.stone_golem, 'fire')
        self.assertEqual(damage, 50)

    def test_no_resistance(self):
        """No resistance means full damage."""
        from behaviors.uc2_combat import apply_damage_resistance

        # Lightning damage with no resistance = full damage
        damage = apply_damage_resistance(100, self.stone_golem, 'ice')
        self.assertEqual(damage, 100)


class TestUC2Weaknesses(unittest.TestCase):
    """Test damage weakness mechanics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.stone_golem = self.engine.game_state.actors['npc_guardian_golem_1']
        self.iron_golem = self.engine.game_state.actors['npc_guardian_golem_2']

    def test_stone_golem_lightning_weakness(self):
        """Stone golem has 50% lightning weakness."""
        weaknesses = self.stone_golem.properties.get('weaknesses', {})
        self.assertEqual(weaknesses.get('lightning'), 50)

    def test_iron_golem_rust_weakness(self):
        """Iron golem has 100% rust weakness."""
        weaknesses = self.iron_golem.properties.get('weaknesses', {})
        self.assertEqual(weaknesses.get('rust'), 100)

    def test_apply_weakness(self):
        """Weakness increases incoming damage."""
        from behaviors.uc2_combat import apply_damage_weakness

        # 100 lightning damage with 50% weakness = 150 damage
        damage = apply_damage_weakness(100, self.stone_golem, 'lightning')
        self.assertEqual(damage, 150)

    def test_apply_high_weakness(self):
        """High weakness dramatically increases damage."""
        from behaviors.uc2_combat import apply_damage_weakness

        # 100 rust damage with 100% weakness = 200 damage
        damage = apply_damage_weakness(100, self.iron_golem, 'rust')
        self.assertEqual(damage, 200)

    def test_no_weakness(self):
        """No weakness means normal damage."""
        from behaviors.uc2_combat import apply_damage_weakness

        # Fire damage with no weakness = normal damage
        damage = apply_damage_weakness(100, self.iron_golem, 'fire')
        self.assertEqual(damage, 100)


class TestUC2Counterattack(unittest.TestCase):
    """Test golem counterattack mechanics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors['player']
        self.stone_golem = self.engine.game_state.actors['npc_guardian_golem_1']
        # Move player to temple sanctum
        self.player.location = 'loc_temple_sanctum'

    def test_golem_counterattack(self):
        """Golem counterattacks when damaged."""
        from behaviors.uc2_combat import golem_counterattack

        accessor = _create_accessor(self.engine)
        initial_player_health = self.player.properties.get('health')

        message = golem_counterattack(accessor, self.stone_golem, self.player)

        self.assertIsNotNone(message)
        self.assertIn('counterattack', message.lower())
        # Player should have taken damage
        self.assertLess(self.player.properties.get('health'), initial_player_health)

    def test_dead_golem_no_counterattack(self):
        """Dead golem cannot counterattack."""
        from behaviors.uc2_combat import golem_counterattack

        accessor = _create_accessor(self.engine)

        # Kill the golem
        self.stone_golem.properties['health'] = 0

        message = golem_counterattack(accessor, self.stone_golem, self.player)

        self.assertIsNone(message)

    def test_golem_select_attack(self):
        """Golem selects appropriate attack."""
        from behaviors.uc2_combat import golem_select_attack

        attack = golem_select_attack(self.stone_golem, self.player)

        self.assertIsNotNone(attack)
        # Should select area attack if available
        self.assertEqual(attack.get('name'), 'ground_slam')

    def test_on_golem_damaged_handler(self):
        """on_golem_damaged triggers counterattack."""
        from behaviors.uc2_combat import on_golem_damaged

        accessor = _create_accessor(self.engine)
        initial_player_health = self.player.properties.get('health')

        context = {
            'damage': 10,
            'attacker_id': 'player'
        }

        result = on_golem_damaged(self.stone_golem, accessor, context)

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.message)
        # Player should have taken counterattack damage
        self.assertLess(self.player.properties.get('health'), initial_player_health)


if __name__ == '__main__':
    unittest.main(verbosity=2)
