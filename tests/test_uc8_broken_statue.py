"""Implementation of UC8: Broken Statue scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_uc8_broken_statue.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.

UC8 Tests:
- TestUC8Repair: Repair item restores statue health
- TestUC8Functional: Statue becomes functional at health threshold
- TestUC8GuardDuty: Activated statue guards location
"""
from src.types import ActorId

import sys
import unittest
from pathlib import Path
from tests.conftest import BaseTestCase


# Path to game - must be absolute before importing game modules
GAME_DIR = (Path(__file__).parent.parent / 'examples' / 'actor_interaction_test').resolve()
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# No need for _setup_paths() - GameEngine handles sys.path manipulation
# and BaseTestCase.tearDown() handles cleanup

from src.game_engine import GameEngine
from src.state_accessor import StateAccessor


def _create_accessor(engine):
    """Create a StateAccessor from a GameEngine."""
    return StateAccessor(engine.game_state, engine.behavior_manager)


class TestUC8Repair(BaseTestCase):
    """Test repair mechanics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.statue = self.engine.game_state.get_actor(ActorId('npc_broken_statue'))
        self.chisel = None
        for item in self.engine.game_state.items:
            if item.id == 'item_stone_chisel':
                self.chisel = item
                break
        # Move player to main hall
        self.player.location = 'loc_main_hall'

    def test_statue_exists(self):
        """Statue actor exists."""
        self.assertIsNotNone(self.statue)

    def test_statue_is_construct(self):
        """Statue has construct body form."""
        body = self.statue.properties.get('body', {})
        self.assertEqual(body.get('form'), 'construct')

    def test_statue_starts_damaged(self):
        """Statue starts with low health."""
        health = self.statue.properties.get('health')
        max_health = self.statue.properties.get('max_health')
        self.assertLess(health, max_health)
        self.assertEqual(health, 40)

    def test_chisel_exists(self):
        """Stone chisel exists."""
        self.assertIsNotNone(self.chisel)

    def test_chisel_repairs_constructs(self):
        """Chisel has repairs property for constructs."""
        repairs = self.chisel.properties.get('repairs', [])
        self.assertIn('construct', repairs)

    def test_can_repair(self):
        """can_repair correctly identifies chisel can repair statue."""
        from behaviors.uc8_statue import can_repair

        self.assertTrue(can_repair(self.chisel, self.statue))

    def test_apply_repair(self):
        """apply_repair increases statue health."""
        from behaviors.uc8_statue import apply_repair, get_repair_amount

        accessor = _create_accessor(self.engine)

        initial_health = self.statue.properties.get('health')
        repair_amount = get_repair_amount(self.chisel)

        msg = apply_repair(accessor, self.chisel, self.statue)

        new_health = self.statue.properties.get('health')
        self.assertEqual(new_health, initial_health + repair_amount)
        self.assertIn('repair', msg.lower())


class TestUC8Functional(BaseTestCase):
    """Test functional threshold mechanics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.statue = self.engine.game_state.get_actor(ActorId('npc_broken_statue'))

    def test_statue_not_functional_initially(self):
        """Statue starts non-functional."""
        from behaviors.uc8_statue import is_functional

        self.assertFalse(is_functional(self.statue))

    def test_functional_threshold_default(self):
        """Default functional threshold is 80."""
        from behaviors.uc8_statue import get_functional_threshold

        threshold = get_functional_threshold(self.statue)
        self.assertEqual(threshold, 80)

    def test_check_threshold_below(self):
        """Below threshold remains non-functional."""
        from behaviors.uc8_statue import check_functional_threshold, is_functional

        self.statue.properties['health'] = 70  # Below 80

        check_functional_threshold(self.statue)

        self.assertFalse(is_functional(self.statue))

    def test_check_threshold_at(self):
        """At threshold becomes functional."""
        from behaviors.uc8_statue import check_functional_threshold, is_functional

        self.statue.properties['health'] = 80  # At threshold

        check_functional_threshold(self.statue)

        self.assertTrue(is_functional(self.statue))

    def test_check_threshold_above(self):
        """Above threshold is functional."""
        from behaviors.uc8_statue import check_functional_threshold, is_functional

        self.statue.properties['health'] = 100  # Above threshold

        check_functional_threshold(self.statue)

        self.assertTrue(is_functional(self.statue))

    def test_repair_to_functional(self):
        """Repairing to threshold makes statue functional."""
        from behaviors.uc8_statue import apply_repair, is_functional

        accessor = _create_accessor(self.engine)

        # Start at 40 health, repair_amount is 30
        # Two repairs should get to 100, making it functional
        self.assertFalse(is_functional(self.statue))

        # Get chisel
        chisel = None
        for item in self.engine.game_state.items:
            if item.id == 'item_stone_chisel':
                chisel = item
                break

        apply_repair(accessor, chisel, self.statue)  # 40 -> 70
        self.assertFalse(is_functional(self.statue))

        apply_repair(accessor, chisel, self.statue)  # 70 -> 100 (capped)
        self.assertTrue(is_functional(self.statue))


class TestUC8GuardDuty(BaseTestCase):
    """Test guard duty mechanics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.statue = self.engine.game_state.get_actor(ActorId('npc_broken_statue'))
        # Get a hostile actor (spider queen)
        self.hostile = self.engine.game_state.actors.get(ActorId('npc_spider_queen'))

    def test_statue_has_guarding_location(self):
        """Statue has guarding property."""
        from behaviors.uc8_statue import get_guarded_location

        guarded = get_guarded_location(self.statue)
        self.assertEqual(guarded, 'loc_main_hall')

    def test_is_guarding(self):
        """is_guarding correctly identifies guarded location."""
        from behaviors.uc8_statue import is_guarding

        self.assertTrue(is_guarding(self.statue, 'loc_main_hall'))
        self.assertFalse(is_guarding(self.statue, 'loc_central_hub'))

    def test_no_attack_when_non_functional(self):
        """Non-functional statue doesn't attack."""
        from behaviors.uc8_statue import on_guard_duty, is_functional

        accessor = _create_accessor(self.engine)

        # Ensure statue is non-functional
        self.assertFalse(is_functional(self.statue))

        # Move hostile to guarded location
        if self.hostile:
            self.hostile.location = 'loc_main_hall'

        messages = on_guard_duty(accessor, self.statue)

        self.assertEqual(len(messages), 0)

    def test_attack_when_functional(self):
        """Functional statue attacks hostiles."""
        from behaviors.uc8_statue import on_guard_duty, is_functional

        accessor = _create_accessor(self.engine)

        # Make statue functional
        self.statue.properties['health'] = 100
        self.statue.properties['functional'] = True
        self.assertTrue(is_functional(self.statue))

        # Move hostile to guarded location
        if self.hostile:
            initial_hostile_health = self.hostile.properties.get('health', 100)
            self.hostile.location = 'loc_main_hall'

            messages = on_guard_duty(accessor, self.statue)

            # Should have attacked
            self.assertGreater(len(messages), 0)
            # Hostile should have taken damage
            self.assertLess(self.hostile.properties.get('health'), initial_hostile_health)

    def test_get_hostiles_in_location(self):
        """get_hostiles_in_location finds hostile actors."""
        from behaviors.uc8_statue import get_hostiles_in_location

        accessor = _create_accessor(self.engine)

        # Move hostile to main hall
        if self.hostile:
            self.hostile.location = 'loc_main_hall'

            hostiles = get_hostiles_in_location(accessor, self.statue, 'loc_main_hall')

            self.assertIn(self.hostile, hostiles)


if __name__ == '__main__':
    unittest.main(verbosity=2)
