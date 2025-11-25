# Phase 13 Implementation Issues

**Date:** 2025-11-25
**Phase:** Query Handler Refactoring
**Status:** Not Started - Blocked by Prerequisites

## Overview

Phase 13 requires refactoring query handlers in `json_protocol.py` (not `llm_protocol.py` as named in the phasing document) to use the new utility functions and StateAccessor. During exploration, several significant issues were discovered that must be addressed before Phase 13 can proceed.

## Phase 13 Goals

According to [behavior_refactoring_phasing.md](behavior_refactoring_phasing.md:2307-2345):

1. Refactor `_query_location()` to use:
   - `get_visible_items_in_location()`
   - `get_visible_actors_in_location()`
   - `get_doors_in_location()`

2. Refactor `_query_inventory()` to accept actor_id parameter and use accessor

3. Refactor `_query_entity()` to use accessor getter methods

4. All queries should pass actor_id to utilities for NPC support

## Critical Issues Discovered

### Issue 1: json_protocol.py Still Uses Old State Model

**Location:** [src/json_protocol.py](../src/json_protocol.py)

**Problem:** The file has not been updated to Phase 3's unified actor model:

```python
# Line 23-24: Constructor stores state directly
def __init__(self, state: GameState, behavior_manager: Optional[BehaviorManager] = None):
    self.state = state
    self.behavior_manager = behavior_manager
```

**Current State:**
- References `self.state.player` (line 70, 1241, and elsewhere)
- References `self.state.npcs` (lines 1227, 1312)
- No StateAccessor integration
- Implements visibility logic inline in query methods

**Expected State (Phase 3):**
- Should use `self.state.actors` dict with "player" key
- Should have StateAccessor for all state access
- Should delegate visibility logic to utility functions

### Issue 2: No StateAccessor in JSONProtocolHandler

**Problem:** JSONProtocolHandler doesn't have a StateAccessor instance, which is required for:
- Using utility functions (they all require `accessor` parameter)
- Proper actor_id threading
- Consistent state access patterns

**Required Changes:**
```python
# Constructor needs to be:
def __init__(self, state: GameState, behavior_manager: Optional[BehaviorManager] = None):
    self.state = state
    self.behavior_manager = behavior_manager
    self.accessor = StateAccessor(state, behavior_manager)  # ADD THIS
```

### Issue 3: Query Methods Implement Visibility Logic Inline

**Current Implementation Example** ([src/json_protocol.py:1177-1198](../src/json_protocol.py:1177-1198)):

```python
if "items" in include or not include:
    items = []
    # Get items directly in location
    for item in self.state.items:
        if item.location == loc.id:
            items.append(self._entity_to_dict(item))

    # Get items on surface containers and in open enclosed containers
    for container in self.state.items:
        container_props = container.properties.get("container")
        if container.location == loc.id and container_props:
            # Surface containers: always show items
            if container_props.get("is_surface", False):
                for item in self.state.items:
                    if item.location == container.id:
                        items.append(self._entity_to_dict(item))
            # Enclosed containers: only show if open
            elif container_props.get("open", False):
                for item in self.state.items:
                    if item.location == container.id:
                        items.append(self._entity_to_dict(item))

    data["items"] = items
```

**Should Be:**
```python
if "items" in include or not include:
    actor_id = message.get("actor_id", "player")  # Support NPC queries
    items = get_visible_items_in_location(self.accessor, loc.id, actor_id)
    data["items"] = [self._entity_to_dict(item) for item in items]
```

### Issue 4: Query Methods Don't Support actor_id Parameter

**Problem:** Current query methods are player-centric:

```python
def _query_inventory(self, message: Dict) -> Dict:
    """Query player inventory."""
    items = []
    for item_id in self.state.player.inventory:  # Hardcoded to player!
        item = self._get_item_by_id(item_id)
        if item:
            items.append(self._entity_to_dict(item))
```

**Should Support:**
```python
def _query_inventory(self, message: Dict) -> Dict:
    """Query actor inventory."""
    actor_id = message.get("actor_id", "player")  # Support NPC queries
    actor = self.accessor.get_actor(actor_id)
    if not actor:
        return {"type": "error", "message": f"Actor {actor_id} not found"}

    items = []
    for item_id in actor.inventory:
        item = self.accessor.get_item(item_id)
        if item:
            items.append(self._entity_to_dict(item))
```

## Available Utility Functions

The following utility functions exist in [utilities/utils.py](../utilities/utils.py) and are ready to use:

1. **get_visible_items_in_location(accessor, location_id, actor_id)** - Lines 147-162
   - Returns all visible items in a location
   - Currently returns all items (future: visibility rules)

2. **get_visible_actors_in_location(accessor, location_id, actor_id)** - Lines 165-182
   - Returns all visible actors, excluding the viewing actor
   - Already filters out actor_id from results

3. **get_doors_in_location(accessor, location_id, actor_id)** - Lines 185-204
   - Returns all doors connected to a location

4. **find_accessible_item(accessor, name, actor_id)** - Lines 12-49
   - Finds items in actor's location or inventory

5. **find_item_in_inventory(accessor, name, actor_id)** - Lines 52-75
   - Finds items in actor's inventory

All utility functions properly accept and use `actor_id` parameter for NPC support.

## Recommended Approach

### Option 1: Complete Phase 13 Prerequisites First

Before tackling Phase 13, complete:

1. **Update json_protocol.py to Phase 3 unified actor model**
   - Replace `self.state.player` with `self.state.actors["player"]`
   - Replace `self.state.npcs` with iteration over `self.state.actors`
   - Add unit tests for this refactor

2. **Add StateAccessor to JSONProtocolHandler**
   - Update `__init__` to create accessor instance
   - Update all state access to go through accessor

3. **Then proceed with Phase 13** as originally planned

### Option 2: Combined Phase 13 + Legacy Cleanup

Combine Phase 13 with updating json_protocol.py in one larger phase:

1. Add StateAccessor to constructor
2. Update to unified actor model
3. Refactor query methods to use utilities
4. Add actor_id parameter support
5. Write comprehensive tests

**Estimated Duration:** 6-8 hours (instead of original 3-4 hours)

### Option 3: Skip Phase 13 for Now

Phase 13 is categorized under "Infrastructure & Cleanup" and is not blocking:
- Command handlers (Phases 7-12) already use utilities
- json_protocol.py is primarily for LLM interaction
- Could be deferred until json_protocol.py is otherwise updated

## Testing Strategy

When Phase 13 is implemented, tests should verify:

### Test 1: Query Location Shows Visible Items
```python
def test_query_location_shows_visible_items(self):
    """Test that location query uses get_visible_items_in_location()."""
    # Create state with items in location
    # Query location
    # Verify correct items returned
    # Verify utility function was used (not inline logic)
```

### Test 2: Query Location is Actor-Specific
```python
def test_query_location_actor_specific(self):
    """Test that location query respects actor_id parameter."""
    # Create two actors in different locations
    # Query with player actor_id - should see player's location
    # Query with NPC actor_id - should see NPC's location
    # Verify different results
```

### Test 3: Query Inventory Supports NPCs
```python
def test_query_inventory_npc(self):
    """Test that inventory query works for NPCs."""
    # Give player item A
    # Give NPC item B
    # Query with actor_id="player" - should see item A
    # Query with actor_id="npc_guard" - should see item B
```

### Test 4: Query Entity Uses Accessor Getters
```python
def test_query_entity_uses_accessor(self):
    """Test that entity query uses accessor.get_item() etc."""
    # Query item by ID
    # Verify accessor.get_item() was called
    # Query door by ID
    # Verify accessor.get_door() was called
```

## File Locations

- **Query handlers:** [src/json_protocol.py](../src/json_protocol.py)
  - `_query_location()` - Line 1168
  - `_query_inventory()` - Line 1238
  - `_query_entity()` - Line 1252
  - `_query_entities()` - Line 1287

- **Utility functions:** [utilities/utils.py](../utilities/utils.py)
  - `get_visible_items_in_location()` - Line 147
  - `get_visible_actors_in_location()` - Line 165
  - `get_doors_in_location()` - Line 185

- **StateAccessor:** [src/state_accessor.py](../src/state_accessor.py)

## Next Steps

1. **Decide on approach** (Option 1, 2, or 3 above)
2. If proceeding:
   - Create Phase 13 test file: `tests/test_phase13_query_refactoring.py`
   - Update json_protocol.py constructor to add StateAccessor
   - Refactor query methods one at a time
   - Run tests after each refactor
   - Update phasing document with completion notes

## Notes

- Phase 12 (Interaction & Locks) is **COMPLETE** with all 138 phase tests passing
- json_protocol.py is a large file (1300+ lines) with many dependencies
- This refactor touches core LLM interaction code - test thoroughly
- Consider creating backup branch before starting Phase 13
