# Behavior Refactoring Design Review - Session Summary

## Date: 2025-11-23

## Overview

Completed a thorough design review of `behavior_refactoring.md`. The document was substantially improved through discussion and is now internally consistent.

## Key Design Decisions Made

### 1. Atomic Updates with `related_changes`
The `update()` method now accepts a `related_changes` parameter for atomic multi-entity updates. This solves the problem of inventory changes happening separately from item location changes.

```python
result = accessor.update(
    entity=item,
    changes={"location": accessor.actor_id},
    event="on_take",
    related_changes=[
        (actor, {"+inventory": item.id})
    ]
)
```

The `+` and `-` prefixes in paths indicate list append/remove operations.

### 2. Entity Behaviors Receive Accessor
Changed entity behavior signature from `(entity, state, context)` to `(entity, accessor, context)`. This allows behaviors to query any state they need rather than having StateAccessor anticipate what to put in context. Keeps StateAccessor generic.

### 3. Separated Message and Data in Results
Both `EventResult` and `UpdateResult` now have:
- `message: Optional[str]` - Human-readable text
- `data: Optional[Dict]` - Structured info for programmatic use

This eliminates `isinstance` checks and clarifies intent.

### 4. Handler Chaining via `invoke_next_handler()`
Chose `invoke_next_handler("verb", accessor, action)` over `get_base_handler()`. Simpler API - single call, no intermediate variable, and semantically accurate (it's not necessarily the "base" handler).

### 5. Semantic Events
Added `on_put` event separate from `on_drop` so entity behaviors can distinguish putting in container vs dropping on ground.

### 6. Convenience Methods Removal
`move_item()` and `set_player_location()` in state_manager.py will be removed - they contain game semantics that should live in behavior handlers.

## Deferred Items

- Multi-participant event invocation (notifying actor/location when item is taken)
- Undo/rollback support
- Transaction batching
- NPC AI using behavior handlers
- Behavior override/priority system

The multi-participant pattern was explicitly deferred pending real use cases.

## Areas That May Need Attention in Next Review

1. **Testing strategy section** - Has basic examples but may need more detail for implementation planning

2. **Error handling** - What happens if `_set_path` operations fail (e.g., removing item not in list)? Currently will raise exceptions, which surfaces bugs but may need graceful handling.

3. **Query handling** - Explicitly out of scope but may need its own design eventually

4. **Phase 2d (NPC AI)** - Mentioned but not detailed; will need its own design

5. **Validator pluggability** - Document asks "could validators be made pluggable?" - decision needed

## Implementation Considerations

The migration path is clearly defined in three phases:
- Phase 2a: StateAccessor and utils
- Phase 2b: Move command handlers
- Phase 2c: Simplify infrastructure

Suggest implementing one complete handler (e.g., `handle_take`) end-to-end first to validate the design before migrating all handlers.

## Files Modified

- `/Users/jed/Development/text-game/docs/behavior_refactoring.md` - Main design document, extensively updated
