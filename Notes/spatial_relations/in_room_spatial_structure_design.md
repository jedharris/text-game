# In-Room Spatial Structure Design for the Text Adventure Engine

This document describes how to add **structured intra-room spatial modeling** to your existing Python-based text adventure engine. The design introduces new **intra-room movement** and **structured room graph** models while remaining fully compatible with your engine’s current architecture—dataclasses (`Location`, `Item`, `Actor`), JSON game state, property-based extensibility, and `StateAccessor` as the authoritative query/update interface.

---

# 0. Design Goals

- Introduce **zones**, **walls**, and **spatial relations** inside a location.
- Enable **movement within a room** (“go to window”, “move to throne”).
- Support **object-relative actions** (“examine desk” moves you near the desk).
- Keep all spatial data stored in existing JSON under `properties`.
- Allow **legacy rooms** to continue working unchanged.
- Integrate cleanly with `StateAccessor`, behaviors, and validation.
- Future-proof for possible migration to a full SQLite-based relation model.

---

# 1. Static Spatial Structure Per Location

Locations gain a new optional block:

```jsonc
"properties": {
  "spatial": {
    "zones": {
      "center": {
        "id": "center",
        "name": "center of the hall",
        "description": "You stand in the open middle of the hall.",
        "adjacent": ["by_throne", "by_entrance"],
        "traits": ["open", "exposed"]
      },
      "by_throne": {
        "id": "by_throne",
        "name": "at the foot of the throne",
        "description": "You stand before the raised throne.",
        "adjacent": ["center"],
        "faces_wall": "north_wall"
      }
    },
    "walls": {
      "north_wall": {
        "id": "north_wall",
        "name": "north wall",
        "description": "The wall is hung with faded banners."
      }
    },
    "attachments": [
      { "type": "ATTACHED_TO", "object_id": "item_banner", "target_wall": "north_wall" }
    ]
  }
}
```

### Key Concepts

- **Zones** represent subregions inside the room.  
- **Walls** are named surfaces and can have objects attached.  
- **Attachments** represent static relations (e.g., painting attached to wall).  
- **Adjacency** forms a simple graph enabling movement like “go to dais”.  
- **faces_wall** indicates the directional orientation of a zone.

This structure mirrors the earlier “structured room graph” while fitting cleanly into your engine’s JSON model.

---

# 2. Dynamic Spatial State for Actors and Items

Entities gain per-room positional state as properties:

### Actor example:

```jsonc
"properties": {
  "zone": "center",
  "anchor": null
}
```

### NPC example:

```jsonc
"properties": {
  "zone": "by_throne",
  "anchor": "item_throne"
}
```

### Item (optional):

```jsonc
"properties": {
  "zone": "by_throne",
  "attached_to_wall": "north_wall"
}
```

### Meaning of fields

- `zone` — Current zone where the entity is located.  
- `anchor` — Entity the actor is focused on (desk, window, NPC).  
- `attached_to_wall` — For environmental objects that live on walls.

Zones and anchors allow **positional and object-relative** movement to be unified.

---

# 3. Property Accessors for Spatial Data

Add simple convenience accessors to existing dataclasses:

```python
@property
def zone(self):
    return self.properties.get("zone")

@property
def anchor(self):
    return self.properties.get("anchor")

@property
def attached_to_wall(self):
    return self.properties.get("attached_to_wall")
```

Using accessors avoids touching the dataclass structure and preserves backward compatibility.

---

# 4. StateAccessor Extensions

`StateAccessor` becomes the API for spatial queries and updates.

### Query: actor’s current zone

```python
def get_actor_zone(self, actor_id: str):
    actor = self.get_actor(actor_id)
    return actor.zone if actor else None
```

### Query: get entities in a zone

```python
def get_entities_in_zone(self, location_id: str, zone_id: str):
    items = [...]
    actors = [...]
    return items, actors
```

### Update: move actor within room

```python
def move_actor_to_zone(self, actor_id: str, location_id: str, zone_id: str):
    return self.update(
        actor,
        changes={"properties": {**actor.properties, "zone": zone_id}},
        verb="move_within",
        actor_id=actor_id,
    )
```

### Optional: set anchor

```python
def set_anchor(self, actor_id: str, entity_id: str):
    # update anchor property
```

These helpers ensure every spatial change passes through validation, behaviors, history tracking, and narration hooks.

---

# 5. New Behavioral Logic: “Approach / Go To”

Add a new verb such as **approach**:

```python
def handle_approach(accessor: StateAccessor, action: Dict) -> EventResult:
    # identify target
    # derive appropriate zone
    # move actor to target zone
    # optionally set anchor
```

### Behavior Summary

- `approach desk` moves player to the desk’s zone.  
- If the target has its own zone defined, use that.  
- If not, fall back to room’s default zone.  
- Sets the player’s `anchor` to the desk.  
- Returns narration and a valid `EventResult`.

This single behavior unlocks all structured movement.

---

# 6. Zone-Based Interaction Rules

Verbs like **open**, **push**, **pull**, **search**, **talk** can enforce:

```python
if actor.zone != entity.zone:
    return failure("You’re too far away. Try APPROACH X first.")
```

This keeps gameplay intuitive while leveraging spatial modeling.

---

# 7. Advantages of This Design

### ✓ Fully backward compatible  
Existing games without zones continue to function unchanged.

### ✓ Fully implemented using `properties`  
No redesign of dataclasses, no schema breakage.

### ✓ Graph-based but JSON-friendly  
Zones/walls/attachments form a small structured graph inside each Location.

### ✓ Playable and extensible  
You get:
- object-relative movement  
- local navigation  
- zone-based gating  
- richer environmental descriptions  

### ✓ Future-proof  
Can migrate later to:
- a full relation storage model, or  
- a SQLite backend,  
without breaking JSON-format locations.

---

# 8. Next Steps (Optional)

If wanted, I can generate:

- Python code patches for all necessary classes.  
- Schema guidelines for authoring room spatial structures.  
- Upgrades to the location serializer so that LLM narration incorporates zone/wall data.  
- Testing scenarios and validation routines for zone graphs.

---

**End of Document**
