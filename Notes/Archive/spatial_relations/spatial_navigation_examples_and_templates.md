# Spatially-Aware Rooms: Examples and Templates for Game Authors

This document provides **practical examples** and **starter templates** for using the new in-room spatial design in your text adventure framework. It is intended as a companion to the spatial navigation chapter in the Game Author Manual.

You’ll see:

- Example room definitions with **zones**, **walls**, and **attachments**
- How to place **items** and **NPCs** into specific zones
- How to write **zone-aware behavior hooks** (e.g., NPCs that react to you entering a zone)
- Suggested patterns for **verbs** like `APPROACH`, `MOVE TO`, and zone-gated interactions

All examples assume:

- Locations, items, and actors use `properties` for flexible fields.
- Spatial structure is stored under `location.properties.spatial`.
- Actor and item position within the room is stored as properties:
  - `properties.zone`
  - `properties.anchor` (for actors)
  - `properties.attached_to_wall` (for items on walls)


---

## 1. Minimal Spatial Room Example

### 1.1 Goal

Create a simple room where:

- The player can stand in the **center** or **by the window**.
- A **painting** hangs on the north wall.
- The **window** is interactable only when you are near it.

### 1.2 Location Definition (JSON-ish)

```jsonc
{
  "id": "loc_study",
  "name": "Quiet Study",
  "description": "A compact study with a single window and a worn rug.",
  "exits": {
    "south": {
      "to": "loc_hallway",
      "properties": {}
    }
  },
  "items": ["item_painting", "item_window_latch"],
  "properties": {
    "spatial": {
      "zones": {
        "center": {
          "id": "center",
          "name": "center of the study",
          "description": "You stand on the worn rug in the middle of the room.",
          "adjacent": ["by_window"]
        },
        "by_window": {
          "id": "by_window",
          "name": "by the window",
          "description": "You are right next to the narrow window.",
          "adjacent": ["center"],
          "faces_wall": "north_wall"
        }
      },
      "walls": {
        "north_wall": {
          "id": "north_wall",
          "name": "north wall",
          "description": "The north wall is dominated by a narrow window and an old painting."
        }
      },
      "attachments": [
        {
          "type": "ATTACHED_TO",
          "object_id": "item_painting",
          "target_wall": "north_wall"
        }
      ]
    },
    "default_zone": "center"
  },
  "behaviors": [
    "behaviors.spatial.default_room_description"
  ]
}
```

### 1.3 Items

```jsonc
{
  "id": "item_painting",
  "name": "old painting",
  "description": "A faded landscape painting in an ornate frame.",
  "location": "loc_study",
  "properties": {
    "attached_to_wall": "north_wall",
    "zone": "by_window"
  },
  "behaviors": []
}
```

```jsonc
{
  "id": "item_window_latch",
  "name": "window latch",
  "description": "A stiff little latch that seems rarely used.",
  "location": "loc_study",
  "properties": {
    "zone": "by_window",
    "is_latch": true
  },
  "behaviors": []
}
```

### 1.4 Player Initial Position

```jsonc
{
  "id": "player",
  "name": "you",
  "location": "loc_study",
  "inventory": [],
  "properties": {
    "zone": "center",
    "anchor": null
  },
  "behaviors": []
}
```

### 1.5 Example Interactions (Intended)

- `LOOK`  
  → Describes the study, then adds a short bit about your current zone (center or by_window).

- `APPROACH WINDOW` or `GO TO WINDOW`  
  → Moves the player from `center` to `by_window`, changes `zone`, sets `anchor` to the window (or latch) entity.

- `OPEN WINDOW`  
  - Fails with a hint if you are in `center` zone:
    > You’re too far from the window. Try APPROACH WINDOW first.
  - Works in `by_window` zone:
    > With a bit of force, you push the stiff latch and crack the window open.

---

## 2. Template: Generic Spatial Location Skeleton

Use this template as a starting point for any location where you want simple two–three zone layout.

```jsonc
{
  "id": "loc_TEMPLATE",
  "name": "TEMPLATE Name",
  "description": "Base description of the room.",
  "exits": {
    "north": { "to": "loc_OTHER", "properties": {} }
  },
  "items": [],
  "properties": {
    "spatial": {
      "zones": {
        "center": {
          "id": "center",
          "name": "center of the room",
          "description": "You are standing in the middle of the room.",
          "adjacent": ["zone1"]
        },
        "zone1": {
          "id": "zone1",
          "name": "near something interesting",
          "description": "You stand near something interesting.",
          "adjacent": ["center"],
          "faces_wall": "wall1"
        }
      },
      "walls": {
        "wall1": {
          "id": "wall1",
          "name": "feature wall",
          "description": "A wall that draws your attention."
        }
      },
      "attachments": [
        {
          "type": "ATTACHED_TO",
          "object_id": "item_something",
          "target_wall": "wall1"
        }
      ]
    },
    "default_zone": "center"
  },
  "behaviors": [
    "behaviors.spatial.default_room_description"
  ]
}
```

You can:

- Add more zones (e.g., `by_door`, `by_dais`).
- Add more walls (`east_wall`, `south_wall`).
- Attach items to walls, or just place them in zones via `properties.zone`.

---

## 3. Code Template: Zone-Aware Room Description

Below is a Python-style behavior function that:

- Uses the player’s `zone` to add a context-specific sentence to the room description.
- Assumes you have access to a `StateAccessor`-like object and a `location_serializer`.

```python
def default_room_description(accessor, actor_id: str, location_id: str):
    actor = accessor.get_actor(actor_id)
    location = accessor.get_location(location_id)

    base = location.description or ""
    spatial = (location.properties or {}).get("spatial", {})
    zones = spatial.get("zones", {})

    zone_id = actor.properties.get("zone") or location.properties.get("default_zone")
    zone_info = zones.get(zone_id) if zone_id else None

    extra = ""
    if zone_info and zone_info.get("description"):
        extra = " " + zone_info["description"]

    # You might integrate this with your existing location_serializer.
    return base + extra
```

Use this as a hook for your room display system.

---

## 4. Code Template: APPROACH / GO TO Verb

This is a sketch of a behavior handler that:

- Finds a target entity in the current location.
- Derives the appropriate zone.
- Moves the player into that zone.
- Sets `anchor` to that entity for subsequent context.

```python
def handle_approach(accessor, action):
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)
    if not actor:
        return accessor.fail("You momentarily fail to exist.")

    obj_entry = action.get("object")
    if not obj_entry:
        return accessor.fail("What do you want to approach?")

    # Find entity matching the parsed object in the same location
    target = accessor.find_entity_in_location(
        obj_entry,
        actor.location,
        adjective=action.get("adjective"),
        actor_id=actor_id
    )
    if not target:
        return accessor.fail(f"You don't see {obj_entry.word} here.")

    location = accessor.get_location(actor.location)
    spatial = (location.properties or {}).get("spatial", {})
    default_zone = location.properties.get("default_zone", "center")

    # Use the target's own zone if it has one; otherwise fall back to default.
    target_zone = getattr(target, "zone", None) or                   target.properties.get("zone") or                   default_zone

    # Update actor's zone via your standard state update mechanism.
    accessor.set_actor_zone(actor_id, target_zone)
    accessor.set_actor_anchor(actor_id, target.id)

    return accessor.success(
        f"You move to {target.name}.",
        data={
            "actor_id": actor_id,
            "zone": target_zone,
            "anchor": target.id
        }
    )
```

You’ll want to adapt names like `accessor.fail` / `accessor.success` to your actual engine’s result pattern.

---

## 5. Zone-Gated Interaction Example

### 5.1 Goal

Prevent the player from doing something unless they are in the correct zone.

Example: The player can only **OPEN WINDOW** if they are in the `by_window` zone.

### 5.2 Behavior Sketch

```python
def handle_open(accessor, action):
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)
    obj_entry = action.get("object")

    if not obj_entry:
        return accessor.fail("What do you want to open?")

    target = accessor.find_entity_in_location(
        obj_entry,
        actor.location,
        adjective=action.get("adjective"),
        actor_id=actor_id
    )
    if not target:
        return accessor.fail("You don't see that here.")

    required_zone = target.properties.get("required_zone")

    if required_zone:
        current_zone = actor.properties.get("zone")
        if current_zone != required_zone:
            zone_name = required_zone
            # if you want to resolve zone_name from spatial.zones, you can
            return accessor.fail(
                f"You're too far away to open {target.name}. Try APPROACH {target.name.upper()} first."
            )

    # Proceed with your existing open logic.
    # For now, just pretend it works:
    return accessor.success(f"You open {target.name}.")
```

### 5.3 Item Example with `required_zone`

```jsonc
{
  "id": "item_window_latch",
  "name": "window latch",
  "description": "A stiff little latch that seems rarely used.",
  "location": "loc_study",
  "properties": {
    "zone": "by_window",
    "required_zone": "by_window"
  },
  "behaviors": [
    "behaviors.spatial.open_window_latch"
  ]
}
```

This pattern lets authors:

- Mark certain objects as requiring proximity (via zones) without needing deep engine changes.
- Incrementally convert puzzles to use fine-grained spatial gating.

---

## 6. Zone-Aware NPC Behavior Examples

### 6.1 NPC That Reacts When the Player Enters a Zone

Scenario:

- A guard stands by the throne (`zone = "by_throne"`).
- The guard challenges the player when they first step into `by_throne`.

#### NPC Definition

```jsonc
{
  "id": "npc_guard",
  "name": "palace guard",
  "description": "A stern guard in polished armor.",
  "location": "loc_throne_room",
  "properties": {
    "zone": "by_throne",
    "has_challenged": false
  },
  "behaviors": [
    "behaviors.npc.guard_zone_challenge"
  ]
}
```

#### Behavior: Trigger on Zone Entry

You might implement an event or hook like `on_zone_change(actor, old_zone, new_zone)` in your engine. A simple polling/trigger-based behavior might look like:

```python
def guard_zone_challenge(accessor, npc_id: str):
    guard = accessor.get_entity(npc_id)
    if guard.properties.get("has_challenged"):
        return  # Only trigger once.

    player = accessor.get_player()
    if player.location != guard.location:
        return

    player_zone = player.properties.get("zone")
    guard_zone = guard.properties.get("zone")

    if player_zone == guard_zone:
        accessor.send_message(
            "The guard steps in front of you. \"Halt! No one approaches the throne without permission.\""
        )
        guard.properties["has_challenged"] = True
        accessor.save_entity(guard)
```

You can wire this into your engine’s turn/update cycle (e.g., NPC tick, after player movement).

---

## 7. Putting It All Together: Starter Spatial Room Pack

Here is a compact, ready-to-adapt set of definitions for a small **throne room** using zones, walls, and NPCs.

### 7.1 Location

```jsonc
{
  "id": "loc_throne_room",
  "name": "Throne Room",
  "description": "A long, vaulted hall culminating in a raised dais where the throne sits.",
  "exits": {
    "south": { "to": "loc_hallway", "properties": {} }
  },
  "items": ["item_throne", "item_banner_1", "item_banner_2"],
  "properties": {
    "spatial": {
      "zones": {
        "entrance": {
          "id": "entrance",
          "name": "at the entrance",
          "description": "You stand under the high archway at the south end of the hall.",
          "adjacent": ["center"]
        },
        "center": {
          "id": "center",
          "name": "center of the hall",
          "description": "You stand midway along the hall, the throne distant but imposing.",
          "adjacent": ["entrance", "by_throne"]
        },
        "by_throne": {
          "id": "by_throne",
          "name": "before the throne",
          "description": "You stand at the foot of the dais, the throne looming above.",
          "adjacent": ["center"],
          "faces_wall": "north_wall"
        }
      },
      "walls": {
        "north_wall": {
          "id": "north_wall",
          "name": "north wall",
          "description": "Tall windows and hanging banners flank the throne."
        }
      },
      "attachments": [
        {
          "type": "ATTACHED_TO",
          "object_id": "item_banner_1",
          "target_wall": "north_wall"
        },
        {
          "type": "ATTACHED_TO",
          "object_id": "item_banner_2",
          "target_wall": "north_wall"
        }
      ]
    },
    "default_zone": "entrance"
  },
  "behaviors": [
    "behaviors.spatial.default_room_description"
  ]
}
```

### 7.2 Throne & Banners

```jsonc
{
  "id": "item_throne",
  "name": "jeweled throne",
  "description": "A massive throne inlaid with gold and gems.",
  "location": "loc_throne_room",
  "properties": {
    "zone": "by_throne",
    "is_throne": true
  },
  "behaviors": []
}
```

```jsonc
{
  "id": "item_banner_1",
  "name": "red banner",
  "description": "A red banner bearing the royal crest.",
  "location": "loc_throne_room",
  "properties": {
    "zone": "by_throne",
    "attached_to_wall": "north_wall"
  },
  "behaviors": []
}
```

```jsonc
{
  "id": "item_banner_2",
  "name": "blue banner",
  "description": "A blue banner, heavy with embroidered symbols.",
  "location": "loc_throne_room",
  "properties": {
    "zone": "by_throne",
    "attached_to_wall": "north_wall"
  },
  "behaviors": []
}
```

### 7.3 Guard NPC

```jsonc
{
  "id": "npc_guard",
  "name": "palace guard",
  "description": "A stern guard in polished armor, watching the throne.",
  "location": "loc_throne_room",
  "properties": {
    "zone": "by_throne",
    "has_challenged": false
  },
  "behaviors": [
    "behaviors.npc.guard_zone_challenge"
  ]
}
```

### 7.4 Player Start

```jsonc
{
  "id": "player",
  "name": "you",
  "location": "loc_throne_room",
  "inventory": [],
  "properties": {
    "zone": "entrance",
    "anchor": null
  },
  "behaviors": []
}
```

With this configuration:

- The player starts in `entrance`.
- `APPROACH THRONE` moves them to `by_throne`.
- When they reach `by_throne`, the guard can challenge them.
- `LOOK` will show slightly different descriptions depending on the player’s zone.

---

## 8. Authoring Checklist for Spatial Rooms

When creating a spatially-aware room, check:

1. **Zones defined?**
   - Names, descriptions, `adjacent` lists.
   - A `default_zone` in the location’s `properties`.

2. **Walls defined?**
   - Only if you need wall flavor or attachments.

3. **Attachments and item zones set?**
   - Items on walls: `attached_to_wall` and `zone`.
   - Items requiring proximity: `required_zone`.

4. **NPC zones and behaviors?**
   - `properties.zone` for each NPC.
   - Any zone-triggered behaviors (e.g., `guard_zone_challenge`).

5. **Verbs and gating?**
   - `APPROACH` / `GO TO` support.
   - Zone checks in actions that should require proximity.

If these are in place, you’ve got a fully **spatially-aware room** ready for nuanced gameplay.

---

**End of Document**
