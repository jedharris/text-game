# String Typing Plan

## Overview

This document analyzes the codebase to identify all places where bare strings are passed that should be typed, and proposes a plan to add proper types. The goal is to eliminate passing untyped strings as far as possible, improving type safety and catching errors at development time rather than runtime.

## Current State Analysis

### Existing Types

The codebase already has several typed structures:

| Type | Location | Purpose |
|------|----------|---------|
| `WordEntry` | `src/word_entry.py` | Typed vocabulary entries with word, synonyms, word_type |
| `WordType` | `src/word_entry.py` | Enum for grammatical word types |
| `ActionDict` | `src/action_types.py` | TypedDict for action dictionaries |
| `EventResult` | `src/state_accessor.py` | Result dataclass for behaviors |
| `UpdateResult` | `src/state_accessor.py` | Result dataclass for updates |
| `HandlerResult` | `src/state_accessor.py` | Result dataclass for handlers |

### Key Problem Areas

The codebase has several categories of untyped strings that cause problems:

---

## Category 1: Entity IDs (Highest Priority)

Entity IDs are passed as bare `str` throughout the codebase. This causes:
- No type checking to catch ID type mismatches
- Easy to pass wrong type of ID (location_id where actor_id expected)
- No IDE autocomplete or type hints

### Proposed Types

```python
# In src/types.py (new file)
from typing import NewType

LocationId = NewType('LocationId', str)
ActorId = NewType('ActorId', str)
ItemId = NewType('ItemId', str)
LockId = NewType('LockId', str)
PartId = NewType('PartId', str)
ExitId = NewType('ExitId', str)

# Union type for any entity ID
EntityId = LocationId | ActorId | ItemId | LockId | PartId | ExitId
```

### Affected Locations

#### StateAccessor (src/state_accessor.py)
| Method | Current | Proposed |
|--------|---------|----------|
| `get_location(location_id: str)` | str | LocationId |
| `get_actor(actor_id: str)` | str | ActorId |
| `get_item(item_id: str)` | str | ItemId |
| `get_lock(lock_id: str)` | str | LockId |
| `get_part(part_id: str)` | str | PartId |
| `get_entity(entity_id: str)` | str | EntityId |
| `get_parts_of(entity_id: str)` | str | EntityId |
| `get_items_at_part(part_id: str)` | str | PartId |
| `get_visible_exits(location_id: str, actor_id: str)` | str, str | LocationId, ActorId |
| `get_current_location(actor_id: str)` | str | ActorId |
| `get_items_in_location(location_id: str)` | str | LocationId |
| `get_actors_in_location(location_id: str)` | str | LocationId |
| `get_door_for_exit(location_id: str, direction: str)` | str, str | LocationId, Direction |
| `get_focused_entity(actor_id: str)` | str | ActorId |

#### Entity Dataclasses (src/state_manager.py)
| Entity | Field | Current | Proposed |
|--------|-------|---------|----------|
| `Location` | `id` | str | LocationId |
| `Location` | `items` | List[str] | List[ItemId] |
| `Item` | `id` | str | ItemId |
| `Item` | `location` | str | LocationId \| ItemId \| ActorId |
| `Actor` | `id` | str | ActorId |
| `Actor` | `location` | str | LocationId |
| `Actor` | `inventory` | List[str] | List[ItemId] |
| `Lock` | `id` | str | LockId |
| `Lock` | `opens_with` | List[str] | List[ItemId] |
| `Part` | `id` | str | PartId |
| `Part` | `part_of` | str | EntityId |
| `ExitDescriptor` | `to` | Optional[str] | Optional[LocationId] |
| `ExitDescriptor` | `door_id` | Optional[str] | Optional[ItemId] |
| `Metadata` | `start_location` | str | LocationId |

#### Utility Functions (utilities/utils.py)
| Function | Parameters to Update |
|----------|---------------------|
| `find_actor_by_name` | actor_id: str → ActorId |
| `find_accessible_item` | actor_id: str → ActorId |
| `find_item_in_inventory` | actor_id: str → ActorId |
| `find_container_by_name` | location_id: str → LocationId |
| `find_container_with_adjective` | location_id: str → LocationId |
| `find_item_in_container` | container_id: str → ItemId |
| `find_door_with_adjective` | location_id: str → LocationId, actor_id: Optional[str] → Optional[ActorId] |
| `find_lock_by_context` | location_id: str → LocationId, actor_id: str → ActorId |
| `find_exit_by_name` | actor_id: str → ActorId |
| `get_visible_items_in_location` | location_id: str → LocationId, actor_id: str → ActorId |
| `get_visible_actors_in_location` | location_id: str → LocationId, actor_id: str → ActorId |
| `get_doors_in_location` | location_id: str → LocationId, actor_id: str → ActorId |
| `gather_location_contents` | location_id: str → LocationId, actor_id: str → ActorId |
| `describe_location` | actor_id: str → ActorId |
| `actor_has_key_for_door` | actor_id: str → ActorId |
| `is_observable` | actor_id: str → ActorId |

#### Handler Utilities (utilities/handler_utils.py)
| Function | Parameters to Update |
|----------|---------------------|
| `validate_actor_and_location` | Returns actor_id: str → ActorId |
| `find_action_target` | Returns actor_id from action |

---

## Category 2 (NOT NEEDED): Direction Strings

**NOTE**: Directions do NOT need a separate type. Per the completed refactoring documented in `Archive/directions_as_nouns.md`, directions are now regular vocabulary words - nouns with multi-valued `word_type: ["noun", "adjective"]`. They are defined in `behaviors/core/exits.py` as regular nouns alongside exit-related vocabulary.

Direction strings in `Location.exits` dict keys and `ExitDescriptor._direction` are just strings that happen to contain direction words from the vocabulary. They don't need special typing because:
1. Directions are extensible vocabulary (games can add "portside", "starboard", etc.)
2. The vocabulary system already validates direction words
3. A fixed enum would violate the extensibility principle

### Cleanup Needed

There is extensive legacy cruft that should be cleaned up. This is tracked in **Issue #165**: "Remove legacy 'directions' vocabulary section handling"

The issue affects ~30 files including:
- Core source files (`behavior_manager.py`, `llm_protocol.py`, `llm_narrator.py`, `vocabulary_generator.py`)
- All behavior module vocabulary dicts (empty `"directions": []` entries)
- Example game behaviors
- Multiple test files

This cleanup is unrelated to typing but should be done to prevent future confusion.

---

## Category 2: ActionDict Enforcement

`ActionDict` is already defined but not consistently enforced. The main issue is:
- `action.get("object")` and `action.get("indirect_object")` should always return `WordEntry` per the type definition
- Code defensively handles both `str` and `WordEntry` using `get_display_name()` and `get_object_word()`

### Current ActionDict Definition (src/action_types.py)

```python
class ActionDict(TypedDict, total=False):
    actor_id: str                          # Should be ActorId
    verb: str                              # Consider VerbString type
    object: Optional[WordEntry]            # ✓ Already typed
    adjective: str                         # Keep as str
    indirect_object: Optional[WordEntry]   # ✓ Already typed
    indirect_adjective: str                # Keep as str
    preposition: str                       # Keep as str
    raw_after_preposition: str             # Keep as str
```

### Proposed Changes

```python
class ActionDict(TypedDict, total=False):
    actor_id: ActorId                      # Changed from str
    verb: str
    object: Optional[WordEntry]            # Keep as WordEntry
    adjective: str
    indirect_object: Optional[WordEntry]   # Keep as WordEntry
    indirect_adjective: str
    preposition: str
    raw_after_preposition: str
```

### Code Cleanup Required

The following utility functions exist to handle the str/WordEntry ambiguity and can be simplified once enforcement is complete:

| Function | Location | Action |
|----------|----------|--------|
| `ensure_word_entry()` | utilities/utils.py | Keep for tests only, add deprecation warning for production |
| `get_display_name()` | utilities/handler_utils.py | Simplify to only accept WordEntry |
| `get_object_word()` | utilities/handler_utils.py | Simplify to only accept WordEntry |
| `_convert_action_strings_to_wordentry()` | src/llm_protocol.py | Remove after all paths provide WordEntry |

---

## Category 3: Behavior Module Names

Behavior module names are passed as strings in entity `behaviors` lists. Consider typing these.

### Current Usage

```python
# In entity definitions
behaviors: List[str] = ["behaviors.core.manipulation", "behaviors.core.locks"]
```

### Proposed Type

```python
# In src/types.py
BehaviorModulePath = NewType('BehaviorModulePath', str)
```

This is lower priority since module paths are validated at load time and errors fail loudly.

---

## Category 4: Event Names and Hook Names

Event names (e.g., "on_take", "on_examine") and hook names (e.g., "visibility_check") are passed as strings.

### Proposed Types

```python
# In src/types.py
EventName = NewType('EventName', str)
HookName = NewType('HookName', str)
```

Affected locations:
- `BehaviorManager.invoke_behavior(event_name: str)` → `EventName`
- `BehaviorManager.get_event_for_hook(hook_name: str)` → `HookName`
- `src/hooks.py` constants

---

## Implementation Plan

### Phase 1: Create Type Definitions (Foundation)

**Estimated scope**: 1 new file, ~40 lines

1. Create `src/types.py` with all NewType definitions
2. Export types from `src/__init__.py`

### Phase 2: Entity ID Types (High Impact)

**Estimated scope**: ~20 files, ~200 changes

1. Update `src/state_manager.py` entity dataclasses
2. Update `src/state_accessor.py` method signatures
3. Update `utilities/utils.py` function signatures
4. Update `utilities/handler_utils.py`
5. Update `utilities/positioning.py`
6. Update all behavior handlers in `behaviors/core/`
7. Update behavior libraries
8. Update tests

### Phase 3: ActionDict Enforcement (Medium Impact)

**Estimated scope**: ~15 files, ~100 changes

1. Update `ActionDict` to use `ActorId`
2. Remove string fallbacks in `get_display_name()` and `get_object_word()`
3. Remove `_convert_action_strings_to_wordentry()` from llm_protocol.py
4. Add deprecation warnings to `ensure_word_entry()`
5. Update tests to always use WordEntry

### Phase 4: Secondary Types (Lower Priority)

**Estimated scope**: ~10 files, ~30 changes

1. Add `BehaviorModulePath` type
2. Add `EventName` and `HookName` types
3. Update behavior_manager.py signatures
4. Update tests

---

## Migration Strategy

For each phase:

1. **Add types without breaking changes**: Use `Union[NewType, str]` temporarily
2. **Update callers incrementally**: Convert call sites to use typed values
3. **Enable strict typing**: Remove `str` from unions, add mypy strict checks
4. **Clean up**: Remove backward compatibility code

### TDD Approach

For each phase:
1. Write tests that verify the new types work correctly
2. Run mypy to identify all locations needing updates
3. Update code to pass mypy checks
4. Ensure all existing tests pass
5. Add new tests for type validation edge cases

---

## Files to Create/Modify Summary

### New Files
- `src/types.py` - Type definitions

### Core Files (Phase 2)
- `src/state_manager.py` - Entity dataclasses
- `src/state_accessor.py` - Accessor methods
- `src/action_types.py` - ActionDict update

### Utility Files (Phase 2-3)
- `utilities/utils.py` - Finder functions
- `utilities/handler_utils.py` - Handler helpers
- `utilities/positioning.py` - Positioning utilities
- `utilities/location_serializer.py` - Serialization
- `utilities/entity_serializer.py` - Entity serialization

### Behavior Files (Phase 2-3)
- `behaviors/core/manipulation.py`
- `behaviors/core/perception.py`
- `behaviors/core/exits.py`
- `behaviors/core/spatial.py`
- `behaviors/core/locks.py`
- `behaviors/core/containers.py`
- `behaviors/core/actors.py`
- `behaviors/core/combat.py`
- `behaviors/core/consumables.py`
- `behaviors/core/light_sources.py`
- `behaviors/core/interaction.py`
- `behaviors/core/meta.py`

### Behavior Library Files (Phase 2)
- `behavior_libraries/actor_lib/*.py`
- `behavior_libraries/companion_lib/*.py`
- `behavior_libraries/npc_movement_lib/*.py`
- `behavior_libraries/dialog_lib/*.py`
- `behavior_libraries/offering_lib/*.py`
- `behavior_libraries/darkness_lib/*.py`
- `behavior_libraries/puzzle_lib/*.py`
- `behavior_libraries/crafting_lib/*.py`
- `behavior_libraries/timing_lib/*.py`

### Test Files (All Phases)
- All test files will need updates to use typed values

---

## Success Criteria

1. **mypy passes with strict mode** on all modified files
2. **All existing tests pass** without modification to test logic
3. **No runtime type coercion** - types flow cleanly through the system
4. **IDE support works** - autocomplete and type hints functional
5. **Documentation updated** - docstrings reflect new types

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large scope causes integration issues | High | Phase implementation, comprehensive testing |
| NewType doesn't catch all errors | Medium | Add runtime validation at boundaries |
| Performance impact from type checking | Low | NewType has zero runtime cost |
| Test maintenance burden | Medium | Update tests incrementally per phase |

---

## Recommendation

Start with **Phase 1 and Phase 2** (Entity ID types) as they provide the highest value:
- Most common source of bugs (wrong ID type passed)
- Largest codebase impact
- Foundation for other phases

Phase 3 (ActionDict enforcement) can follow. Phase 4 (secondary types) is optional polish.
