# Claude Session Guide - AI Assistant Quick Start

**Purpose:** Essential patterns and gotchas for AI assistants working on this codebase. Read this FIRST, consult detailed guides when stuck.

---

## Critical Gotchas (Most Common Mistakes)

### 1. State Access - WRONG Attribute Names ❌

```python
# WRONG - accessor.state doesn't exist
state = accessor.state  # AttributeError!

# RIGHT - use accessor.game_state
state = accessor.game_state
```

### 2. Item Access - Items is a LIST, not a Dict ❌

```python
# WRONG - items is a list, not a dict
item = state.items.get(item_id)  # AttributeError!

# RIGHT - use get_item() method
item = state.get_item(ItemId("sword"))  # Raises KeyError if missing (fail-fast)
```

### 3. Actor Access - Use get_actor() for Fail-Fast ❌

```python
# RISKY - Returns None silently if actor doesn't exist
actor = state.actors.get(actor_id)  # Only use for optional NPCs!

# RIGHT - Fails loudly if actor missing (catches authoring errors)
actor = state.get_actor(ActorId("player"))  # Raises KeyError
actor = accessor.get_actor(actor_id)  # Same behavior, either works
```

### 4. WordEntry vs Strings - Extract First ❌

```python
# WRONG - action values are WordEntry objects, not strings
def handle_verb(accessor, action):
    object_name = action.get("object")  # This is a WordEntry!
    if object_name == "sword":  # This comparison fails!
        ...

# RIGHT - extract the string
from utilities.utils import _extract_word

def handle_verb(accessor, action):
    object_name = action.get("object")
    word_str = _extract_word(object_name)  # Now it's a string
    if word_str == "sword":
        ...
```

### 5. Multi-Word Names - MUST Add Adjective Vocabulary ❌

```python
# Item: "cold weather gear"
# Parser sees: NOUN + NOUN + NOUN (parse fails!)

# FIX - Add adjectives in behavior vocabulary:
vocabulary: Dict[str, Any] = {
    "adjectives": [
        {"word": "cold", "synonyms": []},
        {"word": "weather", "synonyms": []}
    ]
}
# Now parser sees: ADJ + ADJ + NOUN (parse succeeds!)
```

**Rule:** Every word BEFORE the final noun in multi-word names MUST be added as an adjective.

### 6. Behavior Dispatch - NEVER Call Handlers Directly ❌

```python
# WRONG - calling handler directly
result = on_damage(entity, accessor, context)

# RIGHT - always use dispatch
result = accessor.behavior_manager.invoke_behavior(
    entity, "on_damage", accessor, context
)
```

**No exceptions.** Even "infrastructure" behaviors use dispatch.

### 7. Inventory Operations - Set Location AND Append to List ❌

```python
# WRONG - only sets location, doesn't update inventory list
item.location = "player"

# RIGHT - set location AND append to inventory
item.location = "player"
player = state.actors.get("player")
if player and item.id not in player.inventory:
    player.inventory.append(item.id)

# BETTER - use utility function
from utilities.handler_utils import transfer_item_to_actor
result, error = transfer_item_to_actor(
    accessor, item, actor, actor_id,
    verb="take",
    item_changes={"location": actor_id}
)
```

### 8. Walkthrough Discipline - Never Ship Without 100% Success ❌

```python
# WRONG - marking work complete without walkthrough
# "Feature is mostly working, just needs testing"

# RIGHT - ALWAYS run walkthrough BEFORE claiming complete
python tools/walkthrough.py examples/big_game --file walkthroughs/feature.txt
# Fix ALL failures until 100% success
# Paste results in issue comment
# ONLY THEN close issue
```

### 9. Exception Handling - Fail Loudly for Authoring Errors ❌

```python
# WRONG - masking authoring/coding errors
try:
    module = importlib.import_module(behavior_path)
except ImportError:
    pass  # Silent failure - bug goes undetected!

# RIGHT - let authoring errors propagate
module = importlib.import_module(behavior_path)
# ImportError will surface immediately during development
```

**Only catch exceptions for external/runtime issues** (I/O, user input at boundaries).

### 10. Handler Result Serialization - Always Include Data ❌

```python
# WRONG - missing serialized data for narrator
return HandlerResult(
    success=True,
    primary="You examine the door."
)

# RIGHT - include serialized entity data
from utilities.entity_serializer import serialize_for_handler_result

return HandlerResult(
    success=True,
    primary="You examine the door.",
    data=serialize_for_handler_result(door, accessor, actor_id)
)
```

---

## Standard Patterns (Copy-Paste Templates)

### Basic Command Handler

```python
from src.state_accessor import HandlerResult
from utilities.handler_utils import find_action_target
from utilities.entity_serializer import serialize_for_handler_result

def handle_read(accessor, action):
    """Handle read command."""
    item, error = find_action_target(accessor, action)
    if error:
        return error

    actor_id = action.get("actor_id") or ActorId("player")

    # Check if readable
    if not item.properties.get("readable", False):
        return HandlerResult(
            success=False,
            primary=f"You can't read the {item.name}."
        )

    text = item.properties.get("text", "")
    return HandlerResult(
        success=True,
        primary=f"You read the {item.name}: {text}",
        data=serialize_for_handler_result(item, accessor, actor_id)
    )
```

### Extended Command Handler (with Actor/Location Validation)

```python
from utilities.handler_utils import validate_actor_and_location

def handle_put(accessor, action):
    """Handle put X in/on Y command."""
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action,
        require_object=True,
        require_indirect_object=True
    )
    if error:
        return error

    # Now have: actor_id, actor, location all validated
    object_name = action.get("object")
    container_name = action.get("indirect_object")
    # ... continue with handler logic
```

### Event Handler (Entity Behavior)

```python
from src.behavior_manager import EventResult

def on_take(entity, accessor, context):
    """Called when entity is taken."""
    state = accessor.game_state

    # Check conditions
    if entity.properties.get("cursed", False):
        return EventResult(
            allow=False,
            feedback="The item burns your hand! You can't pick it up."
        )

    # Allow with custom message
    return EventResult(
        allow=True,
        feedback="The item feels warm to the touch."
    )
```

---

## Behavior Architecture in 60 Seconds

### Three-Tier System

**Tier 1 (Game-specific):** Your game's `behaviors/` directory - highest priority
**Tier 2 (Infrastructure):** Shared libraries in `behavior_libraries/` - middle priority
**Tier 3 (Core):** Universal behaviors in `behaviors/core/` - lowest priority

**How it works:** All tiers are symlinked into your game's `behaviors/` directory. The system discovers all Python files and loads them with priority based on directory depth.

### Critical Rules

1. **ALL handlers use invoke_behavior()** - No direct function calls, ever
2. **Behaviors are modules** - Each behavior is a Python file with optional vocabulary, handlers, and event functions
3. **Entities reference behaviors by module path** - `"behaviors": ["behaviors.regions.cave"]` in game_state.json
4. **Handler precedence** - Game > Infrastructure > Core (higher tiers checked first)

### Module Naming

```python
# Symlinked file: behaviors/actor_lib/combat.py
# Module name: "behaviors.actor_lib.combat"
# Entity reference: ["behaviors.actor_lib.combat"] in behaviors list
```

---

## When You're Stuck - Decision Tree

### Parse Failure ("I don't understand that")

1. **Multi-word name?** → Add adjectives for all words before final noun
2. **Custom verb?** → Check vocabulary in behavior module
3. **Still failing?** → See [debugging_guide.md#vocabulary](debugging_guide.md#vocabulary)

### Handler Not Found / No Response

1. **Verb in vocabulary?** → Check behavior vocabulary dict
2. **Handler registered?** → Check module has `handle_<verb>` function
3. **Entity has behavior?** → Check entity's `behaviors` list in game_state.json
4. **Still failing?** → See [debugging_guide.md#handler-dispatch](debugging_guide.md#handler-dispatch)

### Test Failures (Context-Dependent)

1. **Passes alone, fails in suite?** → Check for sys.path manipulation, module cache pollution
2. **Wrong state access?** → Search for `accessor.state` (should be `.game_state`)
3. **Wrong item access?** → Search for `state.items.get()` (should be `.get_item()`)
4. **Still failing?** → See [test_style_guide.md](test_style_guide.md)

### Walkthrough Failures

1. **Parse error?** → Missing adjective vocabulary (most common!)
2. **"You don't see X here"?** → Wrong location or missing entity
3. **"Can't go X"?** → Missing exit definition
4. **Still failing?** → See [authoring_guide.md#walkthrough-testing](authoring_guide.md#walkthrough-testing)

### Type Errors / API Confusion

1. **What's the signature?** → See [quick_reference.md#common-utilities](quick_reference.md#common-utilities)
2. **What fields exist?** → See [user_docs/architectural_conventions.md](../user_docs/architectural_conventions.md)
3. **Still confused?** → See [authoring_guide.md](authoring_guide.md)

---

## Essential Imports Reference

```python
# Core types
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult, StateAccessor
from src.types import ActorId, LocationId, ItemId
from src.word_entry import WordEntry

# Handler utilities
from utilities.handler_utils import (
    validate_actor_and_location,
    find_action_target,
    transfer_item_to_actor,
    get_object_word
)

# Entity utilities
from utilities.utils import (
    find_accessible_item,
    find_actor_by_name,
    name_matches,
    _extract_word
)

# Serialization
from utilities.entity_serializer import serialize_for_handler_result

# Infrastructure
from src.infrastructure_utils import (
    get_current_state,
    transition_state,
    modify_trust,
    get_bool_flag,
    set_bool_flag
)
```

---

## Workflow Checklist

### Before Implementation
- [ ] Identify multi-word entity names requiring adjective vocabulary
- [ ] Create walkthrough file defining expected behavior

### During Implementation
- [ ] Use `accessor.game_state` (not `.state`)
- [ ] Use `state.get_item()` (not `.items.get()`)
- [ ] Use `state.get_actor()` for fail-fast (not `.actors.get()` unless None is valid)
- [ ] Extract WordEntry with helpers
- [ ] Include serialized data in HandlerResult
- [ ] Use invoke_behavior() for all behavior calls

### Before Completion
- [ ] Run walkthrough: `python tools/walkthrough.py examples/big_game --file walkthroughs/feature.txt`
- [ ] Fix ALL failures until 100% success
- [ ] Paste walkthrough results in issue comment
- [ ] ONLY THEN close issue

---

## Red Flags - Stop and Discuss

- Event handler names don't match event names in vocabulary
- Behavior module paths don't match actual load paths
- Claiming "mostly working" without 100% walkthrough success
- Adding try/except for authoring/coding errors
- Adding backward compatibility code
- Using loose types or `Any` without justification
- Calling behavior handlers directly instead of using dispatch

---

## Deep Dive References

- **[quick_reference.md](quick_reference.md)** - Condensed API reference, common utilities
- **[authoring_guide.md](authoring_guide.md)** - Handler patterns, vocabulary, walkthroughs
- **[debugging_guide.md](debugging_guide.md)** - Parser, vocabulary, error diagnosis
- **[test_style_guide.md](test_style_guide.md)** - Test structure, patterns, anti-patterns
- **[user_docs/architectural_conventions.md](../user_docs/architectural_conventions.md)** - Type system, core architecture
