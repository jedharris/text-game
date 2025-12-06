"""Tests for the 'down' command to return to ground level or move down."""

import unittest
from tests.conftest import SimpleGameTestCase, make_action


class TestDownCommand(SimpleGameTestCase):
    """Test 'down' command for dismounting and descending."""

    def test_down_from_climbing(self):
        """Test 'down' command after climbing."""
        player = self.accessor.get_actor("player")

        player.properties["posture"] = "climbing"
        player.properties["focused_on"] = "item_bench"

        # Say 'down' to get down
        action = make_action(verb="down", actor_id="player")
        result = self.behavior_manager.invoke_handler("down", self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("down", result.message.lower())

        # Verify posture cleared
        self.assertNotIn("posture", player.properties)
        self.assertNotIn("focused_on", player.properties)

    def test_down_from_cover(self):
        """Test 'down' command after taking cover."""
        player = self.accessor.get_actor("player")

        player.properties["posture"] = "cover"
        player.properties["focused_on"] = "item_table"

        # Say 'down'
        action = make_action(verb="down", actor_id="player")
        result = self.behavior_manager.invoke_handler("down", self.accessor, action)

        self.assertTrue(result.success)

        # Verify posture cleared
        self.assertNotIn("posture", player.properties)
        self.assertNotIn("focused_on", player.properties)

    def test_down_from_concealed(self):
        """Test 'down' command after hiding."""
        player = self.accessor.get_actor("player")

        player.properties["posture"] = "concealed"
        player.properties["focused_on"] = "item_wardrobe"

        # Say 'down'
        action = make_action(verb="down", actor_id="player")
        result = self.behavior_manager.invoke_handler("down", self.accessor, action)

        self.assertTrue(result.success)

        # Verify posture cleared
        self.assertNotIn("posture", player.properties)
        self.assertNotIn("focused_on", player.properties)

    def test_go_down_with_no_posture_and_no_exit(self):
        """Test 'go down' when standing normally with no down exit."""
        player = self.accessor.get_actor("player")

        # Make sure no posture
        player.properties.pop("posture", None)
        player.properties.pop("focused_on", None)

        # Move to a location with no 'down' exit (locked room has no down exit)
        self.accessor.update(player, {"location": "loc_locked_room"})

        # Try 'go down' - should fail since no down exit
        action = make_action(verb="go", object="down", actor_id="player")
        result = self.behavior_manager.invoke_handler("go", self.accessor, action)

        self.assertFalse(result.success)
        # Should get error about can't go down
        self.assertIn("down", result.message.lower())

    def test_go_down_with_no_posture_uses_exit(self):
        """Test 'go down' when standing normally goes through down exit."""
        player = self.accessor.get_actor("player")

        # Make sure no posture
        player.properties.pop("posture", None)
        player.properties.pop("focused_on", None)

        # Move to tower which has stairs down to hallway
        self.accessor.update(player, {"location": "loc_tower"})

        # Say 'go down' - should use the stairs
        action = make_action(verb="go", object="down", actor_id="player")
        result = self.behavior_manager.invoke_handler("go", self.accessor, action)

        self.assertTrue(result.success)
        # Should have moved to hallway
        self.assertEqual(player.location, "loc_hallway")


if __name__ == "__main__":
    unittest.main()
