# Phase 6: Behavior Handler Annotations Plan

## Overview

Phase 6 was deferred from the original typing refinement work because adding type annotations to handlers exposed numerous mypy errors. This plan addresses those issues systematically.

**Root Cause**: `action.get()` returns `Optional[T]` values that are passed to utility functions expecting non-optional parameters. The fix requires updating utility signatures to accept Optional parameters with early returns.

## Sub-Phases

### Phase 6.1: Update Utility Function Signatures

Update 9 functions in `utilities/utils.py` to accept Optional parameters:

1. `find_accessible_item(name: Optional[WordEntry])` - return None if name is None
2. `find_actor(actor_name: Optional[WordEntry])` - return None if name is None
3. `find_item_by_word(word: Optional[WordEntry])` - return None if word is None
4. `get_display_name(word: Optional[WordEntry])` - return "" or None if word is None
5. `get_object_word(word: Optional[WordEntry])` - return None if word is None
6. `is_observable(entity, ...)` - already handles Optional correctly
7. `resolve_target_location(target: Optional[WordEntry])` - return None if None
8. `validate_actor_and_location(actor_id: Optional[str])` - return error if None
9. `resolve_indirect_object(indirect: Optional[WordEntry])` - return None if None

**Pattern**:
```python
def find_accessible_item(
    accessor: StateAccessor,
    name: Optional[WordEntry],  # Changed from WordEntry
    actor_id: ActorId,
    adjective: Optional[str] = None
) -> Optional[Item]:
    if name is None:
        return None
    # ... rest unchanged
```

### Phase 6.2: Update Positioning Module

Update `utilities/positioning.py`:
- `try_implicit_positioning(actor_id: Optional[ActorId])` - early return if None

### Phase 6.3: Add Handler Type Annotations

Add type annotations to 39 handlers across 12 files in `behaviors/core/`:

| File | Handlers | Count |
|------|----------|-------|
| manipulation.py | handle_take, handle_drop, handle_give, handle_put | 4 |
| perception.py | handle_look, handle_examine, handle_inventory | 3 |
| exits.py | handle_go, handle_climb, 10 direction handlers | 13 |
| interaction.py | handle_open, handle_close, handle_use, handle_read, handle_pull, handle_push | 6 |
| locks.py | handle_lock, handle_unlock | 2 |
| spatial.py | handle_climb, handle_descend, handle_enter, handle_exit, handle_sit, handle_stand | 6 |
| combat.py | handle_attack | 1 |
| consumables.py | handle_eat, handle_drink | 2 |
| meta.py | handle_wait, handle_help, handle_quit | 3 |

**Handler Signature Pattern**:
```python
def handle_take(
    action: ActionDict,
    accessor: StateAccessor,
    behavior_manager: BehaviorManager
) -> HandlerResult:
```

**Type Narrowing Pattern** (after validate_actor_and_location):
```python
def handle_take(action: ActionDict, accessor: StateAccessor, behavior_manager: BehaviorManager) -> HandlerResult:
    error, actor, location, actor_id = validate_actor_and_location(action, accessor)
    if error:
        return error

    # Add assertions for type narrowing
    assert actor is not None
    assert location is not None
    assert actor_id is not None

    # Now mypy knows these are non-None
    ...
```

### Phase 6.4: Update Handler Utils

Update `utilities/handler_utils.py` with proper type annotations:
- Import TYPE_CHECKING guard for circular import prevention
- Add return type annotations to all helper functions

## Implementation Notes

1. **Use assertions, not Optional checks**: After `validate_actor_and_location`, values are guaranteed non-None. Use `assert` to tell mypy this, not `if x is None: return`.

2. **Early returns for truly optional inputs**: For functions that receive `action.get("object")`, add early returns if the value is legitimately optional.

3. **TYPE_CHECKING imports**: Use conditional imports to avoid circular dependencies:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from src.behavior_manager import BehaviorManager
   ```

4. **Test after each sub-phase**: Run mypy and tests after completing each sub-phase.

## Estimated Effort

- Phase 6.1: ~1 hour (9 utility functions)
- Phase 6.2: ~15 minutes (1 module)
- Phase 6.3: ~2 hours (39 handlers)
- Phase 6.4: ~30 minutes (handler utils)

**Total**: ~4 hours

## Testing Strategy

1. Run `mypy src/ behaviors/ utilities/` after each sub-phase
2. Run full test suite to ensure no regressions
3. Verify type narrowing works with explicit mypy checks

## Files Modified

- `utilities/utils.py`
- `utilities/positioning.py`
- `utilities/handler_utils.py`
- `behaviors/core/manipulation.py`
- `behaviors/core/perception.py`
- `behaviors/core/exits.py`
- `behaviors/core/interaction.py`
- `behaviors/core/locks.py`
- `behaviors/core/spatial.py`
- `behaviors/core/combat.py`
- `behaviors/core/consumables.py`
- `behaviors/core/meta.py`
