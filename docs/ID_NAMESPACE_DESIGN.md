# ID Namespace Design

**Version:** 2.0
**Date:** 2025-11-16
**Status:** Final

## Overview

This document defines the ID namespace strategy for game state entities using **internal unique IDs** separate from user-visible names. This eliminates namespace collision issues and simplifies reference validation.

## Design Philosophy

**Key Principle:** Every entity has two identifiers:
1. **Internal ID** - Unique numeric or string ID used for references (NOT visible to player)
2. **Name** - User-visible name for display and interaction (can duplicate across entity types)

This separation provides:
- No namespace collisions (all internal IDs are globally unique)
- Simple reference validation (just check ID exists)
- User-friendly names without constraints
- Easy serialization and debugging (IDs are stable, names can change)

## Entity Types and IDs

All entities now use internal unique IDs:

| Entity Type | Collection Key | ID Field | Name Field | ID Format | Storage Format |
|-------------|---------------|----------|------------|-----------|----------------|
| Location | `locations` | `id` | `name` | `"loc_001"` | `[{"id": "loc_001", "name": "Crypt Entrance", ...}]` |
| Door | `doors` | `id` | `description` | `"door_001"` | `[{"id": "door_001", "description": "Iron gate", ...}]` |
| Item | `items` | `id` | `name` | `"item_001"` | `[{"id": "item_001", "name": "Torch", ...}]` |
| Lock | `locks` | `id` | `description` | `"lock_001"` | `[{"id": "lock_001", "description": "Raven lock", ...}]` |
| NPC | `npcs` | `id` | `name` | `"npc_001"` | `[{"id": "npc_001", "name": "Ghostly Guard", ...}]` |
| Script | `scripts` | `id` | (none) | `"script_001"` | `[{"id": "script_001", ...}]` |
| Player | (special) | (implicit) | (none) | `"player"` | Referenced as `"player"` (singleton) |

**ID Format Options:**
1. **Sequential numbers:** `1`, `2`, `3`, ... (simple, compact)
2. **Prefixed numbers:** `"loc_1"`, `"item_42"`, ... (readable in debugging)
3. **UUIDs:** `"550e8400-..."` (universally unique, but verbose)

**Recommendation:** Use prefixed sequential integers (`"loc_1"`, `"item_1"`, etc.) for human-readable debugging while maintaining uniqueness.

## Namespace Strategy

### Global Unique ID Space

**All internal IDs are globally unique** across all entity types. This eliminates all collision concerns.

```
Global ID Registry:
- loc_1, loc_2, loc_3, ...
- door_1, door_2, ...
- item_1, item_2, item_3, ...
- lock_1, lock_2, ...
- npc_1, npc_2, ...
- script_1, script_2, ...
- player (singleton)
```

**Benefits:**
- No namespace collisions possible
- Simple reference validation (check if ID exists anywhere)
- IDs can be assigned sequentially as entities are created
- No special cases or constraints

**ID Generation:**
- Authoring tools assign IDs sequentially: `"loc_1"`, `"loc_2"`, etc.
- State manager validates all IDs are unique globally
- IDs are immutable (changing ID breaks all references)
- Names can change freely without affecting references

### Validation Rules

#### Global Uniqueness

1. **All IDs must be globally unique** - No two entities can share the same ID, regardless of type
   - Collect all IDs from all collections: locations, doors, items, locks, npcs, scripts
   - Verify no duplicates exist in this global set
   - `"player"` is reserved for the player singleton

#### ID Format

2. **IDs must be non-empty strings** - No empty string, null, or non-string values
3. **IDs should follow convention** - Recommended format: `<type>_<number>` (e.g., `"loc_1"`, `"item_42"`)
   - This is not enforced but helps debugging
   - Alternative formats (numeric, UUID) are valid if unique

#### Reference Format

4. **Item location field** - Can contain:
   - Location ID: `"loc_1"` (item is in that location)
   - Container item ID: `"item_5"` (item is inside that container)
   - Player inventory: `"player"` (item is held by player)
   - NPC inventory: `<npc_id>` (item is held by that NPC, e.g., `"npc_3"`)

5. **No special prefixes needed** - Unlike v1.0, we don't need `"inventory:player"` prefix
   - Just use the entity ID directly: `"player"` or `"npc_1"`
   - This works because all IDs are globally unique

## Reference Validation Matrix

This table shows which fields reference which entity types:

| Source Field | Valid Target Type(s) | Validation Rule |
|--------------|---------------------|-----------------|
| `metadata.start_location` | Location | ID must exist in `locations` array |
| `exit.to` | Location | ID must exist in `locations` array |
| `exit.door_id` | Door | ID must exist in `doors` array |
| `door.locations[]` | Location | Each ID must exist in `locations` array |
| `door.lock_id` | Lock | ID must exist in `locks` array |
| `lock.opens_with[]` | Item | Each ID must exist in `items` array |
| `item.location` | Location, Item (container), or special `"player"` | See item location validation below |
| `container.contents[]` | Item | Each ID must exist in `items` array |
| `location.items[]` | Item | Each ID must exist in `items` array |
| `location.npcs[]` | NPC | Each ID must exist in `npcs` array |
| `npc.location` | Location | ID must exist in `locations` array |
| `player_state.location` | Location | ID must exist in `locations` array |
| `player_state.inventory[]` | Item | Each ID must exist in `items` array |
| `script` trigger/effects | Various | Entity IDs must exist in respective collections |

### Item Location Validation

The `item.location` field requires special validation since it can reference different entity types:

```python
def validate_item_location(item, all_entities):
    """
    Validate item.location field.
    all_entities: dict mapping all IDs to their entity type
    """
    location_id = item.location

    # Check if ID exists globally
    if location_id not in all_entities:
        raise ValidationError(
            f"Item {item.id} has unknown location '{location_id}'"
        )

    entity_type = all_entities[location_id]

    # Validate appropriate entity type
    if entity_type == "location":
        return True  # Item is in a location
    elif entity_type == "item":
        # Verify it's a container
        container = get_item_by_id(location_id)
        if not container.container:
            raise ValidationError(
                f"Item {item.id} location {location_id} is not a container"
            )
        return True
    elif entity_type == "player":
        return True  # Item is in player inventory
    elif entity_type == "npc":
        return True  # Item is in NPC inventory
    else:
        raise ValidationError(
            f"Item {item.id} location {location_id} has invalid type {entity_type}"
        )
```

## Global ID Registry

The state manager must maintain a global ID registry during validation:

```python
def build_global_id_registry(game_state):
    """Build a registry of all IDs and their entity types."""
    registry = {"player": "player"}  # Reserved ID

    for location in game_state.locations:
        if location.id in registry:
            raise ValidationError(f"Duplicate ID: {location.id}")
        registry[location.id] = "location"

    for door in game_state.doors:
        if door.id in registry:
            raise ValidationError(f"Duplicate ID: {door.id}")
        registry[door.id] = "door"

    for item in game_state.items:
        if item.id in registry:
            raise ValidationError(f"Duplicate ID: {item.id}")
        registry[item.id] = "item"

    for lock in game_state.locks:
        if lock.id in registry:
            raise ValidationError(f"Duplicate ID: {lock.id}")
        registry[lock.id] = "lock"

    for npc in game_state.npcs:
        if npc.id in registry:
            raise ValidationError(f"Duplicate ID: {npc.id}")
        registry[npc.id] = "npc"

    for script in game_state.scripts:
        if script.id in registry:
            raise ValidationError(f"Duplicate ID: {script.id}")
        registry[script.id] = "script"

    return registry
```

This registry is then used for all reference validation.

## Examples

### Valid Configuration (New Design)

```json
{
  "locations": [
    {"id": "loc_1", "name": "Crypt Entrance", ...},
    {"id": "loc_2", "name": "Treasury", ...}
  ],
  "items": [
    {
      "id": "item_1",
      "name": "Stone Chest",
      "type": "container",
      "location": "loc_1",
      "container": {"contents": ["item_2"]}
    },
    {
      "id": "item_2",
      "name": "Silver Key",
      "type": "key",
      "location": "item_1"
    },
    {
      "id": "item_3",
      "name": "Gold Coins",
      "type": "treasure",
      "location": "loc_2"
    },
    {
      "id": "item_4",
      "name": "Rusty Sword",
      "type": "weapon",
      "location": "player"
    },
    {
      "id": "item_5",
      "name": "Mysterious Amulet",
      "type": "jewelry",
      "location": "npc_1"
    }
  ],
  "npcs": [
    {"id": "npc_1", "name": "Ghostly Guard", "location": "loc_1"}
  ]
}
```

**Valid because:**
- All IDs are globally unique: `loc_1`, `loc_2`, `item_1`-`item_5`, `npc_1`, `player`
- Names can duplicate (e.g., could have two "Sword" items with different IDs)
- Item locations reference valid IDs:
  - `"loc_1"` and `"loc_2"` are valid location IDs
  - `"item_1"` is a valid container item ID
  - `"player"` is the reserved player ID
  - `"npc_1"` is a valid NPC ID

### Invalid Configuration (ID Collision)

```json
{
  "locations": [
    {"id": "loc_1", "name": "Entrance"},
    {"id": "loc_2", "name": "Vault"}
  ],
  "items": [
    {"id": "loc_1", "name": "Ancient Tome", "location": "loc_2"}
  ]
}
```

**Invalid because:**
- Item has ID `"loc_1"` which collides with location ID `"loc_1"`
- Global uniqueness violated

### Invalid Configuration (Missing Reference)

```json
{
  "locations": [
    {"id": "loc_1", "name": "Entrance"}
  ],
  "items": [
    {
      "id": "item_1",
      "name": "Cursed Ring",
      "location": "npc_99"
    }
  ],
  "npcs": []
}
```

**Invalid because:**
- Item references NPC `"npc_99"` in location field
- But NPC with ID `"npc_99"` doesn't exist

## Summary of Requirements

1. ✅ **Global uniqueness:** All IDs globally unique across all entity types
2. ✅ **Simple references:** Just use IDs directly - no prefixes needed
3. ✅ **Reserved ID:** `"player"` is reserved for player singleton
4. ✅ **All references validated:** Every ID reference must point to existing entity
5. ✅ **Name flexibility:** Names can duplicate, change freely without breaking references

## Key Advantages Over V1.0

**Problems solved:**
- ❌ No more namespace collision concerns between locations and containers
- ❌ No more special prefix syntax (`"inventory:player"` → just `"player"`)
- ❌ No more complex validation rules for specific entity type pairs
- ❌ No more naming conventions required to avoid collisions

**Benefits gained:**
- ✅ Single global ID validation (much simpler)
- ✅ IDs are implementation detail (not exposed to players)
- ✅ Easy to generate sequentially or with UUIDs
- ✅ Stable references even when names change
- ✅ Simpler validation code

## Implementation Checklist

When implementing the state manager validator:

- [ ] Build global ID registry from all collections
- [ ] Check all IDs are globally unique (including reserved `"player"`)
- [ ] Validate all cross-references exist in registry
- [ ] Provide clear error messages with both ID and entity type
- [ ] Ensure IDs are never exposed to player (use names instead)

## ID Generation Strategy

**For authoring tools:**
```python
def generate_id(entity_type, counter):
    """Generate sequential prefixed ID."""
    return f"{entity_type}_{counter}"

# Usage:
location_id = generate_id("loc", 1)  # "loc_1"
item_id = generate_id("item", 42)    # "item_42"
```

**For runtime/dynamic entities:**
```python
import uuid

def generate_unique_id(entity_type):
    """Generate UUID-based ID."""
    return f"{entity_type}_{uuid.uuid4().hex[:8]}"

# Usage:
dynamic_item = generate_unique_id("item")  # "item_a3f5b8c2"
```

---

**Related Documents:**
- [game_state_spec.md](game_state_spec.md) - Full schema specification
- [state_manager_plan.md](state_manager_plan.md) - Implementation plan
- [state_manager_testing.md](state_manager_testing.md) - Test plan

**Version History:**
- V1.0 (2025-11-16): Namespace collision avoidance with prefixed inventory references
- V2.0 (2025-11-16): Global unique IDs with no collision concerns
