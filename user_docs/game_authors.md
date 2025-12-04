# Text Adventure Game Framework - Game Author Guide

## Document Purpose

This guide is for game authors who want to create interactive fiction games using this framework. You'll learn how to:
- Create new games from scratch
- Define locations, items, and characters
- Write custom behaviors and puzzles
- Integrate with the LLM narrator
- Test and debug your game

**Not for engine developers** - If you want to extend the core engine or contribute code, see the Developer Documentation instead.

---

# 1. Overview

## 1.1 What is This Framework?

This is a text adventure game framework that combines:
- **Traditional parser-based gameplay** - Fast, deterministic command processing
- **LLM-powered narration** - Rich, dynamic storytelling via Claude or other LLMs
- **Behavior-driven extension** - Add new functionality through Python modules
- **JSON-based world definition** - Define your game world in readable JSON files

## 1.2 Design Philosophy

**Core Principles:**

1. **Author Capability** - The framework maximizes what you can create
2. **Player Agency** - Players have rich interactions with your world
3. **Separation of Concerns** - The engine manages state, the LLM narrates
4. **Extension Through Behaviors** - Add new functionality without modifying core code
5. **First-Class Entities** - All entities participate fully in narration and action

**How It Works:**

```
Player: "take the rusty key from the wooden chest"
    ↓
Parser: Understands common commands instantly
    ↓
Game Engine: Updates game state (key moves to inventory)
    ↓
LLM Narrator: Creates vivid prose description
    ↓
Player sees: "You reach into the old chest and carefully lift out the
             rusty key. Its cold metal feels rough against your palm,
             and you notice strange markings etched along its length."
```

**The Key Rule:** The game engine is responsible for ALL state management. The LLM never changes game state - it only narrates what happened.

## 1.3 Extension Model

Your game is built in three tiers:

```
┌─────────────────────────────────────┐
│   Your Game-Specific Behaviors      │  ← Your custom puzzles and mechanics
│   (examples/my_game/behaviors/)     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Shared Behavior Libraries         │  ← Reusable puzzle mechanics
│   (behavior_libraries/)             │     (optional)
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Core Behaviors                    │  ← Built-in game mechanics
│   (behaviors/core/)                 │     (take, examine, go, etc.)
└─────────────────────────────────────┘
```

Your game combines:
- **Core behaviors** (built-in): Movement, object manipulation, perception
- **Libraries** (optional): Reusable puzzle mechanics from shared libraries
- **Your behaviors** (custom): Unique puzzles and interactions for your game

---

# 2. Quick Start

## 2.1 Your First Game

Let's create a minimal game to understand the structure.

**Step 1: Create game directory**
```bash
mkdir -p my_first_game/behaviors
cd my_first_game
```

**Step 2: Create game_state.json**
```json
{
  "metadata": {
    "title": "My First Adventure",
    "author": "Your Name",
    "version": "1.0",
    "description": "A simple test game",
    "start_location": "loc_start"
  },
  "locations": [
    {
      "id": "loc_start",
      "name": "Starting Room",
      "description": "A small, cozy room with wooden walls.",
      "exits": {
        "north": {
          "type": "open",
          "to": "loc_garden"
        }
      }
    },
    {
      "id": "loc_garden",
      "name": "Garden",
      "description": "A peaceful garden with blooming flowers.",
      "exits": {
        "south": {
          "type": "open",
          "to": "loc_start"
        }
      }
    }
  ],
  "items": [
    {
      "id": "item_key",
      "name": "key",
      "description": "A small brass key.",
      "location": "loc_start",
      "properties": {
        "portable": true
      }
    }
  ],
  "locks": [],
  "actors": {
    "player": {
      "id": "player",
      "name": "Adventurer",
      "description": "That's you!",
      "location": "loc_start",
      "inventory": []
    }
  }
}
```

**Step 3: Create narrator_style.txt**
```
You are narrating a cozy, lighthearted adventure game.

Style Guidelines:
- Use warm, friendly tone
- Keep descriptions concise but evocative
- Emphasize textures and sensory details
- Add gentle humor when appropriate

Example narration:
- "You pick up the brass key. It's surprisingly warm to the touch."
- "The garden welcomes you with the scent of roses and lavender."
```

**Step 4: Create behaviors directory with core symlink**
```bash
# From inside my_first_game/
mkdir behaviors
cd behaviors
ln -s ../../behaviors/core core
cd ../..
```

**Step 5: Run your game**
```bash
# Make sure you have ANTHROPIC_API_KEY set
export ANTHROPIC_API_KEY=your-key-here

python -m src.llm_game my_first_game
```

**Try these commands:**
```
> look
> examine key
> take key
> inventory
> north
> look
> south
```

Congratulations! You've created your first game.

## 2.2 Making Your First Change

Let's add a flower you can pick.

**Edit game_state.json**, add to the items array:
```json
{
  "id": "item_rose",
  "name": "rose",
  "description": "A beautiful red rose.",
  "location": "loc_garden",
  "properties": {
    "portable": true,
    "fragrant": true
  }
}
```

Restart the game and try:
```
> north
> examine rose
> take rose
> smell rose
```

The engine handles taking the rose automatically. The LLM creates unique narration using the description and properties.

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

# 4. The Behavior System

The behavior system is how you extend the game with new functionality. This is the most powerful feature of the framework.

## 4.1 What Are Behaviors?

**Behaviors are Python modules that provide:**

1. **Vocabulary** - New verbs and their synonyms
2. **Command Handlers** - Functions that process commands (`handle_<verb>`)
3. **Entity Behaviors** - Functions that respond to events on specific entities (`on_<event>`)

**Example behavior module structure:**
```python
# behaviors/magic_items.py

# 1. Vocabulary (optional)
VOCABULARY = {
    "verbs": [
        {
            "word": "cast",
            "synonyms": ["invoke", "recite"],
            "object_required": True
        }
    ]
}

# 2. Command handler (optional)
def handle_cast(accessor, action):
    """Handle the 'cast' command."""
    # Implementation...
    return EventResult(success=True, message="...")

# 3. Entity behavior (optional)
def on_take(entity, accessor, context):
    """Called when entity is taken."""
    if entity.properties.get("magical"):
        entity.states["glowing"] = True
        return EventResult(allow=True,
                         message="The item glows as you touch it!")
    return EventResult(allow=True)
```

## 4.2 Three-Tier Hierarchy

Behaviors are organized in three tiers:

```
Your Game (Tier 1)
    ├─ Custom puzzles
    ├─ Unique mechanics
    └─ Game-specific logic
        ↓ Can call
Shared Libraries (Tier 2)
    ├─ Puzzle patterns
    ├─ Reusable mechanics
    └─ Generic handlers
        ↓ Can call
Core Behaviors (Tier 3)
    ├─ Movement (go, enter, exit)
    ├─ Manipulation (take, drop, put)
    ├─ Perception (examine, look, inventory)
    ├─ Interaction (open, close, unlock, lock)
    └─ Meta (help, save, load, quit)
```

**Precedence:** Game > Library > Core

When multiple modules provide handlers for the same verb, game-specific handlers are called first.

### How Tiers Are Determined

Tiers are calculated automatically based on **directory depth** in your game's `behaviors/` folder:

```
behaviors/
  my_puzzle.py              # Tier 1 (depth 0 - directly in behaviors/)
  lib/                      # Directory (not a tier)
    spatial/                # Tier 2 (depth 1 - one level down)
      stand_sit.py
    core/                   # Tier 2 (depth 1 - symlink at depth 1)
      -> ../../../behaviors/core/
```

**Key principles:**
- **Depth = subdirectory levels** below `behaviors/`, not counting the file itself
- **Tier = Depth + 1** (so depth 0 → Tier 1, depth 1 → Tier 2, etc.)
- **Symlinks work naturally** - tier is based on where the symlink appears in your game structure, not the engine's internal structure
- **You control tiers** by organizing your directory structure

**Example:** If you create `behaviors/lib/core/` as a symlink to the engine's core behaviors, those handlers become Tier 3 because the symlink is at depth 2 in your game's directory structure.

**Common patterns:**

*Pattern 1: Game + Core (2 tiers)*
```
behaviors/
  my_game.py           # Tier 1
  core/ -> engine      # Tier 2
```

*Pattern 2: Game + Library + Core (3 tiers)*
```
behaviors/
  my_game.py           # Tier 1
  lib/
    spatial/           # Tier 2
      stand_sit.py
    core/ -> engine    # Tier 3 (nested deeper)
```

*Pattern 3: Multiple libraries*
```
behaviors/
  my_game.py           # Tier 1
  lib/
    puzzles/           # Tier 2
    spatial/           # Tier 2
    contrib/
      core/ -> engine  # Tier 4 (deeply nested)
```

## 4.3 Using Core Behaviors

Core behaviors provide standard adventure game commands:

### Movement
- `go <direction>` - Move to another location
- Bare directions work: `north`, `south`, `up`, `down`, etc.

### Manipulation
- `take <item>` - Pick up an item
- `drop <item>` - Drop an item from inventory
- `put <item> in/on <container>` - Place item in/on container
- `take <item> from <container>` - Take item from container

### Perception
- `look` or `l` - Describe current location
- `examine <thing>` or `x <thing>` - Examine in detail
- `inventory` or `i` - List items you're carrying

### Interaction
- `open <container/door>` - Open something
- `close <container/door>` - Close something
- `unlock <door/container> with <key>` - Unlock with key
- `lock <door/container> with <key>` - Lock with key
- `push <item>` - Push an object
- `pull <item>` - Pull an object
- `turn <item>` - Turn/rotate an object
- `read <item>` - Read text
- `light <item>` - Light a light source
- `extinguish <item>` - Put out a light

### Meta Commands
- `help` - Show available commands
- `save` - Save game state
- `load` - Load game state
- `quit` - Exit game

**To use core behaviors:**
```bash
# In your game's behaviors directory
ln -s ../../../behaviors/core core
```

That's it! Core behaviors are automatically loaded.

## 4.4 Using Behavior Libraries

Behavior libraries are reusable behavior packages for common patterns.

### Available Libraries

**puzzle_lib** - Puzzle mechanics
- Sequence tracking (combinations, musical puzzles)
- Threshold checking (weight puzzles, resource puzzles)
- State revelation (hidden items, progressive descriptions)

**offering_lib** - Offering mechanics
- Item offerings to altars/wells/shrines
- Blessing and curse effects
- Alignment tracking

### Using a Library

```bash
# In your game's behaviors directory
ln -s ../../../behavior_libraries/puzzle_lib puzzle_lib
```

Then use library functions in your behavior modules:
```python
# my_game/behaviors/music_box.py
from behavior_libraries.puzzle_lib import sequence_tracker

def on_turn(entity, accessor, context):
    """Handle turning the music box."""
    note = entity.states.get("current_note", "C")

    # Track the sequence
    sequence_tracker.track_action(entity, note)

    # Check if correct melody played
    if sequence_tracker.check_sequence(entity, ["C", "E", "G", "C"]):
        # Success!
        return EventResult(allow=True,
                         message="The music box chimes and opens!")

    return EventResult(allow=True,
                     message=f"The music box plays a {note} note.")
```

## 4.5 Writing Custom Behaviors

This is where you create unique mechanics for your game.

### Behavior Module Structure

Create a Python file in your game's `behaviors/` directory:

```python
# my_game/behaviors/magic_mirror.py

from src.state_accessor import EventResult

# Optional: Add new vocabulary
VOCABULARY = {
    "verbs": [
        {
            "word": "peer",
            "synonyms": ["gaze", "stare"],
            "object_required": True,
            "narration_mode": "tracking"  # or "brief"
        }
    ]
}

# Optional: Command handler
def handle_peer(accessor, action):
    """Handle 'peer' command."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # Find object to peer at
    obj_entry = action.get("object")
    if not obj_entry:
        return EventResult(success=False,
                         message="What do you want to peer at?")

    entity = accessor.find_entity_in_location(
        obj_entry,
        actor.location,
        action.get("adjective")
    )

    if not entity:
        return EventResult(success=False,
                         message=f"You don't see {obj_entry.word} here.")

    # Check if entity has on_peer behavior
    if accessor.behavior_manager:
        result = accessor.behavior_manager.invoke_behavior(
            entity, "on_peer", accessor.state,
            {"actor_id": actor_id}
        )
        if result and result.message:
            return EventResult(success=True, message=result.message)

    # Default behavior
    return EventResult(success=True,
                     message=f"You peer at {entity.name}.")

# Optional: Entity behavior
def on_peer(entity, accessor, context):
    """Called when player peers at this entity."""
    if entity.id == "item_magic_mirror":
        # Magic mirror shows hidden item
        hidden_key = accessor.get_item("item_hidden_key")
        if hidden_key and hidden_key.states.get("hidden", False):
            hidden_key.states["hidden"] = False
            return EventResult(
                allow=True,
                message="In the mirror's reflection, you see a key hidden behind the mirror!"
            )

    return EventResult(allow=True)
```

### StateAccessor API

The `accessor` parameter provides access to game state:

**Query methods:**
```python
accessor.get_location(location_id)          # Get location by ID
accessor.get_item(item_id)                  # Get item by ID
accessor.get_actor(actor_id)                # Get actor by ID
accessor.get_lock(lock_id)                  # Get lock by ID

accessor.get_items_in_location(location_id) # Get all items in location
accessor.get_actors_in_location(location_id)# Get all actors in location
accessor.get_items_in_container(container_id) # Get items in container

accessor.find_entity_in_location(           # Find entity by name/synonyms
    word_entry,                             # WordEntry from vocabulary
    location_id,                            # Where to search
    adjective=None                          # Optional adjective for disambiguation
)
```

**State update methods:**
```python
# Update entity and invoke its behaviors
result = accessor.update(
    entity,                    # Entity to update
    {"states.lit": True},      # Changes to apply
    verb="light",              # Optional: trigger on_light behaviors
    actor_id="player"          # Who is acting
)

# Result contains:
# - success: bool
# - message: str
# - changes_applied: dict
```

**Handler invocation:**
```python
# Call another command handler
result = accessor.invoke_handler("take", action)

# Call previous handler in chain (for handler precedence)
result = accessor.invoke_previous_handler("take", action)
```

### EventResult Return Values

All handlers and behaviors return `EventResult`:

```python
from src.state_accessor import EventResult

# Success
return EventResult(
    success=True,           # Command succeeded
    message="You take the key.",
    data={"id": "item_key", "name": "key"}  # Optional extra data
)

# Failure
return EventResult(
    success=False,
    message="You can't take that."
)

# Entity behavior - allow action
return EventResult(
    allow=True,             # Allow the action to proceed
    message="Custom message"  # Optional custom message
)

# Entity behavior - deny action
return EventResult(
    allow=False,            # Prevent the action
    message="The magic prevents you from taking it!"
)
```

### Registering Behaviors on Entities

To attach a behavior to a specific entity, add the module path to its `behaviors` list:

```json
{
  "id": "item_magic_mirror",
  "name": "mirror",
  "description": "An ornate silver mirror.",
  "location": "loc_chamber",
  "properties": {
    "portable": false,
    "magical": true
  },
  "behaviors": [
    "behaviors.magic_mirror"    // Your behavior module
  ]
}
```

Now when someone interacts with the mirror (peer, examine, touch, etc.), your behavior functions will be called.

## 4.6 Behavior Precedence and Chaining

When multiple modules provide handlers for the same verb, they form a chain:

**Example scenario:**
- Core provides `handle_take` (basic taking)
- Your game provides `handle_take` (custom rules)

**Execution order:**
1. Your game's `handle_take` is called first
2. You can add custom logic
3. You can call `accessor.invoke_previous_handler("take", action)` to delegate to core
4. Or you can completely replace core behavior

**Example:**
```python
# my_game/behaviors/custom_take.py

def handle_take(accessor, action):
    """Custom take handler with weight limits."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # Custom logic: Check weight limit
    current_weight = sum(
        accessor.get_item(item_id).properties.get("weight", 0)
        for item_id in actor.inventory
    )

    obj_entry = action.get("object")
    entity = accessor.find_entity_in_location(obj_entry, actor.location)

    if entity:
        item_weight = entity.properties.get("weight", 0)
        if current_weight + item_weight > 100:
            return EventResult(success=False,
                             message="That's too heavy to carry!")

    # Delegate to core handler for normal take logic
    return accessor.invoke_previous_handler("take", action)
```

---

# 5. Common Patterns and Recipes

## 5.1 Puzzles

### Hidden Items (Revelation)

**Goal:** Item is hidden until revealed by some action.

**Pattern:**
```json
{
  "id": "item_secret_key",
  "name": "key",
  "description": "A hidden key.",
  "location": "loc_study",
  "properties": {
    "portable": true,
    "states": {
      "hidden": true       // Item starts hidden
    }
  }
}
```

**Behavior to reveal:**
```python
# behaviors/secret_panel.py

def on_push(entity, accessor, context):
    """Pushing the panel reveals the key."""
    if entity.id == "item_panel":
        key = accessor.get_item("item_secret_key")
        if key and key.states.get("hidden", False):
            key.states["hidden"] = False
            return EventResult(
                allow=True,
                message="The panel slides aside, revealing a hidden key!"
            )
    return EventResult(allow=True)
```

### Locked Containers and Doors

**Pattern:**
```json
{
  "id": "item_chest",
  "name": "chest",
  "description": "A locked chest.",
  "location": "loc_treasury",
  "properties": {
    "portable": false,
    "container": {
      "is_surface": false,
      "capacity": 10,
      "open": false,
      "locked": true,
      "lock_id": "lock_chest"
    }
  }
}
```

```json
{
  "id": "lock_chest",
  "name": "lock",
  "description": "An iron lock.",
  "properties": {
    "opens_with": ["item_iron_key"],  // Key that unlocks
    "auto_unlock": false              // Must explicitly unlock
  }
}
```

**Commands:**
```
> unlock chest with iron key
> open chest
> take gem from chest
```

### Sequence Puzzles

**Goal:** Player must perform actions in correct order.

**Using puzzle_lib:**
```python
# behaviors/musical_puzzle.py
from behavior_libraries.puzzle_lib import sequence_tracker

def on_play(entity, accessor, context):
    """Handle playing notes on the harp."""
    note = context.get("note")  # Which string was played

    sequence_tracker.track_action(entity, note)

    # Check if melody is correct
    correct_melody = ["C", "E", "G", "E", "C"]
    if sequence_tracker.check_sequence(entity, correct_melody):
        # Success! Open the door
        door = accessor.get_item("door_music_chamber")
        door.door_locked = False
        door.door_open = True

        return EventResult(
            allow=True,
            message="The harp resonates with a beautiful chord, and you hear a door unlock!"
        )

    current = entity.states.get("sequence", [])
    if len(current) >= len(correct_melody):
        # Wrong sequence, reset
        sequence_tracker.reset_sequence(entity)
        return EventResult(
            allow=True,
            message="The notes sound discordant. Try again."
        )

    return EventResult(allow=True)
```

### Threshold/Weight Puzzles

**Goal:** Achieve exact weight or resource amount.

**Using puzzle_lib:**
```python
# behaviors/balance_puzzle.py
from behavior_libraries.puzzle_lib import threshold_checker

def on_put(entity, accessor, context):
    """Handle placing items on the scale."""
    if entity.id != "item_scale":
        return EventResult(allow=True)

    # Calculate total weight on scale
    items_on_scale = accessor.get_items_in_container("item_scale")
    total_weight = sum(
        item.properties.get("weight", 0)
        for item in items_on_scale
    )

    target_weight = 50  # Exact weight needed

    if threshold_checker.check_threshold(total_weight, target_weight, tolerance=0):
        # Perfect balance!
        secret_door = accessor.get_item("door_secret")
        secret_door.states["revealed"] = True
        return EventResult(
            allow=True,
            message="The scale balances perfectly, and a door swings open!"
        )
    else:
        # Give feedback
        feedback = threshold_checker.get_threshold_feedback(
            total_weight,
            target_weight
        )
        return EventResult(allow=True, message=feedback)
```

## 5.2 Interactive Objects

### Containers (Chests, Boxes, Surfaces)

**Enclosed container (chest, box):**
```json
{
  "id": "item_chest",
  "name": "chest",
  "description": "A wooden chest.",
  "location": "loc_room",
  "properties": {
    "portable": false,
    "container": {
      "is_surface": false,    // Enclosed
      "capacity": 10,
      "open": false           // Must open to see contents
    }
  }
}
```

**Surface (table, pedestal):**
```json
{
  "id": "item_table",
  "name": "table",
  "description": "A wooden table.",
  "location": "loc_room",
  "properties": {
    "portable": false,
    "container": {
      "is_surface": true,     // Surface
      "capacity": 5           // Can hold 5 items
    }
  }
}
```

**Items in containers:**
```json
{
  "id": "item_gem",
  "name": "gem",
  "description": "A sparkling gem.",
  "location": "item_chest",   // Inside the chest
  "properties": {
    "portable": true
  }
}
```

### Light Sources

**Lantern with states:**
```json
{
  "id": "item_lantern",
  "name": "lantern",
  "description": "A brass lantern.",
  "location": "loc_start",
  "properties": {
    "portable": true,
    "provides_light": true,
    "states": {
      "lit": false
    }
  },
  "behaviors": ["behaviors.core.light_sources"]
}
```

**Commands:**
```
> take lantern
> light lantern
> extinguish lantern
```

Core behavior handles the mechanics automatically.

### Readable Items

**Book with custom read behavior:**
```json
{
  "id": "item_spellbook",
  "name": "spellbook",
  "description": "An ancient tome.",
  "location": "loc_library",
  "properties": {
    "portable": true,
    "readable": true,
    "text": "The spell of opening: Speak 'alohomora' to any lock."
  }
}
```

Core `read` command will show the text automatically.

**For complex reading (progressive revelation):**
```python
# behaviors/progressive_book.py

def on_read(entity, accessor, context):
    """Reading reveals more each time."""
    if entity.id == "item_ancient_book":
        times_read = entity.states.get("times_read", 0)
        times_read += 1
        entity.states["times_read"] = times_read

        if times_read == 1:
            return EventResult(allow=True,
                             message="The first page describes a ritual...")
        elif times_read == 2:
            return EventResult(allow=True,
                             message="The second page reveals the ingredients...")
        else:
            return EventResult(allow=True,
                             message="You've learned all the book contains.")

    return EventResult(allow=True)
```

## 5.3 NPCs and Dialogue

### Creating NPCs

**Basic NPC:**
```json
{
  "id": "npc_merchant",
  "name": "Merchant",
  "description": "A friendly merchant.",
  "location": "loc_market",
  "inventory": ["item_coins"],
  "properties": {
    "dialogue": [
      "Welcome to my shop!",
      "I have the finest goods!",
      "Safe travels, friend."
    ]
  }
}
```

### NPC with State-Based Dialogue

```python
# behaviors/npc_merchant.py

VOCABULARY = {
    "verbs": [
        {"word": "talk", "synonyms": ["speak", "chat"], "object_required": True},
        {"word": "ask", "synonyms": ["question"], "object_required": True}
    ]
}

def handle_talk(accessor, action):
    """Handle talking to NPCs."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    obj_entry = action.get("object")
    entity = accessor.find_entity_in_location(obj_entry, actor.location)

    if not entity or not hasattr(entity, 'inventory'):  # Not an NPC
        return EventResult(success=False,
                         message=f"You can't talk to {obj_entry.word}.")

    # Check for on_talk behavior
    if accessor.behavior_manager:
        result = accessor.behavior_manager.invoke_behavior(
            entity, "on_talk", accessor.state,
            {"actor_id": actor_id}
        )
        if result and result.message:
            return EventResult(success=True, message=result.message)

    # Default dialogue
    dialogue = entity.properties.get("dialogue", [])
    if dialogue:
        return EventResult(success=True, message=dialogue[0])

    return EventResult(success=True,
                     message=f"{entity.name} has nothing to say.")

def on_talk(entity, accessor, context):
    """State-based dialogue for merchant."""
    if entity.id == "npc_merchant":
        actor_id = context["actor_id"]
        actor = accessor.get_actor(actor_id)

        # Check if player has bought something
        if entity.states.get("sold_item", False):
            return EventResult(allow=True,
                             message="Thank you for your business!")

        # Check if player has money
        has_coins = "item_coins" in actor.inventory
        if has_coins:
            return EventResult(allow=True,
                             message="I see you have coins! Care to buy something?")
        else:
            return EventResult(allow=True,
                             message="Come back when you have some coins!")

    return EventResult(allow=True)
```

### NPC Inventory and Trading

NPCs can carry items just like the player:

```python
# behaviors/trading.py

def handle_trade(accessor, action):
    """Trade items with NPC."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)

    # Get what player offers
    offer_entry = action.get("object")
    offer_item = accessor.find_entity_in_location(offer_entry, actor.location)

    # Get NPC
    npc_entry = action.get("indirect_object")
    npc = accessor.find_entity_in_location(npc_entry, actor.location)

    if not npc or not hasattr(npc, 'inventory'):
        return EventResult(success=False, message="Trade with whom?")

    # Check if NPC accepts this trade
    if offer_item.id == "item_coins" and npc.id == "npc_merchant":
        # Give player the sword from merchant
        sword = accessor.get_item("item_sword")
        sword.location = actor_id
        actor.inventory.append("item_sword")

        # Take coins
        offer_item.location = npc.id
        actor.inventory.remove("item_coins")
        npc.inventory.append("item_coins")

        npc.states["sold_item"] = True

        return EventResult(success=True,
                         message="The merchant hands you a fine sword!")

    return EventResult(success=False,
                     message="The merchant isn't interested in that.")
```

## 5.4 Locations and Navigation

### Exit Types

**Open passage:**
```json
{
  "north": {
    "type": "open",
    "to": "loc_hallway"
  }
}
```

**Door:**
```json
{
  "east": {
    "type": "door",
    "to": "loc_storage",
    "door_id": "door_storage"
  }
}
```

**Named exits:**
```json
{
  "up": {
    "type": "open",
    "to": "loc_tower_top",
    "name": "spiral staircase",
    "description": "A narrow staircase winds upward."
  }
}
```

Players can use: `go up`, `climb spiral staircase`, `examine staircase`

### Exit Descriptions and Traits

Add `llm_context` to exits for richer descriptions:

```json
{
  "north": {
    "type": "open",
    "to": "loc_cavern",
    "name": "dark passage",
    "description": "A narrow passage leads into darkness.",
    "properties": {
      "llm_context": {
        "traits": [
          "dripping water",
          "musty air",
          "echo of footsteps",
          "cold draft"
        ],
        "atmosphere": "foreboding, mysterious"
      }
    }
  }
}
```

### Hidden Exits

Use states to hide exits:

```json
{
  "west": {
    "type": "open",
    "to": "loc_secret_room",
    "name": "hidden door",
    "description": "A concealed door.",
    "properties": {
      "states": {
        "hidden": true
      }
    }
  }
}
```

**Behavior to reveal:**
```python
def on_push(entity, accessor, context):
    """Pushing the stone reveals the door."""
    if entity.id == "item_loose_stone":
        location = accessor.get_location(entity.location)
        west_exit = location.exits.get("west")
        if west_exit and west_exit.properties.get("states", {}).get("hidden"):
            west_exit.properties["states"]["hidden"] = False
            return EventResult(allow=True,
                             message="The wall shifts, revealing a hidden door!")
    return EventResult(allow=True)
```

### One-Way Passages

Simply don't define the return exit:

```json
// From tower_top
{
  "down": {
    "type": "open",
    "to": "loc_chasm_floor"  // Can go down...
  }
}

// From chasm_floor - no "up" exit defined
// Player can't climb back up
```

### Conditional Exits

**Exits that require conditions:**
```python
# behaviors/guarded_passage.py

def on_go(entity, accessor, context):
    """Prevent passage unless condition met."""
    # entity here is the location
    if entity.id == "loc_guard_post":
        direction = context.get("direction")
        if direction == "north":
            actor_id = context["actor_id"]
            actor = accessor.get_actor(actor_id)

            # Check if player has pass
            if "item_guard_pass" not in actor.inventory:
                return EventResult(allow=False,
                                 message="The guard blocks your way. 'Show your pass!'")

    return EventResult(allow=True)
```

---

# 6. The Parser and Commands

## 6.1 How Commands Work

When a player types a command, here's what happens:

```
Player: "take the red key from the wooden chest"
    ↓
1. Fast Local Parser (attempts instant parse)
   ├─ Success: Converts to JSON command
   └─ Failure: Falls back to LLM
    ↓
2. LLM Fallback (for complex input)
   ├─ LLM interprets intent
   └─ Generates JSON command
    ↓
3. Game Engine (processes command)
   ├─ Finds handler for verb
   ├─ Resolves entities (red key, wooden chest)
   ├─ Validates action (key in chest? chest open?)
   ├─ Updates state (move key to inventory)
   └─ Returns result JSON
    ↓
4. LLM Narrator (creates prose)
   ├─ Receives result + llm_context
   ├─ Determines verbosity (full/brief)
   └─ Generates narrative
    ↓
Player sees: "You reach into the weathered chest and carefully
             lift out the ornate red key..."
```

**Fast parser handles:** ~70% of commands (directions, common verbs, simple structure)
**LLM fallback handles:** ~30% (complex phrasing, ambiguity, conversational input)

## 6.2 Command Structure

Commands follow this pattern:

**Basic:** `[verb] [object]`
- `take key`
- `examine chest`
- `go north`

**With adjective:** `[verb] [adjective] [object]`
- `take red key`
- `examine wooden chest`

**With preposition:** `[verb] [object] [preposition] [indirect-object]`
- `put key in chest`
- `take gem from box`
- `unlock door with key`

**With both adjectives:** `[verb] [adj] [object] [prep] [adj] [indirect-object]`
- `take red key from wooden chest`
- `put iron sword on stone table`

**Bare directions:** Just the direction
- `north`
- `up`
- `down`

## 6.3 Vocabulary Management

The game uses a merged vocabulary from multiple sources:

1. **Base vocabulary** (`src/vocabulary.json`) - Common words
2. **Core behaviors** - Standard adventure game verbs
3. **Library behaviors** - Additional verbs from libraries
4. **Your behaviors** - Custom verbs you add

### Vocabulary Structure

```python
VOCABULARY = {
    "verbs": [
        {
            "word": "cast",                    # Primary word
            "synonyms": ["invoke", "recite"],  # Alternative words
            "object_required": True,           # Needs an object?
            "narration_mode": "tracking"       # "tracking" or "brief"
        }
    ],
    "nouns": [
        {
            "word": "key",
            "synonyms": ["passkey"],
            "word_type": "noun"
        }
    ],
    "directions": [
        {
            "word": "north",
            "synonyms": ["n"],
            "word_type": ["noun", "adjective"]  # Multi-valued for directions
        }
    ]
}
```

### Adding Custom Vocabulary

**In your behavior module:**
```python
# behaviors/magic_spells.py

VOCABULARY = {
    "verbs": [
        {
            "word": "cast",
            "synonyms": ["invoke", "recite", "chant"],
            "object_required": True,
            "narration_mode": "brief"  # Always brief narration
        },
        {
            "word": "enchant",
            "synonyms": ["bewitch", "charm"],
            "object_required": True,
            "narration_mode": "tracking"  # Full first time, brief after
        }
    ],
    "nouns": [
        {
            "word": "spell",
            "synonyms": ["incantation", "magic"],
            "word_type": "noun"
        }
    ]
}
```

Now players can use:
- `cast spell`
- `invoke incantation`
- `enchant sword`
- `charm key`

### Synonyms Best Practices

**Good synonyms:**
- Natural alternatives: "take" / "get" / "grab"
- Common abbreviations: "examine" / "x"
- Thematic variations: "unlock" / "open" (for locks)

**Avoid:**
- Too many synonyms (confusing for players)
- Ambiguous synonyms (words that mean different things)
- Cross-verb synonyms (same word for different verbs)

---

# 7. LLM Integration

## 7.1 How the LLM Works

**Key principle:** The LLM is a narrator, not a game master.

**What the LLM does:**
- Translates complex player input to game commands
- Creates vivid prose descriptions of game events
- Uses llm_context to add flavor and variety

**What the LLM does NOT do:**
- Change game state
- Make up items or locations
- Override game rules
- Remember previous conversations (state is in game engine)

### The Separation

```
┌─────────────────────────────────┐
│  LLM (Narrator)                 │
│  - Interprets input             │
│  - Generates prose              │
│  - No state management          │
└────────┬───────────────▲────────┘
         │ JSON          │ JSON
         │ Commands      │ Results
         ▼               │
┌─────────────────────────────────┐
│  Game Engine                    │
│  - ALL state management         │
│  - Command execution            │
│  - Rules enforcement            │
└─────────────────────────────────┘
```

## 7.2 Customizing Narration

### narrator_style.txt

This file defines the narrative style for your game:

```
You are narrating a dark fantasy adventure game set in a cursed tower.

Tone and Style:
- Gothic and atmospheric
- Emphasis on mood and dread
- Use sensory details: cold, damp, echoing
- Short, punchy sentences for action
- Longer, flowing sentences for description

Voice:
- Second person ("You...")
- Present tense
- Active voice preferred

Mood Keywords:
- Ominous, foreboding, ancient
- Mysterious, eldritch, otherworldly
- Decay, corruption, shadow

Example Narration:
- "You lift the ancient key. Its weight surprises you, and a chill runs through
   your fingers where metal touches skin."
- "The door groans open, revealing darkness beyond. The air that escapes is
   cold and stale, untouched for decades."
- "Darkness presses against you from all sides. Your lantern feels inadequate
   against the weight of so much shadow."

Avoid:
- Modern references or anachronisms
- Humor or levity (unless explicitly part of a puzzle)
- Breaking the fourth wall
- Excessive verbosity
```

### Using llm_context Effectively

**Traits should:**
- Be specific and sensory
- Match your game's tone
- Provide variety (5-8 per entity)
- Avoid generic descriptions

**Example - Generic (bad):**
```json
{
  "llm_context": {
    "traits": ["old", "big", "heavy", "nice"]
  }
}
```

**Example - Specific (good):**
```json
{
  "llm_context": {
    "traits": [
      "weathered oak planks",
      "iron-reinforced corners",
      "tarnished brass hinges",
      "musty interior smell",
      "carved runes along edges"
    ]
  }
}
```

### Verbosity Modes

The narrator automatically adjusts verbosity:

**Full narration:**
- First visit to a location
- First examination of an entity
- Important events
- Uses most llm_context traits

**Brief narration:**
- Subsequent visits/examinations
- Routine actions
- Uses fewer traits, focuses on action

**Control per verb:**
```python
VOCABULARY = {
    "verbs": [
        {
            "word": "inventory",
            "narration_mode": "brief"     # Always brief
        },
        {
            "word": "examine",
            "narration_mode": "tracking"  # Full first time
        }
    ]
}
```

## 7.3 Debugging Narration

### Show Traits Flag

Run with `--show-traits` to see what the LLM sees:

```bash
python -m src.llm_game my_game --show-traits
```

Output:
```
[location traits: ancient stone, echoing halls, cold draft]
[item_key traits: brass, intricate engravings, cold metal]

You enter the ancient hall. Cold air swirls around you...
```

This helps you:
- Verify traits are appropriate
- See which traits were selected (randomized)
- Debug poor narration

### Debug Flag

Run with `--debug` for detailed logging:

```bash
python -m src.llm_game my_game --debug
```

Shows:
- Parser decisions (local vs LLM)
- Behavior module loading
- Handler invocations
- API cache statistics
- Token usage

### Troubleshooting Poor Narration

**Problem:** Narration is too generic

**Solutions:**
- Add more specific traits to llm_context
- Improve narrator_style.txt with better examples
- Check that traits match your tone

**Problem:** Narration contradicts game state

**Solution:**
- The LLM should never contradict state
- Check that your result messages are clear
- Verify llm_context reflects current state (use state_variants)

**Problem:** Narration is too verbose

**Solutions:**
- Set verbs to `"narration_mode": "brief"`
- Reduce number of traits
- Adjust narrator_style.txt to request brevity

---

# 8. Testing and Debugging

## 8.1 Validating Game State

**Validate your game state:**
```bash
python -m src.game_engine my_first_game --validate
```

**Common validation errors:**

1. **"ID not unique"** - Two entities have the same ID
   - Solution: Make all IDs unique (even across types)

2. **"Reference not found"** - Exit points to non-existent location
   - Solution: Check `to` field matches actual location ID

3. **"start_location not found"** - Metadata references non-existent location
   - Solution: Check metadata.start_location matches a location ID

4. **"Player actor not found"** - No actor with id "player"
   - Solution: Add player actor to actors section

5. **"Circular containment"** - Item A in item B in item A
   - Solution: Break the cycle in item locations

6. **"Door has no location"** - Door not attached to exit
   - Solution: Set door location to `"exit:loc_id:direction"`

## 8.2 Testing Behaviors

### Manual Testing

**Test workflow:**
1. Make changes to behavior module
2. Restart game (behaviors load at startup)
3. Test commands manually
4. Use `--debug` flag to see behavior invocations

### Automated Testing

**Write unit tests for behaviors:**

```python
# tests/test_my_behavior.py
import unittest
from src.state_manager import GameState, Item, Actor, Location
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.word_entry import WordEntry, WordType

class TestMagicMirror(unittest.TestCase):
    def setUp(self):
        """Set up test state."""
        # Create minimal game state
        self.state = GameState(
            metadata=...,
            locations=[...],
            items=[...],
            actors={"player": Actor(...)},
            locks=[]
        )

        # Load your behavior
        self.manager = BehaviorManager()
        import behaviors.magic_mirror
        self.manager.load_module(behaviors.magic_mirror)

        self.accessor = StateAccessor(self.state, self.manager)

    def test_peer_reveals_key(self):
        """Test that peering at mirror reveals hidden key."""
        from behaviors.magic_mirror import handle_peer

        # Add mirror and hidden key
        mirror = Item(id="item_magic_mirror", name="mirror",
                     description="...", location="loc_room",
                     properties={}, behaviors=["behaviors.magic_mirror"])
        key = Item(id="item_hidden_key", name="key",
                  description="...", location="loc_room",
                  properties={"portable": True, "states": {"hidden": True}},
                  behaviors=[])

        self.state.items.extend([mirror, key])

        # Peer at mirror
        action = {
            "verb": "peer",
            "object": WordEntry("mirror", WordType.NOUN, []),
            "actor_id": "player"
        }

        result = handle_peer(self.accessor, action)

        # Verify key revealed
        self.assertTrue(result.success)
        self.assertFalse(key.states.get("hidden", False))
        self.assertIn("key", result.message.lower())

if __name__ == "__main__":
    unittest.main()
```

**Run tests:**
```bash
python -m unittest tests/test_my_behavior.py
```

## 8.3 Debugging Commands

### Understanding Errors

**"Handler not found"**
```
Error: I don't understand 'cast'.
```
- Behavior module not loaded
- VOCABULARY not exported
- Handler function not at module level

**Check:**
```bash
python -m src.llm_game my_game --debug
```
Look for: `Loaded module: behaviors.magic_spells`

**"Entity not found"**
```
You don't see key here.
```
- Item not in current location
- Name doesn't match vocabulary
- Synonyms missing

**Debug:**
```python
# In behavior handler, add:
import sys
print(f"DEBUG: Looking for {obj_entry.word}", file=sys.stderr)
print(f"DEBUG: Synonyms: {obj_entry.synonyms}", file=sys.stderr)
print(f"DEBUG: Items here: {[i.name for i in items]}", file=sys.stderr)
```

**"State corrupted"**
```
Game state is corrupted. Please save and restart.
```
- Inconsistent state detected
- Usually: invalid references, broken containment

**Solution:** Check error message details, fix game_state.json, restart

### Testing Command Variations

Test different phrasings:
```
> take key
> get the key
> pick up key
> grab key

> examine red key
> look at the red key
> x red key
> inspect red key
```

All should work if synonyms are defined properly.

---

# 9. Save/Load System

## 9.1 How Saves Work

**What is saved:**
- Current game state (all entity data)
- Player location and inventory
- Item locations
- Entity states (open/closed, lit/unlit, etc.)
- Custom properties and flags

**What is NOT saved (reconstructed at load):**
- Behavior modules (reloaded from files)
- Vocabulary (rebuilt from behaviors)
- Handler functions
- System prompts

### Save Commands

**In-game:**
```
> save
```

**Uses file dialog to choose save location.**

**Load:**
```
> load
```

**Uses file dialog to choose save file.**

**Command line:**
```bash
# Start game with saved state
python -m src.llm_game my_game --load saved_game.json
```

## 9.2 Schema Versioning

**Current schema:** `v_0.01`

**Schema version in metadata:**
```json
{
  "metadata": {
    "schema_version": "v_0.01",
    "title": "My Game",
    ...
  }
}
```

### Breaking Changes

When the engine updates to incompatible format:
- Old saves won't load in new engine
- Migration tool provided separately
- No backward compatibility in engine (keeps code clean)

**Migration process:**
```bash
# Use migration tool (when available)
python tools/migrate_v001_to_v002.py old_save.json new_save.json
```

### Save File Compatibility

**Safe changes (won't break saves):**
- Adding new items to world
- Adding new locations
- Adding properties to entities
- Adding behaviors to entities

**Breaking changes (will break saves):**
- Changing entity IDs
- Removing required entities
- Changing entity types (Item → Location)
- Restructuring properties format

**Best practice:** Test loading old saves after making changes.

---

# 10. Advanced Topics

## 10.1 Handler Chaining in Depth

Handler chaining allows you to extend or override core functionality.

### When to Use Chaining

**Use chaining when you want to:**
- Add pre-conditions to existing commands
- Add post-processing to results
- Extend functionality while keeping core behavior
- Override specific cases while falling back to core

**Example: Weight limits on take**
```python
# behaviors/weight_limits.py

def handle_take(accessor, action):
    """Add weight limit check before normal take."""
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)
    obj_entry = action.get("object")

    # Find item
    entity = accessor.find_entity_in_location(obj_entry, actor.location,
                                             action.get("adjective"))

    if entity:
        # Check weight
        current_weight = sum(
            accessor.get_item(item_id).properties.get("weight", 0)
            for item_id in actor.inventory
        )
        item_weight = entity.properties.get("weight", 0)
        max_weight = actor.properties.get("max_weight", 100)

        if current_weight + item_weight > max_weight:
            return EventResult(success=False,
                             message="That's too heavy to carry right now.")

    # Weight is OK, use normal take logic
    return accessor.invoke_previous_handler("take", action)
```

### Example: Enhanced Examine

```python
# behaviors/detailed_examine.py

def handle_examine(accessor, action):
    """Add bonus information for magical items."""
    # First do normal examine
    result = accessor.invoke_previous_handler("examine", action)

    if not result.success:
        return result

    # Get the entity that was examined
    obj_entry = action.get("object")
    actor_id = action["actor_id"]
    actor = accessor.get_actor(actor_id)
    entity = accessor.find_entity_in_location(obj_entry, actor.location)

    # Add magical info if applicable
    if entity and entity.properties.get("magical"):
        magical_info = entity.properties.get("magical_description",
                                            "It radiates magical energy.")
        result.message = f"{result.message}\n\n{magical_info}"

    return result
```

## 10.2 StateAccessor Advanced Features

### Update with Behaviors

The `update()` method automatically invokes entity behaviors:

```python
# Update lantern state, triggering on_light behavior
result = accessor.update(
    lantern,                          # Entity to update
    {"states.lit": True},            # Change to apply
    verb="light",                     # Triggers on_light
    actor_id="player"
)

if result.success:
    # Behavior allowed the update
    print(result.message)  # Behavior's custom message (if any)
else:
    # Behavior denied the update
    print(result.message)  # Behavior's denial message
```

### Complex Queries

**Find all items with property:**
```python
light_sources = [
    item for item in accessor.get_items_in_location(location_id)
    if item.properties.get("provides_light")
]
```

**Find all locked containers:**
```python
locked_containers = [
    item for item in state.items
    if item.container and item.container.get("locked", False)
]
```

**Check if player has any key:**
```python
player = accessor.get_actor("player")
has_key = any(
    "key" in accessor.get_item(item_id).name.lower()
    for item_id in player.inventory
)
```

## 10.3 Creating Behavior Libraries

If you create reusable behavior patterns, package them as a library.

### Library Structure

```
behavior_libraries/
└── my_puzzle_lib/
    ├── __init__.py           # Package marker
    ├── pattern1.py           # Reusable pattern
    ├── pattern2.py           # Another pattern
    └── README.md             # Documentation
```

### Library Module Pattern

```python
# behavior_libraries/my_puzzle_lib/combination_lock.py

"""Combination lock puzzle utilities.

Provides reusable functions for combination lock puzzles.
"""

def set_combination(entity, combination: list) -> None:
    """Set the correct combination for a lock.

    Args:
        entity: The lock entity
        combination: List of values (e.g., [3, 7, 2, 1])
    """
    entity.states["correct_combination"] = combination
    entity.states["current_attempt"] = []

def try_digit(entity, digit: int) -> bool:
    """Try entering a digit.

    Args:
        entity: The lock entity
        digit: The digit to enter

    Returns:
        True if combination is now complete and correct
    """
    if "current_attempt" not in entity.states:
        entity.states["current_attempt"] = []

    entity.states["current_attempt"].append(digit)

    correct = entity.states.get("correct_combination", [])
    current = entity.states["current_attempt"]

    # Check if too long
    if len(current) > len(correct):
        reset_combination(entity)
        return False

    # Check if complete and correct
    if len(current) == len(correct):
        if current == correct:
            return True
        else:
            reset_combination(entity)
            return False

    return False

def reset_combination(entity) -> None:
    """Reset the current attempt."""
    entity.states["current_attempt"] = []
```

### Library Documentation

```markdown
# My Puzzle Library

Reusable puzzle mechanics for combination locks, switches, and more.

## Installation

```bash
cd my_game/behaviors
ln -s ../../../behavior_libraries/my_puzzle_lib my_puzzle_lib
```

## Usage

### Combination Lock

```python
from behavior_libraries.my_puzzle_lib import combination_lock

def on_turn(entity, accessor, context):
    """Handle turning the dial."""
    digit = context.get("digit")

    if combination_lock.try_digit(entity, digit):
        # Success!
        return EventResult(allow=True,
                         message="Click! The lock opens.")

    return EventResult(allow=True,
                     message="The dial clicks.")
```

## API Reference

...
```

---

# 11. Tips and Best Practices

## 11.1 Game Design

1. **Start small** - Begin with 3-5 locations, add more as you learn
2. **Test frequently** - Play your game after every change
3. **Clear goals** - Players should know what they're trying to do
4. **Fair puzzles** - Provide hints, avoid moon logic
5. **Reward exploration** - Hidden details for thorough players
6. **Consistent tone** - Maintain atmosphere throughout
7. **Iterative design** - Build, test, refine, repeat

## 11.2 World Building

1. **Logical geography** - Exits should make spatial sense
2. **Appropriate scale** - Match location detail to importance
3. **Environmental storytelling** - World reveals story through details
4. **Purposeful items** - Every item should have a reason to exist
5. **Living world** - NPCs with goals, not just quest dispensers

## 11.3 Writing Behaviors

1. **Start with core** - Use core behaviors as examples
2. **One behavior = one feature** - Keep modules focused
3. **Handle edge cases** - What if player does unexpected thing?
4. **Return EventResult** - Always return proper result object
5. **Update state carefully** - Don't break state consistency
6. **Test thoroughly** - Write unit tests for complex behaviors
7. **Document your code** - Future you will thank you

## 11.4 LLM Context

1. **Quality over quantity** - 5 good traits better than 10 mediocre
2. **Sensory details** - Engage all senses, not just sight
3. **Concrete descriptions** - "Cold iron" better than "metallic"
4. **Match your tone** - Gothic? Whimsical? Keep it consistent
5. **State variants for key states** - Open/closed, lit/unlit, etc.
6. **Test narration** - Use --show-traits to verify

## 11.5 Common Pitfalls

**Don't:**
- Hard-code item names in behavior code (use IDs)
- Create circular containment (item A in item B in item A)
- Forget to update item locations when moving items
- Duplicate IDs across entities
- Skip validation before running
- Make puzzles that require exact phrasing
- Forget to test with different command phrasings

**Do:**
- Use IDs for entity references
- Validate game state frequently
- Test all puzzle solutions
- Provide multiple synonym options
- Keep state management in engine (not LLM)
- Write clear error messages
- Document complex puzzles

---

# 12. Getting Help

## 12.1 Documentation

- **This guide** - Game creation and behaviors
- **Developer Documentation** (`docs/engine_documentation.md`) - Engine internals
- **Example games** (`examples/`) - Working examples to study
- **Design documents** (`docs/`) - Detailed design documentation

## 12.2 Example Games

**simple_game** - Basic features
- Minimal world (3 locations)
- Simple items and containers
- One locked door
- Good starting point

**extended_game** - Advanced features
- More locations (8+)
- Custom behaviors
- Complex puzzles
- NPCs with dialogue
- Multiple behavior modules

**layered_game** - Three-tier hierarchy
- Demonstrates game + library + core
- Reusable library behaviors
- Handler chaining
- Advanced patterns

## 12.3 Troubleshooting

1. **Validation fails** - Fix errors in game_state.json first
2. **Command not recognized** - Check VOCABULARY exported from behavior
3. **Behavior not invoked** - Verify module loaded (use --debug)
4. **Poor narration** - Improve llm_context and narrator_style.txt
5. **State corruption** - Check for invalid references in game_state.json

## 12.4 Community

- **GitHub Issues** - Bug reports and feature requests
- **Discussions** - Questions and sharing games
- **Examples** - Share your games as examples for others

---

# Appendix A: Complete Minimal Game

Here's a complete, minimal game you can use as a template:

## game_state.json

```json
{
  "metadata": {
    "title": "The Mysterious Room",
    "author": "New Author",
    "version": "1.0",
    "description": "A simple mystery puzzle",
    "start_location": "loc_room"
  },
  "locations": [
    {
      "id": "loc_room",
      "name": "Mysterious Room",
      "description": "A small room with stone walls. A heavy door stands to the north.",
      "exits": {
        "north": {
          "type": "door",
          "to": "loc_outside",
          "door_id": "door_exit"
        }
      },
      "properties": {},
      "behaviors": []
    },
    {
      "id": "loc_outside",
      "name": "Outside",
      "description": "You're free! Sunlight and fresh air greet you.",
      "exits": {
        "south": {
          "type": "door",
          "to": "loc_room",
          "door_id": "door_exit"
        }
      }
    }
  ],
  "items": [
    {
      "id": "door_exit",
      "name": "door",
      "description": "A heavy wooden door with an iron lock.",
      "location": "exit:loc_room:north",
      "door": {
        "open": false,
        "locked": true,
        "lock_id": "lock_door"
      },
      "llm_context": {
        "traits": ["heavy oak", "iron-banded", "imposing"]
      }
    },
    {
      "id": "item_key",
      "name": "key",
      "description": "An iron key.",
      "location": "item_chest",
      "properties": {
        "portable": true
      },
      "llm_context": {
        "traits": ["cold iron", "simple", "slightly rusty"]
      }
    },
    {
      "id": "item_chest",
      "name": "chest",
      "description": "A small wooden chest.",
      "location": "loc_room",
      "properties": {
        "portable": false,
        "container": {
          "is_surface": false,
          "capacity": 5,
          "open": false,
          "locked": false
        }
      },
      "llm_context": {
        "traits": ["weathered wood", "brass hinges", "simple latch"]
      }
    }
  ],
  "locks": [
    {
      "id": "lock_door",
      "name": "lock",
      "description": "An iron lock.",
      "properties": {
        "opens_with": ["item_key"],
        "auto_unlock": false
      }
    }
  ],
  "actors": {
    "player": {
      "id": "player",
      "name": "Adventurer",
      "description": "That's you!",
      "location": "loc_room",
      "inventory": [],
      "properties": {},
      "behaviors": []
    }
  }
}
```

## narrator_style.txt

```
You are narrating a simple mystery puzzle game.

Style: Clear, direct, slightly mysterious
Tone: Neutral to slightly suspenseful
Perspective: Second person, present tense

Keep descriptions concise but evocative. Focus on what the player can see and do.

Example narration:
- "You open the chest. Inside lies an iron key."
- "The key slides into the lock with a satisfying click."
- "The door swings open, revealing daylight beyond."
```

## Solution

```
> look
> examine chest
> open chest
> take key
> unlock door with key
> open door
> north
```

You've escaped!

---

# Appendix B: Glossary

**Actor** - Player or NPC character with location and inventory

**Behavior** - Python code responding to commands or events

**Behavior Module** - Python file with vocabulary, handlers, and/or behaviors

**Command Handler** - Function processing a verb (handle_*)

**Container** - Item that can hold other items (chest, table, box)

**Core Behaviors** - Built-in game mechanics (behaviors/core/)

**Entity** - Any game object (Item, Actor, Location, Lock, Exit)

**Entity Behavior** - Function responding to events on specific entity (on_*)

**Event** - Something that happens (take, drop, examine, etc.)

**EventResult** - Return value from handlers/behaviors

**Exit** - Connection between locations

**Game State** - Complete game world (all entities)

**Handler Chain** - Multiple handlers for same verb (game > library > core)

**LLM Context** - Descriptive data for narration (traits, state_variants)

**Location** - Room or place in game world

**Properties** - Flexible key-value data on entities

**State** - Dynamic game data (lit/unlit, open/closed)

**StateAccessor** - API for querying/modifying game state

**Three-Tier Hierarchy** - Game > Library > Core precedence

**Verbosity** - Narration detail (full/brief)

**WordEntry** - Vocabulary entry with synonyms

---

# Appendix C: Quick Reference

## File Structure
```
my_game/
├── game_state.json         # World definition
├── narrator_style.txt      # Narration style
└── behaviors/              # Behavior modules
    ├── core/              # Symlink to core
    ├── my_puzzle.py       # Custom behaviors
    └── custom_verbs.py    # More behaviors
```

## Running Your Game
```bash
export ANTHROPIC_API_KEY=your-key
python -m src.llm_game my_game
python -m src.llm_game my_game --debug --show-traits
```

## Core Commands
```
Movement: north, south, east, west, up, down, go <dir>
Items: take, drop, put <item> in/on <container>
Looking: look, examine <thing>, inventory
Interaction: open, close, unlock <thing> with <key>
Meta: help, save, load, quit
```

## Behavior Template
```python
from src.state_accessor import EventResult

VOCABULARY = {
    "verbs": [{"word": "myverb", "object_required": True}]
}

def handle_myverb(accessor, action):
    """Handle myverb command."""
    # Implementation
    return EventResult(success=True, message="...")

def on_myevent(entity, accessor, context):
    """Handle myevent on entity."""
    # Implementation
    return EventResult(allow=True, message="...")
```

## Common Properties
```json
{
  "portable": true/false,
  "container": {"is_surface": true/false, "capacity": 10, "open": true/false},
  "provides_light": true/false,
  "readable": true/false,
  "states": {"lit": false, "hidden": true}
}
```

---

**You're ready to create your game! Start with the Quick Start section, build something small, and expand from there. Happy creating!**
