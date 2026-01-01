# Entity Whereabouts Index - Design Document

**TL;DR**: Replace scattered entity location updates and dual representation (entity.location + location.items) with a centralized bidirectional index for O(1) lookups. Fixes Myconid Sanctuary bug where items appear in narration but can't be taken.

**GitHub Issue**: [#350](https://github.com/jedharris/text-game/issues/350)

## Problem Statement

Currently, entity location tracking is inconsistent:
- **Items have `.location` property** indicating where they are (location ID, actor ID for inventory, item ID for containers, part ID for surfaces, or "" for consumed)
- **Actors have `.location` property** indicating which location they're in
- **Locations have `.items` list** that is supposed to mirror items with `location == location_id`
- **Actors have `.inventory` list** that mirrors items with `location == actor_id`

This creates a **dual representation problem**:
1. The `.location` property is the source of truth (used by narration, most queries)
2. The `.items` and `.inventory` lists are supposed to be kept in sync but aren't
3. Location updates are scattered across ~13 different files
4. The `game_engine.py` parser context builder uses `location.items` (always empty) instead of scanning items

**Bug**: In Myconid Sanctuary, items appear in narration but can't be taken because `location.items` is empty while `item.location` is correctly set.

## Goals

1. **Single source of truth**: Entity `.location` property is authoritative
2. **Centralized updates**: All location changes go through one routine
3. **Fast bidirectional lookups**: O(1) to find entities at a location, O(1) to find where an entity is
4. **Semantic removal states**: Distinguish "consumed", "destroyed", "dead" rather than generic ""
5. **Uniform handling**: All entity types (items, actors, parts, locks, etc.) use same mechanism
6. **Debug support**: Clear state tracking for debugging and invariant checking

## Non-Goals

- Property enforcement (using `@property` to prevent direct assignment) - defer until later if violations occur
- Exits/ExitDescriptors - these connect locations but don't have a `.location` themselves (special case)
- Performance optimization beyond O(1) lookups - no caching beyond the index

## Design

### Terminology

- **Entity**: Any game object that can be "somewhere" (Item, Actor, Part, Lock, potentially others)
- **Where ID**: String indicating where an entity currently is:
  - Location ID (e.g., `"loc_forest"`)
  - Actor ID for inventory (e.g., `"player"`, `"npc_merchant"`)
  - Item ID for containers/surfaces (e.g., `"item_chest"`, `"item_table"`)
  - Part ID for parts (e.g., `"part_shelf"`)
  - Exit ID for doors (e.g., `"exit:loc_library:up"` - see Exit Extent below)
  - Removal state (e.g., `"__consumed_by_player__"` - see below)

### Removal States

Instead of `location = ""`, use semantic states with `__prefix__` to distinguish from valid IDs:

- `"__dead__"` - Actor was killed
- `"__consumed_by_player__"` - Item was eaten/drunk by player
- `"__consumed_by_<actor_id>__"` - Item was consumed by specific NPC (e.g., `"__consumed_by_npc_dragon__"`)
- `"__destroyed__"` - Item was destroyed (broke, burned, disintegrated, etc.)
- `"__removed__"` - Generic removal (for migration/debugging)

**Benefits**:
- Self-documenting (easy to understand in debugger)
- Queryable (can list all consumed items)
- State machine friendly (clear transitions: in_world → consumed → ...)
- Distinguishable from valid entity IDs (double underscore prefix convention)

### Bidirectional Index

Add to `GameState`:

```python
@dataclass
class GameState:
    # ... existing fields ...

    # NEW: Bidirectional whereabouts index
    _entities_at: Dict[str, Set[str]] = field(default_factory=dict)  # where_id → set(entity_ids)
    _entity_where: Dict[str, str] = field(default_factory=dict)      # entity_id → where_id
```

**Index maintenance**:
- Built once during `load_game_state()` from entity `.location` properties
- Updated atomically by centralized `set_entity_where()` function
- Both indexes updated together (impossible to desync if only one function modifies them)

### Centralized Update Function

Add to `StateAccessor`:

```python
def set_entity_where(self, entity_id: str, new_where: str) -> None:
    """
    Set entity whereabouts. Updates both entity.location and bidirectional index.

    This is the ONLY function that should modify entity locations.

    Args:
        entity_id: ID of entity to move (item, actor, part, lock, etc.)
        new_where: Where to place entity (location ID, actor ID, item ID, part ID, or removal state)

    Raises:
        ValueError: If entity_id not found
    """
    # Find the entity (try all entity types)
    entity = self._find_entity(entity_id)
    if not entity:
        raise ValueError(f"Entity {entity_id} not found")

    # Get old where_id
    old_where = self.game_state._entity_where.get(entity_id)

    # Remove from old location's set
    if old_where and old_where in self.game_state._entities_at:
        self.game_state._entities_at[old_where].discard(entity_id)
        if not self.game_state._entities_at[old_where]:  # Clean up empty sets
            del self.game_state._entities_at[old_where]

    # Update entity's location property
    entity.location = new_where

    # Update forward index
    if new_where:
        self.game_state._entity_where[entity_id] = new_where

        # Add to new location's set
        if new_where not in self.game_state._entities_at:
            self.game_state._entities_at[new_where] = set()
        self.game_state._entities_at[new_where].add(entity_id)
    else:
        # Entity removed from game entirely (shouldn't happen with semantic states)
        if entity_id in self.game_state._entity_where:
            del self.game_state._entity_where[entity_id]
```

Helper function:

```python
def _find_entity(self, entity_id: str) -> Optional[Any]:
    """Find entity by ID across all entity types."""
    # Try items
    for item in self.game_state.items:
        if item.id == entity_id:
            return item

    # Try actors
    if entity_id in self.game_state.actors:
        return self.game_state.actors[entity_id]

    # Try parts
    for part in self.game_state.parts:
        if part.id == entity_id:
            return part

    # Try locks
    for lock in self.game_state.locks:
        if lock.id == entity_id:
            return lock

    return None
```

### Query Functions

Update existing query functions to use index:

```python
def get_entities_at(self, where_id: str) -> List[Any]:
    """Get all entities at a location (items, actors, parts, locks)."""
    entity_ids = self.game_state._entities_at.get(where_id, set())
    return [self._find_entity(eid) for eid in entity_ids if self._find_entity(eid)]

def get_items_in_location(self, location_id: LocationId) -> List[Item]:
    """Get all items at a location."""
    entity_ids = self.game_state._entities_at.get(location_id, set())
    return [self.get_item(eid) for eid in entity_ids if self.get_item(eid)]

def get_entity_where(self, entity_id: str) -> Optional[str]:
    """Get where an entity is located. Returns where_id or None if not found."""
    return self.game_state._entity_where.get(entity_id)
```

### Index Building (Load Time)

In `load_game_state()`, after parsing all entities:

```python
def _build_whereabouts_index(game_state: GameState) -> None:
    """Build bidirectional whereabouts index from entity locations."""
    game_state._entities_at = {}
    game_state._entity_where = {}

    # Index all items
    for item in game_state.items:
        if item.location:
            if item.location not in game_state._entities_at:
                game_state._entities_at[item.location] = set()
            game_state._entities_at[item.location].add(item.id)
            game_state._entity_where[item.id] = item.location

    # Index all actors
    for actor in game_state.actors.values():
        if actor.location:
            if actor.location not in game_state._entities_at:
                game_state._entities_at[actor.location] = set()
            game_state._entities_at[actor.location].add(actor.id)
            game_state._entity_where[actor.id] = actor.location

    # Index all parts
    for part in game_state.parts:
        if part.part_of:
            # Parts use "part_of" instead of "location"
            # For now, don't include in whereabouts index
            # (parts are attached to entities, not "located" somewhere)
            pass

    # Index all locks (if they have location property)
    # Note: Locks might not have a location property currently
    for lock in game_state.locks:
        if hasattr(lock, 'location') and lock.location:
            if lock.location not in game_state._entities_at:
                game_state._entities_at[lock.location] = set()
            game_state._entities_at[lock.location].add(lock.id)
            game_state._entity_where[lock.id] = lock.location
```

Call this at end of `load_game_state()`:

```python
# Build whereabouts index
_build_whereabouts_index(game_state)
```

## Migration Strategy

### Phase 1: Add Index Infrastructure
1. Add `_entities_at` and `_entity_where` to GameState dataclass
2. Implement `_build_whereabouts_index()` and call from `load_game_state()`
3. Implement `set_entity_where()` in StateAccessor
4. Implement `_find_entity()` helper
5. Write unit tests for index building and updates

### Phase 2: Update Scattered Location Assignments
Replace all direct `.location =` assignments with `accessor.set_entity_where()`:

**Items (8 places)**:
1. `src/state_manager.py:840-849` - `move_item()` ✓
2. `behaviors/core/consumables.py:166` - drink consumption
3. `behaviors/core/consumables.py:210` - eat consumption
4. `behavior_libraries/offering_lib/offering_handler.py:104` - offering consumption
5. `behavior_libraries/actor_lib/combat.py:348` - drop items on death
6. `behavior_libraries/actor_lib/trading.py:132` - trade item transfer

**Actors (5 places)**:
7. `src/state_manager.py:860` - `move_actor()` ✓
8. `behavior_libraries/companion_lib/following.py:165` - follower movement
9. `behavior_libraries/npc_movement_lib/patrol.py:46` - patrol movement
10. `behavior_libraries/npc_movement_lib/wander.py:51` - wander movement
11. `behavior_libraries/actor_lib/morale.py:277` - flee/retreat movement

For each:
- Change `entity.location = new_value` → `accessor.set_entity_where(entity.id, new_value)`
- For removal states, use semantic constants instead of `""`
- Run existing tests to verify no regressions

### Phase 3: Update Query Functions
1. Update `get_items_in_location()` to use index
2. Update `game_engine.py:149-164` to use `accessor.get_items_in_location()` instead of `location.items`
3. Remove O(n) scans from `state_accessor.py` and `llm_protocol.py`
4. Add new `get_entities_at()` and `get_entity_where()` query functions

### Phase 4: Cleanup and Documentation
1. Consider deprecating `location.items` field (or keep for backwards compat but don't populate)
2. Consider deprecating `actor.inventory` field (same reasoning)
3. Document the pattern in authoring guide
4. Add debug validation function to check index consistency (optional, for testing)

## Testing Strategy

### Unit Tests
1. **Index building**: Load game state, verify index matches entity locations
2. **Index updates**: Call `set_entity_where()`, verify both indexes updated
3. **Query functions**: Verify `get_entities_at()` returns correct results
4. **Removal states**: Verify semantic states work correctly

### Integration Tests
1. **Myconid Sanctuary bug**: Items should appear in narration AND be takeable
2. **Consumption**: Drink/eat should update location to `__consumed_by_player__`
3. **Combat**: Items dropped on death should transfer to death location
4. **NPC movement**: Patrol/wander should update actor locations correctly

### Regression Tests
Run all existing tests - should pass without modification (internal change only).

### Exit Extent and Door Placement

**Problem**: Some exits have "extent" - they span a distance with features at different ends.

**Example** (from `examples/spatial_game`): The exit from Library to Sanctum has:
- A door at the library end (`door_at: "loc_library"`)
- Narrow stone stairs extending upward
- The sanctum at the top

Both ends of the exit reference `door_id: "door_sanctum"`, but the door is physically at one end.

**Solution**: Doors use exit-based location syntax:
```json
{
  "id": "door_sanctum",
  "location": "exit:loc_library:up"
}
```

This means:
- Doors ARE located somewhere (at an exit)
- The exit ID format is `"exit:<location_id>:<direction>"`
- This works with the whereabouts index (just another valid where_id)
- Actors/items CANNOT be located "in the extent" of an exit (only at endpoints)

**Index handling**:
- Doors are indexed at their exit location
- Query `get_entities_at("exit:loc_library:up")` returns `[door_sanctum]`
- The extent itself (stairs) is not a location - it's part of the exit's traversal description
- Actors/items on stairs would be at one endpoint or the other, not "on the stairs"

### ExitDescriptors vs First-Class Entities

**ExitDescriptors** (defined in `Location.exits` dict):
- NOT first-class entities with their own `.location`
- Embedded data structures that connect two locations
- Can have doors attached to them (doors have `.location = "exit:..."`)
- The exit itself is not "somewhere" - it IS a place (for doors)

**Doors** (Items with door properties):
- ARE first-class entities
- Have `.location = "exit:<location_id>:<direction>"`
- Indexed in whereabouts system
- Can be found via `get_entities_at("exit:loc_library:up")`

## Open Questions

1. **Parts**: Do parts need to be in the whereabouts index? They use `part_of` not `location`.
   - **Decision**: No, parts are attached to entities, not "located" somewhere. Skip for now.

2. **Locks**: Do locks have a `.location` property?
   - **Decision**: Currently no. Locks are referenced by doors (items). If we add lock location later, include in index.

3. **Property enforcement**: Should we add `@property` to prevent direct assignment?
   - **Decision**: Not initially. Rely on discipline during migration. Add enforcement later if violations occur during testing.

4. **Backwards compatibility**: Keep `location.items` and `actor.inventory` fields?
   - **Decision**: Defer - discuss after Phase 2. Could keep for save file compatibility but stop populating them.

## Benefits

1. **Single source of truth**: Entity `.location` is authoritative, index is derived
2. **Fast queries**: O(1) lookups in both directions
3. **Centralized updates**: Only one function modifies locations, impossible to miss an update
4. **Better debugging**: Semantic removal states, queryable index
5. **Fixes bug**: Myconid Sanctuary items will be takeable
6. **Cleaner code**: No more scattered O(n) scans

## Risks

1. **Migration effort**: Must update 13 scattered assignments (mitigated by mechanical changes)
2. **Index desync**: If code bypasses `set_entity_where()` (mitigated by discipline, optional property enforcement)
3. **Memory overhead**: Two dicts for index (negligible - ~100 entities in big_game)
4. **Save file format**: Might need migration if we remove `location.items` (deferred decision)

## Estimated Effort

- **Phase 1** (infrastructure): 1-2 hours
- **Phase 2** (migration): 2-3 hours
- **Phase 3** (queries): 1 hour
- **Phase 4** (cleanup): 1 hour

**Total**: 5-7 hours of Claude coding time

## Success Criteria

1. All unit tests pass
2. All integration tests pass
3. Myconid Sanctuary bug is fixed (items can be taken)
4. No performance regression (O(1) lookups are fast)
5. Code is cleaner (no scattered assignments, no O(n) scans)
