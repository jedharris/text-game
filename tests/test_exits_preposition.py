"""Tests for preposition-based exit traversal (go through archway)."""

import json
import tempfile
import unittest
from pathlib import Path
from src.state_manager import GameState, Location, Actor, ExitDescriptor, Metadata
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.parser import Parser
from src.llm_narrator import parsed_to_json
from behaviors.core.exits import handle_go


class TestGoThroughPreposition(unittest.TestCase):
    """Test 'go through <exit name>' functionality."""

    def setUp(self):
        """Set up test game state with named exits and parser."""
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

        # Create parser with merged vocabulary (base + behavior modules)
        base_vocab_path = Path(__file__).parent.parent / "src" / "vocabulary.json"
        with open(base_vocab_path, 'r') as f:
            vocabulary = json.load(f)
        merged_vocabulary = self.behavior_manager.get_merged_vocabulary(vocabulary)

        # Write merged vocabulary to temp file for Parser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(merged_vocabulary, f)
            self.vocab_path = f.name

        self.parser = Parser(self.vocab_path)

    def tearDown(self):
        """Clean up temp vocabulary file."""
        Path(self.vocab_path).unlink()

    def test_go_through_archway_traverses_exit(self):
        """Test 'go through archway' moves player to destination.

        Uses parser to convert natural language to action dict.
        """
        parsed = self.parser.parse_command("go through archway")
        action = parsed_to_json(parsed)["action"]
        action["actor_id"] = "player"

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("second room", result.message.lower())
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room2")

    def test_go_through_nonexistent_exit_fails(self):
        """Test 'go through' with non-existent exit name fails."""
        parsed = self.parser.parse_command("go through portal")
        action = parsed_to_json(parsed)["action"]
        action["actor_id"] = "player"

        result = handle_go(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())
        # Player should not have moved
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room1")

    def test_walk_through_uses_synonym(self):
        """Test 'walk through archway' works (walk is synonym of go)."""
        parsed = self.parser.parse_command("walk through archway")
        action = parsed_to_json(parsed)["action"]
        action["actor_id"] = "player"

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room2")

    def test_go_through_stairs_traverses_exit(self):
        """Test 'go through stairs' finds exit by matching 'staircase'.

        Tests synonym matching in exit names.
        """
        # Move player to room3 first
        player = self.accessor.get_actor("player")
        self.accessor.update(player, {"location": "room3"})

        parsed = self.parser.parse_command("go through stairs")
        action = parsed_to_json(parsed)["action"]
        action["actor_id"] = "player"

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room4")

    def test_go_through_full_name_works(self):
        """Test using full exit name 'stone archway' works."""
        parsed = self.parser.parse_command("go through stone archway")
        action = parsed_to_json(parsed)["action"]
        action["actor_id"] = "player"

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room2")

    def test_go_north_still_works(self):
        """Test direction-based 'go north' still works after adding preposition support."""
        parsed = self.parser.parse_command("go north")
        action = parsed_to_json(parsed)["action"]
        action["actor_id"] = "player"

        result = handle_go(self.accessor, action)

        self.assertTrue(result.success)
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "room2")


if __name__ == '__main__':
    unittest.main()
