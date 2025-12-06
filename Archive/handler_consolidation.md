# Handler Consolidation Design

**Issue:** #42
**Status:** Draft
**Author:** Claude

## Goals

1. Eliminate duplicate code across item-targeting handlers
2. Ensure all handlers consistently extract and use `adjective` for disambiguation
3. Use vocabulary-derived verb in messages (not hardcoded strings)
4. Reduce maintenance burden and bug risk

## Use Cases

1. **Simple item verbs** (push, pull, use): Find item, invoke behaviors, return result
2. **Property-requiring verbs** (read, climb): Same as above but validate a property first
3. **Content-displaying verbs** (read): Same as above but include property content in message

## Non-Goals (Deferred)

- Consolidating `open`/`close` handlers (complex door/container logic)
- Consolidating `take`/`drop`/`give`/`put` handlers (inventory transfer logic)
- Moving property requirements to vocabulary metadata (wait for more use cases)

## Current State

Five handlers in `interaction.py` follow this pattern:

```python
def handle_push(accessor, action):
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")  # Some handlers missing this!

    if not object_name:
        return HandlerResult(success=False, message="What do you want to push?")

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(success=False, message=f"INCONSISTENT STATE: Actor {actor_id} not found")

    item = find_accessible_item(accessor, object_name, actor_id, adjective)
    if not item:
        return HandlerResult(success=False, message=f"You don't see any {object_name} here.")

    result = accessor.update(item, {}, verb="push", actor_id=actor_id)

    base_message = f"You push the {item.name}."
    data = serialize_for_handler_result(item)
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)
    return HandlerResult(success=True, message=base_message, data=data)
```

**Problems:**
- Lines 1-14 are identical across 5 handlers (except message text)
- `handle_use`, `handle_read`, `handle_climb` don't extract `adjective`
- Message text is hardcoded instead of using `action["verb"]`

## Design

### New Utility: `find_action_target()`

Location: `utilities/handler_utils.py`

```python
from typing import Tuple, Optional, Dict, Any
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item


def find_action_target(
    accessor,
    action: Dict[str, Any]
) -> Tuple[Optional[Any], Optional[HandlerResult]]:
    """
    Standard preamble for item-targeting handlers.

    Extracts actor_id, object, adjective from action.
    Validates actor exists.
    Finds accessible item using adjective for disambiguation.

    The verb in action["verb"] is used for error messages and is the
    canonical form from the parser/vocabulary.

    Args:
        accessor: StateAccessor instance
        action: Action dict containing:
            - verb: Canonical verb from parser (required for messages)
            - actor_id: Actor performing action (default: "player")
            - object: Name of target object
            - adjective: Optional adjective for disambiguation

    Returns:
        Tuple of (item, error_result):
        - If item found: (item, None)
        - If error: (None, HandlerResult with error message)
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")
    verb = action.get("verb", "interact with")

    if not object_name:
        return None, HandlerResult(
            success=False,
            message=f"What do you want to {verb}?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return None, HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    item = find_accessible_item(accessor, object_name, actor_id, adjective)
    if not item:
        return None, HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    return item, None
```

### Refactored Handlers

**Simple handlers (push, pull, use):**

```python
from utilities.handler_utils import find_action_target

def handle_push(accessor, action):
    """Handle push command."""
    item, error = find_action_target(accessor, action)
    if error:
        return error

    verb = action.get("verb", "push")
    actor_id = action.get("actor_id", "player")

    result = accessor.update(item, {}, verb=verb, actor_id=actor_id)

    base_message = f"You {verb} the {item.name}."
    data = serialize_for_handler_result(item)

    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)
    return HandlerResult(success=True, message=base_message, data=data)
```

**Property-checking handlers (read, climb):**

```python
def handle_read(accessor, action):
    """Handle read command - requires readable property."""
    item, error = find_action_target(accessor, action)
    if error:
        return error

    # Property validation specific to this verb
    if not item.properties.get("readable", False):
        return HandlerResult(success=False, message=f"You can't read the {item.name}.")

    verb = action.get("verb", "read")
    actor_id = action.get("actor_id", "player")

    result = accessor.update(item, {}, verb=verb, actor_id=actor_id)

    # Special handling: show text content
    text = item.properties.get("text", "")
    if text:
        base_message = f"You read the {item.name}: {text}"
    else:
        base_message = f"You read the {item.name}."

    data = serialize_for_handler_result(item)

    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)
    return HandlerResult(success=True, message=base_message, data=data)
```

## Phasing

### Phase 1: Create `find_action_target()` utility

**Tasks:**
1. Create `utilities/handler_utils.py`
2. Implement `find_action_target()` function
3. Write comprehensive tests in `tests/test_handler_utils.py`

**Tests (write first):**
- `test_find_action_target_returns_item_when_found`
- `test_find_action_target_error_when_no_object`
- `test_find_action_target_error_when_actor_not_found`
- `test_find_action_target_error_when_item_not_found`
- `test_find_action_target_uses_adjective_for_disambiguation`
- `test_find_action_target_uses_verb_in_error_message`

**Validation:** All existing tests pass, new tests pass

### Phase 2: Refactor simple handlers

**Tasks:**
1. Refactor `handle_push` to use `find_action_target()`
2. Refactor `handle_pull` to use `find_action_target()`
3. Refactor `handle_use` to use `find_action_target()` (adds adjective support)

**Tests:**
- Existing tests in `tests/test_interaction_handlers.py` should continue to pass
- Add `test_use_with_adjective_selects_correct_item` (currently missing)

**Validation:** All 1120+ tests pass

### Phase 3: Refactor property-checking handlers

**Tasks:**
1. Refactor `handle_read` to use `find_action_target()` (adds adjective support)
2. Refactor `handle_climb` to use `find_action_target()` (adds adjective support)

**Tests:**
- Existing tests should continue to pass
- Add `test_read_with_adjective_selects_correct_item`
- Add `test_climb_with_adjective_selects_correct_item`

**Validation:** All tests pass

## Code Reduction Summary

| Handler | Before | After | Reduction |
|---------|--------|-------|-----------|
| handle_push | 40 lines | 14 lines | 65% |
| handle_pull | 40 lines | 14 lines | 65% |
| handle_use | 38 lines | 14 lines | 63% |
| handle_read | 48 lines | 22 lines | 54% |
| handle_climb | 42 lines | 18 lines | 57% |
| **Total** | ~208 lines | ~82 lines | **60%** |

Plus `find_action_target()` adds ~35 lines in utility, for net reduction of ~90 lines.

## Deferred Work

### Vocabulary-Driven Property Requirements (Issue #43)

Currently, `handle_read` and `handle_climb` check item properties in handler code:
- `handle_read` checks `item.properties.get("readable", False)`
- `handle_climb` checks `item.properties.get("climbable", False)`

This pattern could be moved to vocabulary metadata, making handlers fully declarative.

**Decision:** Deferred to Issue #43. Only 2 verbs currently use this pattern. The infrastructure cost isn't justified until more verbs need property requirements.

**When to revisit:** When a third verb needs a property requirement, or during a broader vocabulary schema revision.

### Consolidating Other Handlers

The `open`/`close` handlers have complex door/container logic that doesn't fit this pattern. The `take`/`drop`/`give`/`put` handlers have inventory transfer logic.

These could potentially share a different preamble utility, but that's a separate design effort.

---

## Progress Log

### Phase 1
**Status:** Complete

**Tasks completed:**
1. Created `utilities/handler_utils.py` with `find_action_target()` function
2. Created `tests/test_handler_utils.py` with 8 comprehensive tests
3. All tests passing

**Validation:** 1128 tests pass

### Phase 2
**Status:** Complete

**Tasks completed:**
1. Refactored `handle_push` to use `find_action_target()` - reduced from ~50 lines to ~16 lines
2. Refactored `handle_pull` to use `find_action_target()` - reduced from ~50 lines to ~16 lines
3. Refactored `handle_use` to use `find_action_target()` - added missing adjective support
4. Added `TestUseWithAdjective` tests to `test_interaction_handlers.py`

**Validation:** All 1128 tests pass

### Phase 3
**Status:** Complete

**Tasks completed:**
1. Refactored `handle_read` to use `find_action_target()` - added adjective support
2. Refactored `handle_climb` to use `find_action_target()` - added adjective support
3. Added `TestReadWithAdjective` tests (2 tests)
4. Added `TestClimbWithAdjective` tests (2 tests)

**Validation:** All 1134 tests pass (6 new tests added)

### Summary

All phases complete. The consolidation achieved:
- ~60% code reduction in the 5 refactored handlers
- All handlers now consistently support adjective disambiguation
- Messages use vocabulary-derived verbs from `action["verb"]`
- Single code path for common preamble logic in `find_action_target()`
