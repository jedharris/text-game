# Phase 13 Implementation Plan

**Date:** 2025-11-25
**Status:** Planning
**Goal:** Complete the behavior refactoring by updating json_protocol.py to use the new architecture

## Overview

Phase 13 was originally scoped as "Query Handler Refactoring" (3-4 hours), but the previous session discovered that [json_protocol.py](../src/json_protocol.py) still uses the old state model from before Phase 3. This implementation plan addresses all necessary updates to complete the refactoring and achieve a clean implementation of the new architecture.

## Current State Assessment

### What's Already Complete (Phases 1-12)

✅ **StateAccessor infrastructure** - [src/state_accessor.py](../src/state_accessor.py) implemented with:
- EventResult, UpdateResult, HandlerResult dataclasses
- Generic state access methods (get_item, get_actor, get_location, etc.)
- update() method with automatic behavior invocation
- _set_path() for nested property updates

✅ **Unified Actor Model (Phase 3)** - [src/state_manager.py](../src/state_manager.py):
- GameState.actors dict (all actors including player)
- Backward compatibility properties (player, npcs)

✅ **Utility Functions** - [utilities/utils.py](../utilities/utils.py):
- find_accessible_item(accessor, name, actor_id)
- find_item_in_inventory(accessor, name, actor_id)
- get_visible_items_in_location(accessor, location_id, actor_id)
- get_visible_actors_in_location(accessor, location_id, actor_id)
- get_doors_in_location(accessor, location_id, actor_id)
- actor_has_key_for_door(accessor, door, actor_id)

✅ **Command Handlers (Phases 7-12)** - All command handlers in behaviors/ use:
- StateAccessor for state access
- actor_id parameter throughout
- Utility functions for common operations
- HandlerResult return type

✅ **Test Infrastructure** - 138 passing phase tests

### What Needs to be Updated

❌ **json_protocol.py** - Still uses old patterns:
- Direct state access: `self.state.player`, `self.state.npcs`
- No StateAccessor instance
- Inline visibility logic in query methods
- Player-centric queries (no actor_id support)
- Old command dispatch to internal `_cmd_*` methods

## Problems to Solve

### Problem 1: json_protocol.py Uses Old State Model

**Current:**
```python
# Line 23-24
def __init__(self, state: GameState, behavior_manager: Optional[BehaviorManager] = None):
    self.state = state
    self.behavior_manager = behavior_manager
```

**Issues:**
- References `self.state.player` (70, 1241, etc.) - should use `self.state.actors["player"]`
- References `self.state.npcs` (1227, 1312) - should iterate `self.state.actors`
- No StateAccessor for consistent state access

**Solution:**
Update constructor and all references to use unified actor model via StateAccessor.

### Problem 2: Query Methods Implement Visibility Inline

**Current** ([lines 1177-1198](../src/json_protocol.py)):
```python
# 50+ lines of inline visibility logic
for item in self.state.items:
    if item.location == loc.id:
        items.append(self._entity_to_dict(item))
# ...more inline logic for containers...
```

**Should be:**
```python
items = get_visible_items_in_location(self.accessor, loc.id, actor_id)
data["items"] = [self._entity_to_dict(item) for item in items]
```

**Solution:**
Refactor query methods to use utility functions from utilities/utils.py.

### Problem 3: No Actor ID Support in Queries

**Current:**
```python
def _query_inventory(self, message: Dict) -> Dict:
    """Query player inventory."""
    for item_id in self.state.player.inventory:  # Hardcoded!
```

**Solution:**
All query methods should accept and use actor_id parameter from message dict.

## Implementation Strategy

Given the scope of changes, this phase will be broken into 5 sub-phases to ensure systematic progress and continuous test validation.

---

## Sub-Phase 13a: Add StateAccessor to JSONProtocolHandler

**Duration:** ~30 minutes

**Goal:** Add StateAccessor instance without breaking existing functionality

### Tasks

1. Update constructor to create StateAccessor:
```python
def __init__(self, state: GameState, behavior_manager: Optional[BehaviorManager] = None):
    self.state = state
    self.behavior_manager = behavior_manager
    self.accessor = StateAccessor(state, behavior_manager)  # ADD
```

2. Add import at top of file:
```python
from src.state_accessor import StateAccessor, HandlerResult
```

### Tests

Run existing tests to ensure nothing breaks:
```bash
python -m pytest tests/ -v
```

### Validation

- All existing tests still pass
- self.accessor is available throughout JSONProtocolHandler

---

## Sub-Phase 13b: Update Direct State Access to Unified Actor Model

**Duration:** ~1-2 hours

**Goal:** Replace all `self.state.player` and `self.state.npcs` with unified actor model

### Tasks

1. **Identify all references** (grep results show ~19 occurrences):
   - Lines: 71, 118, 282, 310, 327, 377, 415, 479, 764, 797, 833, 869, 1095, 1154, 1227, 1241, 1312, 1355, 1382, 1430, 1539

2. **Replace patterns:**
   - `self.state.player` → `self.state.actors["player"]` or `self.accessor.get_actor("player")`
   - `self.state.player.location` → `self.accessor.get_actor("player").location`
   - `self.state.player.inventory` → `self.accessor.get_actor("player").inventory`
   - `for npc in self.state.npcs:` → `for actor_id, actor in self.state.actors.items(): if actor_id != "player":`

3. **Prefer accessor methods** over direct state access where appropriate:
   - Use `self.accessor.get_actor(actor_id)` instead of dict access
   - Use `self.accessor.get_current_location(actor_id)` instead of manual lookup

### Example Changes

**Before:**
```python
def _cmd_take(self, message: Dict) -> Dict:
    # ...
    self.state.player.inventory.append(item.id)
```

**After:**
```python
def _cmd_take(self, message: Dict) -> Dict:
    # ...
    player = self.accessor.get_actor("player")
    player.inventory.append(item.id)
```

### Tests

1. Run all existing tests:
```bash
python -m pytest tests/ -v
```

2. Specifically verify commands that modify player state:
   - test_take_item
   - test_drop_item
   - test_go_command
   - test_inventory

### Validation

- All 138 existing phase tests still pass
- No test regressions
- Code uses unified actor model consistently

---

## Sub-Phase 13c: Refactor Query Methods to Use Utilities

**Duration:** ~2-3 hours

**Goal:** Replace inline visibility logic with utility function calls

### Tasks

1. **Refactor `_query_location()` (line ~1168)**

**Before:**
```python
def _query_location(self, message: Dict) -> Dict:
    # 50+ lines of inline visibility logic
    items = []
    for item in self.state.items:
        if item.location == loc.id:
            items.append(self._entity_to_dict(item))
    # ...container logic...
```

**After:**
```python
def _query_location(self, message: Dict) -> Dict:
    """Query location details."""
    from utilities.utils import get_visible_items_in_location, get_visible_actors_in_location, get_doors_in_location

    actor_id = message.get("actor_id", "player")
    loc = self.accessor.get_current_location(actor_id)
    if not loc:
        return {"type": "error", "message": "Location not found"}

    include = message.get("include", [])
    data = {"location": self._location_to_dict(loc)}

    if "items" in include or not include:
        items = get_visible_items_in_location(self.accessor, loc.id, actor_id)
        data["items"] = [self._entity_to_dict(item) for item in items]

    if "doors" in include or not include:
        doors = get_doors_in_location(self.accessor, loc.id, actor_id)
        data["doors"] = [self._door_to_dict(door) for door in doors]

    if "exits" in include or not include:
        data["exits"] = {
            direction: {"type": exit_desc.type, "to": exit_desc.to}
            for direction, exit_desc in loc.exits.items()
        }

    if "actors" in include or not include:
        actors = get_visible_actors_in_location(self.accessor, loc.id, actor_id)
        data["actors"] = [self._actor_to_dict(actor) for actor in actors]

    return {
        "type": "query_response",
        "query_type": "location",
        "data": data
    }
```

2. **Refactor `_query_inventory()` (line ~1238)**

**Before:**
```python
def _query_inventory(self, message: Dict) -> Dict:
    """Query player inventory."""
    items = []
    for item_id in self.state.player.inventory:
        item = self._get_item_by_id(item_id)
        if item:
            items.append(self._entity_to_dict(item))
```

**After:**
```python
def _query_inventory(self, message: Dict) -> Dict:
    """Query actor inventory."""
    actor_id = message.get("actor_id", "player")
    actor = self.accessor.get_actor(actor_id)
    if not actor:
        return {"type": "error", "message": f"Actor {actor_id} not found"}

    items = []
    for item_id in actor.inventory:
        item = self.accessor.get_item(item_id)
        if item:
            items.append(self._entity_to_dict(item))

    return {
        "type": "query_response",
        "query_type": "inventory",
        "data": {"items": items}
    }
```

3. **Refactor `_query_entity()` (line ~1252)**

**Before:**
```python
def _query_entity(self, message: Dict) -> Dict:
    # Uses self._get_item_by_id(), self._get_door_by_id(), etc.
```

**After:**
```python
def _query_entity(self, message: Dict) -> Dict:
    """Query specific entity by ID."""
    entity_id = message.get("id")
    if not entity_id:
        return {"type": "error", "message": "Missing entity ID"}

    # Try each entity type
    entity = self.accessor.get_item(entity_id)
    if entity:
        return {
            "type": "query_response",
            "query_type": "entity",
            "data": {"entity": self._entity_to_dict(entity)}
        }

    entity = self.accessor.get_door(entity_id)
    if entity:
        return {
            "type": "query_response",
            "query_type": "entity",
            "data": {"entity": self._door_to_dict(entity)}
        }

    entity = self.accessor.get_actor(entity_id)
    if entity:
        return {
            "type": "query_response",
            "query_type": "entity",
            "data": {"entity": self._actor_to_dict(entity)}
        }

    entity = self.accessor.get_location(entity_id)
    if entity:
        return {
            "type": "query_response",
            "query_type": "entity",
            "data": {"entity": self._location_to_dict(entity)}
        }

    return {"type": "error", "message": f"Entity {entity_id} not found"}
```

4. **Refactor `_query_entities()` (line ~1287)** - Similar pattern to above

### Tests (write first)

Create [tests/test_phase13_query_refactoring.py](../tests/test_phase13_query_refactoring.py):

```python
def test_query_location_shows_visible_items(state_with_items):
    """Test that location query uses get_visible_items_in_location()."""
    handler = JSONProtocolHandler(state_with_items)

    result = handler.handle_message({
        "type": "query",
        "query_type": "location",
        "include": ["items"]
    })

    assert result["type"] == "query_response"
    assert "items" in result["data"]
    # Verify correct items are visible

def test_query_location_actor_specific(state_with_multiple_actors):
    """Test that location query respects actor_id parameter."""
    handler = JSONProtocolHandler(state_with_multiple_actors)

    # Query as player
    result_player = handler.handle_message({
        "type": "query",
        "query_type": "location",
        "actor_id": "player"
    })

    # Query as NPC
    result_npc = handler.handle_message({
        "type": "query",
        "query_type": "location",
        "actor_id": "npc_guard"
    })

    # Should see different locations
    assert result_player["data"]["location"]["id"] != result_npc["data"]["location"]["id"]

def test_query_inventory_npc(state_with_npc):
    """Test that inventory query works for NPCs."""
    handler = JSONProtocolHandler(state_with_npc)

    result = handler.handle_message({
        "type": "query",
        "query_type": "inventory",
        "actor_id": "npc_guard"
    })

    assert result["type"] == "query_response"
    assert "items" in result["data"]
    # Verify NPC's items are returned

def test_query_entity_uses_accessor(state_with_items):
    """Test that entity query uses accessor.get_* methods."""
    handler = JSONProtocolHandler(state_with_items)

    result = handler.handle_message({
        "type": "query",
        "query_type": "entity",
        "id": "item_sword"
    })

    assert result["type"] == "query_response"
    assert result["data"]["entity"]["id"] == "item_sword"
```

### Validation

- New tests pass
- All existing tests still pass
- Query methods use utilities, not inline logic
- Queries support actor_id parameter

---

## Sub-Phase 13d: Update Command Dispatch (if still using old `_cmd_*`)

**Duration:** ~1 hour (conditional - may already be complete)

**Goal:** Ensure command dispatch uses behavior handlers, not internal `_cmd_*` methods

### Investigation

Check if json_protocol.py still has `_cmd_*` methods and command dispatch logic. Previous phases should have already migrated to behavior handlers via BehaviorManager.

### Tasks (if needed)

1. Remove old `_cmd_*` methods
2. Update command dispatch to use `self.behavior_manager.invoke_handler()`
3. Remove any command routing tables that reference old methods

### Tests

```bash
python -m pytest tests/ -v
```

### Validation

- No `_cmd_*` methods remain in json_protocol.py
- Command dispatch goes through BehaviorManager
- All tests pass

---

## Sub-Phase 13e: Update Visibility Functions for Containers

**Duration:** ~1 hour

**Goal:** Ensure get_visible_items_in_location() handles containers correctly

### Current Issue

The utility function [get_visible_items_in_location()](../utilities/utils.py:147-162) currently just returns all items in the location. It doesn't handle:
- Items on surface containers (always visible)
- Items in open enclosed containers (visible when open)
- Items in closed containers (not visible)

### Tasks

1. **Update get_visible_items_in_location() in utilities/utils.py:**

```python
def get_visible_items_in_location(accessor, location_id: str, actor_id: str) -> List:
    """
    Get all visible items in a location.

    Includes:
    - Items directly in the location
    - Items on surface containers
    - Items in open enclosed containers

    Args:
        accessor: StateAccessor instance
        location_id: ID of the location
        actor_id: ID of the actor viewing (for future visibility rules)

    Returns:
        List of visible Item objects
    """
    visible_items = []

    # Items directly in location
    items_in_location = accessor.get_items_in_location(location_id)
    visible_items.extend(items_in_location)

    # Check containers for visible items
    for container in items_in_location:
        container_props = container.properties.get("container")
        if not container_props:
            continue

        # Surface containers: always show contents
        if container_props.get("is_surface", False):
            visible_items.extend(accessor.get_items_in_location(container.id))
        # Enclosed containers: only show if open
        elif container_props.get("open", False):
            visible_items.extend(accessor.get_items_in_location(container.id))

    return visible_items
```

2. **Write tests** for container visibility:

```python
def test_visible_items_includes_surface_container_contents():
    """Items on surface containers are always visible."""
    # Create table (surface container) with item on it
    # Query location
    # Verify item on table is in visible items

def test_visible_items_includes_open_container_contents():
    """Items in open containers are visible."""
    # Create chest (enclosed container, open) with item in it
    # Query location
    # Verify item in chest is in visible items

def test_visible_items_excludes_closed_container_contents():
    """Items in closed containers are not visible."""
    # Create chest (enclosed container, closed) with item in it
    # Query location
    # Verify item in chest is NOT in visible items
```

### Validation

- Container visibility tests pass
- Query location tests still pass
- Existing tests don't regress

---

## Final Validation & Cleanup

**Duration:** ~30 minutes

### Tasks

1. **Run full test suite:**
```bash
python -m pytest tests/ -v
```

2. **Verify all 138+ tests pass** (138 from phases 1-12, plus new phase 13 tests)

3. **Code review checklist:**
   - [ ] No `self.state.player` references remain
   - [ ] No `self.state.npcs` references remain
   - [ ] All queries use utility functions
   - [ ] All queries support actor_id parameter
   - [ ] StateAccessor is used consistently
   - [ ] No inline visibility logic remains
   - [ ] All helper methods use accessor, not direct state

4. **Update documentation:**
   - Mark Phase 13 as complete in [behavior_refactoring_phasing.md](behavior_refactoring_phasing.md)
   - Document any issues encountered in phase_13_issues.md (if any)

5. **Commit changes:**
```bash
git add .
git commit -m "Phase 13: Complete - Query refactoring and unified actor model in json_protocol.py

- Added StateAccessor to JSONProtocolHandler
- Migrated all state access to unified actor model (actors dict)
- Refactored query methods to use utility functions
- Added actor_id support to all queries
- Updated get_visible_items_in_location() for container visibility
- All 138+ phase tests passing"
```

---

## Risk Assessment & Mitigation

### Risk 1: Breaking Existing Functionality

**Mitigation:** Incremental sub-phases with test validation after each

### Risk 2: Test Coverage Gaps

**Mitigation:** Write new tests before refactoring (TDD approach)

### Risk 3: Overlooked References

**Mitigation:** Use grep to find all occurrences before starting each sub-phase

### Risk 4: Time Overrun

**Original estimate:** 3-4 hours
**Revised estimate:** 5-7 hours (due to scope expansion)

**Mitigation:** Sub-phases can be stopped at any point with partial progress committed

---

## Success Criteria

Phase 13 is complete when:

1. ✅ JSONProtocolHandler has StateAccessor instance
2. ✅ All state access uses unified actor model (no `self.state.player` or `self.state.npcs`)
3. ✅ Query methods use utility functions from utilities/utils.py
4. ✅ All queries support actor_id parameter
5. ✅ Container visibility works correctly (surface/open/closed)
6. ✅ All 138 existing phase tests still pass
7. ✅ New phase 13 tests pass
8. ✅ No inline visibility logic remains
9. ✅ Code follows architecture in behavior_refactoring.md

---

## Next Steps After Phase 13

Once Phase 13 is complete, the behavior refactoring will be essentially done. Remaining phases are:

- **Phase 14:** Inconsistent State Handling (add error detection/recovery)
- **Phase 15:** Cleanup & Removal (delete old code, finalize structure)

These are infrastructure improvements and can be tackled independently.

---

## Notes for Implementation

- **Backward Compatibility:** GameState has player/npcs properties for backward compatibility, but new code should use actors dict
- **Error Handling:** Query methods should return error dicts when entities not found
- **Actor ID:** Always extract actor_id from message with default "player": `actor_id = message.get("actor_id", "player")`
- **Defensive Checks:** Always check if accessor.get_*() returns None before accessing properties
- **Testing Philosophy:** Use real GameState objects, no mocking required
