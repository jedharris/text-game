"""MLX-LM based Narrator module for text adventure games.

Provides a thin layer between natural language input and the JSON protocol,
translating player input to commands and game results to narrative prose.
Uses Apple's MLX framework for native Metal GPU acceleration on Apple Silicon.

As of Phase 5 (Narration API), verbosity determination and visit tracking are
handled by LLMProtocolHandler. The narrator just passes through the NarrationResult.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Check for MLX-LM availability
try:
    from mlx_lm import load, generate, stream_generate
    from mlx_lm.sample_utils import make_sampler
    from mlx_lm.models.cache import make_prompt_cache, trim_prompt_cache
    import mlx.core as mx
    HAS_MLX = True
except ImportError:
    HAS_MLX = False

from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from src.command_utils import parsed_to_json
from src.parser import Parser
from src.vocabulary_service import load_base_vocabulary


# Default vocabulary file location
DEFAULT_VOCABULARY_FILE = Path(__file__).parent / "vocabulary.json"

# Default MLX model
DEFAULT_MODEL = "mlx-community/Llama-3.2-3B-Instruct-4bit"
DEFAULT_MAX_TOKENS = 300


class MLXNarrator:
    """Translates between natural language and the JSON protocol using MLX-LM."""

    def __init__(self, json_handler: LLMProtocolHandler,
                 model: str = DEFAULT_MODEL,
                 prompt_file: Optional[Path] = None,
                 behavior_manager: Optional[BehaviorManager] = None,
                 vocabulary: Optional[Dict[str, Any]] = None,
                 show_traits: bool = False,
                 temperature: float = 0.8,
                 max_tokens: int = DEFAULT_MAX_TOKENS,
                 shared_backend: Optional[Any] = None):
        """Initialize the narrator.

        Args:
            json_handler: LLMProtocolHandler for game engine communication
            model: MLX model path (HuggingFace format) - only used if shared_backend is None
            prompt_file: Path to system prompt file (required, must exist)
            behavior_manager: Optional BehaviorManager to get merged vocabulary
            vocabulary: Optional merged vocabulary dict (if not provided, loads default)
            show_traits: If True, print llm_context traits before each LLM narration
            temperature: Temperature for generation (0.0-2.0)
            max_tokens: Max tokens to generate
            shared_backend: Optional SharedMLXBackend instance (saves ~4-6GB memory)

        Raises:
            ImportError: If mlx-lm is not installed
            FileNotFoundError: If prompt_file does not exist
        """
        if not HAS_MLX:
            raise ImportError(
                "mlx-lm library is required. Install with: pip install mlx-lm\n"
                "Note: Requires macOS 13.5+ and Apple Silicon (M1/M2/M3/M4)."
            )

        self.handler = json_handler
        self.model_path = model
        self.behavior_manager = behavior_manager
        self.show_traits = show_traits
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.shared_backend = shared_backend

        # Load model and tokenizer (or use shared backend)
        if shared_backend is not None:
            logger.info(f"Using shared MLX backend: {shared_backend.model_path}")
            self.model = shared_backend.model
            self.tokenizer = shared_backend.tokenizer
            self._owns_model = False
        else:
            logger.info(f"Loading MLX model: {model}")
            self.model, self.tokenizer = load(model)[:2]  # Ignore cache info
            logger.info("MLX model loaded successfully")
            self._owns_model = True

        # Store merged vocabulary for parser (must be before _load_system_prompt)
        self.merged_vocabulary = self._get_merged_vocabulary(vocabulary)
        self.parser = self._create_parser(self.merged_vocabulary)
        assert prompt_file is not None, "prompt_file is required"
        self.system_prompt = self._load_system_prompt(prompt_file)

        # Initialize prompt cache for faster generation
        self._init_prompt_cache()

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

            # Check for error or query responses from LLM - don't send to engine
            msg_type = extracted.get("type")
            if msg_type == "error":
                return extracted.get("message", "I don't understand what you want to do.")
            if msg_type == "query":
                # LLM should not send queries when parsing - return error
                logger.warning(f"LLM sent query instead of command: {extracted}")
                return "I don't understand what you want to do."

            json_cmd = extracted

        # 2. Execute command via game engine (result includes verbosity from NarrationResult)
        result = self.handler.handle_message(json_cmd)

        # 3. Print traits if enabled
        self._print_traits(result)

        # 4. Build narration input - only include fields needed for narration
        # The 'data' field contains raw engine data (including state_fragments) that
        # would confuse the LLM. Only send 'narration' (the NarrationPlan), 'success',
        # and 'verbosity' fields.
        narration_dict: Dict[str, Any] = {
            "success": result.get("success", True),
            "verbosity": result.get("verbosity", "full"),
        }
        if "narration" in result:
            narration_dict.update(result["narration"])

        # 5. Get narrative from LLM
        narration_input = f"Narrate this result:\n{json.dumps(narration_dict, indent=2)}"
        logger.debug(f"Narration input ({len(narration_input)} chars): {narration_input[:500]}...")
        narrative = self._call_llm(narration_input)
        logger.debug(f"Narration output ({len(narrative)} chars): {narrative[:200]}...")

        return narrative

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

        # Print traits if enabled
        self._print_traits(result)

        # Opening always uses full verbosity
        result_with_verbosity = dict(result)
        result_with_verbosity["verbosity"] = "full"

        # Opening scene needs more tokens than regular commands
        return self._call_llm(
            f"Narrate the opening scene:\n{json.dumps(result_with_verbosity, indent=2)}",
            max_tokens=500
        )

    def _init_prompt_cache(self) -> None:
        """Initialize and warm the prompt cache with the system prompt.

        This pre-computes the KV cache for the system prompt so that subsequent
        generation calls only need to process the user message, significantly
        reducing latency.
        """
        # Create the prompt cache
        self.prompt_cache = make_prompt_cache(self.model)

        # Build the system prompt prefix in chat format
        # We use just the system message to establish the cached prefix
        system_messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Get the tokenized system prompt prefix
        # Note: We don't add_generation_prompt here since user message comes next
        system_prefix = self.tokenizer.apply_chat_template(
            system_messages,
            add_generation_prompt=False,
            tokenize=False
        )

        # Tokenize and convert to MLX array
        system_tokens = self.tokenizer.encode(system_prefix)
        self.system_prompt_length = len(system_tokens)

        # Warm the cache by running the model on the system prompt
        logger.info(f"Warming prompt cache with {self.system_prompt_length} tokens...")
        prompt_array = mx.array(system_tokens)

        # Process the system prompt through the model to fill the cache
        # We process in one go since system prompts are typically not huge
        self.model(prompt_array[None], cache=self.prompt_cache)
        mx.eval([c.state for c in self.prompt_cache])

        logger.info("Prompt cache initialized")

    def _call_llm(self, user_message: str, max_tokens: Optional[int] = None) -> str:
        """Make a call to the MLX model using cached system prompt.

        Uses the pre-warmed prompt cache for the system prompt, only processing
        the user message tokens for each call.

        Args:
            user_message: The message to send
            max_tokens: Optional override for max tokens (uses self.max_tokens if not specified)

        Returns:
            The LLM's response text
        """
        if max_tokens is None:
            max_tokens = self.max_tokens
        logger.debug(f"User message: {user_message[:200]}...")

        # Trim cache back to system prompt length for fresh generation
        cache_len = self.prompt_cache[0].offset if self.prompt_cache else 0
        tokens_to_trim = cache_len - self.system_prompt_length
        if tokens_to_trim > 0:
            trim_prompt_cache(self.prompt_cache, tokens_to_trim)

        # Build just the user message portion (system prompt is cached)
        # We need the continuation after the system prompt
        user_messages = [
            {"role": "user", "content": user_message}
        ]

        # Get the user message in chat format with generation prompt
        user_portion = self.tokenizer.apply_chat_template(
            user_messages,
            add_generation_prompt=True,
            tokenize=False
        )

        # Create sampler with temperature
        sampler = make_sampler(temp=self.temperature)

        # Generate response using the cached system prompt
        # Any errors here indicate bugs in MLX library usage or model issues
        # and should fail loudly during development
        response = ""
        for chunk in stream_generate(
            self.model,
            self.tokenizer,
            prompt=user_portion,
            max_tokens=max_tokens,
            sampler=sampler,
            prompt_cache=self.prompt_cache,
        ):
            response += chunk.text

        return response.strip() if response else "[No response from model]"

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

        Combines the protocol specification from src/narrator_protocol.txt
        with game-specific style guidance.

        Args:
            prompt_file: Path to game-specific style file (narrator_style.txt)

        Returns:
            Combined system prompt string

        Raises:
            FileNotFoundError: If protocol template or style file does not exist
        """
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
        # Use the already-merged vocabulary
        vocab = self.merged_vocabulary

        # Just list verb names (directions are included as verbs since they can be bare commands)
        verbs = [v["word"] for v in vocab.get("verbs", [])]

        if not verbs:
            return "Available verbs: (none - behavior modules should provide verbs)"

        return f"Available verbs: {', '.join(verbs)}"
