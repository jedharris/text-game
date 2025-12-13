"""Ollama-based Narrator module for text adventure games.

Provides a thin layer between natural language input and the JSON protocol,
translating player input to commands and game results to narrative prose.
Uses local Ollama server instead of Anthropic API.
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from src.command_utils import parsed_to_json
from src.parser import Parser
from src.vocabulary_service import load_base_vocabulary


# Default vocabulary file location
DEFAULT_VOCABULARY_FILE = Path(__file__).parent / "vocabulary.json"

# Default Ollama configuration
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "mistral:7b-instruct-q8_0"


class OllamaNarrator:
    """Translates between natural language and the JSON protocol using Ollama."""

    # Trait limits for verbosity modes
    FULL_TRAITS = 8
    BRIEF_TRAITS = 3

    def __init__(self, json_handler: LLMProtocolHandler,
                 model: str = DEFAULT_MODEL,
                 ollama_url: str = DEFAULT_OLLAMA_URL,
                 prompt_file: Optional[Path] = None,
                 behavior_manager: Optional[BehaviorManager] = None,
                 vocabulary: Optional[Dict[str, Any]] = None,
                 show_traits: bool = False,
                 temperature: float = 0.8,
                 num_predict: int = 150):
        """Initialize the narrator.

        Args:
            json_handler: LLMProtocolHandler for game engine communication
            model: Ollama model to use for generation
            ollama_url: Base URL for Ollama server
            prompt_file: Path to system prompt file (required, must exist)
            behavior_manager: Optional BehaviorManager to get merged vocabulary
            vocabulary: Optional merged vocabulary dict (if not provided, loads default)
            show_traits: If True, print llm_context traits before each LLM narration
            temperature: Temperature for generation (0.0-2.0)
            num_predict: Max tokens to generate

        Raises:
            FileNotFoundError: If prompt_file does not exist
            ConnectionError: If Ollama server is not reachable
        """
        self.handler = json_handler
        self.model = model
        self.ollama_url = ollama_url.rstrip('/')
        self.behavior_manager = behavior_manager
        self.show_traits = show_traits
        self.temperature = temperature
        self.num_predict = num_predict

        # Store merged vocabulary for narration mode lookup (must be before _load_system_prompt)
        self.merged_vocabulary = self._get_merged_vocabulary(vocabulary)
        self.parser = self._create_parser(self.merged_vocabulary)
        assert prompt_file is not None, "prompt_file is required"
        self.system_prompt = self._load_system_prompt(prompt_file)

        # Visit tracking for verbosity control
        self.visited_locations: set[str] = set()
        self.examined_entities: set[str] = set()

    def check_connection(self) -> bool:
        """Check if Ollama server is reachable.

        Returns:
            True if server is reachable, False otherwise
        """
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

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

        def collect_traits(obj: Any, prefix: str = "") -> list[tuple[str, list[str]]]:
            """Recursively collect traits from nested structures."""
            collected: list[tuple[str, list[str]]] = []
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

    def _get_merged_vocabulary(self, vocabulary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get merged vocabulary from base + behaviors.

        Args:
            vocabulary: Optional pre-merged vocabulary dict

        Returns:
            Merged vocabulary dict
        """
        if vocabulary is None:
            # Load base vocabulary
            vocabulary = load_base_vocabulary(DEFAULT_VOCABULARY_FILE)

        # Merge with behavior module vocabulary if available
        if self.behavior_manager:
            vocabulary = self.behavior_manager.get_merged_vocabulary(vocabulary)

        return vocabulary

    def _create_parser(self, vocabulary: Dict[str, Any]) -> Parser:
        """Create a Parser with merged vocabulary.

        Args:
            vocabulary: Merged vocabulary dict

        Returns:
            Parser instance ready to parse commands
        """
        return Parser.from_vocab(vocabulary)

    def process_turn(self, player_input: str) -> str:
        """Process one turn: input -> command -> result -> narrative.

        Uses a fast local parser for simple commands and falls back to
        LLM for complex/ambiguous input.

        Args:
            player_input: Natural language input from player

        Returns:
            Narrative description of what happened
        """
        # 1. Try fast local parsing first
        parsed = self.parser.parse_command(player_input)
        json_cmd: Dict[str, Any]

        if parsed is not None:
            # Convert ParsedCommand to JSON protocol format
            if parsed.direct_object and not parsed.verb:
                # Bare direction (e.g., "north") -> go command
                # Directions are now in direct_object as nouns
                json_cmd = {"type": "command", "action": {"verb": "go", "object": parsed.direct_object}}
            else:
                json_cmd = parsed_to_json(parsed)
            logger.debug(f"Local parse: {player_input!r} -> {json_cmd}")
        else:
            # Fall back to LLM for complex input
            logger.debug(f"LLM parse needed for: {player_input!r}")
            command_response = self._call_llm(
                f"Player says: {player_input}\n\nRespond with a JSON command."
            )
            extracted = self._extract_json(command_response)

            if extracted is None:
                return "I don't understand what you want to do."
            json_cmd = extracted

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

    def _get_narration_mode(self, verb: str) -> str:
        """Look up narration_mode for a verb from merged vocabulary.

        Args:
            verb: The verb to look up

        Returns:
            "brief" or "tracking" (default: "tracking")
        """
        # Search for verb in merged vocabulary
        for verb_entry in self.merged_vocabulary.get("verbs", []):
            if verb_entry.get("word") == verb:
                # Return narration_mode if specified, otherwise default to "tracking"
                return verb_entry.get("narration_mode", "tracking")

        # If verb not found in vocabulary, default to "tracking"
        return "tracking"

    def _determine_verbosity(self, json_cmd: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Determine verbosity level based on command and tracking state.

        Args:
            json_cmd: The JSON command that was executed
            result: The result from the game engine

        Returns:
            "full" for first visits/examines, "brief" for subsequent or routine actions
        """
        verb = json_cmd.get("action", {}).get("verb", "")

        # Look up narration_mode from merged vocabulary
        narration_mode = self._get_narration_mode(verb)

        # Brief mode is always brief
        if narration_mode == "brief":
            return "brief"

        # Tracking mode: full on first occurrence, brief on subsequent
        # For go/movement: check if destination is new
        if verb == "go" and result.get("success"):
            # Get the new location ID from the result (nested under data.location)
            loc_id = result.get("data", {}).get("location", {}).get("id")
            if loc_id and loc_id not in self.visited_locations:
                return "full"
            return "brief"

        # For other verbs: check if entity is new
        entity_id = result.get("data", {}).get("id")
        if entity_id and entity_id not in self.examined_entities:
            return "full"
        return "brief"

    def _update_tracking(self, json_cmd: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Update visit/examine tracking based on successful commands.

        Args:
            json_cmd: The JSON command that was executed
            result: The result from the game engine
        """
        if not result.get("success"):
            return

        verb = json_cmd.get("action", {}).get("verb", "")

        # Only track for verbs in tracking mode
        narration_mode = self._get_narration_mode(verb)
        if narration_mode != "tracking":
            return

        # Track visited locations on successful movement
        if verb == "go":
            # Location ID is nested under data.location
            loc_id = result.get("data", {}).get("location", {}).get("id")
            if loc_id:
                self.visited_locations.add(loc_id)
        else:
            # Track entities for all other tracking verbs
            entity_id = result.get("data", {}).get("id")
            if entity_id:
                self.examined_entities.add(entity_id)

    def get_opening(self) -> str:
        """Get opening narrative for game start.

        Returns:
            Narrative description of the opening scene
        """
        # Query current location with all relevant details for opening scene
        result = self.handler.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["items", "doors", "exits", "actors"]
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
        """Make an API call to the Ollama server.

        Uses the chat endpoint with explicit message roles for clearer
        separation of system instructions and user content.

        Args:
            user_message: The message to send

        Returns:
            The LLM's response text
        """
        logger.debug(f"System prompt length: {len(self.system_prompt)} chars")
        logger.debug(f"User message: {user_message[:200]}...")

        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "stream": False,
                    "keep_alive": -1,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.num_predict
                    }
                },
                timeout=60  # Longer timeout for generation
            )
            response.raise_for_status()

            data = response.json()

            # Log timing info for debugging
            if "total_duration" in data:
                duration_ms = data["total_duration"] / 1_000_000
                logger.debug(
                    f"Ollama call - duration: {duration_ms:.0f}ms, "
                    f"prompt_tokens: {data.get('prompt_eval_count', '?')}, "
                    f"output_tokens: {data.get('eval_count', '?')}"
                )

            # Chat endpoint returns message.content instead of response
            message = data.get("message", {})
            return message.get("content", "[No response from model]")

        except requests.Timeout:
            return "[Narrator timeout - model may be loading]"
        except requests.ConnectionError:
            return "[Narrator unavailable - is Ollama running?]"
        except requests.HTTPError as e:
            return f"[Narrator error: {e}]"
        except (KeyError, json.JSONDecodeError) as e:
            return f"[Unexpected response format: {e}]"

    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
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

        Combines the protocol specification from src/ollama_narrator_protocol.txt
        (a simpler, narration-focused prompt) with game-specific style guidance.

        Args:
            prompt_file: Path to game-specific style file (narrator_style.txt)

        Returns:
            Combined system prompt string

        Raises:
            FileNotFoundError: If protocol template or style file does not exist
        """
        # Load Ollama-specific protocol template (simpler than the Claude one)
        protocol_path = Path(__file__).parent / "ollama_narrator_protocol.txt"
        if not protocol_path.exists():
            raise FileNotFoundError(
                f"Protocol template not found: {protocol_path}\n"
                "The ollama_narrator_protocol.txt file should be in the src/ directory."
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
        # Use the already-merged vocabulary
        vocab = self.merged_vocabulary

        # Just list verb names (directions are included as verbs since they can be bare commands)
        verbs = [v["word"] for v in vocab.get("verbs", [])]

        if not verbs:
            return "Available verbs: (none - behavior modules should provide verbs)"

        return f"Available verbs: {', '.join(verbs)}"
