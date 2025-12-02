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

from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from src.parser import Parser
from src.parsed_command import ParsedCommand


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

    # Verbs that always use brief verbosity regardless of first/subsequent
    BRIEF_VERBS = {'drop', 'put', 'close', 'lock', 'extinguish', 'attack'}

    # Verbs that use full verbosity on first occurrence, brief on subsequent
    TRACKING_VERBS = {'go', 'examine', 'look', 'take', 'open', 'unlock', 'light', 'eat', 'drink'}

    # Trait limits for verbosity modes
    FULL_TRAITS = 8
    BRIEF_TRAITS = 3

    def __init__(self, api_key: str, json_handler: LLMProtocolHandler,
                 model: str = "claude-3-5-haiku-20241022",
                 prompt_file: Path = None,
                 behavior_manager: Optional[BehaviorManager] = None,
                 vocabulary: Optional[Dict[str, Any]] = None,
                 show_traits: bool = False):
        """Initialize the narrator.

        Args:
            api_key: Anthropic API key
            json_handler: LLMProtocolHandler for game engine communication
            model: Model to use for generation
            prompt_file: Path to system prompt file (required, must exist)
            behavior_manager: Optional BehaviorManager to get merged vocabulary
            vocabulary: Optional merged vocabulary dict (if not provided, loads default)
            show_traits: If True, print llm_context traits before each LLM narration

        Raises:
            FileNotFoundError: If prompt_file does not exist
        """
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic library is required. Install with: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.handler = json_handler
        self.model = model
        self.behavior_manager = behavior_manager
        self.show_traits = show_traits
        self.system_prompt = self._load_system_prompt(prompt_file)
        self.parser = self._create_parser(vocabulary)

        # Visit tracking for verbosity control
        self.visited_locations: set = set()
        self.examined_entities: set = set()

    def _print_traits(self, result: Dict[str, Any]) -> None:
        """Print llm_context traits from a result if show_traits is enabled.

        Searches for llm_context in the result at various nesting levels:
        - Top-level llm_context (command results)
        - data.llm_context (command results with data)
        - data.location.llm_context (location queries)
        - Entities in items, doors, actors lists

        Args:
            result: JSON result from game engine
        """
        if not self.show_traits:
            return

        def collect_traits(obj: Any, prefix: str = "") -> list:
            """Recursively collect traits from nested structures."""
            collected = []
            if not isinstance(obj, dict):
                return collected

            # Check for llm_context at this level
            llm_context = obj.get("llm_context")
            if llm_context and "traits" in llm_context:
                name = obj.get("name", prefix.rstrip(".") or "result")
                collected.append((name, llm_context["traits"]))

            # Recurse into known containers
            for key in ["data", "location"]:
                if key in obj and isinstance(obj[key], dict):
                    collected.extend(collect_traits(obj[key], f"{prefix}{key}."))

            # Recurse into entity lists
            for key in ["items", "doors", "actors", "exits"]:
                if key in obj and isinstance(obj[key], list):
                    for item in obj[key]:
                        collected.extend(collect_traits(item, f"{prefix}{key}."))

            return collected

        all_traits = collect_traits(result)
        for name, traits in all_traits:
            print(f"[{name} traits: {', '.join(traits)}]")

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

        # 3. Determine verbosity and update tracking
        verbosity = self._determine_verbosity(json_cmd, result)
        self._update_tracking(json_cmd, result)

        # 4. Print traits if enabled
        self._print_traits(result)

        # 5. Add verbosity hint to result for LLM
        result_with_verbosity = dict(result)
        result_with_verbosity["verbosity"] = verbosity

        # 6. Get narrative from LLM
        narrative = self._call_llm(
            f"Narrate this result:\n{json.dumps(result_with_verbosity, indent=2)}"
        )

        return narrative

    def _determine_verbosity(self, json_cmd: Dict, result: Dict) -> str:
        """Determine verbosity level based on command and tracking state.

        Args:
            json_cmd: The JSON command that was executed
            result: The result from the game engine

        Returns:
            "full" for first visits/examines, "brief" for subsequent or routine actions
        """
        verb = json_cmd.get("action", {}).get("verb", "")

        # Brief verbs are always brief
        if verb in self.BRIEF_VERBS:
            return "brief"

        # For go/movement: check if destination is new
        if verb == "go" and result.get("success"):
            # Get the new location ID from the result (nested under data.location)
            loc_id = result.get("data", {}).get("location", {}).get("id")
            if loc_id and loc_id not in self.visited_locations:
                return "full"
            return "brief"

        # For other tracking verbs: check if entity is new
        if verb in self.TRACKING_VERBS and verb != "go":
            entity_id = result.get("data", {}).get("id")
            if entity_id and entity_id not in self.examined_entities:
                return "full"
            return "brief"

        # Default to brief for unknown verbs
        return "brief"

    def _update_tracking(self, json_cmd: Dict, result: Dict) -> None:
        """Update visit/examine tracking based on successful commands.

        Args:
            json_cmd: The JSON command that was executed
            result: The result from the game engine
        """
        if not result.get("success"):
            return

        verb = json_cmd.get("action", {}).get("verb", "")

        # Track visited locations on successful movement
        if verb == "go":
            # Location ID is nested under data.location
            loc_id = result.get("data", {}).get("location", {}).get("id")
            if loc_id:
                self.visited_locations.add(loc_id)

        # Track entities for all other tracking verbs
        if verb in self.TRACKING_VERBS and verb != "go":
            entity_id = result.get("data", {}).get("id")
            if entity_id:
                self.examined_entities.add(entity_id)

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

        # Mark starting location as visited
        loc_id = result.get("data", {}).get("location", {}).get("id")
        if loc_id:
            self.visited_locations.add(loc_id)

        # Print traits if enabled
        self._print_traits(result)

        # Opening always uses full verbosity
        result_with_verbosity = dict(result)
        result_with_verbosity["verbosity"] = "full"

        return self._call_llm(
            f"Narrate the opening scene:\n{json.dumps(result_with_verbosity, indent=2)}"
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

    def _load_system_prompt(self, prompt_file: Path) -> str:
        """Load the system prompt from protocol template and game style file.

        Combines the protocol specification from src/narrator_protocol.txt
        with game-specific style guidance from the prompt_file.

        Args:
            prompt_file: Path to game-specific style file (narrator_style.txt)

        Returns:
            Combined system prompt string

        Raises:
            FileNotFoundError: If protocol template or style file does not exist
        """
        # Load protocol template from src/
        protocol_path = Path(__file__).parent / "narrator_protocol.txt"
        if not protocol_path.exists():
            raise FileNotFoundError(
                f"Protocol template not found: {protocol_path}\n"
                "The narrator_protocol.txt file should be in the src/ directory."
            )

        protocol = protocol_path.read_text()

        # Load game-specific style
        if not prompt_file:
            raise FileNotFoundError(
                "prompt_file is required. Each game must have a narrator_style.txt file."
            )

        if not prompt_file.exists():
            raise FileNotFoundError(
                f"Narrator style file not found: {prompt_file}\n"
                "Each game must have a narrator_style.txt file in its directory."
            )

        style = prompt_file.read_text()

        # Combine protocol + style
        base_prompt = f"{protocol}\n\n{style}"

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
