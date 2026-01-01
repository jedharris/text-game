# Entity Whereabouts and Connections - Design Document

**TL;DR**: Introduce two complementary indexing systems: a **containment index** (whereabouts) for hierarchical "entity is inside container" relationships, and a **connection index** for peer-to-peer relationships like exits linking locations. This unifies entity management, makes exits first-class entities, and fixes the Myconid Sanctuary bug.

**GitHub Issue**: [#350](https://github.com/jedharris/text-game/issues/350)

## Problem Statement

### Original Problem: Dual Representation
Currently, entity location tracking is inconsistent:
- **Items have `.location` property** indicating where they are
- **Locations have `.items` list** that is supposed to mirror items with `location == location_id`
- These get out of sync, causing bugs (items appear in narration but can't be taken)

### Deeper Problem: Exits Are Special
Exits are currently handled differently from all other entities:
- **ExitDescriptors** are embedded in `Location.exits` dict, not first-class entities
- **Directions** are a special vocabulary category with hardcoded handling
- **Doors** awkwardly reference exits via synthetic IDs like `"exit:loc_library:up"`
- Exits can only be traversed via direction commands, not by name, spell, or artifact

This creates unnecessary complexity and limits author capability.

## Goals

1. **Single source of truth**: Entity `.location` property is authoritative for containment
2. **Unified entity model**: Exits become first-class entities like items and actors
3. **Two relationship types**: Containment (hierarchical) and Connection (peer-to-peer)
4. **Fast bidirectional lookups**: O(1) for both index types
5. **Flexible exit access**: Traverse exits by direction, name, spell, artifact, etc.
6. **Clean door/passage model**: Doors and passages fit naturally without special cases

## Conceptual Model: Two Spaces

### Containment Space (Whereabouts)

Hierarchical relationships where one entity is "inside" another:

```
loc_forest
├── sword (item)
├── player (actor)
└── chest (container item)
    └── gold_coins (item inside chest)
```

- **One-to-many**: A container has many entities; each entity has one container
- **Entities**: Items, actors, doors (inside doorways)
- **Query**: "What's in this location?" / "Where is this entity?"

### Connection Space

Peer-to-peer relationships linking entities without hierarchy:

```
exit_forest_north ←──connected──→ exit_cave_south
        │                               │
        └───────connected───────────────┘
                     │
                 doorway_1
```

- **Many-to-many**: Entities can connect to multiple other entities
- **Symmetric**: If A connects to B, B connects to A
- **Entities**: Exits, doorways, passages
- **Query**: "What's connected to this exit?"

### Key Insight

Some entities exist only in containment space (items, actors). Some exist only in connection space (doorways, passages). Exits exist in **both**: they are contained in a location AND connected to other exits/doorways/passages.

## Exits as First-Class Entities

### Current Model (ExitDescriptor)
```python
# Embedded in Location.exits dict - not a real entity
location.exits = {
    "north": ExitDescriptor(destination="loc_cave", ...)
}
```

### New Model (Exit Entity)
```python
exit_forest_north = {
    "id": "exit_forest_north",
    "name": "cave entrance",
    "location": "loc_forest",        # Containment: where you access it from
    "destination": "loc_cave",       # Where it leads
    "direction": "north",            # Optional: for "go north" matching
    "adjectives": ["dark", "narrow"],
    "description": "A dark narrow opening in the hillside"
}
```

### Benefits

**Uniform querying**: Find exits the same way you find items:
```python
exits_here = accessor.get_entities_at("loc_forest", entity_type="exit")
```

**Flexible access**: The LLM parser can match exits by any property:
- `"go north"` → matches exit with `direction: "north"`
- `"enter cave"` → matches exit with `name: "cave entrance"`
- `"go to forest"` → matches exit with `destination: "loc_forest"` (from other side)
- `"use portal"` → matches exit with `name: "portal"`

**Directions become optional**: An exit doesn't need a direction. Hidden exits, portals, magical passages - all work without special handling.

**Consistent narration**: Exits have descriptions, adjectives, traits - same as items.

## Doors and Passages

### The Problem
A door connects two locations but is one physical entity. It can't have two `.location` values.

### The Solution: Doorways

A **doorway** is an entity that exists only in connection space. It connects to exits (or passages) and can contain a door.

```
loc_library                                    loc_sanctum
     │                                              │
     └── exit_library_up ──┬────── exit_sanctum_down ──┘
                           │
                      (connected)
                           │
                       doorway_1
                           │
                      (contains)
                           │
                       door_sanctum
```

- `doorway_1` connects to both `exit_library_up` and `exit_sanctum_down`
- `door_sanctum` has `.location = "doorway_1"` (normal containment)
- The door is accessible from either side via the connection

### Passages

A **passage** represents the physical space between two locations (stairs, tunnel, bridge). Like doorways, passages exist in connection space.

```
loc_library                                              loc_sanctum
     │                                                        │
     └── exit_library_up ──┬──────────────┬── exit_sanctum_down ──┘
                           │              │
                      (connected)    (connected)
                           │              │
                        passage_stairs ───┘
                           │
                      (connected)
                           │
                       doorway_1
                           │
                      (contains)
                           │
                       door_sanctum
```

The passage can have its own description ("narrow stone stairs spiral upward"). The doorway can be at one end of the passage (the door is at the bottom of the stairs, in the library).

### Entity Types by Space

| Entity Type | Containment Space | Connection Space |
|-------------|-------------------|------------------|
| Item        | Yes (has location) | No |
| Actor       | Yes (has location) | No |
| Exit        | Yes (has location) | Yes (connects to exits, doorways, passages) |
| Doorway     | No | Yes (connects to exits or passages) |
| Passage     | No | Yes (connects to exits) |
| Door        | Yes (location = doorway) | No |

## Index Structures

### Containment Index (Whereabouts)

```python
@dataclass
class GameState:
    # Bidirectional containment index
    _entities_at: Dict[str, Set[str]] = field(default_factory=dict)  # where_id → set(entity_ids)
    _entity_where: Dict[str, str] = field(default_factory=dict)      # entity_id → where_id
```

### Connection Index

```python
@dataclass
class GameState:
    # Symmetric connection index
    _connected_to: Dict[str, Set[str]] = field(default_factory=dict)  # entity_id → set(connected_entity_ids)
```

The connection index is symmetric: adding a connection A→B automatically adds B→A.

### Centralized Update Functions

```python
def set_entity_where(self, entity_id: str, new_where: str) -> None:
    """Move entity to new container. Updates entity.location and containment index."""
    ...

def add_connection(self, entity_a: str, entity_b: str) -> None:
    """Connect two entities. Symmetric - adds both directions."""
    if entity_a not in self.game_state._connected_to:
        self.game_state._connected_to[entity_a] = set()
    if entity_b not in self.game_state._connected_to:
        self.game_state._connected_to[entity_b] = set()
    self.game_state._connected_to[entity_a].add(entity_b)
    self.game_state._connected_to[entity_b].add(entity_a)

def remove_connection(self, entity_a: str, entity_b: str) -> None:
    """Disconnect two entities. Symmetric - removes both directions."""
    if entity_a in self.game_state._connected_to:
        self.game_state._connected_to[entity_a].discard(entity_b)
    if entity_b in self.game_state._connected_to:
        self.game_state._connected_to[entity_b].discard(entity_a)

def get_connected(self, entity_id: str) -> Set[str]:
    """Get all entities connected to this one."""
    return self.game_state._connected_to.get(entity_id, set())
```

### Query Examples

```python
# What items are in the forest?
items = accessor.get_entities_at("loc_forest", entity_type="item")

# What exits are accessible from the library?
exits = accessor.get_entities_at("loc_library", entity_type="exit")

# What's connected to this exit? (other exit, doorway, passage)
connected = accessor.get_connected("exit_library_up")

# Is there a door on this exit?
for entity_id in accessor.get_connected("exit_library_up"):
    entity = accessor.get_entity(entity_id)
    if entity.type == "doorway":
        door = accessor.get_entities_at(entity_id, entity_type="door")
```

## Removal States

For entities removed from the game world, use semantic states instead of empty string:

- `"__dead__"` - Actor was killed
- `"__consumed_by_player__"` - Item was eaten/drunk by player
- `"__consumed_by_<actor_id>__"` - Item was consumed by specific NPC
- `"__destroyed__"` - Item was destroyed
- `"__removed__"` - Generic removal

Benefits: self-documenting, queryable, distinguishable from valid IDs.

## LLM Parser Integration

The LLM parser receives exit entities as context, just like items and actors. It can match player commands to exits using any property:

**Context provided to LLM:**
```json
{
  "exits": [
    {
      "id": "exit_forest_north",
      "name": "cave entrance",
      "direction": "north",
      "destination": "loc_cave",
      "description": "A dark narrow opening in the hillside"
    }
  ]
}
```

**Player commands that all resolve to same exit:**
- `"go north"` - matches direction
- `"enter cave"` - matches name
- `"go into the dark opening"` - matches description
- `"north"` - bare direction, implied "go"

The LLM produces:
```json
{"verb": "go", "object": "exit_forest_north"}
```

No special direction handling needed. Exits are entities; LLM matches them.

## Migration Strategy

### Phase 1: Add Containment Index Infrastructure
1. Add `_entities_at`, `_entity_where` to GameState
2. Implement `set_entity_where()` in StateAccessor
3. Implement `_build_whereabouts_index()` at load time
4. Write unit tests for index building and updates
5. **Low risk** - additive change, existing code continues to work

### Phase 2: Centralize Location Assignments
1. Replace all direct `.location =` assignments with `accessor.set_entity_where()`
2. ~11 production code locations, mostly in `state_manager.py`
3. Update tests as needed (~172 assignments, mechanical changes)
4. **Low risk** - same behavior, just routed through central function

### Phase 3: Create Exit Entity Type
1. Define Exit class with: id, name, location, destination, direction, description, properties, behaviors
2. Add `exits` list to GameState (parallel to `items`, `actors`)
3. Update state loading to parse Exit entities
4. Update index building to include exits in containment index
5. **Medium risk** - new entity type, but doesn't break existing code yet

### Phase 4: JSON Format Migration Tool
1. Create `tools/migrate_exits.py` migration tool
2. For each `Location.exits` entry:
   - Create Exit entity with location = this location
   - Create paired Exit entity with location = destination, direction = opposite
   - Copy properties, generate symmetric defaults for return exit
3. Handle doors: create Doorway entities, update door locations
4. Handle passages: create Passage entities if `passage` field present
5. Run migration on all game_state.json files
6. **Medium risk** - one-time transformation, validate with walkthroughs

### Phase 5: Add Connection Index
1. Add `_connected_to` to GameState
2. Implement `add_connection()`, `remove_connection()`, `get_connected()`
3. Build connection index at load time from Exit destinations and Doorway/Passage connections
4. **Low risk** - additive

### Phase 6: Update Traversal and Query Logic
1. Update `behaviors/core/exits.py` to use Exit entities via index
2. Update narration to query exits via `get_entities_at(location, type="exit")`
3. Update door finding to use connection queries
4. Remove O(n) scans
5. **High risk** - core traversal logic changes, extensive testing needed

### Phase 7: Deprecate Legacy Fields
1. Remove `Location.exits` dict (no longer used after Phase 6)
2. Remove `location.items` and `actor.inventory` lists
3. Update validators to check new format
4. Document patterns in authoring guide
5. **Low risk** - cleanup after everything works

## Design Decisions

1. **Exit entity type**: New `Exit` class
   - Cleaner than overloading Item with exit properties
   - Exits have distinct semantics (destination, traversal)

2. **Doorway/Passage entity types**: New classes, possibly sharing a base with Exit
   - All three are "structural" entities related to spatial connections
   - Could share a common base class or protocol
   - Doorway and Passage exist only in connection space (no `.location`)

3. **Bidirectional exit authoring**: Auto-generation by default, explicit override available
   - Author writes one exit; engine creates paired exit automatically
   - Reduces boilerplate and errors for common case
   - Authors can write both exits explicitly for asymmetric cases (one-way, different descriptions per side)
   - **Principle**: If authors stick with defaults, everything looks the same as now

4. **Connection index persistence**: Rebuild from entity data at load time
   - Minimal data in game_state.json is source of truth
   - Connections derived from per-entity properties (e.g., exit's `destination`)
   - Index is computed, not stored

5. **Direction vocabulary**: Keep as-is for now
   - Avoid excessive change in this phase
   - Directions remain a vocabulary category
   - Future: could migrate to adjectives/synonyms on exits

## Additional Design Decisions

6. **Shared base class**: Exit, Doorway, Passage share as much as possible
   - Propose maximal sharing; refine based on what works
   - All participate in connection space
   - Exit also participates in containment space

7. **JSON format migration**: Update game_state.json files, not load-time conversion
   - Migration tool converts embedded `Location.exits` to explicit Exit entities
   - Each direction becomes its own Exit entity in the file
   - Paired exits generated with symmetric defaults during migration
   - After migration, each exit can have independent descriptions/properties/behaviors
   - **Authoring burden unchanged** - still specify source, destination, direction
   - **Authoring capability increased** - can now customize each direction independently

8. **Doorway/Passage connections**: Always between exactly two exits
   - Author specifies connections to two exits
   - Future: could generalize, but defer until use cases emerge

## Open Questions (Deferred)

1. **Non-default exit cases**: One-way exits, asymmetric properties - what's the authoring format?
   - Defer until we have concrete use cases

2. **Multi-way passages**: Could a passage connect more than two exits?
   - Defer - current model assumes two endpoints

## Benefits

1. **Unified model**: Exits, items, actors all handled consistently
2. **Flexible access**: Traverse exits by direction, name, spell, or artifact
3. **Clean door model**: Doors in doorways, doorways connected to exits
4. **LLM-friendly**: Parser matches exits like any entity
5. **Fast queries**: O(1) lookups in both directions
6. **Fixes bugs**: Myconid Sanctuary items will be takeable

## Risks

1. **Migration effort**: Significant changes to exit handling
2. **Two index types**: More complex than single whereabouts index
3. **Authoring changes**: Exit authoring format changes
4. **Connection-only entities**: New concept (doorway, passage) without `.location`

## Success Criteria

1. All unit tests pass
2. All integration tests pass
3. Exits accessible by direction, name, and destination
4. Doors work correctly from both sides of exit
5. Myconid Sanctuary bug is fixed
6. No performance regression
