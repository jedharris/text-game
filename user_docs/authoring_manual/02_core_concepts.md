# Core Concepts

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Previous: [Overview & Quick Start](01_overview.md) | Next: [Actors](03_actors.md)

---

# 3. Core Concepts

## 3.1 The Game World

Your game world consists of:

### Locations (Rooms)

**What they are:** Places in your game world where things happen.

**Key properties:**
- `id` - Unique identifier (e.g., "loc_tower_entrance")
- `name` - Player-visible name (e.g., "Tower Entrance")
- `description` - What players see when they look
- `exits` - Connections to other locations (e.g., north, south, up)

**Example:**
```json
{
  "id": "loc_tower",
  "name": "Tower Top",
  "description": "A circular chamber at the tower's peak. Wind whistles through narrow windows.",
  "exits": {
    "down": {
      "type": "open",
      "to": "loc_tower_stairs"
    }
  }
}
```

### Items (Objects)

**What they are:** Things in the world that players can interact with.

Items can be:
- Simple objects (keys, books, gems)
- Containers (chests, boxes, tables)
- Doors (wooden door, iron gate)
- Furniture (desk, pedestal, altar)

**Key properties:**
- `id` - Unique identifier (e.g., "item_sword")
- `name` - What players call it (e.g., "sword")
- `description` - What they see when examining
- `location` - Where it is (location ID, container ID, or actor ID)
- `properties` - Flexible attributes (portable, container, door, etc.)

**Example simple item:**
```json
{
  "id": "item_sword",
  "name": "sword",
  "description": "A well-balanced steel sword with a leather grip.",
  "location": "loc_armory",
  "properties": {
    "portable": true,
    "weapon": true
  }
}
```

### Actors (Player and NPCs)

**What they are:** Characters in the game world.

The player is always an actor with id `"player"`. NPCs are additional actors.

**Key properties:**
- `id` - Unique identifier ("player" or "npc_guard")
- `name` - Character name
- `description` - What players see when examining
- `location` - Current location
- `inventory` - List of item IDs they're carrying

**Example NPC:**
```json
{
  "id": "npc_merchant",
  "name": "Merchant",
  "description": "A jovial merchant with a ready smile.",
  "location": "loc_market",
  "inventory": ["item_coins"]
}
```

For comprehensive actor documentation, see [Actors](03_actors.md) and [Actor Interactions](04_actor_interactions.md).

### IDs vs Names

**Important distinction:**

- **IDs** are internal identifiers (must be globally unique)
  - Example: `"loc_dark_forest"`, `"item_magic_key"`
  - Used for references and code

- **Names** are what players see (can duplicate)
  - Example: `"Forest"`, `"key"`
  - Used for commands and narration

**Recommended ID format:** `<type>_<descriptive_name>`
- Locations: `loc_tower`, `loc_garden`, `loc_throne_room`
- Items: `item_key`, `item_chest`, `item_sword`
- Doors: `door_entrance`, `door_secret`
- NPCs: `npc_guard`, `npc_wizard`, `npc_merchant`
- Locks: `lock_treasure`, `lock_gate`

The special ID `"player"` is reserved for the player character.

## 3.2 Game State JSON Format

Your game world is defined in `game_state.json`. Let's look at each section:

### Metadata Section

```json
{
  "metadata": {
    "title": "The Lost Tower",           // Required: Game title
    "author": "Your Name",                // Optional: Your name
    "version": "1.0",                     // Optional: Version number
    "description": "A mysterious tower...", // Optional: Game description
    "start_location": "loc_entrance"      // Required: Where player starts
  }
}
```

### Locations Section

```json
{
  "locations": [
    {
      "id": "loc_entrance",               // Required: Unique ID
      "name": "Tower Entrance",           // Required: Display name
      "description": "A grand archway...", // Required: Room description
      "exits": {                          // Optional: Connections
        "north": {
          "type": "open",                 // "open" or "door"
          "to": "loc_hallway",            // Destination location
          "name": "stone archway",        // Optional: Exit name
          "description": "An archway..."  // Optional: Exit description
        },
        "east": {
          "type": "door",
          "to": "loc_storage",
          "door_id": "door_storage"       // References door item
        }
      },
      "properties": {},                   // Optional: Custom properties
      "behaviors": []                     // Optional: Behavior modules
    }
  ]
}
```

### Items Section

**Simple item:**
```json
{
  "id": "item_key",
  "name": "key",
  "description": "A brass key with intricate engravings.",
  "location": "loc_entrance",             // Where it is
  "properties": {
    "portable": true                      // Can be picked up
  },
  "behaviors": []                         // Optional behaviors
}
```

**Container item:**
```json
{
  "id": "item_chest",
  "name": "chest",
  "description": "A sturdy wooden chest.",
  "location": "loc_entrance",
  "properties": {
    "portable": false,                    // Too heavy to carry
    "container": {
      "is_surface": false,                // Enclosed container (not a table)
      "capacity": 10,                     // Max items (0 = unlimited)
      "open": false,                      // Currently closed
      "locked": false                     // Not locked
    }
  }
}
```

**Door item:**
```json
{
  "id": "door_storage",
  "name": "door",
  "description": "A simple wooden door.",
  "location": "exit:loc_entrance:east",   // Special location format for doors
  "door": {                               // Door properties (top level, not in properties)
    "open": false,
    "locked": true,
    "lock_id": "lock_storage"             // References lock
  }
}
```

**Item location values:**
- `"loc_room"` - Item is in that location
- `"player"` - Item is in player's inventory
- `"npc_guard"` - Item is in NPC's inventory
- `"item_chest"` - Item is inside a container
- `"exit:loc_entrance:east"` - Door attached to an exit (special format)

### Locks Section

```json
{
  "locks": [
    {
      "id": "lock_storage",
      "name": "lock",
      "description": "A simple lock.",
      "properties": {
        "opens_with": ["item_key"],       // Item IDs that unlock
        "auto_unlock": false              // Must explicitly unlock
      }
    }
  ]
}
```

### Actors Section

```json
{
  "actors": {
    "player": {                           // Required: Must have player
      "id": "player",
      "name": "Adventurer",
      "description": "A brave explorer.",
      "location": "loc_entrance",         // Starting location
      "inventory": []                     // Starting inventory
    },
    "npc_guard": {                        // Optional: NPCs
      "id": "npc_guard",
      "name": "Guard",
      "description": "A stern guard in armor.",
      "location": "loc_hallway",
      "inventory": ["item_sword"]
    }
  }
}
```

## 3.3 Properties and States

The `properties` dict is your flexible data store for entity attributes.

### Common Properties

**For items:**
```json
{
  "properties": {
    "portable": true,                     // Can be picked up
    "weapon": true,                       // Custom game property
    "provides_light": true,               // Light source
    "readable": true,                     // Can be read
    "container": {                        // Container properties
      "is_surface": true,                 // Table/pedestal
      "capacity": 5,
      "open": true
    }
  }
}
```

**For actors:**
```json
{
  "properties": {
    "stats": {                            // Numeric attributes
      "health": 100,
      "strength": 10
    },
    "flags": {                            // Boolean flags
      "hostile": false,
      "knows_secret": true
    }
  }
}
```

### States vs Properties

**Use properties for:** Static or semi-permanent attributes
- Is it portable?
- Is it a weapon?
- Container capacity

**Use states for:** Dynamic game state that changes during play
- Is the lamp lit?
- Is the item hidden?
- Has the puzzle been solved?

**States are stored in properties:**
```json
{
  "properties": {
    "portable": true,
    "provides_light": true,
    "states": {                           // States nested in properties
      "lit": false,                       // Dynamic: changes during game
      "examined": false
    }
  }
}
```

**Access in code:**
```python
# In behavior code:
if entity.states.get("lit", False):
    # Lamp is lit
    ...

entity.states["lit"] = True  # Light the lamp
```

## 3.4 LLM Context for Narration

The `llm_context` section provides information to the LLM narrator to create rich descriptions.

### Structure

```json
{
  "llm_context": {
    "traits": [                           // Descriptive attributes
      "ancient oak",
      "brass fittings",
      "heavy",
      "ornate carvings"
    ],
    "state_variants": {                   // Conditional descriptions
      "open": "lid thrown back, contents visible",
      "closed": "sealed tight",
      "locked": "secured with an iron lock"
    },
    "atmosphere": "mysterious, foreboding, ancient"  // Mood
  }
}
```

### Traits

Traits are descriptive attributes the LLM uses to add flavor.

**Good traits:**
- Sensory: "cold iron", "musty smell", "smooth stone"
- Visual: "gleaming brass", "weathered oak", "intricate runes"
- Textural: "rough surface", "smooth edges", "jagged"
- Atmospheric: "ominous", "inviting", "mysterious"

**Trait randomization:** The engine randomly selects a subset of traits for each narration, providing variety on repeated interactions.

**Example:**
```json
{
  "id": "item_sword",
  "name": "sword",
  "description": "An ancient blade.",
  "llm_context": {
    "traits": [
      "razor-sharp",
      "rune-etched blade",
      "worn leather grip",
      "perfect balance",
      "cold steel",
      "battle-scarred"
    ]
  }
}
```

First examination might mention: "razor-sharp", "rune-etched blade", "perfect balance"
Second examination might mention: "cold steel", "worn leather grip", "battle-scarred"

### State Variants

State variants provide conditional descriptions based on entity state.

**Example:**
```json
{
  "id": "item_lantern",
  "name": "lantern",
  "description": "A brass lantern.",
  "properties": {
    "provides_light": true,
    "states": {
      "lit": false
    }
  },
  "llm_context": {
    "traits": ["brass", "hexagonal", "wire handle"],
    "state_variants": {
      "lit": "glowing warmly, casting dancing shadows",
      "unlit": "dark and cold, waiting to be lit",
      "examined": "well-crafted, with intricate engravings"
    }
  }
}
```

The LLM uses the appropriate state variant based on current entity state.

### Best Practices

1. **Use 5-8 traits** - Enough for variety, not overwhelming
2. **Be specific** - "weathered oak" better than "old"
3. **Engage senses** - Touch, smell, sound, not just sight
4. **Match tone** - Traits should fit your game's atmosphere
5. **State variants are optional** - Only add if state matters for description

---

> **Next:** [Actors](03_actors.md) - Learn about creating players, NPCs, creatures, and constructs
