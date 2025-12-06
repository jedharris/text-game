# Design: Unified LLM Context Handling

## Problem Statement

The `--show-traits` flag displays `llm_context.traits` before each LLM narration call. Initial investigation revealed an architectural concern: `llm_context` is added in multiple scattered locations throughout the codebase. This creates:

1. **Inconsistency**: Some handlers include llm_context, others don't
2. **Maintenance burden**: New handlers must remember to add this pattern
3. **Duplicated code**: Multiple entity-to-dict conversion paths

This document proposes a unified approach to maximize consistency and merge code paths.

## Current Architecture Analysis

### Two Distinct Use Cases

The codebase has two separate paths that produce JSON for the LLM:

1. **Command Results** (via behavior handlers)
   - Flow: `handle_*()` → `HandlerResult(data={...})` → `LLMNarrator`
   - Handlers manually add `llm_context` to `HandlerResult.data`
   - Examples: `handle_examine`, `handle_look`, `handle_go`

2. **Query Responses** (via llm_protocol.py)
   - Flow: `_query_*()` → `_entity_to_dict()` → JSON response
   - Uses `_add_llm_context()` helper for trait randomization
   - Examples: `_query_location`, `_query_inventory`, `_query_entity`

### Current Code Paths for llm_context

| Location | Method | Trait Randomization | Used By |
|----------|--------|---------------------|---------|
| `llm_protocol._add_llm_context()` | Centralized helper | Yes | Query handlers |
| `llm_protocol._entity_to_dict()` | Calls `_add_llm_context` | Yes | Queries |
| `llm_protocol._door_to_dict()` | Calls `_add_llm_context` | Yes | Queries |
| `llm_protocol._location_to_dict()` | Calls `_add_llm_context` | Yes | Queries |
| `llm_protocol._actor_to_dict()` | Calls `_add_llm_context` | Yes | Queries |
| `perception.handle_examine()` | Direct assignment | **No** | Commands |
| `perception.handle_look()` | Via `gather_location_llm_context` | **No** | Commands |
| `movement.handle_go()` | Via `gather_location_llm_context` | **No** | Commands |
| `utils.gather_location_llm_context()` | Direct assignment | **No** | Commands |

### Key Observations

1. **Trait randomization is inconsistent**: Query responses randomize traits (for narration variety), but command results don't.

2. **Entity-to-dict conversions are duplicated**:
   - `llm_protocol._entity_to_dict()` for queries
   - Inline dict building in handlers for commands

3. **Many handlers don't include llm_context at all**:
   - `handle_take`, `handle_drop`, `handle_open`, `handle_close`
   - `handle_unlock`, `handle_lock`, `handle_use`, `handle_put`
   - `handle_give`, `handle_read`, `handle_climb`, `handle_pull`, `handle_push`

4. **Location llm_context uses wrong accessor**: `gather_location_llm_context()` checks `item.properties.get('llm_context')` but Item has an `llm_context` property accessor.

## Proposed Solution: Unified Entity Serialization

### Goals

1. **Single code path** for entity-to-dict conversion
2. **Consistent trait randomization** for both commands and queries
3. **Automatic llm_context inclusion** without handler boilerplate
4. **Centralized logic** in utilities, not scattered in handlers

### Design: Entity Serializer Module

Create a new module `utilities/entity_serializer.py` with unified serialization:

```python
"""Entity serialization for LLM communication.

Provides unified entity-to-dict conversion with automatic llm_context
handling and trait randomization.
"""
import random
from typing import Any, Dict, Optional

def entity_to_dict(entity, include_llm_context: bool = True) -> Dict[str, Any]:
    """Convert any entity to a dict suitable for LLM communication.

    Handles: Item, Location, Actor, ExitDescriptor, Lock

    Args:
        entity: Entity object to serialize
        include_llm_context: If True, include llm_context with randomized traits

    Returns:
        Dict representation of entity
    """
    result = _serialize_core_fields(entity)

    if include_llm_context:
        _add_llm_context(result, entity)

    return result

def _serialize_core_fields(entity) -> Dict[str, Any]:
    """Serialize core fields based on entity type."""
    result = {"id": entity.id, "name": entity.name}

    if hasattr(entity, 'description') and entity.description:
        result["description"] = entity.description

    # Item-specific fields
    if hasattr(entity, 'is_door') and entity.is_door:
        result["type"] = "door"
        result["open"] = entity.door_open
        result["locked"] = entity.door_locked
    elif hasattr(entity, 'container') and entity.container:
        result["type"] = "container"
    elif hasattr(entity, 'portable'):
        result["type"] = "item"

    # Actor-specific fields
    if hasattr(entity, 'inventory'):
        result["type"] = "actor"

    # Light source state
    if hasattr(entity, 'states'):
        if entity.states.get('lit'):
            result["lit"] = entity.states['lit']

    if hasattr(entity, 'provides_light') and entity.provides_light:
        result["provides_light"] = True

    return result

def _add_llm_context(result: Dict, entity) -> None:
    """Add llm_context with randomized traits.

    Randomizes trait order to encourage varied LLM narration.
    """
    llm_context = None

    # Try direct property first (Item, Location, ExitDescriptor)
    if hasattr(entity, 'llm_context'):
        llm_context = entity.llm_context
    # Fall back to properties dict
    elif hasattr(entity, 'properties') and isinstance(entity.properties, dict):
        llm_context = entity.properties.get('llm_context')

    if not llm_context:
        return

    # Copy to avoid mutation
    context_copy = dict(llm_context)

    # Randomize traits
    if 'traits' in context_copy and isinstance(context_copy['traits'], list):
        traits_copy = list(context_copy['traits'])
        random.shuffle(traits_copy)
        context_copy['traits'] = traits_copy

    result['llm_context'] = context_copy

def serialize_for_handler_result(entity) -> Dict[str, Any]:
    """Serialize entity for inclusion in HandlerResult.data.

    Convenience function for behavior handlers.
    """
    return entity_to_dict(entity, include_llm_context=True)
```

### Migration Plan

#### Phase 1: Create Unified Serializer

1. Create `utilities/entity_serializer.py` with functions above
2. Add comprehensive tests for all entity types
3. Verify trait randomization works correctly

#### Phase 2: Migrate Query Handlers (llm_protocol.py)

Replace `_*_to_dict` methods with calls to unified serializer:

```python
# Before
def _entity_to_dict(self, item) -> Dict:
    result = {"id": item.id, "name": item.name, ...}
    self._add_llm_context(result, item.properties)
    return result

# After
from utilities.entity_serializer import entity_to_dict

def _entity_to_dict(self, item) -> Dict:
    return entity_to_dict(item)
```

Files to modify:
- `src/llm_protocol.py`: Remove `_entity_to_dict`, `_door_to_dict`, `_location_to_dict`, `_actor_to_dict`, `_add_llm_context`

#### Phase 3: Migrate Behavior Handlers

Update handlers to use `serialize_for_handler_result()`:

```python
# Before (perception.py handle_examine)
data = {}
if item.llm_context:
    data["llm_context"] = item.llm_context
return HandlerResult(success=True, message=msg, data=data if data else None)

# After
from utilities.entity_serializer import serialize_for_handler_result

data = serialize_for_handler_result(item)
return HandlerResult(success=True, message=msg, data=data)
```

Handlers to update:
| Handler | File | Entity Type | Priority |
|---------|------|-------------|----------|
| `handle_examine` (item) | perception.py | Item | High |
| `handle_examine` (door) | perception.py | Item (door) | High |
| `handle_examine` (exit) | perception.py | ExitDescriptor | High |
| `handle_examine` (lock) | perception.py | Lock | High |
| `handle_take` | manipulation.py | Item | Medium |
| `handle_drop` | manipulation.py | Item | Medium |
| `handle_open` | interaction.py | Item | Medium |
| `handle_close` | interaction.py | Item | Medium |
| `handle_unlock` | locks.py | Item/Lock | Medium |
| `handle_lock` | locks.py | Item/Lock | Medium |
| `handle_use` | interaction.py | Item | Low |
| `handle_put` | manipulation.py | Item | Low |
| `handle_give` | manipulation.py | Item | Low |

#### Phase 4: Fix gather_location_llm_context

Update `utilities/utils.py`:

```python
# Before
for item in all_items:
    if hasattr(item, 'properties') and item.properties.get('llm_context'):
        items_with_context.append({
            "name": item.name,
            "llm_context": item.properties['llm_context']
        })

# After
from utilities.entity_serializer import entity_to_dict

for item in all_items:
    serialized = entity_to_dict(item)
    if "llm_context" in serialized:
        items_with_context.append({
            "name": serialized["name"],
            "llm_context": serialized["llm_context"]
        })
```

### Benefits of This Approach

1. **Single serialization path**: All entity-to-dict goes through `entity_to_dict()`
2. **Consistent trait randomization**: Every path gets randomized traits
3. **Less handler boilerplate**: Handlers just call `serialize_for_handler_result(entity)`
4. **Centralized maintenance**: Changes to serialization format happen in one place
5. **Type-aware serialization**: Function detects entity type and serializes appropriately
6. **Backward compatible**: Existing code continues to work during migration

### Additional Improvement: Central Intervention Point

For stronger enforcement, add post-processing in `LLMProtocolHandler.handle_command()`:

```python
def handle_command(self, message: Dict) -> Dict:
    # ... existing code ...

    if result.success:
        response = {
            "type": "result",
            "success": True,
            "action": verb,
            "message": result.message
        }
        if result.data:
            # Ensure llm_context has randomized traits
            response["data"] = self._ensure_randomized_traits(result.data)
        return response

def _ensure_randomized_traits(self, data: Dict) -> Dict:
    """Randomize traits in any llm_context found in data."""
    if "llm_context" in data and "traits" in data["llm_context"]:
        data = dict(data)  # Copy
        data["llm_context"] = dict(data["llm_context"])
        traits = list(data["llm_context"]["traits"])
        random.shuffle(traits)
        data["llm_context"]["traits"] = traits
    return data
```

This provides a safety net: even if a handler forgets to use the serializer, traits will still be randomized.

## Alternative: Handler Protocol Validation

For future enforcement, add validation that handlers return proper data:

```python
# In BehaviorManager or LLMProtocolHandler
def _validate_handler_result(self, result: HandlerResult, verb: str) -> None:
    """Warn if handler result is missing expected llm_context."""
    if result.success and result.data:
        if "llm_context" not in result.data:
            logger.warning(f"Handler for '{verb}' returned data without llm_context")
```

This helps catch handlers that forget to include llm_context during development.

## Testing Strategy

### Unit Tests

1. `test_entity_serializer.py`:
   - Test serialization of each entity type
   - Test trait randomization
   - Test entities without llm_context
   - Test nested llm_context in properties

2. Update existing tests:
   - Verify llm_context presence in handler results
   - Verify trait randomization in query responses

### Integration Tests

1. Run with `--show-traits` flag
2. Verify traits print for all command types
3. Verify trait order varies between invocations

## Summary

The current architecture has llm_context handling scattered across:
- 4 `_*_to_dict` methods in llm_protocol.py
- 6+ handler functions in behavior modules
- 1 utility function (gather_location_llm_context)

The proposed solution consolidates to:
- 1 unified serializer module
- Consistent trait randomization everywhere
- Optional central intervention point for safety

This reduces ~200 lines of duplicated/scattered code to ~50 lines of centralized logic.

## Implementation Order

1. **Phase 1**: Create entity_serializer.py with tests
2. **Phase 2**: Migrate llm_protocol.py (biggest code reduction)
3. **Phase 3**: Migrate behavior handlers (consistency improvement)
4. **Phase 4**: Fix gather_location_llm_context (bug fix)
5. **Optional**: Add central intervention point (safety net)
6. **Optional**: Add handler validation (development aid)

---

## Implementation Log

### Phase 1: Create entity_serializer.py with tests - COMPLETED

**Results:**
- Created `utilities/entity_serializer.py` with unified serialization logic
- Created `tests/test_entity_serializer.py` with 19 test cases covering:
  - Basic serialization for all entity types (Item, Location, Actor, ExitDescriptor, Lock)
  - llm_context inclusion/exclusion
  - Trait randomization verification
  - Original data non-mutation
  - Specialized item types (door, container, light source)

**Issue encountered:** Lock test initially failed because Lock stores `opens_with` in properties dict, not as a constructor parameter. Fixed by using `properties={"opens_with": ["item_key"]}`.

**All 19 tests pass. Full suite: 1039 tests pass.**

### Phase 2: Migrate llm_protocol.py - COMPLETED

**Results:**
- Modified `_entity_to_dict()` to use `entity_to_dict()` from serializer
  - Retained query-specific container location info (on_surface/in_container)
- Modified `_door_to_dict()` to use `entity_to_dict()` from serializer
- Modified `_location_to_dict()` to use `entity_to_dict()` from serializer
- Modified `_actor_to_dict()` to use `entity_to_dict()` from serializer
- Kept `_add_llm_context()` as deprecated wrapper for now (exit descriptor handling still uses it)

**Code reduction:** The `_*_to_dict` methods now delegate to the unified serializer, with only query-specific post-processing retained.

**All 1039 tests pass.**

### Phase 3: Migrate behavior handlers - COMPLETED

**Results:**
- Migrated `handle_examine` in `behaviors/core/perception.py` to use `serialize_for_handler_result()`:
  - Item examination: Uses serializer with trait randomization
  - Door examination: Uses serializer with trait randomization
  - Exit examination: Uses serializer, adds exit-specific fields (direction, type, door_id)
  - Lock examination: Uses serializer with trait randomization

**Scope clarification:** The design document listed many handlers as not returning llm_context. The Phase 3 target was handlers that *manually built* llm_context dicts. Only `handle_examine` did this. Handlers like `handle_look` and `handle_go` use `gather_location_llm_context()`, which is Phase 4's target.

**All 1039 tests pass.**

### Phase 4: Fix gather_location_llm_context - COMPLETED

**Results:**
- Updated `gather_location_llm_context()` in `utilities/utils.py` to use `entity_to_dict()` from the serializer
- Fixed bug where function was using `item.properties.get('llm_context')` instead of the proper `llm_context` property accessor
- Added trait randomization for all entities (location, items, actors)
- Now consistently uses the same code path as query handlers and examine handler

**All 1039 tests pass.**

---

## Implementation Summary

All four phases completed successfully:
1. **Phase 1**: Created `utilities/entity_serializer.py` with 19 tests
2. **Phase 2**: Migrated `llm_protocol.py` to use serializer
3. **Phase 3**: Migrated `handle_examine` to use serializer
4. **Phase 4**: Fixed `gather_location_llm_context` to use serializer

**Result**: All llm_context handling now flows through `entity_to_dict()` from `utilities/entity_serializer.py`, providing:
- Consistent trait randomization everywhere
- Single code path for entity serialization
- Proper use of entity property accessors

---

### Phase 5: Extend llm_context to All Remaining Handlers - COMPLETED

**Decision**: Extended llm_context unconditionally to all handlers rather than selectively.

**Rationale**: Sending richer context to the LLM narrator enables more varied and contextual narration. Over-narration concerns can be addressed by tuning the narrator prompt rather than filtering context at the handler level.

**Implementation**:
- Created `tests/test_handler_llm_context.py` with 14 tests for all handlers
- Updated manipulation handlers: `handle_take`, `handle_drop`, `handle_give`, `handle_put`
- Updated interaction handlers: `handle_open`, `handle_close`, `handle_use`, `handle_read`, `handle_climb`, `handle_pull`, `handle_push`
- Updated lock handlers: `handle_unlock`, `handle_lock`
- Updated perception handler: `handle_inventory`

All handlers now use `serialize_for_handler_result(item)` from `utilities/entity_serializer.py` to include llm_context with randomized traits.

**Tests**: 14 new tests in `tests/test_handler_llm_context.py`, all passing. Full suite: 1053 tests pass.

---

## Appendix: Updated Handler llm_context Status

| Handler | Returns llm_context? | Has Trait Randomization? |
|---------|---------------------|-------------------------|
| handle_look | Yes (via utility) | **Yes** |
| handle_examine (item) | Yes | **Yes** |
| handle_examine (door) | Yes | **Yes** |
| handle_examine (exit) | Yes | **Yes** |
| handle_examine (lock) | Yes | **Yes** |
| handle_go | Yes (via utility) | **Yes** |
| handle_take | **Yes** | **Yes** |
| handle_drop | **Yes** | **Yes** |
| handle_open | **Yes** | **Yes** |
| handle_close | **Yes** | **Yes** |
| handle_unlock | **Yes** | **Yes** |
| handle_lock | **Yes** | **Yes** |
| handle_use | **Yes** | **Yes** |
| handle_put | **Yes** | **Yes** |
| handle_give | **Yes** | **Yes** |
| handle_read | **Yes** | **Yes** |
| handle_climb | **Yes** | **Yes** |
| handle_pull | **Yes** | **Yes** |
| handle_push | **Yes** | **Yes** |
| handle_inventory | **Yes** (items array) | **Yes** |
