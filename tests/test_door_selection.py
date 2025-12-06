"""Tests for smart door selection when multiple doors are present.

When a player says "unlock door" or "open door" in a location with multiple
doors, the game should prefer doors that the player can actually interact with:
1. For unlock: prefer doors that the player has a key for
2. For open: prefer doors that are closed but unlocked (actionable)
3. Fall back to locked/closed doors over already open ones
"""

import unittest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utilities.utils import find_door_with_adjective, actor_has_key_for_door
from tests.conftest import SimpleGameTestCase, make_word_entry, make_action


class TestDoorSelection(SimpleGameTestCase):
    """Test smart door selection for unlock/open/close commands."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()

        # Move player to hallway where there are two doors
        player = self.accessor.get_actor("player")
        self.accessor.update(player, {"location": "loc_hallway"})

    def test_unlock_prefers_door_player_has_key_for(self):
        """Test that 'unlock door' prefers the door the player has a key for."""
        # Give player the key
        player = self.accessor.get_actor("player")
        self.accessor.update(player, {"inventory": ["item_key"]})

        # In loc_hallway there are two doors:
        # - door_wooden (south) - no lock
        # - door_treasure (east) - locked, opens with item_key

        action = make_action(object="door", actor_id="player")
        result = self.behavior_manager.invoke_handler("unlock", self.accessor, action)

        # Should unlock door_treasure, not complain about door_wooden having no lock
        self.assertTrue(result.success)
        self.assertIn("unlock", result.message.lower())

    def test_unlock_without_key_still_finds_locked_door(self):
        """Test that 'unlock door' finds the locked door even without key."""
        # Player has no key
        action = make_action(object="door", actor_id="player")
        result = self.behavior_manager.invoke_handler("unlock", self.accessor, action)

        # Should fail because no key, but should have tried the locked door
        self.assertFalse(result.success)
        self.assertIn("key", result.message.lower())

    def test_open_prefers_closed_unlocked_door(self):
        """Test that 'open door' prefers a closed but unlocked door."""
        # Close the wooden door (it's unlocked)
        wooden_door = self.accessor.get_door_item("door_wooden")
        if wooden_door:
            wooden_door.door_open = False

        # Now we have:
        # - door_wooden: closed, unlocked (actionable!)
        # - door_treasure: closed, locked (not actionable without key)

        action = make_action(object="door", actor_id="player")
        result = self.behavior_manager.invoke_handler("open", self.accessor, action)

        # Should successfully open the wooden door
        self.assertTrue(result.success)
        self.assertIn("open", result.message.lower())

    def test_open_locked_door_fails_appropriately(self):
        """Test that 'open door' on locked door fails with locked message."""
        # Ensure wooden door is open, treasure door is locked
        wooden_door = self.accessor.get_door_item("door_wooden")
        if wooden_door:
            wooden_door.door_open = True

        # Now only door_treasure is closed (and locked)
        action = make_action(object="door", actor_id="player")
        result = self.behavior_manager.invoke_handler("open", self.accessor, action)

        # Should fail because the only closed door is locked
        self.assertFalse(result.success)
        self.assertIn("locked", result.message.lower())

    def test_adjective_overrides_smart_selection(self):
        """Test that explicit adjective still selects the specified door."""
        # Give player the key
        player = self.accessor.get_actor("player")
        self.accessor.update(player, {"inventory": ["item_key"]})

        # Explicitly ask for the wooden door
        action = make_action(object="door", adjective="wooden", actor_id="player")
        result = self.behavior_manager.invoke_handler("unlock", self.accessor, action)

        # Should try to unlock wooden door - it's not locked so "already unlocked"
        # (The wooden door has no lock_id but also locked=false in the game state)
        self.assertIn("already unlocked", result.message.lower())

    def test_close_prefers_open_door(self):
        """Test that 'close door' prefers an open door."""
        # Ensure wooden door is open, treasure door is closed
        wooden_door = self.accessor.get_door_item("door_wooden")
        if wooden_door:
            wooden_door.door_open = True

        action = make_action(object="door", actor_id="player")
        result = self.behavior_manager.invoke_handler("close", self.accessor, action)

        # Should close the wooden door (the open one)
        self.assertTrue(result.success)
        self.assertIn("close", result.message.lower())


class TestDoorSelectionUtility(SimpleGameTestCase):
    """Test the find_door_with_adjective utility function improvements."""

    def test_actor_has_key_for_door(self):
        """Test the actor_has_key_for_door utility."""
        # Get door
        door = self.accessor.get_door_item("door_treasure")

        # Player without key
        result = actor_has_key_for_door(self.accessor, "player", door)
        self.assertFalse(result)

        # Give player the key
        player = self.accessor.get_actor("player")
        self.accessor.update(player, {"inventory": ["item_key"]})

        result = actor_has_key_for_door(self.accessor, "player", door)
        self.assertTrue(result)

    def test_find_door_with_adjective_iron(self):
        """Test finding door by 'iron' adjective."""
        # In loc_hallway, door_treasure is described as "heavy iron door"
        door_entry = make_word_entry("door")

        door = find_door_with_adjective(

            self.accessor, door_entry, "iron", "loc_hallway")
        self.assertIsNotNone(door)
        self.assertEqual(door.id, "door_treasure")

    def test_find_door_with_adjective_wooden(self):
        """Test finding door by 'wooden' adjective."""
        door_entry = make_word_entry("door")

        door = find_door_with_adjective(

            self.accessor, door_entry, "wooden", "loc_hallway")
        self.assertIsNotNone(door)
        self.assertEqual(door.id, "door_wooden")


if __name__ == "__main__":
    unittest.main()
