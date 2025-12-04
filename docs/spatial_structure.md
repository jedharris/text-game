# Spatial Structure Design - Object-Relative Positioning with Parts

## Overview

This document describes how to add **spatial awareness** to the text adventure engine through **object-relative positioning using Part entities**. The design enables rich spatial interactions while maintaining the framework's philosophy of simplicity, property-based extensibility, and minimal authoring burden.

**Key principle:** Spatial relationships are expressed through a new entity type called **Part**, which represents spatial components of other entities (rooms, items, actors). Parts have unique IDs and work seamlessly with the existing vocabulary and behavior systems.

---

# 1. Design Goals

## Primary Goals

1. **Enable spatial interactions** - Players can be near objects, behind objects, at specific positions
2. **Implicit positioning** - Most spatial changes happen automatically during interaction
3. **Entity uniformity** - All referenceable spatial features are entities with IDs
4. **Minimal authoring burden** - Authors create parts only when needed for gameplay
5. **Backward compatible** - Existing games work unchanged
6. **Property-based** - All spatial data lives in entity properties
7. **Progressive disclosure** - Simple games ignore parts, complex games use them

## Non-Goals

- Zone-based movement systems (too complex)
- XY coordinate grids (wrong abstraction)
- Pathfinding algorithms (unnecessary for IF)
- Parts as a requirement (only create when needed)

---

# 2. The Part Entity

## 2.1 Definition

**Part** is a new entity type representing a spatial component of another entity. Parts:

- Have unique IDs (like all entities)
- Have names that can be referenced in commands
- Always belong to a parent entity (`part_of` property)
- Can have properties and behaviors
- Can be locations for items or actors
- Cannot be portable
- Participate in normal vocabulary system

## 2.2 Part Entity Specification

```python
class Part:
    """A spatial component of another entity."""
    id: str                          # Unique identifier (e.g., "part_north_wall")
    name: str                        # Display name (e.g., "north wall")
    part_of: str                     # Parent entity ID
    properties: Dict[str, Any]       # Flexible properties dict
    behaviors: List[str]             # Behavior module paths
    llm_context: Optional[str]       # Description for LLM narration
```

### Core Constraints

- **`part_of` is required** - Every part must have a parent entity (room, item, container, actor)
- **Parts cannot be portable** - They're spatial components, not independent objects
- **Parts can be locations for items** - Items can have `location = part_id`
- **Actors use both location and focused_on** - Actors use `location` to track which room they're in (always a location_id), and `properties.focused_on` to track position within that room (can be item, container, part, or actor ID)
- **Parts use vocabulary system** - Normal WordEntry matching, no special string handling

### Storage in GameState

Parts live at the top level of GameState:

```python
class GameState:
    locations: Dict[str, Location]
    items: Dict[str, Item]
    containers: Dict[str, Container]
    actors: Dict[str, Actor]
    parts: Dict[str, Part]           # New collection
```

## 2.3 Example Parts

### Room Wall Parts

```json
{
  "id": "part_throne_north_wall",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_throne_room",
  "properties": {
    "material": "stone",
    "description": "Cold stone, damp to the touch."
  }
}
```

### Multi-Sided Object Parts

```json
{
  "id": "part_bench_left",
  "entity_type": "part",
  "name": "left side of bench",
  "part_of": "item_bench",
  "properties": {
    "description": "Grinding tools are arranged at this end of the bench."
  }
}
```

### Container Parts

```json
{
  "id": "part_cabinet_back",
  "entity_type": "part",
  "name": "back of cabinet",
  "part_of": "container_cabinet",
  "properties": {
    "description": "The back panel looks slightly different from the rest."
  },
  "behaviors": ["behaviors.secret_compartment"]
}
```

---

# 3. Core Concepts

## 3.1 Two Positioning Models

The system supports two complementary models:

### Implicit Positioning (Automatic)

The engine automatically tracks what the player is focused on during interactions:

```
> examine desk
(Player implicitly moves near desk)
You move closer to the desk. It's a heavy oak desk...

> open drawer
(Already near desk - drawer is part of desk)
You pull open the drawer, revealing...

> examine throne
(Player implicitly moves near throne, away from desk)
You step toward the throne. The carved wood...
```

**No explicit movement commands needed.** The game feels natural and flows smoothly.

### Explicit Positioning (When Needed)

For puzzles requiring precise positioning, authors can require explicit positioning:

```
> grind herbs
You need to be at the left side of the bench where the mortar is.

> approach left side of bench
You move to the left end of the bench.

> grind herbs
You crush the dried leaves into a fine powder.
```

**Use sparingly.** Most games should rely on implicit positioning.

## 3.2 Spatial Properties

### On Actors

```json
{
  "id": "player",
  "name": "Adventurer",
  "properties": {
    "focused_on": "part_bench_left",
    "posture": null
  }
}
```

**Spatial Property Meanings:**

- **`focused_on`** (Actor) - What entity (item, container, part) the actor is currently near/interacting with. Note: Actors always have `location = location_id` (which room they're in). The `focused_on` property tracks their position WITHIN that room.
- **`posture`** (Actor) - Optional mode describing how the actor is positioned at focused_on:
  - `null` or omitted: Normal positioning (examining, interacting)
  - `"cover"`: Taking cover behind the entity (combat/stealth)
  - `"concealed"`: Hiding inside/within the entity
  - `"climbing"`: Climbing on the entity (tree, ladder, wall)
  - Custom postures as needed by game-specific behaviors

### On Items/Containers

```json
{
  "id": "item_bench",
  "name": "bench",
  "properties": {
    "portable": false,
    "provides_cover": true,
    "interaction_distance": "near"
  }
}
```

**Spatial Property Meanings:**

- **`provides_cover`** (Item/Container/Part) - Whether this can be used for cover (combat/stealth)
- **`interaction_distance`** (Item/Container/Part) - "near" or "any" - how close player must be

### Interaction Distance Values

Only two values to keep system simple:

- **`"any"`** - Can interact from anywhere in the location. No implicit positioning. This is the default.
- **`"near"`** - Must be near the entity. Triggers implicit positioning on interaction.

**Default behavior:**
- All entities default to `interaction_distance: "any"` unless explicitly set otherwise
- This provides backward compatibility and predictable behavior
- Set `interaction_distance: "near"` on specific entities when you want implicit positioning

**When to use "near":**
- Items in spatial rooms where position matters for realism
- Small/detailed objects that require close examination
- Interactive objects where player should be positioned nearby

**Implementation:** Simple property lookup with `"any"` fallback. No complex room-based derivation needed.

Additional distance requirements can be added later if use cases justify them.

## 3.3 Items Located at Parts

Items can be located at a Part:

```json
{
  "id": "item_tapestry",
  "name": "tapestry",
  "location": "part_throne_north_wall",
  "properties": {
    "portable": false,
    "removable": true
  }
}
```

This creates a clear hierarchy:
- Room contains parts
- Parts contain items
- Parser resolves "examine north wall" → finds part_throne_north_wall → lists items at that part

---

# 4. Core Behaviors

## 4.1 Implicit Positioning in Core Behaviors

Core interaction verbs automatically update player focus:

### Examine Behavior Enhancement

```python
def handle_examine(accessor, action):
    """Enhanced examine with implicit positioning."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)
    location = accessor.get_current_location(actor_id)

    # ... find entity (item, container, part, actor) ...

    # Check interaction distance (defaults to "any")
    distance = entity.properties.get("interaction_distance", "any")

    if distance == "any":
        # Can examine from anywhere - don't move
        prefix = ""
    elif distance == "near":
        # Move player near entity
        old_focus = actor.properties.get("focused_on")
        if old_focus != entity.id:
            actor.properties["focused_on"] = entity.id
            prefix = f"You move closer to the {entity.name}. "
        else:
            prefix = ""

    # ... rest of examine logic ...
    return EventResult(success=True, message=prefix + description)
```

### Take/Drop/Open/Close Enhancement

Similar logic - automatically position player near target when `interaction_distance` is "near".

## 4.2 Explicit Positioning Commands

Add `approach` verb for explicit positioning:

### Basic Approach

```python
def handle_approach(accessor, action):
    """Move player near an object or part."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # ... find target entity (item, container, part, actor) ...

    # Ensure target is accessible from current location
    if not _is_accessible(accessor, actor, entity):
        return EventResult(
            success=False,
            message=f"You can't reach the {entity.name} from here."
        )

    # Update player focus
    old_focus = actor.properties.get("focused_on")
    actor.properties["focused_on"] = entity.id

    if old_focus == entity.id:
        message = f"You're already at the {entity.name}."
    else:
        message = f"You move to the {entity.name}."

    return EventResult(success=True, message=message,
                      data={"id": entity.id, "name": entity.name})

def _is_accessible(accessor, actor, target):
    """Check if target is reachable from actor's location."""
    # If target is an item/container/actor, check same location
    if hasattr(target, 'location'):
        return target.location == actor.location

    # If target is a part, check parent is in same location
    if hasattr(target, 'part_of'):
        parent = accessor.get_entity(target.part_of)
        if hasattr(parent, 'location'):
            return parent.location == actor.location
        # Parent is a location - check actor is in that location
        return parent.id == actor.location

    return False
```

### Take Cover

For combat/stealth:

```python
def handle_take_cover(accessor, action):
    """Take cover behind an object or part."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # ... find cover entity ...

    # Verify entity provides cover
    if not entity.properties.get("provides_cover"):
        return EventResult(
            success=False,
            message=f"The {entity.name} doesn't provide cover."
        )

    # Set cover state
    actor.properties["focused_on"] = entity.id
    actor.properties["posture"] = "cover"

    message = f"You take cover behind the {entity.name}."
    return EventResult(success=True, message=message)
```

### Posture Example - Concealment

The `posture` property enables rich gameplay variations:

```python
def handle_hide_in(accessor, action):
    """Hide inside a container or behind curtains."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # ... find hiding spot entity ...

    # Check if entity allows concealment
    if not entity.properties.get("allows_concealment"):
        return EventResult(
            success=False,
            message=f"You can't hide in the {entity.name}."
        )

    # Set concealed state
    actor.properties["focused_on"] = entity.id
    actor.properties["posture"] = "concealed"

    message = f"You squeeze into the {entity.name} and remain very still."
    return EventResult(success=True, message=message)
```

**Gameplay with posture:**

```
> hide in wardrobe
You squeeze into the wardrobe and remain very still.

> (Guard enters room)
The guard looks around suspiciously but doesn't spot you.

> leave wardrobe
You step out of the wardrobe.
```

The `posture = "concealed"` signals to NPC behaviors that the player is hidden, enabling stealth gameplay.

### Posture Example - Climbing

Climbing provides clear mechanical differences that justify a mode:

```python
def handle_climb(accessor, action):
    """Climb a tree, ladder, or wall."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # ... find climbable entity ...

    # Check if entity is climbable
    if not entity.properties.get("climbable"):
        return EventResult(
            success=False,
            message=f"You can't climb the {entity.name}."
        )

    # Set climbing posture
    actor.properties["focused_on"] = entity.id
    actor.properties["posture"] = "climbing"

    message = f"You climb up the {entity.name}."
    return EventResult(success=True, message=message)
```

**Gameplay with climbing posture:**

```
> climb tree
You climb up the tree.

> pick apple
You pluck a ripe apple from the branch.

> (Wolf enters clearing)
The wolf circles below but can't reach you in the tree.

> climb down
You climb back down to the ground.
```

**Why posture works for these use cases:**

1. **Mutually exclusive states** - Can't be both "in cover" and "climbing" simultaneously
2. **Clear mechanical effects** - Each posture changes available actions and NPC behavior
3. **Natural state transitions** - Moving away clears the posture automatically
4. **Single source of truth** - One property tracks "how you're positioned"

The pattern extends naturally to other postures like `"operating"` (using a control panel), `"mounted"` (on horseback), or domain-specific states.

## 4.3 Part-Specific Behaviors

### Examining Parts

Parts are examined like any other entity. The core examine behavior finds the part by ID:

```python
def handle_examine(accessor, action):
    """Enhanced examine handles all entity types including parts."""
    obj_entry = action.get("object")
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)
    location_id = actor.location

    # Try to find entity - checks items, containers, actors, AND parts
    entity = _find_entity_in_location(accessor, location_id, obj_entry)

    if not entity:
        return EventResult(
            success=False,
            message=f"You don't see {obj_entry.word} here."
        )

    # If entity is a part, also list items at that part
    description = entity.properties.get("description", f"You see the {entity.name}.")

    if hasattr(entity, 'part_of'):  # It's a part
        items_at_part = accessor.get_items_at_location(entity.id)
        if items_at_part:
            item_names = ", ".join(f"a {item.name}" for item in items_at_part)
            description += f" At the {entity.name}: {item_names}."

    return EventResult(success=True, message=description)
```

### Universal Surface Fallback

**Problem:** Every room has a ceiling and floor, but most rooms won't have ceiling/floor parts. Players typing "examine ceiling" or "examine floor" should get a sensible response, not "You don't see ceiling here."

**Solution:** A spatial behavior module (`behaviors/core/spatial.py`) provides vocabulary for universal surfaces and handles fallback responses when no explicit part exists.

**Universal surfaces supported:**
- ceiling
- floor
- ground
- sky
- walls (as a group)

These are defined in the vocabulary system in `behaviors/core/spatial.py`, not hardcoded. Each has a default description that's returned when no explicit part exists.

```python
def handle_examine(accessor, action):
    """Enhanced examine handles all entity types including parts and universal surfaces."""
    obj_entry = action.get("object")
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)
    location_id = actor.location

    # Try to find entity - checks items, containers, actors, AND parts
    entity = _find_entity_in_location(accessor, location_id, obj_entry)

    if entity:
        # Found explicit entity - examine it normally
        description = entity.properties.get("description", f"You see the {entity.name}.")

        if hasattr(entity, 'part_of'):  # It's a part
            items_at_part = accessor.get_items_at_location(entity.id)
            if items_at_part:
                item_names = ", ".join(f"a {item.name}" for item in items_at_part)
                description += f" At the {entity.name}: {item_names}."

        return EventResult(success=True, message=description)

    # Entity not found - check if it's a universal surface
    if _is_universal_surface(obj_entry.word):
        return _examine_universal_surface(accessor, obj_entry.word, location_id)

    # Not found and not universal surface
    return EventResult(
        success=False,
        message=f"You don't see {obj_entry.word} here."
    )

def _is_universal_surface(obj_entry: WordEntry) -> bool:
    """Check if word refers to a universal surface present in every room.

    Universal surface vocabulary is defined in behaviors/core/spatial.py.
    Uses the vocabulary system to identify universal surfaces.
    """
    # Check if word entry matches any universal surface noun in vocabulary
    universal_surfaces = vocabulary.get_universal_surface_nouns()
    return obj_entry.word in universal_surfaces

def _examine_universal_surface(accessor, obj_entry: WordEntry, location_id: str):
    """Provide generic description for universal surfaces without explicit parts.

    Default responses are defined in behaviors/core/spatial.py as part of
    the universal surface vocabulary entries.
    """
    # Get default description from vocabulary
    surface_vocab = vocabulary.get_noun_entry(obj_entry.word)
    default_desc = surface_vocab.get("default_description",
                                      f"Nothing remarkable about the {obj_entry.word}.")

    return EventResult(success=True, message=default_desc)
```

**Simple fallback:** If authors want custom ceiling/floor descriptions, they should create explicit parts. The universal surface fallback provides basic responses to avoid "You don't see ceiling here" errors, nothing more.

**When parts override defaults:**

If a location has an explicit ceiling part, the part is found first and examined normally:

```json
{
  "id": "part_cathedral_ceiling",
  "entity_type": "part",
  "name": "ceiling",
  "part_of": "loc_cathedral",
  "properties": {
    "description": "A magnificent vaulted ceiling with frescoes depicting angels."
  }
}
```

```
> examine ceiling
A magnificent vaulted ceiling with frescoes depicting angels. At the ceiling: a chandelier.
```

The part description takes precedence over the universal surface fallback.

### Removing Items from Parts

When items are located at parts, removal works naturally:

```python
def handle_remove(accessor, action):
    """Remove item from wall/surface (part)."""
    # ... find item ...

    # Check if item is at a part
    if not item.location.startswith("part_"):
        return EventResult(
            success=False,
            message=f"The {item.name} isn't attached to anything."
        )

    part = accessor.get_part(item.location)
    if not item.properties.get("removable", False):
        return EventResult(
            success=False,
            message=f"The {item.name} is permanently attached to the {part.name}."
        )

    # Move to inventory
    item.location = actor_id
    actor.inventory.append(item.id)

    return EventResult(
        success=True,
        message=f"You carefully remove the {item.name} from the {part.name}."
    )
```

---

# 5. Gameplay Examples

## 5.1 Simple Puzzle - Hidden Button

**Scenario:** A button is hidden behind a tapestry on the north wall.

**Implementation:**

```json
{
  "id": "part_throne_north_wall",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_throne_room",
  "properties": {
    "description": "The stone wall is cold and damp."
  }
}
```

```json
{
  "id": "item_tapestry",
  "name": "tapestry",
  "location": "part_throne_north_wall",
  "properties": {
    "portable": false,
    "removable": false,
    "description": "A faded tapestry depicting a great battle.",
    "conceals": "item_button"
  }
}
```

```json
{
  "id": "item_button",
  "name": "button",
  "location": "part_throne_north_wall",
  "properties": {
    "portable": false,
    "states": {
      "hidden": true
    },
    "description": "A small stone button set into the wall."
  }
}
```

**Gameplay:**

```
> look
Throne Room
The stone walls are cold and damp.

You see: throne
On the north wall: tapestry

> examine north wall
The stone wall is cold and damp. At the north wall: a tapestry.

> examine tapestry
(Player automatically moves near tapestry via implicit positioning)
You move closer to the tapestry. A faded tapestry depicting a great battle.

> look behind tapestry
You pull aside the tapestry, revealing a small stone button!

> push button
(Already near wall/button from previous interaction)
You press the button. A grinding sound echoes through the room.
```

**Why this works:**
- Wall is a proper entity (part) with ID and properties
- Items located at part use normal location hierarchy
- Parser finds "north wall" through vocabulary system (no string matching)
- Implicit positioning moves player naturally
- Behaviors can check player's focused_on to enable button push

**Comparison to string-based approach:**
- **Before:** `"attached_to": "north_wall"` (string), string matching to find wall
- **After:** `"location": "part_throne_north_wall"` (entity ID), normal entity resolution

## 5.2 Multi-Sided Object - Alchemy Bench

**Scenario:** A bench with tools on different sides requires positional precision.

**Implementation:**

```json
{
  "id": "item_bench",
  "name": "bench",
  "location": "loc_workshop",
  "properties": {
    "portable": false,
    "interaction_distance": "near",
    "description": "A long wooden work surface for alchemical experiments."
  }
}
```

```json
{
  "id": "part_bench_left",
  "entity_type": "part",
  "name": "left side of bench",
  "part_of": "item_bench",
  "properties": {
    "description": "Grinding tools are arranged at this end."
  }
}
```

```json
{
  "id": "part_bench_center",
  "entity_type": "part",
  "name": "center of bench",
  "part_of": "item_bench",
  "properties": {
    "description": "A spirit burner sits ready for heating."
  }
}
```

```json
{
  "id": "part_bench_right",
  "entity_type": "part",
  "name": "right side of bench",
  "part_of": "item_bench",
  "properties": {
    "description": "Glass flasks and vials are organized here."
  }
}
```

```json
{
  "id": "item_mortar",
  "name": "mortar",
  "location": "part_bench_left",
  "properties": {
    "portable": false,
    "description": "A stone mortar with its pestle."
  }
}
```

**Behavior for position-dependent actions:**

```python
# behaviors/alchemy.py

def handle_grind(accessor, action):
    """Grind herbs in mortar - requires being at left side of bench."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # Check if player has herbs
    herbs = accessor.get_item("item_herbs")
    if herbs.location != actor_id:
        return EventResult(
            success=False,
            message="You need to be holding the herbs."
        )

    # Check if focused on the correct part
    focused = actor.properties.get("focused_on")
    if focused != "part_bench_left":
        return EventResult(
            success=False,
            message="You need to be at the left side of the bench where the mortar is."
        )

    # Perform grinding
    herbs.properties["states"]["ground"] = True
    return EventResult(
        success=True,
        message="You crush the dried herbs into a fine powder using the mortar and pestle."
    )
```

**Gameplay:**

```
> examine bench
You move to the bench. A long wooden work surface for alchemical experiments.

> examine left side of bench
Grinding tools are arranged at this end. At the left side of bench: a mortar.

> grind herbs
You need to be at the left side of the bench where the mortar is.

> approach left side of bench
You move to the left end of the bench.

> grind herbs
You crush the dried herbs into a fine powder using the mortar and pestle.

> approach center of bench
You move to the center of the bench.

> examine center
A spirit burner sits ready for heating.
```

**Why this works:**
- Each side is a proper entity with ID, name, properties
- Player can examine each side independently
- Behavior checks `focused_on` against specific part ID
- Parser resolves "left side of bench" through normal entity matching
- Clear, explicit positioning when puzzle requires it

**Comparison to string-based approach:**
- **Before:** `"sides": ["left", "center", "right"]` (strings), `position_at` is string, need to validate string matches
- **After:** Three part entities, `focused_on` is entity ID, validation is entity existence

## 5.3 Environmental Obstacle - Fallen Beam

**Scenario:** A beam has fallen, blocking access to part of the room.

**Implementation:**

```json
{
  "id": "item_beam",
  "name": "beam",
  "location": "loc_collapsed_hall",
  "properties": {
    "portable": false,
    "provides_cover": true,
    "description": "A massive wooden beam that has fallen from the ceiling.",
    "blocks_path_to": ["part_hall_throne_area"]
  },
  "behaviors": ["behaviors.obstacles"]
}
```

```json
{
  "id": "part_hall_throne_area",
  "entity_type": "part",
  "name": "throne area",
  "part_of": "loc_collapsed_hall",
  "properties": {
    "description": "The raised dais where the throne sits."
  }
}
```

```json
{
  "id": "item_throne",
  "name": "throne",
  "location": "part_hall_throne_area",
  "properties": {
    "portable": false,
    "description": "An ornate stone throne."
  }
}
```

**Behavior:**

```python
# behaviors/obstacles.py

def on_approach(entity, accessor, context):
    """Check if beam blocks path to target."""
    if not entity.properties.get("blocks_path_to"):
        return EventResult(allow=True)

    target_id = context.get("target_id")
    blocked_parts = entity.properties.get("blocks_path_to", [])

    # Check if trying to approach a blocked part or item at blocked part
    if target_id in blocked_parts:
        return EventResult(
            allow=False,
            message=f"The {entity.name} blocks your way. You'll need to find another route."
        )

    # Check if target is an item at a blocked part
    target = accessor.get_entity(target_id)
    if hasattr(target, 'location') and target.location in blocked_parts:
        return EventResult(
            allow=False,
            message=f"The {entity.name} blocks your path to the {target.name}."
        )

    return EventResult(allow=True)
```

**Gameplay:**

```
> look
Collapsed Hall
The hall is grand but damaged.

You see: beam
At the throne area: throne

> examine throne area
You can't get close enough - the beam blocks your way.

> approach throne
The beam blocks your path to the throne.

> examine beam
A massive wooden beam that has fallen from the ceiling.

> push beam
The beam is far too heavy to move.

> go west
You circle around through the side passage.

> approach throne area
You step up onto the raised dais.

> examine throne
An ornate stone throne.
```

**Why this works:**
- Throne area is a Part, representing a spatial zone in the room
- Beam's behavior checks if target is in blocked parts list
- Natural spatial structure: room has parts, items can be at parts
- Obstacle can be removed/cleared by setting `blocks_path_to` to empty list

## 5.4 Interactive Discovery - Window View

**Scenario:** A window offers different views of the courtyard.

**Implementation:**

```json
{
  "id": "part_tower_east_wall",
  "entity_type": "part",
  "name": "east wall",
  "part_of": "loc_tower_room",
  "properties": {
    "description": "The eastern wall has a narrow window."
  }
}
```

```json
{
  "id": "item_window",
  "name": "window",
  "location": "part_tower_east_wall",
  "properties": {
    "portable": false,
    "description": "A narrow window overlooking the courtyard.",
    "viewpoints": {
      "courtyard": "You see the courtyard below, bustling with activity.",
      "mountains": "Beyond the courtyard, snow-capped mountains rise majestically.",
      "gate": "The main gate is visible, with guards standing watch."
    }
  },
  "behaviors": ["behaviors.windows"]
}
```

**Behavior:**

```python
# behaviors/windows.py

VOCABULARY = {
    "verbs": [
        {
            "word": "peer",
            "synonyms": ["gaze", "stare"],
            "object_required": True
        }
    ]
}

def handle_peer(accessor, action):
    """Look through windows at specific features."""
    actor_id = action["actor_id"]
    obj_entry = action.get("object")

    # Find target entity
    entity = _find_entity(accessor, actor_id, obj_entry)

    viewpoints = entity.properties.get("viewpoints", {})
    if not viewpoints:
        return EventResult(
            success=False,
            message=f"You can't peer through the {entity.name}."
        )

    # Check if player specified what to look at (indirect object)
    indirect = action.get("indirect_object")
    if indirect:
        view_name = indirect.word
        if view_name in viewpoints:
            return EventResult(
                success=True,
                message=viewpoints[view_name]
            )
        else:
            return EventResult(
                success=False,
                message=f"You don't see {view_name} from the {entity.name}."
            )

    # Show all viewpoints
    views = "\n".join(viewpoints.values())
    return EventResult(success=True, message=views)
```

**Gameplay:**

```
> examine east wall
The eastern wall has a narrow window. At the east wall: a window.

> approach window
You move to the window on the east wall.

> peer through window
You see the courtyard below, bustling with activity.
Beyond the courtyard, snow-capped mountains rise majestically.
The main gate is visible, with guards standing watch.

> peer at mountains
Beyond the courtyard, snow-capped mountains rise majestically.

> peer at gate
The main gate is visible, with guards standing watch.
```

**Why this works:**
- Wall is a Part entity
- Window is located at the wall part (proper location hierarchy)
- Custom verb adds flavor to interaction
- Properties store view data
- Implicit positioning brings player to window

## 5.5 NPC Interaction - Position Matters

**Scenario:** A nervous merchant reacts differently depending on where you approach from.

**Implementation:**

```json
{
  "id": "part_market_stall_front",
  "entity_type": "part",
  "name": "front of stall",
  "part_of": "item_market_stall",
  "properties": {
    "dialogue_mood": "hostile",
    "description": "The counter where the merchant displays wares."
  }
}
```

```json
{
  "id": "part_market_stall_side",
  "entity_type": "part",
  "name": "side of stall",
  "part_of": "item_market_stall",
  "properties": {
    "dialogue_mood": "friendly",
    "description": "A less formal approach to the merchant."
  }
}
```

```json
{
  "id": "npc_merchant",
  "name": "Merchant",
  "location": "loc_market",
  "properties": {
    "default_location": "part_market_stall_side",
    "description": "A nervous-looking merchant tending his wares."
  },
  "behaviors": ["behaviors.nervous_merchant"]
}
```

**Behavior:**

```python
# behaviors/nervous_merchant.py

def on_talk(entity, accessor, context):
    """Merchant dialogue depends on player's position."""
    if entity.id != "npc_merchant":
        return EventResult(allow=True)

    actor_id = context["actor_id"]
    actor = accessor.get_actor(actor_id)

    # Check which part of the stall the player is at
    focused = actor.properties.get("focused_on")

    if not focused or not focused.startswith("part_market_stall"):
        return EventResult(
            allow=True,
            message="The merchant seems too far away to talk comfortably."
        )

    # Get the mood based on which part player is at
    part = accessor.get_part(focused)
    mood = part.properties.get("dialogue_mood", "neutral")

    if mood == "hostile":
        return EventResult(
            allow=True,
            message="The merchant backs away nervously. 'Too close! Come around to the side!'"
        )
    elif mood == "friendly":
        return EventResult(
            allow=True,
            message="The merchant relaxes. 'Ah, a customer! What can I show you?'"
        )

    return EventResult(allow=True)
```

**Gameplay:**

```
> examine merchant
A nervous-looking merchant tending his wares.

> talk to merchant
The merchant seems too far away to talk comfortably.

> approach front of stall
You move to the counter where the merchant displays his wares.

> talk to merchant
The merchant backs away nervously. 'Too close! Come around to the side!'

> approach side of stall
You step to the side of the merchant's stall.

> talk to merchant
The merchant relaxes. 'Ah, a customer! What can I show you?'
```

**Why this works:**
- Different parts of stall have different properties (dialogue_mood)
- Behavior checks which part player is focused on
- Parts enable position-dependent NPC reactions
- Natural player experience with clear feedback

## 5.6 Ceiling/Floor Puzzle - Hidden Trapdoor

**Scenario:** A rug in a chapel conceals a trapdoor in the floor. The puzzle requires discovering and accessing the hidden trapdoor.

**Implementation:**

```json
{
  "id": "loc_chapel",
  "name": "Chapel",
  "properties": {
    "description": "A small stone chapel with simple furnishings."
  }
}
```

```json
{
  "id": "part_chapel_floor",
  "entity_type": "part",
  "name": "floor",
  "part_of": "loc_chapel",
  "properties": {
    "material": "stone",
    "description": "The stone floor is worn smooth by centuries of footsteps."
  }
}
```

```json
{
  "id": "item_rug",
  "name": "rug",
  "location": "part_chapel_floor",
  "properties": {
    "portable": false,
    "movable": true,
    "description": "A threadbare rug covers the center of the floor.",
    "conceals": "item_trapdoor"
  },
  "behaviors": ["behaviors.concealing"]
}
```

```json
{
  "id": "item_trapdoor",
  "name": "trapdoor",
  "location": "part_chapel_floor",
  "properties": {
    "portable": false,
    "openable": true,
    "states": {
      "open": false,
      "hidden": true
    },
    "description": "A wooden trapdoor set into the floor.",
    "leads_to": "loc_crypt"
  }
}
```

**Behavior:**

```python
# behaviors/concealing.py

def on_move(entity, accessor, context):
    """Moving rug reveals what it conceals."""
    if not entity.properties.get("conceals"):
        return EventResult(allow=True)

    concealed_id = entity.properties["conceals"]
    concealed_item = accessor.get_item(concealed_id)

    if concealed_item and concealed_item.properties.get("states", {}).get("hidden"):
        # Reveal the concealed item
        concealed_item.properties["states"]["hidden"] = False

        return EventResult(
            allow=True,
            message=f"You slide the {entity.name} aside, revealing {concealed_item.name}!"
        )

    return EventResult(allow=True)
```

**Gameplay:**

```
> look
Chapel
A small stone chapel with simple furnishings.

You see: wooden pew
At the floor: rug

> examine floor
The stone floor is worn smooth by centuries of footsteps. At the floor: a rug.

> examine ceiling
The chapel ceiling is plain whitewashed stone.

> examine rug
A threadbare rug covers the center of the floor.

> move rug
You slide the rug aside, revealing a trapdoor!

> examine trapdoor
A wooden trapdoor set into the floor.

> open trapdoor
You pull open the heavy trapdoor, revealing stone steps leading down into darkness.

> go down
You descend the steps into the crypt below.
```

**Why this needs a floor part:**
- Two items (rug and trapdoor) are specifically located on the floor
- Floor part enables clear spatial hierarchy: examining floor lists items at floor
- The "At the floor: rug" output in `look` creates clear mental image
- With 2+ items on floor, the part is justified

**Alternative with single item:**

If only the trapdoor existed (no rug), you could skip the floor part:

```json
{
  "id": "item_trapdoor",
  "location": "loc_chapel",
  "properties": {
    "states": {"hidden": true}
  }
}
```

```
> look
Chapel
A small stone chapel with simple furnishings.

You see: wooden pew

> examine floor
Nothing remarkable about the floor.
```

The universal surface fallback handles "examine floor" adequately for rooms without floor parts.

**When floor part not needed:**

If rug and trapdoor were just `"location": "loc_chapel"` with no specific floor interactions:

```json
{
  "id": "loc_chapel",
  "name": "Chapel",
  "properties": {
    "floor_description": "The stone floor is worn smooth by centuries of footsteps."
  }
}
```

```
> examine floor
The stone floor is worn smooth by centuries of footsteps.
```

Universal surface fallback provides good UX without creating part entity.

---

# 6. Advantages of This Design

## 6.1 Aligns With Framework Philosophy

### ✅ Maximizes Author Capability

Authors can create spatial puzzles by:
- Creating Part entities only when spatial distinction matters
- Adding properties to parts for custom spatial logic
- Writing behaviors that check `focused_on` for positioning requirements
- Using implicit or explicit positioning as needed
- Starting simple (no parts) and adding complexity incrementally

### ✅ Maximizes Player Agency

Players can:
- Interact naturally without explicit movement (implicit positioning)
- Use explicit positioning when puzzles require it (approach commands)
- Examine and interact with all spatial features (walls, sides, areas)
- Position themselves strategically (combat/stealth via `behind` property)

### ✅ Separation of Concerns

- Engine manages all spatial state (`focused_on`, `behind`, part locations)
- LLM narrates positioning changes naturally
- Behaviors handle spatial logic (distance checking, position requirements)

### ✅ Entity Uniformity

- **All spatial features are entities** - No special string matching or hardcoded wall handling
- Parts have IDs, names, properties, behaviors - just like items, containers, actors
- Vocabulary system works uniformly across all entity types
- Parser uses consistent entity resolution

### ✅ Property-Based Entities

- All spatial data lives in properties dict
- Parts use same flexible property system as other entities
- Backward compatible (existing games ignore spatial features)

### ✅ Behavior-Driven Extension

- Core provides implicit positioning
- Game behaviors add explicit positioning requirements where needed
- Libraries can provide reusable spatial patterns (obstacles, viewpoints, position-dependent interactions)

## 6.2 Technical Benefits

### Entity Uniformity Restored

**Problem solved:** String-based walls and sides had unclear ontological status and couldn't use vocabulary system.

**Solution:** Parts are proper entities. "examine north wall" uses normal WordEntry matching to find part_throne_north_wall.

### Location Hierarchy Makes Sense

```
Room (Location)
├── Items (location = room ID)
├── Parts (part_of = room ID)
│   ├── Items at wall (location = part ID)
│   └── Actors at area (location = part ID)
└── Sub-Parts possible (part_of = item ID)
    └── Items at item-part (location = sub-part ID)
```

Clear, consistent location semantics.

### Validation is Simple

Part validation checks:
- `part_of` references valid entity ID (room, item, container, actor)
- Part ID doesn't conflict with other entity IDs
- `focused_on` references valid entity ID (can be item, container, part, actor)
- `behind` references valid entity with `provides_cover` property

No complex spatial validation needed - just entity reference validation.

### StateAccessor Extensions

Add part-aware methods to StateAccessor:

```python
def get_part(self, part_id: str) -> Optional[Part]:
    """Get part by ID."""
    return self.state.parts.get(part_id)

def get_parts_of(self, entity_id: str) -> List[Part]:
    """Get all parts belonging to an entity."""
    return [p for p in self.state.parts.values()
            if p.part_of == entity_id]

def get_items_at_part(self, part_id: str) -> List[Item]:
    """Get items located at a part."""
    return [i for i in self.state.items.values()
            if i.location == part_id]

def get_focused_entity(self, actor_id: str):
    """Get entity actor is focused on (can be item, container, part, actor)."""
    actor = self.get_actor(actor_id)
    if not actor:
        return None

    focused_id = actor.properties.get("focused_on")
    if not focused_id:
        return None

    # Check all entity types
    return (self.get_item(focused_id) or
            self.get_container(focused_id) or
            self.get_part(focused_id) or
            self.get_actor(focused_id))

def get_entity(self, entity_id: str):
    """Get any entity by ID regardless of type."""
    return (self.get_location(entity_id) or
            self.get_item(entity_id) or
            self.get_container(entity_id) or
            self.get_actor(entity_id) or
            self.get_part(entity_id))
```

### Backward Compatible

Existing games:
- Continue working unchanged
- Ignore Part entities entirely
- Don't need to create any parts
- No migration needed

### Estimated Implementation Effort

Core changes:
1. Add Part entity type and collection to GameState (1 day)
2. Update entity resolution to include parts (1 day)
3. Add implicit positioning to core behaviors (2 days)
4. Add `approach` command (1 day)
5. Add StateAccessor part methods (1 day)
6. Add validation for parts (1 day)
7. Update vocabulary system to handle parts (1 day)
8. Testing (2 days)

**Total: 10 days / 2 weeks**

---

# 7. Validation Rules for Parts

## 7.1 Part Definition Validation

**Required fields:**
- `id` - Must be unique across ALL entity types (items, containers, actors, parts, locations)
- `entity_type` - Must be "part"
- `name` - Display name
- `part_of` - Must reference a valid entity ID

**Optional fields:**
- `properties` - Flexible properties dict
- `behaviors` - List of behavior module paths
- `llm_context` - Description for narration

**Constraints:**
- Part cannot be portable (implicit - not an item)
- Part cannot have inventory (implicit - not a container)
- `part_of` cannot reference another part ID (Phase 1 constraint - nested parts planned for future phase, see Section 10.1)

## 7.2 Runtime Validation

**On game load:**
1. Check all part IDs are unique
2. Check all `part_of` references point to valid entities
3. Check no circular references (part → parent → part)
4. Warn if `interaction_distance` has value other than "any" or "near"

**On command execution:**
1. Check `focused_on` references valid entity (if not null)
2. Check entity being focused on is accessible from actor's location
3. If `posture` is "cover", check that `focused_on` entity has `provides_cover` property

### Part Lifecycle

**Part creation:** Parts are defined in game JSON and loaded at game start. Dynamic part creation is not supported in Phase 1 (see Section 10.1 for future extensions).

**Parts follow their parent:** Parts are permanently attached to their parent entity. When a parent entity moves to a different location, its parts move with it conceptually - they remain accessible and referenceable wherever the parent is accessible. Items located at parts remain at those parts regardless of where the parent entity moves.

**Example:**
```python
# Bench with parts starts in workshop
bench.location = "loc_workshop"
part_bench_left.part_of = "item_bench"  # Always attached to bench
mortar.location = "part_bench_left"      # At the left side of bench

# If bench moves to storage room
bench.location = "loc_storage"
# part_bench_left is still accessible (via bench in storage)
# mortar is still at part_bench_left
# Players in storage room can "examine left side of bench"
```

**Parts persist independently of items:** Parts represent spatial structure, not item containers. When all items at a part are removed or destroyed, the part remains. This is correct behavior - the "north wall" exists whether or not anything is mounted on it. New items can be attached to parts at any time during gameplay.

**Example:**
```python
# Wall part with tapestry
tapestry.location = "part_throne_north_wall"

# Player removes tapestry
tapestry.location = "player_inventory"

# part_throne_north_wall still exists and is examinable
# Later, player could attach a new painting to the same wall part
painting.location = "part_throne_north_wall"
```

**Part destruction:** When a parent entity is destroyed, its parts MUST be destroyed:

```python
def destroy_entity(accessor, entity_id):
    """Destroy entity and all its parts."""
    entity = accessor.get_entity(entity_id)

    # Find and destroy all parts belonging to this entity
    parts = accessor.get_parts_of(entity_id)
    for part in parts:
        # First, move any items at this part to the parent's location
        for item in accessor.game_state.items:
            if item.location == part.id:
                item.location = entity.location

        # Delete the part
        del accessor.game_state.parts[part.id]

    # Destroy entity
    # ... normal destruction logic ...
```

**Orphaned parts:** If a part's parent is destroyed without cleaning up the part:
- This is a **noisy error** condition
- Validation should detect and fail loudly: `ValidationError: Part {part_id} references non-existent parent {parent_id}`
- Never silently ignore orphaned parts

## 7.3 Authoring Validation

**Warning conditions:**
- Part's `part_of` references non-existent entity
- Multiple parts with similar names (e.g., "left side", "left side")
- Part exists but is never referenced (orphaned at authoring time)

---

# 8. Authoring Guidelines

## 8.1 When to Create Parts

### Decision Guide

**Ask: Do spatial details matter for gameplay?**

```
NO → Don't create parts
    Just describe spatial details in location/item descriptions
    Example: "The throne room has tapestries on the north wall."

YES → Continue...
```

**Ask: Do players need to interact with specific spatial features?**

```
NO → Don't create parts
    Spatial details are just narrative flavor
    Example: "The carved pillars support the vaulted ceiling."

YES → Continue...
```

**Ask: Which spatial features need interaction?**

```
- Walls where items are mounted → Create wall parts
- Multi-sided objects with different tools/features → Create side parts
- Distinct areas within a room → Create area parts
- Spatial features with special properties/behaviors → Create parts
```

### Create Parts When:

1. **Items need to be attached to walls**
   - Paintings, tapestries, sconces, buttons
   - Create part for each wall with mounted items

2. **Object has distinct sides with different features**
   - Alchemy bench with tools on different sides
   - Control panel with buttons on multiple faces
   - Create part for each distinct side

3. **Room has distinct spatial areas**
   - Throne area separated from main hall
   - Altar at far end of chapel
   - Create part for each significant area

4. **Spatial feature needs properties or behaviors**
   - North wall is damaged (property)
   - Back of cabinet has secret compartment (behavior)
   - Create part for feature

### Don't Create Parts When:

1. **Simple directional description**
   - "The throne is at the north end of the room"
   - Just describe in room's `llm_context`

2. **Object is spatially uniform**
   - A simple table with no special sides
   - Don't create parts for every object

3. **Spatial detail is pure flavor**
   - "Dust motes float in shafts of sunlight"
   - Description text only, no parts needed

4. **Single-item attachment**
   - If only one tapestry in entire room
   - Can still create wall part, but consider if it adds value

## 8.2 Standard Part Patterns

### Pattern 1: Four Cardinal Walls

Only create parts that enhance gameplay, for example walls, ceiling or floor that will be used to attach items or will enhance description. Surfaces that aren't worth focusing on don't need to be parts.

The parts themselves define the relationship via `part_of`:

```json
{
  "id": "part_throne_north_wall",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_throne_room"
}
```

*Authoring tool can generate these automatically. No need to list parts in parent entity.*

### Pattern 2: Multi-Sided Object

Object with 3-4 distinct interaction sides. Parts reference the object via `part_of`:

```json
{
  "id": "part_workbench_left",
  "entity_type": "part",
  "name": "left side of workbench",
  "part_of": "item_workbench"
}
```

### Pattern 3: Room Areas

Large room divided into distinct zones:

```json
{
  "id": "part_hall_entrance",
  "entity_type": "part",
  "name": "entrance area",
  "part_of": "loc_great_hall"
}
```

### Pattern 4: Container with Hidden Compartment

```json
{
  "id": "part_cabinet_back",
  "entity_type": "part",
  "name": "back of cabinet",
  "part_of": "container_cabinet",
  "behaviors": ["behaviors.secret_compartment"]
}
```

Back part has behavior for secret compartment detection.

### Pattern 5: Ceiling and Floor Parts

**Clear rule: Create ceiling/floor parts when 2+ items are located there OR when special behaviors/properties are needed.**

#### Create Ceiling Part When:

- **2+ items attached to ceiling** (chandelier + bell, multiple banners)
- **Ceiling has behaviors** (collapsing ceiling, retractable roof mechanism)
- **Ceiling has special properties** requiring state tracking (structural integrity, damage level)

**Example - Cathedral with chandelier:**

```json
{
  "id": "part_cathedral_ceiling",
  "entity_type": "part",
  "name": "ceiling",
  "part_of": "loc_cathedral",
  "properties": {
    "height": "very high",
    "description": "A magnificent vaulted ceiling with frescoes depicting angels."
  }
}
```

```json
{
  "id": "item_chandelier",
  "name": "chandelier",
  "location": "part_cathedral_ceiling",
  "properties": {
    "portable": false,
    "description": "An enormous crystal chandelier hanging far above."
  }
}
```

#### Create Floor Part When:

- **2+ items on floor** (rug + trapdoor, multiple floor tiles, grate + drain)
- **Floor has behaviors** (pressure plate mechanics, collapsing floor)
- **Floor has special properties** requiring state tracking (structural integrity, wetness, magical circle power)

**Example - Chapel with hidden trapdoor:**

```json
{
  "id": "part_chapel_floor",
  "entity_type": "part",
  "name": "floor",
  "part_of": "loc_chapel",
  "properties": {
    "material": "stone",
    "description": "The stone floor is worn smooth by centuries of footsteps."
  }
}
```

```json
{
  "id": "item_rug",
  "name": "rug",
  "location": "part_chapel_floor",
  "properties": {
    "portable": false,
    "movable": true,
    "conceals": "item_trapdoor"
  }
}
```

```json
{
  "id": "item_trapdoor",
  "name": "trapdoor",
  "location": "part_chapel_floor",
  "properties": {
    "openable": true,
    "states": {
      "open": false,
      "hidden": true
    }
  }
}
```

#### Don't Create Ceiling/Floor Parts When:

- **Only 1 item on ceiling/floor** - Just use `"location": "loc_room"` for the item
- **No items and no behaviors** - Universal surface fallback handles "examine ceiling/floor"
- **Pure decoration** - Description is flavor text only (include in room's description/llm_context)

**Rule of thumb:** If you can't list 2 items at the part or name a behavior it needs, don't create it.

**Important:** Universal surface fallback (Section 4.3) provides basic responses for "examine ceiling/floor" in rooms without parts, avoiding "You don't see ceiling here" errors.

## 8.3 Naming Conventions

### Part ID Format

`part_<parent>_<descriptor>`

- `part_throne_north_wall` - Wall in throne room
- `part_bench_left` - Left side of bench
- `part_hall_entrance` - Entrance area of hall

### Part Display Names

Use natural language that players will type:

- "north wall" (not "northern wall")
- "left side of bench" (not "bench left")
- "back of cabinet" (not "cabinet back")

Remember: Players will type these names in commands.

## 8.4 When to Use Implicit vs Explicit Positioning

### Default Behavior Summary

All entities default to `interaction_distance: "any"` - players can interact from anywhere in the room without implicit positioning.

Set `interaction_distance: "near"` on specific entities when you want the player to automatically move near them during interaction.

### Setting "near" for Spatial Realism

**High/distant objects that should remain accessible:**
```json
{
  "id": "item_chandelier",
  "location": "part_cathedral_ceiling",
  "properties": {
    "portable": false,
    "description": "An enormous crystal chandelier hanging far above."
  }
}
```
No `interaction_distance` needed - defaults to "any" so player can examine from anywhere.

**Items requiring close approach:**
```json
{
  "id": "item_inscription",
  "location": "loc_cave",
  "properties": {
    "interaction_distance": "near",  // Player must move close to examine
    "description": "Tiny runes carved in ancient script."
  }
}
```

**Items in spatial rooms where position matters:**
```json
{
  "id": "item_bench",
  "location": "loc_workshop",
  "properties": {
    "portable": false,
    "interaction_distance": "near",  // Player moves near when examining
    "description": "A long workbench."
  }
}
```

### Use Implicit Positioning (interaction_distance: "near")

**For:**
- Story-focused games with spatial rooms
- Casual interactions with automatic positioning
- Natural flow without explicit movement commands
- When position matters for realism but not puzzle mechanics

Player examines desk → automatically moves near → can open drawer without explicit approach.

### Use Explicit Positioning (requiring approach command)

**For:**
- Position-dependent puzzles
- Multi-part objects where wrong position fails
- When teaching player about spatial system
- Combat/stealth positioning

**Example:**
```python
def handle_grind(accessor, action):
    # Check if focused on specific part
    if actor.properties.get("focused_on") != "part_bench_left":
        return EventResult(
            success=False,
            message="You need to be at the left side of the bench."
        )
```

Requires player to use `approach left side of bench` before grinding.

### Behavior Override

Custom behaviors can modify interaction distance checks:

**Dynamic distance adjustment:**
```python
# behaviors/magic_telescope.py
def on_examine(entity, accessor, context):
    """Telescope can be examined from across room using magic."""
    if entity.id == "item_telescope":
        entity.properties["interaction_distance"] = "any"
    return EventResult(allow=True)
```

**Block approach:**
```python
# behaviors/dangerous_artifact.py
def on_approach(entity, accessor, context):
    """Can't get near the glowing artifact - it burns."""
    if entity.id == "item_artifact":
        return EventResult(
            allow=False,
            message="The artifact radiates intense heat. You can't get closer."
        )
    return EventResult(allow=True)
```

**Custom distance requirements:**
```python
# behaviors/delicate_puzzle.py
def on_examine(entity, accessor, context):
    """Puzzle requires being very close to see details."""
    actor_id = context["actor_id"]
    actor = accessor.get_actor(actor_id)

    focused = actor.properties.get("focused_on")
    if focused != entity.id:
        return EventResult(
            allow=True,
            message="From here you can't make out the details. You'd need to get closer."
        )

    return EventResult(allow=True, message="The puzzle has intricate symbols...")
```

### Decision Rule

1. **Use default ("any")** for most entities - no positioning required
2. **Set "near"** when you want implicit positioning (spatial rooms, detailed objects, realistic positioning)
3. **Require explicit approach** via behaviors when wrong position should fail with helpful message or when multiple positions matter

## 8.5 Container vs Part: Decision Principle

**Core principle:** Use Container for internal storage; use Part for spatial regions.

### Use Container When:

- **Entity holds items internally** - Drawers, boxes, bags, chests
- **Items are "in" or "inside" it** - "look in drawer", "put coin in box"
- **Can be opened/closed** - Access control via open/closed state
- **Portable storage** - Backpacks, pouches, sacks

**Example - Desk drawer:**
```json
{
  "id": "container_drawer",
  "entity_type": "container",
  "name": "drawer",
  "location": "item_desk",
  "parent_item": "item_desk",
  "properties": {
    "openable": true,
    "states": {"open": false}
  }
}
```

### Use Part When:

- **Entity represents spatial region** - Wall, side of object, area within room
- **Items are "at" or "on" it** - "tapestry on north wall", "mortar at left side"
- **Defines position for interaction** - "approach left side of bench"
- **Cannot be opened** - It's not a container, it's a spatial location

**Example - Cabinet back with secret compartment:**
```json
{
  "id": "part_cabinet_back",
  "entity_type": "part",
  "name": "back of cabinet",
  "part_of": "container_cabinet",
  "behaviors": ["behaviors.secret_compartment"],
  "properties": {
    "description": "The back panel of the cabinet."
  }
}
```

The secret compartment behavior can reveal a hidden item when examining the back part.

### Examples Compared:

**Desk drawer (Container):**
- Items are "in" the drawer
- Can be opened/closed
- Separate entity from desk

**Bench left side (Part):**
- Items are "at" the left side
- Not opened/closed
- Spatial component of bench

**Cabinet interior (Container):**
- Normal storage space
- Open/close to access

**Cabinet back panel (Part):**
- Spatial location for secret items
- Examined for hidden compartments
- Position matters

## 8.6 Common Mistakes to Avoid

### Mistake 1: Creating Parts for Everything

**Bad:**
```json
{
  "id": "item_key",
  "properties": {
    "portable": true
  }
}

{
  "id": "part_key_top",
  "entity_type": "part",
  "name": "top of key",
  "part_of": "item_key"
}
```

**Why:** Key has no spatial gameplay - parts add complexity without benefit.

**Good:**
```json
{
  "id": "item_key",
  "properties": {
    "portable": true
  }
}
```

Just a simple item, no parts needed.

### Mistake 2: Using Parts Instead of Separate Items

**Bad:**
```json
{
  "id": "part_desk_drawer",
  "name": "drawer",
  "part_of": "item_desk"
}
```

**Why:** Drawer should be a separate container entity, not a part. Parts are for spatial positioning, not containment.

**Good:**
```json
{
  "id": "container_drawer",
  "name": "drawer",
  "location": "item_desk",
  "parent_item": "item_desk"
}
```

### Mistake 3: Inconsistent Part Names

**Bad:**
- "north wall" and "eastern wall" (inconsistent adjective form)
- "left side of bench" and "bench right side" (inconsistent structure)

**Good:**
- "north wall", "south wall", "east wall", "west wall"
- "left side of bench", "right side of bench", "center of bench"

### Mistake 4: Too Many Parts

**Bad:** Every room has 4 walls, 2 corners, ceiling, floor as parts (8 parts per room).

**Why:** If no gameplay uses these parts, they're pure overhead.

**Good:** Only create parts when:
- Items will be located at them
- Behaviors will reference them
- Players will explicitly interact with them

## 8.7 Performance Considerations

### Parts are Lightweight

Each part is just:
- ID string
- Name string
- Parent reference
- Properties dict
- Optional behaviors list

**Cost:** ~200-500 bytes per part in memory

### Typical Part Counts

**Simple game:** 0-10 parts total
- No wall parts
- Maybe 1-2 multi-sided objects

**Medium game:** 20-50 parts
- 3-5 rooms with 4 wall parts each (12-20)
- 5-10 multi-sided objects (5-10)
- 2-5 room areas (2-5)

**Complex game:** 100-200 parts
- 15-20 rooms with wall parts (60-80)
- Many multi-sided objects (30-50)
- Multiple room areas (20-40)
- Special spatial features (10-30)

**Performance impact:** Negligible until thousands of parts.

### Authoring Tool Support

Authoring tools should:
1. Auto-generate 4 wall parts for rooms on request
2. Provide templates for common part patterns (multi-sided object, room areas)
3. Validate part references (part_of, parts array consistency)
4. Warn about unused parts (part exists but no items at it, no behaviors reference it)

---

# 9. Integration With Existing Systems

## 9.1 Behavior System

Parts integrate seamlessly with behaviors:

### Position-Dependent Actions

```python
def on_push(entity, accessor, context):
    """Lever requires player to be at control panel."""
    if entity.id != "item_lever":
        return EventResult(allow=True)

    actor_id = context["actor_id"]
    actor = accessor.get_actor(actor_id)

    # Check if player is at the correct part
    focused = actor.properties.get("focused_on")
    if focused != "part_wall_panel":
        return EventResult(
            allow=False,
            message="You need to be at the control panel to reach the lever."
        )

    return EventResult(allow=True)
```

### Part-Specific Behaviors

Parts can have their own behaviors:

```json
{
  "id": "part_cabinet_back",
  "entity_type": "part",
  "name": "back of cabinet",
  "part_of": "container_cabinet",
  "behaviors": ["behaviors.secret_compartment"]
}
```

```python
# behaviors/secret_compartment.py

def on_examine(entity, accessor, context):
    """Examining back of cabinet reveals secret compartment."""
    if not entity.properties.get("secret_discovered"):
        entity.properties["secret_discovered"] = True

        # Create hidden item
        hidden_item = accessor.get_item("item_hidden_letter")
        hidden_item.properties["states"]["hidden"] = False

        return EventResult(
            allow=True,
            message="You notice a slight gap in the wood. Pressing on it reveals a hidden compartment!"
        )

    return EventResult(allow=True)
```

### NPC Positioning

NPCs use the same spatial properties as the player:

**Spatial properties for NPCs:**
- `npc.properties["focused_on"]` tracks NPC position within room
- `npc.properties["posture"]` tracks how NPC is positioned (e.g., "cover", "concealed", "climbing")
- `npc.location` is always a location_id (which room), never a part_id

**NPC behaviors should set focused_on explicitly:**
```python
# behaviors/guard_patrol.py

def on_turn(entity, accessor, context):
    """Guard patrols between different parts of the room."""
    if entity.id != "npc_guard":
        return EventResult(allow=True)

    # Cycle through patrol points
    patrol_points = ["part_hall_entrance", "part_hall_center", "part_hall_throne"]
    current = entity.properties.get("focused_on")

    if current in patrol_points:
        next_idx = (patrol_points.index(current) + 1) % len(patrol_points)
        entity.properties["focused_on"] = patrol_points[next_idx]

    return EventResult(allow=True)
```

**Collision handling:**
Multiple actors can be focused on the same entity/part - no collision detection:
```python
# Both valid simultaneously:
player.properties["focused_on"] = "part_bench_left"
npc_alchemist.properties["focused_on"] = "part_bench_left"
```

This is natural - two people can both be at the left side of a bench.

**Exclusive positioning (if needed):**
Implement via behavior-level checks for special cases:
```python
# behaviors/narrow_ledge.py

def on_approach(entity, accessor, context):
    """Only one actor at a time can fit on narrow ledge."""
    if entity.id != "part_ledge":
        return EventResult(allow=True)

    actor_id = context["actor_id"]

    # Check if anyone else is already there
    for other_actor in accessor.game_state.actors.values():
        if other_actor.id != actor_id:
            if other_actor.properties.get("focused_on") == entity.id:
                return EventResult(
                    allow=False,
                    message=f"{other_actor.name} is already on the ledge. There's no room."
                )

    return EventResult(allow=True)
```

## 9.2 LLM Narration

Spatial state enhances narration automatically:

### Movement Narration

When player approaches entity, pass context to LLM:

```python
# In approach handler
data = {
    "id": entity.id,
    "name": entity.name,
    "type": entity.entity_type,  # "part", "item", "container", "actor"
    "focused_on": True,
    "llm_context": entity.llm_context or entity.properties.get("description", "")
}

return EventResult(success=True, message="You move to the {entity.name}.", data=data)
```

LLM uses this to narrate movement naturally:

```
You step toward the north wall where the ancient tapestry hangs,
its faded threads depicting a long-forgotten battle.
```

### Part Context in Room Descriptions

LLM receives part information when generating room descriptions:

```python
def get_room_context_for_llm(accessor, location_id):
    """Build context including parts and their contents."""
    location = accessor.get_location(location_id)
    parts = accessor.get_parts_of(location_id)

    context = {
        "location": location.name,
        "description": location.llm_context,
        "parts": []
    }

    for part in parts:
        items_at_part = accessor.get_items_at_part(part.id)
        if items_at_part:
            context["parts"].append({
                "name": part.name,
                "items": [item.name for item in items_at_part]
            })

    return context
```

LLM generates:

```
You stand in the throne room. Ancient stone walls surround you.
On the north wall hangs a faded tapestry. The east wall features
an ornate torch in an iron sconce.
```

## 9.3 Parser Integration

### Entity Resolution Order

When player types "examine north wall", parser:

1. Builds WordEntry from vocabulary
2. Searches for matching entities in this order:
   - Items in current location
   - Containers in current location
   - Actors in current location
   - **Parts of current location** ← New
   - **Parts of items in current location** ← New
3. Returns first match

### Disambiguation

If multiple entities match, the parser uses the normal disambiguation system:

```
> examine wall
Which wall do you mean: north wall, south wall, east wall, or west wall?
```

Parts are disambiguated like any other entity type. The game engine presents the options and lets the player choose. Disambiguation handling is the responsibility of game designers through careful naming and the player through clarification - there's no engine-level priority ordering among parts with the same word.

### Vocabulary

Parts participate in vocabulary system:

```json
{
  "nouns": [
    {
      "word": "wall",
      "synonyms": ["stone", "stonework"]
    },
    {
      "word": "side",
      "synonyms": ["end"]
    }
  ]
}
```

"examine stone" matches part with name "north wall" if wall has material=stone property.

## 9.4 Save/Load System

Parts serialize to JSON like any entity:

```json
{
  "parts": {
    "part_throne_north_wall": {
      "id": "part_throne_north_wall",
      "entity_type": "part",
      "name": "north wall",
      "part_of": "loc_throne_room",
      "properties": {
        "material": "stone",
        "damaged": false
      }
    }
  }
}
```

No special handling needed - parts are just another entity collection.

---

# 10. Future Extensions

## 10.1 Nested Parts (Sub-Parts)

Currently `part_of` cannot point to another part. Future extension:

```json
{
  "id": "part_altar_base_left",
  "entity_type": "part",
  "name": "left corner of altar base",
  "part_of": "part_altar_base",
  "properties": {
    "description": "An ornate corner piece with carved runes."
  }
}
```

Enables fine-grained spatial structure when needed.

## 10.2 Position-Based Perception

Items visible only from specific parts:

```json
{
  "id": "item_inscription",
  "location": "loc_chapel",
  "properties": {
    "states": {
      "hidden": true
    },
    "visible_from": ["part_altar_back"]
  }
}
```

Examine behavior checks if actor's `focused_on` is in `visible_from` list.

## 10.3 Line-of-Sight System

For stealth/combat using parts as spatial anchors:

```python
def has_line_of_sight(accessor, observer_id, target_id):
    """Check if observer can see target based on positions and cover."""
    observer = accessor.get_actor(observer_id)
    target = accessor.get_actor(target_id)

    # Check if target is in cover
    if target.properties.get("posture") == "cover":
        cover_id = target.properties.get("focused_on")
        if cover_id:
            cover = accessor.get_entity(cover_id)
            # Complex logic: does cover block LOS from observer's position?
            return False

    return True
```

## 10.4 Part-Based Pathfinding

For complex spatial puzzles:

```python
def find_path_between_parts(accessor, start_part_id, end_part_id):
    """Find sequence of parts player must traverse."""
    # Build graph of connected parts
    # Return list of part IDs forming path
```

Used for puzzles where player must navigate around obstacles.

---

# 11. Comparison to Alternatives

## vs. String-Based Walls (Original Design)

| Feature | Parts (This Design) | Strings (Original) |
|---------|-------------------|-------------------|
| Entity status | First-class entities | Strings in properties |
| Vocabulary system | Full participation | String matching hacks |
| Properties | Yes (full properties dict) | No |
| Behaviors | Yes (full behavior support) | No |
| Parser integration | Natural entity resolution | Special string matching |
| Location hierarchy | Clean (items at parts) | Messy (`attached_to` string) |
| Validation | Entity reference checks | String validation |
| Authoring burden | Higher (create entities) | Lower (just strings) |
| Conceptual integrity | High (everything is entity) | Low (walls are special) |

**Verdict:** Parts are more work to create but provide much cleaner, more extensible design.

## vs. Zone-Based Systems

| Feature | Parts | Zones |
|---------|-------|-------|
| Authoring complexity | Moderate | Very High |
| JSON verbosity | Reasonable | Extensive |
| Learning curve | Gentle | Steep |
| Validation complexity | Simple | Complex |
| Backward compatibility | Full | Difficult |
| Code maintenance | Low | High |
| Gameplay capability | 95% of use cases | 100% of use cases |

**Verdict:** Zones handle extreme edge cases parts don't, but at 5-10x the cost. Parts cover nearly all real needs.

## vs. XY Grid Systems

| Feature | Parts | XY Grids |
|---------|-------|----------|
| Abstraction level | Natural language | Coordinates |
| Author-friendly | Yes | No |
| Player commands | "approach north wall" | "move 3 2" |
| Fits IF conventions | Yes | No |
| Implementation cost | Moderate | Moderate |

**Verdict:** XY grids are wrong abstraction for parser IF. Parts fit IF conventions naturally.

## vs. No Spatial System

| Feature | Parts | No Spatial |
|---------|-------|------------|
| Spatial puzzles | Fully supported | Not supported |
| Wall interactions | Rich (walls are entities) | Limited/hacks |
| Position-dependent actions | Natural (check focused_on) | Hacks via properties |
| Author effort | Incremental (create parts only when needed) | None |
| Player experience | Natural spatial interaction | Fine for simple games |

**Verdict:** Parts add significant capability without burdening authors who don't need spatial features.

---

# 12. Conclusion

This design provides spatial awareness through a new entity type called **Part**, representing spatial components of other entities. Parts enable rich spatial gameplay while maintaining the framework's core philosophy of simplicity, extensibility, and minimal authoring burden.

## Key Design Principles

1. **Entity uniformity** - All spatial features are entities with IDs, names, properties, behaviors
2. **Implicit by default** - Most interactions work automatically via `interaction_distance`
3. **Explicit when needed** - Precise positioning via `approach` command for puzzles
4. **Progressive disclosure** - Simple games ignore parts, complex games create them
5. **Property-based** - All spatial data lives in properties dict
6. **Minimal authoring burden** - Create parts only when spatial distinction matters

## When to Use Parts

**Create parts when:**
- Items need to be mounted on walls
- Objects have distinct sides with different features
- Rooms have distinct spatial areas
- Spatial features need properties or behaviors

**Don't create parts when:**
- Spatial detail is pure flavor (use description text)
- Object is spatially uniform
- Game doesn't need spatial positioning

## Implementation Path

**Phase 1-2 (Weeks 1-2): Core Infrastructure**
1. Add Part entity type and collection
2. Implement implicit positioning

**Phase 3-4 (Weeks 2-3): Rich Spatial Features**
3. Add explicit positioning (approach command)
4. Add standard wall part patterns

**Phase 5-6 (Week 3): Advanced and Documentation**
5. Optional: Add cover system for tactical gameplay
6. Create comprehensive authoring guide and examples

## Core Benefits

✅ **Conceptual integrity** - Everything referenceable is an entity
✅ **Vocabulary system** - Parts use WordEntry matching, not string hacks
✅ **Extensibility** - Parts have properties and behaviors like all entities
✅ **Backward compatibility** - Existing games unaffected
✅ **Progressive disclosure** - Complexity only when needed

The design exemplifies the framework's philosophy: **Maximum capability, minimal complexity.**

Parts solve the ontological problem while enabling rich spatial gameplay.
