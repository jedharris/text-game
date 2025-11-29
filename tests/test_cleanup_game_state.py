"""
Tests for game state format conversion (Phase C-1).

These tests validate that the example game state uses the new unified format:
- behaviors as list (not dict)
- properties in properties dict (not at top level)
- actors in unified dict format
"""

import unittest
import json
from pathlib import Path
from src.state_manager import load_game_state, GameState


class TestGameStateFormat(unittest.TestCase):
    """Test that game state file uses new format."""

    def test_load_example_game_state(self):
        """Test that example game state loads successfully."""
        state = load_game_state(Path("examples/simple_game/game_state.json"))
        self.assertIsInstance(state, GameState)

    def test_behaviors_are_list_format(self):
        """Test that item behaviors use list format, not dict."""
        with open("examples/simple_game/game_state.json") as f:
            data = json.load(f)

        for item in data.get("items", []):
            behaviors = item.get("behaviors", [])
            if behaviors:
                self.assertIsInstance(behaviors, list,
                    f"Item {item['id']} behaviors should be list, got {type(behaviors)}")

    def test_item_properties_in_properties_dict(self):
        """Test that item portable/type are in properties dict."""
        with open("examples/simple_game/game_state.json") as f:
            data = json.load(f)

        for item in data.get("items", []):
            # These should NOT be at top level
            self.assertNotIn("portable", item,
                f"Item {item['id']} has 'portable' at top level, should be in properties")
            self.assertNotIn("type", item,
                f"Item {item['id']} has 'type' at top level, should be in properties")
            self.assertNotIn("provides_light", item,
                f"Item {item['id']} has 'provides_light' at top level, should be in properties")
            self.assertNotIn("states", item,
                f"Item {item['id']} has 'states' at top level, should be in properties")
            self.assertNotIn("container", item,
                f"Item {item['id']} has 'container' at top level, should be in properties")

    def test_lantern_behaviors_list_format(self):
        """Test that lantern with behaviors uses list format."""
        state = load_game_state(Path("examples/simple_game/game_state.json"))
        lantern = state.get_item("item_lantern")

        self.assertIsNotNone(lantern)
        self.assertIsInstance(lantern.behaviors, list)
        self.assertTrue(len(lantern.behaviors) > 0)

    def test_actors_unified_format(self):
        """Test that actors use unified dict format."""
        with open("examples/simple_game/game_state.json") as f:
            data = json.load(f)

        self.assertIn("actors", data)
        self.assertIsInstance(data["actors"], dict)
        self.assertIn("player", data["actors"])

    def test_door_properties_in_properties_dict(self):
        """Test that door locked/open are in properties dict."""
        with open("examples/simple_game/game_state.json") as f:
            data = json.load(f)

        for door in data.get("doors", []):
            # These should NOT be at top level
            self.assertNotIn("locked", door,
                f"Door {door['id']} has 'locked' at top level, should be in properties")
            self.assertNotIn("open", door,
                f"Door {door['id']} has 'open' at top level, should be in properties")
            self.assertNotIn("lock_id", door,
                f"Door {door['id']} has 'lock_id' at top level, should be in properties")
            # description stays at top level (it's a standard field)

    def test_lock_properties_in_properties_dict(self):
        """Test that lock opens_with/auto_unlock are in properties dict."""
        with open("examples/simple_game/game_state.json") as f:
            data = json.load(f)

        for lock in data.get("locks", []):
            # These should NOT be at top level
            self.assertNotIn("opens_with", lock,
                f"Lock {lock['id']} has 'opens_with' at top level, should be in properties")
            self.assertNotIn("auto_unlock", lock,
                f"Lock {lock['id']} has 'auto_unlock' at top level, should be in properties")
            # description stays at top level (it's a standard field)


if __name__ == '__main__':
    unittest.main()
