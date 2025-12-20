"""Mock LLM narrator for testing.

This module provides a MockLLMNarrator that bypasses actual LLM API calls,
returning predetermined responses for testing narrator logic.
"""

from typing import Dict, Any, Optional

from src.llm_narrator import LLMNarrator
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager


class MockLLMNarrator(LLMNarrator):
    """Narrator with mocked LLM responses for testing.

    This class bypasses the actual LLM API and returns predetermined responses,
    useful for testing the narrator logic without API calls.

    As of Phase 5 (Narration API), verbosity determination and visit tracking are
    handled by LLMProtocolHandler. Access handler.visited_locations and
    handler.examined_entities for tracking tests.
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

        # Store merged vocabulary for parser
        self.merged_vocabulary = self._get_merged_vocabulary(vocabulary)
        self.parser = self._create_parser(self.merged_vocabulary)

    @property
    def visited_locations(self) -> set:
        """Proxy to handler's visited_locations for backward-compatible tests."""
        return self.handler.visited_locations

    @property
    def examined_entities(self) -> set:
        """Proxy to handler's examined_entities for backward-compatible tests."""
        return self.handler.examined_entities

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
