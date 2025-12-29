"""Implementation of big_game condition tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_big_game_conditions.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.
"""

import sys
import unittest
from pathlib import Path


# Path to game - must be absolute before importing game modules
GAME_DIR = (Path(__file__).parent.parent / 'examples' / 'big_game').resolve()
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def _setup_paths():
    """Ensure game directory is first in sys.path for behaviors imports.

    The game directory is added first so that its behaviors/ package is found
    before the project root's behaviors/ package.

    IMPORTANT: We remove '' (current directory) from path because when running
    from project root, Python would find behaviors/ from project root before
    finding it from the game directory.
    """
    # Remove CWD ('') from path to prevent project root behaviors from being found
    while '' in sys.path:
        sys.path.remove('')

    # Add game directory first (for behaviors imports)
    game_dir_str = str(GAME_DIR)
    if game_dir_str not in sys.path:
        sys.path.insert(0, game_dir_str)

    # Add project root after (for src imports)
    project_str = str(PROJECT_ROOT)
    if project_str not in sys.path:
        sys.path.insert(1, project_str)


# Set up paths before importing game modules
_setup_paths()

from src.game_engine import GameEngine
from src.state_accessor import StateAccessor
from src.types import LocationId


class TestBigGameConditionIntegration(unittest.TestCase):
    """Test condition system integration with big_game."""

    def setUp(self):
        """Load big_game state and engine."""
        self.engine = GameEngine(GAME_DIR)
        self.accessor = StateAccessor(
            self.engine.game_state,
            self.engine.behavior_manager
        )

    def test_condition_tick_hook_registered(self):
        """Verify condition_tick hook is registered."""
        hook_event = self.engine.behavior_manager._hook_to_event.get('condition_tick')
        self.assertIsNotNone(hook_event, "condition_tick hook should be registered")
        event_name, tier = hook_event
        self.assertEqual(event_name, 'on_condition_tick')

    def test_aldric_has_fungal_infection(self):
        """Aldric starts with fungal infection in game_state.json."""
        aldric = self.engine.game_state.actors.get('npc_aldric')
        self.assertIsNotNone(aldric)

        conditions = aldric.properties.get('conditions', {})
        self.assertIn('fungal_infection', conditions)

        infection = conditions['fungal_infection']
        self.assertEqual(infection.get('severity'), 80)
        self.assertEqual(infection.get('damage_per_turn'), 7)
        self.assertEqual(infection.get('progression_rate'), 2)

    def test_spore_mother_has_regeneration(self):
        """Spore Mother has regeneration property."""
        spore_mother = self.engine.game_state.actors.get('npc_spore_mother')
        self.assertIsNotNone(spore_mother)
        self.assertEqual(spore_mother.properties.get('regeneration'), 10)

    def test_health_regeneration_healing(self):
        """Actor with regeneration property heals each turn."""
        from behavior_libraries.actor_lib.conditions import tick_conditions

        # Use Spore Mother with regeneration
        spore_mother = self.engine.game_state.actors.get('npc_spore_mother')
        spore_mother.properties['health'] = 50  # Damaged
        spore_mother.properties['max_health'] = 150
        spore_mother.properties['regeneration'] = 10

        # Tick conditions
        messages = tick_conditions(spore_mother)

        # Should have healed
        self.assertEqual(spore_mother.properties['health'], 60)
        self.assertIn('regenerates 10 health', ' '.join(messages))

    def test_health_regeneration_caps_at_max(self):
        """Regeneration doesn't exceed max_health."""
        from behavior_libraries.actor_lib.conditions import tick_conditions

        spore_mother = self.engine.game_state.actors.get('npc_spore_mother')
        spore_mother.properties['health'] = 145  # Near max
        spore_mother.properties['max_health'] = 150
        spore_mother.properties['regeneration'] = 10

        messages = tick_conditions(spore_mother)

        # Should cap at max_health
        self.assertEqual(spore_mother.properties['health'], 150)

    def test_health_regeneration_no_message_when_full(self):
        """No regeneration message when already at full health."""
        from behavior_libraries.actor_lib.conditions import tick_conditions

        spore_mother = self.engine.game_state.actors.get('npc_spore_mother')
        spore_mother.properties['health'] = 150
        spore_mother.properties['max_health'] = 150
        spore_mother.properties['regeneration'] = 10

        messages = tick_conditions(spore_mother)

        # No message about regeneration
        self.assertNotIn('regenerates', ' '.join(messages))

    def test_aldric_infection_ticks(self):
        """Aldric's infection deals damage but also regenerates (net -2 HP)."""
        from behavior_libraries.actor_lib.conditions import tick_conditions

        aldric = self.engine.game_state.actors.get('npc_aldric')
        initial_health = aldric.properties.get('health', 100)

        messages = tick_conditions(aldric)

        # Net effect: -7 (infection) + 5 (default regen) = -2 HP
        new_health = aldric.properties.get('health')
        self.assertEqual(new_health, initial_health - 2)

        # Severity should have increased
        infection = aldric.properties['conditions']['fungal_infection']
        self.assertEqual(infection['severity'], 82)  # 80 + progression_rate(2)

        # Should have messages about both damage and regen
        self.assertTrue(any('damage' in m for m in messages))
        self.assertTrue(any('regenerates' in m for m in messages))

    def test_condition_with_duration_expires(self):
        """Conditions with duration are removed when duration reaches 0."""
        from behavior_libraries.actor_lib.conditions import apply_condition, tick_conditions

        player = self.engine.game_state.actors.get('player')

        # Apply temporary condition
        apply_condition(player, 'test_condition', {
            'severity': 50,
            'duration': 2,
            'damage_per_turn': 5
        })

        # Tick once - duration goes to 1
        messages = tick_conditions(player)
        self.assertIn('test_condition', player.properties['conditions'])

        # Tick again - duration goes to 0, removed
        messages = tick_conditions(player)
        self.assertNotIn('test_condition', player.properties['conditions'])
        self.assertTrue(any('worn off' in m for m in messages))

    def test_multiple_conditions_all_tick(self):
        """Multiple conditions on same actor all tick."""
        from behavior_libraries.actor_lib.conditions import apply_condition, tick_conditions

        player = self.engine.game_state.actors.get('player')
        player.properties['health'] = 100

        # Apply two conditions
        apply_condition(player, 'poison', {
            'severity': 30,
            'damage_per_turn': 3
        })
        apply_condition(player, 'bleeding', {
            'severity': 20,
            'damage_per_turn': 2
        })

        messages = tick_conditions(player)

        # Net effect: -3 (poison) -2 (bleeding) +5 (default regen) = 0
        self.assertEqual(player.properties['health'], 100)
        self.assertTrue(any('poison' in m for m in messages))
        self.assertTrue(any('bleeding' in m for m in messages))
        self.assertTrue(any('regenerates' in m for m in messages))


class TestRegionalBehaviorConditions(unittest.TestCase):
    """Test regional behaviors that use conditions."""

    def setUp(self):
        """Load big_game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.accessor = StateAccessor(
            self.engine.game_state,
            self.engine.behavior_manager
        )

    def test_fungal_infection_uses_dict_format(self):
        """spore_zones.py uses dict format for conditions."""
        from behaviors.regions.fungal_depths import spore_zones
        from behavior_libraries.actor_lib.conditions import get_condition

        # Get player
        player = self.engine.game_state.actors.get('player')
        player.location = LocationId('spore_heart')
        player.properties['conditions'] = {}  # Start clean

        # Find spore heart location
        spore_heart = None
        for loc in self.engine.game_state.locations:
            if loc.id == 'spore_heart':
                spore_heart = loc
                break

        self.assertIsNotNone(spore_heart)
        spore_heart.properties['spore_level'] = 'medium'

        # Call handler
        result = spore_zones.on_spore_zone_turn(None, self.accessor, {})

        # Check conditions use dict format
        conditions = player.properties.get('conditions', {})
        self.assertIsInstance(conditions, dict)
        self.assertIn('fungal_infection', conditions)

        # Check infection data structure
        infection = conditions['fungal_infection']
        self.assertIsInstance(infection, dict)
        self.assertIn('severity', infection)
        self.assertNotIn('type', infection)  # Old list format had 'type' field

    def test_hypothermia_uses_dict_format(self):
        """hypothermia.py uses dict format for conditions."""
        from behaviors.regions.frozen_reaches import hypothermia

        player = self.engine.game_state.actors.get('player')
        player.location = LocationId('frozen_pass')
        player.properties['conditions'] = {}

        # Find frozen pass
        frozen_pass = None
        for loc in self.engine.game_state.locations:
            if loc.id == 'frozen_pass':
                frozen_pass = loc
                break

        self.assertIsNotNone(frozen_pass)
        frozen_pass.properties['temperature'] = 'cold'

        # Call handler
        result = hypothermia.on_cold_zone_turn(None, self.accessor, {})

        # Check dict format
        conditions = player.properties.get('conditions', {})
        self.assertIsInstance(conditions, dict)
        self.assertIn('hypothermia', conditions)

        hypo = conditions['hypothermia']
        self.assertIsInstance(hypo, dict)
        self.assertNotIn('type', hypo)


if __name__ == '__main__':
    unittest.main(verbosity=2)
