# Behavior Refactoring Design Review - Session 3 Summary

## Date: 2025-11-24

## Overview

Third review pass of `behavior_refactoring.md` following the two previous reviews documented in `behavior_refactoring_review.md` and `behavior_refactoring_review_2.md`. This session addressed the final two remaining design holes identified in earlier analysis: multi-update consistency (#4) and query handler architecture (#5).

## Issues Identified and Resolved

### 1. Multi-Update Consistency (Hole #4)

**Issue**: Handlers making multiple sequential `update()` calls lack transaction support. If a later update fails after earlier updates succeed, state becomes inconsistent. For example, in `handle_take`:
1. First update changes item location (succeeds)
2. Second update adds item to actor inventory (fails)
3. Result: Item location changed but inventory unchanged - inconsistent state

The same issue affects `handle_drop`, `handle_put`, and `handle_give` (which has three sequential updates).

**Resolution**: Implemented "Check and Report" pattern with lightweight error message convention:
- All handlers now check the result of follow-up `update()` calls
- If a follow-up fails, handler returns error with `"INCONSISTENT STATE:"` prefix
- This makes consistency violations immediately visible during development and testing
- Added "Multi-Update Limitation" section documenting the current limitation
- Expanded Deferred section with detailed "Transaction Support" discussion explaining:
  - What full transaction support would provide (batch updates, automatic rollback)
  - Why it's deferred (complexity of rollback, nested transactions, non-reversible behaviors)
  - Current mitigation strategy

**Example Pattern**:
```python
# First update
result = accessor.update(entity=item, changes={"location": actor_id}, event="on_take")
if not result.success:
    return HandlerResult(success=False, message=result.message)

# Follow-up update with error checking
inventory_result = accessor.update(entity=actor, changes={"+inventory": item.id})
if not inventory_result.success:
    return HandlerResult(
        success=False,
        message=f"INCONSISTENT STATE: Item location changed but inventory update failed: {inventory_result.message}"
    )
```

### 2. Query Handler Architecture (Hole #5)

**Issue**: Query handlers (`_query_location`, `_query_inventory`, `_query_entities`) in `llm_protocol.py` contain game-specific logic:
- Container visibility rules (surface containers vs enclosed containers)
- Open/closed semantics
- What items are accessible in a location

This violates Goal #3: making `llm_protocol.py` pure infrastructure with no game-specific knowledge.

**Resolution**: Moved all game-specific query logic to behavior modules:

1. **Created `behaviors/core/visibility.py`** with three utility functions:
   - `get_visible_items_in_location()` - Implements game-specific visibility rules (container semantics, surface vs enclosed)
   - `get_visible_npcs_in_location()` - Returns NPCs visible to actor
   - `get_doors_in_location()` - Returns accessible doors with their directions

2. **Refactored query handlers** to be thin wrappers:
   - Call visibility utilities from behavior modules
   - Serialize results to JSON using existing `_entity_to_dict()` helpers
   - Contain zero game logic about visibility, containers, or accessibility

3. **Updated architecture documentation**:
   - Added "Query Handling" section with motivation explaining why queries need same treatment as commands
   - Provided complete refactored `_query_location` example
   - Updated Module Organization to document `visibility.py`
   - Updated `llm_protocol.py` description to emphasize "pure infrastructure"
   - Updated Migration Path (Phase 2a and 2c)
   - Added new benefit: "Customizable visibility: Games can override visibility rules without touching infrastructure code"
   - Removed statement that queries were "out of scope"

**Example Before** (game logic in llm_protocol.py):
```python
# Check if container is surface or open
if container_props.get("is_surface", False) or container_props.get("open", False):
    items_in_container = self.state.get_items_in_location(container.id)
    items.extend(items_in_container)
```

**Example After** (pure infrastructure):
```python
from behaviors.core.visibility import get_visible_items_in_location
items = get_visible_items_in_location(accessor, loc.id, "player")
data["items"] = [self._entity_to_dict(item) for item in items]
```

## Design Improvements

The document now provides:

1. **Complete error handling pattern** for multi-update operations with clear conventions
2. **Clean separation of concerns**: All game logic (commands and queries) lives in behavior modules
3. **Pure infrastructure layer**: `llm_protocol.py` contains only routing and JSON serialization
4. **Extensible visibility**: Games can customize visibility rules by overriding functions in `visibility.py`
5. **Consistent architecture**: Queries follow the same delegation pattern as commands

## Files Modified

- `/Users/jed/Development/text-game/docs/behavior_refactoring.md` - Extensively updated:
  - Added Multi-Update Limitation section (lines 193-213)
  - Updated all multi-update handlers with error checking (handle_take, handle_drop, handle_put, handle_give)
  - Expanded Deferred section with Transaction Support discussion (lines 1283-1300)
  - Added Query Handling section with motivation and examples (lines 1159-1275)
  - Added `behaviors/core/visibility.py` specification (lines 1209-1266)
  - Updated Module Organization to include visibility.py (lines 805-814)
  - Updated llm_protocol.py description (lines 597-602)
  - Updated Migration Path phases 2a and 2c (lines 1319-1325, 1339-1349)
  - Updated Benefits section (lines 1148-1157)
  - Removed "out of scope" statement about queries

## Current Status

All identified design holes have been addressed. The design document is complete and ready for implementation with:
- Clear error handling patterns for current limitations
- Comprehensive architecture for both commands and queries
- Pure infrastructure layer with all game logic in behavior modules
- Well-documented deferred items for future enhancement

## Next Steps

The design is ready for implementation. Recommended approach from previous reviews:
- Implement one complete handler (e.g., `handle_take`) end-to-end first to validate the design before migrating all handlers
- Implement `visibility.py` utilities alongside first handler to validate query pattern

## Deferred Items (No Changes)

- Handler chaining (with use case documented)
- Undo/rollback support
- Transaction batching
- NPC AI using behavior handlers
- Behavior override/priority system
- Multi-participant event invocation
