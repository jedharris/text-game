"""Implementation of UC1: Infected Scholar scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_uc1_infected_scholar.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.

UC1 Tests:
- TestUC1Infection: Spore exposure applies condition
- TestUC1Resistance: Player resistance reduces severity
- TestUC1Cure: Giving silvermoss cures scholar
- TestUC1Contagion: Proximity to infected spreads condition
- TestUC1Progression: Condition worsens over turns
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
from src.state_manager import Actor
from src.state_accessor import StateAccessor


def _create_accessor(engine):
    """Create a StateAccessor from a GameEngine."""
    return StateAccessor(engine.game_state, engine.behavior_manager)


class TestUC1Infection(BaseTestCase):
    """Test spore exposure applies fungal_infection condition."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))

    def test_spore_exposure_low_level(self):
        """Low spore exposure applies low severity infection."""
        from behavior_libraries.actor_lib.environment import check_spores

        # Get the low spore part
        part = None
        for p in self.engine.game_state.parts:
            if p.id == 'part_basement_entrance':
                part = p
                break

        self.assertIsNotNone(part)

        # Player starts without infection
        self.assertNotIn('conditions', self.player.properties)

        # Apply spore effect
        msg = check_spores(self.player, part)

        # Player should now have fungal_infection
        self.assertIn('conditions', self.player.properties)
        self.assertIn('fungal_infection', self.player.properties['conditions'])
        self.assertEqual(
            self.player.properties['conditions']['fungal_infection']['severity'],
            5  # Low spore level = severity 5
        )

    def test_spore_exposure_high_level(self):
        """High spore exposure applies high severity infection."""
        from behavior_libraries.actor_lib.environment import check_spores

        # Get the high spore part
        part = None
        for p in self.engine.game_state.parts:
            if p.id == 'part_basement_center':
                part = p
                break

        self.assertIsNotNone(part)

        # Apply spore effect
        msg = check_spores(self.player, part)

        # Player should have high severity infection
        self.assertIn('fungal_infection', self.player.properties.get('conditions', {}))
        self.assertEqual(
            self.player.properties['conditions']['fungal_infection']['severity'],
            30  # High spore level = severity 30
        )

    def test_spore_exposure_stacks(self):
        """Repeated spore exposure increases severity."""
        from behavior_libraries.actor_lib.environment import check_spores

        # Get the low spore part
        part = None
        for p in self.engine.game_state.parts:
            if p.id == 'part_basement_entrance':
                part = p
                break

        # First exposure
        check_spores(self.player, part)
        first_severity = self.player.properties['conditions']['fungal_infection']['severity']

        # Second exposure
        check_spores(self.player, part)
        second_severity = self.player.properties['conditions']['fungal_infection']['severity']

        # Severity should have increased
        self.assertGreater(second_severity, first_severity)
        self.assertEqual(second_severity, first_severity + 5)


class TestUC1Resistance(BaseTestCase):
    """Test player resistance reduces condition severity."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        # Player has 30% disease resistance per game_state.json

    def test_resistance_reduces_severity(self):
        """Resistance reduces incoming condition severity."""
        from behaviors.uc1_infection import apply_condition_with_resistance

        # Apply infection with resistance calculation
        msg = apply_condition_with_resistance(
            self.player,
            'fungal_infection',
            {'severity': 100, 'damage_per_turn': 2}
        )

        # Severity should be reduced by 30% (100 * 0.7 = 70)
        self.assertIn('conditions', self.player.properties)
        actual_severity = self.player.properties['conditions']['fungal_infection']['severity']
        self.assertEqual(actual_severity, 70)
        self.assertIn('resistance', msg.lower())

    def test_resistance_calculation(self):
        """Test the resistance calculation function directly."""
        from behaviors.uc1_infection import apply_resistance

        # 30% resistance on 100 severity = 70
        self.assertEqual(apply_resistance(100, 30), 70)

        # 50% resistance on 50 severity = 25
        self.assertEqual(apply_resistance(50, 50), 25)

        # 0% resistance = no change
        self.assertEqual(apply_resistance(100, 0), 100)

        # 100% resistance = minimum 1
        self.assertEqual(apply_resistance(100, 100), 1)

    def test_no_resistance_full_severity(self):
        """Actor without resistance gets full severity."""
        from behaviors.uc1_infection import apply_condition_with_resistance

        # Remove player's resistance
        self.player.properties['resistances'] = {}

        # Apply infection
        apply_condition_with_resistance(
            self.player,
            'fungal_infection',
            {'severity': 50}
        )

        # Full severity
        self.assertEqual(
            self.player.properties['conditions']['fungal_infection']['severity'],
            50
        )


class TestUC1Cure(BaseTestCase):
    """Test giving silvermoss cures scholar's fungal infection."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.scholar = self.engine.game_state.get_actor(ActorId('npc_scholar'))

    def test_scholar_starts_infected(self):
        """Scholar starts with fungal_infection condition."""
        self.assertIn('conditions', self.scholar.properties)
        self.assertIn('fungal_infection', self.scholar.properties['conditions'])
        self.assertEqual(
            self.scholar.properties['conditions']['fungal_infection']['severity'],
            80
        )

    def test_silvermoss_can_treat_infection(self):
        """Silvermoss item can treat fungal_infection."""
        from behavior_libraries.actor_lib.treatment import can_treat, get_treatable_conditions

        silvermoss = None
        for item in self.engine.game_state.items:
            if item.id == 'item_silvermoss':
                silvermoss = item
                break

        self.assertIsNotNone(silvermoss)
        self.assertTrue(can_treat(silvermoss, 'fungal_infection'))
        self.assertIn('fungal_infection', get_treatable_conditions(silvermoss))

    def test_treatment_cures_scholar(self):
        """Applying silvermoss treatment cures the scholar."""
        from behavior_libraries.actor_lib.treatment import apply_treatment

        silvermoss = None
        for item in self.engine.game_state.items:
            if item.id == 'item_silvermoss':
                silvermoss = item
                break

        accessor = _create_accessor(self.engine)

        # Apply treatment
        result = apply_treatment(accessor, silvermoss, self.scholar)

        self.assertTrue(result.success)
        self.assertIn('fungal_infection', result.conditions_treated)

        # Scholar should no longer have the infection
        self.assertNotIn(
            'fungal_infection',
            self.scholar.properties.get('conditions', {})
        )

    def test_consumable_item_removed(self):
        """Consumable treatment items are removed after use."""
        from behavior_libraries.actor_lib.treatment import apply_treatment

        silvermoss = None
        for item in self.engine.game_state.items:
            if item.id == 'item_silvermoss':
                silvermoss = item
                break

        # Put silvermoss in player inventory
        self.player.inventory.append('item_silvermoss')
        accessor = _create_accessor(self.engine)

        # Apply treatment
        result = apply_treatment(accessor, silvermoss, self.scholar)

        self.assertTrue(result.item_consumed)
        self.assertNotIn('item_silvermoss', self.player.inventory)


class TestUC1Contagion(BaseTestCase):
    """Test proximity to infected spreads condition."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.scholar = self.engine.game_state.get_actor(ActorId('npc_scholar'))

    def test_contagion_requires_focus(self):
        """Contagion only spreads when focused on infected actor."""
        from behaviors.uc1_infection import check_contagion

        accessor = _create_accessor(self.engine)

        # Move player to library (same location as scholar)
        self.player.location = 'loc_library'

        # Without focus, no contagion
        self.player.properties['focused_on'] = None
        msg = check_contagion(self.scholar, self.player, accessor)

        self.assertIsNone(msg)
        self.assertNotIn('fungal_infection', self.player.properties.get('conditions', {}))

    def test_contagion_spreads_with_focus(self):
        """Contagion spreads when player focused on infected NPC."""
        from behaviors.uc1_infection import check_contagion

        accessor = _create_accessor(self.engine)

        # Move player to library and focus on scholar
        self.player.location = 'loc_library'
        self.player.properties['focused_on'] = 'npc_scholar'

        # Contagion should spread
        msg = check_contagion(self.scholar, self.player, accessor)

        self.assertIsNotNone(msg)
        self.assertIn('conditions', self.player.properties)
        self.assertIn('fungal_infection', self.player.properties['conditions'])

    def test_contagion_severity_reduced(self):
        """Contagion spreads with reduced severity."""
        from behaviors.uc1_infection import check_contagion

        accessor = _create_accessor(self.engine)

        self.player.location = 'loc_library'
        self.player.properties['focused_on'] = 'npc_scholar'
        # Remove resistance for clear test
        self.player.properties['resistances'] = {}

        check_contagion(self.scholar, self.player, accessor)

        # Scholar has severity 80, contagion should be 80/4 = 20
        player_severity = self.player.properties['conditions']['fungal_infection']['severity']
        self.assertEqual(player_severity, 20)

    def test_contagion_affected_by_resistance(self):
        """Contagion severity is reduced by player resistance."""
        from behaviors.uc1_infection import check_contagion

        accessor = _create_accessor(self.engine)

        self.player.location = 'loc_library'
        self.player.properties['focused_on'] = 'npc_scholar'
        # Player has 30% disease resistance

        check_contagion(self.scholar, self.player, accessor)

        # Scholar severity 80 -> contagion 20 -> with 30% resistance = 14
        player_severity = self.player.properties['conditions']['fungal_infection']['severity']
        self.assertEqual(player_severity, 14)


class TestUC1Progression(BaseTestCase):
    """Test condition worsens over turns."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.scholar = self.engine.game_state.get_actor(ActorId('npc_scholar'))

    def test_condition_tick_applies_damage(self):
        """Condition tick applies damage_per_turn to health (net with regeneration)."""
        from behavior_libraries.actor_lib.conditions import tick_conditions

        initial_health = self.scholar.properties['health']
        damage_per_turn = self.scholar.properties['conditions']['fungal_infection']['damage_per_turn']
        default_regen = 5  # Living actors get default 5 HP/turn

        tick_conditions(self.scholar)

        # Net effect: damage - regen
        expected_health = initial_health - damage_per_turn + default_regen
        self.assertEqual(
            self.scholar.properties['health'],
            expected_health
        )

    def test_condition_tick_increases_severity(self):
        """Condition tick increases severity by progression_rate."""
        from behavior_libraries.actor_lib.conditions import tick_conditions

        initial_severity = self.scholar.properties['conditions']['fungal_infection']['severity']
        progression_rate = self.scholar.properties['conditions']['fungal_infection']['progression_rate']

        tick_conditions(self.scholar)

        self.assertEqual(
            self.scholar.properties['conditions']['fungal_infection']['severity'],
            initial_severity + progression_rate
        )

    def test_multiple_ticks_cumulative(self):
        """Multiple condition ticks have cumulative effect."""
        from behavior_libraries.actor_lib.conditions import tick_conditions

        initial_health = self.scholar.properties['health']
        damage_per_turn = self.scholar.properties['conditions']['fungal_infection']['damage_per_turn']
        default_regen = 5  # Living actors get default 5 HP/turn

        # Three ticks
        tick_conditions(self.scholar)
        tick_conditions(self.scholar)
        tick_conditions(self.scholar)

        # Net effect per tick: -2 damage + 5 regen = +3
        # After 3 ticks: +9 total
        expected_health = initial_health - (damage_per_turn * 3) + (default_regen * 3)
        self.assertEqual(
            self.scholar.properties['health'],
            expected_health
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
