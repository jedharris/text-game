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

### Key Insight: The Continuum of Places

**Ontologically, the connection graph is fundamental.** Every "where" is a node in the connection graph. Each "where" is an island with a tree of contained items, actors, sub-places, etc.

Locations, passages, and doorways form a continuum - they're all "places in the connection graph":
- **Locations (rooms)**: Large places containing many things, connected to other locations via exits
- **Passages (stairs, tunnels)**: Medium places connecting locations, representing physical space between them
- **Doorways (door frames)**: Small places where exits meet, can contain doors

All three are **containers** (keys in `_entities_at` index) but are **not contained** (no `.where` property themselves - they ARE the "where").

**Participation in spaces:**
- **Containment space only**: Items, actors (have `.where`, are not "wheres")
- **Connection space only**: Initially passages and doorways (are "wheres" but have no `.where`)
- **Both spaces**: Exits (have `.where` = the location they're in, AND connect to other entities)

**Future flexibility**: Over time, passages and doorways may gain containment semantics (items on stairs, actors blocking doorways). The structure supports this - they're already container keys. Current semantic constraint: they can only contain doors (for doorways) or nothing (for passages), and their contents cannot be mutated by gameplay.

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
    "location": "loc_forest",            # Containment: where you access it from
    "connections": ["exit_cave_south"],  # What this exit connects to (drives connection index)
    "direction": "north",                # Optional: for "go north" matching
    "adjectives": ["dark", "narrow"],
    "description": "A dark narrow opening in the hillside"
}
```

**Connection semantics:**
- `.connections` is a list of entity IDs (typically other exits)
- Initially contains one paired exit: `["exit_cave_south"]`
- Future: multi-destination portals could have multiple connections
- Connection index is **derived** from `.connections` at load time (symmetric - if A→B then B→A)

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

| Entity Type | Has `.where`? | Is a "where"? | Connection Space | Notes |
|-------------|---------------|---------------|------------------|-------|
| Location    | No | Yes (container key) | No | Root containers |
| Item        | Yes | No | No | Normal contained entities |
| Actor       | Yes | No | No | Normal contained entities |
| Exit        | Yes | Yes (container key) | Yes (`.connections` list) | Dual participation |
| Doorway     | No | Yes (container key) | Yes (`.connections` list) | Can contain doors only (initially) |
| Passage     | No | Yes (container key) | Yes (`.connections` list) | Cannot contain entities (initially) |
| Door        | Yes (`.where` = doorway) | No | No | Contained in doorways |

## Index Structures

### Containment Index (Whereabouts)

```python
@dataclass
class GameState:
    # Bidirectional containment index
    _entities_at: Dict[str, Set[str]] = field(default_factory=dict)  # where_id → set(entity_ids)
    _entity_where: Dict[str, str] = field(default_factory=dict)      # entity_id → where_id
```

**Index scope:**
- **Keys** in `_entities_at`: Any entity that can serve as a container (locations, doorways, passages, exits, container items)
- **Values** in both indices: Entities with `.where` property (items, actors, exits, doors)
- Built from entities with `hasattr(entity, 'where')` or equivalent `.location` property
- Passages and doorways are **keys only** (containers without being contained)

### Connection Index

```python
@dataclass
class GameState:
    # Symmetric connection index
    _connected_to: Dict[str, Set[str]] = field(default_factory=dict)  # entity_id → set(connected_entity_ids)
```

**Index semantics:**
- Connection index is **symmetric**: adding a connection A→B automatically adds B→A
- Built from entity `.connections` lists at load time (exits, doorways, passages)
- Index is **derived**, not stored in game_state.json
- Validation ensures symmetry: if A→B then B→A must be true

**Index scope:**
- Entities with `.connections` property: Exits, doorways, passages
- Future: Any entity type that participates in peer-to-peer relationships

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

## LLM Integration Details

### Exit Serialization for LLM Context

**What changes**: Exit entities are serialized into the LLM parser context just like items and actors.

**Format**:
```python
def build_parser_context(self, actor_id: ActorId = ActorId("player")):
    # ... existing code for items, actors ...

    # Add exits from current location
    location = self.get_entity_where(actor_id)
    exits_here = self.get_entities_at(location, entity_type="exit")

    context["exits"] = [
        {
            "id": exit.id,
            "name": exit.name,
            "direction": exit.direction if hasattr(exit, 'direction') else None,
            "description": exit.description,
            "adjectives": exit.adjectives
        }
        for exit in exits_here
    ]
```

**Player experience**: Commands like "enter the dark opening" will match exit descriptions, not just directions.

### Vocabulary Generation Changes

**Direction verbs**: Initially unchanged - "go", "enter", "exit" remain as verbs.

**Direction vocabulary**: Initially unchanged - "north", "south" etc. remain as direction category.

**Future evolution**: After Phase 6 completes, direction words could migrate to:
- Exit synonyms: `exit_forest_north.synonyms = ["north"]`
- Exit adjectives: `exit_forest_north.adjectives = ["northern"]`

This would eliminate the direction vocabulary category entirely. Deferred until after migration completes.

### Parser Matching Strategy

**LLM output unchanged**: Parser still returns `{"verb": "go", "object": "exit_forest_north"}`.

**Match priority** (handled by LLM, not code):
1. Exact name match: "cave entrance" → exit with `name: "cave entrance"`
2. Direction match: "north" → exit with `direction: "north"`
3. Synonym match: "north" → exit with `"north"` in `.synonyms` (future)
4. Description match: "dark opening" → exit with `description` containing those words

**Backward compatibility**: Existing "go north" commands continue to work identically.

## Exit ID Convention

**Convention-based IDs**: `exit_{location_id}_{direction}`

Examples:
- `exit_forest_north` - north exit from forest
- `exit_cave_south` - south exit from cave (pairs with forest_north)

**Migration requirements:**
- Tool must know opposite direction mappings: north↔south, east↔west, up↔down, ne↔sw, etc.
- Tool creates paired exits with reciprocal IDs
- Future: non-directional exits (portals) will use different ID patterns (e.g., `exit_forest_portal`)

**Validation:**
- Each exit in `.connections` list must reference an existing exit ID
- Connection graph must be symmetric (enforced at load time)

## Default Semantics and Authoring Invariants

**Strong defaults**: Initial implementation enforces strict invariants with validation:

1. **Paired exits are required**: Every exit must have exactly one connection to its paired exit
2. **Symmetric connections**: If A→B in `.connections`, then B→A must exist
3. **One direction per exit**: Each exit has exactly one direction (initially)
4. **Fixed doorway/passage structure**: Doorways can only contain doors; passages cannot contain entities

**No override fields initially**: Authors cannot deviate from these defaults. Validation enforces the invariants.

**Future extensibility**: Optional fields will be added later to support:
- One-way exits (`one_way: true`)
- Multi-destination portals (`.connections` with >1 entry)
- Directionless exits (portal, hidden passage)
- Mutable doorway/passage contents

**Authoring burden unchanged**: Despite new entity model, authors still specify source, destination, direction - same as current format. Migration tool generates the paired exits automatically.

## Invariants and Validation

### Core Invariants

**1. Read-only `.location`/`.where` property**
- ONLY `set_entity_where()` may mutate `.location` (or `.where` alias)
- Direct assignment `entity.location = "new_place"` is forbidden
- Enforced by: Code review, future linting rule
- Rationale: Ensures indices stay synchronized with entity state

**2. Removed entities excluded from indices**
- Entities with `.location` starting with `"__"` are not indexed
- Example: `entity.location = "__consumed_by_player__"` removes from `_entities_at` and `_entity_where`
- Check in `_build_whereabouts_index()` and `set_entity_where()`
- Rationale: Prevents removed entities from appearing in queries

**3. Door location must be doorway**
- Validation: `if entity.type == "door": assert entity.location.startswith("doorway_")`
- Checked during: State loading (Phase 4+)
- Rationale: Doors live in doorways, not locations

**4. Symmetric connections**
- Validation: `if A in _connected_to[B]: assert B in _connected_to[A]`
- Checked during: Index building at load time
- Rationale: Connections are bidirectional - if you can go A→B, you can go B→A

**5. Exit connections reference existing entities**
- Validation: `for conn in exit.connections: assert conn in all_entity_ids`
- Checked during: State loading (Phase 5+)
- Rationale: Prevents dangling references

### Validation Strategy

**Load-time validation** (fail fast):
- Build indices from entity data
- Check symmetric connection constraint
- Validate door locations are doorways
- Fail with detailed error message if invariants violated

**Debug mode consistency checks** (development only):
- After every `set_entity_where()` call: assert `entity.location == _entity_where[entity.id]`
- After every `add_connection()`: assert symmetry
- Enabled via `--debug` flag or environment variable
- Performance: Only in dev builds, not production

**Runtime validation** (minimal):
- `set_entity_where()`: Check that `new_where` exists as a container
- `add_connection()`: Check that both entities exist
- Rationale: Prevent obviously invalid operations, but trust internal code

### Error Reporting

**Load-time errors** (fail loudly):
```python
raise ValueError(
    f"Connection symmetry violation: "
    f"{entity_a} → {entity_b} exists but {entity_b} → {entity_a} does not"
)
```

**Debug mode errors** (assert):
```python
assert entity.location == self._entity_where[entity.id], \
    f"Index out of sync: {entity.id}.location={entity.location} but index says {self._entity_where[entity.id]}"
```

**Runtime errors** (minimal):
```python
if new_where not in self._entities_at:
    raise ValueError(f"Cannot move {entity_id} to non-existent container {new_where}")
```

## Migration Stability

### Deterministic ID Generation

**Requirement**: Generated exit IDs must be stable across re-runs of migration tool.

**Strategy**:
- Use convention-based naming: `exit_{source_location}_{direction}`
- Paired exit IDs derived from opposite direction: `exit_{dest_location}_{opposite_direction}`
- Doorway IDs use content hash: `doorway_{hash(sorted([exit_a, exit_b]))}`
- Passage IDs use location and direction: `passage_{source_location}_{direction}`

**Testing**: Run migration twice, diff the outputs - should be identical.

### Canonical Ordering

**Lists in JSON**: All entity lists serialized in sorted order by ID.

**Why**: Stable diffs, easier code review of migrated files.

**Implementation**:
```python
game_state["exits"] = sorted(exits, key=lambda e: e["id"])
game_state["doorways"] = sorted(doorways, key=lambda d: d["id"])
```

### Save File Compatibility

**Breaking changes acceptable**: During Phases 1-7, old save files will not load with new code.

**Migration tool for saves**: After Phase 7 completes, create `tools/migrate_saves.py` to update old save files.

**No backward compatibility in code**: New code only supports new format. Conversion is external.

**Rationale**: Clean separation of concerns - migration is one-time, runtime code is simple.

**User impact**: After migration, players must start new games or run migration tool on their saves.

## Migration Strategy

**Two-phase approach**: Containment index migration (Phases 1-2) is separate from and precedes exit/connection migration (Phases 3-7).

**Phase 1-2 will be completed and tested thoroughly** (including walkthroughs and manual play) before starting Phase 3.

**Exit migration (Phases 3-7) will be done on a separate branch** to allow careful testing and iteration without blocking other work.

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

3. **Bidirectional exit authoring**: Auto-generation by migration tool
   - Migration tool creates paired exits automatically from `Location.exits` entries
   - Each direction becomes its own Exit entity
   - Reduces boilerplate and errors for common case
   - **Principle**: Authoring burden unchanged - still specify source, destination, direction
   - Future: Authors can write both exits explicitly for asymmetric cases (after override fields are added)

4. **Connection index persistence**: Rebuild from entity data at load time
   - Minimal data in game_state.json is source of truth
   - Connections derived from per-entity `.connections` lists
   - Index is computed, not stored
   - Symmetric constraint validated at load time

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

## Open Questions (Deferred to Future Phases)

1. **Non-default exit cases**: One-way exits, asymmetric properties - authoring format for overrides
   - Deferred until after migration completes
   - Will add optional override fields (e.g., `one_way: true`) when use cases emerge
   - Initial strict validation ensures consistency

2. **Multi-way passages**: Could a passage connect more than two exits?
   - Deferred - current model assumes two endpoints
   - Structure supports it (`.connections` is a list), semantics will be added later

3. **Entity type enumeration**: Complete list of entities participating in indices
   - Will be discovered during Phase 1 implementation
   - Core types are clear: Items, Actors, Locations, (future: Exits, Doors, Doorways, Passages)
   - Missing types will be found via bugs and added incrementally

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

**Phase 1-2 (Containment Index):**
1. All unit tests pass
2. Walkthroughs complete successfully
3. Manual playtesting confirms no regressions
4. Myconid Sanctuary bug is fixed (items are takeable)
5. No performance regression

**Phase 3-7 (Exit/Connection Migration):**
1. All exits traversable by direction, name, description
2. Doors work correctly from both sides
3. All game content migrated to new format
4. Validation catches symmetric connection violations
5. LLM parser matches exits as entities
