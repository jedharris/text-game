"""Implementation of UC3: Hungry Wolf Pack scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_uc3_wolf_pack.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.

UC3 Tests:
- TestUC3PackSync: Followers copy alpha disposition
- TestUC3Feeding: Giving food pacifies wolves
- TestUC3MoraleFlee: Damaged wolves flee when morale low
- TestUC3Relationship: Repeated feeding builds gratitude
- TestUC3Domestication: High gratitude makes wolves friendly
"""
from src.types import ActorId

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


class TestUC3PackSync(unittest.TestCase):
    """Test pack followers sync with alpha disposition."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.alpha = self.engine.game_state.get_actor(ActorId('npc_alpha_wolf'))
        self.wolf1 = self.engine.game_state.get_actor(ActorId('npc_wolf_1'))
        self.wolf2 = self.engine.game_state.get_actor(ActorId('npc_wolf_2'))

    def test_pack_members_exist(self):
        """All pack members are loaded."""
        self.assertIsNotNone(self.alpha)
        self.assertIsNotNone(self.wolf1)
        self.assertIsNotNone(self.wolf2)

    def test_alpha_has_correct_role(self):
        """Alpha wolf has pack_role=alpha."""
        self.assertEqual(self.alpha.properties.get('pack_role'), 'alpha')

    def test_followers_have_correct_role(self):
        """Follower wolves have pack_role=follower."""
        self.assertEqual(self.wolf1.properties.get('pack_role'), 'follower')
        self.assertEqual(self.wolf2.properties.get('pack_role'), 'follower')

    def test_all_same_pack(self):
        """All wolves share the same pack_id."""
        pack_id = self.alpha.properties.get('pack_id')
        self.assertEqual(self.wolf1.properties.get('pack_id'), pack_id)
        self.assertEqual(self.wolf2.properties.get('pack_id'), pack_id)

    def test_sync_pack_disposition(self):
        """Changing alpha disposition syncs to followers."""
        from behavior_libraries.actor_lib.packs import sync_pack_disposition

        accessor = _create_accessor(self.engine)

        # All start hostile
        self.assertEqual(self.alpha.properties.get('disposition'), 'hostile')
        self.assertEqual(self.wolf1.properties.get('disposition'), 'hostile')

        # Change alpha to neutral
        self.alpha.properties['disposition'] = 'neutral'

        # Sync pack
        changed = sync_pack_disposition(accessor, 'wolf_pack')

        # Followers should now be neutral
        self.assertEqual(self.wolf1.properties.get('disposition'), 'neutral')
        self.assertEqual(self.wolf2.properties.get('disposition'), 'neutral')
        self.assertEqual(len(changed), 2)

    def test_sync_single_follower(self):
        """Sync individual follower to alpha."""
        from behavior_libraries.actor_lib.packs import sync_follower_disposition

        accessor = _create_accessor(self.engine)

        # Change alpha disposition
        self.alpha.properties['disposition'] = 'friendly'

        # Sync just wolf1
        changed = sync_follower_disposition(accessor, self.wolf1)

        self.assertTrue(changed)
        self.assertEqual(self.wolf1.properties.get('disposition'), 'friendly')
        # wolf2 not synced yet
        self.assertEqual(self.wolf2.properties.get('disposition'), 'hostile')


class TestUC3Feeding(unittest.TestCase):
    """Test giving food pacifies wolves."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.alpha = self.engine.game_state.get_actor(ActorId('npc_alpha_wolf'))
        self.wolf1 = self.engine.game_state.get_actor(ActorId('npc_wolf_1'))
        self.venison = None
        for item in self.engine.game_state.items:
            if item.id == 'item_venison':
                self.venison = item
                break

    def test_venison_satisfies_hunger(self):
        """Venison item has satisfies: hunger property."""
        self.assertIsNotNone(self.venison)
        self.assertIn('hunger', self.venison.properties.get('satisfies', []))

    def test_wolves_need_hunger(self):
        """Wolves have hunger in their needs."""
        self.assertIn('hunger', self.alpha.properties.get('needs', []))
        self.assertIn('hunger', self.wolf1.properties.get('needs', []))

    def test_feeding_removes_need(self):
        """Feeding wolf removes hunger from needs."""
        from behaviors.uc3_wolf_pack import apply_feeding

        accessor = _create_accessor(self.engine)

        # Feed the alpha
        apply_feeding(accessor, self.venison, self.alpha)

        # Hunger should be removed
        self.assertNotIn('hunger', self.alpha.properties.get('needs', []))

    def test_feeding_alpha_changes_disposition(self):
        """Feeding alpha wolf changes disposition to neutral."""
        from behaviors.uc3_wolf_pack import apply_feeding

        accessor = _create_accessor(self.engine)

        self.assertEqual(self.alpha.properties.get('disposition'), 'hostile')

        apply_feeding(accessor, self.venison, self.alpha)

        self.assertEqual(self.alpha.properties.get('disposition'), 'neutral')

    def test_feeding_alpha_syncs_pack(self):
        """Feeding alpha syncs pack disposition."""
        from behaviors.uc3_wolf_pack import apply_feeding

        accessor = _create_accessor(self.engine)

        apply_feeding(accessor, self.venison, self.alpha)

        # All pack members should be neutral now
        self.assertEqual(self.alpha.properties.get('disposition'), 'neutral')
        self.assertEqual(self.wolf1.properties.get('disposition'), 'neutral')


class TestUC3MoraleFlee(unittest.TestCase):
    """Test damaged wolves flee when morale drops."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.alpha = self.engine.game_state.get_actor(ActorId('npc_alpha_wolf'))
        self.wolf1 = self.engine.game_state.get_actor(ActorId('npc_wolf_1'))
        # Move player to clearing
        self.player.location = 'loc_forest_clearing'

    def test_healthy_wolf_high_morale(self):
        """Healthy wolf with allies has high morale."""
        from behavior_libraries.actor_lib.morale import get_morale

        accessor = _create_accessor(self.engine)

        morale = get_morale(accessor, self.wolf1)
        # With allies and alpha present, morale should be high
        self.assertGreater(morale, 50)

    def test_damaged_wolf_low_morale(self):
        """Damaged wolf has lower morale."""
        from behavior_libraries.actor_lib.morale import get_morale

        accessor = _create_accessor(self.engine)

        # Damage the wolf significantly
        self.wolf1.properties['health'] = 10

        morale = get_morale(accessor, self.wolf1)
        # Morale based on health percentage should be lower
        self.assertLess(morale, 50)

    def test_flee_condition_triggered(self):
        """Low morale triggers flee condition when isolated."""
        from behavior_libraries.actor_lib.morale import check_flee_condition

        accessor = _create_accessor(self.engine)

        # Move wolf1 to wolf den alone (no ally bonuses)
        self.wolf1.location = 'loc_wolf_den'
        self.player.location = 'loc_wolf_den'

        # Damage wolf - now with no allies, morale is purely health-based
        # At 10hp/50max = 20% -> morale ~20, threshold is 30
        self.wolf1.properties['health'] = 10

        should_flee = check_flee_condition(accessor, self.wolf1)
        self.assertTrue(should_flee)

    def test_directed_flee(self):
        """Alpha flees to flee_destination when triggered."""
        from behaviors.uc3_wolf_pack import directed_flee

        accessor = _create_accessor(self.engine)

        # Damage alpha severely
        self.alpha.properties['health'] = 5

        # Alpha should flee to wolf_den
        self.assertEqual(self.alpha.location, 'loc_forest_clearing')

        message = directed_flee(accessor, self.alpha)

        self.assertIsNotNone(message)
        self.assertEqual(self.alpha.location, 'loc_wolf_den')


class TestUC3Relationship(unittest.TestCase):
    """Test repeated feeding builds gratitude relationship."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.alpha = self.engine.game_state.get_actor(ActorId('npc_alpha_wolf'))

    def test_no_initial_relationship(self):
        """Wolf starts with no relationship to player."""
        from behavior_libraries.actor_lib.relationships import get_relationship

        rel = get_relationship(self.alpha, 'player')
        self.assertEqual(rel, {})

    def test_feeding_builds_gratitude(self):
        """Feeding increases gratitude relationship."""
        from behavior_libraries.actor_lib.relationships import modify_relationship

        accessor = _create_accessor(self.engine)

        result = modify_relationship(accessor, self.alpha, 'player', 'gratitude', 1)

        self.assertEqual(result.old_value, 0)
        self.assertEqual(result.new_value, 1)

    def test_multiple_feedings_stack(self):
        """Multiple feedings increase gratitude cumulatively."""
        from behavior_libraries.actor_lib.relationships import modify_relationship, get_relationship

        accessor = _create_accessor(self.engine)

        modify_relationship(accessor, self.alpha, 'player', 'gratitude', 1)
        modify_relationship(accessor, self.alpha, 'player', 'gratitude', 1)
        modify_relationship(accessor, self.alpha, 'player', 'gratitude', 1)

        rel = get_relationship(self.alpha, 'player')
        self.assertEqual(rel.get('gratitude'), 3)


class TestUC3Domestication(unittest.TestCase):
    """Test high gratitude makes wolves friendly (domesticated)."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.alpha = self.engine.game_state.get_actor(ActorId('npc_alpha_wolf'))

    def test_domestication_threshold(self):
        """Gratitude >= 3 triggers domestication threshold."""
        from behavior_libraries.actor_lib.relationships import modify_relationship

        accessor = _create_accessor(self.engine)

        # First two don't cross threshold
        result1 = modify_relationship(accessor, self.alpha, 'player', 'gratitude', 1)
        self.assertIsNone(result1.threshold_crossed)

        result2 = modify_relationship(accessor, self.alpha, 'player', 'gratitude', 1)
        self.assertIsNone(result2.threshold_crossed)

        # Third one crosses threshold
        result3 = modify_relationship(accessor, self.alpha, 'player', 'gratitude', 1)
        self.assertEqual(result3.threshold_crossed, 'domestication')

    def test_check_domestication(self):
        """check_domestication returns true when threshold met."""
        from behaviors.uc3_wolf_pack import check_domestication
        from behavior_libraries.actor_lib.relationships import modify_relationship

        accessor = _create_accessor(self.engine)

        # Not domesticated initially
        self.assertFalse(check_domestication(self.alpha))

        # Build gratitude to 3
        modify_relationship(accessor, self.alpha, 'player', 'gratitude', 3)

        # Now domesticated
        self.assertTrue(check_domestication(self.alpha))

    def test_feeding_to_domestication(self):
        """Repeated feeding through apply_feeding leads to domestication."""
        from behaviors.uc3_wolf_pack import apply_feeding, check_domestication

        accessor = _create_accessor(self.engine)

        # Create multiple food items for testing
        venison = None
        for item in self.engine.game_state.items:
            if item.id == 'item_venison':
                venison = item
                break

        # Feed 3 times (need to restore hunger each time for test)
        for i in range(3):
            self.alpha.properties['needs'] = ['hunger']
            apply_feeding(accessor, venison, self.alpha)

        # Should be domesticated now
        self.assertTrue(check_domestication(self.alpha))
        self.assertEqual(self.alpha.properties.get('disposition'), 'friendly')


if __name__ == '__main__':
    unittest.main(verbosity=2)
