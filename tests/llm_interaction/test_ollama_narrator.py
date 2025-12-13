"""Tests for Ollama narrator infrastructure.

Tests the OllamaNarrator class using MockOllamaNarrator to avoid actual API calls.
"""

import unittest
import json
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.state_manager import load_game_state
from src.llm_protocol import LLMProtocolHandler
from src.ollama_narrator import OllamaNarrator
from src.behavior_manager import BehaviorManager
from src.types import ActorId, LocationId
from typing import Dict, Any, Optional


class MockOllamaNarrator(OllamaNarrator):
    """Narrator with mocked Ollama responses for testing.

    This class bypasses the actual Ollama API and returns predetermined responses,
    useful for testing the narrator logic without API calls.
    """

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
        self.model = "mock-model"
        self.ollama_url = "http://localhost:11434"
        self.temperature = 0.8
        self.num_predict = 150

        # Store merged vocabulary for narration mode lookup
        self.merged_vocabulary = self._get_merged_vocabulary(vocabulary)
        self.parser = self._create_parser(self.merged_vocabulary)

        # Visit tracking for verbosity control (same as parent)
        self.visited_locations: set[str] = set()
        self.examined_entities: set[str] = set()

    def _call_llm(self, user_message: str) -> str:
        """Return mock response instead of calling API.

        Args:
            user_message: The message that would be sent

        Returns:
            Next response from the responses list
        """
        self.calls.append(user_message)
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response

    def check_connection(self) -> bool:
        """Mock always returns True."""
        return True


class TestOllamaJSONExtraction(unittest.TestCase):
    """Test extracting JSON from various LLM response formats."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = LLMProtocolHandler(self.state)

    def test_extract_json_from_code_block(self) -> None:
        """Test extracting JSON from markdown code block with json tag."""
        narrator = MockOllamaNarrator(self.handler, ["dummy"])

        response = '```json\n{"type": "command", "action": {"verb": "take", "object": "sword"}}\n```'
        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["action"]["verb"], "take")
        self.assertEqual(result["action"]["object"], "sword")

    def test_extract_json_plain(self) -> None:
        """Test extracting plain JSON response without code block."""
        narrator = MockOllamaNarrator(self.handler, ["dummy"])

        response = '{"type": "command", "action": {"verb": "inventory"}}'
        result = narrator._extract_json(response)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["action"]["verb"], "inventory")

    def test_extract_json_invalid_returns_none(self) -> None:
        """Test that invalid JSON returns None."""
        narrator = MockOllamaNarrator(self.handler, ["dummy"])

        result = narrator._extract_json("not json at all")
        self.assertIsNone(result)


class TestOllamaProcessTurn(unittest.TestCase):
    """Test the process_turn method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = LLMProtocolHandler(self.state)

    def test_process_turn_take_item(self) -> None:
        """Test processing a take command."""
        # Ensure player is in loc_start where sword is
        self.state.actors[ActorId("player")].location = LocationId("loc_start")

        # Mock responses: first for command generation, second for narration
        responses = [
            '```json\n{"type": "command", "action": {"verb": "take", "object": "sword"}}\n```',
            "You pick up the rusty sword. Its weight feels reassuring in your hand."
        ]
        narrator = MockOllamaNarrator(self.handler, responses)

        result = narrator.process_turn("pick up the sword")

        # Should return narrative
        self.assertIn("sword", result.lower())
        # Should have made 2 LLM calls
        self.assertEqual(narrator.call_count, 2)

    def test_process_turn_invalid_json_returns_error(self) -> None:
        """Test that invalid JSON from LLM returns error message."""
        responses = [
            "I'm not sure what you mean by that.",  # Invalid - no JSON
        ]
        narrator = MockOllamaNarrator(self.handler, responses)

        result = narrator.process_turn("do something weird")

        self.assertEqual(result, "I don't understand what you want to do.")
        # Only one call since extraction failed
        self.assertEqual(narrator.call_count, 1)


class TestOllamaGetOpening(unittest.TestCase):
    """Test the get_opening method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = LLMProtocolHandler(self.state)

    def test_get_opening_returns_narrative(self) -> None:
        """Test that get_opening returns a narrative."""
        self.state.actors[ActorId("player")].location = LocationId("loc_start")

        responses = [
            "You awaken in a small stone chamber. Dim light filters through cracks in the ceiling."
        ]
        narrator = MockOllamaNarrator(self.handler, responses)

        result = narrator.get_opening()

        self.assertIn("stone", result.lower())
        self.assertEqual(narrator.call_count, 1)

    def test_get_opening_marks_start_location_visited(self) -> None:
        """Test that get_opening marks the starting location as visited."""
        self.state.actors[ActorId("player")].location = LocationId("loc_start")

        responses = ["You awaken in a small room."]
        narrator = MockOllamaNarrator(self.handler, responses)

        narrator.get_opening()

        self.assertIn("loc_start", narrator.visited_locations)


class TestOllamaVerbosityTracking(unittest.TestCase):
    """Test visit tracking and verbosity determination."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = LLMProtocolHandler(self.state)

    def test_narrator_has_visit_tracking_sets(self) -> None:
        """Test that narrator initializes with empty tracking sets."""
        narrator = MockOllamaNarrator(self.handler, ["response"])

        self.assertTrue(hasattr(narrator, 'visited_locations'))
        self.assertTrue(hasattr(narrator, 'examined_entities'))
        self.assertIsInstance(narrator.visited_locations, set)
        self.assertIsInstance(narrator.examined_entities, set)
        self.assertEqual(len(narrator.visited_locations), 0)
        self.assertEqual(len(narrator.examined_entities), 0)

    def test_first_room_entry_uses_full_verbosity(self) -> None:
        """Test that first entry to a room uses full verbosity."""
        self.state.actors[ActorId("player")].location = LocationId("loc_start")

        responses = [
            '{"type": "command", "action": {"verb": "go", "object": "north"}}',
            "You enter the hallway."
        ]
        narrator = MockOllamaNarrator(self.handler, responses)

        narrator.process_turn("go north")

        # Check that the narration request includes full verbosity
        narrate_call = narrator.calls[-1]  # Last call is narration
        self.assertIn('"verbosity": "full"', narrate_call)


class TestOllamaConnectionCheck(unittest.TestCase):
    """Test Ollama connection checking."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = LLMProtocolHandler(self.state)

    @patch('src.ollama_narrator.requests.get')
    def test_check_connection_success(self, mock_get: Mock) -> None:
        """Test that check_connection returns True when Ollama is running."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Create a real OllamaNarrator (not mock) to test actual check_connection
        # We need to avoid loading the system prompt, so patch that too
        with patch.object(OllamaNarrator, '__init__', lambda self, **kwargs: None):
            narrator = OllamaNarrator.__new__(OllamaNarrator)
            narrator.ollama_url = "http://localhost:11434"

            result = narrator.check_connection()

            self.assertTrue(result)
            mock_get.assert_called_once_with(
                "http://localhost:11434/api/tags",
                timeout=5
            )

    @patch('src.ollama_narrator.requests.get')
    def test_check_connection_failure(self, mock_get: Mock) -> None:
        """Test that check_connection returns False when Ollama is not running."""
        import requests  # type: ignore[import-untyped]
        mock_get.side_effect = requests.ConnectionError()

        with patch.object(OllamaNarrator, '__init__', lambda self, **kwargs: None):
            narrator = OllamaNarrator.__new__(OllamaNarrator)
            narrator.ollama_url = "http://localhost:11434"

            result = narrator.check_connection()

            self.assertFalse(result)


class TestOllamaAPICall(unittest.TestCase):
    """Test actual Ollama API calls (mocked at requests level)."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = LLMProtocolHandler(self.state)

    @patch('src.ollama_narrator.requests.post')
    def test_call_llm_constructs_correct_request(self, mock_post: Mock) -> None:
        """Test that _call_llm sends correct request to Ollama."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Chat endpoint returns message.content instead of response
        mock_response.json.return_value = {
            "message": {"content": "Test response from Ollama"},
            "done": True
        }
        mock_post.return_value = mock_response

        with patch.object(OllamaNarrator, '__init__', lambda self, **kwargs: None):
            narrator = OllamaNarrator.__new__(OllamaNarrator)
            narrator.ollama_url = "http://localhost:11434"
            narrator.model = "mistral:7b-instruct-q8_0"
            narrator.system_prompt = "You are a game narrator."
            narrator.temperature = 0.8
            narrator.num_predict = 150

            result = narrator._call_llm("Test message")

            self.assertEqual(result, "Test response from Ollama")

            # Verify the request was constructed correctly (now uses /api/chat)
            call_args = mock_post.call_args
            self.assertEqual(call_args[0][0], "http://localhost:11434/api/chat")

            request_body = call_args[1]['json']
            self.assertEqual(request_body['model'], "mistral:7b-instruct-q8_0")
            # Chat endpoint uses messages array with system and user roles
            messages = request_body['messages']
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0]['role'], 'system')
            self.assertEqual(messages[0]['content'], "You are a game narrator.")
            self.assertEqual(messages[1]['role'], 'user')
            self.assertEqual(messages[1]['content'], "Test message")
            self.assertFalse(request_body['stream'])
            self.assertEqual(request_body['keep_alive'], -1)
            self.assertEqual(request_body['options']['temperature'], 0.8)
            self.assertEqual(request_body['options']['num_predict'], 150)

    @patch('src.ollama_narrator.requests.post')
    def test_call_llm_handles_timeout(self, mock_post: Mock) -> None:
        """Test that _call_llm handles timeout gracefully."""
        import requests
        mock_post.side_effect = requests.Timeout()

        with patch.object(OllamaNarrator, '__init__', lambda self, **kwargs: None):
            narrator = OllamaNarrator.__new__(OllamaNarrator)
            narrator.ollama_url = "http://localhost:11434"
            narrator.model = "mistral:7b-instruct-q8_0"
            narrator.system_prompt = "System prompt"
            narrator.temperature = 0.8
            narrator.num_predict = 150

            result = narrator._call_llm("Test message")

            self.assertIn("timeout", result.lower())

    @patch('src.ollama_narrator.requests.post')
    def test_call_llm_handles_connection_error(self, mock_post: Mock) -> None:
        """Test that _call_llm handles connection error gracefully."""
        import requests
        mock_post.side_effect = requests.ConnectionError()

        with patch.object(OllamaNarrator, '__init__', lambda self, **kwargs: None):
            narrator = OllamaNarrator.__new__(OllamaNarrator)
            narrator.ollama_url = "http://localhost:11434"
            narrator.model = "mistral:7b-instruct-q8_0"
            narrator.system_prompt = "System prompt"
            narrator.temperature = 0.8
            narrator.num_predict = 150

            result = narrator._call_llm("Test message")

            self.assertIn("unavailable", result.lower())


class TestOllamaMergedVocabulary(unittest.TestCase):
    """Test that Ollama narrator uses merged vocabulary from behavior modules."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixture_path))
        self.handler = LLMProtocolHandler(self.state)

    def test_vocabulary_section_includes_behavior_verbs_when_manager_provided(self) -> None:
        """Test that vocabulary includes verbs from behavior modules."""
        behavior_manager = BehaviorManager()
        behavior_manager.load_module("behaviors.core.containers")

        narrator = MockOllamaNarrator(self.handler, ["response"],
                                      behavior_manager=behavior_manager)

        vocab_section = narrator._build_vocabulary_section()

        # Should include verbs from containers.py (open, close)
        self.assertIn("open", vocab_section.lower())
        self.assertIn("close", vocab_section.lower())


if __name__ == "__main__":
    unittest.main()
