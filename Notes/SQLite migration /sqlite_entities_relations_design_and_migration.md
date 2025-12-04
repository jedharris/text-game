# Unified Entities + Relations SQLite Design and Migration Plan

This document describes a **unified, generic `Entity` + `Relation` model** for your text adventure engine, backed by SQLite. It replaces the current type-specific collections (`Location`, `Item`, `Actor`, `Lock`, `ExitDescriptor`) with a more uniform graph model, while preserving the overall engine architecture and integrating cleanly with the new **in-room spatial structure**.

The document is split into:

1. Goals & current situation  
2. Target conceptual model (entities & relations)  
3. SQLite schema design  
4. Mapping from old model to new model  
5. Runtime API & engine integration  
6. Migration strategy (step-by-step)  
7. Future evolution & open questions  

---

## 1. Goals & Current Situation

### 1.1 Goals

- Move toward a **uniform world model**:
  - Everything that “exists” is an `Entity`.
  - Relationships between things are explicit `Relation` records.
- Remove technical debt caused by rigid `Location` / `Item` / `Actor` separations.
- Preserve:
  - the **Python engine architecture** (behaviors, StateAccessor, game loop),
  - the **JSON-friendly properties pattern**, and
  - the new **in-room spatial structure**.
- Gain:
  - a clean SQLite-backed world graph,
  - easier tooling and introspection,
  - flexibility for future systems (magic, factions, etc.).

### 1.2 Current Model (Simplified)

- `GameState` holds:
  - `locations: Dict[str, Location]`
  - `items: Dict[str, Item]`
  - `actors: Dict[str, Actor]`
  - `locks: Dict[str, Lock]`
  - `exits: Dict[str, ExitDescriptor]`
- Each dataclass has:
  - fixed fields (id, name, description, location, etc.)
  - flexible `properties: Dict[str, Any]`
- In-room spatial model (planned):
  - `Location.properties["spatial"]`: zones, walls, attachments.
  - `Actor.properties["zone"]`, `["anchor"]`.
  - `Item.properties["zone"]`, `["attached_to_wall"]`.

---

## 2. Target Conceptual Model: Entities & Relations

### 2.1 Entity

Everything in the game world that:

- can be referenced by id,
- can have properties,
- might participate in relationships,

…is an **Entity**.

Examples:

- “The Grand Hall” (a location)
- “Bronze key” (an item)
- “Palace guard” (an actor)
- “North wall” (a wall)
- “Dais center” (a zone)
- “Exit from Hall to Corridor” (an exit entity)
- “Lock on the iron gate” (a lock entity)
- “Player character” (the player entity)

Each entity has:

- `id`: globally unique string
- `kind`: type tag (`location`, `item`, `actor`, `lock`, `exit`, `zone`, `wall`, etc.)
- `name`: human-readable name
- `description`: optional description
- `properties`: JSON blob for flexible data

Optional common fields:

- `parent_id`: for containment or hierarchical organization (e.g., a zone’s parent is a location).
- `is_static`: distinguishes world-definition entities from purely runtime constructs.

### 2.2 Relation

A **Relation** expresses a directed edge in the world graph:

> **(subject) –[type]–> (object)**

with an optional `meta_json` for extra data.

Examples:

- `(player, IN_LOCATION, grand_hall)`
- `(item_bronze_key, IN_INVENTORY, player)`
- `(item_sword, IN_ZONE, zone_by_throne)`
- `(zone_by_throne, PART_OF, grand_hall)`
- `(north_wall, PART_OF, grand_hall)`
- `(banner_1, ATTACHED_TO, north_wall)`
- `(exit_hall_north, LINK_FROM, grand_hall)`
- `(exit_hall_north, LINK_TO, corridor)`
- `(exit_hall_north, HAS_LOCK, lock_iron_gate)`
- `(lock_iron_gate, UNLOCKED_BY, item_bronze_key)`
- `(player, ANCHORED_ON, item_throne)`
- `(guard_1, FACING, player)`

Key aspects:

- `type` is a controlled vocabulary (e.g., `IN_LOCATION`, `IN_ZONE`, `IN_INVENTORY`, `PART_OF`, `ATTACHED_TO`, `LINK_FROM`, `LINK_TO`).
- `meta_json` can store:
  - direction (`"north"`, `"south"`),
  - distances,
  - temporary flags,
  - etc.

This model subsumes:

- location membership,
- containment,
- exits & locks,
- spatial structure,
- NPC relationships, etc.

---

## 3. SQLite Schema Design (Entities + Relations)

### 3.1 Entities Table

```sql
CREATE TABLE entities (
    id          TEXT PRIMARY KEY,        -- e.g., "loc:grand_hall", "item:bronze_key"
    kind        TEXT NOT NULL,          -- "location", "item", "actor", "zone", "wall", "exit", "lock", ...
    name        TEXT NOT NULL,
    description TEXT,
    parent_id   TEXT,                   -- optional hierarchy (e.g., zone parent is location)
    is_static   INTEGER NOT NULL DEFAULT 1,   -- 1 = defined in content, 0 = runtime-only or instance
    properties  TEXT,                   -- JSON blob
    FOREIGN KEY(parent_id) REFERENCES entities(id)
);
```

### 3.2 Relations Table

```sql
CREATE TABLE relations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id  TEXT NOT NULL,
    type        TEXT NOT NULL,          -- "IN_LOCATION", "IN_ZONE", "IN_INVENTORY", ...
    object_id   TEXT NOT NULL,
    meta_json   TEXT,                   -- arbitrary extra data (direction, strength, flags)
    is_static   INTEGER NOT NULL DEFAULT 0,  -- 1 = content relation, 0 = purely runtime
    FOREIGN KEY(subject_id) REFERENCES entities(id),
    FOREIGN KEY(object_id) REFERENCES entities(id)
);
```

### 3.3 Indexes & Constraints

To keep queries fast and invariants safe, create indexes:

```sql
CREATE INDEX idx_rel_subject_type ON relations(subject_id, type);
CREATE INDEX idx_rel_object_type  ON relations(object_id, type);
CREATE INDEX idx_rel_type         ON relations(type);
```

Optional invariants (enforced via your code or via partial unique indexes):

- Each entity can have at most **one** `IN_LOCATION` relation.
- Each entity can have at most **one** `IN_ZONE` relation.
- A `zone` entity must have a `PART_OF` relation to a `location`.
- A `wall` entity must have a `PART_OF` relation to a `location`.

You can encode those as:

```sql
-- Example: ensure at most one IN_LOCATION per subject (SQLite doesn't directly support WHERE in UNIQUE in older versions, so you may enforce via triggers or app logic).
```

For now, plan to enforce these invariants in Python.

---

## 4. Mapping from Old Model to New Model

### 4.1 Location → Entity + Relations

**Old:**

```python
Location(id, name, description, exits, items, properties, behaviors)
```

**New:**

- Create an entity:
  - `id = "loc:<old_id>"`
  - `kind = "location"`
  - `name`, `description` taken directly
  - `properties` includes:
    - `spatial` block (zones, walls, attachments) if present
    - any other existing location properties

- Zones & walls:
  - Create separate `zone` and `wall` entities **only if** you want them as first-class.
  - Otherwise, keep them as JSON in `properties["spatial"]` (intermediate step).

Example as separate entities:

- `entity id = "zone:grand_hall:center"`, `kind = "zone"`, `parent_id = "loc:grand_hall"`
- `entity id = "wall:grand_hall:north"`, `kind = "wall"`, `parent_id = "loc:grand_hall"`

Relations:

- `(zone:grand_hall:center, PART_OF, loc:grand_hall)`
- `(wall:grand_hall:north, PART_OF, loc:grand_hall)`
- `(zone:grand_hall:center, ADJACENT_TO, zone:grand_hall:by_throne)` – adjacency
- `(zone:grand_hall:by_throne, FACES, wall:grand_hall:north)` – orientation
- `(item_banner, ATTACHED_TO, wall:grand_hall:north)`

### 4.2 Item → Entity + Relations

**Old:**

```python
Item(id, name, description, location, properties, behaviors)
```

**New:**

- Entity:
  - `id = "item:<old_id>"`
  - `kind = "item"`
  - `name`, `description` from old item
  - `properties` contains `portable`, `container`, etc., and any item-specific data.

- Location/container/zone membership:
  - If item’s `location` is a location id:
    - `(item:..., IN_LOCATION, loc:...)`
  - If item is inside another item (container):
    - `(item:..., IN_INVENTORY, item:container_id)` or more general `IN_CONTAINER`.
  - If item has a `zone`:
    - `(item:..., IN_ZONE, zone:grand_hall:center)`

- Wall attachments:
  - If `attached_to_wall` flag exists:
    - `(item:banner, ATTACHED_TO, wall:grand_hall:north)`

### 4.3 Actor → Entity + Relations

**Old:**

```python
Actor(id, name, description, location, inventory, properties, behaviors)
```

**New:**

- Entity:
  - `id = "actor:<old_id>"`
  - `kind = "actor"`
  - `properties` includes `stats`, `faction`, etc.

Relations:

- `(actor:..., IN_LOCATION, loc:...)`
- `(actor:..., IN_ZONE, zone:...)` if using in-room spatial positioning
- For inventory contents:
  - For each carried item: `(item:..., IN_INVENTORY, actor:...)`
- For anchor:
  - `(actor:..., ANCHORED_ON, item:throne)` rather than `anchor` property.
- For facing:
  - `(actor:guard_1, FACING, actor:player)` or `FACING, wall:grand_hall:north`.

### 4.4 ExitDescriptor → Entity + Relations

**Old:**

```python
ExitDescriptor(id, from_location, to_location, direction, lock_id, properties)
```

**New:**

- Entity:
  - `id = "exit:<old_id>"`
  - `kind = "exit"`
  - `properties` may include description, flags (e.g., visible/hidden) and any existing extra data.

Relations:

- `(exit:..., LINK_FROM, loc:from_id)`
- `(exit:..., LINK_TO, loc:to_id)`
- Direction is stored in `meta_json`:
  - Example: `(exit:..., DIRECTION_OF, loc:from_id)` with `{ "direction": "north" }`
  - Or simply in `exit.properties["direction"]`.
- If locked:
  - `(exit:..., HAS_LOCK, lock:...)`

### 4.5 Lock → Entity + Relations

**Old:**

```python
Lock(id, is_locked, properties)
```

**New:**

- Entity:
  - `id = "lock:<old_id>"`
  - `kind = "lock"`
  - `properties["locked"] = true/false`
  - `properties` can also include icon, description, etc.

Relations:

- `(exit:..., HAS_LOCK, lock:...)`
- `(lock:..., UNLOCKED_BY, item:key_id)` if you want explicit key-to-lock relationships.

---

## 5. Runtime API & Engine Integration

### 5.1 GameStateStore Becomes Entity/Relation Store

Instead of storing typed dicts on `GameState`, the core store becomes:

- `EntityStore` interface (backed by SQLite).
- `RelationStore` interface (also backed by SQLite, or combined).

Example Python protocol:

```python
class WorldStore(Protocol):
    # Entities
    def get_entity(self, entity_id: str) -> Entity: ...
    def save_entity(self, entity: Entity): ...
    def find_entities(self, kind: Optional[str] = None, **filters) -> List[Entity]: ...

    # Relations
    def get_relations(self, subject_id: Optional[str] = None,
                      type: Optional[str] = None,
                      object_id: Optional[str] = None) -> List[Relation]: ...
    def add_relation(self, relation: Relation): ...
    def remove_relation(self, relation_id: int): ...
```

`StateAccessor` then becomes a **semantic adapter**:

- `get_location(...)` becomes:
  - Find entity with `kind="location"` and given id.
- `get_items_in_location(loc_id)`:
  - Find relations `(item_x, IN_LOCATION, loc:loc_id)`.

### 5.2 Behavior Layer (Almost) Unchanged

Behaviors should still operate with high-level concepts:

- “Get the location the actor is in”
- “Get items visible to actor”
- “Move actor from one location to another”
- “Check if exit is locked”

But under the hood, these calls use:

- `WorldStore.get_entity` + `get_relations` instead of `GameState.locations/items/actors`.

---

## 6. Migration Strategy (Step-by-Step)

### Step 0 – Define `Entity` and `Relation` Core Classes

- Add dataclasses in Python:

```python
@dataclass
class Entity:
    id: str
    kind: str
    name: str
    description: str = ""
    parent_id: Optional[str] = None
    is_static: bool = True
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Relation:
    id: Optional[int]  # DB-assigned
    subject_id: str
    type: str
    object_id: str
    meta: Dict[str, Any] = field(default_factory=dict)
    is_static: bool = False
```

### Step 1 – Add WorldStore Interface & SQLiteWorldStore

- Implement CRUD for entities and relations in SQLite.
- Start with a simple mapping:
  - `Entity` ↔ `entities` table
  - `Relation` ↔ `relations` table

### Step 2 – Add “Bridge Layer” for Old APIs

- Add helper methods in `StateAccessor` like:

```python
def get_location(self, location_id: str) -> Entity: ...
def get_item(self, item_id: str) -> Entity: ...
def get_actor(self, actor_id: str) -> Entity: ...
```

- Initially, these can be backed by either:
  - The old `GameState` (for JSON mode), or
  - The new `WorldStore` (for SQLite mode).

### Step 3 – Migration Script JSON → Entities + Relations

Write an offline script that:

1. Loads existing JSON game state.
2. For each `Location`:
   - Creates a `location` entity, plus optional `zone`/`wall` entities.
3. For each `Item`:
   - Creates an `item` entity.
   - Adds `IN_LOCATION` or `IN_INVENTORY` relations.
4. For each `Actor`:
   - Creates an `actor` entity.
   - Adds `IN_LOCATION`, `IN_ZONE`, `IN_INVENTORY` relations.
5. For each `ExitDescriptor`:
   - Creates an `exit` entity.
   - Adds `LINK_FROM`, `LINK_TO`, `HAS_LOCK` relations.
6. For each `Lock`:
   - Creates `lock` entity.
   - Adds `UNLOCKED_BY` or similar key relations.

### Step 4 – Switch Engine to Read from `WorldStore`

- Modify initialization to:
  - Open SQLite DB
  - Create `WorldStore` (e.g., `SqliteWorldStore`)
  - Construct `StateAccessor` using `WorldStore`
- Update behaviors to use the new `StateAccessor` methods for:
  - Getting locations, items, actors
  - Getting exits for a location
  - Checking locks, etc.

### Step 5 – Decommission Type-Specific Collections

Once the engine is fully reading/writing via `WorldStore`:

- Remove or reduce `GameState.locations`, `items`, `actors`, etc.
- Or keep a small `GameState` only for global flags, time counters, etc., while all world content lives in entities/relations.

---

## 7. Future Evolution & Open Questions

### 7.1 Normalizing Spatial Structure

Initially, you can keep your spatial model in `properties["spatial"]` for `location` entities. Later:

- Promote `zones` and `walls` to first-class entities, with:
  - `kind = "zone"` / `"wall"`
  - `PART_OF` and `ADJACENT_TO` relations.

### 7.2 High-Level Query Utilities

To keep behavior code clean, you can build a small “graph query” layer:

- `get_player_location()`
- `get_entities_in_location(loc_id)`
- `get_entities_in_zone(zone_id)`
- `get_exits_from_location(loc_id)`
- `get_items_attached_to_wall(wall_id)`

All implemented via `WorldStore` queries on `entities` and `relations`.

### 7.3 Static vs Dynamic Worlds

You can differentiate:

- Static “world definition” entities (`is_static = 1`).
- Dynamic runtime entities (`is_static = 0`), created or destroyed during play.

This sets you up nicely for:

- resets,
- cloning instances,
- multi-run scenario generation.

---

**End of Document**
