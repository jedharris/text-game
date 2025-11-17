Example Adventure Game State JSON
=================================

Overview
--------

This document outlines a JSON file structure for describing an adventure
game world. The goal is to capture locations, items, actors, doors, and
locks in a deterministic format the parser/game engine can load.

Top-Level Sections
------------------

```
{
  "metadata": {...},
  "vocabulary": {...},
  "locations": {...},
  "doors": [...],
  "items": [...],
  "locks": {...},
  "npcs": [...]
}
```

Section Details
---------------

* `metadata`: title, author, version, optional default messages.
* `vocabulary`: optional alias map to keep descriptive nouns aligned with
  parser-recognized tokens (e.g., canonical ids mapped to synonyms).
* `locations`: dictionary keyed by location id. Each location stores a
  `name`, `description`, `items` (list of item ids located there),
  optional `npcs`, and an `exits` object mapping directions to exit
  descriptors. Exits can point directly to destinations or reference a
  door entry when the passage has state (locked/open).
* `doors`: array of bidirectional (or one-way) doors that might be shared
  between two locations. Fields include `id`, `locations` (list of one or
  two location ids), `description`, `locked`, `lock_id`, and `open`. Exits
  refer to these via `door_id`.
* `items`: array of item definitions. Each entry has `id`, `name`,
  `description`, `type`, `portable`, and `location` (current holder or
  containing location). Container-type items include a `container`
  sub-object with `contents`, `locked`, `lock_id`, and `capacity`.
* `locks`: dictionary keyed by lock ids describing how to unlock (e.g.,
  `opens_with` pointing to a key item id or puzzle condition) and any
  special messages.
* `npcs`: array describing non-player entities with `id`, `name`,
  `description`, and optional dialogue cues. NPC entries can appear in
  `locations.npcs`.

Example JSON
------------

```json
{
  "metadata": {
    "title": "Crypt of Winds",
    "author": "Example Author",
    "version": "1.0"
  },
  "locations": {
    "entrance": {
      "name": "Crypt Entrance",
      "description": "A marble archway opens into darkness...",
      "exits": {
        "north": { "type": "door", "door_id": "iron_gate" },
        "south": { "type": "open", "to": "courtyard" }
      },
      "items": ["torch"],
      "npcs": [],
      "tags": ["outdoors"]
    },
    "antechamber": {
      "name": "Antechamber",
      "description": "Dusty banners hang from cracked walls.",
      "exits": {
        "south": { "type": "door", "door_id": "iron_gate" },
        "east": { "type": "open", "to": "treasure_room" }
      },
      "items": ["stone_chest"],
      "npcs": ["ghost_guard"]
    }
  },
  "doors": [
    {
      "id": "iron_gate",
      "locations": ["entrance", "antechamber"],
      "description": "An ornate iron gate patterned with ravens.",
      "locked": true,
      "lock_id": "gate_lock",
      "open": false
    }
  ],
  "items": [
    {
      "id": "torch",
      "name": "Unlit Torch",
      "description": "Wrapped in old linens, still usable.",
      "type": "tool",
      "portable": true,
      "location": "entrance"
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
        "contents": ["silver_key"]
      }
    },
    {
      "id": "silver_key",
      "name": "Silver Key",
      "description": "A key with a raven-shaped bow.",
      "type": "key",
      "portable": true,
      "location": "stone_chest"
    }
  ],
  "locks": {
    "gate_lock": {
      "opens_with": "silver_key",
      "description": "Intricate raven sigil."
    },
    "chest_lock": {
      "opens_with": "riddle_solution",
      "description": "Carved runes glow faintly."
    }
  },
  "npcs": [
    {
      "id": "ghost_guard",
      "name": "Ghostly Guard",
      "description": "Translucent armor-clad figure watching silently.",
      "dialogue": "Turn back... unless you bear the raven's blessing."
    }
  ]
}
```

Additional sections (quests, scripted events, ambient effects, etc.) can
be appended as needed without breaking the core schema above.
