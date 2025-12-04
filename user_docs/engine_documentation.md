# Text Adventure Game Engine - Developer Documentation

## Document Purpose

This document is for developers who want to:
- Understand the engine's internal architecture
- Extend core engine functionality
- Contribute to the codebase
- Debug engine internals
- Add new core features

**Not for game authors** - If you're creating games with this framework, see the Game Author Guide instead.

---

# 1. Architecture Overview

## 1.1 Design Philosophy

**Core Principles:**
- **Separation of concerns**: Engine manages state, LLM narrates
- **Property-based entities**: Flexible properties dict, minimal core fields
- **Behavior-driven extension**: New functionality via external modules
- **Validation over runtime checks**: Fail fast during load, not during play
- **Test-driven development**: Comprehensive test coverage required
- **Maximize author capability and player agency**

**State Management Rule:**
The game engine is solely responsible for all state management. The LLM never causes state changes - it only narrates state changes made by the engine.

## 1.2 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Game Author                           │
│  (Creates game_state.json, behaviors, narrator_style.txt)   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │         llm_game.py (CLI)             │
         │  - Entry point                        │
         │  - Handles API keys                   │
         │  - Game loop                          │
         └─────────────┬─────────────────────────┘
                       │
                       ▼
         ┌───────────────────────────────────────┐
         │      LLM Narrator (llm_narrator.py)   │
         │  - Natural language → JSON commands   │
         │  - Fast local parser (common cmds)    │
         │  - LLM fallback (complex input)       │
         │  - JSON results → Narrative prose     │
         └─────────────┬─────────────────────────┘
                       │
                       ▼ JSON Protocol
         ┌───────────────────────────────────────┐
         │    Game Engine (GameEngine class)     │
         │  - State loading/validation           │
         │  - Behavior management                │
         │  - Protocol handler creation          │
         └─────────────┬─────────────────────────┘
                       │
                       ▼
         ┌───────────────────────────────────────┐
         │  LLM Protocol Handler                 │
         │  (llm_protocol.py)                    │
         │  - Command routing                    │
         │  - Query processing                   │
         │  - Handler invocation                 │
         └─────────────┬─────────────────────────┘
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
   ┌─────────────────┐   ┌─────────────────┐
   │ Behavior System │   │  State Manager  │
   │ - Module loading│   │  - GameState    │
   │ - Handlers      │   │  - Entities     │
   │ - Entity events │   │  - Validation   │
   └────────┬────────┘   └────────┬────────┘
            │                     │
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │   StateAccessor     │
            │  - Entity queries   │
            │  - State updates    │
            │  - Behavior invoke  │
            └─────────────────────┘
```

## 1.3 Module Organization

```
src/
├── game_engine.py          # High-level engine API
├── llm_narrator.py         # LLM integration layer
├── llm_protocol.py         # JSON protocol handler
├── state_manager.py        # Entity models, load/save
├── state_accessor.py       # Unified state access API
├── behavior_manager.py     # Behavior module system
├── parser.py               # Fast local command parser
├── parsed_command.py       # Parser output structure
├── word_entry.py           # Vocabulary entry type
├── vocabulary.json         # Base vocabulary
└── narrator_protocol.txt   # LLM protocol specification

behaviors/core/             # Core behavior modules
├── __init__.py
├── manipulation.py         # take, drop, put
├── perception.py           # examine, look, inventory
├── interaction.py          # open, close, unlock, etc.
└── meta.py                 # help, save, load, quit

behavior_libraries/         # Shared reusable behaviors
├── puzzle_lib/
└── offering_lib/

utilities/                  # Helper functions
├── entity_serializer.py    # Entity → dict conversion
├── location_serializer.py  # Location → LLM format
└── utils.py                # Misc utilities

tests/                      # Comprehensive test suite
```

---

# 2. Core Components

## 2.1 State Manager (state_manager.py)

**Purpose:** Define entity data models and handle persistence

### Entity Models

All entities follow the property-based pattern:
- **Core fields**: Structural data (id, name, location, exits, inventory)
- **Properties dict**: Flexible non-structural data
- **Behaviors list**: Behavior module references

**Entity Types:**
```python
@dataclass
class Location:
    id: str                           # Globally unique ID
    name: str                         # User-facing name
    description: str                  # Prose description
    exits: Dict[str, ExitDescriptor]  # Direction → exit mapping
    items: List[str]                  # Item IDs in this location
    properties: Dict[str, Any]        # Flexible properties
    behaviors: List[str]              # Behavior module paths

@dataclass
class Item:
    id: str
    name: str
    description: str
    location: str                     # Where this item is
    properties: Dict[str, Any]        # portable, container, door, etc.
    behaviors: List[str]

@dataclass
class Actor:
    id: str
    name: str
    description: str
    location: str                     # Current location
    inventory: List[str]              # Item IDs
    properties: Dict[str, Any]        # stats, flags, states
    behaviors: List[str]

@dataclass
class Lock:
    id: str
    name: str
    description: str
    properties: Dict[str, Any]        # opens_with, auto_unlock
    behaviors: List[str]

@dataclass
class ExitDescriptor:
    type: str                         # "open" or "door"
    to: Optional[str]                 # Destination location ID
    door_id: Optional[str]            # Door item ID (if type="door")
    name: str                         # User-facing exit name
    description: str                  # Prose description
    properties: Dict[str, Any]
    behaviors: List[str]
```

### Property Accessors

Common properties have convenience accessors:
```python
# Item
item.portable → properties.get("portable", False)
item.container → ContainerInfo wrapper or None
item.is_door → "door" in properties
item.states → properties.get("states", {})
item.llm_context → properties.get("llm_context")

# Actor
actor.stats → properties.get("stats", {})
actor.flags → properties.get("flags", {})
actor.states → properties.get("states", {})

# Lock
lock.opens_with → properties.get("opens_with", [])
lock.auto_unlock → properties.get("auto_unlock", False)
```

### Loading and Saving

```python
def load_game_state(source: Union[str, Path, Dict]) -> GameState:
    """Load and validate game state from JSON file or dict."""
    # 1. Parse JSON
    # 2. Convert to entity objects
    # 3. Validate structure
    # 4. Build global ID registry
    # 5. Validate all references
    # 6. Return GameState

def save_game_state(state: GameState, path: Path) -> None:
    """Serialize game state to JSON file."""
    # Converts entity objects back to JSON-serializable dicts
```

### Validation Rules

Structural validation (in `validators.py`):
- All IDs globally unique across entity types
- All references valid (location exits, item locations, lock references)
- Required fields present
- Special ID "player" reserved
- Actor "player" must exist
- Metadata.start_location must exist
- No cycles in containment (items in items)

## 2.2 State Accessor (state_accessor.py)

**Purpose:** Unified API for querying and modifying game state

### Design Rationale

StateAccessor provides:
1. **Consistent interface** - Single API for all entity access
2. **Behavior integration** - Automatic behavior invocation on updates
3. **Validation** - Ensures updates maintain state consistency
4. **Encapsulation** - Hides GameState internal structure

### Core Methods

**Entity Queries:**
```python
def get_location(self, location_id: str) -> Optional[Location]
def get_item(self, item_id: str) -> Optional[Item]
def get_actor(self, actor_id: str) -> Optional[Actor]
def get_lock(self, lock_id: str) -> Optional[Lock]

def get_items_in_location(self, location_id: str) -> List[Item]
def get_actors_in_location(self, location_id: str) -> List[Actor]
def get_items_in_container(self, container_id: str) -> List[Item]
```

**Entity Matching:**
```python
def find_entity_in_location(
    self,
    word_entry: WordEntry,
    location_id: str,
    adjective: Optional[str] = None,
    actor_id: str = "player"
) -> Optional[Union[Item, Actor, ExitDescriptor]]
```

**State Updates:**
```python
def update(
    self,
    entity: Union[Item, Actor, Location, Lock],
    changes: Dict[str, Any],
    verb: Optional[str] = None,
    actor_id: str = "player"
) -> UpdateResult

# UpdateResult contains:
# - success: bool
# - message: str
# - changes_applied: Dict[str, Any]
```

**Behavior Invocation:**
```python
def invoke_handler(self, verb: str, action: Dict) -> EventResult
def invoke_previous_handler(self, verb: str, action: Dict) -> EventResult
```

### Update with Behaviors

When `update()` is called with a verb:
1. Look up corresponding event name (`on_<verb>`)
2. Invoke entity behaviors for that event
3. If any behavior denies (allow=False), abort update
4. Apply changes if all behaviors allow
5. Return result with behavior message if present

This enables entity-specific reactions to state changes.

## 2.3 Behavior Manager (behavior_manager.py)

**Purpose:** Load and manage behavior modules

### Module Discovery

```python
def discover_modules(self, behaviors_dir: str) -> List[str]:
    """Recursively find all .py files in behaviors directory.

    Handles symlinks (for core/library tiers).
    Returns module paths like: behaviors.core.manipulation
    """
```

### Module Loading

```python
def load_module(self, module: ModuleType) -> None:
    """Load behavior module and extract:
    - VOCABULARY (if present)
    - Command handlers (handle_* functions)
    - Entity behaviors (on_* functions)
    """
```

### Handler Management

```python
def register_handler(self, verb: str, handler: Callable) -> None:
    """Register command handler, maintaining precedence order.

    Precedence: game > library > core
    Multiple handlers per verb form a chain.
    """

def get_handler(self, verb: str) -> Optional[Callable]:
    """Get primary (highest precedence) handler for verb."""

def invoke_handler(self, verb: str, accessor: StateAccessor,
                   action: Dict) -> EventResult:
    """Invoke handler chain for verb."""
```

### Vocabulary Merging

```python
def get_merged_vocabulary(self, base_vocab: Dict) -> Dict:
    """Merge base vocabulary with all loaded module vocabularies.

    Ensures no duplicate words across modules.
    Returns unified vocabulary with all verbs, nouns, directions.
    """
```

### Handler Precedence

When multiple modules provide handlers for the same verb:
1. Game-specific handlers (tier 1) are called first
2. Library handlers (tier 2) are called next
3. Core handlers (tier 3) are called last

Handlers can call `invoke_previous_handler()` to delegate to lower tiers.

## 2.4 Parser (parser.py)

**Purpose:** Fast local parsing of common command patterns

### Design

The parser provides quick, deterministic parsing for:
- Direction commands ("north", "go south")
- Simple verb-object commands ("take key", "examine door")
- Verb-object-preposition-object ("put key in box")
- Adjective disambiguation ("examine red key")

Complex or ambiguous input falls back to LLM parsing.

### ParsedCommand Structure

```python
@dataclass
class ParsedCommand:
    verb: Optional[WordEntry]              # Action verb
    direct_object: Optional[WordEntry]     # Primary object
    direct_adjective: Optional[WordEntry]  # Object adjective
    preposition: Optional[WordEntry]       # "in", "on", "to"
    indirect_object: Optional[WordEntry]   # Secondary object
    indirect_adjective: Optional[WordEntry]# Secondary adjective
    raw_input: str                         # Original input
```

### WordEntry Type

All vocabulary uses WordEntry (never bare strings):
```python
@dataclass
class WordEntry:
    word: str                    # Primary word
    word_type: WordType          # VERB, NOUN, DIRECTION, etc.
    synonyms: List[str]          # Alternative forms
    object_required: bool = False   # For verbs
    narration_mode: str = "tracking"  # "brief" or "tracking"
```

### Parsing Flow

1. **Tokenize** - Split input into words
2. **Match vocabulary** - Find WordEntry objects for tokens
3. **Identify verb** - First word or after "go"
4. **Extract objects** - Direct and indirect objects
5. **Find adjectives** - Words before objects
6. **Identify preposition** - Between objects
7. **Return ParsedCommand** - Or None if parsing fails

### Performance

Parser uses trie-based vocabulary lookup for O(n) matching where n is input length.
Typical parse time: < 1ms for common commands.

## 2.5 LLM Protocol Handler (llm_protocol.py)

**Purpose:** Implement JSON protocol for LLM-engine communication

### Message Types

**Commands:**
```json
{
  "type": "command",
  "action": {
    "verb": "take",
    "object": <WordEntry or string>,
    "adjective": "red",
    "preposition": "from",
    "indirect_object": <WordEntry or string>,
    "indirect_adjective": "wooden",
    "actor_id": "player"
  }
}
```

**Queries:**
```json
{
  "type": "query",
  "query_type": "location|entity|entities|vocabulary|metadata",
  "include": ["items", "doors", "exits", "actors"],  // For location queries
  "entity_type": "item|door|npc|location",           // For entity queries
  "entity_id": "item_id",                            // For entity queries
  "actor_id": "player"
}
```

### Response Format

**Success:**
```json
{
  "type": "result",
  "success": true,
  "action": "verb",
  "message": "Human-readable result",
  "data": {
    // Optional additional data (e.g., entity details, location info)
  }
}
```

**Failure:**
```json
{
  "type": "result",
  "success": false,
  "action": "verb",
  "error": {
    "message": "Error description",
    "fatal": false  // true for state corruption
  }
}
```

### String to WordEntry Conversion

Protocol handler converts string objects to WordEntry objects:
```python
def _convert_action_strings_to_wordentry(action: Dict) -> Dict:
    """Convert object/indirect_object strings to WordEntry.

    Handlers expect WordEntry objects for entity matching.
    Verbs, adjectives, prepositions remain as strings.
    """
```

### Meta Command Handling

Meta commands (save, load, quit, help) must work even if state is corrupted.
Protocol handler checks for state corruption and blocks non-meta commands.

## 2.6 LLM Narrator (llm_narrator.py)

**Purpose:** Bridge between natural language and JSON protocol

### Two-Stage Processing

**Stage 1: Input → JSON Command**
- Try fast local parser first
- Fall back to LLM for complex input
- Extract JSON from LLM response
- Validate command structure

**Stage 2: JSON Result → Narrative**
- Add verbosity hint (full/brief)
- Send to LLM with system prompt
- Return narrative prose

### Fast Parser Integration

```python
def process_turn(self, player_input: str) -> str:
    # 1. Try local parser
    parsed = self.parser.parse_command(player_input)

    if parsed:
        # Convert ParsedCommand to JSON
        json_cmd = parsed_to_json(parsed)
    else:
        # Fall back to LLM
        json_cmd = self._ask_llm_to_parse(player_input)

    # 2. Execute via engine
    result = self.handler.handle_message(json_cmd)

    # 3. Narrate result
    narrative = self._ask_llm_to_narrate(result)
    return narrative
```

### Verbosity Control

Narrator tracks visited locations and examined entities:
```python
visited_locations: Set[str]
examined_entities: Set[str]
```

Verbosity determination:
- **Full**: First visit to location or first examination of entity
- **Brief**: Subsequent visits/examinations
- **Brief verbs**: Some verbs always brief (e.g., inventory, help)

Verbosity mode comes from verb's `narration_mode` property:
- `"tracking"`: Full first time, brief after
- `"brief"`: Always brief

### Prompt Caching

Uses Claude's prompt caching to reduce cost/latency:
```python
system=[{
    "type": "text",
    "text": self.system_prompt,
    "cache_control": {"type": "ephemeral"}
}]
```

Cache TTL: 5 minutes
Typical cache hit rate: 90%+ after first request

### System Prompt Construction

```python
def _load_system_prompt(self, prompt_file: Path) -> str:
    """Combine protocol template + game style + vocabulary.

    1. Load src/narrator_protocol.txt (standard protocol)
    2. Load game's narrator_style.txt (game-specific style)
    3. Build vocabulary section from merged vocabulary
    4. Combine: protocol + style + vocabulary
    """
```

---

# 3. Data Flow and Execution

## 3.1 Game Initialization

```
1. llm_game.py main()
   ├─ Load API key from environment
   ├─ Create GameEngine(game_dir)
   │  ├─ Load game_state.json
   │  ├─ Validate structure
   │  ├─ Create BehaviorManager
   │  ├─ Discover behavior modules
   │  ├─ Load modules (vocabulary + handlers)
   │  └─ Return initialized engine
   ├─ Create LLMNarrator
   │  ├─ Build merged vocabulary
   │  ├─ Create Parser with vocabulary
   │  ├─ Load narrator prompts
   │  └─ Initialize LLM client
   └─ Enter game loop
```

## 3.2 Command Execution Flow

```
Player Input: "take the red key from the wooden box"
    ↓
1. LLMNarrator.process_turn()
    ├─ Try Parser.parse_command()
    │  ├─ Match "take" → VERB
    │  ├─ Match "key" → NOUN (direct_object)
    │  ├─ Match "red" → ADJECTIVE (direct_adjective)
    │  ├─ Match "from" → PREPOSITION
    │  ├─ Match "box" → NOUN (indirect_object)
    │  ├─ Match "wooden" → ADJECTIVE (indirect_adjective)
    │  └─ Return ParsedCommand
    ├─ Convert to JSON:
    │  {
    │    "type": "command",
    │    "action": {
    │      "verb": "take",
    │      "object": WordEntry("key", ...),
    │      "adjective": "red",
    │      "preposition": "from",
    │      "indirect_object": WordEntry("box", ...),
    │      "indirect_adjective": "wooden",
    │      "actor_id": "player"
    │    }
    │  }
    ↓
2. LLMProtocolHandler.handle_command()
    ├─ Extract verb: "take"
    ├─ Convert string fields to WordEntry if needed
    ├─ Ensure actor_id present
    ├─ Check if handler exists
    ├─ BehaviorManager.invoke_handler("take", accessor, action)
    │  ├─ Get handler function (highest precedence)
    │  └─ Call handle_take(accessor, action)
    ↓
3. handle_take() [in behaviors/core/manipulation.py]
    ├─ Extract action parameters
    ├─ Resolve "key" with adjective "red" → item_red_key
    ├─ Resolve "box" with adjective "wooden" → item_wooden_box
    ├─ Validate: key in box? box is container? key portable?
    ├─ Check behavior: item_red_key has behaviors?
    │  ├─ Yes: invoke on_take() for item_red_key
    │  └─ Behavior allows? Update state
    ├─ Update state: move item_red_key from box to player inventory
    ├─ Return EventResult(success=True, message="You take the red key.")
    ↓
4. LLMProtocolHandler formats result:
    {
      "type": "result",
      "success": true,
      "action": "take",
      "message": "You take the red key from the wooden box.",
      "data": {
        "id": "item_red_key",
        "name": "key",
        "description": "An ornate red key...",
        "llm_context": {
          "traits": ["ornate", "red", "cold iron"],
          "state_variants": {...}
        }
      }
    }
    ↓
5. LLMNarrator determines verbosity:
    ├─ Check if item_red_key in examined_entities
    ├─ First examination → verbosity: "full"
    ├─ Add verbosity to result
    ├─ Mark item_red_key as examined
    ↓
6. LLMNarrator._call_llm() for narration:
    ├─ Send result + verbosity to Claude
    ├─ Claude generates prose from result + llm_context
    ├─ Return narrative
    ↓
7. Display to player:
    "You carefully lift the ornate red key from the wooden box.
    The cold iron feels heavy in your hand, and intricate runes
    gleam along its length."
```

## 3.3 Query Flow (Location)

```
Request: {"type": "query", "query_type": "location", "include": ["items", "doors", "exits"]}
    ↓
1. LLMProtocolHandler._query_location()
    ├─ Get current player location
    ├─ Get location object
    ├─ Call serialize_location_for_llm()
    │  ├─ Convert location to dict with llm_context
    │  ├─ Get items in location
    │  │  └─ Convert each to dict with llm_context
    │  ├─ Get doors (from exits with door_id)
    │  │  └─ Convert each to dict with llm_context
    │  ├─ Get exits
    │  │  └─ Include exit llm_context if present
    │  ├─ Get actors in location
    │  │  └─ Convert each to dict with llm_context
    │  └─ Return complete location data
    ├─ Filter to requested includes
    └─ Return query_response
```

---

# 4. Extension Points

## 4.1 Adding Core Behaviors

**When to extend core:**
- Fundamental game mechanic needed by most games
- Widely reusable functionality
- No game-specific logic

**Process:**
1. Create module in `behaviors/core/`
2. Export VOCABULARY (verbs with properties)
3. Write command handlers (`handle_*` functions)
4. Write entity behaviors (`on_*` functions) if needed
5. Add comprehensive tests
6. Update core behavior documentation

**Example: Adding "climb" verb**

```python
# behaviors/core/navigation.py

VOCABULARY = {
    "verbs": [
        {
            "word": "climb",
            "synonyms": ["scale", "ascend"],
            "object_required": True,
            "narration_mode": "brief"
        }
    ]
}

def handle_climb(accessor: StateAccessor, action: Dict) -> EventResult:
    """Handle climb command."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # Find climbable object in location
    obj_entry = action.get("object")
    if not obj_entry:
        return EventResult(success=False,
                         message="What do you want to climb?")

    entity = accessor.find_entity_in_location(
        obj_entry,
        actor.location,
        action.get("adjective")
    )

    if not entity:
        return EventResult(success=False,
                         message=f"You don't see {obj_entry.word} here.")

    if not entity.properties.get("climbable"):
        return EventResult(success=False,
                         message=f"You can't climb {entity.name}.")

    # Check for on_climb behavior
    if accessor.behavior_manager:
        result = accessor.behavior_manager.invoke_behavior(
            entity, "on_climb", accessor.state,
            {"actor_id": actor_id, "verb": "climb"}
        )
        if result and not result.allow:
            return EventResult(success=False, message=result.message)
        if result and result.message:
            return EventResult(success=True, message=result.message)

    return EventResult(success=True,
                      message=f"You climb {entity.name}.",
                      data={"id": entity.id, "name": entity.name})
```

## 4.2 Creating Behavior Libraries

**Purpose:** Reusable behavior packages for common game patterns

**Structure:**
```
behavior_libraries/
└── puzzle_lib/
    ├── __init__.py              # Package marker
    ├── sequence_tracker.py      # Sequence puzzles
    ├── threshold_checker.py     # Weight/resource puzzles
    └── state_revealer.py        # Hidden item revelation
```

**Library Module Pattern:**
```python
# behavior_libraries/puzzle_lib/sequence_tracker.py

# 1. Optional vocabulary
VOCABULARY = {
    "verbs": [
        {"word": "activate", "synonyms": ["trigger"], "object_required": True}
    ]
}

# 2. Optional command handlers
def handle_activate(accessor: StateAccessor, action: Dict) -> EventResult:
    """Generic activation handler that delegates to entity behavior."""
    # Implementation...

# 3. Utility functions for use in game behaviors
def track_action(entity, action_key: str) -> None:
    """Append action to entity's sequence."""
    if "sequence" not in entity.states:
        entity.states["sequence"] = []
    entity.states["sequence"].append(action_key)

def check_sequence(entity, expected: List[str]) -> bool:
    """Check if entity's sequence matches expected."""
    actual = entity.states.get("sequence", [])
    return actual == expected

def reset_sequence(entity) -> None:
    """Clear entity's sequence tracker."""
    entity.states["sequence"] = []
```

**Using Libraries in Games:**
```python
# examples/my_game/behaviors/music_puzzle.py
from behavior_libraries.puzzle_lib import sequence_tracker

def on_play(entity, accessor, context):
    """Handle playing the musical instrument."""
    note = context.get("note")

    # Use library function
    sequence_tracker.track_action(entity, note)

    # Check if sequence complete
    expected = ["C", "E", "G", "C"]
    if sequence_tracker.check_sequence(entity, expected):
        # Solve puzzle
        return EventResult(allow=True,
                         message="The melody unlocks the door!")

    return EventResult(allow=True)
```

## 4.3 Extending the Parser

**Adding new token types:**

Parser currently supports:
- VERB, NOUN, DIRECTION, ADJECTIVE, PREPOSITION

To add new token types:
1. Update `WordType` enum in `word_entry.py`
2. Update parser vocabulary loading
3. Update grammar rules in `parser.py`
4. Add test cases

**Modifying grammar:**

Grammar defined in `parser.py`:
```python
# Current patterns:
# [direction]
# [verb] [adjective*] [noun]
# [verb] [adjective*] [noun] [prep] [adjective*] [noun]
```

To add new patterns:
1. Add pattern to `_try_parse_*` methods
2. Update `ParsedCommand` if needed
3. Add comprehensive tests

**Example: Adding adverbs**
```python
# word_entry.py
class WordType(Enum):
    VERB = "verb"
    NOUN = "noun"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"  # New type
    # ...

# parser.py
def _try_parse_with_adverb(self, tokens: List[WordEntry]) -> Optional[ParsedCommand]:
    """Try to parse: [verb] [adverb] [object]
    Example: "take quickly key"
    """
    # Implementation...
```

## 4.4 Protocol Extensions

**Adding new query types:**

1. Add handler in `llm_protocol.py`:
```python
def handle_query(self, message: Dict) -> Dict:
    query_type = message.get("query_type")

    if query_type == "location":
        return self._query_location(message)
    # ... existing types ...
    elif query_type == "my_new_query":
        return self._query_my_new_type(message)
```

2. Implement query handler:
```python
def _query_my_new_type(self, message: Dict) -> Dict:
    """Handle my_new_query type."""
    # Extract parameters
    # Query state
    # Format response
    return {
        "type": "query_response",
        "query_type": "my_new_query",
        "data": {...}
    }
```

3. Document in protocol specification
4. Add tests

**Adding new command result fields:**

Result format is flexible - add any fields needed:
```python
return {
    "type": "result",
    "success": True,
    "action": "my_verb",
    "message": "Result message",
    "data": {...},
    "custom_field": "custom_value"  # New field
}
```

LLM narrator will have access to all fields.

---

# 5. Testing

## 5.1 Test Organization

```
tests/
├── test_state_manager.py       # Entity models, load/save
├── test_state_accessor.py      # StateAccessor API
├── test_behavior_manager.py    # Module loading, handlers
├── test_parser.py              # Command parsing
├── test_llm_protocol.py        # Protocol message handling
├── test_integration_*.py       # End-to-end scenarios
├── command_parser/             # Parser-specific tests
│   ├── test_parser.py
│   ├── test_vocabulary_loading.py
│   └── fixtures/
└── fixtures/                   # Test data
    ├── test_state.json
    └── test_vocabulary.json
```

## 5.2 Test Utilities

**Creating test state:**
```python
from tests.fixtures.test_state import create_test_state

def setUp(self):
    self.state = create_test_state()
    # State includes:
    # - Player actor
    # - Basic location
    # - Sample items
    # - No behaviors loaded
```

**Loading behaviors:**
```python
from pathlib import Path

def setUp(self):
    self.behavior_manager = BehaviorManager()
    behaviors_dir = Path(__file__).parent.parent / "behaviors"
    modules = self.behavior_manager.discover_modules(str(behaviors_dir))
    self.behavior_manager.load_modules(modules)
```

**Creating StateAccessor:**
```python
def setUp(self):
    self.state = create_test_state()
    self.manager = BehaviorManager()
    self.accessor = StateAccessor(self.state, self.manager)
```

## 5.3 Testing Behaviors

**Command handler tests:**
```python
def test_handle_take_success(self):
    """Test taking an item successfully."""
    # Arrange
    from behaviors.core.manipulation import handle_take

    item = Item(id="item_key", name="key", description="A key",
                location=self.state.actors["player"].location,
                properties={"portable": True}, behaviors=[])
    self.state.items.append(item)

    action = {
        "verb": "take",
        "object": WordEntry("key", WordType.NOUN, []),
        "actor_id": "player"
    }

    # Act
    result = handle_take(self.accessor, action)

    # Assert
    self.assertTrue(result.success)
    self.assertIn("item_key", self.state.actors["player"].inventory)
```

**Entity behavior tests:**
```python
def test_on_take_behavior(self):
    """Test entity behavior on take."""
    # Create item with behavior
    item = Item(id="item_magic", name="orb", description="Glowing orb",
                location="loc_room",
                properties={"portable": True, "magical": True},
                behaviors=["behaviors.magic_items"])

    # Load behavior module
    import behaviors.magic_items
    self.manager.load_module(behaviors.magic_items)

    # Take item
    action = {"verb": "take", "object": WordEntry("orb", ...), "actor_id": "player"}
    result = handle_take(self.accessor, action)

    # Verify behavior was invoked
    self.assertTrue(result.success)
    self.assertIn("glows", result.message.lower())
    self.assertTrue(item.states.get("glowing", False))
```

## 5.4 Integration Tests

**End-to-end command flow:**
```python
def test_integration_take_from_container(self):
    """Test full flow of taking item from container."""
    # Create container with item
    chest = Item(id="item_chest", name="chest", description="Wooden chest",
                 location="loc_room",
                 properties={"container": {"is_surface": False, "capacity": 10, "open": True}},
                 behaviors=[])

    key = Item(id="item_key", name="key", description="A key",
               location="item_chest",
               properties={"portable": True}, behaviors=[])

    self.state.items.extend([chest, key])

    # Process command through protocol handler
    message = {
        "type": "command",
        "action": {
            "verb": "take",
            "object": WordEntry("key", WordType.NOUN, []),
            "preposition": "from",
            "indirect_object": WordEntry("chest", WordType.NOUN, []),
            "actor_id": "player"
        }
    }

    result = self.handler.handle_message(message)

    # Verify result
    self.assertEqual(result["type"], "result")
    self.assertTrue(result["success"])
    self.assertIn("item_key", self.state.actors["player"].inventory)
```

## 5.5 Test Coverage

**Target coverage:** 80% for new code

**Running coverage:**
```bash
coverage run -m unittest discover tests
coverage report
coverage html
open htmlcov/index.html
```

**Critical coverage areas:**
- State manager: 90%+ (core data integrity)
- Protocol handler: 85%+ (command execution)
- Behavior manager: 85%+ (extension mechanism)
- Parser: 80%+ (common path optimization)
- StateAccessor: 85%+ (state consistency)

---

# 6. Debugging and Observability

## 6.1 Debug Flags

**Command-line flags:**
```bash
python -m src.llm_game examples/simple_game --debug           # Enable debug logging
python -m src.llm_game examples/simple_game --show-traits     # Print llm_context
python -m src.llm_game examples/simple_game --debug --show-traits  # Both
```

**Debug logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG,
                   format='[DEBUG] %(name)s: %(message)s')
```

Shows:
- Parser decisions (local vs LLM)
- Behavior loading
- Handler invocation
- API cache statistics

## 6.2 Trait Inspection

**--show-traits flag:**

Prints llm_context traits before each LLM narration:
```
[location traits: ancient stone, echoing halls, flickering torches]
[item_chest traits: ornate gold filigree, heavy oak, brass fittings]
[door_wooden traits: rough-hewn planks, iron hinges]
```

Useful for:
- Debugging narration issues
- Verifying trait randomization
- Understanding what LLM sees

## 6.3 State Inspection

**During test:**
```python
def test_debug_state(self):
    # Print entire state
    print(json.dumps(dataclasses.asdict(self.state), indent=2))

    # Print specific entity
    item = self.accessor.get_item("item_key")
    print(f"Item: {item.name}")
    print(f"Location: {item.location}")
    print(f"Properties: {item.properties}")
    print(f"States: {item.states}")
```

**Runtime inspection:**

Add debug prints in handlers:
```python
def handle_take(accessor, action):
    import sys
    print(f"DEBUG: action = {action}", file=sys.stderr)
    # ... rest of handler
```

## 6.4 Common Issues

**"Handler not found"**
- Behavior module not loaded
- Handler not exported at module level
- Handler name doesn't match `handle_<verb>` pattern
- Check: `behavior_manager.get_handler(verb)` returns None

**"Entity not found"**
- ID mismatch (check exact ID string)
- Entity in wrong location
- Name matching failed (check synonyms)
- Check: `accessor.find_entity_in_location(...)` returns None

**"State corrupted"**
- Inconsistent state detected during validation
- Save game and restart
- Check error message for details
- Usually caused by: invalid references, broken containment cycles

**"Behavior not invoked"**
- Entity missing behaviors list entry
- Event name doesn't match verb (`on_<verb>`)
- Behavior module not loaded
- Behavior function not at module level

---

# 7. Performance Considerations

## 7.1 Parser Optimization

**Fast path:**
- Trie-based vocabulary lookup: O(n) where n = input length
- Common commands (go, take, examine): < 1ms
- No LLM call for ~70% of commands

**Slow path:**
- LLM parsing for complex input: 200-500ms
- Only used when local parser returns None

## 7.2 LLM Call Optimization

**Prompt caching:**
- System prompt cached for 5 minutes
- Cache hit: 50-100ms vs 200-500ms cold
- Typical cache savings: 60-80% of input tokens

**Token usage:**
- System prompt: ~2000 tokens (cached)
- Per-turn input: 100-300 tokens
- Per-turn output: 50-150 tokens

**Cost optimization:**
- Use fast model for narration (Haiku)
- Cache system prompts
- Keep result JSON compact

## 7.3 State Access Patterns

**Efficient:**
```python
# Direct ID lookup
item = accessor.get_item(item_id)  # O(n) scan but unavoidable

# Location query (cached on Location object)
items = accessor.get_items_in_location(location_id)
```

**Inefficient:**
```python
# Multiple scans
for verb in all_verbs:
    handler = behavior_manager.get_handler(verb)  # Repeated lookups

# Better: Cache handlers dict
handlers = {v: behavior_manager.get_handler(v) for v in verbs}
```

## 7.4 Scaling Considerations

**Current limits:**
- ~1000 entities: No performance issues
- ~100 behaviors: Module loading < 100ms
- ~500 vocabulary entries: Trie builds in ~10ms

**Bottlenecks:**
- LLM API calls (200-500ms per call)
- Large location queries (many items/NPCs)
- Deep containment chains (items in items in items)

---

# 8. Code Style and Conventions

## 8.1 Python Style

**Follow:**
- PEP 8 for formatting
- Type hints for all public APIs
- Docstrings for all public functions/classes
- Prefer explicit over implicit

**Example:**
```python
def get_item(self, item_id: str) -> Optional[Item]:
    """Get item by ID.

    Args:
        item_id: The item's unique identifier

    Returns:
        Item object if found, None otherwise
    """
    for item in self.state.items:
        if item.id == item_id:
            return item
    return None
```

## 8.2 Naming Conventions

**Functions:**
- Command handlers: `handle_<verb>()` (e.g., `handle_take`)
- Entity behaviors: `on_<event>()` (e.g., `on_take`)
- Private methods: `_method_name()` (leading underscore)
- Queries: `get_<thing>()`, `find_<thing>()`

**Variables:**
- `snake_case` for variables and functions
- `PascalCase` for classes
- `UPPER_CASE` for module-level constants

**Entity IDs:**
- Recommended format: `<type>_<name>`
- Examples: `loc_tower`, `item_key`, `door_entrance`, `npc_guard`
- Special: `"player"` (reserved singleton)

## 8.3 Error Handling

**Design principle:** Fail fast during load, not during play

**Validation errors:**
```python
# Good: Fail during load_game_state()
if not metadata.start_location:
    raise ValidationError("metadata.start_location is required")

# Bad: Runtime check
if not metadata.start_location:
    return EventResult(success=False, message="No start location!")
```

**Runtime errors:**
```python
# Return EventResult for expected failures
if not entity:
    return EventResult(success=False, message=f"You don't see {word} here.")

# Raise exception for programmer errors
if not isinstance(entity, Item):
    raise TypeError(f"Expected Item, got {type(entity)}")
```

## 8.4 Testing Conventions

**Test naming:**
```python
def test_<function>_<scenario>_<expected_result>(self):
    """Test description."""
```

**Examples:**
```python
def test_handle_take_portable_item_success(self):
    """Test taking a portable item succeeds."""

def test_handle_take_nonportable_item_fails(self):
    """Test taking non-portable item fails with error."""

def test_handle_take_item_not_in_location_fails(self):
    """Test taking item not in location fails."""
```

**Test structure (AAA):**
```python
def test_something(self):
    # Arrange - Set up test state
    item = Item(...)
    self.state.items.append(item)

    # Act - Perform action
    result = handle_take(self.accessor, action)

    # Assert - Verify results
    self.assertTrue(result.success)
    self.assertIn(item.id, self.state.actors["player"].inventory)
```

---

# 9. Contributing

## 9.1 Development Workflow

1. **Create issue** describing the feature/bug
2. **Discuss approach** in issue comments
3. **Write tests first** (TDD)
4. **Implement feature** with tests passing
5. **Update documentation** (docstrings, this guide)
6. **Submit pull request** referencing issue
7. **Code review** and iteration
8. **Merge** when approved

## 9.2 Pull Request Guidelines

**PR must include:**
- Clear description of changes
- Reference to issue number
- New tests for new functionality
- All tests passing
- Updated documentation
- No decrease in test coverage

**PR should not include:**
- Unrelated changes
- Commented-out code
- Debug print statements
- Formatting-only changes mixed with logic

## 9.3 Code Review Checklist

**Functionality:**
- [ ] Does it solve the stated problem?
- [ ] Are edge cases handled?
- [ ] Is error handling appropriate?

**Testing:**
- [ ] Are there comprehensive tests?
- [ ] Do all tests pass?
- [ ] Is coverage maintained/improved?

**Code Quality:**
- [ ] Follows style conventions?
- [ ] Clear naming?
- [ ] Appropriate comments/docstrings?
- [ ] No code duplication?

**Architecture:**
- [ ] Fits with existing design?
- [ ] Uses appropriate extension points?
- [ ] Doesn't introduce tight coupling?

**Documentation:**
- [ ] Public APIs documented?
- [ ] Complex logic explained?
- [ ] User-facing docs updated?

---

# 10. Advanced Topics

## 10.1 Custom Validators

Add custom validation beyond structural checks:

```python
# In validators.py or custom module
def validate_custom_rules(state: GameState) -> List[str]:
    """Custom validation rules for specific game requirements."""
    errors = []

    # Example: All doors must have locks
    for item in state.items:
        if item.is_door and not item.door_lock_id:
            errors.append(f"Door {item.id} has no lock")

    # Example: All containers must have capacity
    for item in state.items:
        if item.container and item.container.capacity == 0:
            errors.append(f"Container {item.id} has unlimited capacity")

    return errors

# Call during load
errors = validate_custom_rules(state)
if errors:
    raise ValidationError("Custom validation failed", errors)
```

## 10.2 Custom Entity Types

While not recommended (use properties instead), you can add entity types:

```python
# In state_manager.py
@dataclass
class Quest:
    """Quest tracking entity."""
    id: str
    name: str
    description: str
    objectives: List[str]
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)

# In GameState
@dataclass
class GameState:
    # ... existing fields ...
    quests: List[Quest] = field(default_factory=list)

# Add accessor methods
class StateAccessor:
    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get quest by ID."""
        for quest in self.state.quests:
            if quest.id == quest_id:
                return quest
        return None
```

## 10.3 State Migration Tools

Create migration tools for schema changes:

```python
# tools/migrate_v1_to_v2.py
def migrate_game_state(old_state: Dict) -> Dict:
    """Migrate game state from v1 to v2 format."""
    new_state = old_state.copy()

    # Example: Rename field
    if "old_field" in new_state:
        new_state["new_field"] = new_state.pop("old_field")

    # Example: Restructure data
    for item in new_state["items"]:
        if "container_data" in item:
            item["properties"]["container"] = item.pop("container_data")

    # Update schema version
    new_state["metadata"]["schema_version"] = "v_0.02"

    return new_state

if __name__ == "__main__":
    with open("old_game.json") as f:
        old = json.load(f)

    new = migrate_game_state(old)

    with open("new_game.json", "w") as f:
        json.dump(new, f, indent=2)
```

## 10.4 Performance Profiling

Profile engine performance:

```python
import cProfile
import pstats

def profile_command(handler, command):
    """Profile a single command execution."""
    profiler = cProfile.Profile()
    profiler.enable()

    result = handler.handle_message(command)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumtime')
    stats.print_stats(20)  # Top 20 functions

    return result

# Usage:
message = {"type": "command", "action": {"verb": "take", ...}}
result = profile_command(handler, message)
```

---

# 11. Glossary

**Actor** - Player or NPC entity with location and inventory

**Behavior** - Python code that responds to events or commands

**Behavior Manager** - System that loads and manages behavior modules

**Behavior Module** - Python file that exports vocabulary, handlers, and/or behaviors

**Command Handler** - Function that processes a verb command (handle_*)

**Container** - Item with container property that can hold other items

**Entity** - Generic term for any game object (Item, Actor, Location, etc.)

**Entity Behavior** - Function attached to specific entity that responds to events (on_*)

**Event** - Something that happens in the game (take, drop, open, etc.)

**EventResult** - Return value from behaviors indicating allow/deny and message

**Exit** - Connection from one location to another

**GameState** - Complete game state including all entities

**Handler Chain** - Multiple handlers for same verb, invoked by precedence

**LLM Context** - Descriptive data (traits, state variants) for LLM narration

**Location** - Room or place in the game world

**ParsedCommand** - Structured output from parser

**Properties Dict** - Flexible key-value storage on entities

**Protocol Handler** - Implements JSON message protocol

**StateAccessor** - Unified API for querying and modifying game state

**States Dict** - Dynamic state flags within properties dict

**Three-tier Hierarchy** - Game > Library > Core behavior precedence

**UpdateResult** - Return value from state updates

**Verbosity** - Narration detail level (full/brief)

**WordEntry** - Vocabulary entry with word, type, and synonyms

---

# 12. References

## 12.1 Key Design Documents

- `docs/behavior_refactoring.md` - Behavior system design (historical)
- `docs/layered_game_design.md` - Three-tier hierarchy design
- `docs/ID_NAMESPACE_DESIGN.md` - Entity ID system
- `docs/game_state_example.md` - JSON format examples
- `Archive/entity_behaviors.md` - Original behavior design

## 12.2 Example Code

- `examples/simple_game/` - Basic game demonstrating core features
- `examples/extended_game/` - Advanced features and behaviors
- `examples/layered_game/` - Three-tier behavior hierarchy
- `behaviors/core/` - Core behavior implementations
- `behavior_libraries/` - Reusable behavior libraries

## 12.3 Test Examples

- `tests/test_integration_*.py` - End-to-end test patterns
- `tests/test_behavior_*.py` - Behavior system test patterns
- `tests/test_state_*.py` - State management test patterns

---

# Appendix A: Module Dependency Graph

```
llm_game.py
    └── game_engine.py
        ├── state_manager.py
        │   └── word_entry.py
        ├── behavior_manager.py
        │   └── state_accessor.py
        │       └── state_manager.py
        └── llm_narrator.py
            ├── llm_protocol.py
            │   ├── state_manager.py
            │   ├── behavior_manager.py
            │   └── state_accessor.py
            └── parser.py
                ├── word_entry.py
                └── parsed_command.py

behaviors/core/*
    ├── state_accessor.py (imported by all)
    └── word_entry.py (for VOCABULARY)

utilities/*
    └── state_manager.py (entity types)
```

# Appendix B: JSON Protocol Quick Reference

**Command:**
```json
{
  "type": "command",
  "action": {
    "verb": "string",
    "object": "WordEntry or string",
    "adjective": "string (optional)",
    "preposition": "string (optional)",
    "indirect_object": "WordEntry or string (optional)",
    "indirect_adjective": "string (optional)",
    "actor_id": "string (default: player)"
  }
}
```

**Query:**
```json
{
  "type": "query",
  "query_type": "location|entity|entities|vocabulary|metadata",
  "include": ["items", "doors", "exits", "actors"],
  "entity_type": "item|door|npc|location",
  "entity_id": "string",
  "location_id": "string",
  "actor_id": "string"
}
```

**Result:**
```json
{
  "type": "result",
  "success": true|false,
  "action": "string",
  "message": "string",
  "data": {...},
  "error": {"message": "string", "fatal": true|false}
}
```

# Appendix C: Common Patterns

**Pattern: Adding a new verb**
1. Add to VOCABULARY in behavior module
2. Write `handle_<verb>()` function
3. Extract and validate action parameters
4. Resolve entities with StateAccessor
5. Check entity behaviors
6. Update state if needed
7. Return EventResult
8. Write comprehensive tests

**Pattern: Entity-specific behavior**
1. Write `on_<event>()` function in behavior module
2. Add behavior module path to entity's behaviors list
3. Behavior checks conditions
4. Modifies entity state if needed
5. Returns EventResult with allow/deny and message
6. Handler respects behavior result

**Pattern: Chained handlers**
1. Higher-precedence handler does specialized logic
2. Calls `accessor.invoke_previous_handler(verb, action)`
3. Lower-precedence handler provides default logic
4. Return combined or modified result

**Pattern: State updates with behaviors**
1. Use `accessor.update(entity, changes, verb=verb)`
2. StateAccessor invokes entity behaviors
3. Behaviors can deny update (allow=False)
4. Changes applied only if all behaviors allow
5. Result includes behavior message
