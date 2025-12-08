"""Implementation of UC6: Injured Merchant scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_uc6_injured_merchant.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.

UC6 Tests:
- TestUC6Treatment: Bandages treat bleeding
- TestUC6Trading: Merchant trades while injured
- TestUC6Escort: Guiding merchant to town
- TestUC6Reward: Reward on successful escort
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


class TestUC6Treatment(unittest.TestCase):
    """Test treatment mechanics with bandages."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors['player']
        self.merchant = self.engine.game_state.actors['npc_merchant']
        self.bandages = None
        for item in self.engine.game_state.items:
            if item.id == 'item_bandages':
                self.bandages = item
                break
        # Move player to forest road
        self.player.location = 'loc_forest_road'

    def test_merchant_has_bleeding(self):
        """Merchant has bleeding condition."""
        from behaviors.actors.conditions import has_condition

        self.assertTrue(has_condition(self.merchant, 'bleeding'))

    def test_bandages_exist(self):
        """Bandages item exists."""
        self.assertIsNotNone(self.bandages)

    def test_bandages_treat_bleeding(self):
        """Bandages have treats property for bleeding."""
        from behaviors.actors.treatment import can_treat

        self.assertTrue(can_treat(self.bandages, 'bleeding'))

    def test_apply_treatment(self):
        """Applying bandages removes bleeding."""
        from behaviors.actors.treatment import apply_treatment
        from behaviors.actors.conditions import has_condition

        accessor = _create_accessor(self.engine)

        self.assertTrue(has_condition(self.merchant, 'bleeding'))

        result = apply_treatment(accessor, self.bandages, self.merchant)

        self.assertTrue(result.success)
        self.assertIn('bleeding', result.conditions_treated)
        self.assertFalse(has_condition(self.merchant, 'bleeding'))

    def test_treatment_consumes_bandages(self):
        """Using bandages consumes them."""
        from behaviors.actors.treatment import apply_treatment

        accessor = _create_accessor(self.engine)

        # Give bandages to player
        self.player.inventory.append(self.bandages.id)

        result = apply_treatment(accessor, self.bandages, self.merchant)

        self.assertTrue(result.item_consumed)
        self.assertNotIn(self.bandages.id, self.player.inventory)


class TestUC6Trading(unittest.TestCase):
    """Test merchant trading while injured."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors['player']
        self.merchant = self.engine.game_state.actors['npc_merchant']
        # Move player to forest road
        self.player.location = 'loc_forest_road'

    def test_merchant_has_trade_service(self):
        """Merchant offers trade service."""
        from behaviors.actors.services import get_available_services

        services = get_available_services(self.merchant)
        self.assertIn('trade', services)

    def test_merchant_is_friendly(self):
        """Injured merchant has friendly disposition."""
        disposition = self.merchant.properties.get('disposition')
        self.assertEqual(disposition, 'friendly')

    def test_can_trade_while_injured(self):
        """Merchant can trade even while bleeding."""
        from behaviors.actors.conditions import has_condition
        from behaviors.actors.services import get_available_services

        # Verify merchant is injured
        self.assertTrue(has_condition(self.merchant, 'bleeding'))

        # Services should still be available
        services = get_available_services(self.merchant)
        self.assertIn('trade', services)


class TestUC6Escort(unittest.TestCase):
    """Test escort mechanics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors['player']
        self.merchant = self.engine.game_state.actors['npc_merchant']
        # Move player to forest road
        self.player.location = 'loc_forest_road'

    def test_merchant_has_escort_destination(self):
        """Merchant has escort_destination property."""
        dest = self.merchant.properties.get('escort_destination')
        self.assertEqual(dest, 'loc_town_gate')

    def test_start_escort(self):
        """Starting escort sets following property."""
        from behaviors.uc6_merchant import start_escort, is_following

        accessor = _create_accessor(self.engine)

        msg = start_escort(accessor, self.merchant, self.player)

        self.assertIn('following', msg.lower())
        self.assertTrue(is_following(self.merchant, self.player.id))

    def test_is_following(self):
        """is_following correctly identifies following state."""
        from behaviors.uc6_merchant import is_following

        # Not following initially
        self.assertFalse(is_following(self.merchant, self.player.id))

        # Set following
        self.merchant.properties['following'] = self.player.id

        self.assertTrue(is_following(self.merchant, self.player.id))

    def test_update_escort_location(self):
        """Escort NPC moves with player."""
        from behaviors.uc6_merchant import start_escort, update_escort_location

        accessor = _create_accessor(self.engine)

        # Start escort
        start_escort(accessor, self.merchant, self.player)

        # Move player (simulated)
        self.player.location = 'loc_town_gate'
        update_escort_location(accessor, self.merchant, 'loc_town_gate')

        self.assertEqual(self.merchant.location, 'loc_town_gate')

    def test_check_escort_arrival(self):
        """check_escort_arrival detects destination reached."""
        from behaviors.uc6_merchant import check_escort_arrival

        accessor = _create_accessor(self.engine)

        # Not at destination initially
        self.assertFalse(check_escort_arrival(accessor, self.merchant))

        # Move to destination
        self.merchant.location = 'loc_town_gate'

        self.assertTrue(check_escort_arrival(accessor, self.merchant))


class TestUC6Reward(unittest.TestCase):
    """Test reward on escort completion."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors['player']
        self.merchant = self.engine.game_state.actors['npc_merchant']
        self.reward = None
        for item in self.engine.game_state.items:
            if item.id == 'item_merchant_pouch':
                self.reward = item
                break
        # Move player to forest road
        self.player.location = 'loc_forest_road'

    def test_merchant_has_reward(self):
        """Merchant has reward item in inventory."""
        self.assertIn('item_merchant_pouch', self.merchant.inventory)

    def test_reward_item_exists(self):
        """Reward item exists and has reward type."""
        self.assertIsNotNone(self.reward)
        self.assertEqual(self.reward.properties.get('type'), 'reward')

    def test_give_reward(self):
        """give_reward transfers item to player."""
        from behaviors.uc6_merchant import give_reward

        accessor = _create_accessor(self.engine)

        initial_player_inv = len(self.player.inventory)

        msg = give_reward(accessor, self.merchant, self.player)

        self.assertIsNotNone(msg)
        self.assertIn('pouch', msg.lower())
        self.assertIn('item_merchant_pouch', self.player.inventory)
        self.assertNotIn('item_merchant_pouch', self.merchant.inventory)

    def test_complete_escort_gives_reward(self):
        """Completing escort gives reward."""
        from behaviors.uc6_merchant import start_escort, complete_escort

        accessor = _create_accessor(self.engine)

        # Start and complete escort
        start_escort(accessor, self.merchant, self.player)
        self.merchant.location = 'loc_town_gate'

        msg = complete_escort(accessor, self.merchant, self.player)

        self.assertIn('thank', msg.lower())
        self.assertIn('item_merchant_pouch', self.player.inventory)

    def test_escort_clears_destination(self):
        """Completing escort clears escort_destination."""
        from behaviors.uc6_merchant import start_escort, complete_escort

        accessor = _create_accessor(self.engine)

        # Start and complete escort
        start_escort(accessor, self.merchant, self.player)
        self.merchant.location = 'loc_town_gate'
        complete_escort(accessor, self.merchant, self.player)

        # Destination should be cleared
        self.assertIsNone(self.merchant.properties.get('escort_destination'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
