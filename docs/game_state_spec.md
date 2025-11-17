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
| `locations` | object | yes | Rooms/areas keyed by unique id. |
| `doors` | array | no | Shared door records for bidirectional passages. |
| `items` | array | no | Portable objects, scenery, and containers. |
| `locks` | object | no | Reusable lock definitions (key requirements, clues). |
| `npcs` | array | no | Non-player characters/creatures. |
| `scripts` | array | no | Optional declarative hooks for puzzles or events. |

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

`locations` is an object keyed by unique location ids:

```json
"locations": {
  "entrance": {
    "name": "Crypt Entrance",
    "description": "A marble archway opens into darkness...",
    "tags": ["outdoors", "windy"],
    "items": ["torch"],
    "npcs": [],
    "exits": {
      "north": { "type": "door", "door_id": "iron_gate" },
      "south": { "type": "open", "to": "courtyard" }
    }
  }
}
```

Fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | yes | Player-facing location name. |
| `description` | string | yes | Default description (LLM may augment). |
| `tags` | array of string | no | For ambiance/scripting filters. |
| `items` | array of item ids | no | Items currently located here. |
| `npcs` | array of npc ids | no | NPCs initially present. |
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

* `type` **required** enumerated string.
* `to` required unless `type` references a `door`.
* `door_id` required when type is `door` (shared door entry).
* `hidden` optional boolean; engine may conceal exit until revealed.
* `conditions` optional array of state flags required to use the exit.
* `on_fail` optional message when conditions unmet.

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
| `location` | string | yes | Location id or container id or `inventory:<npc_id>`. |
| `states` | object | no | Arbitrary boolean/number flags for gameplay. |

Container-specific `container` sub-object:

* `locked` boolean (default false).
* `lock_id` string referencing `locks`.
* `contents` array of item ids; items listed should have `location` equal to the
  container id.
* `capacity` optional number for encumbrance systems.

Weapon/tool specific fields (optional): `damage`, `uses`, `effects`.

## Locks

Locks encapsulate unlocking logic and narrative messaging. Referenced by
`doors.lock_id` or `container.lock_id`.

```json
"locks": {
  "gate_lock": {
    "opens_with": ["silver_key"],
    "auto_unlock": false,
    "description": "Shaped like a raven.",
    "fail_message": "The key does not fit."
  },
  "warded_seal": {
    "opens_with": ["spell:dispel_magic"],
    "auto_unlock": true,
    "description": "Runes glow faintly."
  }
}
```

Fields:

* `opens_with` array of requirements (item ids, skills, scripted flags).
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
* `location` location id where NPC begins.
* `dialogue` array of stock lines or map of state→text.
* `states` object for custom flags (loyalty, hostility, etc.).

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

## Validation Rules

1. All ids must be unique within their respective collections.
2. References (`to`, `door_id`, `lock_id`, `location`, `contents`, `opens_with`,
   etc.) must point to existing ids.
3. Items listed in `location.items` must have matching `location` values (the
   engine may enforce or auto-sync as needed).
4. A `door` referencing a `lock_id` must have that lock defined.
5. Containers cannot list `contents` that include themselves (no cycles).
6. Exits must either specify `to` or `door_id` (never neither).
7. `start_location` must be a valid location id.

Tooling may generate additional warnings (e.g., orphaned items, unreachable
locations) but the core schema above is the minimum contract.

## Relation to Example

`docs/example_game_state` provides a concrete instance conforming to this spec.
Use it as a template when authoring new worlds, and extend the schema carefully
to maintain backward compatibility.
