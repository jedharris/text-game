# Description Handling Cleanup

## Status: COMPLETED

All phases completed successfully. See "Work Completed" section at end for details.

## Motivation

During the implementation of exit descriptions (issue #20), a data structure mismatch was discovered: the test expected `description` in `properties`, but the fix placed it at the top level. This revealed broader inconsistencies in how different entity types handle core fields like `name`, `description`, and `llm_context`.

Consistent data structures enable:
- **Simpler code** - Shared patterns can be extracted into reusable utilities
- **Fewer bugs** - Developers don't need to remember entity-specific quirks
- **Better author experience** - Game authors use consistent JSON patterns everywhere

## Final State (After Cleanup)

### Entity Field Comparison

| Entity | `name` | `description` | `llm_context` | `properties` | `behaviors` | Accessor |
|--------|--------|---------------|---------------|--------------|-------------|----------|
| Location | top-level | top-level | in properties | dict | top-level | @property |
| Item | top-level | top-level | in properties | dict | top-level | @property |
| ExitDescriptor | top-level | top-level | in properties | dict | top-level | @property |
| Actor | top-level | top-level | in properties | dict | top-level | @property |
| Lock | top-level | top-level | in properties | dict | top-level | @property |

**All entities now follow the same pattern:** top-level `id`, `name`, `description`, `behaviors`, with `llm_context` accessible via `@property` from `properties`.

## Original Inconsistencies (Now Fixed)

#### 1. Lock Class Was Missing Core Fields (FIXED)

The `Lock` dataclass previously lacked `name`, `description`, and `behaviors` as top-level fields.

**Before:**
```python
@dataclass
class Lock:
    id: str
    properties: Dict[str, Any] = field(default_factory=dict)
```

**After:**
```python
@dataclass
class Lock:
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        return self.properties.get("llm_context")
```

#### 2. Actor Missing `llm_context` Property Accessor (FIXED)

Actor now has the `@property` accessor for `llm_context` like other entities.

#### 3. Lock Missing `llm_context` Property Accessor (FIXED)

Lock now has the `@property` accessor for `llm_context`.

### Parser/Serializer Patterns

Each entity type has its own `_parse_*` function, but serializers now share a common `_serialize_entity()` helper:

| Entity | Parser | Serializer |
|--------|--------|------------|
| Location | `_parse_location()` | `_serialize_location()` → uses `_serialize_entity()` |
| Item | `_parse_item()` | `_serialize_item()` → uses `_serialize_entity()` |
| Exit | `_parse_exit()` | `_serialize_exit()` → uses `_serialize_entity()` |
| Actor | `_parse_actor()` | `_serialize_actor()` → uses `_serialize_entity()` |
| Lock | `_parse_lock()` | `_serialize_lock()` → uses `_serialize_entity()` |

**Parsers remain separate** because each entity has specific logic:
- Location: Nested exit parsing, items list
- Actor: `actor_id` parameter for dict-key override
- Item/Lock: Simpler but different core_fields sets

**Serializers consolidated** into `_serialize_entity()` helper:
```python
def _serialize_entity(
    entity,
    required_fields: List[str],
    optional_fields: List[str] = None
) -> Dict[str, Any]:
    """Generic entity serializer."""
    result = {}
    for field in required_fields:
        result[field] = getattr(entity, field)
    for field in (optional_fields or []):
        value = getattr(entity, field, None)
        if value:
            result[field] = value
    result.update(entity.properties)
    if entity.behaviors:
        result['behaviors'] = entity.behaviors
    return result
```

### LLM Protocol `_*_to_dict` Functions

`src/llm_protocol.py` has separate functions for building LLM context dictionaries:

- `_location_to_dict()` - handles Location
- `_item_to_dict()` - handles Item
- `_actor_to_dict()` - handles Actor
- `_exit_to_dict()` - handles ExitDescriptor
- `_door_to_dict()` - handles door Items

These could potentially share more logic if entity structures were consistent.

## Implementation (Completed)

### Phase 1: Make Lock Consistent ✓

**COMPLETED.** Added `name`, `description`, `behaviors`, and `llm_context` accessor to Lock class.

### Phase 2: Add Actor `llm_context` Accessor ✓

**COMPLETED.** Added `@property llm_context` accessor to Actor class.

### Phase 3: Consolidate Serializers ✓

**COMPLETED.** Created `_serialize_entity()` helper and refactored all 5 serializers to use it.

**Decision:** Parsers remain separate due to entity-specific logic (nested exits in Location, `actor_id` parameter in Actor). Serializers consolidated because they all follow the same pattern.

### Phase 4: Remove Backward Compatibility ✓

**COMPLETED.** Removed backward compatibility handling from `_parse_actor()` per project policy.

The old code handled game saves where actor data might not have an `id` field:
```python
# REMOVED: Handle backward compatibility - old saves may have player_state without id
if 'id' not in raw and actor_id:
    raw = dict(raw)
    raw['id'] = actor_id
```

Now simplified to:
```python
effective_id = actor_id or raw['id']  # Will raise KeyError if neither exists
```

One test fixture migrated: `tests/state_manager/fixtures/invalid_player_state.json` updated from old `player_state` format to new `actors` dict format.

## Code Path Merger Analysis (Final State)

### Parser Functions

All `_parse_*` functions now follow consistent patterns:

| Function | core_fields | Extracts name? | Extracts description? | Extracts behaviors? |
|----------|-------------|----------------|----------------------|---------------------|
| `_parse_location` | id, name, description, exits, items, npcs, behaviors | Yes | Yes | Yes |
| `_parse_item` | id, name, description, location, behaviors | Yes | Yes | Yes |
| `_parse_exit` | type, to, door_id, name, description, behaviors | Yes | Yes | Yes |
| `_parse_actor` | id, name, description, location, inventory, behaviors | Yes | Yes | Yes |
| `_parse_lock` | id, name, description, behaviors | Yes | Yes | Yes |

**Decision:** Parsers remain separate due to entity-specific logic (nested exits, `actor_id` parameter, etc.).

### Serializer Functions

All `_serialize_*` functions now use the `_serialize_entity()` helper:

| Function | required_fields | optional_fields |
|----------|-----------------|-----------------|
| `_serialize_location` | id, name, description | (handles exits/items specially) |
| `_serialize_item` | id, name, description, location | - |
| `_serialize_exit` | type | to, door_id, name, description |
| `_serialize_actor` | id, name, description, location, inventory | - |
| `_serialize_lock` | id | name, description |

**Decision:** Serializers consolidated into shared helper.

### Examination Code Paths in `perception.py`

`handle_examine()` searches in order:
1. Items → uses `item.llm_context` ✓
2. Doors → uses `door.llm_context` ✓
3. Exits → uses `exit_desc.llm_context` ✓

**Future work:** Lock examination could be added using same pattern now that Lock has `llm_context` accessor.

### LLM Protocol `_*_to_dict` Functions

Functions in `llm_protocol.py` now all have access to `entity.llm_context`:

| Function | Entity Type | llm_context accessible? |
|----------|-------------|------------------------|
| `_entity_to_dict` | Item | Yes ✓ |
| `_door_to_dict` | Door Item | Yes ✓ |
| `_location_to_dict` | Location | Yes ✓ |
| `_actor_to_dict` | Actor | Yes ✓ (newly added) |

**Decision:** Keep separate functions - each entity type needs different extra fields. All use `_add_llm_context` consistently.

### Code Simplified By Consistency

Now that all entities have consistent `llm_context` accessors:
- Test helper functions can use uniform pattern
- Examination code uses consistent `entity.llm_context` access
- LLM protocol functions all use same `_add_llm_context` pattern

**Future opportunity:** An `_examine_result()` helper could further reduce duplication in `perception.py`.

## Results

### What Got Simpler

1. **Examination code** - Can use consistent `entity.description` and `entity.llm_context` patterns
2. **LLM context building** - All entities have `llm_context` accessor
3. **Developer mental model** - "All examinable entities have name, description, llm_context"
4. **Serializers** - All use shared `_serialize_entity()` helper
5. **No backward compat debt** - Clean code without legacy format handling

### What Stayed the Same

1. **Parser functions** - Still entity-specific due to different field sets (by design)
2. **Entity-specific behaviors** - Doors, locks, containers have unique functionality

## Design Decisions (Implemented)

### Lock Has a `name` Field ✓

**Decision:** Yes, Lock has a `name` field.

**Motivation:** A door can have multiple locks. Consider:
- A treasure vault with both a mundane iron lock and a magical ward
- A prison cell with a padlock and a deadbolt
- An ancient door with a rusted lock and a newer replacement

With multiple locks on a single door, players need to distinguish them:
- "examine the iron lock" vs "examine the magical ward"
- "unlock the padlock with the key" vs "pick the deadbolt"

### Lock Has `behaviors` ✓

**Decision:** Yes, Lock has a `behaviors` list.

**Motivation:** Locks can have complex unlock conditions beyond simple key matching:
- A lock that only opens if the key is blessed first
- A lock that requires speaking an incantation while turning the key
- A lock that can be picked with thieves' tools (skill check)
- A lock that triggers a trap if the wrong key is used
- A magical lock that responds to specific spells

The behaviors system already handles conditional logic elegantly. Locks now participate in this system like other entities.

### Lock Parser Bug Fixed ✓

The parser now correctly extracts `name`, `description`, and `behaviors` from JSON to top-level fields.

### Parsers Remain Separate, Serializers Consolidated ✓

**Decision:** Keep parsers separate, consolidate serializers.

**Rationale:** Parsers have entity-specific logic (nested exits in Location, `actor_id` parameter in Actor, different core_fields sets). Serializers all follow same pattern of extracting required/optional fields and merging properties, so a shared helper reduces duplication.

## Test Results

All 961 tests pass after the cleanup.

### Tests Updated

- `tests/state_manager/test_simplified_models.py` - Updated Lock tests for new fields
- `tests/state_manager/fixtures/invalid_player_state.json` - Migrated from old `player_state` format to new `actors` dict format

### Backward Compatibility Removed

Per `.claude/CLAUDE.md`: "do not provide backward compatibility within the code base."

Removed from `_parse_actor()`:
```python
# REMOVED: Handle backward compatibility - old saves may have player_state without id
if 'id' not in raw and actor_id:
    raw = dict(raw)
    raw['id'] = actor_id
```

### Property Accessors Retained

Lock's `opens_with` and `auto_unlock` property accessors remain - they provide convenient access patterns (not backward compatibility).

## Conclusion

All cleanup work completed. The codebase now has:

1. **Consistent entity structure** - All entities (Location, Item, ExitDescriptor, Actor, Lock) have top-level `name`, `description`, `behaviors` with `llm_context` accessible via `@property`

2. **Consolidated serializers** - `_serialize_entity()` helper reduces duplication across all 5 serializers

3. **No backward compatibility debt** - Removed legacy format handling per project policy

4. **961 tests passing** - Full test coverage maintained throughout

### Files Changed

| File | Change |
|------|--------|
| `src/state_manager.py` | Added Lock fields, Actor accessor, `_serialize_entity()` helper, removed backward compat |
| `tests/state_manager/test_simplified_models.py` | Updated Lock tests |
| `tests/state_manager/fixtures/invalid_player_state.json` | Migrated to new format |

### Related Issues

- GitHub Issue #23: Lock as first-class entity - **COMPLETED**
- Comments added documenting serializer consolidation and backward compat removal
