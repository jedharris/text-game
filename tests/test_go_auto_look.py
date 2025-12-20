"""Tests for auto-look behavior after movement.

When a player successfully moves to a new location via the 'go' command,
the game should automatically provide a description of the new location
(equivalent to running 'look').
"""

import unittest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import SimpleGameTestCase, make_action


class TestGoAutoLook(SimpleGameTestCase):
    """Test that 'go' command includes location description."""

    def test_go_includes_location_name(self):
        """Test that successful 'go' includes the new location's name."""
        # Player starts in loc_start, go north to loc_hallway
        action = make_action(object="north", actor_id="player")
        result = self.behavior_manager.invoke_handler("go", self.accessor, action)

        self.assertTrue(result.success)
        # The message should include the destination name
        self.assertIn("Long Hallway", result.primary)

    def test_go_includes_location_description(self):
        """Test that successful 'go' includes the new location's description."""
        action = make_action(object="north", actor_id="player")
        result = self.behavior_manager.invoke_handler("go", self.accessor, action)

        self.assertTrue(result.success)
        # Should include part of the location description
        self.assertIn("long hallway", result.primary.lower())

    def test_go_includes_visible_items(self):
        """Test that successful 'go' lists visible items in the new location."""
        action = make_action(object="north", actor_id="player")
        result = self.behavior_manager.invoke_handler("go", self.accessor, action)

        self.assertTrue(result.success)
        # loc_hallway has a key and table
        self.assertIn("key", result.primary.lower())

    def test_go_failure_does_not_include_look(self):
        """Test that failed 'go' does not include look info."""
        # Try to go east from loc_start (no exit)
        action = make_action(object="east", actor_id="player")
        result = self.behavior_manager.invoke_handler("go", self.accessor, action)

        self.assertFalse(result.success)
        # Should not include any location description
        self.assertNotIn("Long Hallway", result.primary)

    def test_go_blocked_by_door_does_not_include_look(self):
        """Test that 'go' blocked by closed door does not include look info."""
        # First move to hallway
        action = make_action(object="north", actor_id="player")
        self.behavior_manager.invoke_handler("go", self.accessor, action)

        # Now try to go east through the locked door
        action = make_action(object="east", actor_id="player")
        result = self.behavior_manager.invoke_handler("go", self.accessor, action)

        self.assertFalse(result.success)
        # Should mention door is closed/locked, not the treasure room
        self.assertNotIn("Treasure Room", result.primary)


if __name__ == "__main__":
    unittest.main()
