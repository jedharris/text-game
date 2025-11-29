"""
Unit tests for examining locks functionality.

Tests the examine command patterns for locks:
- "examine lock" - basic lock examination
- "examine east lock" - direction-qualified lock
- "examine lock in door" - prepositional phrase
- "examine lock in iron door" - prepositional with adjective
"""

import unittest
import json
import tempfile
from pathlib import Path

from src.state_manager import load_game_state
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from src.word_entry import WordEntry, WordType


class TestExamineLockBase(unittest.TestCase):
    """Base class for lock examination tests."""

    def setUp(self):
        """Set up test fixtures with simple game state."""
        # Load game state
        state_path = Path(__file__).parent.parent / "examples" / "simple_game" / "game_state.json"
        self.state = load_game_state(str(state_path))

        # Set up behavior manager
        self.behavior_manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        # Create protocol handler
        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.behavior_manager)

    def move_player_to(self, location_id: str):
        """Helper to move player to a specific location."""
        self.state.actors["player"].location = location_id


class TestExamineLockBasic(TestExamineLockBase):
    """Tests for basic 'examine lock' command."""

    def test_examine_lock_at_locked_door(self):
        """Test examining lock when at location with single locked door."""
        # Move player to hallway (has the locked treasure door to east)
        self.move_player_to("loc_hallway")

        # Build action with lock as WordEntry (simulating parser output)
        lock_word = WordEntry(word="lock", word_type=WordType.NOUN, synonyms=[])

        response = self.handler.handle_message({
            "type": "command",
            "action": {
                "verb": "examine",
                "object": lock_word
            }
        })

        self.assertTrue(response.get("success"), f"Expected success, got: {response}")
        self.assertIn("lock", response.get("message", "").lower())

    def test_examine_lock_no_lock_present(self):
        """Test examining lock when no lock is visible."""
        # Move player to tower (no locked doors)
        self.move_player_to("loc_tower")

        lock_word = WordEntry(word="lock", word_type=WordType.NOUN, synonyms=[])

        response = self.handler.handle_message({
            "type": "command",
            "action": {
                "verb": "examine",
                "object": lock_word
            }
        })

        self.assertFalse(response.get("success"))
        self.assertIn("lock", response.get("error", {}).get("message", "").lower())


class TestExamineLockWithDirection(TestExamineLockBase):
    """Tests for 'examine east lock' pattern."""

    def test_examine_east_lock(self):
        """Test examining lock with direction qualifier."""
        self.move_player_to("loc_hallway")

        lock_word = WordEntry(word="lock", word_type=WordType.NOUN, synonyms=[])

        response = self.handler.handle_message({
            "type": "command",
            "action": {
                "verb": "examine",
                "object": lock_word,
                "direction": "east"
            }
        })

        self.assertTrue(response.get("success"), f"Expected success, got: {response}")
        # Should find the treasure room lock
        self.assertIn("lock", response.get("message", "").lower())

    def test_examine_direction_lock_no_door(self):
        """Test examining lock in direction without a door."""
        self.move_player_to("loc_hallway")

        lock_word = WordEntry(word="lock", word_type=WordType.NOUN, synonyms=[])

        response = self.handler.handle_message({
            "type": "command",
            "action": {
                "verb": "examine",
                "object": lock_word,
                "direction": "up"  # Stairs, no door
            }
        })

        self.assertFalse(response.get("success"))

    def test_examine_direction_lock_unlocked_door(self):
        """Test examining lock on door with no lock."""
        self.move_player_to("loc_hallway")

        lock_word = WordEntry(word="lock", word_type=WordType.NOUN, synonyms=[])

        response = self.handler.handle_message({
            "type": "command",
            "action": {
                "verb": "examine",
                "object": lock_word,
                "direction": "south"  # Wooden door, no lock
            }
        })

        self.assertFalse(response.get("success"))


class TestExamineLockPrepositional(TestExamineLockBase):
    """Tests for 'examine lock in door' pattern."""

    def test_examine_lock_in_door(self):
        """Test examining lock with prepositional phrase."""
        self.move_player_to("loc_hallway")

        lock_word = WordEntry(word="lock", word_type=WordType.NOUN, synonyms=[])
        door_word = WordEntry(word="door", word_type=WordType.NOUN, synonyms=[])

        response = self.handler.handle_message({
            "type": "command",
            "action": {
                "verb": "examine",
                "object": lock_word,
                "preposition": "in",
                "indirect_object": door_word
            }
        })

        # Should find the treasure door lock (only locked door here)
        self.assertTrue(response.get("success"), f"Expected success, got: {response}")

    def test_examine_lock_in_iron_door(self):
        """Test examining lock with adjective on door."""
        self.move_player_to("loc_hallway")

        lock_word = WordEntry(word="lock", word_type=WordType.NOUN, synonyms=[])
        door_word = WordEntry(word="door", word_type=WordType.NOUN, synonyms=[])

        response = self.handler.handle_message({
            "type": "command",
            "action": {
                "verb": "examine",
                "object": lock_word,
                "preposition": "in",
                "indirect_adjective": "iron",
                "indirect_object": door_word
            }
        })

        self.assertTrue(response.get("success"), f"Expected success, got: {response}")

    def test_examine_lock_in_wooden_door_no_lock(self):
        """Test examining lock on door without a lock."""
        self.move_player_to("loc_hallway")

        lock_word = WordEntry(word="lock", word_type=WordType.NOUN, synonyms=[])
        door_word = WordEntry(word="door", word_type=WordType.NOUN, synonyms=[])

        response = self.handler.handle_message({
            "type": "command",
            "action": {
                "verb": "examine",
                "object": lock_word,
                "preposition": "in",
                "indirect_adjective": "wooden",
                "indirect_object": door_word
            }
        })

        self.assertFalse(response.get("success"))


class TestExamineLockLLMContext(TestExamineLockBase):
    """Tests that lock llm_context is included in response."""

    def test_lock_llm_context_included(self):
        """Test that lock's llm_context is returned in data."""
        self.move_player_to("loc_hallway")

        lock_word = WordEntry(word="lock", word_type=WordType.NOUN, synonyms=[])

        response = self.handler.handle_message({
            "type": "command",
            "action": {
                "verb": "examine",
                "object": lock_word,
                "direction": "east"
            }
        })

        self.assertTrue(response.get("success"))

        # Check that llm_context is present
        data = response.get("data", {})
        self.assertIn("llm_context", data)

        # Verify it has traits from the lock
        llm_context = data["llm_context"]
        self.assertIn("traits", llm_context)
        traits = llm_context["traits"]
        # The treasure lock has these traits
        self.assertTrue(any("iron" in trait.lower() for trait in traits))


class TestFindLockByContext(unittest.TestCase):
    """Unit tests for find_lock_by_context utility function."""

    def setUp(self):
        """Set up test fixtures."""
        state_path = Path(__file__).parent.parent / "examples" / "simple_game" / "game_state.json"
        self.state = load_game_state(str(state_path))

        self.behavior_manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_find_lock_by_direction(self):
        """Test finding lock via direction."""
        from utilities.utils import find_lock_by_context

        lock = find_lock_by_context(
            self.accessor,
            location_id="loc_hallway",
            direction="east"
        )

        self.assertIsNotNone(lock)
        self.assertEqual(lock.id, "lock_treasure")

    def test_find_lock_by_direction_no_door(self):
        """Test direction with no door returns None."""
        from utilities.utils import find_lock_by_context

        lock = find_lock_by_context(
            self.accessor,
            location_id="loc_hallway",
            direction="up"  # Stairs, no door
        )

        self.assertIsNone(lock)

    def test_find_lock_by_direction_door_no_lock(self):
        """Test direction with door but no lock returns None."""
        from utilities.utils import find_lock_by_context

        lock = find_lock_by_context(
            self.accessor,
            location_id="loc_hallway",
            direction="south"  # Wooden door, no lock
        )

        self.assertIsNone(lock)

    def test_find_lock_by_door_name(self):
        """Test finding lock via door name."""
        from utilities.utils import find_lock_by_context

        lock = find_lock_by_context(
            self.accessor,
            location_id="loc_hallway",
            door_name="door"
        )

        # Should find the treasure door lock (the locked one)
        self.assertIsNotNone(lock)

    def test_find_lock_single_locked_door(self):
        """Test finding lock when only one visible door has a lock."""
        from utilities.utils import find_lock_by_context

        lock = find_lock_by_context(
            self.accessor,
            location_id="loc_hallway"
        )

        # Should find the treasure door lock
        self.assertIsNotNone(lock)
        self.assertEqual(lock.id, "lock_treasure")

    def test_find_lock_no_locks_visible(self):
        """Test returns None when no locks are visible."""
        from utilities.utils import find_lock_by_context

        lock = find_lock_by_context(
            self.accessor,
            location_id="loc_tower"  # No locked doors
        )

        self.assertIsNone(lock)

    def test_find_lock_hidden_lock_not_found(self):
        """Test that hidden locks are not found."""
        from utilities.utils import find_lock_by_context

        # Make the treasure lock hidden
        treasure_lock = self.accessor.get_lock("lock_treasure")
        treasure_lock.states["hidden"] = True

        # Should not find the hidden lock via direction
        lock = find_lock_by_context(
            self.accessor,
            location_id="loc_hallway",
            direction="east"
        )
        self.assertIsNone(lock)

        # Should not find via auto-select either
        lock = find_lock_by_context(
            self.accessor,
            location_id="loc_hallway"
        )
        self.assertIsNone(lock)

    def test_find_lock_unhidden_lock_found(self):
        """Test that lock becomes visible after unhiding."""
        from utilities.utils import find_lock_by_context

        # Hide then unhide the lock
        treasure_lock = self.accessor.get_lock("lock_treasure")
        treasure_lock.states["hidden"] = True
        treasure_lock.states["hidden"] = False

        # Should find the lock now
        lock = find_lock_by_context(
            self.accessor,
            location_id="loc_hallway",
            direction="east"
        )
        self.assertIsNotNone(lock)
        self.assertEqual(lock.id, "lock_treasure")


class TestExamineLockHidden(TestExamineLockBase):
    """Tests for hidden lock behavior via examine command."""

    def test_examine_hidden_lock_fails(self):
        """Test that examining a hidden lock returns 'no lock' error."""
        self.move_player_to("loc_hallway")

        # Make the treasure lock hidden
        treasure_lock = None
        for lock in self.state.locks:
            if lock.id == "lock_treasure":
                treasure_lock = lock
                break
        treasure_lock.states["hidden"] = True

        lock_word = WordEntry(word="lock", word_type=WordType.NOUN, synonyms=[])

        response = self.handler.handle_message({
            "type": "command",
            "action": {
                "verb": "examine",
                "object": lock_word,
                "direction": "east"
            }
        })

        self.assertFalse(response.get("success"))
        self.assertIn("lock", response.get("error", {}).get("message", "").lower())


if __name__ == '__main__':
    unittest.main()
