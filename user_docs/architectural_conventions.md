# Architectural Conventions

This document codifies the de facto standard types, calling conventions, and data structures used throughout the text-game engine. All code—including tests—must adhere to these conventions.

---

## 1. Core Entity Types

All entities share a common structure:

```python
@dataclass
class Entity:
    id: str                              # Unique identifier
    name: str                            # Display name
    description: str                     # Base description
    properties: Dict[str, Any]           # Flexible property storage
    behaviors: List[str]                 # Module paths for behaviors
```

### Entity-Specific Fields

| Entity | Additional Required Fields |
|--------|---------------------------|
| Location | `exits: Dict[str, ExitDescriptor]` |
| Item | `location: str` (where item is) |
| Actor | `location: str`, `is_player: bool` |
| Part | `part_of: str` (parent entity ID) |
| Lock | `locked: bool`, `key_id: Optional[str]` |
| ExitDescriptor | `type: str` ("open" or "door"), `to: Optional[str]` |

### Property Accessors

Entities provide convenience accessors for common nested properties:

```python
entity.states         # properties.get("states", {}) with auto-init
entity.llm_context    # properties.get("llm_context")
item.portable         # properties.get("portable", False)
item.container        # ContainerInfo wrapper or None
actor.stats           # properties.get("stats", {})
```

---

## 2. ID Naming Conventions

Use descriptive prefixes to indicate entity type:

| Entity Type | Prefix | Examples |
|------------|--------|----------|
| Location | `loc_` | `loc_tower`, `loc_throne_room` |
| Item | `item_` | `item_key`, `item_chest` |
| Actor (NPC) | `npc_` | `npc_guard`, `npc_wizard` |
| Actor (creature) | `creature_` | `creature_wolf`, `creature_spider` |
| Door | `door_` | `door_entrance`, `door_secret` |
| Lock | `lock_` | `lock_treasure`, `lock_gate` |
| Part | `part_` | `part_throne_north_wall` |
| Exit | `exit:` | `exit:loc_study:north` (synthesized) |

**Reserved IDs:**
- `player` - The player character (singleton)

---

## 3. Handler Calling Conventions

### Command Handlers

**Signature:** `handle_<verb>(accessor, action) -> HandlerResult`

```python
def handle_take(accessor: StateAccessor, action: Dict[str, Any]) -> HandlerResult:
    """Handle take/get/grab command."""
    ...
```

**Action Dict Structure:**
```python
{
    "verb": str,                    # Canonical verb from vocabulary
    "object": WordEntry | str,      # Target entity (use .word for string)
    "adjective": Optional[str],     # Disambiguator ("old" in "take old key")
    "actor_id": str,                # Who's acting (defaults to "player")
    "direction": Optional[str],     # For movement commands
    "preposition": Optional[str],   # For complex verbs ("put X on Y")
    "indirect_object": Optional[str],
    "indirect_adjective": Optional[str],
}
```

**HandlerResult:**
```python
@dataclass
class HandlerResult:
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None  # Extra info (llm_context, etc.)
```

### Entity Behavior Handlers

**Signature:** `on_<event>(entity, accessor, context) -> EventResult`

```python
def on_take(entity, accessor: StateAccessor, context: Dict[str, Any]) -> EventResult:
    """Called when this entity is taken."""
    ...
```

**Context Dict:**
```python
{
    "actor_id": str,        # Who performed the action
    "verb": str,            # What verb triggered this
    "changes": Dict,        # What was changed (optional)
    "adjective": str,       # Optional: adjective used
    "location": str,        # Optional: location context
}
```

**EventResult:**
```python
@dataclass
class EventResult:
    allow: bool                      # Whether action proceeds
    message: Optional[str] = None    # Narration text
```

---

## 4. StateAccessor API

All state queries go through StateAccessor. Never access GameState internals directly.

### Query Methods

```python
accessor.get_item(item_id: str) -> Optional[Item]
accessor.get_actor(actor_id: str) -> Optional[Actor]
accessor.get_location(location_id: str) -> Optional[Location]
accessor.get_lock(lock_id: str) -> Optional[Lock]
accessor.get_part(part_id: str) -> Optional[Part]
accessor.get_door_item(door_id: str) -> Optional[Item]
accessor.get_parts_of(entity_id: str) -> List[Part]
accessor.get_items_at_part(part_id: str) -> List[Item]
accessor.get_current_location(actor_id: str) -> Optional[Location]
```

**Convention:** All getters return `None` if not found. Check return values.

### State Access

```python
accessor.game_state          # The GameState object
accessor.behavior_manager    # The BehaviorManager instance
```

---

## 5. Vocabulary Conventions

### Module Vocabulary Structure

```python
vocabulary = {
    "verbs": [
        {
            "word": "take",
            "event": "on_take",           # Entity behavior event
            "synonyms": ["get", "grab"],
            "object_required": True,      # True, False, or "optional"
            "narration_mode": "brief",    # Optional: brief, full, tracking
            "fallback_event": "on_drop",  # Optional: fallback if primary fails
        }
    ],
    "nouns": [...],
    "adjectives": [...],
    "directions": [...],
    "events": [                           # Hook registrations
        {
            "event": "on_npc_turn",
            "hook": "npc_action",
            "description": "Called during NPC phase"
        }
    ]
}
```

### WordEntry Structure

```python
@dataclass
class WordEntry:
    word: str
    word_type: Union[WordType, Set[WordType]]  # Single or multi-type
    synonyms: List[str] = field(default_factory=list)
    value: Optional[int] = None
    object_required: bool | str = True
```

**Multi-Type Words:** When a word serves multiple grammatical roles (e.g., "north" as direction and adjective), it becomes multi-type with merged synonyms.

### Word Matching Rules

- **NEVER** build vocabulary into code
- **ALWAYS** use the merged vocabulary and WordEntry
- **NEVER** add local heuristics for word matching
- These rules apply to tests as well as normal code

---

## 6. Global State Storage

### GameState.extra

For game-wide state not tied to specific entities:

```python
state.extra["scheduled_events"] = [...]
state.extra["faction_relations"] = {...}
state.extra["regions"] = {...}
state.extra["flags"] = {...}  # Global game flags
```

### Actor Flags (per-actor persistent state)

```python
# Via GameState convenience methods
state.set_flag("met_wizard", True)       # Sets on player
state.get_flag("met_wizard", False)

# Direct access
actor.properties.setdefault("flags", {})["quest_stage"] = 2
```

---

## 7. Behavior Module Structure

```python
# 1. VOCABULARY - Define new verbs, nouns, events
vocabulary = {
    "verbs": [...],
    "events": [...]
}

# 2. COMMAND HANDLERS - handle_<verb>
def handle_take(accessor, action):
    """Process take command."""
    return HandlerResult(...)

# 3. ENTITY BEHAVIORS - on_<event>
def on_take(entity, accessor, context):
    """Triggered when entity is taken."""
    return EventResult(...)
```

### Handler Tier System

Handlers are prioritized by tier (lower = higher precedence):
1. **Tier 1:** Game-specific handlers
2. **Tier 2:** Library handlers (behavior_libraries/)
3. **Tier 3:** Core handlers (behaviors/core/)

---

## 8. Error Handling Conventions

### Design Principle: Fail Fast During Load

```python
# GOOD: Fail at load time
if not metadata.start_location:
    raise ValidationError("metadata.start_location is required")

# BAD: Silent runtime failure
if not metadata.start_location:
    return EventResult(success=False, message="No start location")
```

### Error Categories

| Category | Handling |
|----------|----------|
| Validation errors | Raise exception at load time |
| User action failures | Return EventResult/HandlerResult with message |
| Inconsistent state | Prefix with "INCONSISTENT STATE:" (indicates bug) |
| Fatal errors | Include `"fatal": True` in result data |

---

## 9. Testing Conventions

### Subprocess Isolation Pattern

Tests for games with custom behaviors use subprocess isolation:

```
tests/
├── test_<game>_scenarios.py      # Wrapper - runs in subprocess
└── _<game>_scenarios_impl.py     # Implementation - actual tests
```

**Why:** Python caches modules by name. Each game has its own `behaviors/` directory. Subprocess ensures fresh Python state.

### Path Setup for Tests

```python
def _setup_paths():
    """Ensure paths are set up for imports."""
    # Remove CWD to prevent wrong behaviors/ from loading
    while '' in sys.path:
        sys.path.remove('')

    # Add game directory first (for behaviors imports)
    sys.path.insert(0, str(GAME_DIR))
    # Add project root second (for src imports)
    sys.path.insert(1, str(PROJECT_ROOT))
```

### Test Naming Convention

```python
def test_<function>_<scenario>_<expected_result>(self):
    """Descriptive docstring."""

# Examples:
def test_handle_take_portable_item_success(self):
def test_handle_take_nonportable_item_fails(self):
```

### Testing Handler Calls

Tests must use the same calling conventions as the engine:

```python
# CORRECT: Use proper action dict
result = handle_take(accessor, {
    "actor_id": "player",
    "verb": "take",
    "object": word_entry,  # WordEntry, not raw string
})

# WRONG: Ad-hoc action structure
result = handle_take(accessor, {"target": "key"})
```

---

## 10. LLM Context Conventions

### Structure

```json
{
  "llm_context": {
    "traits": [
      "weathered oak planks",
      "iron-reinforced corners",
      "musty interior smell"
    ],
    "state_variants": {
      "lit": "glowing warmly",
      "open": "lid thrown back"
    },
    "atmosphere": "mysterious, foreboding"
  }
}
```

### Narration Modes

| Mode | Usage |
|------|-------|
| `brief` | Routine interactions, repeated actions |
| `full` | First examination, important events |
| `tracking` | Full first time, brief subsequent |

---

## 11. Scheduled Events Architecture

The scheduling system has two layers:

1. **timing_lib** - Infrastructure: stores events, checks deadlines, fires events
2. **Game event handler** - Game logic: implements what each event DOES

```python
# Scheduling (timing_lib)
schedule_event(accessor, "on_cave_collapse", trigger_turn=50, data={...})

# Handling (your game's behavior module)
def on_world_event_check(entity, accessor, context):
    event_name = context.get('event_name')
    if event_name == "on_cave_collapse":
        # Implement collapse effects
        return EventResult(allow=True, message="The cave collapses!")
```

**Critical:** `timing_lib` does NOT know what events do. Your game must implement the handler.

---

## 12. Common Patterns

### Standard Handler Preamble

```python
from utilities.handler_utils import validate_actor_and_location

def handle_take(accessor, action):
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    # Continue with handler logic...
```

### Entity Type Checking

Handlers should test positively for what they CAN handle:

```python
# GOOD: Check for expected type, reject others
def handle_climb(accessor, action):
    target = resolve_target(accessor, action)
    if not target.properties.get("climbable"):
        return HandlerResult(success=False, message="You can't climb that.")
    # Handle climbing...

# BAD: Check for all types it CAN'T handle
def handle_climb(accessor, action):
    if isinstance(target, Actor):
        return HandlerResult(success=False, ...)
    if isinstance(target, Location):
        return HandlerResult(success=False, ...)
    # etc...
```

### Behavior Event Invocation

```python
# Get events for a verb
events = behavior_manager.get_events_for_verb("take")

# Invoke behavior on entity
result = behavior_manager.invoke_behavior(
    entity,
    "on_take",
    accessor,
    context={"actor_id": "player", "verb": "take"}
)
```

---

## 13. Data Serialization

### Game State JSON Structure

```json
{
  "metadata": {
    "schema_version": "v_0.01",
    "title": "Game Name",
    "start_location": "loc_entrance"
  },
  "locations": [...],
  "items": [...],
  "locks": [...],
  "actors": {...},
  "parts": [...],
  "extra": {...}
}
```

| Field | Type | Notes |
|-------|------|-------|
| locations | Array | ID-keyed lookup after load |
| items | Array | ID-keyed lookup after load |
| locks | Array | Referenced by ID |
| actors | Dict | Keyed by actor ID |
| parts | Array | Spatial components |
| extra | Dict | Global game state |

---

## Summary: Key Rules

1. **Use StateAccessor** for all state queries
2. **Follow handler signatures exactly** - `(accessor, action)` or `(entity, accessor, context)`
3. **Return correct types** - HandlerResult for commands, EventResult for behaviors
4. **Use vocabulary** - never hardcode word matching
5. **Fail fast at load time** - validate during initialization
6. **Test with proper calling conventions** - same as engine
7. **Use subprocess isolation** for game-specific tests
8. **Prefix IDs correctly** - `loc_`, `item_`, `npc_`, etc.
