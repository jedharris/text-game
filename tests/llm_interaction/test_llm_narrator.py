"""Tests for LLM narrator infrastructure.

Tests the LLMNarrator class using MockLLMNarrator to avoid actual API calls.
"""

import unittest
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.state_manager import load_game_state
from src.json_protocol import JSONProtocolHandler
from src.llm_narrator import MockLLMNarrator


class TestJSONExtraction(unittest.TestCase):
    """Test extracting JSON from various LLM response formats."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = JSONProtocolHandler(self.state)

    def test_extract_json_from_code_block(self):
        """Test extracting JSON from markdown code block with json tag."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        response = '```json\n{"type": "command", "action": {"verb": "take", "object": "sword"}}\n```'
        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["action"]["verb"], "take")
        self.assertEqual(result["action"]["object"], "sword")

    def test_extract_json_from_code_block_no_tag(self):
        """Test extracting JSON from markdown code block without json tag."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        response = '```\n{"type": "command", "action": {"verb": "look"}}\n```'
        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["action"]["verb"], "look")

    def test_extract_json_plain(self):
        """Test extracting plain JSON response without code block."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        response = '{"type": "command", "action": {"verb": "inventory"}}'
        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["action"]["verb"], "inventory")

    def test_extract_json_with_whitespace(self):
        """Test extracting JSON with surrounding whitespace."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        response = '  \n  {"type": "query", "query_type": "location"}  \n  '
        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "query")
        self.assertEqual(result["query_type"], "location")

    def test_extract_json_with_surrounding_text(self):
        """Test extracting JSON from code block with surrounding text."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        response = '''I'll help you pick that up.

```json
{"type": "command", "action": {"verb": "take", "object": "key"}}
```

This will pick up the key.'''

        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        self.assertEqual(result["action"]["object"], "key")

    def test_extract_json_invalid_returns_none(self):
        """Test that invalid JSON returns None."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        result = narrator._extract_json("not json at all")
        self.assertIsNone(result)

    def test_extract_json_malformed_returns_none(self):
        """Test that malformed JSON returns None."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        result = narrator._extract_json('{"type": "command", "action":}')
        self.assertIsNone(result)

    def test_extract_json_empty_returns_none(self):
        """Test that empty string returns None."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        result = narrator._extract_json("")
        self.assertIsNone(result)

    def test_extract_json_code_block_with_invalid_json(self):
        """Test code block containing invalid JSON."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        response = '```json\n{invalid json}\n```'
        result = narrator._extract_json(response)
        self.assertIsNone(result)

    def test_extract_json_multiline(self):
        """Test extracting formatted multiline JSON."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        response = '''```json
{
  "type": "command",
  "action": {
    "verb": "go",
    "direction": "north"
  }
}
```'''
        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        self.assertEqual(result["action"]["verb"], "go")
        self.assertEqual(result["action"]["direction"], "north")


class TestProcessTurn(unittest.TestCase):
    """Test the process_turn method."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = JSONProtocolHandler(self.state)

    def test_process_turn_take_item(self):
        """Test processing a take command."""
        # Ensure player is in loc_start where sword is
        self.state.player.location = "loc_start"

        # Mock responses: first for command generation, second for narration
        responses = [
            '```json\n{"type": "command", "action": {"verb": "take", "object": "sword"}}\n```',
            "You pick up the rusty sword. Its weight feels reassuring in your hand."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        result = narrator.process_turn("pick up the sword")

        # Should return narrative
        self.assertIn("sword", result.lower())
        # Should have made 2 LLM calls
        self.assertEqual(narrator.call_count, 2)
        # First call should be for command generation
        self.assertIn("Player says:", narrator.calls[0])
        # Second call should be for narration
        self.assertIn("Narrate", narrator.calls[1])

    def test_process_turn_movement(self):
        """Test processing a movement command."""
        self.state.player.location = "loc_start"

        responses = [
            '{"type": "command", "action": {"verb": "go", "direction": "north"}}',
            "You step through the doorway into the hallway."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        result = narrator.process_turn("go north")

        self.assertIn("hallway", result.lower())
        self.assertEqual(narrator.call_count, 2)

    def test_process_turn_invalid_json_returns_error(self):
        """Test that invalid JSON from LLM returns error message."""
        responses = [
            "I'm not sure what you mean by that.",  # Invalid - no JSON
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        result = narrator.process_turn("do something weird")

        self.assertEqual(result, "I don't understand what you want to do.")
        # Only one call since extraction failed
        self.assertEqual(narrator.call_count, 1)

    def test_process_turn_failed_action(self):
        """Test processing a command that fails."""
        self.state.player.location = "loc_start"

        # Try to take something that doesn't exist
        responses = [
            '{"type": "command", "action": {"verb": "take", "object": "diamond"}}',
            "You look around but don't see any diamond here."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        result = narrator.process_turn("take the diamond")

        # Should still narrate, even on failure
        self.assertEqual(narrator.call_count, 2)
        self.assertIn("diamond", result.lower())

    def test_process_turn_examine(self):
        """Test processing an examine command."""
        self.state.player.location = "loc_start"

        responses = [
            '{"type": "command", "action": {"verb": "examine", "object": "sword"}}',
            "The sword is old and rusty, but still has an edge."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        result = narrator.process_turn("look at the sword")

        self.assertEqual(narrator.call_count, 2)

    def test_process_turn_inventory(self):
        """Test processing an inventory command."""
        # Give player some items
        self.state.player.inventory = ["item_sword"]

        responses = [
            '{"type": "command", "action": {"verb": "inventory"}}',
            "You are carrying a rusty sword."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        result = narrator.process_turn("what am I carrying")

        self.assertEqual(narrator.call_count, 2)

    def test_process_turn_query(self):
        """Test processing a location query."""
        self.state.player.location = "loc_start"

        responses = [
            '{"type": "query", "query_type": "location"}',
            "You are in a small stone room."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        result = narrator.process_turn("where am I")

        self.assertEqual(narrator.call_count, 2)


class TestGetOpening(unittest.TestCase):
    """Test the get_opening method."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = JSONProtocolHandler(self.state)

    def test_get_opening_returns_narrative(self):
        """Test that get_opening returns a narrative."""
        self.state.player.location = "loc_start"

        responses = [
            "You awaken in a small stone chamber. Dim light filters through cracks in the ceiling."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        result = narrator.get_opening()

        self.assertIn("stone", result.lower())
        self.assertEqual(narrator.call_count, 1)

    def test_get_opening_includes_location_context(self):
        """Test that get_opening sends location info to LLM."""
        self.state.player.location = "loc_start"

        responses = ["Opening narrative"]
        narrator = MockLLMNarrator(self.handler, responses)

        narrator.get_opening()

        # Check the call included location data
        self.assertEqual(len(narrator.calls), 1)
        self.assertIn("Narrate the opening scene", narrator.calls[0])
        # Should include JSON with location info
        self.assertIn("loc_start", narrator.calls[0])

    def test_get_opening_queries_full_location(self):
        """Test that get_opening requests items, doors, npcs."""
        self.state.player.location = "loc_start"

        responses = ["You stand in a dusty chamber."]
        narrator = MockLLMNarrator(self.handler, responses)

        narrator.get_opening()

        # The query should include items, doors, npcs
        call_content = narrator.calls[0]
        # These should be in the JSON result sent to LLM
        self.assertIn("items", call_content.lower())


class TestMockNarrator(unittest.TestCase):
    """Test the MockLLMNarrator class itself."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = JSONProtocolHandler(self.state)

    def test_mock_tracks_calls(self):
        """Test that mock narrator tracks all calls."""
        responses = ["response1", "response2", "response3"]
        narrator = MockLLMNarrator(self.handler, responses)

        narrator._call_llm("first message")
        narrator._call_llm("second message")

        self.assertEqual(len(narrator.calls), 2)
        self.assertEqual(narrator.calls[0], "first message")
        self.assertEqual(narrator.calls[1], "second message")

    def test_mock_cycles_responses(self):
        """Test that mock narrator cycles through responses."""
        responses = ["a", "b"]
        narrator = MockLLMNarrator(self.handler, responses)

        self.assertEqual(narrator._call_llm("1"), "a")
        self.assertEqual(narrator._call_llm("2"), "b")
        self.assertEqual(narrator._call_llm("3"), "a")  # Cycles back
        self.assertEqual(narrator._call_llm("4"), "b")

    def test_mock_call_count(self):
        """Test that mock narrator counts calls correctly."""
        responses = ["response"]
        narrator = MockLLMNarrator(self.handler, responses)

        self.assertEqual(narrator.call_count, 0)
        narrator._call_llm("test")
        self.assertEqual(narrator.call_count, 1)
        narrator._call_llm("test")
        self.assertEqual(narrator.call_count, 2)


class TestIntegration(unittest.TestCase):
    """Integration tests for the full turn cycle."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = JSONProtocolHandler(self.state)

    def test_full_game_sequence(self):
        """Test a sequence of game actions."""
        self.state.player.location = "loc_start"

        # Sequence: look, take sword, go north
        responses = [
            # Look
            '{"type": "query", "query_type": "location", "include": ["items", "doors"]}',
            "You're in a small stone room with a sword on the ground.",
            # Take sword
            '{"type": "command", "action": {"verb": "take", "object": "sword"}}',
            "You pick up the rusty sword.",
            # Go north
            '{"type": "command", "action": {"verb": "go", "direction": "north"}}',
            "You head north into a hallway."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        # Turn 1: Look
        result1 = narrator.process_turn("look around")
        self.assertEqual(narrator.call_count, 2)

        # Turn 2: Take sword
        result2 = narrator.process_turn("pick up sword")
        self.assertEqual(narrator.call_count, 4)
        # Verify sword is now in inventory
        self.assertIn("item_sword", self.state.player.inventory)

        # Turn 3: Go north
        result3 = narrator.process_turn("go north")
        self.assertEqual(narrator.call_count, 6)
        # Verify player moved
        self.assertEqual(self.state.player.location, "loc_hallway")

    def test_unlock_and_open_door(self):
        """Test unlocking and opening a door."""
        self.state.player.location = "loc_hallway"
        # Give player the key
        self.state.player.inventory = ["item_key"]

        # Find the iron door and ensure it's locked
        for door in self.state.doors:
            if door.id == "door_iron":
                door.locked = True
                door.open = False
                break

        responses = [
            # Unlock
            '{"type": "command", "action": {"verb": "unlock", "object": "door"}}',
            "You unlock the iron door with the key.",
            # Open
            '{"type": "command", "action": {"verb": "open", "object": "door"}}',
            "The iron door swings open with a creak."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        # Unlock the door
        narrator.process_turn("unlock the door")

        # Open the door
        narrator.process_turn("open the door")

        # Verify door state
        for door in self.state.doors:
            if door.id == "door_iron":
                self.assertFalse(door.locked)
                self.assertTrue(door.open)
                break


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = JSONProtocolHandler(self.state)

    def test_empty_input(self):
        """Test handling empty player input."""
        responses = [
            "I need you to tell me what you want to do.",
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        result = narrator.process_turn("")

        # LLM should still be called, but may fail to extract JSON
        self.assertEqual(narrator.call_count, 1)

    def test_very_long_input(self):
        """Test handling very long player input."""
        responses = [
            '{"type": "command", "action": {"verb": "look"}}',
            "You look around the room."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        long_input = "I want to " + "really " * 100 + "look around the room"
        result = narrator.process_turn(long_input)

        self.assertEqual(narrator.call_count, 2)

    def test_special_characters_in_input(self):
        """Test handling special characters in input."""
        responses = [
            '{"type": "command", "action": {"verb": "look"}}',
            "You look around."
        ]
        narrator = MockLLMNarrator(self.handler, responses)

        result = narrator.process_turn("look @ the 'sword' & things!")

        self.assertEqual(narrator.call_count, 2)

    def test_json_with_extra_fields(self):
        """Test that extra fields in JSON don't break extraction."""
        narrator = MockLLMNarrator(self.handler, ["dummy"])

        response = '{"type": "command", "action": {"verb": "take", "object": "sword"}, "extra": "ignored"}'
        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        self.assertEqual(result["action"]["verb"], "take")


class TestSystemPrompt(unittest.TestCase):
    """Test system prompt construction."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = JSONProtocolHandler(self.state)

    def test_mock_narrator_has_empty_system_prompt(self):
        """Test that mock narrator has empty system prompt."""
        narrator = MockLLMNarrator(self.handler, ["response"])
        self.assertEqual(narrator.system_prompt, "")


if __name__ == "__main__":
    unittest.main()
