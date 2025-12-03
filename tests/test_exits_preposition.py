"""Tests for preposition-based exit traversal (go through archway)."""

import unittest
from src.state_manager import GameState, Location, Actor, ExitDescriptor, Metadata
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.parser import WordEntry, WordType
from behaviors.core.exits import handle_go


class TestGoThroughPreposition(unittest.TestCase):
    """Test 'go through <exit name>' functionality."""

    def setUp(self):
        """Set up test game state with named exits."""
        self.state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="room1",
                    name="First Room",
                    description="A room with an archway to the north.",
                    exits={
                        "north": ExitDescriptor(
                            type="open",
                            to="room2",
                            name="stone archway",
                            description="A grand stone archway"
                        )
                    }
                ),
                Location(
                    id="room2",
                    name="Second Room",
                    description="A room beyond the archway.",
                    exits={}
                ),
                Location(
                    id="room3",
                    name="Third Room",
                    description="A room with stairs down.",
                    exits={
                        "down": ExitDescriptor(
                            type="open",
                            to="room4",
                            name="spiral staircase",
                            description="A narrow spiral staircase"
                        )
                    }
                ),
                Location(
                    id="room4",
                    name="Fourth Room",
                    description="A room at the bottom of the stairs.",
                    exits={}
                )
            ],
            actors={"player": Actor(
                id="player",
                name="Adventurer",
                description="The player",
                location="room1",
                inventory=[]
            )}
        )
        self.behavior_manager = BehaviorManager()
        import behaviors.core.exits
        self.behavior_manager.load_module(behaviors.core.exits)
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_go_through_archway_traverses_exit(self):
        """Test 'go through archway' moves player to destination.

        Uses WordEntry with synonyms as the actual game parser does.
        """
        # When player types "go through archway", parser creates WordEntry with synonyms
        archway_entry = WordEntry(
            word="archway",
            word_type=WordType.NOUN,
            synonyms=["arch"]
        )
        action = {
            "actor_id": "player",
            "verb": "go",
            "preposition": "through",
            "object": archway_entry
        }

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("second room", result.message.lower())
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room2")

    def test_go_through_nonexistent_exit_fails(self):
        """Test 'go through' with non-existent exit name fails."""
        portal_entry = WordEntry(
            word="portal",
            word_type=WordType.NOUN,
            synonyms=[]
        )
        action = {
            "actor_id": "player",
            "verb": "go",
            "preposition": "through",
            "object": portal_entry
        }

        result = handle_go(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())
        # Player should not have moved
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room1")

    def test_walk_through_uses_synonym(self):
        """Test 'walk through archway' works (walk is synonym of go)."""
        archway_entry = WordEntry(
            word="archway",
            word_type=WordType.NOUN,
            synonyms=["arch"]
        )
        action = {
            "actor_id": "player",
            "verb": "walk",
            "preposition": "through",
            "object": archway_entry
        }

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room2")

    def test_go_through_stairs_traverses_exit(self):
        """Test 'go through stairs' finds exit by matching 'staircase'.

        Uses WordEntry with synonyms - "stairs" has synonym "staircase" which
        matches the exit name "spiral staircase".
        """
        # Move player to room3 first
        player = self.accessor.get_actor("player")
        self.accessor.update(player, {"location": "room3"})

        # When player types "go through stairs", parser creates WordEntry with synonyms
        stairs_entry = WordEntry(
            word="stairs",
            word_type=WordType.NOUN,
            synonyms=["staircase", "stairway", "steps"]
        )
        action = {
            "actor_id": "player",
            "verb": "go",
            "preposition": "through",
            "object": stairs_entry
        }

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room4")

    def test_go_through_full_name_works(self):
        """Test using full exit name 'stone archway' works."""
        # Multi-word noun phrase - parser would handle as single object
        archway_entry = WordEntry(
            word="stone archway",
            word_type=WordType.NOUN,
            synonyms=[]
        )
        action = {
            "actor_id": "player",
            "verb": "go",
            "preposition": "through",
            "object": archway_entry
        }

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room2")

    def test_go_north_still_works(self):
        """Test direction-based 'go north' still works after adding preposition support."""
        action = {
            "actor_id": "player",
            "verb": "go",
            "object": "north"
        }

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room2")


if __name__ == '__main__':
    unittest.main()
