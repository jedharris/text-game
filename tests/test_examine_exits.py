"""Tests for examining exits.

Verifies that handle_examine can find and describe exits, not just items and doors.
"""

import unittest
from tests.conftest import create_test_state
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.state_manager import Location, ExitDescriptor
from behaviors.core.perception import handle_examine
from utilities.utils import find_exit_by_name
from src.word_entry import WordEntry, WordType


class TestFindExitByName(unittest.TestCase):
    """Test the find_exit_by_name utility function."""

    def setUp(self):
        """Set up test state with various exits."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Get player's location
        player = self.state.actors["player"]
        self.location_id = player.location

        # Add destination rooms
        tower = Location(
            id="tower",
            name="Tower",
            description="A tower.",
            exits={"down": ExitDescriptor(type="open", to=self.location_id)}
        )
        cellar = Location(
            id="cellar",
            name="Cellar",
            description="A cellar.",
            exits={"up": ExitDescriptor(type="open", to=self.location_id)}
        )
        self.state.locations.append(tower)
        self.state.locations.append(cellar)

        # Add exits from player's current location
        room = self.accessor.get_location(self.location_id)
        room.exits["up"] = ExitDescriptor(
            type="open",
            to="tower",
            name="spiral staircase",
            description="A narrow spiral staircase winds upward."
        )
        room.exits["down"] = ExitDescriptor(
            type="open",
            to="cellar",
            name="stone steps",
            description="Rough stone steps descend into darkness."
        )
        room.exits["north"] = ExitDescriptor(
            type="open",
            to="tower"  # No name or description
        )

    def test_find_exit_by_direction(self):
        """Find exit using direction name."""
        result = find_exit_by_name(self.accessor, "up", "player")
        self.assertIsNotNone(result)
        direction, exit_desc = result
        self.assertEqual(direction, "up")
        self.assertEqual(exit_desc.name, "spiral staircase")

    def test_find_exit_by_direction_abbreviation(self):
        """Find exit using direction abbreviation."""
        result = find_exit_by_name(self.accessor, "u", "player")
        self.assertIsNotNone(result)
        direction, exit_desc = result
        self.assertEqual(direction, "up")

    def test_find_exit_by_name(self):
        """Find exit using exit.name field."""
        result = find_exit_by_name(self.accessor, "staircase", "player")
        self.assertIsNotNone(result)
        direction, exit_desc = result
        self.assertEqual(direction, "up")
        self.assertEqual(exit_desc.name, "spiral staircase")

    def test_find_exit_by_partial_name(self):
        """Find exit using partial name match."""
        result = find_exit_by_name(self.accessor, "spiral", "player")
        self.assertIsNotNone(result)
        direction, exit_desc = result
        self.assertEqual(direction, "up")

    def test_find_exit_by_word_in_name(self):
        """Find exit by matching a word in the name."""
        result = find_exit_by_name(self.accessor, "steps", "player")
        self.assertIsNotNone(result)
        direction, exit_desc = result
        self.assertEqual(direction, "down")

    def test_find_exit_with_adjective_direction(self):
        """Find exit using adjective + 'exit' pattern."""
        result = find_exit_by_name(self.accessor, "exit", "player", adjective="north")
        self.assertIsNotNone(result)
        direction, exit_desc = result
        self.assertEqual(direction, "north")

    def test_generic_exit_with_single_exit(self):
        """Find the only exit when using generic 'exit' term."""
        # Create a location with only one exit
        single_exit_loc = Location(
            id="single_exit_room",
            name="Single Exit Room",
            description="A room with one exit.",
            exits={"east": ExitDescriptor(
                type="open",
                to="tower",
                name="stone passage"
            )}
        )
        self.state.locations.append(single_exit_loc)
        self.state.actors["player"].location = "single_exit_room"

        result = find_exit_by_name(self.accessor, "exit", "player")
        self.assertIsNotNone(result)
        direction, exit_desc = result
        self.assertEqual(direction, "east")
        self.assertEqual(exit_desc.name, "stone passage")

    def test_generic_exit_with_multiple_exits_returns_none(self):
        """Generic 'exit' with multiple exits returns None (ambiguous)."""
        # The default setUp has multiple exits
        result = find_exit_by_name(self.accessor, "exit", "player")
        self.assertIsNone(result)

    def test_exit_not_found(self):
        """Return None when exit doesn't exist."""
        result = find_exit_by_name(self.accessor, "nonexistent", "player")
        self.assertIsNone(result)

    def test_exit_without_name_found_by_direction(self):
        """Exits without name field can still be found by direction."""
        result = find_exit_by_name(self.accessor, "north", "player")
        self.assertIsNotNone(result)
        direction, exit_desc = result
        self.assertEqual(direction, "north")
        self.assertIsNone(exit_desc.name)


class TestExamineExit(unittest.TestCase):
    """Test that handle_examine works for exits."""

    def setUp(self):
        """Set up test state with exits."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Get player's location
        player = self.state.actors["player"]
        self.location_id = player.location

        # Add destination rooms
        tower = Location(
            id="tower",
            name="Tower",
            description="A tower.",
            exits={"down": ExitDescriptor(type="open", to=self.location_id)}
        )
        self.state.locations.append(tower)

        # Add exits from player's current location
        room = self.accessor.get_location(self.location_id)
        room.exits["up"] = ExitDescriptor(
            type="open",
            to="tower",
            name="spiral staircase",
            description="A narrow spiral staircase winds upward into shadow.",
            properties={
                "llm_context": {
                    "traits": ["worn stone steps", "cold draft from above"],
                    "state_variants": {"first_visit": "The stairs beckon."}
                }
            }
        )
        room.exits["north"] = ExitDescriptor(
            type="open",
            to="tower",
            name="stone archway"
            # No description - should generate one from name
        )
        room.exits["south"] = ExitDescriptor(
            type="open",
            to="tower"
            # No name or description - should use generic
        )

    def test_examine_exit_by_direction(self):
        """Examine exit using direction returns description."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "up",
            "actor_id": "player"
        })
        self.assertTrue(result.success)
        self.assertIn("spiral staircase", result.message.lower())

    def test_examine_exit_by_name(self):
        """Examine exit using name returns description."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "staircase",
            "actor_id": "player"
        })
        self.assertTrue(result.success)
        self.assertIn("spiral", result.message.lower())

    def test_examine_exit_returns_llm_context(self):
        """Examine exit includes llm_context in data."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "up",
            "actor_id": "player"
        })
        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertIn("llm_context", result.data)
        self.assertIn("traits", result.data["llm_context"])

    def test_examine_exit_returns_direction_info(self):
        """Examine exit includes direction and type in data."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "up",
            "actor_id": "player"
        })
        self.assertTrue(result.success)
        self.assertIn("exit_direction", result.data)
        self.assertEqual(result.data["exit_direction"], "up")
        self.assertIn("exit_type", result.data)
        self.assertEqual(result.data["exit_type"], "open")

    def test_examine_exit_without_description_uses_name(self):
        """Exit without description gets generated message from name."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "archway",
            "actor_id": "player"
        })
        self.assertTrue(result.success)
        self.assertIn("stone archway", result.message.lower())
        self.assertIn("north", result.message.lower())

    def test_examine_exit_without_name_or_description(self):
        """Exit with only direction gets minimal message."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "south",
            "actor_id": "player"
        })
        self.assertTrue(result.success)
        self.assertIn("passage", result.message.lower())
        self.assertIn("south", result.message.lower())

    def test_examine_nonexistent_exit(self):
        """Examining nonexistent exit fails gracefully."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "west",
            "actor_id": "player"
        })
        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())


class TestExitExaminationPriority(unittest.TestCase):
    """Test that items/doors are examined before exits when names conflict."""

    def setUp(self):
        """Set up test state with potential name conflicts."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Get player's location
        player = self.state.actors["player"]
        self.location_id = player.location
        room = self.accessor.get_location(self.location_id)

        # Add an exit named "stairs"
        tower = Location(
            id="tower",
            name="Tower",
            description="A tower.",
            exits={}
        )
        self.state.locations.append(tower)

        room.exits["up"] = ExitDescriptor(
            type="open",
            to="tower",
            name="stairs",
            description="Exit stairs going up."
        )

    def test_direction_always_finds_exit(self):
        """Using direction like 'up' always finds exit, not item."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "up",
            "actor_id": "player"
        })
        self.assertTrue(result.success)
        self.assertIn("exit_direction", result.data)


class TestExamineExitWithDirectionAdjective(unittest.TestCase):
    """Test examining exits using direction as adjective.

    Tests the pattern "examine <direction> exit" and "examine <direction> door"
    where the direction acts as an adjective to select the specific exit/door.
    """

    def setUp(self):
        """Set up test state with multiple exits."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Get player's location
        player = self.state.actors["player"]
        self.location_id = player.location
        room = self.accessor.get_location(self.location_id)

        # Add destination rooms
        north_room = Location(
            id="north_room",
            name="North Room",
            description="A room to the north.",
            exits={"south": ExitDescriptor(type="open", to=self.location_id)}
        )
        east_room = Location(
            id="east_room",
            name="East Room",
            description="A room to the east.",
            exits={"west": ExitDescriptor(type="open", to=self.location_id)}
        )
        self.state.locations.append(north_room)
        self.state.locations.append(east_room)

        # Add exits with descriptions
        room.exits["north"] = ExitDescriptor(
            type="open",
            to="north_room",
            name="stone archway",
            description="A worn stone archway leads north."
        )
        room.exits["east"] = ExitDescriptor(
            type="open",
            to="east_room",
            name="wooden doorway",
            description="A simple wooden doorway leads east."
        )

    def test_examine_direction_exit(self):
        """Test 'examine north exit' finds the north exit."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "exit",
            "direction": "north",
            "actor_id": "player"
        })

        self.assertTrue(result.success)
        self.assertIn("north", result.message.lower())
        self.assertEqual(result.data["exit_direction"], "north")

    def test_examine_east_exit(self):
        """Test 'examine east exit' finds the east exit."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "exit",
            "direction": "east",
            "actor_id": "player"
        })

        self.assertTrue(result.success)
        self.assertIn("east", result.message.lower())
        self.assertEqual(result.data["exit_direction"], "east")

    def test_examine_direction_passage(self):
        """Test 'examine north passage' finds the north exit.

        Parser normalizes 'passage' to canonical 'exit' with synonyms.
        """
        # Simulate what parser provides - canonical word with synonyms
        exit_word = WordEntry(
            word="exit",
            word_type=WordType.NOUN,
            synonyms=["passage", "way", "path", "opening"]
        )
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": exit_word,
            "direction": "north",
            "actor_id": "player"
        })

        self.assertTrue(result.success)
        self.assertIn("north", result.message.lower())

    def test_examine_nonexistent_direction_exit(self):
        """Test 'examine west exit' fails when no west exit exists."""
        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": "exit",
            "direction": "west",
            "actor_id": "player"
        })

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())


class TestExitSynonymMatching(unittest.TestCase):
    """Test that vocabulary synonyms are used when matching exit names.

    This tests the fix for issue #25: "examine stairs" should find an exit
    named "spiral staircase" because "staircase" is a synonym of "stairs"
    in the vocabulary.
    """

    def setUp(self):
        """Set up test state with exits that have multi-word names."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Get player's location
        player = self.state.actors["player"]
        self.location_id = player.location
        room = self.accessor.get_location(self.location_id)

        # Add destination rooms
        tower = Location(
            id="tower",
            name="Tower",
            description="A tower.",
            exits={"down": ExitDescriptor(type="open", to=self.location_id)}
        )
        self.state.locations.append(tower)

        # Add exit with multi-word name "spiral staircase"
        # The vocabulary defines stairs with synonyms: ["staircase", "stairway", "steps"]
        room.exits["up"] = ExitDescriptor(
            type="open",
            to="tower",
            name="spiral staircase",
            description="A narrow spiral staircase carved from living rock."
        )

    def test_find_exit_with_synonym_staircase_matches_stairs(self):
        """'stairs' (canonical) should find exit named 'spiral staircase'.

        The vocabulary defines:
        {"word": "stairs", "synonyms": ["staircase", "stairway", "steps"]}

        So when user types "stairs", the WordEntry has synonym "staircase",
        which should match "staircase" in "spiral staircase".
        """
        from src.word_entry import WordEntry, WordType

        # Create WordEntry as the parser would
        stairs_entry = WordEntry(
            word="stairs",
            word_type=WordType.NOUN,
            synonyms=["staircase", "stairway", "steps"]
        )

        result = find_exit_by_name(self.accessor, stairs_entry, "player")
        self.assertIsNotNone(result, "Should find 'spiral staircase' with WordEntry('stairs')")
        direction, exit_desc = result
        self.assertEqual(direction, "up")
        self.assertEqual(exit_desc.name, "spiral staircase")

    def test_find_exit_with_synonym_steps_matches_stairs(self):
        """'steps' (synonym) should find exit named 'spiral staircase'."""
        from src.word_entry import WordEntry, WordType

        # When user types "steps", parser returns WordEntry with canonical "stairs"
        # and synonyms including "staircase"
        steps_entry = WordEntry(
            word="stairs",  # canonical form
            word_type=WordType.NOUN,
            synonyms=["staircase", "stairway", "steps"]
        )

        result = find_exit_by_name(self.accessor, steps_entry, "player")
        self.assertIsNotNone(result, "Should find 'spiral staircase' via synonym")
        direction, exit_desc = result
        self.assertEqual(direction, "up")

    def test_examine_with_synonym_finds_exit(self):
        """Full examine flow: 'examine stairs' finds 'spiral staircase'."""
        from src.word_entry import WordEntry, WordType

        # Simulate what the parser produces for "examine stairs"
        stairs_entry = WordEntry(
            word="stairs",
            word_type=WordType.NOUN,
            synonyms=["staircase", "stairway", "steps"]
        )

        result = handle_examine(self.accessor, {
            "verb": "examine",
            "object": stairs_entry,  # WordEntry instead of plain string
            "actor_id": "player"
        })

        self.assertTrue(result.success, f"Should succeed but got: {result.message}")
        self.assertIn("spiral staircase", result.message.lower())

    def test_plain_string_still_works(self):
        """Plain string matching still works (backward compatibility)."""
        # Using "staircase" directly (a word in the exit name) should work
        result = find_exit_by_name(self.accessor, "staircase", "player")
        self.assertIsNotNone(result)
        direction, exit_desc = result
        self.assertEqual(direction, "up")

    def test_plain_string_stairs_without_wordentry_fails(self):
        """Plain string 'stairs' doesn't match 'staircase' (no synonyms).

        This demonstrates why passing WordEntry is important - a plain
        string doesn't have synonym information.
        """
        result = find_exit_by_name(self.accessor, "stairs", "player")
        # Without WordEntry, plain "stairs" doesn't match "staircase" in name
        self.assertIsNone(result, "Plain 'stairs' shouldn't match 'spiral staircase'")


class TestExamineDirectionExitEndToEnd(unittest.TestCase):
    """End-to-end tests for 'examine <direction> exit' command flow.

    Tests the full pipeline from text parsing through to examination result.
    """

    def setUp(self):
        """Set up test state with parser and handler."""
        import tempfile
        import json
        from pathlib import Path
        from src.parser import Parser

        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        # Load behaviors
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Set up exits
        player = self.state.actors["player"]
        self.location_id = player.location
        room = self.accessor.get_location(self.location_id)

        # Add destination room
        north_room = Location(
            id="north_room",
            name="North Room",
            description="A room to the north.",
            exits={"south": ExitDescriptor(type="open", to=self.location_id)}
        )
        self.state.locations.append(north_room)

        room.exits["north"] = ExitDescriptor(
            type="open",
            to="north_room",
            name="stone archway",
            description="A weathered stone archway leads north."
        )

        # Load vocabulary and merge with behavior vocabulary
        vocab_path = Path(__file__).parent.parent / "src" / "vocabulary.json"
        with open(vocab_path, 'r') as f:
            base_vocab = json.load(f)

        merged_vocab = self.behavior_manager.get_merged_vocabulary(base_vocab)

        # Write to temp file for parser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(merged_vocab, f)
            vocab_path_temp = f.name

        self.parser = Parser(vocab_path_temp)
        Path(vocab_path_temp).unlink()

    def test_parse_examine_north_exit(self):
        """Verify 'examine north exit' parses with direction and noun."""
        result = self.parser.parse_command("examine north exit")

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "examine")
        self.assertEqual(result.direction.word, "north")
        self.assertEqual(result.direct_object.word, "exit")

    def test_full_flow_examine_north_exit(self):
        """Test full flow from parsing to examination."""
        from src.text_game import parsed_to_json

        # Parse command
        parsed = self.parser.parse_command("examine north exit")
        self.assertIsNotNone(parsed)

        # Convert to JSON action format
        json_cmd = parsed_to_json(parsed)
        action = json_cmd["action"]

        # Ensure actor_id is set
        action["actor_id"] = "player"

        # Execute examine handler
        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success, f"Expected success but got: {result.message}")
        self.assertIn("north", result.message.lower())


if __name__ == "__main__":
    unittest.main()
