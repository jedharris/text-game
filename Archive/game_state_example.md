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
  "locations": [...],
  "doors": [...],
  "items": [...],
  "locks": [...],
  "npcs": [...]
}
```

Section Details
---------------

* `metadata`: title, author, version, optional default messages.
* `vocabulary`: optional alias map to keep descriptive nouns aligned with
  parser-recognized tokens (e.g., canonical ids mapped to synonyms).
* `locations`: **array** of location objects. Each location has a unique internal
  `id` (e.g., `"loc_1"`), a `name` (player-visible), `description`, `items` (list
  of item IDs located there), optional `npcs`, and an `exits` object mapping
  directions to exit descriptors. Exits can point directly to destinations or
  reference a door entry when the passage has state (locked/open).
* `doors`: array of bidirectional (or one-way) doors that might be shared
  between two locations. Fields include `id` (internal unique ID), `locations`
  (list of one or two location IDs), `description`, `locked`, `lock_id`, and
  `open`. Exits refer to these via `door_id`.
* `items`: array of item definitions. Each entry has `id` (internal unique ID),
  `name` (player-visible), `description`, `type`, `portable`, and `location`
  (location ID, container item ID, `"player"`, or NPC ID). Container-type items
  include a `container` sub-object with `contents`, `locked`, `lock_id`, and
  `capacity`.
* `locks`: **array** of lock objects. Each has `id` (internal unique ID),
  `opens_with` (array of item IDs or puzzle conditions), and optional
  `description` and `fail_message`.
* `npcs`: array describing non-player entities with `id` (internal unique ID),
  `name` (player-visible), `description`, `location` (location ID), and optional
  dialogue cues.

Example JSON
------------

```json
{
  "metadata": {
    "title": "Crypt of Winds",
    "author": "Example Author",
    "version": "2.0",
    "start_location": "loc_1"
  },
  "locations": [
    {
      "id": "loc_1",
      "name": "Crypt Entrance",
      "description": "A marble archway opens into darkness...",
      "exits": {
        "north": { "type": "door", "door_id": "door_1" },
        "south": { "type": "open", "to": "loc_3" }
      },
      "items": ["item_1"],
      "npcs": [],
      "tags": ["outdoors"]
    },
    {
      "id": "loc_2",
      "name": "Antechamber",
      "description": "Dusty banners hang from cracked walls.",
      "exits": {
        "south": { "type": "door", "door_id": "door_1" },
        "east": { "type": "open", "to": "loc_4" }
      },
      "items": ["item_2"],
      "npcs": ["npc_1"]
    },
    {
      "id": "loc_3",
      "name": "Courtyard",
      "description": "Overgrown garden beneath a gray sky.",
      "exits": {
        "north": { "type": "open", "to": "loc_1" }
      },
      "items": [],
      "npcs": []
    },
    {
      "id": "loc_4",
      "name": "Treasure Room",
      "description": "Glittering coins and artifacts fill alcoves.",
      "exits": {
        "west": { "type": "open", "to": "loc_2" }
      },
      "items": [],
      "npcs": []
    }
  ],
  "doors": [
    {
      "id": "door_1",
      "locations": ["loc_1", "loc_2"],
      "description": "An ornate iron gate patterned with ravens.",
      "locked": true,
      "lock_id": "lock_1",
      "open": false
    }
  ],
  "items": [
    {
      "id": "item_1",
      "name": "Unlit Torch",
      "description": "Wrapped in old linens, still usable.",
      "type": "tool",
      "portable": true,
      "location": "loc_1"
    },
    {
      "id": "item_2",
      "name": "Stone Chest",
      "description": "Heavy lid carved with spiral motifs.",
      "type": "container",
      "portable": false,
      "location": "loc_2",
      "container": {
        "locked": true,
        "lock_id": "lock_2",
        "contents": ["item_3"]
      }
    },
    {
      "id": "item_3",
      "name": "Silver Key",
      "description": "A key with a raven-shaped bow.",
      "type": "key",
      "portable": true,
      "location": "item_2"
    }
  ],
  "locks": [
    {
      "id": "lock_1",
      "opens_with": ["item_3"],
      "description": "Intricate raven sigil."
    },
    {
      "id": "lock_2",
      "opens_with": ["riddle_solution"],
      "description": "Carved runes glow faintly."
    }
  ],
  "npcs": [
    {
      "id": "npc_1",
      "name": "Ghostly Guard",
      "description": "Translucent armor-clad figure watching silently.",
      "location": "loc_2",
      "dialogue": "Turn back... unless you bear the raven's blessing."
    }
  ]
}
```

Additional sections (quests, scripted events, ambient effects, etc.) can
be appended as needed without breaking the core schema above.
