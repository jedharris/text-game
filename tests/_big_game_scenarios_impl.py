"""Implementation of big_game scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_big_game_scenarios.py
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
from src.text_game import format_command_result


class TestGameLoads(unittest.TestCase):
    """Test that the game loads without errors."""

    def test_engine_initializes(self):
        """GameEngine should initialize with big_game."""
        engine = GameEngine(GAME_DIR)
        self.assertIsNotNone(engine)
        self.assertIsNotNone(engine.game_state)

    def test_player_exists(self):
        """Player actor should exist and have correct starting location."""
        engine = GameEngine(GAME_DIR)
        player = engine.game_state.actors.get('player')
        self.assertIsNotNone(player)
        self.assertEqual(player.location, 'loc_mn_nexus_chamber')

    def test_locations_loaded(self):
        """All locations should be loaded."""
        engine = GameEngine(GAME_DIR)
        locations = engine.game_state.locations
        self.assertGreaterEqual(len(locations), 30)  # Should have ~31

    def test_actors_loaded(self):
        """All actors should be loaded."""
        engine = GameEngine(GAME_DIR)
        actors = engine.game_state.actors
        self.assertGreaterEqual(len(actors), 40)  # Should have ~50

    def test_items_loaded(self):
        """All items should be loaded."""
        engine = GameEngine(GAME_DIR)
        items = engine.game_state.items
        self.assertGreaterEqual(len(items), 50)  # Should have ~78

    def test_regions_defined(self):
        """Region definitions should exist in extra."""
        engine = GameEngine(GAME_DIR)
        regions = engine.game_state.extra.get('regions', {})
        self.assertIn('meridian_nexus', regions)
        self.assertIn('fungal_depths', regions)
        self.assertIn('beast_wilds', regions)
        self.assertIn('frozen_reaches', regions)
        self.assertIn('sunken_district', regions)
        self.assertIn('civilized_remnants', regions)


class TestBasicNavigation(unittest.TestCase):
    """Test basic movement between locations."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors['player']

    def _execute(self, verb, obj=None):
        """Execute a command and return the response."""
        action = {"verb": verb}
        if obj:
            action["object"] = obj
        return self.engine.json_handler.handle_message({
            "type": "command",
            "action": action
        })

    def test_look_works(self):
        """Look command should work in starting location."""
        response = self._execute("look")
        self.assertTrue(response.get("success"), f"Look failed: {response}")

    def test_can_go_west_to_fungal_depths(self):
        """Can navigate west from Nexus to Fungal Depths."""
        response = self._execute("go", "west")
        self.assertTrue(response.get("success"), f"Go west failed: {response}")
        self.assertEqual(self.player.location, 'loc_fd_cavern_entrance')

    def test_can_go_south_to_beast_wilds(self):
        """Can navigate south from Nexus to Beast Wilds."""
        response = self._execute("go", "south")
        self.assertTrue(response.get("success"), f"Go south failed: {response}")
        self.assertEqual(self.player.location, 'loc_bw_forest_edge')

    def test_can_go_north_to_frozen_reaches(self):
        """Can navigate north from Nexus to Frozen Reaches."""
        response = self._execute("go", "north")
        self.assertTrue(response.get("success"), f"Go north failed: {response}")
        self.assertEqual(self.player.location, 'loc_fr_frozen_pass')

    def test_can_go_east_to_sunken_district(self):
        """Can navigate east from Nexus to Sunken District."""
        response = self._execute("go", "east")
        self.assertTrue(response.get("success"), f"Go east failed: {response}")
        self.assertEqual(self.player.location, 'loc_sd_flooded_streets')

    def test_can_go_down_to_town(self):
        """Can navigate down from Nexus to Civilized Remnants."""
        response = self._execute("go", "down")
        self.assertTrue(response.get("success"), f"Go down failed: {response}")
        self.assertEqual(self.player.location, 'loc_cr_town_gate')


class TestNexusHub(unittest.TestCase):
    """Test the Meridian Nexus hub area."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors['player']

    def _execute(self, verb, obj=None):
        """Execute a command and return the response."""
        action = {"verb": verb}
        if obj:
            action["object"] = obj
        return self.engine.json_handler.handle_message({
            "type": "command",
            "action": action
        })

    def test_can_reach_observatory(self):
        """Can reach Observatory Platform from Nexus Chamber."""
        response = self._execute("go", "up")
        self.assertTrue(response.get("success"))
        self.assertEqual(self.player.location, 'loc_mn_observatory_platform')

    def test_can_reach_keepers_quarters(self):
        """Can reach Keeper's Quarters from Observatory."""
        self._execute("go", "up")  # To observatory
        response = self._execute("go", "east")
        self.assertTrue(response.get("success"))
        self.assertEqual(self.player.location, 'loc_mn_keepers_quarters')

    def test_can_reach_crystal_garden(self):
        """Can reach Crystal Garden from Keeper's Quarters."""
        self._execute("go", "up")  # To observatory
        self._execute("go", "east")  # To keeper's quarters
        response = self._execute("go", "south")
        self.assertTrue(response.get("success"))
        self.assertEqual(self.player.location, 'loc_mn_crystal_garden')

    def test_keepers_journal_exists(self):
        """Keeper's Journal should be in Keeper's Quarters."""
        journal = None
        for item in self.engine.game_state.items:
            if item.id == 'item_mn_keepers_journal':
                journal = item
                break
        self.assertIsNotNone(journal)
        self.assertEqual(journal.location, 'loc_mn_keepers_quarters')


class TestDialogSystem(unittest.TestCase):
    """Test NPC dialog with topics."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.player = self.engine.game_state.actors['player']

    def _execute(self, verb, obj=None):
        """Execute a command and return the response."""
        action = {"verb": verb}
        if obj:
            action["object"] = obj
        return self.engine.json_handler.handle_message({
            "type": "command",
            "action": action
        })

    def test_healer_elara_has_dialog_topics(self):
        """Healer Elara should have dialog topics defined."""
        elara = self.engine.game_state.actors.get('npc_cr_healer_elara')
        self.assertIsNotNone(elara)
        topics = elara.properties.get('dialog_topics', {})
        self.assertIn('help', topics)
        self.assertIn('infection', topics)

    def test_gate_guard_has_dialog_topics(self):
        """Gate Guard should have dialog topics defined."""
        guard = self.engine.game_state.actors.get('npc_cr_gate_guard')
        self.assertIsNotNone(guard)
        topics = guard.properties.get('dialog_topics', {})
        self.assertIn('entry', topics)

    def test_the_echo_has_dialog_topics(self):
        """The Echo should have dialog topics defined."""
        echo = self.engine.game_state.actors.get('npc_mn_the_echo')
        self.assertIsNotNone(echo)
        topics = echo.properties.get('dialog_topics', {})
        self.assertIn('meridian', topics)
        self.assertIn('keeper', topics)


class TestRegionSystem(unittest.TestCase):
    """Test region definitions and lookups."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)

    def test_all_region_locations_exist(self):
        """All locations listed in regions should exist."""
        regions = self.engine.game_state.extra.get('regions', {})
        location_ids = {loc.id for loc in self.engine.game_state.locations}

        for region_id, region_def in regions.items():
            for loc_id in region_def.get('locations', []):
                self.assertIn(
                    loc_id, location_ids,
                    f"Region {region_id} references non-existent location {loc_id}"
                )

    def test_fungal_depths_locations(self):
        """Fungal Depths should have 5 locations."""
        regions = self.engine.game_state.extra.get('regions', {})
        fungal = regions.get('fungal_depths', {})
        self.assertEqual(len(fungal.get('locations', [])), 5)

    def test_beast_wilds_locations(self):
        """Beast Wilds should have 5 locations."""
        regions = self.engine.game_state.extra.get('regions', {})
        beast = regions.get('beast_wilds', {})
        self.assertEqual(len(beast.get('locations', [])), 5)

    def test_faction_members_exist(self):
        """All faction members should exist as actors."""
        factions = self.engine.game_state.extra.get('factions', {})
        actor_ids = set(self.engine.game_state.actors.keys())

        for faction_id, faction_def in factions.items():
            for member_id in faction_def.get('members', []):
                self.assertIn(
                    member_id, actor_ids,
                    f"Faction {faction_id} references non-existent actor {member_id}"
                )


if __name__ == '__main__':
    unittest.main(verbosity=2)
