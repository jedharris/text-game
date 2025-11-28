# Game State JSON Format Specification - v_0.01

This document specifies schema version `v_0.01` for game state JSON files.

## Schema Version

The schema version is stored in metadata:

```json
{
  "metadata": {
    "schema_version": "v_0.01",
    ...
  }
}
```

Files without a `schema_version` field are considered "pre-versioned" and should be migrated to v_0.01.

## Overview

The game state file is a JSON object with the following top-level keys:
- `metadata` - Game information
- `locations` - Array of location objects
- `items` - Array of item objects (including doors)
- `locks` - Array of lock objects
- `actors` - Dict of actor objects (keyed by actor ID)

## Metadata

```json
{
  "metadata": {
    "title": "string (required)",
    "version": "string",
    "description": "string",
    "start_location": "string (location ID)",
    "author": "string"
  }
}
```

## Locations

Locations are stored as an array. Each location has:

```json
{
  "id": "loc_example (required)",
  "name": "Room Name (required)",
  "description": "Full prose description (required)",
  "exits": { ... },
  "items": ["item_id1", "item_id2"],
  "tags": [],
  "llm_context": { ... },
  "behaviors": ["module.path"]
}
```

### Exit Descriptors

Exits are a dict keyed by direction. Each exit has:

```json
{
  "north": {
    "type": "open | door (required)",
    "to": "destination_location_id",
    "door_id": "door_item_id (for type: door)",
    "name": "descriptive name (e.g., 'spiral staircase')",
    "description": "Prose description for examine",
    "llm_context": {
      "traits": ["trait1", "trait2"],
      "atmosphere": "string",
      "state_variants": { ... }
    }
  }
}
```

**Key points:**
- `type` is required: `"open"` for passages, `"door"` for doors
- `door_id` references an item with `door` property
- `name` and `description` are optional but recommended for rich narration
- `llm_context` is stored inside the exit descriptor (not in a separate `properties` dict)

### Location llm_context

```json
{
  "llm_context": {
    "traits": ["list", "of", "descriptive", "traits"],
    "atmosphere": "comma-separated mood descriptors",
    "state_variants": {
      "first_visit": "narration text",
      "revisit": "narration text",
      "custom_state": "narration text"
    }
  }
}
```

## Items

Items are stored as an array. Items include regular objects, containers, and doors.

### Regular Item

```json
{
  "id": "item_example (required)",
  "name": "item name (required)",
  "description": "prose description (required)",
  "location": "loc_id | actor_id | container_id | exit:loc_id:direction",
  "properties": {
    "type": "object | furniture",
    "portable": true | false
  },
  "llm_context": {
    "traits": ["trait1", "trait2"],
    "state_variants": { ... }
  },
  "behaviors": ["module.path"]
}
```

**Location values:**
- `"loc_room"` - In a room
- `"player"` or `"npc_id"` - In an actor's inventory
- `"item_container"` - Inside a container item
- `"exit:loc_id:direction"` - A door attached to an exit

### Container Item

```json
{
  "id": "item_chest",
  "name": "chest",
  "description": "A wooden chest.",
  "location": "loc_room",
  "properties": {
    "type": "furniture",
    "portable": false,
    "container": {
      "is_container": true,
      "is_surface": true | false,
      "capacity": 5,
      "open": false,
      "locked": false,
      "lock_id": "lock_id (optional)"
    }
  },
  "llm_context": { ... }
}
```

**Container properties:**
- `is_container`: Must be `true` for containers
- `is_surface`: `true` for surfaces (tables, pedestals), `false` for enclosed containers
- `capacity`: Maximum items (0 for unlimited)
- `open`: Current open/closed state (only for enclosed containers)
- `locked`: Whether container requires unlocking
- `lock_id`: References a lock in the `locks` array

### Door Item

Doors are items with a `door` property:

```json
{
  "id": "door_wooden",
  "name": "door",
  "description": "A simple wooden door.",
  "location": "exit:loc_start:north",
  "door": {
    "open": true | false,
    "locked": true | false,
    "lock_id": "lock_treasure (optional)"
  },
  "llm_context": {
    "traits": ["rough-hewn planks", "iron hinges"],
    "state_variants": {
      "open": "stands ajar",
      "closed": "blocks the way",
      "locked": "sealed tight"
    }
  }
}
```

**Key points:**
- `location` format: `"exit:location_id:direction"` - This is the canonical location for doors
- `door` is at the top level (NOT inside `properties`)
- The exit descriptor references this door via `door_id`

### Light Source Item

```json
{
  "id": "item_lantern",
  "name": "lantern",
  "description": "A small lantern.",
  "location": "loc_room",
  "properties": {
    "type": "object",
    "portable": true,
    "provides_light": true,
    "states": {
      "lit": false
    }
  },
  "llm_context": { ... },
  "behaviors": ["behaviors.core.light_sources"]
}
```

### Hidden Item

```json
{
  "id": "item_hidden_gem",
  "name": "gem",
  "description": "A magnificent ruby.",
  "location": "loc_room",
  "properties": {
    "type": "object",
    "portable": true,
    "states": {
      "hidden": true
    }
  },
  "llm_context": { ... }
}
```

## Locks

Locks are stored as an array:

```json
{
  "id": "lock_treasure (required)",
  "name": "iron lock (optional)",
  "description": "A sturdy lock. (optional)",
  "properties": {
    "opens_with": ["item_key1", "item_key2"],
    "auto_unlock": true | false
  },
  "llm_context": {
    "traits": ["heavy iron", "complex tumblers"],
    "state_variants": {
      "locked": "clicks firmly",
      "unlocked": "mechanism disengaged"
    }
  },
  "behaviors": []
}
```

**Key points:**
- `opens_with` is inside `properties` (not at top level)
- `auto_unlock`: If true, having the key automatically unlocks when opening the door

## Actors

Actors (player and NPCs) are stored as a dict keyed by ID:

```json
{
  "actors": {
    "player": {
      "id": "player",
      "name": "player",
      "description": "",
      "location": "loc_start",
      "inventory": ["item_sword"],
      "flags": {},
      "stats": {}
    },
    "npc_guard": {
      "id": "npc_guard",
      "name": "Guard",
      "description": "A stern guard.",
      "location": "loc_hallway",
      "inventory": [],
      "llm_context": {
        "traits": ["vigilant", "armored"]
      }
    }
  }
}
```

**Key points:**
- `actors` is a dict (not an array) with IDs as keys
- The player always has id `"player"`
- `flags` and `stats` are top-level (for backward compatibility) but internally stored in `properties`

## llm_context Structure

The `llm_context` field provides information to the LLM narrator:

```json
{
  "llm_context": {
    "traits": [
      "short descriptive phrases",
      "sensory details",
      "mood-setting elements"
    ],
    "atmosphere": "comma-separated mood words",
    "state_variants": {
      "state_name": "narration text for this state"
    }
  }
}
```

**Guidelines:**
- `traits`: Array of 3-25 short phrases describing the entity
- `atmosphere`: Brief mood descriptors (optional)
- `state_variants`: Context-sensitive narration hints (optional)

## Properties vs Top-Level Fields

The current format uses a hybrid approach for backward compatibility:

1. **Core fields** are always at top level: `id`, `name`, `description`, `location`, etc.
2. **Properties** can be either:
   - Inside an explicit `"properties": {}` dict
   - At the top level (for backward compatibility)

When loading, top-level non-core fields are merged into properties. When saving, properties are serialized at top level (merged with core fields).

**Exception: `door` for door items** - This is at top level, NOT inside properties.

## Format Differences: fancy_game_state.json

The `fancy_game_state.json` file has the following differences from the current format:

### 1. Missing Exit Descriptive Fields

**Old format (fancy_game_state.json):**
```json
"exits": {
  "north": {
    "type": "door",
    "to": "loc_hallway",
    "door_id": "door_wooden"
  }
}
```

**Current format (simple_game_state.json):**
```json
"exits": {
  "north": {
    "type": "door",
    "to": "loc_hallway",
    "door_id": "door_wooden",
    "name": "wooden doorway",
    "description": "A simple wooden doorway leads north...",
    "llm_context": { ... }
  }
}
```

**Migration:** Add `name`, `description`, and optionally `llm_context` to exit descriptors.

### 2. Location llm_context at Top Level (Same - No Change Needed)

Both formats have `llm_context` at the location top level. No migration needed.

### 3. Item llm_context at Top Level (Same - No Change Needed)

Both formats have `llm_context` at the item top level. No migration needed.

### 4. Door Properties Location (Same - No Change Needed)

Both formats have `door` at the item top level. No migration needed.

### 5. Lock llm_context at Top Level (Same - No Change Needed)

Both formats have `llm_context` at the lock top level. No migration needed.

## Migration Checklist: fancy_game_state.json → Current Format

1. **Exit descriptors**: Add `name` and `description` fields to each exit
2. **Exit llm_context**: Optionally add `llm_context` with traits to exits (especially stairs, archways, etc.)
3. **No structural changes needed** for:
   - Locations
   - Items (including doors)
   - Locks
   - Actors

## Example Migration

**Before (fancy_game_state.json):**
```json
"up": {
  "type": "open",
  "to": "loc_tower"
}
```

**After (migrated):**
```json
"up": {
  "type": "open",
  "to": "loc_tower",
  "name": "spiral staircase",
  "description": "A narrow spiral staircase carved from living rock winds upward into shadow.",
  "llm_context": {
    "traits": [
      "spiral staircase carved from living rock",
      "worn treads polished by centuries of footsteps",
      "narrow passage barely wide enough for one"
    ],
    "atmosphere": "vertical, ancient, slightly vertiginous"
  }
}
```

## Migration from Pre-Versioned Format

Files without `schema_version` in metadata need the following migration to become v_0.01:

1. **Add schema_version**: Set `metadata.schema_version` to `"v_0.01"`

No structural changes are required - the pre-versioned format is structurally identical to v_0.01. The migration simply adds the version marker.
