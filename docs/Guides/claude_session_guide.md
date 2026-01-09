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

### 11. Exit Access - Locations Have NO .exits Dict ❌

```python
# WRONG - location.exits doesn't exist anymore
exits = location.exits  # AttributeError!

# RIGHT - exits are entities in the index
exits_here = accessor.get_entities_at(location.id, entity_type="exit")
for exit_entity in exits_here:
    print(f"Can go {exit_entity.direction}: {exit_entity.name}")
```

**Background:** Exits were migrated from embedded dicts to first-class entities (see [exit_migration_implementation.md](../../docs/Archive/exit_migration_implementation.md)).

### 12. Reaction Infrastructure - Must Be in entity.behaviors ❌

```python
# WRONG - infrastructure in extra.behaviors (O(n) scaling!)
{
  "extra": {
    "behaviors": [
      "behaviors.shared.infrastructure.dialog_reactions"  # ❌ Wrong!
    ]
  }
}

# RIGHT - infrastructure in entity.behaviors (O(1) dispatch)
{
  "actors": {
    "herbalist_maren": {
      "behaviors": [
        "behaviors.shared.infrastructure.dialog_reactions",  # ✓ Correct!
        "behaviors.regions.civilized_remnants.services"
      ],
      "properties": {
        "dialog_reactions": {
          "handler": "examples.big_game.behaviors.regions.civilized_remnants.services:on_service_request"
        }
      }
    }
  }
}
```

**Why?**
- `entity.behaviors`: O(1) - only target entity's behaviors invoked
- `extra.behaviors`: O(n) - invoked for EVERY entity on EVERY event
- Dialog/combat/item_use are entity-specific → MUST use entity.behaviors

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

### Reaction System Architecture (NEW)

**Three-Layer Architecture: Commands → Hooks → Reactions**

```
Layer 1: COMMANDS (behavior_libraries/command_lib/)
  - Define verbs (ask, talk, attack, use)
  - Parse user input
  - Fire hooks on target entities
  - NO business logic, ONLY dispatch

Layer 2: HOOKS (engine infrastructure)
  - Broadcast events to entity.behaviors
  - O(1) dispatch - only target entity invoked
  - invoke_behavior(entity, "on_dialog", context)

Layer 3: REACTIONS (game/behaviors/shared/infrastructure/)
  - Subscribe to hooks via vocabulary.events
  - Check entity.properties for config
  - Call handlers or unified interpreter
```

**Example Flow:** `ask maren about trade`
1. Command handler (`command_lib/dialog.py`) fires `entity_dialog` hook on maren
2. Hook system invokes `on_dialog` in maren's behaviors list
3. Reaction infrastructure (`dialog_reactions.py`) checks maren's `dialog_reactions` property
4. Calls handler or interpreter → returns response

See [reaction_system_complete_architecture.md](../../docs/big_game_work/reaction_system_complete_architecture.md) for full spec.

### entity.behaviors vs extra.behaviors

**entity.behaviors** (e.g., `maren.behaviors`):
- Modules that handle events for THIS specific entity
- Invoked when `invoke_behavior(entity, event)` called with `entity != None`
- Entity-specific events: dialog, combat, take, item_use, etc.
- **O(1) complexity** - only target entity's behaviors invoked

**extra.behaviors** (`game_state.extra.behaviors`):
- Modules that handle GLOBAL events (`entity=None`)
- Invoked when `invoke_behavior(None, event)` called
- Global events: turn phases, scheduled events, gossip propagation
- **O(n) complexity** - invoked once per turn, not per entity

**Rule:** Entity-specific events MUST use entity.behaviors, NOT extra.behaviors.

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

## Workflows (A, B, C)

All work must follow one of three documented workflows. See ~/.claude/CLAUDE.md for full details.

**Workflow A** - Small/moderate changes (single feature, bug fix):
1. Create issue describing problem
2. Add comment with design
3. Implement using TDD
4. Comment describing work done
5. Close issue

**Workflow B** - Large changes with phases (architecture changes, major features):
1. Create parent issue
2. Design with phasing
3. Create sub-issue per phase
4. Implement each phase with TDD
5. Close phase sub-issues as completed
6. Close parent when all phases done

**Workflow C** - Systematic testing of multiple similar entities (NEW):
1. Create parent issue with testing plan
2. For EACH entity (one at a time):
   - Create sub-issue
   - Fix entity following guide
   - Create walkthrough, run until 100% success
   - Commit with sub-issue reference
   - Close sub-issue
   - Update current_focus.txt
3. Close parent when all entities complete

**When to use:**
- Workflow A: Bug fixes, small features, single-entity changes
- Workflow B: Architecture changes, multi-phase projects, design-heavy work
- Workflow C: Systematic testing/fixing of multiple NPCs, items, or locations

**GitHub Sub-Issues:**
For Workflows B & C, link sub-issues to parent:
```bash
# Get internal ID (not issue number!)
gh api /repos/jedharris/text-game/issues/ISSUE_NUM --jq .id

# Link sub-issue to parent
GH_TOKEN=$(gh auth token)
curl -X POST \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/jedharris/text-game/issues/PARENT_NUM/sub_issues \
  -d '{"sub_issue_id": CHILD_INTERNAL_ID}'
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
- [ ] Put reaction infrastructure in entity.behaviors (NOT extra.behaviors)
- [ ] Access exits via `get_entities_at(location_id, entity_type="exit")` (NOT `location.exits`)

### Before Completion
- [ ] Run walkthrough: `python tools/walkthrough.py examples/big_game --file walkthroughs/feature.txt`
- [ ] Fix ALL failures until 100% success
- [ ] Paste walkthrough results in issue comment
- [ ] ONLY THEN close issue

## Walkthrough Tool Usage

The walkthrough tool is critical for testing. It supports:

**Basic usage:**
```bash
# Run commands from file
python tools/walkthrough.py examples/big_game --file walkthroughs/test.txt

# Stop on first failure
python tools/walkthrough.py examples/big_game --file test.txt --stop-on-error

# Show detailed state after each command
python tools/walkthrough.py examples/big_game --file test.txt --show-vitals
```

**Walkthrough file syntax:**
```
# Comments start with #
look
take sword

# Expected failures are OK (guardians block exit)
go south  # EXPECT_FAIL

# State manipulation for testing
@set player.properties.gold = 500
@set player.properties.trust_state.current = 3

# Assertions to verify state
@assert player.properties.gold >= 500
@assert player.location == "loc_forest"

# Verify output contains text
ask maren about trade
@expect "shows you her wares"
```

**Annotations:**
- `# EXPECT_FAIL` or `# EXPECTED_FAILURE` - marks command as expected to fail
- `@set path = value` - modify game state (for testing scenarios)
- `@assert path operator value` - verify game state (operators: `==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`)
- `@expect "text"` - verify last command output contains text

**Exit codes:**
- `0` - all commands behaved as expected (successes succeeded, expected failures failed)
- `1` - unexpected failures or assertion failures occurred

---

## Red Flags - Stop and Discuss

- Event handler names don't match event names in vocabulary
- Behavior module paths don't match actual load paths
- Claiming "mostly working" without 100% walkthrough success
- Adding try/except for authoring/coding errors
- Adding backward compatibility code
- Using loose types or `Any` without justification
- Calling behavior handlers directly instead of using dispatch
- Infrastructure modules in `extra.behaviors` instead of `entity.behaviors` (O(n) scaling!)
- Accessing `location.exits` dict (doesn't exist - exits are entities now)
- Invoking hook names instead of event names (`entity_dialog` vs `on_dialog`)

---

## Deep Dive References

- **[quick_reference.md](quick_reference.md)** - Condensed API reference, common utilities
- **[authoring_guide.md](authoring_guide.md)** - Handler patterns, vocabulary, walkthroughs
- **[debugging_guide.md](debugging_guide.md)** - Parser, vocabulary, error diagnosis
- **[test_style_guide.md](test_style_guide.md)** - Test structure, patterns, anti-patterns
- **[user_docs/architectural_conventions.md](../user_docs/architectural_conventions.md)** - Type system, core architecture
