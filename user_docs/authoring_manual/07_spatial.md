# Spatial Rooms and Positioning

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Previous: [Common Patterns](06_patterns.md) | Next: [Parser & Commands](08_parser.md)

---


This section shows you how to design and implement spatial awareness in your text adventure games using the Part entity system.

## 7.1 When to Use Spatial Structure

### Use Spatial Structure When:

✅ **Multiple items attach to same feature** - "Tapestry and torch both on north wall"

✅ **Position matters for puzzles** - "Must be at left side of bench to grind ingredients"

✅ **Combat/stealth gameplay** - "Take cover behind pillar"

✅ **Complex room layout** - "Large hall with entrance area, center, and throne area"

### Skip Spatial Structure When:

❌ **Simple rooms** - Traditional IF rooms with just items in location work fine

❌ **No position-dependent gameplay** - If position never matters, don't add complexity

❌ **Single item per feature** - "One tapestry in room" doesn't need a wall part

## 7.2 Quick Start with Spatial Rooms

### Step 1: Design Your Room

Ask yourself:
- What spatial features matter for gameplay?
- Which items attach to specific locations?
- Does player position affect interactions?

### Step 2: Create the Room

Simple room without spatial structure:

```json
{
  "id": "loc_study",
  "name": "Study",
  "properties": {
    "description": "A cozy study with wooden furniture."
  },
  "exits": {
    "south": {"type": "open", "to": "loc_hallway"}
  }
}
```

### Step 3: Add Parts (If Needed)

If you need spatial features, create Part entities:

```json
{
  "id": "part_study_north_wall",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_study",
  "properties": {
    "description": "The north wall is covered in bookshelves."
  }
}
```

### Step 4: Attach Items to Parts

```json
{
  "id": "item_painting",
  "name": "painting",
  "location": "part_study_north_wall",
  "properties": {
    "portable": false,
    "description": "An oil painting of a sailing ship."
  }
}
```

### What Happens Automatically

The spatial system provides:
- Tracks player position via `focused_on` property
- Lists items by their spatial location in `look` output when items are at parts
- Optional implicit positioning when you set `interaction_distance: "near"` on entities

## 7.3 Understanding Parts

### What is a Part?

A **Part** represents a spatial component of another entity (room, item, or container). Parts are first-class entities with:
- Unique IDs
- Names players can reference
- Properties and behaviors
- Ability to serve as locations for items

### Part Anatomy

```json
{
  "id": "part_throne_north_wall",           // Unique identifier
  "entity_type": "part",                    // Must be "part"
  "name": "north wall",                     // What players type
  "part_of": "loc_throne_room",             // Parent entity ID
  "properties": {
    "material": "stone",                    // Custom properties
    "description": "Cold stone, damp."      // Examine text
  },
  "behaviors": ["behaviors.secret_door"]    // Optional behaviors
}
```

### Core Rules

1. **Every part must have a parent** - `part_of` is required
2. **Parts cannot be portable** - They're spatial components, not items
3. **Parts cannot have parts** - `part_of` cannot reference another part (nested parts not supported in current version)
4. **Items can be located at parts** - Use `"location": "part_id"`
5. **Actors use focused_on** - Actor position tracked via `properties.focused_on`, not location

## 7.4 Common Spatial Patterns

### Pattern 1: Wall-Mounted Items

**Use case**: Multiple items on walls (paintings, torches, tapestries)

**When to create wall parts**:
- ✅ 2+ items on same wall
- ✅ Different items on different walls
- ❌ Single item in entire room

**Example - Throne room with multiple wall items**:

```json
{
  "id": "loc_throne_room",
  "name": "Throne Room",
  "properties": {
    "description": "A grand chamber with stone walls."
  }
}
```

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
    "description": "A faded tapestry depicting a great battle."
  }
}
```

```json
{
  "id": "item_button",
  "name": "button",
  "location": "part_throne_north_wall",
  "properties": {
    "states": {"hidden": true},
    "description": "A small stone button set into the wall."
  },
  "behaviors": ["behaviors.hidden_button"]
}
```

**Gameplay**:
```
> look
Throne Room
A grand chamber with stone walls.

You see: throne
On the north wall: tapestry

> examine north wall
The stone wall is cold and damp. On the north wall: tapestry.

> examine tapestry
You move closer to the tapestry. A faded tapestry depicting a great battle.
```

### Pattern 2: Multi-Sided Objects

**Use case**: Workbench with different tools/activities on each side

**Example - Alchemist's bench**:

```json
{
  "id": "item_bench",
  "name": "bench",
  "location": "loc_workshop",
  "properties": {
    "portable": false,
    "description": "A long wooden work surface."
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
    "description": "Grinding tools are arranged at this end.",
    "tools": "grinding"
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
    "description": "Beakers and burners for mixing.",
    "tools": "mixing"
  }
}
```

**With position-dependent behavior**:

```python
# behaviors/alchemy.py

def on_grind(entity, accessor, context):
    """Grinding requires being at left side of bench."""
    actor_id = context["actor_id"]
    actor = accessor.get_actor(actor_id)

    focused = actor.properties.get("focused_on")
    if focused != "part_bench_left":
        return EventResult(
            allow=False,
            message="You need to be at the left side of the bench to use the grinding tools."
        )

    # Perform grinding...
    return EventResult(allow=True, message="You grind the herbs into fine powder.")
```

**Gameplay**:
```
> grind herbs
You need to be at the left side of the bench to use the grinding tools.

> approach left side of bench
You move to the left side of the bench.

> grind herbs
You grind the herbs into fine powder.
```

### Pattern 3: Floor/Ceiling Items

**Rule**: Create floor/ceiling parts when **2+ items located there** OR **special behaviors needed**.

**Example - Chapel with hidden trapdoor**:

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
    "states": {"open": false, "hidden": true}
  }
}
```

**Gameplay**:
```
> look
Chapel
A small stone chapel with simple furnishings.

You see: wooden pew
At the floor: rug

> examine floor
The stone floor is worn smooth by centuries of footsteps. At the floor: rug.

> move rug
You push aside the rug, revealing a trapdoor!

> open trapdoor
You pull open the heavy trapdoor, revealing stone steps.
```

**When NOT to create floor part**:

If only the trapdoor existed (no rug), skip the floor part:

```json
{
  "id": "item_trapdoor",
  "location": "loc_chapel",
  "properties": {
    "states": {"hidden": true}
  }
}
```

**Universal Surfaces**: The spatial system includes built-in fallback support for common room features:
- `ceiling` - "Nothing remarkable about the ceiling."
- `floor` / `ground` - "Nothing remarkable about the floor."
- `sky` - "The sky stretches above you."
- `walls` - "The walls surround you."

Players can examine these in any location without you creating explicit Part entities. However, creating explicit Parts allows you to:
- Provide custom descriptions
- Attach items to specific surfaces
- Add behaviors for interactions
- Create directional walls (north wall, south wall, etc.)

Explicit Part entities always override the universal surface fallback.

### Pattern 4: Room Areas

**Use case**: Large room divided into distinct zones

**Example - Great Hall**:

```json
{
  "id": "part_hall_entrance",
  "entity_type": "part",
  "name": "entrance area",
  "part_of": "loc_great_hall",
  "properties": {
    "description": "The entrance area near the main doors."
  }
}
```

```json
{
  "id": "part_hall_throne",
  "entity_type": "part",
  "name": "throne area",
  "part_of": "loc_great_hall",
  "properties": {
    "description": "The raised platform where the throne sits."
  }
}
```

```json
{
  "id": "item_throne",
  "name": "throne",
  "location": "part_hall_throne",
  "properties": {
    "portable": false
  }
}
```

### Pattern 5: Hidden Compartments

**Use case**: Secret area within object that requires special interaction

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

```python
# behaviors/secret_compartment.py

def on_examine(entity, accessor, context):
    """Examining back reveals secret compartment."""
    if not entity.properties.get("secret_discovered"):
        entity.properties["secret_discovered"] = True

        # Reveal hidden item
        hidden_item = accessor.get_item("item_letter")
        hidden_item.states["hidden"] = False

        return EventResult(
            allow=True,
            message="You notice a slight gap in the wood. Pressing on it reveals a hidden compartment!"
        )

    return EventResult(allow=True)
```

## 7.5 Positioning and Movement

### How Positioning Works

When a room has parts, the engine tracks actor position via `focused_on` property:

```json
{
  "id": "player",
  "location": "loc_workshop",           // Which room
  "properties": {
    "focused_on": "part_bench_left"    // Position within room
  }
}
```

### Implicit Positioning

In spatial rooms (rooms with parts), examining an item automatically moves the actor near it:

```
> examine tapestry
You move closer to the tapestry. A faded tapestry depicting a great battle.
```

The actor's `focused_on` is now set to the tapestry's location (the wall part).

### Explicit Positioning

Use the `approach` command for deliberate positioning:

```
> approach left side of bench
You move to the left side of the bench.
```

### Interaction Distance

**Default behavior**:
- All entities default to `interaction_distance: "any"` - players can interact from anywhere in the room

**When to set "near"**:
Set `interaction_distance: "near"` on entities when you want the player to automatically move near them during interaction. This provides implicit positioning for spatial realism.

```json
{
  "id": "item_bench",
  "location": "loc_workshop",
  "properties": {
    "portable": false,
    "interaction_distance": "near",
    "description": "A long workbench."
  }
}
```

Player automatically moves near bench when examining it.

**High/distant objects**:
For chandeliers, ceilings, and other distant objects, use the default ("any") so players can examine from anywhere:

```json
{
  "id": "item_chandelier",
  "location": "part_cathedral_ceiling",
  "properties": {
    "portable": false,
    "description": "A chandelier hanging far above."
  }
}
```

No `interaction_distance` needed - defaults to "any".

### Posture

Use `posture` for special positioning states:

**Cover (combat/stealth)**:

```python
def handle_take_cover(accessor, action):
    """Take cover behind object."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # ... find cover entity ...

    actor.properties["focused_on"] = entity.id
    actor.properties["posture"] = "cover"

    return EventResult(success=True, message=f"You take cover behind the {entity.name}.")
```

**Concealment**:

```python
def handle_hide_in(accessor, action):
    """Hide inside container."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # ... find hiding spot ...

    actor.properties["focused_on"] = entity.id
    actor.properties["posture"] = "concealed"

    return EventResult(success=True, message="You squeeze into the wardrobe and remain very still.")
```

**Gameplay**:
```
> hide in wardrobe
You squeeze into the wardrobe and remain very still.

> (Guard enters)
The guard looks around but doesn't spot you.
```

**Important: When Posture is Cleared**

The `posture` property is automatically cleared when the actor's `focused_on` property changes to a different entity. More specifically:

- **Cleared**: When examining or interacting with an entity that has `interaction_distance: "near"` (triggers movement and changes `focused_on`)
- **Preserved**: When examining an entity with `interaction_distance: "any"` or the default (no movement, `focused_on` may change but posture remains)
- **Replaced**: When using a different posture command (e.g., switching from "cover" to "climbing")

This allows players to look around at distant objects without leaving cover, but moving to a different nearby entity clears the posture.

## 7.6 Advanced Spatial Techniques

### Blocking Access to Parts

Use behaviors to prevent approaching certain parts:

```python
# behaviors/blocked_area.py

def on_approach(entity, accessor, context):
    """Beam blocks access to throne area."""
    if entity.id != "part_hall_throne":
        return EventResult(allow=True)

    # Check if beam is blocking
    beam = accessor.get_item("item_fallen_beam")
    if beam and beam.location == "loc_hall":
        return EventResult(
            allow=False,
            message="The fallen beam blocks your path to the throne area."
        )

    return EventResult(allow=True)
```

### Dynamic Part Properties

Change part properties during gameplay:

```python
# behaviors/structural_damage.py

def on_examine(entity, accessor, context):
    """Ceiling shows increasing damage."""
    damage_level = entity.properties.get("damage_level", 0)

    messages = {
        0: "The ceiling is solid stone.",
        1: "You notice some cracks in the ceiling.",
        2: "Large cracks spiderweb across the ceiling.",
        3: "The ceiling looks dangerously unstable!"
    }

    return EventResult(
        allow=True,
        message=messages.get(damage_level, messages[0])
    )
```

### NPC Positioning

NPCs use the same spatial properties as the player:

```python
# behaviors/guard_patrol.py

def on_turn(entity, accessor, context):
    """Guard patrols between parts."""
    if entity.id != "npc_guard":
        return EventResult(allow=True)

    patrol_points = ["part_hall_entrance", "part_hall_center", "part_hall_throne"]
    current = entity.properties.get("focused_on")

    if current in patrol_points:
        next_idx = (patrol_points.index(current) + 1) % len(patrol_points)
        entity.properties["focused_on"] = patrol_points[next_idx]

    return EventResult(allow=True)
```

### Line-of-Sight for Stealth

Check if actor is visible based on position and cover:

```python
def has_line_of_sight(accessor, observer_id, target_id):
    """Check if observer can see target."""
    target = accessor.get_actor(target_id)

    # Check if target is in cover
    if target.properties.get("posture") == "cover":
        cover_id = target.properties.get("focused_on")
        if cover_id:
            # Check if cover blocks LOS based on positions
            return False

    return True
```

## 7.7 Spatial Rooms Troubleshooting

### Common Mistakes

#### Mistake 1: Creating Parts for Everything

**Don't do this**:
```json
{
  "id": "part_key_top",
  "name": "top of key",
  "part_of": "item_key"
}
```

Simple items don't need parts. Only create parts when position matters.

#### Mistake 2: Using Parts Instead of Containers

**Core principle:** Use Container for internal storage; use Part for spatial regions.

**Don't do this**:
```json
{
  "id": "part_desk_drawer",
  "name": "drawer",
  "part_of": "item_desk"
}
```

Drawers hold items internally - they're containers, not parts.

**Do this instead**:
```json
{
  "id": "container_drawer",
  "name": "drawer",
  "location": "item_desk",
  "parent_item": "item_desk",
  "properties": {
    "openable": true
  }
}
```

**When to use Container:**
- Items are "in" it (drawer, box, bag)
- Can be opened/closed
- Internal storage

**When to use Part:**
- Items are "at" or "on" it (wall, surface, area)
- Represents spatial region
- Position matters for interaction

#### Mistake 3: Forgetting Consistent Naming

**Bad**:
- "north wall" and "eastern wall" (inconsistent)
- "left side of bench" and "bench right side" (inconsistent)

**Good**:
- "north wall", "south wall", "east wall", "west wall"
- "left side of bench", "right side of bench"

#### Mistake 4: Too Many Parts

**Bad**: Creating 4 walls + ceiling + floor for every room (8 parts)

**Good**: Only create parts when:
- 2+ items will be located at them
- Behaviors need to reference them
- Position-dependent interactions exist

### Naming Conventions

**Part IDs**: `part_<parent>_<descriptor>`
- `part_throne_north_wall`
- `part_bench_left`
- `part_hall_entrance`

**Part Names**: Use natural language players will type
- "north wall" (not "northern wall")
- "left side of bench" (not "bench left")
- "back of cabinet" (not "cabinet back")

### Universal Surface Fallback

**What it is:** The engine automatically handles common room surfaces (ceiling, floor, ground, sky, walls) without requiring explicit parts.

**Universal surfaces supported:**
- ceiling
- floor
- ground
- sky
- walls

These are defined in the vocabulary system in `behaviors/core/spatial.py`.

**How it works:**

```
> examine ceiling
Nothing remarkable about the ceiling.

> examine floor
Nothing remarkable about the floor.
```

The engine provides generic responses when no explicit part exists, avoiding "You don't see ceiling here" errors.

**When to override with parts:**

Only create ceiling/floor/wall parts when:
- **2+ items** are located there (tapestry + sconce on wall, rug + trapdoor on floor)
- **Special behaviors** needed (collapsing ceiling, secret door in wall)
- **State tracking** required (damaged floor, cracked ceiling)

**Example override:**

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

The explicit part overrides the generic fallback, providing rich description.

### Decision Flowchart

```
Do you need spatial positioning?
├─ NO → Use traditional room (no parts)
└─ YES → Ask: How many items at this location?
    ├─ Just 1 → Skip the part, item location = room
    └─ 2+ OR special behaviors → Create the part
```

## 7.8 Complete Spatial Room Example

Here's a complete spatial room showing multiple patterns:

**Room definition**:
```json
{
  "id": "loc_workshop",
  "name": "Workshop",
  "properties": {
    "description": "A cluttered alchemist's workshop."
  }
}
```

**Wall with multiple items**:
```json
{
  "id": "part_workshop_north_wall",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_workshop"
}
```

```json
{
  "id": "item_shelves",
  "name": "shelves",
  "location": "part_workshop_north_wall",
  "properties": {
    "portable": false,
    "container": {"is_surface": true}
  }
}
```

```json
{
  "id": "item_chart",
  "name": "chart",
  "location": "part_workshop_north_wall",
  "properties": {
    "portable": true,
    "description": "An alchemical reference chart."
  }
}
```

**Multi-sided bench**:
```json
{
  "id": "item_bench",
  "name": "bench",
  "location": "loc_workshop",
  "properties": {
    "portable": false,
    "provides_cover": true
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
    "description": "Grinding tools and mortars.",
    "activity": "grinding"
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
    "description": "Beakers and burners for mixing.",
    "activity": "mixing"
  }
}
```

**Gameplay**:
```
> look
Workshop
A cluttered alchemist's workshop.

You see: bench, table
On the north wall: shelves, chart

> examine north wall
The north wall. On the north wall: shelves, chart.

> approach bench
You move to the bench.

> approach left side of bench
You move to the left side of the bench.

> grind herbs
You grind the herbs into fine powder.

> approach center of bench
You move to the center of the bench.

> mix powder with water
You carefully mix the powder with water.

> take cover behind bench
You take cover behind the bench.
```

## 7.9 Spatial Rooms Summary

**Key Points**:
1. Use spatial structure when position matters for gameplay
2. Create parts when 2+ items at same location OR special behaviors needed
3. Let the engine handle implicit positioning in spatial rooms
4. Use explicit approach commands for puzzle-dependent positioning
5. Don't over-engineer - simple rooms don't need parts

**Remember**:
- Rooms without parts work fine (backward compatible)
- Spatial rooms automatically enable positioning
- Parts are first-class entities with full behavior support
- Universal surface fallback handles ceiling/floor without parts

For more technical details, see the [Spatial Structure Design Document](../docs/spatial_structure.md).

---


---

> **Next:** [Parser & Commands](08_parser.md) - Learn how commands are parsed and vocabulary is managed
