# LLM Command Parser Design

**Status:** Proposed
**Author:** Claude Code
**Date:** 2025-12-26

## Problem Statement

The current pattern-matching parser (`src/parser.py`) is becoming increasingly complex due to:

1. **Multi-valued word types** - Words like "open" that are both verb and adjective require special handling
2. **Multi-word noun phrases** - Entities like "fire wand" need normalization to `fire_wand` for vocabulary lookup
3. **Vocabulary merging complexity** - Combining base vocabulary with behavior modules and entity names creates fragile mappings
4. **Maintenance burden** - Each new entity type or naming pattern requires parser updates

The parser vocabulary building system works but requires careful coordination between:
- Entity naming conventions (`ice_wand` vs "ice wand")
- Vocabulary entries (synonyms, word types)
- Parser pattern matching rules

## Goals

1. **Simplify vocabulary architecture** - Use LLM to normalize natural language to canonical entity IDs
2. **Reduce maintenance burden** - Entity names from game state automatically become valid parse targets
3. **Improve player experience** - Handle natural language variations without explicit vocabulary entries
4. **Memory efficient implementation** - Share model weights between narrator and parser
5. **Enable model upgrades** - Architecture supports larger models (3B → 7B → 13B) with single change
6. **Preserve testing workflow** - Keep simple parser in text_game frontend for automated testing

## Non-Goals

- Context-heavy parsing (pronouns, ambiguity resolution beyond current location)
- Conversational commands ("I want to...", "Please help me...")
- Multi-step command interpretation
- Replacing vocabulary system entirely (vocabulary still resolves canonical names to entities)

## Solution Overview

Replace pattern-matching parser with **LLM normalization layer**:

```
Player Input: "use the fire wand on the glowing mushroom"
       ↓
LLM Parser: Normalize to canonical forms
       ↓
ActionDict: {"verb": "use", "object": "ice_wand", "indirect_object": "glowing_mushroom"}
       ↓
Game Engine: Resolve via existing vocabulary/handlers
```

The LLM acts as a **text normalizer**, not a game interpreter. It maps natural language to canonical forms that the existing vocabulary system resolves to entities.

## Architecture

### 3.1 Shared MLX Backend

**New component:** `src/shared_mlx.py`

```python
class SharedMLXBackend:
    """Shared MLX model instance for multiple uses with separate caches.

    Loads model weights once and provides factory methods for creating
    narrator and parser instances that share the model but have independent
    prompt caches and system prompts.
    """

    def __init__(self, model_path: str):
        """Load model and tokenizer once.

        Args:
            model_path: HuggingFace model path (e.g., "mlx-community/Llama-3.2-3B-Instruct-4bit")
        """
        self.model, self.tokenizer = load(model_path)
        self.model_path = model_path

    def create_narrator_cache(self, system_prompt: str) -> PromptCache:
        """Create and warm a prompt cache for narration.

        Args:
            system_prompt: Narrator protocol + style prompt

        Returns:
            Warmed PromptCache ready for narration generation
        """
        cache = make_prompt_cache(self.model)
        self._warm_cache(cache, system_prompt)
        return cache

    def create_parser_cache(self, system_prompt: str) -> PromptCache:
        """Create and warm a prompt cache for command parsing.

        Args:
            system_prompt: Parser instructions + verb list

        Returns:
            Warmed PromptCache ready for parse generation
        """
        cache = make_prompt_cache(self.model)
        self._warm_cache(cache, system_prompt)
        return cache

    def _warm_cache(self, cache: PromptCache, system_prompt: str) -> int:
        """Warm a cache with system prompt and return token count."""
        # Implementation similar to MLXNarrator._init_prompt_cache()
        ...
```

**Memory footprint:**
- Model weights: ~2-4GB (Llama 3.2 3B, 4-bit quantized)
- Narrator cache: ~50-100MB (depends on system prompt length)
- Parser cache: ~50-100MB
- **Total: ~2.5-4.5GB** (vs ~4-8GB for two separate instances)

**Upgrade path to larger models:**
```python
# Switch from 3B to 7B model with single line change
backend = SharedMLXBackend("mlx-community/Llama-3.3-70B-Instruct-4bit")
# Both narrator and parser automatically use larger model
```

### 3.2 LLM Command Parser

**New component:** `src/llm_command_parser.py`

```python
class LLMCommandParser:
    """LLM-based command parser that normalizes natural language to ActionDict.

    Uses a small local MLX model to map player commands to canonical entity IDs
    and verb forms, producing ActionDict JSON for the game engine.
    """

    def __init__(self,
                 shared_backend: SharedMLXBackend,
                 merged_vocabulary: Dict[str, Any],
                 game_state: GameState):
        """Initialize parser with shared MLX backend.

        Args:
            shared_backend: Shared MLX model and tokenizer
            merged_vocabulary: Merged vocabulary with all verbs
            game_state: Game state for extracting available objects
        """
        self.model = shared_backend.model
        self.tokenizer = shared_backend.tokenizer
        self.game_state = game_state

        # Extract verb list from vocabulary (static, cached)
        self.verbs = self._extract_verbs(merged_vocabulary)

        # Build system prompt with verbs (cached)
        system_prompt = self._build_system_prompt(self.verbs)

        # Create and warm parser cache
        self.cache = shared_backend.create_parser_cache(system_prompt)
        self.system_prompt_length = len(self.tokenizer.encode(system_prompt))

    def parse_command(self,
                      player_input: str,
                      actor_id: str = "player") -> Optional[ActionDict]:
        """Parse player input to ActionDict.

        Args:
            player_input: Natural language command from player
            actor_id: Actor performing the command (default: "player")

        Returns:
            ActionDict if parse succeeds, None if LLM fails to produce valid JSON
        """
        # Get current context (location objects, inventory, exits)
        context = self._build_context(actor_id)

        # Build per-turn prompt
        user_prompt = self._build_user_prompt(context, player_input)

        # Call LLM with cached system prompt
        response = self._call_llm(user_prompt)

        # Parse JSON response
        action_dict = self._parse_response(response)

        if action_dict:
            # Add actor_id
            action_dict["actor_id"] = actor_id
            # Add raw input for debugging
            action_dict["raw_input"] = player_input

        return action_dict

    def _build_context(self, actor_id: str) -> Dict[str, List[str]]:
        """Extract current location objects, inventory, and exits.

        Returns dict with:
        - location_objects: List of entity IDs in current location
        - inventory: List of entity IDs in actor's inventory
        - exits: List of exit direction strings
        """
        actor = self.game_state.actors[actor_id]
        location = self.game_state.locations[actor.location]

        # Get entity IDs (not display names)
        location_objects = [item.id for item in location.items]
        inventory = list(actor.inventory)  # Already IDs
        exits = list(location.exits.keys())

        return {
            "location_objects": location_objects,
            "inventory": inventory,
            "exits": exits
        }

    def _extract_verbs(self, vocabulary: Dict[str, Any]) -> List[str]:
        """Extract canonical verb list from merged vocabulary."""
        return [v["word"] for v in vocabulary.get("verbs", [])]

    def _build_system_prompt(self, verbs: List[str]) -> str:
        """Build parser system prompt with verb list (cached).

        This prompt is cached after first use, so it should contain only
        static information (verbs, schema, examples).
        """
        return f"""You are a command parser for a text adventure game.

Your job: Convert player commands into JSON that the game engine understands.

VALID VERBS (use these exact words):
{', '.join(verbs)}

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

Input objects: ice_wand, frozen_crystal, stone_altar
Command: "use the ice wand on the frozen crystal"
Output: {{"type": "command", "action": {{"verb": "use", "object": "ice_wand", "indirect_object": "frozen_crystal"}}}}

Input objects: ancient_telescope, keepers_journal
Command: "examine the keeper's journal"
Output: {{"type": "command", "action": {{"verb": "examine", "object": "keepers_journal"}}}}

Input exits: north, south, east
Command: "go north"
Output: {{"type": "command", "action": {{"verb": "go", "object": "north"}}}}
"""

    def _build_user_prompt(self, context: Dict[str, List[str]], command: str) -> str:
        """Build per-turn user prompt with current objects and command.

        This is NOT cached - it changes every turn based on location.
        """
        location_objs = ', '.join(context['location_objects']) if context['location_objects'] else 'none'
        inventory = ', '.join(context['inventory']) if context['inventory'] else 'none'
        exits = ', '.join(context['exits']) if context['exits'] else 'none'

        return f"""Current location objects: {location_objs}
Your inventory: {inventory}
Exits: {exits}

Command: "{command}"

Output JSON:"""

    def _call_llm(self, user_prompt: str) -> str:
        """Call LLM with cached system prompt."""
        # Trim cache back to system prompt length
        cache_len = self.cache[0].offset if self.cache else 0
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

    def _parse_response(self, response: str) -> Optional[ActionDict]:
        """Parse LLM response to ActionDict.

        Handles:
        - JSON in code blocks
        - Raw JSON
        - Error messages from LLM

        Returns:
            ActionDict or None if parsing fails
        """
        # Extract JSON (similar to MLXNarrator._extract_json)
        import re
        import json

        # Try code block extraction
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try raw JSON
        try:
            parsed = json.loads(response.strip())
            # Check if it's an error response
            if parsed.get("type") == "error":
                return None
            return parsed
        except json.JSONDecodeError:
            return None
```

### 3.3 Integration with GameEngine

**Modified component:** `src/game_engine.py`

```python
class GameEngine:
    def __init__(self, game_dir: Union[str, Path]):
        # ... existing initialization ...

        # Optional: Initialize shared MLX backend if MLX available
        self.shared_mlx: Optional[SharedMLXBackend] = None

    def create_shared_mlx_backend(self, model: str = "mlx-community/Llama-3.2-3B-Instruct-4bit"):
        """Create shared MLX backend for narrator and parser.

        Call this once to initialize the model, then use create_mlx_narrator()
        and create_llm_parser() which will share the same model weights.

        Args:
            model: MLX model path

        Returns:
            SharedMLXBackend instance
        """
        from src.shared_mlx import SharedMLXBackend
        self.shared_mlx = SharedMLXBackend(model)
        return self.shared_mlx

    def create_llm_parser(self) -> 'LLMCommandParser':
        """Create LLM-based command parser using shared MLX backend.

        Requires create_shared_mlx_backend() to be called first.

        Returns:
            LLMCommandParser instance

        Raises:
            RuntimeError: If shared MLX backend not initialized
        """
        if self.shared_mlx is None:
            raise RuntimeError(
                "Shared MLX backend not initialized. "
                "Call create_shared_mlx_backend() first."
            )

        from src.llm_command_parser import LLMCommandParser
        return LLMCommandParser(
            shared_backend=self.shared_mlx,
            merged_vocabulary=self.merged_vocabulary,
            game_state=self.game_state
        )

    def create_mlx_narrator(self, show_traits: bool = False,
                           temperature: float = 0.8,
                           max_tokens: int = 300):
        """Create MLX narrator using shared backend.

        If shared_mlx is initialized, uses it. Otherwise creates standalone narrator.

        Returns:
            MLXNarrator instance
        """
        style_path = self.game_dir / "narrator_style.txt"
        if not style_path.exists():
            raise FileNotFoundError(f"narrator_style.txt not found: {self.game_dir}")

        if self.shared_mlx:
            # Use shared backend
            from src.mlx_narrator import MLXNarrator
            return MLXNarrator.from_shared_backend(
                shared_backend=self.shared_mlx,
                json_handler=self.json_handler,
                prompt_file=style_path,
                behavior_manager=self.behavior_manager,
                vocabulary=self.merged_vocabulary,
                show_traits=show_traits,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            # Standalone narrator (backwards compatible)
            return self.create_mlx_narrator_standalone(
                show_traits=show_traits,
                temperature=temperature,
                max_tokens=max_tokens
            )
```

### 3.4 Modified MLXNarrator

**Modified component:** `src/mlx_narrator.py`

Add alternative constructor for shared backend:

```python
class MLXNarrator:
    @classmethod
    def from_shared_backend(cls,
                           shared_backend: SharedMLXBackend,
                           json_handler: LLMProtocolHandler,
                           prompt_file: Path,
                           behavior_manager: Optional[BehaviorManager] = None,
                           vocabulary: Optional[Dict[str, Any]] = None,
                           show_traits: bool = False,
                           temperature: float = 0.8,
                           max_tokens: int = 300) -> 'MLXNarrator':
        """Create narrator using shared MLX backend.

        Uses pre-loaded model from shared backend instead of loading separately.

        Args:
            shared_backend: Shared MLX model and tokenizer
            (other args same as __init__)

        Returns:
            MLXNarrator instance using shared model
        """
        instance = cls.__new__(cls)

        # Use shared model instead of loading
        instance.model = shared_backend.model
        instance.tokenizer = shared_backend.tokenizer
        instance.model_path = shared_backend.model_path

        # Initialize other fields normally
        instance.handler = json_handler
        instance.behavior_manager = behavior_manager
        instance.show_traits = show_traits
        instance.temperature = temperature
        instance.max_tokens = max_tokens

        instance.merged_vocabulary = instance._get_merged_vocabulary(vocabulary)
        instance.parser = instance._create_parser(instance.merged_vocabulary)
        instance.system_prompt = instance._load_system_prompt(prompt_file)

        # Create separate cache for narrator
        instance.prompt_cache = shared_backend.create_narrator_cache(instance.system_prompt)
        instance.system_prompt_length = len(instance.tokenizer.encode(instance.system_prompt))

        return instance
```

### 3.5 Text Game Integration

**Modified component:** `text_game.py`

Add option to use LLM parser:

```python
def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument('--llm-parser', action='store_true',
                       help='Use LLM for command parsing (requires MLX)')
    args = parser.parse_args()

    # ... load game engine ...

    if args.llm_parser:
        # Use LLM parser with shared backend
        backend = engine.create_shared_mlx_backend()
        narrator = engine.create_mlx_narrator()
        command_parser = engine.create_llm_parser()

        # Parse loop uses LLM parser
        while True:
            user_input = input("> ")
            action_dict = command_parser.parse_command(user_input)
            if action_dict:
                result = narrator.handler.handle_message(action_dict)
                # ... display result ...
    else:
        # Use traditional parser (for testing)
        parser = engine.create_parser()
        # ... traditional parse loop ...
```

## Implementation Phases

### Phase 1: Shared MLX Backend (2-3 hours)

**Goal:** Create reusable shared model infrastructure

**Tasks:**
1. Create `src/shared_mlx.py` with `SharedMLXBackend` class
2. Implement model loading and cache factory methods
3. Add unit tests for backend initialization and cache creation
4. Test memory usage (verify single model instance)

**Deliverables:**
- `src/shared_mlx.py`
- `tests/test_shared_mlx.py`
- Memory profiling data (single vs dual instance)

**Tests:**
- Backend loads model once
- Multiple caches can be created from same backend
- Each cache is independent (different tokens cached)
- Memory usage ~2-4GB (not 4-8GB)

### Phase 2: LLM Command Parser (3-4 hours)

**Goal:** Implement LLM-based command parsing

**Tasks:**
1. Create `src/llm_command_parser.py` with `LLMCommandParser` class
2. Implement verb extraction from vocabulary
3. Implement context building (location objects, inventory, exits)
4. Implement system prompt generation
5. Implement per-turn prompt generation
6. Implement LLM call with caching
7. Implement JSON response parsing
8. Add unit tests for each component

**Deliverables:**
- `src/llm_command_parser.py`
- `tests/test_llm_command_parser.py`

**Tests:**
- Verb extraction from vocabulary
- Context building from game state
- System prompt contains all verbs
- Per-turn prompt contains correct objects
- JSON parsing handles code blocks and raw JSON
- Error responses return None
- ActionDict has correct structure

### Phase 3: GameEngine Integration (2-3 hours)

**Goal:** Wire up shared backend and parser in GameEngine

**Tasks:**
1. Add `create_shared_mlx_backend()` to GameEngine
2. Add `create_llm_parser()` to GameEngine
3. Modify `create_mlx_narrator()` to optionally use shared backend
4. Add `from_shared_backend()` class method to MLXNarrator
5. Update tests for new factory methods

**Deliverables:**
- Modified `src/game_engine.py`
- Modified `src/mlx_narrator.py`
- Updated `tests/test_game_engine.py`

**Tests:**
- Shared backend creation
- Parser creation from backend
- Narrator creation from backend
- Both share same model instance
- Each has independent cache

### Phase 4: End-to-End Testing (2-3 hours)

**Goal:** Validate parser with real game scenarios

**Tasks:**
1. Create integration test suite with big_game
2. Test common commands ("take X", "go north", "use X on Y")
3. Test multi-word entities ("ice wand", "keeper's journal")
4. Test edge cases (unknown verbs, hallucinated objects)
5. Test error handling (malformed JSON, timeout)
6. Performance benchmarking (latency per parse)
7. Compare with old parser (accuracy, coverage)

**Deliverables:**
- `tests/integration/test_llm_parser_integration.py`
- Performance benchmark results
- Comparison report (old vs new parser)

**Test scenarios:**
- Simple commands: "take ice_wand" → `{"verb": "take", "object": "ice_wand"}`
- Multi-word: "examine keeper's journal" → `{"verb": "examine", "object": "keepers_journal"}`
- With preposition: "use ice wand on frozen crystal" → correct ActionDict
- Directions: "go north" → `{"verb": "go", "object": "north"}`
- Unknown verb: "dance" → None or error
- Hallucinated object: "take unicorn" → `{"verb": "take", "object": "unicorn"}` (handler rejects)
- Malformed JSON: "..." → None

### Phase 5: Text Game Integration (1-2 hours)

**Goal:** Add --llm-parser flag to text_game

**Tasks:**
1. Add `--llm-parser` argument to text_game.py
2. Wire up LLM parser when flag is set
3. Keep traditional parser as default
4. Add usage documentation
5. Test with manual playtesting

**Deliverables:**
- Modified `text_game.py`
- Updated `README.md` with --llm-parser usage

**Manual tests:**
- Start game with `--llm-parser`
- Verify commands parse correctly
- Verify natural language variations work
- Check latency is acceptable (<1s per command)

### Phase 6: Documentation (1 hour)

**Goal:** Document new architecture and usage

**Tasks:**
1. Update `docs/quick_reference.md` with LLM parser info
2. Add LLM parser section to authoring guide
3. Document model upgrade path
4. Add troubleshooting section

**Deliverables:**
- Updated `docs/quick_reference.md`
- Updated `docs/authoring_guide.md` (if needed)
- New `docs/llm_parser_usage.md`

## Testing Strategy

### Unit Tests

**SharedMLXBackend:**
- Model loads once
- Multiple caches created independently
- Cache warming works correctly
- Memory profiling validates single instance

**LLMCommandParser:**
- Verb extraction from vocabulary
- Context building from game state
- System prompt generation
- Per-turn prompt generation
- JSON parsing (code blocks, raw, errors)
- ActionDict structure validation

### Integration Tests

**End-to-end parsing:**
- Simple commands (verb + object)
- Complex commands (verb + adj + object + prep + indirect)
- Multi-word entity normalization
- Direction commands
- Unknown verb handling
- Hallucinated object handling

**Shared backend:**
- Narrator and parser use same model
- Independent caches don't interfere
- Both generate correct outputs

### Performance Tests

**Latency benchmarks:**
- Cold start (first command): <2s
- Warm cache (subsequent commands): <800ms
- Per-turn prompt processing: <100ms
- JSON generation: <500ms

**Memory benchmarks:**
- Shared backend: ~2.5-4.5GB (3B model)
- Traditional separate instances: ~4-8GB (2x 3B model)
- Savings: ~40-50%

### Manual Testing

**Playtest scenarios:**
1. Start big_game with `--llm-parser`
2. Try natural language variations:
   - "use the ice wand"
   - "use ice wand"
   - "use wand"
   - "take keeper's journal"
   - "examine the ancient telescope"
3. Verify error messages for invalid commands
4. Check latency feels responsive

## Error Handling

### LLM Parse Failures

**When LLM produces invalid JSON:**
```python
action_dict = parser.parse_command("fribble the zornack")
if action_dict is None:
    return "I don't understand what you want to do."
```

**When LLM hallucinates objects:**
```python
action_dict = {"verb": "take", "object": "unicorn"}
# Engine passes to handler, which checks entity exists
# Handler returns: HandlerResult(success=False, primary="You don't see that here.")
```

**When LLM hallucinates verbs:**
```python
action_dict = {"verb": "dance", "object": "ice_wand"}
# LLMProtocolHandler.handle_command() checks verb exists
# Returns: {"success": False, "narration": {"primary_text": "I don't understand 'dance'."}}
```

### MLX Failures

**Model fails to load:**
```python
try:
    backend = engine.create_shared_mlx_backend()
except Exception as e:
    print(f"Failed to load MLX model: {e}")
    print("Falling back to traditional parser")
    parser = engine.create_parser()
```

**Generation timeout/error:**
```python
def _call_llm(self, user_prompt: str) -> str:
    try:
        response = stream_generate(...)
        return response
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return '{"type": "error", "message": "Parse failed"}'
```

## Migration Path

### Phase-In Strategy

1. **Week 1-2:** Implement and test with developers
   - Use `--llm-parser` flag for testing
   - Traditional parser remains default
   - Gather performance data

2. **Week 3:** Beta testing with select users
   - Document known issues
   - Collect feedback on latency
   - Identify edge cases

3. **Week 4+:** General availability
   - Make LLM parser default (keep `--traditional-parser` flag)
   - Document migration for existing games
   - Monitor error rates

### Rollback Plan

If LLM parser has critical issues:
1. Revert default to traditional parser
2. LLM parser becomes opt-in via `--llm-parser`
3. Fix issues, re-test, re-deploy

### Backwards Compatibility

- Traditional parser remains in codebase
- All existing games continue to work
- No game state format changes
- No vocabulary format changes

## Model Upgrade Path

### Current Model
- **Model:** Llama 3.2 3B Instruct (4-bit quantized)
- **Memory:** ~2-4GB
- **Speed:** ~50-100 tokens/sec on M1/M2
- **Accuracy:** Good for simple parsing

### Upgrade Options

**Llama 3.3 70B Instruct (4-bit):**
- **Memory:** ~40GB (requires 64GB+ unified memory)
- **Speed:** ~10-20 tokens/sec
- **Accuracy:** Excellent, near-perfect JSON
- **When:** If parsing errors become frequent

**Qwen 2.5 7B Instruct:**
- **Memory:** ~4-6GB
- **Speed:** ~30-50 tokens/sec
- **Accuracy:** Better than 3B, less than 70B
- **When:** If 3B accuracy insufficient but 70B too large

**Upgrade procedure:**
```python
# Single line change in game initialization
backend = engine.create_shared_mlx_backend(
    model="mlx-community/Qwen2.5-7B-Instruct-4bit"
)
```

Both narrator and parser automatically use new model.

## Performance Expectations

### Latency Targets

**Cold start (first command):**
- Model load: ~5-10s (one-time at game start)
- System prompt cache warm: ~1-2s (one-time)
- **Total first command:** <15s (acceptable for game start)

**Subsequent commands:**
- Prompt processing: ~50-100ms
- JSON generation: ~400-600ms
- **Total:** <800ms (feels responsive)

### Memory Targets

**Shared backend (3B model):**
- Model: ~2-4GB
- Narrator cache: ~50-100MB
- Parser cache: ~50-100MB
- **Total:** ~2.5-4.5GB

**Upgrade to 7B model:**
- Model: ~4-6GB
- Caches: ~100-200MB
- **Total:** ~4.5-6.5GB

## Open Questions

1. **Should parser attempt spelling correction?**
   - Pro: Handle typos ("examin" → "examine")
   - Con: Might hallucinate words
   - **Recommendation:** Let LLM try, validate against vocab

2. **Should we cache per-location object lists?**
   - Pro: Skip context building if location unchanged
   - Con: More complexity
   - **Recommendation:** Defer until performance issue identified

3. **Should we support fuzzy object matching?**
   - Example: "wand" matches "ice_wand" if only one wand present
   - Pro: More natural
   - Con: Might be ambiguous
   - **Recommendation:** LLM already handles this naturally

4. **Temperature for parser: 0.0 or 0.1?**
   - 0.0: Fully deterministic
   - 0.1: Tiny variation, might handle edge cases better
   - **Recommendation:** Start with 0.0, test both

## Success Criteria

### Must Have (MVP)

- [ ] LLM parser produces valid ActionDict for common commands
- [ ] Shared backend loads model once (<4.5GB memory)
- [ ] Parsing latency <1s per command
- [ ] No regressions in existing games
- [ ] Traditional parser remains functional

### Should Have (V1)

- [ ] LLM parser handles multi-word entities correctly
- [ ] Error handling provides clear feedback
- [ ] Integration tests pass at >95% rate
- [ ] Documentation complete

### Nice to Have (Future)

- [ ] Spelling correction
- [ ] Abbreviated commands ("n" for "north")
- [ ] Context-aware parsing (pronouns)
- [ ] Multi-step command parsing

## Appendix A: Prompt Examples

### Parser System Prompt (Cached)

```
You are a command parser for a text adventure game.

Your job: Convert player commands into JSON that the game engine understands.

VALID VERBS (use these exact words):
take, drop, use, give, examine, go, climb, unlock, open, close, light, extinguish, read, attack, talk, ask, pour, mix, apply, consume, trade, repair, activate, push, pull, turn, enter, exit, hide, listen, wait, inventory, look, save, load, quit, help

OUTPUT FORMAT:
{
  "type": "command",
  "action": {
    "verb": "<verb from list above>",
    "object": "<entity_id>",
    "adjective": "<optional>",
    "indirect_object": "<entity_id>",
    "indirect_adjective": "<optional>",
    "preposition": "<optional>"
  }
}

RULES:
1. Use EXACT verb from the list above
2. Use EXACT entity IDs from the current turn's object list
3. Multi-word entities use underscores: "ice wand" → ice_wand
4. Output ONLY valid JSON, no explanation
5. If you cannot parse the command, output: {"type": "error", "message": "I don't understand."}

EXAMPLES:

Input objects: ice_wand, frozen_crystal, stone_altar
Command: "use the ice wand on the frozen crystal"
Output: {"type": "command", "action": {"verb": "use", "object": "ice_wand", "indirect_object": "frozen_crystal"}}

Input objects: ancient_telescope, keepers_journal
Command: "examine the keeper's journal"
Output: {"type": "command", "action": {"verb": "examine", "object": "keepers_journal"}}

Input exits: north, south, east
Command: "go north"
Output: {"type": "command", "action": {"verb": "go", "object": "north"}}
```

### Per-Turn User Prompt (Dynamic)

```
Current location objects: ice_wand, frozen_crystal, stone_altar, ancient_telescope
Your inventory: warm_cloak, brass_key
Exits: north, south, down

Command: "use the ice wand on the frozen crystal"

Output JSON:
```

### Expected Response

```json
{"type": "command", "action": {"verb": "use", "object": "ice_wand", "indirect_object": "frozen_crystal"}}
```

## Appendix B: File Structure

```
src/
  shared_mlx.py              # NEW: Shared MLX backend
  llm_command_parser.py      # NEW: LLM command parser
  game_engine.py             # MODIFIED: Add factory methods
  mlx_narrator.py            # MODIFIED: Add from_shared_backend()
  parser.py                  # UNCHANGED: Keep for testing

tests/
  test_shared_mlx.py         # NEW: Backend tests
  test_llm_command_parser.py # NEW: Parser tests
  test_game_engine.py        # MODIFIED: Test new factory methods
  integration/
    test_llm_parser_integration.py  # NEW: E2E tests

docs/
  llm_command_parser_design.md      # THIS DOCUMENT
  llm_parser_usage.md              # NEW: User documentation
  quick_reference.md               # MODIFIED: Add LLM parser section
```

## Appendix C: Total Effort Estimate

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1: Shared MLX Backend | 2-3 hours | None |
| Phase 2: LLM Command Parser | 3-4 hours | Phase 1 |
| Phase 3: GameEngine Integration | 2-3 hours | Phase 1, 2 |
| Phase 4: End-to-End Testing | 2-3 hours | Phase 3 |
| Phase 5: Text Game Integration | 1-2 hours | Phase 4 |
| Phase 6: Documentation | 1 hour | Phase 5 |
| **Total** | **11-16 hours** | Sequential |

**Critical path:** Phases 1 → 2 → 3 → 4 → 5 → 6 (must be sequential)

**Parallel work possible:**
- Documentation can start after Phase 3
- Testing can overlap with Phase 3-5

## Appendix D: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| LLM produces invalid JSON | Medium | High | Robust parsing, fallback to error |
| LLM hallucinates objects | Medium | Low | Handlers validate against game state |
| Memory usage too high for some Macs | Low | Medium | Document minimum requirements (16GB RAM) |
| Parsing latency feels slow | Low | High | Optimize prompt length, test with faster models |
| Model confusion between narrator/parser | Low | High | Separate caches, clear system prompts |
| Traditional parser breaks | Very Low | High | Maintain with tests, keep as default initially |

## Appendix E: Related Work

- Issue #237: Narrator JSON Simplification
- Issue #244: NPC Authoring
- Issue #247: LLM Narrator Data Leak Fix
- `docs/narration/`: Narration design documents
- `src/mlx_narrator.py`: Existing MLX narrator implementation
- `src/parser.py`: Current pattern-matching parser
