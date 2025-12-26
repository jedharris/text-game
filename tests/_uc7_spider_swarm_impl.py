"""Implementation of UC7: Spider Swarm scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_uc7_spider_swarm.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.

UC7 Tests:
- TestUC7SpiderPack: Spider pack configuration
- TestUC7VenomAttack: Venomous spider attacks
- TestUC7WebBurning: Torch burns webs
- TestUC7AlertPropagation: Alerting spider pack
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


class TestUC7SpiderPack(unittest.TestCase):
    """Test spider pack configuration."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.queen = self.engine.game_state.get_actor(ActorId('npc_spider_queen'))
        self.worker1 = self.engine.game_state.get_actor(ActorId('npc_spider_worker_1'))
        self.worker2 = self.engine.game_state.get_actor(ActorId('npc_spider_worker_2'))

    def test_spiders_exist(self):
        """All spider pack members exist."""
        self.assertIsNotNone(self.queen)
        self.assertIsNotNone(self.worker1)
        self.assertIsNotNone(self.worker2)

    def test_queen_is_alpha(self):
        """Spider queen has alpha role."""
        self.assertEqual(self.queen.properties.get('pack_role'), 'alpha')

    def test_workers_are_followers(self):
        """Spider workers have follower role."""
        self.assertEqual(self.worker1.properties.get('pack_role'), 'follower')
        self.assertEqual(self.worker2.properties.get('pack_role'), 'follower')

    def test_all_same_pack(self):
        """All spiders share same pack_id."""
        pack_id = self.queen.properties.get('pack_id')
        self.assertEqual(pack_id, 'spider_swarm')
        self.assertEqual(self.worker1.properties.get('pack_id'), pack_id)
        self.assertEqual(self.worker2.properties.get('pack_id'), pack_id)

    def test_spiders_in_gallery(self):
        """Spiders are in spider gallery."""
        self.assertEqual(self.queen.location, 'loc_spider_gallery')
        self.assertEqual(self.worker1.location, 'loc_spider_gallery')

    def test_is_spider_pack_member(self):
        """is_spider_pack_member correctly identifies members."""
        from behaviors.uc7_spiders import is_spider_pack_member

        self.assertTrue(is_spider_pack_member(self.queen))
        self.assertTrue(is_spider_pack_member(self.worker1))

        # Player is not a spider
        player = self.engine.game_state.get_actor(ActorId('player'))
        self.assertFalse(is_spider_pack_member(player))


class TestUC7VenomAttack(unittest.TestCase):
    """Test venomous spider attacks."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.queen = self.engine.game_state.get_actor(ActorId('npc_spider_queen'))
        # Move player to gallery
        self.player.location = 'loc_spider_gallery'

    def test_queen_has_venomous_attack(self):
        """Spider queen has venomous_bite attack."""
        from behavior_libraries.actor_lib.combat import get_attacks

        attacks = get_attacks(self.queen)
        venom_attacks = [a for a in attacks if a.get('applies_condition')]

        self.assertEqual(len(venom_attacks), 1)
        self.assertEqual(venom_attacks[0]['name'], 'venomous_bite')

    def test_venom_attack_applies_condition(self):
        """Venomous attack defines spider_venom condition."""
        from behavior_libraries.actor_lib.combat import get_attacks

        attacks = get_attacks(self.queen)
        venom_attack = [a for a in attacks if a.get('applies_condition')][0]

        applies = venom_attack['applies_condition']
        self.assertEqual(applies['name'], 'spider_venom')
        self.assertGreater(applies['severity'], 0)

    def test_execute_venom_attack(self):
        """Executing venom attack applies condition."""
        from behavior_libraries.actor_lib.combat import get_attacks, execute_attack
        from behavior_libraries.actor_lib.conditions import has_condition

        accessor = _create_accessor(self.engine)

        attacks = get_attacks(self.queen)
        venom_attack = [a for a in attacks if a.get('applies_condition')][0]

        # Player shouldn't have venom initially
        self.assertFalse(has_condition(self.player, 'spider_venom'))

        # Execute attack
        result = execute_attack(accessor, self.queen, self.player, venom_attack)

        self.assertTrue(result.success)
        self.assertIn('spider_venom', result.conditions_applied)
        self.assertTrue(has_condition(self.player, 'spider_venom'))


class TestUC7WebBurning(unittest.TestCase):
    """Test web burning mechanics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.torch = None
        for item in self.engine.game_state.items:
            if item.id == 'item_torch':
                self.torch = item
                break
        # Move player to gallery
        self.player.location = 'loc_spider_gallery'

    def test_torch_exists(self):
        """Torch item exists."""
        self.assertIsNotNone(self.torch)

    def test_torch_burns_webs(self):
        """Torch has burns_webs property."""
        self.assertTrue(self.torch.properties.get('burns_webs'))

    def test_gallery_has_web_density(self):
        """Gallery parts have web_density."""
        from behaviors.uc7_spiders import get_web_density

        accessor = _create_accessor(self.engine)

        entrance_density = get_web_density(accessor, 'part_gallery_entrance')
        nest_density = get_web_density(accessor, 'part_gallery_nest')

        self.assertEqual(entrance_density, 20)
        self.assertEqual(nest_density, 80)

    def test_reduce_web_density(self):
        """reduce_web_density lowers web amount."""
        from behaviors.uc7_spiders import get_web_density, reduce_web_density

        accessor = _create_accessor(self.engine)

        initial = get_web_density(accessor, 'part_gallery_nest')
        msg = reduce_web_density(accessor, 'part_gallery_nest', 30)
        after = get_web_density(accessor, 'part_gallery_nest')

        self.assertEqual(after, initial - 30)
        self.assertIn('burn', msg.lower())

    def test_burn_webs_with_torch(self):
        """burn_webs_with_torch reduces density."""
        from behaviors.uc7_spiders import get_web_density, burn_webs_with_torch

        accessor = _create_accessor(self.engine)

        initial = get_web_density(accessor, 'part_gallery_entrance')
        msg = burn_webs_with_torch(accessor, self.torch, 'part_gallery_entrance')
        after = get_web_density(accessor, 'part_gallery_entrance')

        burn_amount = self.torch.properties.get('web_burn_amount', 20)
        self.assertEqual(after, max(0, initial - burn_amount))

    def test_cleared_webs_message(self):
        """Clearing all webs gives appropriate message."""
        from behaviors.uc7_spiders import reduce_web_density, get_web_density

        accessor = _create_accessor(self.engine)

        # Reduce entrance webs to 0 (they only have 20)
        reduce_web_density(accessor, 'part_gallery_entrance', 100)
        density = get_web_density(accessor, 'part_gallery_entrance')

        self.assertEqual(density, 0)


class TestUC7AlertPropagation(unittest.TestCase):
    """Test alert propagation through spider pack."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.get_actor(ActorId('player'))
        self.queen = self.engine.game_state.get_actor(ActorId('npc_spider_queen'))
        self.worker1 = self.engine.game_state.get_actor(ActorId('npc_spider_worker_1'))
        self.worker2 = self.engine.game_state.get_actor(ActorId('npc_spider_worker_2'))

    def test_spiders_not_alerted_initially(self):
        """Spiders start not alerted."""
        from behaviors.uc7_spiders import is_alerted

        self.assertFalse(is_alerted(self.queen))
        self.assertFalse(is_alerted(self.worker1))

    def test_alert_single_spider(self):
        """alert_spider sets alerted flag."""
        from behaviors.uc7_spiders import alert_spider, is_alerted

        msg = alert_spider(self.queen)

        self.assertTrue(is_alerted(self.queen))
        self.assertIn('alert', msg.lower())

    def test_alert_swarm(self):
        """alert_swarm alerts all spiders."""
        from behaviors.uc7_spiders import alert_swarm, is_alerted

        accessor = _create_accessor(self.engine)
        messages = alert_swarm(accessor)

        self.assertTrue(is_alerted(self.queen))
        self.assertTrue(is_alerted(self.worker1))
        self.assertTrue(is_alerted(self.worker2))
        self.assertEqual(len(messages), 3)

    def test_alert_swarm_no_double_alert(self):
        """alert_swarm doesn't re-alert already alerted spiders."""
        from behaviors.uc7_spiders import alert_swarm, alert_spider

        accessor = _create_accessor(self.engine)

        # Alert queen first
        alert_spider(self.queen)

        # Alert swarm - queen should not be re-alerted
        messages = alert_swarm(accessor)

        # Only workers should get new alerts
        self.assertEqual(len(messages), 2)

    def test_web_attack_bonus(self):
        """Spiders get attack bonus in heavy webs."""
        from behaviors.uc7_spiders import get_web_attack_bonus

        accessor = _create_accessor(self.engine)

        # Light webs - no bonus
        entrance_bonus = get_web_attack_bonus(accessor, 'part_gallery_entrance')
        self.assertEqual(entrance_bonus, 0)

        # Heavy webs - bonus
        nest_bonus = get_web_attack_bonus(accessor, 'part_gallery_nest')
        self.assertEqual(nest_bonus, 10)


if __name__ == '__main__':
    unittest.main(verbosity=2)
