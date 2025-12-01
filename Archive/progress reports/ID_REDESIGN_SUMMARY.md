# ID Namespace Redesign Summary

**Date:** 2025-11-16
**Version:** 2.0
**Status:** In Progress

## Overview

Major redesign of ID namespace strategy from human-readable string IDs to internal unique IDs separate from user-visible names.

## Key Changes

### V1.0 (Previous Design - DEPRECATED)
- IDs were human-readable strings (`"entrance"`, `"stone_chest"`, `"ghost_guard"`)
- Locations stored as object with IDs as keys: `{"entrance": {...}}`
- Locks stored as object with IDs as keys: `{"gate_lock": {...}}`
- Container item IDs could NOT collide with location IDs (namespace constraint)
- Inventory references used special syntax: `"inventory:player"`, `"inventory:<npc_id>"`

### V2.0 (New Design - CURRENT)
- **IDs are internal unique identifiers** separate from names
- **All IDs globally unique** across all entity types
- **Names are user-visible** and can duplicate
- All collections now use arrays: `[{id": "loc_1", "name": "Entrance"}, ...]`
- Simple ID references, no prefixes: just use `"player"` or `"npc_1"`

## Structural Changes

| Entity Type | V1.0 Storage | V2.0 Storage |
|-------------|--------------|--------------|
| Locations | `{"entrance": {...}}` | `[{"id": "loc_1", "name": "Entrance", ...}]` |
| Doors | `[{"id": "iron_gate", ...}]` | `[{"id": "door_1", ...}]` (unchanged structure) |
| Items | `[{"id": "torch", ...}]` | `[{"id": "item_1", "name": "Torch", ...}]` |
| Locks | `{"gate_lock": {...}}` | `[{"id": "lock_1", ...}]` |
| NPCs | `[{"id": "ghost_guard", ...}]` | `[{"id": "npc_1", "name": "Ghostly Guard", ...}]` |
| Scripts | `[{"id": "unlock_gate", ...}]` | `[{"id": "script_1", ...}]` |

## ID Format Examples

**Recommended format:** `<type>_<number>`

```
Locations:  loc_1, loc_2, loc_3, ...
Doors:      door_1, door_2, ...
Items:      item_1, item_2, item_3, ...
Locks:      lock_1, lock_2, ...
NPCs:       npc_1, npc_2, ...
Scripts:    script_1, script_2, ...
Player:     "player" (reserved singleton)
```

Alternative formats also valid:
- Sequential numbers: `1`, `2`, `3`
- UUIDs: `"550e8400-e29b-41d4-a716-446655440000"`
- Custom: any globally unique string

## Reference Changes

### Item Location Field

**V1.0:**
```json
{
  "id": "silver_key",
  "location": "stone_chest"           // Container ID (ambiguous with location ID)
}
{
  "id": "rusty_sword",
  "location": "inventory:player"      // Special prefix syntax
}
```

**V2.0:**
```json
{
  "id": "item_2",
  "name": "Silver Key",
  "location": "item_1"                // Container item ID (globally unique)
}
{
  "id": "item_4",
  "name": "Rusty Sword",
  "location": "player"                // Simple ID, no prefix
}
```

### Exit References

**V1.0:**
```json
{
  "north": {"type": "door", "door_id": "iron_gate"},
  "south": {"type": "open", "to": "courtyard"}
}
```

**V2.0:**
```json
{
  "north": {"type": "door", "door_id": "door_1"},
  "south": {"type": "open", "to": "loc_2"}
}
```

## Validation Changes

### V1.0 Validation Rules
1. IDs unique within collection
2. **Container item IDs ≠ location IDs** (special constraint)
3. Parse inventory prefix syntax
4. Validate NPC in prefix
5. Check all references exist

### V2.0 Validation Rules
1. **All IDs globally unique** (single simple rule)
2. All IDs are non-empty strings
3. Check all references exist in global registry
4. Validate item location points to appropriate entity type

## Benefits

✅ **Simpler validation** - Single global uniqueness check
✅ **No collision concerns** - Global IDs eliminate namespace issues
✅ **Stable references** - IDs don't change when names change
✅ **User-friendly names** - Names can be anything, duplicate freely
✅ **Easier debugging** - Prefixed IDs (`loc_1`, `item_5`) self-document
✅ **Future-proof** - Can use UUIDs for dynamic content

## Migration Path

Authoring tools will need to:
1. Generate unique IDs for all entities
2. Convert location/lock objects to arrays
3. Update all ID references
4. Remove `inventory:` prefixes from item locations

Example migration:
```python
def migrate_v1_to_v2(old_data):
    new_data = {}
    id_counter = {"loc": 1, "item": 1, "door": 1, "lock": 1, "npc": 1}
    id_map = {}  # old_id -> new_id

    # Convert locations object to array
    new_data["locations"] = []
    for old_id, loc_data in old_data["locations"].items():
        new_id = f"loc_{id_counter['loc']}"
        id_counter["loc"] += 1
        id_map[old_id] = new_id
        new_data["locations"].append({
            "id": new_id,
            **loc_data
        })

    # Similar for other collections...
    # Then update all references using id_map

    return new_data
```

## Files Modified

- ✅ [ID_NAMESPACE_DESIGN.md](ID_NAMESPACE_DESIGN.md) - Complete rewrite (v2.0)
- ✅ [game_state_spec.md](game_state_spec.md) - Updated to array format, global IDs
- ✅ [game_state_example.md](game_state_example.md) - Converted to v2.0 format with internal IDs
- ✅ [state_manager_plan.md](state_manager_plan.md) - Added ID generation strategy and global registry validation
- ✅ [state_manager_API.md](state_manager_API.md) - Updated API to use arrays, added ID lookup helpers
- ✅ [state_manager_testing.md](state_manager_testing.md) - Updated test cases for global ID validation

## Implementation Notes

**ID Generation:**
```python
# Sequential prefixed (recommended)
def generate_id(entity_type):
    global counters
    counters[entity_type] += 1
    return f"{entity_type}_{counters[entity_type]}"

# UUID-based (for dynamic entities)
import uuid
def generate_unique_id(entity_type):
    return f"{entity_type}_{uuid.uuid4().hex[:8]}"
```

**Global ID Registry:**
```python
def build_id_registry(game_state):
    registry = {"player": "player"}
    for loc in game_state.locations:
        assert loc.id not in registry, f"Duplicate ID: {loc.id}"
        registry[loc.id] = "location"
    # ... same for all other collections
    return registry
```

**Reference Validation:**
```python
def validate_references(game_state, registry):
    # Check all exit.to references
    for loc in game_state.locations:
        for direction, exit in loc.exits.items():
            if exit.to and exit.to not in registry:
                raise ValidationError(f"Exit to unknown location: {exit.to}")
    # ... validate all other reference types
```

---

**Impact:** This is a **breaking change** requiring migration of all existing game state JSON files.

**Timeline:**
1. ✅ Design approved (2025-11-16)
2. ✅ Documentation updates complete (2025-11-16)
3. ⏳ Implementation pending
4. ⏳ Migration tool needed
