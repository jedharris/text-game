# Handler Consolidation Plan

## Overview

This plan consolidates duplicated patterns across behavior handlers into reusable helpers in `utilities/handler_utils.py`. This reduces code duplication, simplifies handler implementations, and makes Phase 6 typing easier (fewer functions to annotate).

## New Helpers

### 1. `execute_entity_action`

Wraps the common pattern of invoking behaviors on an entity and building a result message.

```python
def execute_entity_action(
    accessor: StateAccessor,
    entity: Entity,
    changes: Dict[str, Any],
    verb: str,
    actor_id: str,
    base_message: str,
    positioning_msg: Optional[str] = None
) -> HandlerResult:
    """
    Execute an action on an entity with behavior invocation and message building.

    Handles:
    - accessor.update() call with verb/actor_id
    - Failure handling
    - Message building with behavior result
    - Positioning message integration
    - Serialization for llm_context
    """
```

**Handlers that can use this** (9):
- `handle_examine` (item, part, actor variants)
- `handle_open`
- `handle_close` (if it exists separately)
- `_handle_generic_interaction` (use, read, pull, push)
- `handle_attack`
- `handle_climb`
- `_handle_spatial_action`
- `_handle_consume` (eat, drink)

### 2. `transfer_item_to_actor`

Handles taking an item into an actor's inventory with rollback.

```python
def transfer_item_to_actor(
    accessor: StateAccessor,
    item: Item,
    actor: Actor,
    actor_id: str,
    verb: str,
    item_changes: Dict[str, Any],
    rollback_location: str
) -> Tuple[Optional[UpdateResult], Optional[HandlerResult]]:
    """
    Transfer an item to an actor's inventory.

    Handles:
    - Update item with changes (triggers behaviors)
    - Add item to actor's inventory
    - Rollback item location on inventory failure

    Returns:
        (update_result, None) on success
        (None, error_result) on failure
    """
```

**Handlers that can use this** (2):
- `handle_take`
- `handle_give` (second half - add to recipient)

### 3. `transfer_item_from_actor`

Handles removing an item from an actor's inventory with rollback.

```python
def transfer_item_from_actor(
    accessor: StateAccessor,
    item: Item,
    actor: Actor,
    actor_id: str,
    verb: str,
    item_changes: Dict[str, Any]
) -> Tuple[Optional[UpdateResult], Optional[HandlerResult]]:
    """
    Transfer an item from an actor's inventory.

    Handles:
    - Update item with changes (triggers behaviors)
    - Remove item from actor's inventory
    - Rollback item location on inventory failure

    Returns:
        (update_result, None) on success
        (None, error_result) on failure
    """
```

**Handlers that can use this** (3):
- `handle_drop`
- `handle_put`
- `handle_give` (first half - remove from giver)

### 4. `validate_container_accessible`

Validates a container is open (or is a surface) before allowing access.

```python
def validate_container_accessible(
    container: Item,
    verb: str
) -> Optional[HandlerResult]:
    """
    Validate that a container can be accessed (is open or is a surface).

    Returns:
        None if accessible, HandlerResult error if closed
    """
```

**Handlers that can use this** (3):
- `handle_take` (from container)
- `handle_put` (into container)
- `_handle_lock_operation` (container branch)

### 5. `check_actor_has_key`

Validates an actor has a key that opens a lock.

```python
def check_actor_has_key(
    actor: Actor,
    lock: Lock,
    item_name: str,
    verb: str
) -> Optional[HandlerResult]:
    """
    Check if actor has a key that opens the given lock.

    Returns:
        None if actor has key, HandlerResult error if not
    """
```

**Handlers that can use this** (2):
- `_handle_lock_operation` (door branch)
- `_handle_lock_operation` (container branch)

## Implementation Phases

### Phase 1: Add New Helpers

Add the 5 new helper functions to `utilities/handler_utils.py` with full type annotations.

**Files modified:**
- `utilities/handler_utils.py`

**Tests:**
- Add `tests/test_handler_consolidation.py` with unit tests for each helper

### Phase 2: Refactor Simple Action Handlers

Update handlers that can use `execute_entity_action`:

1. `behaviors/core/perception.py` - `handle_examine` (3 call sites)
2. `behaviors/core/interaction.py` - `_handle_generic_interaction`
3. `behaviors/core/combat.py` - `handle_attack`
4. `behaviors/core/spatial.py` - `_handle_spatial_action`, `handle_climb`
5. `behaviors/core/consumables.py` - `_handle_consume`

**Files modified:**
- `behaviors/core/perception.py`
- `behaviors/core/interaction.py`
- `behaviors/core/combat.py`
- `behaviors/core/spatial.py`
- `behaviors/core/consumables.py`

### Phase 3: Refactor Inventory Handlers

Update handlers that use inventory transfer helpers:

1. `handle_take` - use `transfer_item_to_actor`
2. `handle_drop` - use `transfer_item_from_actor`
3. `handle_put` - use `transfer_item_from_actor`
4. `handle_give` - use both helpers sequentially

**Files modified:**
- `behaviors/core/manipulation.py`

### Phase 4: Refactor Container/Lock Validation

Update handlers that use container and key validation:

1. `handle_take` - use `validate_container_accessible` for container case
2. `handle_put` - use `validate_container_accessible`
3. `_handle_lock_operation` - use `validate_container_accessible` and `check_actor_has_key`

**Files modified:**
- `behaviors/core/manipulation.py`
- `behaviors/core/locks.py`

### Phase 5: Cleanup

1. Remove any dead code from handlers
2. Verify all tests pass
3. Run mypy to check types

## Expected Code Reduction

| Handler | Current Lines | Expected Lines | Reduction |
|---------|--------------|----------------|-----------|
| handle_examine | ~80 | ~40 | 50% |
| _handle_generic_interaction | ~50 | ~25 | 50% |
| handle_take | ~90 | ~50 | 45% |
| handle_drop | ~80 | ~45 | 45% |
| handle_put | ~100 | ~60 | 40% |
| handle_give | ~130 | ~70 | 45% |
| _handle_lock_operation | ~130 | ~90 | 30% |

**Total estimated reduction**: ~200 lines across handlers

## Benefits

1. **Less duplication** - Common patterns extracted once
2. **Easier typing** - Type annotations in 5 helpers instead of 15+ handlers
3. **Consistent error messages** - Centralized message building
4. **Easier maintenance** - Fix bugs in one place
5. **Clearer handler logic** - Handlers focus on what's unique to them

## Testing Strategy

1. **Unit tests for helpers** - Test each helper in isolation with mocks
2. **Integration tests unchanged** - Existing handler tests should still pass
3. **Run full test suite** after each phase

## Relationship to Phase 6 Typing

This consolidation should be done **before** Phase 6 typing work because:
- Fewer functions need type annotations
- Helper signatures are cleaner (entity types, not action dicts)
- Reduces the scope of Phase 6 significantly

After consolidation, Phase 6 will primarily need to:
1. Add types to the 5 new helpers (done during this work)
2. Add handler signatures (simpler now)
3. Update remaining utility functions in `utilities/utils.py`
