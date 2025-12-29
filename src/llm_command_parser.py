"""LLM-based command parser that normalizes natural language to action dicts.

Uses a shared MLX model to map player commands to canonical entity IDs and verb forms,
producing structured JSON for the game engine.
"""

import json
import re
from typing import Dict, List, Optional, Any

import mlx.core as mx
from mlx_lm import stream_generate  # type: ignore
from mlx_lm.sample_utils import make_sampler  # type: ignore
from mlx_lm.models.cache import trim_prompt_cache  # type: ignore

from src.shared_mlx import SharedMLXBackend


class LLMCommandParser:
    """LLM-based command parser that normalizes natural language to action dicts.

    Uses a small local MLX model to map player commands to canonical entity IDs
    and verb forms, producing structured JSON for the game engine.

    The parser outputs simple dicts with string entity IDs. A separate adapter
    (Phase 4) will convert these to ActionDict with WordEntry objects.
    """

    def __init__(self,
                 shared_backend: SharedMLXBackend,
                 verbs: List[str]):
        """Initialize parser with shared MLX backend.

        Args:
            shared_backend: Shared MLX model and tokenizer
            verbs: List of valid verb strings from vocabulary
        """
        self.model = shared_backend.model
        self.tokenizer = shared_backend.tokenizer
        self.verbs = verbs

        # Build and cache system prompt
        system_prompt = self._build_system_prompt(self.verbs)
        self.cache, self.system_prompt_length = shared_backend.create_parser_cache(system_prompt)

    def parse_command(self,
                      player_input: str,
                      context: Dict[str, List[str]]) -> Optional[Dict[str, Any]]:
        """Parse player input to action dict.

        Args:
            player_input: Natural language command from player
            context: Current game context with keys:
                - location_objects: List of entity IDs in current location
                - inventory: List of entity IDs in actor's inventory
                - exits: List of exit direction strings

        Returns:
            Dict with structure:
            {
                "type": "command",
                "action": {
                    "verb": str,
                    "object": Optional[str],
                    "indirect_object": Optional[str],
                    "adjective": Optional[str],
                    "indirect_adjective": Optional[str],
                    "preposition": Optional[str]
                },
                "raw_input": str
            }

            Returns None if parse fails or LLM produces invalid JSON.
        """
        # Build per-turn prompt
        user_prompt = self._build_user_prompt(context, player_input)

        # Call LLM with cached system prompt
        response = self._call_llm(user_prompt)

        # Parse JSON response
        parsed = self._parse_response(response)

        if parsed and parsed.get("type") == "command":
            # Add raw input for debugging
            parsed["raw_input"] = player_input
            return parsed

        return None

    def _build_system_prompt(self, verbs: List[str]) -> str:
        """Build parser system prompt with verb list (cached).

        This prompt is cached after first use, so it should contain only
        static information (verbs, schema, examples).
        """
        verb_list = ', '.join(sorted(verbs))  # Sort for consistency

        return f"""You are a command parser for a text adventure game.

Your job: Convert player commands into JSON that the game engine understands.

VALID VERBS (use these exact words):
{verb_list}

OUTPUT FORMAT:
{{
  "type": "command",
  "action": {{
    "verb": "<verb from list above>",
    "object": "<entity_id>",
    "adjective": "<optional>",
    "indirect_object": "<entity_id>",
    "indirect_adjective": "<optional>",
    "preposition": "<optional>"
  }}
}}

RULES:
1. Use EXACT verb from the list above
2. Use EXACT entity IDs from the current turn's object list
3. Multi-word entities use underscores: "ice wand" → ice_wand
4. Output ONLY valid JSON, no explanation
5. If you cannot parse the command, output: {{"type": "error", "message": "I don't understand."}}

EXAMPLES:

Available objects: ice_wand, frozen_crystal, stone_altar
Command: "use the ice wand on the frozen crystal"
Output: {{"type": "command", "action": {{"verb": "use", "object": "ice_wand", "indirect_object": "frozen_crystal"}}}}

Available objects: ancient_telescope, keepers_journal
Command: "examine the keeper's journal"
Output: {{"type": "command", "action": {{"verb": "examine", "object": "keepers_journal"}}}}

Available exits: north, south, east
Command: "go north"
Output: {{"type": "command", "action": {{"verb": "go", "object": "north"}}}}

Available objects: brass_key, wooden_door
Command: "unlock door with key"
Output: {{"type": "command", "action": {{"verb": "unlock", "object": "wooden_door", "indirect_object": "brass_key", "preposition": "with"}}}}

Available objects: ice_wand
Command: "take wand"
Output: {{"type": "command", "action": {{"verb": "take", "object": "ice_wand"}}}}
"""

    def _build_user_prompt(self, context: Dict[str, List[str]], command: str) -> str:
        """Build per-turn user prompt with current objects and command.

        This is NOT cached - it changes every turn based on location.
        """
        location_objs = ', '.join(context.get('location_objects', [])) or 'none'
        inventory = ', '.join(context.get('inventory', [])) or 'none'
        exits = ', '.join(context.get('exits', [])) or 'none'

        return f"""Available objects: {location_objs}
Your inventory: {inventory}
Exits: {exits}

Command: "{command}"

Output JSON:"""

    def _call_llm(self, user_prompt: str) -> str:
        """Call LLM with cached system prompt."""
        # Trim cache back to system prompt length
        cache_len = self.cache[0].offset if (self.cache and len(self.cache) > 0) else 0
        tokens_to_trim = cache_len - self.system_prompt_length
        if tokens_to_trim > 0:
            trim_prompt_cache(self.cache, tokens_to_trim)

        # Build user message portion
        user_messages = [{"role": "user", "content": user_prompt}]
        user_portion = self.tokenizer.apply_chat_template(
            user_messages,
            add_generation_prompt=True,
            tokenize=False
        )

        # Generate with temperature=0.0 for deterministic parsing
        sampler = make_sampler(temp=0.0)

        response = ""
        for chunk in stream_generate(
            self.model,
            self.tokenizer,
            prompt=user_portion,
            max_tokens=150,  # Shorter than narration
            sampler=sampler,
            prompt_cache=self.cache,
        ):
            response += chunk.text

        return response.strip()

    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response to dict.

        Handles:
        - JSON in code blocks
        - Raw JSON
        - Error messages from LLM

        Returns:
            Dict or None if parsing fails
        """
        # Try code block extraction
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            try:
                parsed_dict: Dict[str, Any] = json.loads(match.group(1))
                return parsed_dict
            except json.JSONDecodeError:
                pass

        # Try raw JSON
        try:
            parsed_dict = json.loads(response.strip())
            # Check if it's an error response
            if parsed_dict.get("type") == "error":
                return None
            return parsed_dict
        except json.JSONDecodeError:
            return None
