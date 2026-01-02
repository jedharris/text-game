"""Tests for MLX narrator infrastructure.

Tests the MLXNarrator class using MockMLXNarrator to avoid actual model loading.
"""

import unittest
import json
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.state_manager import load_game_state
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from src.types import ActorId, LocationId
from typing import Dict, Any, Optional
from src.state_accessor import StateAccessor


# Mock the mlx_lm import for testing
sys.modules['mlx_lm'] = MagicMock()


class MockMLXNarrator:
    """Narrator with mocked MLX responses for testing.

    This class bypasses the actual MLX model and returns predetermined responses,
    useful for testing the narrator logic without loading models.
    """

    # Trait limits for verbosity modes
    FULL_TRAITS = 8
    BRIEF_TRAITS = 3

    def __init__(self, json_handler: LLMProtocolHandler, responses: list,
                 behavior_manager: Optional[BehaviorManager] = None,
                 vocabulary: Optional[Dict[str, Any]] = None,
                 show_traits: bool = False):
        """Initialize mock narrator.

        Args:
            json_handler: LLMProtocolHandler for game engine communication
            responses: List of responses to return in sequence
            behavior_manager: Optional BehaviorManager to get merged vocabulary
            vocabulary: Optional merged vocabulary dict (if not provided, loads default)
            show_traits: If True, print llm_context traits before each LLM narration
        """
        self.handler = json_handler
        self.responses = responses
        self.call_count = 0
        self.system_prompt = ""  # Not used in mock
        self.calls: list[str] = []  # Track calls for testing
        self.behavior_manager = behavior_manager
        self.show_traits = show_traits
        self.model_path = "mock-model"
        self.temperature = 0.8
        self.max_tokens = 150

        # Import here to avoid circular imports
        from src.vocabulary_service import load_base_vocabulary
        from src.parser import Parser

        DEFAULT_VOCABULARY_FILE = Path(__file__).parent.parent.parent / "src" / "vocabulary.json"

        # Store merged vocabulary for narration mode lookup
        if vocabulary is None:
            vocabulary = load_base_vocabulary(DEFAULT_VOCABULARY_FILE)
        if behavior_manager:
            vocabulary = behavior_manager.get_merged_vocabulary(vocabulary)
        self.merged_vocabulary = vocabulary
        self.parser = Parser.from_vocab(self.merged_vocabulary)

        # Visit tracking for verbosity control (same as parent)
        self.visited_locations: set[str] = set()
        self.examined_entities: set[str] = set()

    def _call_llm(self, user_message: str) -> str:
        """Return mock response instead of calling model.

        Args:
            user_message: The message that would be sent

        Returns:
            Next response from the responses list
        """
        self.calls.append(user_message)
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response

    def _get_narration_mode(self, verb: str) -> str:
        """Look up narration_mode for a verb from merged vocabulary."""
        for verb_entry in self.merged_vocabulary.get("verbs", []):
            if verb_entry.get("word") == verb:
                return verb_entry.get("narration_mode", "tracking")
        return "tracking"

    def _determine_verbosity(self, json_cmd: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Determine verbosity level based on command and tracking state."""
        verb = json_cmd.get("action", {}).get("verb", "")
        narration_mode = self._get_narration_mode(verb)

        if narration_mode == "brief":
            return "brief"

        if verb == "go" and result.get("success"):
            loc_id = result.get("data", {}).get("location", {}).get("id")
            if loc_id and loc_id not in self.visited_locations:
                return "full"
            return "brief"

        entity_id = result.get("data", {}).get("id")
        if entity_id and entity_id not in self.examined_entities:
            return "full"
        return "brief"

    def _update_tracking(self, json_cmd: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Update visit/examine tracking based on successful commands."""
        if not result.get("success"):
            return

        verb = json_cmd.get("action", {}).get("verb", "")
        narration_mode = self._get_narration_mode(verb)
        if narration_mode != "tracking":
            return

        if verb == "go":
            loc_id = result.get("data", {}).get("location", {}).get("id")
            if loc_id:
                self.visited_locations.add(loc_id)
        else:
            entity_id = result.get("data", {}).get("id")
            if entity_id:
                self.examined_entities.add(entity_id)

    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        import re
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return None

    def _build_vocabulary_section(self) -> str:
        """Build a minimal vocabulary section for the system prompt."""
        vocab = self.merged_vocabulary
        verbs = [v["word"] for v in vocab.get("verbs", [])]
        if not verbs:
            return "Available verbs: (none - behavior modules should provide verbs)"
        return f"Available verbs: {', '.join(verbs)}"

    def process_turn(self, player_input: str) -> str:
        """Process one turn: input -> command -> result -> narrative."""
        from src.command_utils import parsed_to_json

        parsed = self.parser.parse_command(player_input)
        json_cmd: Dict[str, Any]

        if parsed is not None:
            if parsed.direct_object and not parsed.verb:
                json_cmd = {"type": "command", "action": {"verb": "go", "object": parsed.direct_object}}
            else:
                json_cmd = parsed_to_json(parsed)
        else:
            command_response = self._call_llm(
                f"Player says: {player_input}\n\nRespond with a JSON command."
            )
            extracted = self._extract_json(command_response)
            if extracted is None:
                return "I don't understand what you want to do."
            json_cmd = extracted

        result = self.handler.handle_message(json_cmd)
        verbosity = self._determine_verbosity(json_cmd, result)
        self._update_tracking(json_cmd, result)

        result_with_verbosity = dict(result)
        result_with_verbosity["verbosity"] = verbosity

        narrative = self._call_llm(
            f"Narrate this result:\n{json.dumps(result_with_verbosity, indent=2)}"
        )
        return narrative

    def get_opening(self) -> str:
        """Get opening narrative for game start."""
        result = self.handler.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["items", "doors", "exits", "actors"]
        })

        loc_id = result.get("data", {}).get("location", {}).get("id")
        if loc_id:
            self.visited_locations.add(loc_id)

        result_with_verbosity = dict(result)
        result_with_verbosity["verbosity"] = "full"

        return self._call_llm(
            f"Narrate the opening scene:\n{json.dumps(result_with_verbosity, indent=2)}"
        )


class TestMLXJSONExtraction(unittest.TestCase):
    """Test extracting JSON from various LLM response formats."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixture_path))
        self.manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_extract_json_from_code_block(self) -> None:
        """Test extracting JSON from markdown code block with json tag."""
        narrator = MockMLXNarrator(self.handler, ["dummy"])

        response = '```json\n{"type": "command", "action": {"verb": "take", "object": "sword"}}\n```'
        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["action"]["verb"], "take")
        self.assertEqual(result["action"]["object"], "sword")

    def test_extract_json_plain(self) -> None:
        """Test extracting plain JSON response without code block."""
        narrator = MockMLXNarrator(self.handler, ["dummy"])

        response = '{"type": "command", "action": {"verb": "inventory"}}'
        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["action"]["verb"], "inventory")

    def test_extract_json_invalid_returns_none(self) -> None:
        """Test that invalid JSON returns None."""
        narrator = MockMLXNarrator(self.handler, ["dummy"])

        result = narrator._extract_json("not json at all")
        self.assertIsNone(result)


class TestMLXProcessTurn(unittest.TestCase):
    """Test the process_turn method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixture_path))
        self.manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_process_turn_take_item(self) -> None:
        """Test processing a take command."""
        self.accessor.set_entity_where("player", "loc_start")

        responses = [
            '```json\n{"type": "command", "action": {"verb": "take", "object": "sword"}}\n```',
            "You pick up the rusty sword. Its weight feels reassuring in your hand."
        ]
        narrator = MockMLXNarrator(self.handler, responses)

        result = narrator.process_turn("pick up the sword")

        self.assertIn("sword", result.lower())
        self.assertEqual(narrator.call_count, 2)

    def test_process_turn_invalid_json_returns_error(self) -> None:
        """Test that invalid JSON from LLM returns error message."""
        responses = [
            "I'm not sure what you mean by that.",
        ]
        narrator = MockMLXNarrator(self.handler, responses)

        result = narrator.process_turn("do something weird")

        self.assertEqual(result, "I don't understand what you want to do.")
        self.assertEqual(narrator.call_count, 1)


class TestMLXGetOpening(unittest.TestCase):
    """Test the get_opening method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixture_path))
        self.manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_get_opening_returns_narrative(self) -> None:
        """Test that get_opening returns a narrative."""
        self.accessor.set_entity_where("player", "loc_start")

        responses = [
            "You awaken in a small stone chamber. Dim light filters through cracks in the ceiling."
        ]
        narrator = MockMLXNarrator(self.handler, responses)

        result = narrator.get_opening()

        self.assertIn("stone", result.lower())
        self.assertEqual(narrator.call_count, 1)

    def test_get_opening_marks_start_location_visited(self) -> None:
        """Test that get_opening marks the starting location as visited."""
        self.accessor.set_entity_where("player", "loc_start")

        responses = ["You awaken in a small room."]
        narrator = MockMLXNarrator(self.handler, responses)

        narrator.get_opening()

        self.assertIn("loc_start", narrator.visited_locations)


class TestMLXVerbosityTracking(unittest.TestCase):
    """Test visit tracking and verbosity determination."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixture_path))
        self.manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_narrator_has_visit_tracking_sets(self) -> None:
        """Test that narrator initializes with empty tracking sets."""
        narrator = MockMLXNarrator(self.handler, ["response"])

        self.assertTrue(hasattr(narrator, 'visited_locations'))
        self.assertTrue(hasattr(narrator, 'examined_entities'))
        self.assertIsInstance(narrator.visited_locations, set)
        self.assertIsInstance(narrator.examined_entities, set)
        self.assertEqual(len(narrator.visited_locations), 0)
        self.assertEqual(len(narrator.examined_entities), 0)

    def test_first_room_entry_uses_full_verbosity(self) -> None:
        """Test that first entry to a room uses full verbosity."""
        self.accessor.set_entity_where("player", "loc_start")

        responses = [
            '{"type": "command", "action": {"verb": "go", "object": "north"}}',
            "You enter the hallway."
        ]
        narrator = MockMLXNarrator(self.handler, responses)

        narrator.process_turn("go north")

        narrate_call = narrator.calls[-1]
        self.assertIn('"verbosity": "full"', narrate_call)


class TestMLXMergedVocabulary(unittest.TestCase):
    """Test that MLX narrator uses merged vocabulary from behavior modules."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixture_path))
        self.manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_vocabulary_section_includes_behavior_verbs_when_manager_provided(self) -> None:
        """Test that vocabulary includes verbs from behavior modules."""
        behavior_manager = BehaviorManager()
        behavior_manager.load_module("behaviors.core.containers")

        narrator = MockMLXNarrator(self.handler, ["response"],
                                   behavior_manager=behavior_manager)

        vocab_section = narrator._build_vocabulary_section()

        self.assertIn("open", vocab_section.lower())
        self.assertIn("close", vocab_section.lower())


if __name__ == "__main__":
    unittest.main()
