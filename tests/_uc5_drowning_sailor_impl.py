"""Implementation of UC5: Drowning Sailor scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_uc5_drowning_sailor.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.

UC5 Tests:
- TestUC5Breath: Breath decreases in non-breathable areas
- TestUC5Drowning: Actor takes damage when breath depleted
- TestUC5BreathingItem: Air bladder prevents breath loss
- TestUC5Rescue: Bringing sailor to surface restores breath
- TestUC5ConstructImmune: Constructs don't need to breathe
"""
from src.types import ActorId

import sys
import unittest
from pathlib import Path


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


def _get_part(engine, part_id):
    """Get a part by ID."""
    for part in engine.game_state.parts:
        if part.id == part_id:
            return part
    return None


class TestUC5Breath(unittest.TestCase):
    """Test breath decreases in non-breathable areas."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.sailor = self.engine.game_state.get_actor(ActorId('npc_sailor'))

    def test_sailor_starts_with_low_breath(self):
        """Sailor starts with low breath (20 of 60)."""
        self.assertEqual(self.sailor.properties.get('breath'), 20)
        self.assertEqual(self.sailor.properties.get('max_breath'), 60)

    def test_underwater_parts_not_breathable(self):
        """Underwater cave parts are not breathable."""
        shallow = _get_part(self.engine, 'part_underwater_shallow')
        deep = _get_part(self.engine, 'part_underwater_deep')

        self.assertFalse(shallow.properties.get('breathable', True))
        self.assertFalse(deep.properties.get('breathable', True))

    def test_breath_decreases_underwater(self):
        """Breath decreases when in non-breathable area."""
        from behavior_libraries.actor_lib.environment import check_breath

        shallow = _get_part(self.engine, 'part_underwater_shallow')
        accessor = _create_accessor(self.engine)

        # Set player breath
        self.player.properties['breath'] = 60
        self.player.properties['max_breath'] = 60
        self.player.location = 'loc_underwater_cave'

        # Check breath (decreases by 10)
        check_breath(self.player, shallow, accessor)

        self.assertEqual(self.player.properties['breath'], 50)

    def test_breath_restores_on_surface(self):
        """Breath restores to max in breathable area."""
        from behavior_libraries.actor_lib.environment import check_breath

        # Use a breathable part (basement entrance has breathable=true)
        part = _get_part(self.engine, 'part_basement_entrance')
        accessor = _create_accessor(self.engine)

        # Start with low breath
        self.player.properties['breath'] = 20
        self.player.properties['max_breath'] = 60

        # Check breath in breathable area
        check_breath(self.player, part, accessor)

        self.assertEqual(self.player.properties['breath'], 60)


class TestUC5Drowning(unittest.TestCase):
    """Test actor takes damage when breath depleted."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))

    def test_drowning_damage(self):
        """Actor takes drowning damage when breath reaches 0."""
        from behavior_libraries.actor_lib.environment import check_breath

        shallow = _get_part(self.engine, 'part_underwater_shallow')
        accessor = _create_accessor(self.engine)

        # Set player at critically low breath
        self.player.properties['health'] = 100
        self.player.properties['breath'] = 5
        self.player.properties['max_breath'] = 60
        self.player.location = 'loc_underwater_cave'

        # Check breath (will go to -5 and trigger drowning)
        msg = check_breath(self.player, shallow, accessor)

        # Should take drowning damage
        self.assertLess(self.player.properties['health'], 100)
        self.assertIn('drowning', msg.lower())

    def test_continuous_drowning(self):
        """Actor continues taking damage each turn while at 0 breath."""
        from behavior_libraries.actor_lib.environment import check_breath

        shallow = _get_part(self.engine, 'part_underwater_shallow')
        accessor = _create_accessor(self.engine)

        self.player.properties['health'] = 100
        self.player.properties['breath'] = 0
        self.player.properties['max_breath'] = 60
        self.player.location = 'loc_underwater_cave'

        # First drowning tick
        check_breath(self.player, shallow, accessor)
        health_after_1 = self.player.properties['health']

        # Second drowning tick
        check_breath(self.player, shallow, accessor)
        health_after_2 = self.player.properties['health']

        self.assertLess(health_after_2, health_after_1)


class TestUC5BreathingItem(unittest.TestCase):
    """Test air bladder prevents breath loss."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.air_bladder = None
        for item in self.engine.game_state.items:
            if item.id == 'item_air_bladder':
                self.air_bladder = item
                break

    def test_air_bladder_exists(self):
        """Air bladder item exists with provides_breathing property."""
        self.assertIsNotNone(self.air_bladder)
        self.assertTrue(self.air_bladder.properties.get('provides_breathing'))

    def test_breathing_item_works_in_shallow(self):
        """Air bladder prevents breath loss in shallow water."""
        from behavior_libraries.actor_lib.environment import check_breath

        shallow = _get_part(self.engine, 'part_underwater_shallow')
        accessor = _create_accessor(self.engine)

        # Give player the air bladder
        self.player.inventory.append('item_air_bladder')
        self.player.properties['breath'] = 60
        self.player.properties['max_breath'] = 60
        self.player.location = 'loc_underwater_cave'

        # Check breath - should not decrease due to breathing item
        check_breath(self.player, shallow, accessor)

        self.assertEqual(self.player.properties['breath'], 60)

    def test_breathing_item_fails_in_deep(self):
        """Air bladder doesn't work in deep water (breathing_item_works=false)."""
        from behavior_libraries.actor_lib.environment import check_breath

        deep = _get_part(self.engine, 'part_underwater_deep')
        accessor = _create_accessor(self.engine)

        # Deep water has breathing_item_works=false
        self.assertFalse(deep.properties.get('breathing_item_works', True))

        # Give player the air bladder
        self.player.inventory.append('item_air_bladder')
        self.player.properties['breath'] = 60
        self.player.properties['max_breath'] = 60
        self.player.location = 'loc_underwater_cave'

        # Check breath - should decrease despite breathing item
        check_breath(self.player, deep, accessor)

        self.assertEqual(self.player.properties['breath'], 50)


class TestUC5Rescue(unittest.TestCase):
    """Test bringing sailor to surface restores breath."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.sailor = self.engine.game_state.get_actor(ActorId('npc_sailor'))

    def test_rescue_moves_to_surface(self):
        """Rescue moves actor to specified location."""
        from behaviors.uc5_underwater import rescue_to_surface

        accessor = _create_accessor(self.engine)

        self.assertEqual(self.sailor.location, 'loc_underwater_cave')

        rescue_to_surface(accessor, self.sailor, 'loc_dock')

        self.assertEqual(self.sailor.location, 'loc_dock')

    def test_rescue_restores_breath(self):
        """Rescue restores breath to maximum."""
        from behaviors.uc5_underwater import rescue_to_surface

        accessor = _create_accessor(self.engine)

        # Sailor starts with low breath
        self.assertEqual(self.sailor.properties.get('breath'), 20)

        rescue_to_surface(accessor, self.sailor, 'loc_dock')

        # Breath should be restored to max
        self.assertEqual(
            self.sailor.properties.get('breath'),
            self.sailor.properties.get('max_breath')
        )

    def test_breath_warning_messages(self):
        """Custom breath warnings based on level."""
        from behaviors.uc5_underwater import get_breath_warning

        # Set up sailor with different breath levels
        self.sailor.properties['max_breath'] = 100

        # Fine (60%)
        self.sailor.properties['breath'] = 60
        self.assertIsNone(get_breath_warning(self.sailor))

        # Low (40%)
        self.sailor.properties['breath'] = 40
        warning = get_breath_warning(self.sailor)
        self.assertIn('low', warning.lower())

        # Gasping (25%)
        self.sailor.properties['breath'] = 25
        warning = get_breath_warning(self.sailor)
        self.assertIn('gasping', warning.lower())

        # Critical (5%)
        self.sailor.properties['breath'] = 5
        warning = get_breath_warning(self.sailor)
        self.assertIn('drown', warning.lower())


class TestUC5ConstructImmune(unittest.TestCase):
    """Test constructs don't need to breathe."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.golem = self.engine.game_state.get_actor(ActorId('npc_diving_golem'))

    def test_golem_is_construct(self):
        """Diving golem has construct body form."""
        body = self.golem.properties.get('body', {})
        self.assertEqual(body.get('form'), 'construct')

    def test_construct_does_not_need_breath(self):
        """Constructs are flagged as not needing breath."""
        from behavior_libraries.actor_lib.environment import needs_breath

        self.assertFalse(needs_breath(self.golem))

    def test_construct_unaffected_by_water(self):
        """Constructs don't lose breath underwater."""
        from behavior_libraries.actor_lib.environment import check_breath
        from src.state_accessor import IGNORE_EVENT

        shallow = _get_part(self.engine, 'part_underwater_shallow')
        accessor = _create_accessor(self.engine)

        # Golem should not have breath tracking at all
        # check_breath should return IGNORE_EVENT for constructs

        msg = check_breath(self.golem, shallow, accessor)

        self.assertEqual(msg, IGNORE_EVENT)

    def test_construct_immune_to_drowning(self):
        """Constructs cannot drown even with 0 breath."""
        from behavior_libraries.actor_lib.environment import check_breath

        shallow = _get_part(self.engine, 'part_underwater_shallow')
        accessor = _create_accessor(self.engine)

        # Even if we artificially set breath to 0
        self.golem.properties['breath'] = 0
        self.golem.properties['health'] = 150

        # Check breath should not damage construct
        check_breath(self.golem, shallow, accessor)

        self.assertEqual(self.golem.properties['health'], 150)


if __name__ == '__main__':
    unittest.main(verbosity=2)
