"""LLM Narrator module for text adventure games.

Provides a thin layer between natural language input and the JSON protocol,
translating player input to commands and game results to narrative prose.
"""

import json
import re
import time
from pathlib import Path
from typing import Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from src.json_protocol import JSONProtocolHandler


# Default system prompt location
DEFAULT_PROMPT_FILE = Path(__file__).parent.parent / "examples" / "narrator_prompt.txt"


class LLMNarrator:
    """Translates between natural language and the JSON protocol."""

    def __init__(self, api_key: str, json_handler: JSONProtocolHandler,
                 model: str = "claude-sonnet-4-20250514",
                 prompt_file: Optional[Path] = None):
        """Initialize the narrator.

        Args:
            api_key: Anthropic API key
            json_handler: JSONProtocolHandler for game engine communication
            model: Model to use for generation
            prompt_file: Optional path to custom system prompt file
        """
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic library is required. Install with: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.handler = json_handler
        self.model = model
        self.system_prompt = self._load_system_prompt(prompt_file)

    def process_turn(self, player_input: str) -> str:
        """Process one turn: input -> command -> result -> narrative.

        Args:
            player_input: Natural language input from player

        Returns:
            Narrative description of what happened
        """
        # 1. Get JSON command from LLM
        command_response = self._call_llm(
            f"Player says: {player_input}\n\nRespond with a JSON command."
        )
        json_cmd = self._extract_json(command_response)

        if json_cmd is None:
            return "I don't understand what you want to do."

        # 2. Execute command via game engine
        result = self.handler.handle_message(json_cmd)

        # 3. Get narrative from LLM
        narrative = self._call_llm(
            f"Narrate this result:\n{json.dumps(result, indent=2)}"
        )

        return narrative

    def get_opening(self) -> str:
        """Get opening narrative for game start.

        Returns:
            Narrative description of the opening scene
        """
        # Query current location
        result = self.handler.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["items", "doors", "npcs"]
        })

        return self._call_llm(
            f"Narrate the opening scene:\n{json.dumps(result, indent=2)}"
        )

    def _call_llm(self, user_message: str) -> str:
        """Make an API call to the LLM.

        Args:
            user_message: The message to send

        Returns:
            The LLM's response text
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            return response.content[0].text
        except anthropic.RateLimitError:
            time.sleep(1)
            return self._call_llm(user_message)  # Simple retry
        except anthropic.APIError as e:
            return f"[Narrator unavailable: {e}]"

    def _extract_json(self, response: str) -> Optional[dict]:
        """Extract JSON from LLM response.

        Args:
            response: The LLM response text

        Returns:
            Parsed JSON dict, or None if extraction failed
        """
        # Look for JSON in code blocks
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try parsing the whole response
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return None

    def _load_system_prompt(self, prompt_file: Optional[Path] = None) -> str:
        """Load the system prompt from file or use default.

        Args:
            prompt_file: Optional path to custom prompt file

        Returns:
            System prompt string
        """
        # Try custom file first
        if prompt_file and prompt_file.exists():
            return prompt_file.read_text()

        # Try default file
        if DEFAULT_PROMPT_FILE.exists():
            return DEFAULT_PROMPT_FILE.read_text()

        # Fall back to minimal embedded prompt
        return """You are the narrator for an interactive text adventure game.

When asked to generate a command, respond with ONLY a JSON block:
```json
{"type": "command", "action": {"verb": "take", "object": "sword"}}
```

Available verbs: take, drop, examine, go, open, close, unlock, lock, look, inventory
For movement: {"type": "command", "action": {"verb": "go", "direction": "north"}}

When asked to narrate a result, use the llm_context to create 2-4 sentences of
atmospheric prose. Use traits for physical details and state_variants for
context-specific phrasing.

Keep the tone consistent with a classic text adventure - evocative but concise."""


class MockLLMNarrator(LLMNarrator):
    """Narrator with mocked LLM responses for testing.

    This class bypasses the actual LLM API and returns predetermined responses,
    useful for testing the narrator logic without API calls.
    """

    def __init__(self, json_handler: JSONProtocolHandler, responses: list):
        """Initialize mock narrator.

        Args:
            json_handler: JSONProtocolHandler for game engine communication
            responses: List of responses to return in sequence
        """
        self.handler = json_handler
        self.responses = responses
        self.call_count = 0
        self.system_prompt = ""  # Not used in mock
        self.calls = []  # Track calls for testing

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
