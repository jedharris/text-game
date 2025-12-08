# Advanced Topics

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Previous: [Testing & Debugging](10_testing.md)

---

This final section covers game state management, the turn system, save/load, advanced handler techniques, creating behavior libraries, tips, and getting help.

---

# 11. Game State Management

## 11.1 Player Flags

Flags are persistent boolean or simple values stored on the player. Use them to track game progression, puzzle states, and player choices.

**API:**
```python
# Set a flag
state.set_flag("met_wizard", True)
state.set_flag("quest_stage", 2)

# Get a flag
if state.get_flag("met_wizard", False):
    # Player has met the wizard
    ...

quest_stage = state.get_flag("quest_stage", 0)
```

**Storage:** Flags are stored in `player.properties["flags"]` and persist across save/load.

**Example usage - Progressive NPC dialogue:**
```python
def on_talk(entity, accessor, context):
    """NPC responds differently based on game progress."""
    if entity.id != "npc_wizard":
        return EventResult(allow=True)

    state = accessor.state

    if not state.get_flag("met_wizard"):
        state.set_flag("met_wizard", True)
        return EventResult(allow=True,
            message="'Ah, a visitor! I am Alaric, keeper of this tower.'")

    if state.get_flag("has_crystal"):
        return EventResult(allow=True,
            message="'You found the crystal! Now we can begin the ritual.'")

    return EventResult(allow=True,
        message="'Have you found the crystal yet? Look in the eastern caves.'")
```

## 11.2 GameState.extra

The `extra` dict stores non-player global data that needs to persist across save/load. Use it for world-level state that doesn't belong to any specific entity.

**Use cases:**
- World-level counters (total enemies defeated, items crafted)
- Environmental state (weather, time of day)
- Global puzzle state (shared between multiple entities)
- Behavior library data

**Example:**
```python
# In a behavior module
def on_defeat(entity, accessor, context):
    """Track defeated enemies globally."""
    state = accessor.state

    # Initialize if needed
    if "enemies_defeated" not in state.extra:
        state.extra["enemies_defeated"] = 0

    state.extra["enemies_defeated"] += 1

    # Check for achievement
    if state.extra["enemies_defeated"] >= 10:
        state.set_flag("achievement_warrior", True)
        return EventResult(allow=True,
            message="Achievement unlocked: Warrior (10 enemies defeated)")

    return EventResult(allow=True)
```

**Note:** `state.extra` is automatically saved and loaded with game state.

---

# 12. The Turn System

## 12.1 Turn Counter

The game tracks turns via `state.turn_count`. A turn advances after each successful player command.

**API:**
```python
# Read current turn
current_turn = state.turn_count

# Turn increments automatically after successful commands
# You typically don't call this directly:
state.increment_turn()  # Returns new turn count
```

**Example - Time-limited puzzle:**
```python
def on_enter(entity, accessor, context):
    """Track when player entered the flooding room."""
    if entity.id == "loc_flood_chamber":
        accessor.state.extra["flood_start_turn"] = accessor.state.turn_count
        return EventResult(allow=True,
            message="Water begins pouring in through cracks in the walls!")
    return EventResult(allow=True)

def check_flood(accessor):
    """Check if player has drowned."""
    state = accessor.state
    start = state.extra.get("flood_start_turn")

    if start and state.turn_count - start >= 10:
        # Player ran out of time
        return EventResult(success=False,
            message="The water has risen too high. You drown.")

    if start:
        turns_left = 10 - (state.turn_count - start)
        return EventResult(success=True,
            message=f"The water is rising. About {turns_left} turns until it's too deep!")

    return None
```

## 12.2 Turn Phase Hooks

After each successful player command, the engine fires four turn phases in order:

| Phase | Hook Constant | Purpose |
|-------|---------------|---------|
| 1 | `NPC_ACTION` | NPCs take their actions |
| 2 | `ENVIRONMENTAL_EFFECT` | Environmental effects apply |
| 3 | `CONDITION_TICK` | Conditions progress (poison damage, etc.) |
| 4 | `DEATH_CHECK` | Check if anyone died |

**Registration via vocabulary:**

To register a handler for a turn phase, add an `events` entry with a `hook` field:

```python
# In a behavior module's VOCABULARY
VOCABULARY = {
    "events": [
        {
            "event": "on_npc_turn",
            "hook": "npc_action",
            "description": "Fire NPC actions each turn"
        },
        {
            "event": "on_environmental_tick",
            "hook": "environmental_effect",
            "description": "Apply environmental effects each turn"
        }
    ]
}

def on_npc_turn(entity, accessor, context):
    """Handle NPC actions for this turn.

    Note: entity is None for turn phase hooks.
    Iterate over relevant entities yourself.
    """
    messages = []
    state = accessor.state

    for actor_id, actor in state.actors.items():
        if actor_id == "player":
            continue

        # NPC AI logic here
        if actor.properties.get("ai", {}).get("disposition") == "hostile":
            # Hostile NPC attacks
            messages.append(f"{actor.name} attacks!")

    if messages:
        return EventResult(allow=True, message="\n".join(messages))
    return EventResult(allow=True)
```

**Hook execution flow:**
1. Player command succeeds
2. `state.increment_turn()` is called
3. Engine fires each hook in order (NPC_ACTION → ENVIRONMENTAL_EFFECT → CONDITION_TICK → DEATH_CHECK)
4. Messages from each phase are collected and returned to the LLM

**Important:** Turn phase handlers receive `entity=None` because they operate on the world, not a specific entity. Your handler is responsible for iterating over relevant entities.

---

# 13. Light Sources

## 13.1 Light Source Items

Items with `provides_light: true` are light sources. They can illuminate dark areas.

**Basic light source:**
```json
{
  "id": "item_lantern",
  "name": "lantern",
  "description": "A brass lantern with magical runes.",
  "location": "loc_entrance",
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

## 13.2 Core Light Source Behaviors

The core `light_sources` behavior module provides automatic light management:

**Auto-light on take:**
When a player picks up a light source, it automatically lights (runes activate on touch).

**Auto-extinguish on drop/put:**
When a player drops or puts down a light source, it automatically extinguishes.

**Player commands:**
- `light lantern` - Manually light
- `extinguish lantern` - Manually extinguish

**Implementation:**
```python
# From behaviors/core/light_sources.py
def on_take(entity, state, context):
    """Auto-light when taken."""
    entity.states['lit'] = True
    return EventResult(allow=True,
        message="As your hand closes around the lantern, the runes flare to life.")

def on_drop(entity, state, context):
    """Extinguish when dropped."""
    entity.states['lit'] = False
    return EventResult(allow=True,
        message="The lantern's runes fade as you set it down.")
```

## 13.3 Darkness (via darkness_lib)

For full darkness enforcement (blocking actions in dark rooms without light), use the `darkness_lib` behavior library. See [Behavior Libraries Reference](05_behaviors.md#54-using-behavior-libraries).

---

# 14. Save/Load System

## 14.1 How Saves Work

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

## 14.2 Schema Versioning

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

# 15. Advanced Topics

## 15.1 Handler Chaining in Depth

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

## 15.2 StateAccessor Advanced Features

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

## 15.3 Creating Behavior Libraries

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

# 16. Tips and Best Practices

## 16.1 Game Design

1. **Start small** - Begin with 3-5 locations, add more as you learn
2. **Test frequently** - Play your game after every change
3. **Clear goals** - Players should know what they're trying to do
4. **Fair puzzles** - Provide hints, avoid moon logic
5. **Reward exploration** - Hidden details for thorough players
6. **Consistent tone** - Maintain atmosphere throughout
7. **Iterative design** - Build, test, refine, repeat

## 16.2 World Building

1. **Logical geography** - Exits should make spatial sense
2. **Appropriate scale** - Match location detail to importance
3. **Environmental storytelling** - World reveals story through details
4. **Purposeful items** - Every item should have a reason to exist
5. **Living world** - NPCs with goals, not just quest dispensers

## 16.3 Writing Behaviors

1. **Start with core** - Use core behaviors as examples
2. **One behavior = one feature** - Keep modules focused
3. **Handle edge cases** - What if player does unexpected thing?
4. **Return EventResult** - Always return proper result object
5. **Update state carefully** - Don't break state consistency
6. **Test thoroughly** - Write unit tests for complex behaviors
7. **Document your code** - Future you will thank you

## 16.4 LLM Context

1. **Quality over quantity** - 5 good traits better than 10 mediocre
2. **Sensory details** - Engage all senses, not just sight
3. **Concrete descriptions** - "Cold iron" better than "metallic"
4. **Match your tone** - Gothic? Whimsical? Keep it consistent
5. **State variants for key states** - Open/closed, lit/unlit, etc.
6. **Test narration** - Use --show-traits to verify

## 16.5 Common Pitfalls

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

# 17. Getting Help

## 17.1 Documentation

- **This guide** - Game creation and behaviors
- **Developer Documentation** (`docs/engine_documentation.md`) - Engine internals
- **Example games** (`examples/`) - Working examples to study
- **Design documents** (`docs/`) - Detailed design documentation

## 17.2 Example Games

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

## 17.3 Troubleshooting

1. **Validation fails** - Fix errors in game_state.json first
2. **Command not recognized** - Check VOCABULARY exported from behavior
3. **Behavior not invoked** - Verify module loaded (use --debug)
4. **Poor narration** - Improve llm_context and narrator_style.txt
5. **State corruption** - Check for invalid references in game_state.json

## 17.4 Community

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
