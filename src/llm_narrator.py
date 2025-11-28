"""LLM Narrator module for text adventure games.

Provides a thin layer between natural language input and the JSON protocol,
translating player input to commands and game results to narrative prose.
"""

import json
import logging
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from src.llm_protocol import JSONProtocolHandler
from src.behavior_manager import BehaviorManager
from src.parser import Parser
from src.parsed_command import ParsedCommand


# Default system prompt location
DEFAULT_PROMPT_FILE = Path(__file__).parent.parent / "examples" / "narrator_prompt.txt"
# Default vocabulary file location
DEFAULT_VOCABULARY_FILE = Path(__file__).parent / "vocabulary.json"


def parsed_to_json(result: ParsedCommand) -> Dict[str, Any]:
    """Convert ParsedCommand to JSON protocol format.

    Passes WordEntry objects for object/indirect_object to preserve
    vocabulary synonyms for entity matching. Verbs, directions, and
    adjectives use .word since they don't need synonym matching.

    Args:
        result: Parsed command from the Parser

    Returns:
        JSON protocol dict for the command
    """
    action = {"verb": result.verb.word}

    if result.direct_object:
        # Pass full WordEntry to preserve synonyms for entity matching
        action["object"] = result.direct_object
    if result.direct_adjective:
        action["adjective"] = result.direct_adjective.word
    if result.direction:
        action["direction"] = result.direction.word
    if result.indirect_object:
        # Pass full WordEntry to preserve synonyms for entity matching
        action["indirect_object"] = result.indirect_object
    if result.indirect_adjective:
        action["indirect_adjective"] = result.indirect_adjective.word

    return {"type": "command", "action": action}


class LLMNarrator:
    """Translates between natural language and the JSON protocol."""

    def __init__(self, api_key: str, json_handler: JSONProtocolHandler,
                 model: str = "claude-3-5-haiku-20241022",
                 prompt_file: Optional[Path] = None,
                 behavior_manager: Optional[BehaviorManager] = None,
                 vocabulary: Optional[Dict[str, Any]] = None):
        """Initialize the narrator.

        Args:
            api_key: Anthropic API key
            json_handler: JSONProtocolHandler for game engine communication
            model: Model to use for generation
            prompt_file: Optional path to custom system prompt file
            behavior_manager: Optional BehaviorManager to get merged vocabulary
            vocabulary: Optional merged vocabulary dict (if not provided, loads default)
        """
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic library is required. Install with: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.handler = json_handler
        self.model = model
        self.behavior_manager = behavior_manager
        self.system_prompt = self._load_system_prompt(prompt_file)
        self.parser = self._create_parser(vocabulary)

    def _create_parser(self, vocabulary: Optional[Dict[str, Any]] = None) -> Parser:
        """Create a Parser with merged vocabulary.

        Args:
            vocabulary: Optional pre-merged vocabulary dict

        Returns:
            Parser instance ready to parse commands
        """
        if vocabulary is None:
            # Load base vocabulary
            if DEFAULT_VOCABULARY_FILE.exists():
                try:
                    vocabulary = json.loads(DEFAULT_VOCABULARY_FILE.read_text())
                except (json.JSONDecodeError, IOError):
                    vocabulary = {"verbs": [], "nouns": [], "directions": []}
            else:
                vocabulary = {"verbs": [], "nouns": [], "directions": []}

            # Merge with behavior module vocabulary if available
            if self.behavior_manager:
                vocabulary = self.behavior_manager.get_merged_vocabulary(vocabulary)

        # Write vocabulary to temp file for Parser (it requires a file path)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(vocabulary, f)
            vocab_path = f.name

        parser = Parser(vocab_path)
        Path(vocab_path).unlink()  # Clean up temp file
        return parser

    def process_turn(self, player_input: str) -> str:
        """Process one turn: input -> command -> result -> narrative.

        Uses a fast local parser for simple commands (directions, common verbs)
        and falls back to LLM for complex/ambiguous input.

        Args:
            player_input: Natural language input from player

        Returns:
            Narrative description of what happened
        """
        # 1. Try fast local parsing first
        parsed = self.parser.parse_command(player_input)

        if parsed is not None:
            # Convert ParsedCommand to JSON protocol format
            if parsed.direction and not parsed.verb:
                # Bare direction (e.g., "north") -> go command
                json_cmd = {"type": "command", "action": {"verb": "go", "direction": parsed.direction.word}}
            else:
                json_cmd = parsed_to_json(parsed)
            logger.debug(f"Local parse: {player_input!r} -> {json_cmd}")
        else:
            # Fall back to LLM for complex input
            logger.debug(f"LLM parse needed for: {player_input!r}")
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

        Uses prompt caching for the system prompt to reduce latency and costs.
        The system prompt is marked with cache_control to enable caching across
        multiple requests within the cache TTL (currently 5 minutes).

        Args:
            user_message: The message to send

        Returns:
            The LLM's response text
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=[
                    {
                        "type": "text",
                        "text": self.system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{"role": "user", "content": user_message}]
            )
            # Log cache statistics for debugging
            usage = response.usage
            cache_read = getattr(usage, 'cache_read_input_tokens', 0)
            cache_creation = getattr(usage, 'cache_creation_input_tokens', 0)
            logger.debug(
                f"API call - input: {usage.input_tokens}, output: {usage.output_tokens}, "
                f"cache_read: {cache_read}, cache_creation: {cache_creation}"
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
        # Load base prompt
        base_prompt = None

        # Try custom file first
        if prompt_file and prompt_file.exists():
            base_prompt = prompt_file.read_text()
        # Try default file
        elif DEFAULT_PROMPT_FILE.exists():
            base_prompt = DEFAULT_PROMPT_FILE.read_text()
        else:
            # Fall back to minimal embedded prompt
            base_prompt = """You are the narrator for an interactive text adventure game.

When asked to generate a command, respond with ONLY a JSON block:
```json
{"type": "command", "action": {"verb": "take", "object": "sword"}}
```

{{VOCABULARY}}

When asked to narrate a result, use the llm_context to create 2-4 sentences of
atmospheric prose. Use traits for physical details and state_variants for
context-specific phrasing.

Keep the tone consistent with a classic text adventure - evocative but concise."""

        # Load vocabulary and inject into prompt
        vocab_section = self._build_vocabulary_section()
        if "{{VOCABULARY}}" in base_prompt:
            return base_prompt.replace("{{VOCABULARY}}", vocab_section)
        else:
            # Append vocabulary section if no placeholder found
            return base_prompt + "\n\n" + vocab_section

    def _build_vocabulary_section(self) -> str:
        """Build a minimal vocabulary section for the system prompt.

        Returns just verb names. The model can query for full details if needed.

        Returns:
            Compact string listing available verbs
        """
        if not DEFAULT_VOCABULARY_FILE.exists():
            return "Available verbs: take, drop, examine, go, open, close, unlock, lock, look, inventory"

        try:
            base_vocab = json.loads(DEFAULT_VOCABULARY_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            return "Available verbs: take, drop, examine, go, open, close, unlock, lock, look, inventory"

        # Merge with behavior module vocabulary if available
        if self.behavior_manager:
            vocab = self.behavior_manager.get_merged_vocabulary(base_vocab)
        else:
            vocab = base_vocab

        # Just list verb names
        verbs = [v["word"] for v in vocab.get("verbs", [])]
        directions = [d["word"] for d in vocab.get("directions", [])]

        return f"Available verbs: {', '.join(verbs)}\nDirections: {', '.join(directions)}"


class MockLLMNarrator(LLMNarrator):
    """Narrator with mocked LLM responses for testing.

    This class bypasses the actual LLM API and returns predetermined responses,
    useful for testing the narrator logic without API calls.
    """

    def __init__(self, json_handler: JSONProtocolHandler, responses: list,
                 behavior_manager: Optional[BehaviorManager] = None,
                 vocabulary: Optional[Dict[str, Any]] = None):
        """Initialize mock narrator.

        Args:
            json_handler: JSONProtocolHandler for game engine communication
            responses: List of responses to return in sequence
            behavior_manager: Optional BehaviorManager to get merged vocabulary
            vocabulary: Optional merged vocabulary dict (if not provided, loads default)
        """
        self.handler = json_handler
        self.responses = responses
        self.call_count = 0
        self.system_prompt = ""  # Not used in mock
        self.calls = []  # Track calls for testing
        self.behavior_manager = behavior_manager
        self.parser = self._create_parser(vocabulary)

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
