# Representing Structured Rooms in a Text Adventure Engine

When modeling intra-room movement, zones, NPC positions, object placement, and spatial relations, a room in a text adventure becomes more than a “bag of items.” It evolves into a structured **mini-graph** of entities connected by relations. This document explains how to represent that structure cleanly and flexibly.

---

## 1. Conceptual Model: Rooms as Entity+Relation Graphs

A room consists of:

1. **Entities** – anything that can be referred to or have spatial properties:
   - zones  
   - walls  
   - items  
   - furniture  
   - NPCs  
   - the player  

2. **Relations** – statements describing spatial or structural facts:
   - `IN_ZONE`  
   - `NEAR`  
   - `ON`  
   - `UNDER`  
   - `ATTACHED_TO`  
   - `FACES`  
   - `ADJACENT_TO`  
   - `BLOCKS`  
   - …and others depending on your system

Together, these describe the dynamic and static structure of the room.

---

## 2. Entities: What Counts as a “Thing” in a Room?

In this relational model, every spatially relevant element in the room is an **entity**, including:

- **Zones** (like “center,” “near the window,” “on the dais”)  
- **Walls** (north wall, east wall, mural wall)  
- **Furniture** (desk, table, throne)  
- **Items** (key, rope, scroll)  
- **NPCs** (guard, bartender, ghost)  
- **The player**  

Example entity structure:

```json
{
  "id": "desk_1",
  "kind": "object",
  "name": "heavy oak desk",
  "base_description": "A solid wooden desk.",
  "flags": { "climbable": false, "container": true }
}
```

---

## 3. Relations: Static vs. Dynamic

### Static relations
These seldom change and define the layout:

- `(zone_center, ADJACENT_TO, zone_by_window)`
- `(painting_1, ATTACHED_TO, wall_north)`
- `(window_1, ATTACHED_TO, wall_east)`
- `(desk_1, IN_ZONE, zone_center)`

### Dynamic relations
Updated during gameplay:

- `(player, IN_ZONE, zone_by_window)`
- `(player, NEAR, window_1)`
- `(npc_guard, FACING, player)`
- `(small_key, ON, desk_1)`

Static relations define **structure**; dynamic relations define **state**.

---

## 4. Walls and Surfaces as Entities

Walls become entities so objects can be attached to them:

Entities:
```
wall_north
wall_east
painting_1
torch_sconce_1
window_1
```

Relations:
```
(painting_1, ATTACHED_TO, wall_north)
(torch_sconce_1, ATTACHED_TO, wall_east)
(window_1, ATTACHED_TO, wall_east)
(zone_by_window, FACES, wall_east)
```

This supports:
- `LOOK NORTH`
- `GO TO WINDOW`
- flexible room descriptions based on relational queries

---

## 5. NPCs as Entities in the Same Graph

NPCs move and interact by manipulating the same relations:

Example:
```
(guard, IN_ZONE, zone_doorway)
(guard, FACING, wall_south)
(guard, NEAR, door_1)

(ghost_child, IN_ZONE, zone_by_toys)
(ghost_child, NEAR, toy_pile)
```

NPC AI simply updates those relations.

To check player interactions:
- Are player and NPC in the same zone?
- Are they near each other?
- Are they facing each other?

---

## 6. Concrete Data Structure for a Room (Example)

```json
{
  "id": "grand_hall",
  "name": "Grand Hall",
  "entities": [
    { "id": "zone_center", "kind": "zone", "name": "center of the hall" },
    { "id": "zone_by_throne", "kind": "zone", "name": "foot of the throne" },
    { "id": "wall_north", "kind": "wall", "name": "north wall" },
    { "id": "throne", "kind": "object", "name": "jeweled throne" },
    { "id": "banner_1", "kind": "object", "name": "tattered banner" },
    { "id": "guard_1", "kind": "npc", "name": "palace guard" },
    { "id": "player", "kind": "player", "name": "you" }
  ],
  "relations": [
    { "subject": "zone_center", "type": "ADJACENT_TO", "object": "zone_by_throne" },
    { "subject": "throne", "type": "IN_ZONE", "object": "zone_by_throne" },
    { "subject": "banner_1", "type": "ATTACHED_TO", "object": "wall_north" },
    { "subject": "zone_by_throne", "type": "FACES", "object": "wall_north" },

    { "subject": "player", "type": "IN_ZONE", "object": "zone_center" },
    { "subject": "guard_1", "type": "IN_ZONE", "object": "zone_by_throne" },
    { "subject": "guard_1", "type": "FACING", "object": "player" }
  ]
}
```

Queries become simple and powerful:
- Objects on a wall?  
  → all `(x, ATTACHED_TO, wall_north)`
- Who is in your zone?  
  → all `(npc, IN_ZONE, player.zone)`
- What’s near you?  
  → all `(player, NEAR, x)` or `(x, NEAR, player)`

---

## 7. Where These Relations Live (Room-Level vs Global)

### Option A: Room-level relation store
Room internally contains all spatial relations.
- Easy to reason about.
- Good for single-room interactions.

### Option B: Global relation graph
One world-wide store:
```
RelationStore : list[Relation]
```
Room stores only which entities belong to it.
- Required if you want cross-room interactions (e.g., looking through windows).

Both approaches share the same query patterns.

---

## 8. API Convenience Layer

While relations are stored as generic triples, higher-level helper functions make scripting pleasant:

```python
room.move_entity_to_zone("player", "zone_by_window")
room.set_near("player", "window_1")
room.objects_on_wall("north")
room.npcs_in_same_zone_as("player")
room.attach_to_wall("painting_1", "wall_north")
```

These just manipulate or query the relation graph.

---

## Conclusion

A structured room in a text adventure becomes a **mini knowledge graph**, where:

- every spatially meaningful thing is an **entity**
- all structure (walls, subareas, attachments, NPC positions, item placement) is expressed via **relations**
- player movement, NPC AI, and environmental effects all operate by adding, removing, or querying these relations

This model is clean, extensible, and compatible with many different interaction styles, from classic parser IF to more simulation-heavy systems.

