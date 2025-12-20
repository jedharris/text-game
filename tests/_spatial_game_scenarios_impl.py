"""Implementation of spatial_game scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_spatial_game_scenarios.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.
"""
from src.types import ActorId

import sys
import unittest
from pathlib import Path


# Path to spatial_game - must be absolute before importing game modules
SPATIAL_GAME_DIR = (Path(__file__).parent.parent / 'examples' / 'spatial_game').resolve()
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def _setup_paths():
    """Ensure spatial_game directory is first in sys.path for behaviors imports.

    The game directory is added first so that its behaviors/ package is found
    before the project root's behaviors/ package.

    IMPORTANT: We remove '' (current directory) from path because when running
    from project root, Python would find behaviors/ from project root before
    finding it from spatial_game.
    """
    # Remove CWD ('') from path to prevent project root behaviors from being found
    while '' in sys.path:
        sys.path.remove('')

    # Add spatial_game directory first (for behaviors imports)
    game_dir_str = str(SPATIAL_GAME_DIR)
    if game_dir_str not in sys.path:
        sys.path.insert(0, game_dir_str)

    # Add project root after (for src imports)
    project_str = str(PROJECT_ROOT)
    if project_str not in sys.path:
        sys.path.insert(1, project_str)


# Set up paths before importing game modules
_setup_paths()

try:
    from src.game_engine import GameEngine
    from src.text_game import format_command_result
    WX_TEXT_GAME_AVAILABLE = True
except ModuleNotFoundError as exc:
    if exc.name == "wx":
        WX_TEXT_GAME_AVAILABLE = False
        GameEngine = None  # type: ignore[assignment,misc]
        format_command_result = None  # type: ignore[assignment]
    else:
        raise


@unittest.skipUnless(WX_TEXT_GAME_AVAILABLE, "wxPython not installed")
class TestMagicStaircaseVisibility(unittest.TestCase):
    """Test the magic staircase visibility puzzle in spatial_game."""

    def setUp(self):
        """Set up spatial_game engine."""
        self.engine = GameEngine(SPATIAL_GAME_DIR)
        self.player = self.engine.game_state.actors[ActorId('player')]

    def _execute(self, verb, obj=None):
        """Execute a command and return the response."""
        action = {"verb": verb}
        if obj:
            action["object"] = obj
        return self.engine.json_handler.handle_message({
            "type": "command",
            "action": action
        })

    def _look(self):
        """Execute look and return formatted output."""
        response = self._execute("look")
        return format_command_result(response)

    def test_staircase_hidden_without_star(self):
        """Staircase should not appear in tower entrance without the star."""
        self.player.location = 'loc_tower_entrance'
        self.player.inventory = []

        output = self._look()

        self.assertIn("garden archway (south)", output)
        self.assertIn("wooden door (east)", output)
        self.assertNotIn("spiral staircase", output)
        self.assertNotIn("up", output.split("Exits:")[1] if "Exits:" in output else "")

    def test_staircase_visible_with_star(self):
        """Staircase should appear in tower entrance when player has the star."""
        self.player.location = 'loc_tower_entrance'
        self.player.inventory = ['item_magic_star']

        output = self._look()

        self.assertIn("spiral staircase (up)", output)
        self.assertIn("garden archway (south)", output)
        self.assertIn("wooden door (east)", output)

    def test_cannot_go_up_without_star(self):
        """Player should not be able to go up without the star."""
        self.player.location = 'loc_tower_entrance'
        self.player.inventory = []

        response = self._execute("up")

        self.assertFalse(response.get("success"))
        self.assertEqual(self.player.location, 'loc_tower_entrance')

    def test_can_go_up_with_star(self):
        """Player should be able to go up with the star."""
        self.player.location = 'loc_tower_entrance'
        self.player.inventory = ['item_magic_star']

        response = self._execute("up")

        self.assertTrue(response.get("success"))
        self.assertEqual(self.player.location, 'loc_library')


@unittest.skipUnless(WX_TEXT_GAME_AVAILABLE, "wxPython not installed")
class TestMagicStarPuzzle(unittest.TestCase):
    """Test the magic star retrieval puzzle."""

    def setUp(self):
        """Set up spatial_game engine."""
        self.engine = GameEngine(SPATIAL_GAME_DIR)
        self.player = self.engine.game_state.actors[ActorId('player')]
        # Start in garden where the tree and bench are
        self.player.location = 'loc_garden'

    def _execute(self, verb, obj=None):
        """Execute a command and return the response."""
        from src.word_entry import WordEntry, WordType
        action = {"verb": verb}
        if obj:
            if isinstance(obj, str):
                action["object"] = WordEntry(obj, {WordType.NOUN}, [])
            else:
                action["object"] = obj
        return self.engine.json_handler.handle_message({
            "type": "command",
            "action": action
        })

    def _get_message(self, response):
        """Get message from response (handles both success and error formats)."""
        if response.get("success"):
            return response.get("message", "")
        else:
            return response.get("error", {}).get("message", "")

    def test_cannot_take_star_from_ground(self):
        """Cannot take star directly from ground - it's in the tree."""
        response = self._execute("take", "star")

        self.assertFalse(response.get("success"))
        self.assertIn("tree", self._get_message(response).lower())

    def test_cannot_climb_tree_from_ground(self):
        """Cannot climb tree directly from ground - need to stand on bench."""
        response = self._execute("climb", "tree")

        self.assertFalse(response.get("success"))
        self.assertIn("stand on", self._get_message(response).lower())

    def test_can_stand_on_bench(self):
        """Can stand on the bench."""
        response = self._execute("stand", "bench")

        self.assertTrue(response.get("success"))
        self.assertEqual(self.player.properties.get("posture"), "on_surface")
        self.assertEqual(self.player.properties.get("focused_on"), "item_garden_bench")

    def test_can_climb_tree_from_bench(self):
        """Can climb tree when standing on bench."""
        # First stand on bench
        self._execute("stand", "bench")

        # Now climb tree
        response = self._execute("climb", "tree")

        self.assertTrue(response.get("success"))
        self.assertEqual(self.player.properties.get("posture"), "climbing")
        self.assertEqual(self.player.properties.get("focused_on"), "item_tree")

    def test_can_take_star_when_climbing_tree(self):
        """Can take star when climbing the tree."""
        # Stand on bench
        self._execute("stand", "bench")
        # Climb tree
        self._execute("climb", "tree")

        # Take star
        response = self._execute("take", "star")

        self.assertTrue(response.get("success"))
        self.assertIn("item_magic_star", self.player.inventory)

    def test_dropped_star_can_be_picked_up_normally(self):
        """Star dropped elsewhere can be picked up without climbing."""
        # Give player the star and drop it
        self.player.inventory = ['item_magic_star']
        star = next(i for i in self.engine.game_state.items if i.id == 'item_magic_star')
        star.location = 'loc_garden'  # On ground, not in tree
        self.player.inventory = []

        # Should be able to take it normally
        response = self._execute("take", "star")

        self.assertTrue(response.get("success"))
        self.assertIn("item_magic_star", self.player.inventory)


@unittest.skipUnless(WX_TEXT_GAME_AVAILABLE, "wxPython not installed")
class TestExitDescriptions(unittest.TestCase):
    """Test that exits are properly displayed in all locations."""

    def setUp(self):
        """Set up spatial_game engine."""
        self.engine = GameEngine(SPATIAL_GAME_DIR)
        self.player = self.engine.game_state.actors[ActorId('player')]

    def _look(self):
        """Execute look and return formatted output."""
        response = self.engine.json_handler.handle_message({
            "type": "command",
            "action": {"verb": "look"}
        })
        return format_command_result(response)

    def test_garden_shows_exits(self):
        """Garden should show exit to tower entrance."""
        self.player.location = 'loc_garden'

        output = self._look()

        self.assertIn("Exits:", output)
        self.assertIn("stone path (north)", output)

    def test_storage_shows_exits(self):
        """Storage room should show exit back to entrance."""
        self.player.location = 'loc_storage'

        output = self._look()

        self.assertIn("Exits:", output)
        self.assertIn("wooden door (west)", output)

    def test_library_shows_exits(self):
        """Library should show exits up and down."""
        self.player.location = 'loc_library'

        output = self._look()

        self.assertIn("Exits:", output)
        self.assertIn("spiral staircase (down)", output)
        self.assertIn("ornate door (up)", output)


@unittest.skipUnless(WX_TEXT_GAME_AVAILABLE, "wxPython not installed")
class TestFullPuzzleSolution(unittest.TestCase):
    """Test playing through the complete star/staircase puzzle."""

    def setUp(self):
        """Set up spatial_game engine."""
        self.engine = GameEngine(SPATIAL_GAME_DIR)
        self.player = self.engine.game_state.actors[ActorId('player')]
        # Start in garden (the default start location)
        self.player.location = 'loc_garden'

    def _execute(self, verb, obj=None):
        """Execute a command and return the response."""
        from src.word_entry import WordEntry, WordType
        action = {"verb": verb}
        if obj:
            if isinstance(obj, str):
                action["object"] = WordEntry(obj, {WordType.NOUN}, [])
            else:
                action["object"] = obj
        return self.engine.json_handler.handle_message({
            "type": "command",
            "action": action
        })

    def test_complete_puzzle_solution(self):
        """Play through the complete puzzle: get star, reveal staircase, reach library."""
        # 1. Go north to tower entrance
        response = self._execute("north")
        self.assertTrue(response.get("success"))
        self.assertEqual(self.player.location, 'loc_tower_entrance')

        # 2. Verify staircase is hidden
        look_response = self._execute("look")
        self.assertNotIn("spiral staircase", look_response.get("message", ""))

        # 3. Go back south to garden
        response = self._execute("south")
        self.assertTrue(response.get("success"))
        self.assertEqual(self.player.location, 'loc_garden')

        # 4. Stand on bench
        response = self._execute("stand", "bench")
        self.assertTrue(response.get("success"))

        # 5. Climb tree
        response = self._execute("climb", "tree")
        self.assertTrue(response.get("success"))

        # 6. Take star
        response = self._execute("take", "star")
        self.assertTrue(response.get("success"))
        self.assertIn("item_magic_star", self.player.inventory)

        # 7. Get down from tree
        response = self._execute("down")
        self.assertTrue(response.get("success"))

        # 8. Go north to tower entrance
        response = self._execute("north")
        self.assertTrue(response.get("success"))
        self.assertEqual(self.player.location, 'loc_tower_entrance')

        # 9. Verify staircase is now visible
        look_response = self._execute("look")
        self.assertIn("spiral staircase", look_response.get("message", ""))

        # 10. Go up the staircase
        response = self._execute("up")
        self.assertTrue(response.get("success"))
        self.assertEqual(self.player.location, 'loc_library')


if __name__ == '__main__':
    unittest.main(verbosity=2)
