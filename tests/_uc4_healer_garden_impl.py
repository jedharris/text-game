"""Implementation of UC4: Healer and Garden scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_uc4_healer_garden.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.

UC4 Tests:
- TestUC4ToxicPlant: Touching toxic plant applies poison
- TestUC4Knowledge: Knowledge gates plant descriptions
- TestUC4CureService: Healer cures for payment
- TestUC4TeachService: Healer teaches herbalism
- TestUC4TrustDiscount: Trust reduces service cost
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


class TestUC4ToxicPlant(unittest.TestCase):
    """Test toxic plant mechanics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors[ActorId('player')]
        self.nightshade = None
        for item in self.engine.game_state.items:
            if item.id == 'item_nightshade':
                self.nightshade = item
                break
        # Move player to garden
        self.player.location = 'loc_garden'

    def test_nightshade_exists(self):
        """Nightshade item exists."""
        self.assertIsNotNone(self.nightshade)

    def test_nightshade_is_toxic(self):
        """Nightshade has toxic_to_touch property."""
        self.assertTrue(self.nightshade.properties.get('toxic_to_touch'))

    def test_check_toxic_touch(self):
        """check_toxic_touch identifies toxic items."""
        from behaviors.uc4_healer import check_toxic_touch

        self.assertTrue(check_toxic_touch(self.nightshade, self.player))

    def test_apply_toxic_effect(self):
        """apply_toxic_effect applies contact poison."""
        from behaviors.uc4_healer import apply_toxic_effect
        from behavior_libraries.actor_lib.conditions import has_condition

        # Player shouldn't have poison initially
        self.assertFalse(has_condition(self.player, 'contact_poison'))

        # Touch the nightshade
        message = apply_toxic_effect(self.nightshade, self.player)

        self.assertIsNotNone(message)
        self.assertIn('toxic', message.lower())
        # Player should now have contact poison
        self.assertTrue(has_condition(self.player, 'contact_poison'))

    def test_on_take_toxic_handler(self):
        """on_take_toxic event handler applies effect."""
        from behaviors.uc4_healer import on_take_toxic
        from behavior_libraries.actor_lib.conditions import has_condition

        accessor = _create_accessor(self.engine)
        context = {'item_id': 'item_nightshade'}

        result = on_take_toxic(self.player, accessor, context)

        self.assertIsNotNone(result)
        self.assertTrue(result.allow)  # Still allows taking
        self.assertIn('toxic', result.message.lower())
        self.assertTrue(has_condition(self.player, 'contact_poison'))


class TestUC4Knowledge(unittest.TestCase):
    """Test knowledge gating for descriptions."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors[ActorId('player')]
        self.nightshade = None
        self.healing_herb = None
        for item in self.engine.game_state.items:
            if item.id == 'item_nightshade':
                self.nightshade = item
            elif item.id == 'item_healing_herb':
                self.healing_herb = item

    def test_no_herbalism_knowledge_initially(self):
        """Player doesn't know herbalism initially."""
        from behaviors.uc4_healer import has_knowledge

        self.assertFalse(has_knowledge(self.player, 'herbalism'))

    def test_default_description_without_knowledge(self):
        """Without herbalism, get basic description."""
        from behaviors.uc4_healer import get_knowledge_description

        desc = get_knowledge_description(self.nightshade, self.player)

        # Should be the basic description
        self.assertIn('dark purple', desc.lower())
        self.assertNotIn('deadly', desc.lower())  # That's in the herbalism desc

    def test_enhanced_description_with_knowledge(self):
        """With herbalism, get enhanced description."""
        from behaviors.uc4_healer import get_knowledge_description, grant_knowledge

        # Grant herbalism knowledge
        grant_knowledge(self.player, 'herbalism')

        desc = get_knowledge_description(self.nightshade, self.player)

        # Should be the herbalism description
        self.assertIn('deadly', desc.lower())
        self.assertIn('gloves', desc.lower())

    def test_grant_knowledge(self):
        """grant_knowledge adds to knows array."""
        from behaviors.uc4_healer import grant_knowledge, has_knowledge

        self.assertFalse(has_knowledge(self.player, 'herbalism'))

        message = grant_knowledge(self.player, 'herbalism')

        self.assertIn('learned', message.lower())
        self.assertTrue(has_knowledge(self.player, 'herbalism'))

    def test_grant_duplicate_knowledge(self):
        """Granting duplicate knowledge reports already known."""
        from behaviors.uc4_healer import grant_knowledge

        grant_knowledge(self.player, 'herbalism')
        message = grant_knowledge(self.player, 'herbalism')

        self.assertIn('already', message.lower())


class TestUC4CureService(unittest.TestCase):
    """Test healer cure service."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors[ActorId('player')]
        self.healer = self.engine.game_state.actors[ActorId('npc_healer')]
        self.gold = None
        for item in self.engine.game_state.items:
            if item.id == 'item_gold_coins':
                self.gold = item
                break
        # Move player to healer's hut and give gold
        self.player.location = 'loc_healer_hut'
        if self.gold and self.gold.id not in self.player.inventory:
            self.player.inventory.append(self.gold.id)

    def test_healer_has_cure_service(self):
        """Healer offers cure service."""
        from behavior_libraries.actor_lib.services import get_available_services

        services = get_available_services(self.healer)
        self.assertIn('cure', services)

    def test_cure_service_cost(self):
        """Cure service costs 5 gold."""
        from behavior_libraries.actor_lib.services import get_service_cost

        cost = get_service_cost(self.healer, 'cure', self.player)
        self.assertEqual(cost, 5)

    def test_execute_cure_service(self):
        """Execute cure removes conditions."""
        from behavior_libraries.actor_lib.services import execute_service
        from behavior_libraries.actor_lib.conditions import apply_condition, has_condition

        # Give player a condition
        apply_condition(self.player, 'contact_poison', {'severity': 50})
        self.assertTrue(has_condition(self.player, 'contact_poison'))

        # Execute cure service
        result = execute_service(
            _create_accessor(self.engine),
            self.player,
            self.healer,
            'cure',
            self.gold
        )

        self.assertTrue(result.success)
        self.assertFalse(has_condition(self.player, 'contact_poison'))


class TestUC4TeachService(unittest.TestCase):
    """Test healer teach service."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors[ActorId('player')]
        self.healer = self.engine.game_state.actors[ActorId('npc_healer')]
        self.gold = None
        for item in self.engine.game_state.items:
            if item.id == 'item_gold_coins':
                self.gold = item
                break
        # Move player to healer's hut and give gold
        self.player.location = 'loc_healer_hut'
        if self.gold and self.gold.id not in self.player.inventory:
            self.player.inventory.append(self.gold.id)

    def test_healer_has_teach_service(self):
        """Healer offers teach_herbalism service."""
        from behavior_libraries.actor_lib.services import get_available_services

        services = get_available_services(self.healer)
        self.assertIn('teach_herbalism', services)

    def test_teach_service_cost(self):
        """Teach service costs 8 gold."""
        from behavior_libraries.actor_lib.services import get_service_cost

        cost = get_service_cost(self.healer, 'teach_herbalism', self.player)
        self.assertEqual(cost, 8)

    def test_execute_teach_service(self):
        """Execute teach grants herbalism knowledge."""
        from behavior_libraries.actor_lib.services import execute_service
        from behaviors.uc4_healer import has_knowledge

        # Player shouldn't know herbalism
        self.assertFalse(has_knowledge(self.player, 'herbalism'))

        # Execute teach service
        result = execute_service(
            _create_accessor(self.engine),
            self.player,
            self.healer,
            'teach_herbalism',
            self.gold
        )

        self.assertTrue(result.success)
        self.assertIn('learned', result.message.lower())
        self.assertTrue(has_knowledge(self.player, 'herbalism'))


class TestUC4TrustDiscount(unittest.TestCase):
    """Test trust-based service discounts."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors[ActorId('player')]
        self.healer = self.engine.game_state.actors[ActorId('npc_healer')]

    def test_no_discount_without_trust(self):
        """No discount when trust is 0."""
        from behavior_libraries.actor_lib.services import get_service_cost

        cost = get_service_cost(self.healer, 'cure', self.player)
        self.assertEqual(cost, 5)  # Base cost

    def test_discount_with_high_trust(self):
        """50% discount when trust >= 3."""
        from behavior_libraries.actor_lib.services import get_service_cost

        # Set trust to 3
        self.healer.properties.setdefault('relationships', {})
        self.healer.properties['relationships'][self.player.id] = {'trust': 3}

        cost = get_service_cost(self.healer, 'cure', self.player)
        self.assertEqual(cost, 2)  # 50% of 5 = 2.5, rounded down

    def test_trust_builds_with_transactions(self):
        """Trust increases after service transaction."""
        from behavior_libraries.actor_lib.services import execute_service

        accessor = _create_accessor(self.engine)

        # Get gold for player
        gold = None
        for item in self.engine.game_state.items:
            if item.id == 'item_gold_coins':
                gold = item
                break
        self.player.inventory.append(gold.id)

        # Initial trust should be 0
        rel = self.healer.properties.get('relationships', {}).get(self.player.id, {})
        initial_trust = rel.get('trust', 0)

        # Execute a service
        execute_service(accessor, self.player, self.healer, 'heal', gold)

        # Trust should have increased
        rel = self.healer.properties.get('relationships', {}).get(self.player.id, {})
        new_trust = rel.get('trust', 0)
        self.assertEqual(new_trust, initial_trust + 1)

    def test_get_service_with_discount_info(self):
        """get_service_with_discount returns discount info."""
        from behaviors.uc4_healer import get_service_with_discount

        # Without trust
        info = get_service_with_discount(self.healer, 'cure', self.player)
        self.assertEqual(info['base_cost'], 5)
        self.assertEqual(info['effective_cost'], 5)
        self.assertFalse(info['has_discount'])

        # With trust
        self.healer.properties.setdefault('relationships', {})
        self.healer.properties['relationships'][self.player.id] = {'trust': 3}

        info = get_service_with_discount(self.healer, 'cure', self.player)
        self.assertEqual(info['base_cost'], 5)
        self.assertEqual(info['effective_cost'], 2)
        self.assertTrue(info['has_discount'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
