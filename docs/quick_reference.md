# Quick Reference Guide

## Critical Rules (Common Failure Points)

### Vocabulary
- **Multi-word names**: Every word BEFORE the final noun MUST be added as an adjective
  - "cold weather gear" → add "cold", "weather" as adjectives
  - "stone pillar" → add "stone" as adjective
- **No hardcoded vocabulary**: ALWAYS use merged vocabulary and WordEntry
- **Multi-type words**: Use `"word_type": ["verb", "noun"]` when needed (e.g., "water", "open")

### Walkthroughs (MANDATORY)
1. Write walkthrough file BEFORE implementation
2. Run: `python tools/walkthrough.py examples/big_game --file walkthroughs/[feature].txt`
3. Fix ALL failures until 100% success
4. ONLY THEN mark complete
- Never ship without 100% walkthrough success

### State Access
- ✅ `accessor.game_state` (correct)
- ❌ `accessor.state` (doesn't exist)
- ✅ `state.get_item(id)` (fail-fast - raises KeyError)
- ❌ `state.items.get(id)` (wrong - items is a list)
- ✅ `state.get_actor(id)` and `accessor.get_actor(id)` (both fail-fast - raise KeyError)
- ⚠️ `state.actors.get(id)` (only when None is valid/expected - optional NPCs)
- ❌ `state.actors[id]` (no clear error message)

### Handler Protocol
- Action dict contains **WordEntry objects**, not strings
- Extract with: `word_entry.word` or `_extract_word(word_entry)`
- Always include: `data=serialize_for_handler_result(entity, accessor, actor_id)`
- Inventory: Set location AND append to inventory list

### Error Handling
- **Fail loudly** for developer/authoring errors (missing modules, invalid paths, authoring mistakes)
- **No defensive try/except** that masks bugs - exceptions should propagate
- Examples of errors that MUST propagate:
  - Missing behavior modules → ImportError
  - Missing behavior functions → AttributeError
  - Invalid behavior paths → ValueError
  - Missing actors/items when they should exist → KeyError
  - Removing non-existent item from list → ValueError
- Only catch exceptions developers cannot prevent (external I/O, user input at boundaries)
- Validate at load time, not runtime

## Return Types

```python
# Event handlers (behavior hooks)
EventResult(allow=True, feedback="message")

# Command handlers
HandlerResult(success=True, primary="message", data=serialized_entity)
```

## Standard Patterns

### Command Handler Preamble
```python
def handle_verb(accessor, action):
    item, error = find_action_target(accessor, action)
    if error:
        return error
    actor_id = action.get("actor_id") or ActorId("player")
    # ... handler logic
```

### Extended Preamble
```python
def handle_verb(accessor, action):
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error
    # ... handler logic
```

### Event Handler
```python
def on_event(entity, accessor, context):
    state = accessor.game_state
    # Check conditions, perform state changes
    return EventResult(allow=True, feedback="message")
```

## Essential Imports

```python
# Core
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult, StateAccessor
from src.types import ActorId, LocationId, ItemId
from src.word_entry import WordEntry

# Utilities
from utilities.handler_utils import (
    validate_actor_and_location, find_action_target,
    transfer_item_to_actor, get_object_word
)
from utilities.utils import find_accessible_item, name_matches, _extract_word
from utilities.entity_serializer import serialize_for_handler_result

# Infrastructure
from src.infrastructure_utils import (
    get_current_state, transition_state, modify_trust,
    get_bool_flag, set_bool_flag, create_gossip
)
```

## Vocabulary Structure

```python
vocabulary: Dict[str, Any] = {
    "verbs": [
        {
            "word": "water",
            "word_type": ["verb", "noun"],  # Multi-type
            "event": "on_water",
            "object_required": True,
            "synonyms": ["pour"]
        }
    ],
    "adjectives": [
        {"word": "cold", "synonyms": []},  # For "cold weather gear"
        {"word": "weather", "synonyms": []}
    ],
    "nouns": [
        {"word": "heartmoss", "synonyms": ["moss"]}
    ],
    "events": [
        {
            "event": "on_spore_mother_talk",
            "hook": "on_talk",
            "entity_filter": "npc_spore_mother"
        }
    ]
}
```

## Handler Design
- Test positively for what you CAN handle
- Check if entity is right type, return failure if not
- No cross-module dependencies

## Development Workflows

**Workflow A** (small/moderate changes):
1. Discuss → analyze → choose solution
2. Create issue, describe problem
3. Add design comment
4. TDD implementation
5. Add work summary comment
6. Close issue

**Workflow B** (large changes):
1. Discuss → analyze
2. Create issue
3. Propose solution, discuss
4. Write design doc with phases
5. Add design comment to issue
6. Create phase issues, TDD each phase
7. Add phase summary, close phase issue
8. When done, summarize and close main issue

## Code Style
- Fully typed, no loose types without discussion
- Prefer composition over inheritance, explicit over implicit
- NEVER add backward compatibility in code (use migration tools)
- Use `tools/refactor_using_LibCST` for refactoring, NEVER sed
- Review for consistency, reuse existing code, merge similar paths

## Testing
- Use unittest (not pytest)
- Tests use same interfaces as production code (no test-specific shortcuts)
- 80% coverage target
- Memorialize bugs with new tests

## Design Priorities
- Maximize author capability and player agency
- Separation: Engine manages state, LLM narrates
- Behavior-driven extension via external modules
- Validation at load, not runtime
- Fail fast during development

## Common Utilities

```python
# State access - Fail-fast pattern (catches authoring errors immediately)
player = state.get_actor(ActorId("player"))  # Raises KeyError if missing
actor = accessor.get_actor(actor_id)  # Raises KeyError if missing (same behavior)
item = state.get_item(ItemId("sword"))  # Raises KeyError if missing
location = state.get_location(LocationId("cave"))  # Raises KeyError if missing

# Optional actors (only when None is a valid/expected response)
npc = state.actors.get("npc_guard")  # Returns Optional[Actor] - use for optional NPCs

# State machines
sm = actor.properties.get("state_machine", {})
current = get_current_state(sm)
success, msg = transition_state(sm, "friendly")

# Flags
flags = state.extra.get("flags", {})
if get_bool_flag(flags, "key_found"):
    set_bool_flag(flags, "door_unlocked", True)

# Trust
new_trust = modify_trust(current, delta=+1, floor=-5, ceiling=5)

# Finding entities
item = find_accessible_item(accessor, word_entry, actor_id, adjective)
actor = find_actor_by_name(accessor, word_entry, searching_actor_id)
if name_matches(word_entry, "Spore Mother"):
    # Matches synonyms too
```

## Debugging

```bash
# Run tests
python -m unittest discover -s tests -p "test_*.py"

# Walkthrough
python tools/walkthrough.py examples/big_game "cmd1" "cmd2"
python tools/walkthrough.py examples/big_game --file walkthroughs/test.txt

# Refactor
python tools/refactor_using_LibCST --dry-run src/
```

## Checklist for New Handlers

**Before Implementation**:
- [ ] Walkthrough file created
- [ ] Multi-word names identified for vocabulary

**During Implementation**:
- [ ] Correct imports (EventResult/HandlerResult)
- [ ] Standard preamble (find_action_target/validate_actor_and_location)
- [ ] Use `accessor.game_state`
- [ ] Extract WordEntry with helpers
- [ ] Include serialized data in results
- [ ] Adjective vocabulary for ALL words before final noun

**Before Completion**:
- [ ] Walkthrough run: 100% success
- [ ] Results in issue comment
- [ ] Close issue

## Red Flags (Stop and Discuss)
- Event handler names don't match event names in vocabulary
- Behavior module paths don't match actual load paths
- Claiming "mostly working" without 100% walkthrough
- Adding try/except for authoring/coding errors
- Adding backward compatibility code
- Loose types or `Any` without justification
