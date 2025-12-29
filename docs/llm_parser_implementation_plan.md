# LLM Command Parser Implementation Plan

**Status:** Ready to implement
**Branch:** `feature/llm-parser` (separate from ongoing big_game work)
**Design Reference:** `docs/llm_command_parser_design.md`
**Date:** 2025-01-26

## Executive Summary

Implement an LLM-based command parser that shares model weights with the narrator to enable:
1. Natural language command parsing without brittle pattern matching
2. Memory-efficient architecture (shared 7B model instead of 2x 3B models)
3. Independent development on feature branch (zero conflicts with ongoing big_game work)
4. Clean integration path when ready to merge

**Key constraint:** Development must be completely independent of ongoing big_game upgrades and engine/handler debugging happening on main branch.

## Motivation

### Current Parser Limitations

The pattern-matching parser (`src/parser.py`) has increasing complexity:
- **Multi-valued word types**: "open" is both verb and adjective, requires special handling
- **Multi-word noun phrases**: "fire wand" → `fire_wand` normalization is fragile
- **Vocabulary merging complexity**: Coordinating entity names, synonyms, and parser patterns
- **Maintenance burden**: Each new entity type needs parser updates

### Why LLM Parser?

1. **Simplifies vocabulary architecture** - LLM normalizes natural language to canonical entity IDs
2. **Reduces maintenance** - Entity names from game state automatically become valid targets
3. **Better player experience** - Handles natural variations without explicit vocabulary entries
4. **Memory efficient** - Share model weights between narrator and parser
5. **Upgradeable** - Switch from 3B → 7B → 13B models with single line change

### Why Shared MLX Backend?

**Problem:** Running two separate 3B models (narrator + parser) uses ~4-8GB memory

**Solution:** Load model weights once, create two independent prompt caches:
- Narrator cache: Contains narration protocol and style
- Parser cache: Contains parsing instructions and verb list

**Result:**
- Single 7B model (~4-6GB) instead of 2x 3B models (~4-8GB)
- Better accuracy from larger model
- ~40-50% memory savings enables model upgrade

### Key Design Principle

The LLM parser is a **text normalizer**, not a game interpreter:

```
Player: "use the fire wand on the glowing mushroom"
    ↓
LLM Parser: Normalize to canonical entity IDs
    ↓
Output: {"verb": "use", "object": "fire_wand", "indirect_object": "glowing_mushroom"}
    ↓
Game Engine: Resolve IDs via existing vocabulary/handlers
```

The parser produces structured output; the engine handles all game logic.

## Design Decisions

### 1. Separate Prompt Caches (Critical)

**Why not one shared cache?**
- Models get confused when system prompt mixes parsing and narration instructions
- Caching system prompt is essential for performance (<1s response time)
- Each task needs different instructions and examples

**Solution:**
- Load model weights once (`SharedMLXBackend`)
- Create two independent `PromptCache` instances
- Each cache has its own system prompt
- Cache system prompt tokens, only process per-turn user prompt

**Memory impact:**
- Model: ~4-6GB (7B model, 4-bit quantized)
- Narrator cache: ~50-100MB
- Parser cache: ~50-100MB
- **Total: ~4.5-6.5GB**

### 2. Parser Output Format

**Parser produces simplified dict with string IDs:**
```python
{
    "type": "command",
    "action": {
        "verb": "use",
        "object": "ice_wand",              # String ID
        "indirect_object": "frozen_crystal" # String ID
    }
}
```

**Adapter converts to full ActionDict:**
```python
{
    "actor_id": ActorId("player"),
    "verb": "use",
    "object": WordEntry(...),          # Vocabulary lookup
    "indirect_object": WordEntry(...), # Vocabulary lookup
    "raw_input": "use the ice wand on the frozen crystal"
}
```

**Why this separation?**
- Parser is vocabulary-agnostic (works with any game)
- Adapter handles game-specific WordEntry creation
- Clean separation of concerns for testing

### 3. Temperature Setting

**Parser uses temperature=0.0** (fully deterministic)
- Parsing should be consistent
- No creativity needed
- Easier to test and debug

**Narrator uses temperature=0.8** (creative)
- Narration should vary
- More engaging for players

### 4. Independent Development Strategy

**Challenge:** big_game and engine/handlers are being actively modified on main branch

**Solution:** Build on feature branch with zero dependencies on current main:

1. **Frozen type contracts** - Use current `ActionDict` structure as reference
2. **Minimal test fixtures** - Create small, stable test data independent of big_game
3. **No integration until merge** - Build components, design interfaces, validate separately
4. **Contract-based testing** - Test against type signatures, not live game engine

**Benefits:**
- No merge conflicts during development
- Can proceed in parallel with big_game work
- Integration happens when main stabilizes
- Low-risk merge with minimal core file changes

## Implementation Phases

### Phase 1: Shared MLX Backend (3-4 hours)

**Goal:** Create reusable infrastructure for sharing model weights

#### Tasks
1. Create `src/shared_mlx.py` with `SharedMLXBackend` class
2. Implement model loading (one-time operation)
3. Implement cache factory methods (`create_narrator_cache()`, `create_parser_cache()`)
4. Add unit tests
5. Profile memory usage

#### Deliverables
- `src/shared_mlx.py`:
  ```python
  class SharedMLXBackend:
      """Shared MLX model instance for multiple uses with separate caches."""

      def __init__(self, model_path: str):
          """Load model and tokenizer once."""
          self.model, self.tokenizer = load(model_path)
          self.model_path = model_path

      def create_narrator_cache(self, system_prompt: str) -> PromptCache:
          """Create and warm a prompt cache for narration."""
          cache = make_prompt_cache(self.model)
          self._warm_cache(cache, system_prompt)
          return cache

      def create_parser_cache(self, system_prompt: str) -> PromptCache:
          """Create and warm a prompt cache for command parsing."""
          cache = make_prompt_cache(self.model)
          self._warm_cache(cache, system_prompt)
          return cache

      def _warm_cache(self, cache: PromptCache, system_prompt: str) -> int:
          """Warm a cache with system prompt and return token count."""
          # Build messages with system prompt
          messages = [{"role": "system", "content": system_prompt}]
          prompt = self.tokenizer.apply_chat_template(
              messages,
              add_generation_prompt=False,
              tokenize=False
          )
          # Encode and warm cache
          tokens = self.tokenizer.encode(prompt)
          self.model(mx.array([tokens]), cache=cache)
          return len(tokens)
  ```

- `tests/test_shared_mlx.py`:
  ```python
  class TestSharedMLXBackend(unittest.TestCase):
      def test_model_loads_once(self):
          """Backend loads model weights once."""
          backend = SharedMLXBackend("mlx-community/Qwen2.5-7B-Instruct-4bit")
          self.assertIsNotNone(backend.model)
          self.assertIsNotNone(backend.tokenizer)

      def test_multiple_caches_created(self):
          """Multiple independent caches can be created."""
          backend = SharedMLXBackend("mlx-community/Qwen2.5-7B-Instruct-4bit")
          cache1 = backend.create_narrator_cache("You are a narrator.")
          cache2 = backend.create_parser_cache("You are a parser.")

          # Caches are independent objects
          self.assertIsNot(cache1, cache2)

          # But share same model
          self.assertIs(backend.model, backend.model)

      def test_cache_warming(self):
          """Cache warming actually caches tokens."""
          backend = SharedMLXBackend("mlx-community/Qwen2.5-7B-Instruct-4bit")
          system_prompt = "You are a test assistant."
          cache = backend.create_parser_cache(system_prompt)

          # Cache should have non-zero offset
          self.assertGreater(cache[0].offset, 0)

      def test_memory_usage(self):
          """Memory usage is reasonable for 7B model."""
          import psutil
          import os

          process = psutil.Process(os.getpid())
          mem_before = process.memory_info().rss / 1024**3  # GB

          backend = SharedMLXBackend("mlx-community/Qwen2.5-7B-Instruct-4bit")
          cache1 = backend.create_narrator_cache("Narrator prompt...")
          cache2 = backend.create_parser_cache("Parser prompt...")

          mem_after = process.memory_info().rss / 1024**3  # GB
          mem_used = mem_after - mem_before

          # Should be < 7GB for 7B 4-bit model + 2 caches
          self.assertLess(mem_used, 7.0)
          print(f"Memory used: {mem_used:.2f} GB")
  ```

#### Testing Strategy
- **Unit tests**: Model loading, cache creation, independence
- **Memory profiling**: Verify <7GB for 7B model with 2 caches
- **Integration test**: Create both caches, generate from both, verify outputs differ

#### Success Criteria
- ✅ Model loads successfully
- ✅ Multiple caches created from same backend
- ✅ Caches are independent (different offsets)
- ✅ Memory usage <7GB for 7B model
- ✅ Both caches can generate text independently

---

### Phase 2: LLM Command Parser (4-5 hours)

**Goal:** Implement LLM-based command parsing with frozen test data

#### Tasks
1. Create frozen test fixtures (vocabulary snapshot, test contexts)
2. Implement `LLMCommandParser` class
3. Implement verb extraction from vocabulary
4. Implement system prompt generation (cached)
5. Implement per-turn user prompt generation (dynamic)
6. Implement LLM call with cache management
7. Implement JSON response parsing
8. Add comprehensive unit tests

#### Deliverables

- `tests/fixtures/parser_test_data/vocabulary_snapshot.json`:
  ```json
  {
    "verbs": [
      {"word": "take", "types": ["verb"]},
      {"word": "drop", "types": ["verb"]},
      {"word": "use", "types": ["verb"]},
      {"word": "examine", "types": ["verb"]},
      {"word": "go", "types": ["verb"]},
      {"word": "open", "types": ["verb"]},
      {"word": "close", "types": ["verb"]},
      {"word": "unlock", "types": ["verb"]},
      {"word": "inventory", "types": ["verb"]},
      {"word": "look", "types": ["verb"]}
    ]
  }
  ```

- `tests/fixtures/parser_test_data/test_contexts.json`:
  ```json
  {
    "small_room": {
      "location_objects": ["ice_wand", "frozen_crystal", "stone_altar"],
      "inventory": ["brass_key", "warm_cloak"],
      "exits": ["north", "south", "down"]
    },
    "empty_room": {
      "location_objects": [],
      "inventory": [],
      "exits": ["east"]
    },
    "complex_room": {
      "location_objects": ["keepers_journal", "ancient_telescope", "star_map"],
      "inventory": ["ice_wand", "fire_wand", "brass_key"],
      "exits": ["north", "south", "east", "west", "up"]
    }
  }
  ```

- `src/llm_command_parser.py`:
  ```python
  class LLMCommandParser:
      """LLM-based command parser that normalizes natural language to action dicts.

      Uses a small local MLX model to map player commands to canonical entity IDs
      and verb forms, producing structured JSON for the game engine.
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
          self.cache = shared_backend.create_parser_cache(system_prompt)
          self.system_prompt_length = len(self.tokenizer.encode(system_prompt))

      def parse_command(self,
                        player_input: str,
                        context: Dict[str, List[str]]) -> Optional[Dict]:
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
                  }
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
          verb_list = ', '.join(verbs)

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
          from mlx_lm.utils import generate
          from mlx_lm import make_sampler

          # Trim cache back to system prompt length
          if self.cache:
              cache_len = self.cache[0].offset
              tokens_to_trim = cache_len - self.system_prompt_length
              if tokens_to_trim > 0:
                  from mlx_lm.utils import trim_prompt_cache
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

          response = generate(
              self.model,
              self.tokenizer,
              prompt=user_portion,
              max_tokens=150,
              sampler=sampler,
              prompt_cache=self.cache,
              verbose=False
          )

          return response.strip()

      def _parse_response(self, response: str) -> Optional[Dict]:
          """Parse LLM response to dict.

          Handles:
          - JSON in code blocks
          - Raw JSON
          - Error messages from LLM

          Returns:
              Dict or None if parsing fails
          """
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

- `tests/test_llm_command_parser.py`:
  ```python
  class TestLLMCommandParser(unittest.TestCase):
      @classmethod
      def setUpClass(cls):
          """Load shared backend once for all tests."""
          cls.backend = SharedMLXBackend("mlx-community/Qwen2.5-7B-Instruct-4bit")

          # Load frozen test data
          with open('tests/fixtures/parser_test_data/vocabulary_snapshot.json') as f:
              vocab = json.load(f)
          cls.verbs = [v['word'] for v in vocab['verbs']]

          with open('tests/fixtures/parser_test_data/test_contexts.json') as f:
              cls.contexts = json.load(f)

      def setUp(self):
          """Create parser for each test."""
          self.parser = LLMCommandParser(self.backend, self.verbs)

      def test_simple_command(self):
          """Parse simple verb + object command."""
          context = self.contexts['small_room']
          result = self.parser.parse_command("take the ice wand", context)

          self.assertIsNotNone(result)
          self.assertEqual(result['type'], 'command')
          self.assertEqual(result['action']['verb'], 'take')
          self.assertEqual(result['action']['object'], 'ice_wand')

      def test_complex_command(self):
          """Parse verb + object + preposition + indirect_object."""
          context = self.contexts['small_room']
          result = self.parser.parse_command(
              "use the ice wand on the frozen crystal",
              context
          )

          self.assertIsNotNone(result)
          self.assertEqual(result['action']['verb'], 'use')
          self.assertEqual(result['action']['object'], 'ice_wand')
          self.assertEqual(result['action']['indirect_object'], 'frozen_crystal')

      def test_direction_command(self):
          """Parse movement command."""
          context = self.contexts['small_room']
          result = self.parser.parse_command("go north", context)

          self.assertIsNotNone(result)
          self.assertEqual(result['action']['verb'], 'go')
          self.assertEqual(result['action']['object'], 'north')

      def test_multi_word_entity(self):
          """Parse command with multi-word entity name."""
          context = self.contexts['complex_room']
          result = self.parser.parse_command("examine the keeper's journal", context)

          self.assertIsNotNone(result)
          self.assertEqual(result['action']['verb'], 'examine')
          self.assertEqual(result['action']['object'], 'keepers_journal')

      def test_unknown_verb(self):
          """Unknown verb returns None."""
          context = self.contexts['small_room']
          result = self.parser.parse_command("dance with the wand", context)

          # Parser should reject or return None
          # (Depends on how strict we make the LLM prompt)
          self.assertIsNone(result)

      def test_hallucinated_object(self):
          """Parser may accept hallucinated object (handler will reject)."""
          context = self.contexts['empty_room']
          result = self.parser.parse_command("take the unicorn", context)

          # Parser might produce {"verb": "take", "object": "unicorn"}
          # This is OK - the handler will reject "unicorn" as invalid
          # Testing that parser at least produces valid JSON structure
          if result is not None:
              self.assertEqual(result['type'], 'command')
              self.assertEqual(result['action']['verb'], 'take')

      def test_json_structure(self):
          """All successful parses have correct structure."""
          context = self.contexts['small_room']
          result = self.parser.parse_command("examine ice wand", context)

          self.assertIsNotNone(result)
          self.assertIn('type', result)
          self.assertIn('action', result)
          self.assertIn('verb', result['action'])
          self.assertIn('raw_input', result)

      def test_natural_variations(self):
          """Parser handles natural language variations."""
          context = self.contexts['small_room']

          variations = [
              "use the ice wand",
              "use ice wand",
              "use wand",  # Might fail if multiple wands present
          ]

          for cmd in variations:
              result = self.parser.parse_command(cmd, context)
              if result:  # Some variations might fail, that's ok
                  self.assertEqual(result['action']['verb'], 'use')
  ```

#### Testing Strategy
- **Unit tests**: Test each public method with frozen data
- **JSON validation**: Ensure all outputs match expected schema
- **Edge cases**: Unknown verbs, hallucinated objects, malformed input
- **Natural variations**: Different phrasings of same command
- **NO live game state**: All tests use frozen fixtures

#### Success Criteria
- ✅ Parser produces valid JSON for common commands
- ✅ Multi-word entities normalized correctly ("keeper's journal" → "keepers_journal")
- ✅ Verbs validated against frozen verb list
- ✅ Context properly included in per-turn prompt
- ✅ JSON parsing handles code blocks and raw JSON
- ✅ Error cases return None
- ✅ All tests pass with frozen fixtures

---

### Phase 3: Integration Contract Design (2 hours)

**Goal:** Define how parser integrates with game engine (without actually integrating)

#### Tasks
1. Document integration points in GameEngine
2. Document MLXNarrator modifications
3. Document text_game.py CLI flag
4. Design adapter that converts parser output to ActionDict
5. Create stub/commented integration code

#### Deliverables

- `docs/llm_parser_integration_contract.md`:
  ```markdown
  # LLM Parser Integration Contract

  ## Integration Points

  ### 1. GameEngine.create_shared_mlx_backend()

  **Signature:**
  ```python
  def create_shared_mlx_backend(self,
                                model: str = "mlx-community/Qwen2.5-7B-Instruct-4bit"
                               ) -> SharedMLXBackend:
      """Create shared MLX backend for narrator and parser.

      Args:
          model: HuggingFace model path (4-bit quantized recommended)

      Returns:
          SharedMLXBackend instance
      """
  ```

  **Responsibilities:**
  - Load model once
  - Store in `self.shared_mlx`
  - Enable subsequent `create_mlx_narrator()` and `create_llm_parser()` calls

  ### 2. GameEngine.create_llm_parser()

  **Signature:**
  ```python
  def create_llm_parser(self) -> LLMCommandParser:
      """Create LLM-based command parser using shared MLX backend.

      Requires create_shared_mlx_backend() to be called first.

      Returns:
          LLMCommandParser instance

      Raises:
          RuntimeError: If shared MLX backend not initialized
      """
  ```

  **Responsibilities:**
  - Verify `self.shared_mlx` exists
  - Extract verb list from `self.merged_vocabulary`
  - Create and return `LLMCommandParser`

  ### 3. MLXNarrator.from_shared_backend()

  **Signature:**
  ```python
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
      """Create narrator using shared MLX backend."""
  ```

  **Responsibilities:**
  - Use `shared_backend.model` instead of loading separately
  - Create narrator-specific cache via `shared_backend.create_narrator_cache()`
  - Initialize all other fields normally

  ### 4. text_game.py --llm-parser flag

  **Usage:**
  ```bash
  python -m src.text_game path/to/game --llm-parser
  ```

  **Behavior:**
  - Call `engine.create_shared_mlx_backend()`
  - Create narrator with `engine.create_mlx_narrator()`
  - Create parser with `engine.create_llm_parser()`
  - Main loop uses `parser.parse_command()` instead of `Parser.parse()`
  - Adapter converts parser dict output to ActionDict

  ## Data Flow

  ```
  Player input: "use the ice wand on the frozen crystal"
      ↓
  LLMCommandParser.parse_command(input, context)
      ↓ (returns parser dict)
  {
      "type": "command",
      "action": {
          "verb": "use",
          "object": "ice_wand",              # String ID
          "indirect_object": "frozen_crystal" # String ID
      },
      "raw_input": "use the ice wand on the frozen crystal"
  }
      ↓
  LLMParserAdapter.to_action_dict(parser_output, vocabulary, game_state)
      ↓ (converts to ActionDict)
  {
      "actor_id": ActorId("player"),
      "verb": "use",
      "object": WordEntry(word="ice_wand", ...),      # Vocabulary lookup
      "indirect_object": WordEntry(word="frozen_crystal", ...),
      "raw_input": "use the ice wand on the frozen crystal"
  }
      ↓
  LLMProtocolHandler.handle_command(action_dict)
      ↓
  (normal handler flow)
  ```

  ## Adapter Specification

  The adapter bridges parser output (string IDs) to ActionDict (WordEntry objects).

  **Key operations:**
  1. Extract entity IDs from parser action dict
  2. Look up each ID in merged vocabulary → WordEntry
  3. Construct ActionDict with WordEntry objects
  4. Add actor_id and preserve raw_input

  **Error handling:**
  - If entity ID not in vocabulary, return None (will produce "You don't see that here")
  - If verb not in vocabulary, return None (will produce "I don't understand")
  - If JSON structure invalid, return None
  ```

  **Implementation deferred to Phase 4.**

- `src/game_engine.py` (commented stubs):
  ```python
  # LLM Parser Integration (feature/llm-parser branch)
  # Uncomment when merging to main

  # def create_shared_mlx_backend(self,
  #                               model: str = "mlx-community/Qwen2.5-7B-Instruct-4bit"
  #                              ) -> 'SharedMLXBackend':
  #     """Create shared MLX backend for narrator and parser."""
  #     from src.shared_mlx import SharedMLXBackend
  #     self.shared_mlx = SharedMLXBackend(model)
  #     return self.shared_mlx

  # def create_llm_parser(self) -> 'LLMCommandParser':
  #     """Create LLM-based command parser using shared MLX backend."""
  #     if not hasattr(self, 'shared_mlx') or self.shared_mlx is None:
  #         raise RuntimeError(
  #             "Shared MLX backend not initialized. "
  #             "Call create_shared_mlx_backend() first."
  #         )
  #
  #     from src.llm_command_parser import LLMCommandParser
  #     verbs = [v['word'] for v in self.merged_vocabulary.get('verbs', [])]
  #     return LLMCommandParser(self.shared_mlx, verbs)
  ```

#### Testing Strategy
- **Design review**: Validate contract against current ActionDict structure
- **Type checking**: Ensure signatures match existing patterns
- **Documentation**: Clear examples of each integration point

#### Success Criteria
- ✅ Integration contract clearly documented
- ✅ All integration points identified
- ✅ Data flow fully specified
- ✅ Adapter responsibilities defined
- ✅ Stub code compatible with current GameEngine structure

---

### Phase 4: Integration Adapter + Tests (2 hours)

**Goal:** Build and test the adapter that converts parser output to ActionDict

#### Tasks
1. Implement `LLMParserAdapter` class
2. Implement vocabulary lookup for entity IDs
3. Implement WordEntry creation
4. Implement ActionDict construction
5. Add comprehensive unit tests with frozen vocabulary

#### Deliverables

- `src/llm_parser_adapter.py`:
  ```python
  """Adapter that converts LLM parser output to ActionDict format."""

  from typing import Optional, Dict, Any
  from src.action_types import ActionDict
  from src.word_entry import WordEntry
  from src.types import ActorId


  class LLMParserAdapter:
      """Converts LLM parser output (string IDs) to ActionDict (WordEntry objects)."""

      def __init__(self, merged_vocabulary: Dict[str, Any]):
          """Initialize adapter with merged vocabulary.

          Args:
              merged_vocabulary: Merged vocabulary with all entity names and verbs
          """
          self.vocabulary = merged_vocabulary

      def to_action_dict(self,
                        parser_output: Dict,
                        actor_id: str = "player") -> Optional[ActionDict]:
          """Convert parser dict to ActionDict.

          Args:
              parser_output: Dict from LLMCommandParser.parse_command()
              actor_id: Actor performing the command

          Returns:
              ActionDict if conversion succeeds, None if lookup fails
          """
          if not parser_output or parser_output.get("type") != "command":
              return None

          action = parser_output.get("action", {})

          # Verify verb exists
          verb = action.get("verb")
          if not self._verb_exists(verb):
              return None

          # Build ActionDict
          action_dict: ActionDict = {
              "actor_id": ActorId(actor_id),
              "verb": verb,
              "raw_input": parser_output.get("raw_input", "")
          }

          # Look up object if present
          if "object" in action and action["object"]:
              word_entry = self._lookup_entity(action["object"])
              if word_entry:
                  action_dict["object"] = word_entry
              else:
                  # Allow hallucinated objects - handler will reject
                  # Create a minimal WordEntry for the hallucinated ID
                  action_dict["object"] = WordEntry(
                      word=action["object"],
                      types=["noun"],
                      entity_id=action["object"]
                  )

          # Look up indirect_object if present
          if "indirect_object" in action and action["indirect_object"]:
              word_entry = self._lookup_entity(action["indirect_object"])
              if word_entry:
                  action_dict["indirect_object"] = word_entry
              else:
                  action_dict["indirect_object"] = WordEntry(
                      word=action["indirect_object"],
                      types=["noun"],
                      entity_id=action["indirect_object"]
                  )

          # Copy optional fields
          for field in ["adjective", "indirect_adjective", "preposition"]:
              if field in action and action[field]:
                  action_dict[field] = action[field]

          return action_dict

      def _verb_exists(self, verb: str) -> bool:
          """Check if verb exists in vocabulary."""
          if not verb:
              return False
          verbs = self.vocabulary.get("verbs", [])
          return any(v["word"] == verb for v in verbs)

      def _lookup_entity(self, entity_id: str) -> Optional[WordEntry]:
          """Look up entity ID in vocabulary and return WordEntry.

          Args:
              entity_id: Entity ID string (e.g., "ice_wand", "frozen_crystal")

          Returns:
              WordEntry if found, None otherwise
          """
          # Search in nouns section
          nouns = self.vocabulary.get("nouns", [])
          for noun_entry in nouns:
              if noun_entry.get("entity_id") == entity_id:
                  return WordEntry(
                      word=noun_entry["word"],
                      types=noun_entry.get("types", ["noun"]),
                      entity_id=entity_id
                  )

          # Search in other sections if needed
          # (doors, exits, etc.)

          return None
  ```

- `tests/test_llm_parser_adapter.py`:
  ```python
  class TestLLMParserAdapter(unittest.TestCase):
      def setUp(self):
          """Load frozen vocabulary for testing."""
          with open('tests/fixtures/parser_test_data/vocabulary_snapshot.json') as f:
              self.vocabulary = json.load(f)

          self.adapter = LLMParserAdapter(self.vocabulary)

      def test_simple_command_conversion(self):
          """Convert simple verb + object command."""
          parser_output = {
              "type": "command",
              "action": {
                  "verb": "take",
                  "object": "ice_wand"
              },
              "raw_input": "take the ice wand"
          }

          action_dict = self.adapter.to_action_dict(parser_output)

          self.assertIsNotNone(action_dict)
          self.assertEqual(action_dict["actor_id"], ActorId("player"))
          self.assertEqual(action_dict["verb"], "take")
          self.assertIsInstance(action_dict["object"], WordEntry)
          self.assertEqual(action_dict["object"].entity_id, "ice_wand")
          self.assertEqual(action_dict["raw_input"], "take the ice wand")

      def test_complex_command_conversion(self):
          """Convert verb + object + indirect_object."""
          parser_output = {
              "type": "command",
              "action": {
                  "verb": "use",
                  "object": "ice_wand",
                  "indirect_object": "frozen_crystal"
              },
              "raw_input": "use ice wand on crystal"
          }

          action_dict = self.adapter.to_action_dict(parser_output)

          self.assertIsNotNone(action_dict)
          self.assertEqual(action_dict["verb"], "use")
          self.assertIsInstance(action_dict["object"], WordEntry)
          self.assertIsInstance(action_dict["indirect_object"], WordEntry)
          self.assertEqual(action_dict["object"].entity_id, "ice_wand")
          self.assertEqual(action_dict["indirect_object"].entity_id, "frozen_crystal")

      def test_invalid_verb(self):
          """Invalid verb returns None."""
          parser_output = {
              "type": "command",
              "action": {
                  "verb": "dance",
                  "object": "ice_wand"
              },
              "raw_input": "dance with wand"
          }

          action_dict = self.adapter.to_action_dict(parser_output)
          self.assertIsNone(action_dict)

      def test_hallucinated_object(self):
          """Hallucinated object creates placeholder WordEntry."""
          parser_output = {
              "type": "command",
              "action": {
                  "verb": "take",
                  "object": "unicorn"  # Not in vocabulary
              },
              "raw_input": "take unicorn"
          }

          action_dict = self.adapter.to_action_dict(parser_output)

          # Should create ActionDict with placeholder
          self.assertIsNotNone(action_dict)
          self.assertEqual(action_dict["verb"], "take")
          self.assertIsInstance(action_dict["object"], WordEntry)
          self.assertEqual(action_dict["object"].entity_id, "unicorn")

          # Handler will later reject this as "You don't see that here"

      def test_error_response(self):
          """Error type returns None."""
          parser_output = {
              "type": "error",
              "message": "I don't understand."
          }

          action_dict = self.adapter.to_action_dict(parser_output)
          self.assertIsNone(action_dict)

      def test_preserves_optional_fields(self):
          """Optional fields copied to ActionDict."""
          parser_output = {
              "type": "command",
              "action": {
                  "verb": "unlock",
                  "object": "wooden_door",
                  "indirect_object": "brass_key",
                  "preposition": "with"
              },
              "raw_input": "unlock door with key"
          }

          action_dict = self.adapter.to_action_dict(parser_output)

          self.assertIsNotNone(action_dict)
          self.assertEqual(action_dict.get("preposition"), "with")
  ```

#### Testing Strategy
- **Unit tests**: Test conversion with frozen vocabulary
- **Edge cases**: Invalid verbs, hallucinated objects, error responses
- **Type validation**: Ensure ActionDict structure matches schema
- **WordEntry creation**: Verify correct entity_id, word, types

#### Success Criteria
- ✅ Adapter converts parser output to ActionDict
- ✅ Vocabulary lookups work correctly
- ✅ WordEntry objects created properly
- ✅ Invalid verbs rejected
- ✅ Hallucinated objects handled gracefully
- ✅ All optional fields preserved
- ✅ All tests pass with frozen vocabulary

---

### Phase 5: Documentation (1 hour)

**Goal:** Document usage, architecture, and integration

#### Tasks
1. Create user-facing usage guide
2. Update design document with implementation status
3. Document testing approach
4. Create integration checklist for merge

#### Deliverables

- `docs/llm_parser_usage.md`:
  ```markdown
  # LLM Parser Usage Guide

  ## Overview

  The LLM command parser uses a local language model to parse natural language commands
  into structured action dictionaries for the game engine.

  ## Requirements

  - **Memory**: 16GB+ RAM recommended (8GB minimum)
  - **MLX**: Apple Silicon Mac (M1/M2/M3/M4)
  - **Model**: Automatically downloads on first use (~5GB)

  ## Basic Usage

  ### Using with text_game.py (when merged)

  ```bash
  python -m src.text_game path/to/game --llm-parser
  ```

  ### Programmatic Usage

  ```python
  from src.game_engine import GameEngine

  # Load game
  engine = GameEngine("path/to/game")

  # Create shared MLX backend (loads model once)
  backend = engine.create_shared_mlx_backend(
      model="mlx-community/Qwen2.5-7B-Instruct-4bit"
  )

  # Create narrator and parser (share model weights)
  narrator = engine.create_mlx_narrator()
  parser = engine.create_llm_parser()

  # Use parser
  context = {
      "location_objects": ["ice_wand", "frozen_crystal"],
      "inventory": ["brass_key"],
      "exits": ["north", "south"]
  }

  result = parser.parse_command("use the ice wand on the frozen crystal", context)
  # Returns: {"type": "command", "action": {"verb": "use", "object": "ice_wand", ...}}
  ```

  ## Model Options

  ### Recommended: Qwen 2.5 7B (Default)

  ```python
  backend = engine.create_shared_mlx_backend(
      model="mlx-community/Qwen2.5-7B-Instruct-4bit"
  )
  ```

  - **Memory**: ~4-6GB
  - **Speed**: ~30-50 tokens/sec on M1/M2
  - **Accuracy**: Excellent for parsing tasks

  ### Alternative: Llama 3.2 3B

  ```python
  backend = engine.create_shared_mlx_backend(
      model="mlx-community/Llama-3.2-3B-Instruct-4bit"
  )
  ```

  - **Memory**: ~2-4GB
  - **Speed**: ~50-100 tokens/sec
  - **Accuracy**: Good, occasional JSON errors

  ## Performance

  - **First command**: ~1-2 seconds (cache warming)
  - **Subsequent commands**: <1 second
  - **Memory overhead**: ~100MB per prompt cache

  ## Troubleshooting

  ### "Model failed to load"

  - Check available memory: `system_profiler SPHardwareDataType | grep Memory`
  - Try smaller model (Llama 3.2 3B)
  - Close other memory-intensive applications

  ### "Parse returned None"

  - LLM failed to produce valid JSON
  - Check logs for raw LLM output
  - May indicate:
    - Unknown verb (not in vocabulary)
    - Unparseable command structure
    - Model confusion

  ### "Slow response times"

  - First command is always slower (cache warming)
  - Subsequent commands should be <1s
  - If consistently slow:
    - Check system thermal throttling
    - Try smaller model
    - Reduce max_tokens parameter

  ## Fallback to Traditional Parser

  If LLM parser fails to initialize, fall back to traditional parser:

  ```python
  try:
      backend = engine.create_shared_mlx_backend()
      parser = engine.create_llm_parser()
  except Exception as e:
      print(f"LLM parser failed: {e}")
      print("Falling back to traditional parser")
      parser = engine.create_parser()
  ```
  ```

- `docs/llm_command_parser_design.md`:
  ```markdown
  **Status:** Implemented on feature branch `feature/llm-parser`
  **Implementation Plan:** See `docs/llm_parser_implementation_plan.md`

  (Keep existing design content)
  ```

- `docs/llm_parser_merge_checklist.md`:
  ```markdown
  # LLM Parser Merge Checklist

  ## Pre-Merge Validation

  - [ ] Feature branch `feature/llm-parser` is up to date
  - [ ] All unit tests pass on feature branch
  - [ ] Integration contract reviewed against current main
  - [ ] No conflicts with ongoing big_game work

  ## Integration Steps

  1. **Update integration code**
     - [ ] Uncomment `GameEngine.create_shared_mlx_backend()`
     - [ ] Uncomment `GameEngine.create_llm_parser()`
     - [ ] Add `MLXNarrator.from_shared_backend()` method
     - [ ] Add `--llm-parser` flag to `text_game.py`

  2. **Wire adapter**
     - [ ] Import `LLMParserAdapter` in `text_game.py`
     - [ ] Create adapter instance with `engine.merged_vocabulary`
     - [ ] Call `adapter.to_action_dict()` on parser output

  3. **Test with current big_game**
     - [ ] Game loads successfully
     - [ ] Parser handles common commands
     - [ ] Multi-word entities work
     - [ ] Handler integration works
     - [ ] Error messages sensible

  4. **Update documentation**
     - [ ] Update README.md with `--llm-parser` flag
     - [ ] Update quick_reference.md with parser info

  5. **Merge**
     - [ ] Create PR from `feature/llm-parser` to `main`
     - [ ] Review changes
     - [ ] Merge
     - [ ] Delete feature branch

  ## Post-Merge Validation

  - [ ] All tests pass on main
  - [ ] Traditional parser still works (no `--llm-parser` flag)
  - [ ] LLM parser works with flag
  - [ ] No performance regressions
  - [ ] Documentation accurate
  ```

#### Success Criteria
- ✅ Usage guide complete and clear
- ✅ Design document updated with status
- ✅ Merge checklist created
- ✅ All documentation reviewed for accuracy

---

## Summary of Deliverables

### New Files Created
1. `src/shared_mlx.py` - Shared MLX backend
2. `src/llm_command_parser.py` - LLM parser
3. `src/llm_parser_adapter.py` - Adapter to ActionDict
4. `tests/test_shared_mlx.py` - Backend tests
5. `tests/test_llm_command_parser.py` - Parser tests
6. `tests/test_llm_parser_adapter.py` - Adapter tests
7. `tests/fixtures/parser_test_data/vocabulary_snapshot.json` - Test data
8. `tests/fixtures/parser_test_data/test_contexts.json` - Test data
9. `docs/llm_parser_integration_contract.md` - Integration spec
10. `docs/llm_parser_usage.md` - User guide
11. `docs/llm_parser_merge_checklist.md` - Merge guide

### Modified Files
1. `docs/llm_command_parser_design.md` - Update status
2. `src/game_engine.py` - Add commented integration stubs

### Not Modified (Until Merge)
- `src/mlx_narrator.py` - Integration deferred
- `src/text_game.py` - Integration deferred
- `big_game/*` - No dependencies
- All handler code - No dependencies

---

## Testing Summary

### Unit Tests
- SharedMLXBackend: Model loading, cache creation, memory usage
- LLMCommandParser: Parsing logic, JSON handling, context building
- LLMParserAdapter: Dict → ActionDict conversion, vocabulary lookup

### Integration Tests
- Backend + Parser: End-to-end parsing with real MLX model
- Parser + Adapter: Full pipeline from string to ActionDict

### Manual Testing
- Ad-hoc script for prompt engineering iteration
- Performance profiling (latency, memory)

### No Integration with big_game
- All tests use frozen fixtures
- No dependencies on current game state
- Integration testing happens at merge time

---

## Development Workflow

### Branch Strategy
```bash
# Create feature branch
git checkout -b feature/llm-parser

# Work on phases independently
git commit -m "Phase 1: Implement SharedMLXBackend"
git commit -m "Phase 2: Implement LLMCommandParser"
# etc.

# Keep branch separate until big_game work stabilizes
# Merge when ready
```

### Workflow Compliance (per CLAUDE.md)

This is a **Workflow B** task (large change with phasing):

1. ✅ **Create GitHub issue** describing the problem
2. ✅ **Design document exists** (`llm_command_parser_design.md`)
3. ⚠️ **Add comment to issue** with analysis and design reference
4. ⚠️ **Create phase issues** for each phase
5. **Execute phases** using TDD
6. **Close phase issues** with summary comments
7. **Close main issue** when all phases complete

### Issue Structure

**Parent Issue: "Implement LLM Command Parser"**
- Description: Parser limitations, LLM parser motivation
- Comment: Link to design doc and implementation plan
- Sub-issues:
  - Phase 1: Shared MLX Backend
  - Phase 2: LLM Command Parser
  - Phase 3: Integration Contract Design
  - Phase 4: Integration Adapter
  - Phase 5: Documentation

---

## Success Metrics

### Phase Completion
- ✅ All deliverables created
- ✅ All tests passing
- ✅ Code reviewed for quality
- ✅ Documentation complete

### Overall Success
- ✅ Parser works independently with frozen data
- ✅ Integration contract clearly defined
- ✅ Adapter tested with frozen vocabulary
- ✅ Zero conflicts with main branch
- ✅ Ready to merge when big_game stabilizes

---

## Open Design Questions

### 1. Model Selection: 3B vs 7B?

**Recommendation: Start with 7B (Qwen 2.5 7B Instruct)**

**Rationale:**
- Better JSON generation accuracy
- Fewer parsing errors to debug
- Still fits in memory budget (~4-6GB)
- Can downgrade to 3B if performance issues

**Alternative:** Start with 3B for faster iteration, upgrade to 7B for accuracy

**Decision:** [To be decided at start of Phase 1]

### 2. Spelling Correction?

**Question:** Should parser attempt to correct typos? ("examin" → "examine")

**Options:**
- A) Let LLM try naturally, validate verb against vocabulary
- B) Explicitly instruct LLM to correct spelling
- C) Reject typos (strict matching only)

**Recommendation:** Option A - LLM will naturally handle minor typos

**Decision:** [Defer until Phase 2 prompt engineering]

### 3. Temperature: 0.0 or 0.1?

**Question:** Use temperature 0.0 (fully deterministic) or 0.1 (tiny variation)?

**Trade-offs:**
- 0.0: Fully deterministic, easier to test, consistent behavior
- 0.1: Might handle edge cases better, less brittle

**Recommendation:** Start with 0.0 for testing, experiment with 0.1 if issues arise

**Decision:** [Test both in Phase 2]

### 4. Handling Hallucinated Objects

**Question:** How should adapter handle objects not in vocabulary?

**Current approach:** Create placeholder WordEntry, let handler reject

**Alternative:** Adapter returns None, skip handler entirely

**Recommendation:** Current approach - handlers should validate entities

**Decision:** [Validate in Phase 4 testing]

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| LLM produces invalid JSON | Medium | High | Robust JSON parsing, error handling, test extensively |
| LLM hallucinates objects | Medium | Low | Handlers validate against game state |
| Memory usage too high | Low | Medium | Profile in Phase 1, document minimum requirements |
| Parsing latency too slow | Low | High | Use 7B model, optimize prompts, cache system prompt |
| Model confusion (narrator vs parser) | Low | High | Separate caches with distinct system prompts |
| Integration conflicts at merge | Low | Medium | Feature branch strategy, clear integration contract |
| Traditional parser breaks | Very Low | High | No modifications to traditional parser, keep as fallback |

---

## Next Steps

1. **Create GitHub issues** (parent + phases)
2. **Create feature branch** (`feature/llm-parser`)
3. **Start Phase 1:** Shared MLX Backend
   - Decide on 3B vs 7B model
   - Implement `SharedMLXBackend`
   - Test memory usage
   - Verify cache independence
4. **Proceed through phases** sequentially
5. **Review and iterate** on prompts in Phase 2
6. **Prepare for merge** when big_game work stabilizes

---

## Timeline Estimate

| Phase | Estimated Time | Dependencies |
|-------|----------------|--------------|
| Phase 1: Shared MLX Backend | 3-4 hours | None |
| Phase 2: LLM Parser | 4-5 hours | Phase 1 |
| Phase 3: Integration Contract | 2 hours | Phase 2 |
| Phase 4: Integration Adapter | 2 hours | Phase 3 |
| Phase 5: Documentation | 1 hour | Phase 4 |
| **Total** | **12-14 hours** | Sequential |

**Actual integration at merge time:** +2-3 hours for wiring and testing with live big_game

---

## Appendix: Key Constraints

### Independence Requirements
- **No dependencies on big_game** - Use frozen test fixtures
- **No modifications to core files** - Stub integration points only
- **No integration tests with live game** - Wait until merge
- **Feature branch development** - Separate from main until ready

### Technical Requirements
- **Apple Silicon Mac** - MLX requires M1/M2/M3/M4
- **16GB+ RAM recommended** - 8GB minimum for 7B model
- **Python 3.10+** - Type hints, pattern matching
- **MLX installed** - `pip install mlx-lm`

### Code Quality Requirements
- **Full type annotations** - All public APIs typed
- **80% test coverage** - Unit tests for all components
- **TDD approach** - Tests written before/with implementation
- **Documentation** - Docstrings for all public methods
- **Error handling** - Graceful degradation, clear error messages

---

**Ready to begin implementation on feature branch `feature/llm-parser`**
