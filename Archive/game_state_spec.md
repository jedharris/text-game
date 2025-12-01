# Game State Format Specification

This document defines the canonical JSON structure used to describe a text
adventure game's static data (locations, items, doors, locks, NPCs, etc.) and
its mutable state (who holds what, which doors are locked, etc.). It is intended
to be consumed by the parser/game engine and by tools that author or validate
content.

## Top-Level Layout

Every game definition is a single JSON object containing the sections below. All
top-level keys are optional unless marked **required**, though a functional game
will typically provide each section.

| Key | Type | Required | Purpose |
|-----|------|----------|---------|
| `metadata` | object | yes | Identifies the world (title, version, etc.). |
| `vocabulary` | object | no | Optional canonical noun/alias map for parser alignment. |
| `locations` | array | yes | Rooms/areas, each with unique internal ID. |
| `doors` | array | no | Shared door records for bidirectional passages. |
| `items` | array | no | Portable objects, scenery, and containers. |
| `locks` | array | no | Reusable lock definitions (key requirements, clues). |
| `npcs` | array | no | Non-player characters/creatures. |
| `scripts` | array | no | Optional declarative hooks for puzzles or events. |
| `player_state` | object | no | Initial player state (location, inventory, flags). Optional; defaults created if missing. |

**Important:** All entities use internal unique IDs (`id` field) separate from their user-visible `name` fields. IDs must be globally unique across all entity types. See [ID_NAMESPACE_DESIGN.md](ID_NAMESPACE_DESIGN.md) for details.

Consumers should preserve unknown keys to allow future extensions.

## Metadata

```json
"metadata": {
  "title": "Crypt of Winds",
  "author": "Jane Doe",
  "version": "1.1.0",
  "start_location": "entrance",
  "description": "Optional world overview."
}
```

* `title` **required** string.
* `author` optional string.
* `version` optional semantic version string.
* `start_location` **required** string referencing a location id.
* `description` optional long-form text.

## Vocabulary (Optional)

Ensures descriptive text stays aligned with parser-recognized nouns/directions.

```json
"vocabulary": {
  "aliases": {
    "silver_key": ["silver key", "iron key", "key"],
    "north": ["n"]
  }
}
```

* `aliases`: map of canonical ids -> array of synonyms.
* Additional fields (e.g., `stop_words`, `articles`) may be added for tooling.

## Locations

`locations` is an array of location objects, each with a unique `id`:

```json
"locations": [
  {
    "id": "loc_1",
    "name": "Crypt Entrance",
    "description": "A marble archway opens into darkness...",
    "tags": ["outdoors", "windy"],
    "items": ["item_3"],
    "npcs": [],
    "exits": {
      "north": { "type": "door", "door_id": "door_1" },
      "south": { "type": "open", "to": "loc_2" }
    }
  }
]
```

Fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | **Internal unique ID** (not shown to player). Must be globally unique. |
| `name` | string | yes | Player-facing location name (shown in game). |
| `description` | string | yes | Default description (LLM may augment). |
| `tags` | array of string | no | For ambiance/scripting filters. |
| `items` | array of item ids | no | Items currently located here (references item `id` fields). |
| `npcs` | array of npc ids | no | NPCs initially present (references npc `id` fields). |
| `exits` | object | yes | Map direction → exit descriptor. |

Exit descriptor schema:

```json
{
  "type": "door" | "open" | "portal" | "scripted",
  "to": "location_id",
  "door_id": "iron_gate",
  "description": "A shadowy corridor slopes downward.",
  "hidden": false,
  "conditions": ["lit_torch"],
  "on_fail": "You bump into a wall."
}
```

* `type` **required** enumerated string (see Exit Types below).
* `to` required unless `type` references a `door`.
* `door_id` required when type is `door` (shared door entry).
* `hidden` optional boolean; engine may conceal exit until revealed.
* `conditions` optional array of state flags required to use the exit.
* `on_fail` optional message when conditions unmet.

### Exit Types

Four exit types are supported:

* **`"open"`** - Simple, always-accessible passage. Requires `to` field pointing to destination location. Use for hallways, archways, and unconditional connections.

* **`"door"`** - Passage controlled by a shared door object (may be locked/unlocked, open/closed). Requires `door_id` field referencing a door entry. The door entry specifies which locations it connects. Use when passage state must be shared between locations.

* **`"portal"`** - One-way magical/technological transport (teleporter, slide, trapdoor). Requires `to` field. Unlike "open", implies non-obvious or non-reversible travel. Use for dramatic transitions or when return path differs.

* **`"scripted"`** - Exit whose behavior is determined by game scripts/logic. May require `conditions` or trigger script effects. Use for puzzle-dependent passages or story-gated areas.

## Doors

Use shared `doors` entries when an exit's state is shared between two (or more)
locations (e.g., locked door). Each door record is authoritative for lock/open
state.

```json
"doors": [
  {
    "id": "iron_gate",
    "locations": ["entrance", "antechamber"],
    "description": "An ornate iron gate patterned with ravens.",
    "locked": true,
    "lock_id": "gate_lock",
    "open": false,
    "one_way": false
  }
]
```

Fields:

* `id` **required** unique string.
* `locations` **required** array of one or two location ids.
* `description` optional string; used when examining the door.
* `locked` boolean (default false).
* `lock_id` string referencing `locks` entry, if locked.
* `open` boolean (default false).
* `one_way` boolean for trapdoors, slides, etc.
* `requires_item` optional item id needed even when unlocked (e.g., handle).

## Items

An `items` array describes everything the player can interact with:

```json
"items": [
  {
    "id": "torch",
    "name": "Unlit Torch",
    "description": "Wrapped in old linens, still usable.",
    "type": "tool",
    "portable": true,
    "location": "entrance",
    "states": { "lit": false }
  },
  {
    "id": "stone_chest",
    "name": "Stone Chest",
    "description": "Heavy lid carved with spiral motifs.",
    "type": "container",
    "portable": false,
    "location": "antechamber",
    "container": {
      "locked": true,
      "lock_id": "chest_lock",
      "capacity": 5,
      "contents": ["silver_key"]
    }
  }
]
```

Common fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Unique item id. |
| `name` | string | yes | Display name. |
| `description` | string | yes | Examination text. |
| `type` | enum | yes | e.g., `tool`, `key`, `container`, `weapon`, `scenery`. |
| `portable` | boolean | yes | Whether player can pick it up. |
| `location` | string | yes | Location id, container item id, or inventory reference (see below). |
| `states` | object | no | Arbitrary boolean/number flags for gameplay. |

**Item Location Field Format:**

The `location` field contains an entity ID indicating where the item is:

1. **Location ID** (string): e.g., `"loc_1"` - item is in that location
2. **Container Item ID** (string): e.g., `"item_5"` - item is inside that container item
3. **Player inventory** (string): `"player"` - item is held by the player
4. **NPC inventory** (string): e.g., `"npc_3"` - item is held by that NPC

All IDs are globally unique, so no prefixes are needed. Validation ensures the referenced entity exists and is an appropriate type.

Container-specific `container` sub-object:

* `locked` boolean (default false).
* `lock_id` string referencing `locks`.
* `contents` array of item ids; items listed should have `location` equal to the
  container id.
* `capacity` optional number for encumbrance systems (advisory only, not enforced by state manager).

Weapon/tool specific fields (optional): `damage`, `uses`, `effects`.

## Locks

Locks encapsulate unlocking logic and narrative messaging. Referenced by
`doors.lock_id` or `container.lock_id`.

```json
"locks": [
  {
    "id": "lock_1",
    "opens_with": ["item_2"],
    "auto_unlock": false,
    "description": "Shaped like a raven.",
    "fail_message": "The key does not fit."
  },
  {
    "id": "lock_2",
    "opens_with": ["spell:dispel_magic"],
    "auto_unlock": true,
    "description": "Runes glow faintly."
  }
]
```

Fields:

* `id` **required** string - Internal unique ID (globally unique).
* `opens_with` **required** array of requirements (item ids, skills, scripted flags).
* `auto_unlock` boolean: if true, lock disengages automatically when
  requirements met; otherwise requires explicit action.
* `description` optional.
* `fail_message` optional custom rejection text.

## NPCs

```json
"npcs": [
  {
    "id": "ghost_guard",
    "name": "Ghostly Guard",
    "description": "Translucent armor-clad figure watching silently.",
    "location": "antechamber",
    "dialogue": ["Turn back...", "Seek the raven's blessing."],
    "states": { "hostile": false }
  }
]
```

Fields:

* `id`, `name`, `description` **required**.
* `location` location id where NPC is **currently** located (mutable runtime state).
* `dialogue` array of stock lines or map of state→text.
* `states` object for custom flags (loyalty, hostility, etc.).

**NPC Location Tracking:** The `location` field represents the NPC's current location and may be updated at runtime as NPCs move. The location's `npcs` array should remain synchronized with NPC location fields, though the authoritative source is the `npc.location` field itself.

## Scripts / Events (Optional)

The `scripts` array enables declarative triggers without hardcoding behavior.
Each entry may have:

```json
{
  "id": "open_gate_after_guard_defeated",
  "trigger": { "type": "state", "flag": "guard_defeated" },
  "effect": [
    { "action": "set_door", "door_id": "iron_gate", "open": true, "locked": false },
    { "action": "message", "text": "The distant gate clanks open." }
  ]
}
```

Trigger types: `state`, `item_used`, `enter_location`, etc. Effects: mutations to
doors/items/npc states or narrative messages. Implementations may extend this
schema or ignore it entirely.

## Player State

The optional `player_state` section defines the initial player state. If omitted, the state manager will create defaults based on `metadata.start_location`.

```json
"player_state": {
  "location": "entrance",
  "inventory": ["rusty_sword", "health_potion"],
  "flags": {
    "knows_guard_name": true,
    "completed_tutorial": false
  },
  "stats": {
    "health": 100,
    "max_health": 100,
    "strength": 10
  }
}
```

Fields:

* `location` **required** string - current location id (must reference valid location). If `player_state` section is omitted, initialized to `metadata.start_location`.
* `inventory` optional array of item ids currently held by player. Each item listed must exist in `items` and have `location: "inventory:player"`.
* `flags` optional object mapping flag names to arbitrary values (boolean, number, string). Used for quest progress, story branches, puzzle state, etc.
* `stats` optional object for numeric gameplay values (health, mana, attributes). Structure is game-specific.

**Runtime Mutability:** All fields in `PlayerState` are mutable and represent live game state. Changes to player location, inventory, flags, and stats should be persisted when saving games.

## Serialization Format

When serializing game state to JSON (for authoring tools or save games), the following format conventions must be followed:

* **Indentation:** 2 spaces per level
* **Key Ordering:** Keys within objects should be sorted alphabetically for stable diffs
* **Line Endings:** LF (Unix-style `\n`)
* **Trailing Newline:** Yes, files should end with a newline character
* **Unknown Keys:** Preserve any unknown/extra keys for forward compatibility
* **Float Precision:** Use default JSON float precision (no artificial rounding)
* **Array Formatting:** Each array element on its own line when pretty-printing (except for small primitive arrays like `["north", "south"]` which may be inline)

Example serializer invocation:
```python
json.dumps(game_state_dict, indent=2, sort_keys=True, ensure_ascii=False)
```

These conventions ensure:
- Version control-friendly diffs (sorted keys, stable formatting)
- Cross-platform compatibility (LF line endings)
- Human readability (indentation, trailing newline)
- Tool interoperability (preserve unknown keys)

## Validation Rules

1. **Global ID Uniqueness:** All entity IDs must be globally unique across all collections (locations, items, doors, locks, npcs, scripts). The ID `"player"` is reserved for the player singleton.

2. **ID Format:** All IDs must be non-empty strings. Recommended format: `<type>_<number>` (e.g., `"loc_1"`, `"item_42"`).

3. **Reference Validation:** All references must point to existing entities:
   - `metadata.start_location` must reference valid location id
   - Exit `to` must reference valid location id
   - Exit `door_id` must reference valid door id
   - Door `lock_id` must reference valid lock id
   - Door `locations` must reference valid location ids
   - Lock `opens_with` item ids must reference valid item ids
   - Item `location` must be one of: valid location id, valid container item id, `"player"`, or valid npc id
   - Container `contents` must reference valid item ids
   - Location `items` must reference valid item ids
   - Location `npcs` must reference valid npc ids
   - NPC `location` must reference valid location id
   - Script trigger/effect references must point to valid entities
   - PlayerState `location` must reference valid location id
   - PlayerState `inventory` must reference valid item ids

4. **Item Location Consistency:** Items listed in `location.items` must have matching `location` field pointing to that location id. Items in container `contents` must have `location` field pointing to that container's id. Items in `player_state.inventory` must have `location: "player"`.

5. **Container Cycle Prevention:** Containers cannot contain themselves (directly or through chain of containment).

6. **Exit Completeness:** Exits must specify either `to` (for open/portal/scripted) or `door_id` (for door type), never both, neither.

7. **Lock Format:** Lock `opens_with` must be an array (even for single item requirement).

Tooling may generate additional warnings (e.g., orphaned items, unreachable locations, unused locks) but the rules above are the minimum validation contract.

## Relation to Example

`docs/example_game_state` provides a concrete instance conforming to this spec.
Use it as a template when authoring new worlds, and extend the schema carefully
to maintain backward compatibility.
