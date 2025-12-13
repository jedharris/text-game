# The Behavior System

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Previous: [Actor Interactions](04_actor_interactions.md) | Next: [Common Patterns](06_patterns.md)

---

The behavior system is how you extend the game with new functionality. This is the most powerful feature of the framework.

## 5.1 What Are Behaviors?

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

## 5.2 Three-Tier Hierarchy

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

### Hook Conflict Constraint

**Important:** Only one event handler can be registered per hook at each tier level.

If two behaviors at the same tier both register handlers for the same hook, you will get an error:

```
ValueError: Hook 'after_give' conflict at tier 3: already mapped to
'on_fire_gift', cannot also map to 'on_wolf_feed'
```

**Why this happens:** Hooks like `after_give` or `after_actor_state_change` are generic - they fire for ANY give action or state change. Multiple behaviors might legitimately want to react to these hooks for different entities (wolves want food, salamanders want fire items, bee queens want flowers).

**Solution: Infrastructure Dispatchers**

When multiple region behaviors need the same hook, create a single infrastructure-tier handler that dispatches based on entity configuration:

1. Create one handler at infrastructure tier (behaviors/infrastructure/)
2. Remove hook registrations from regional behaviors
3. Configure entities with properties the infrastructure handler reads

**Example: Gift Reactions**

Instead of three conflicting handlers:
```python
# wolf_pack.py - CONFLICT!
vocabulary = {"events": [{"event": "on_wolf_feed", "hook": "after_give"}]}

# salamanders.py - CONFLICT!
vocabulary = {"events": [{"event": "on_fire_gift", "hook": "after_give"}]}
```

Create one infrastructure dispatcher:
```python
# behaviors/infrastructure/gift_reactions.py
vocabulary = {"events": [{"event": "on_gift_given", "hook": "after_give"}]}

def on_gift_given(entity, accessor, context):
    target = context.get("target_actor")
    gift_config = target.properties.get("gift_reactions", {})
    # Dispatch based on entity configuration
```

Then configure entities in game_state.json:
```json
{
    "id": "npc_alpha_wolf",
    "properties": {
        "gift_reactions": {
            "food": {
                "accepted_items": ["venison", "meat", "rabbit"],
                "trust_delta": 1,
                "accept_message": "The wolf accepts the {item}..."
            }
        }
    }
}
```

**Available infrastructure dispatchers:**
- `pack_mirroring.py` - Leader/follower state synchronization
- `gift_reactions.py` - Entity-specific reactions to receiving items
- `dialog_reactions.py` - Entity-specific reactions to dialog keywords
- `item_use_reactions.py` - Entity-specific reactions to item use
- `death_reactions.py` - Entity-specific death consequences
- `turn_phase_dispatcher.py` - Regional turn phase effects

### Hybrid Dispatcher Pattern (Data-Driven + Handler Escape Hatch)

Infrastructure dispatchers support two modes:

**1. Data-Driven (Simple Cases):** Configure entity behavior entirely in JSON:
```json
{
    "id": "npc_wolf",
    "properties": {
        "gift_reactions": {
            "food": {
                "accepted_items": ["venison", "meat", "rabbit"],
                "trust_delta": 1,
                "accept_message": "The wolf accepts the {item}..."
            },
            "reject_message": "The wolf ignores the offering."
        }
    }
}
```

**2. Handler Escape Hatch (Complex Cases):** Delegate to Python for complex logic:
```json
{
    "id": "npc_bee_queen",
    "properties": {
        "gift_reactions": {
            "handler": "behaviors.regions.beast_wilds.bee_queen:on_flower_offer"
        }
    }
}
```

The handler path format is `module.path:function_name`. When specified, the dispatcher calls this function instead of processing data-driven config.

**Handler Signature:**
```python
def on_flower_offer(
    entity: Any,           # The item/entity triggering the event
    accessor: Any,         # StateAccessor instance
    context: dict[str, Any]  # Event-specific context
) -> EventResult:
    """Handle offering flowers to the Bee Queen."""
    # Complex logic here...
    return EventResult(allow=True, message="...")
```

**When to use each mode:**
- **Data-driven:** Simple reactions (trust changes, flags, messages, state transitions)
- **Handler escape hatch:** Multi-step logic, cross-entity coordination, conditional branching

**Fallback behavior:** If a handler path fails to load (module not found, function missing), the dispatcher falls through to data-driven processing. This allows graceful degradation during development.

## 5.3 Using Core Behaviors

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

## 5.4 Using Behavior Libraries

Behavior libraries are reusable behavior packages for common patterns.

### Installing a Library

```bash
# In your game's behaviors directory
ln -s ../../../behavior_libraries/timing_lib timing_lib
```

Then use library functions in your behavior modules:
```python
from behavior_libraries.timing_lib import schedule_event
```

### Available Libraries

---

#### timing_lib - Turn Counter and Scheduled Events

**Purpose:** Schedule events to fire at specific turns.

**Architecture:** This library provides **scheduling infrastructure only**. It tracks when events should fire and removes them from the queue, but does not implement what those events DO. Your game must provide a handler that processes fired events.

The system has two layers:
1. **timing_lib** - Generic infrastructure: stores events, checks deadlines, fires events
2. **Your game's event handler** - Game-specific logic: implements what each event actually does

**API:**
```python
from behavior_libraries.timing_lib import (
    schedule_event, cancel_event, get_scheduled_events
)

# Schedule an event for turn 50
event_id = schedule_event(accessor, "on_cave_collapse", trigger_turn=50,
                         data={"severity": "major"})

# Schedule repeating event every 10 turns
event_id = schedule_event(accessor, "on_hunger_check", trigger_turn=10,
                         repeating=True, interval=10)

# Cancel an event
cancel_event(accessor, "on_cave_collapse")

# List scheduled events
events = get_scheduled_events(accessor)
```

**Storage:** Events stored in `state.extra['scheduled_events']`.

**IMPORTANT: Implementing Event Handlers**

When `on_check_scheduled_events` fires an event, it logs "Event 'X' triggered" but doesn't know what X should DO. You must implement a handler that processes fired events:

```python
# In your game's behaviors (e.g., world_events.py)
def on_world_event_check(entity, accessor, context: dict) -> EventResult:
    """Process scheduled world events when they fire."""
    event_name = context.get('event_name', '')
    data = context.get('data', {})

    messages = []

    if event_name == "on_cave_collapse":
        # Implement what happens when cave collapses
        location_id = data.get('location')
        messages.append("The cave collapses with a thunderous roar!")
        # Block exits, damage players, etc.

    elif event_name == "on_bomb_explode":
        location = data.get('location')
        messages.append("BOOM! The bomb explodes!")
        # Implement explosion effects

    return EventResult(allow=True, message='\n'.join(messages))
```

**Complete Example - Time Bomb with Handler:**

```python
# Step 1: Schedule the event when bomb is taken
def on_take(entity, accessor, context):
    """Start countdown when bomb is taken."""
    if entity.id == "item_bomb":
        current_turn = accessor.state.turn_count
        schedule_event(accessor, "bomb_explode",
                      trigger_turn=current_turn + 10,
                      data={"location": entity.location})
        return EventResult(allow=True,
            message="The bomb starts ticking ominously!")
    return EventResult(allow=True)

# Step 2: Handle the event when it fires
def on_scheduled_event(entity, accessor, context):
    """Process scheduled events."""
    event_name = context.get('event_name', '')
    data = context.get('data', {})

    if event_name == "bomb_explode":
        loc_id = data.get('location')
        # Destroy items in location, damage player, etc.
        return EventResult(allow=True,
            message="BOOM! The bomb explodes, destroying everything nearby!")

    return EventResult(allow=True)
```

**Integration:** To connect your handler to the scheduled events system, you need to call your handler when events fire. See `big_game/behaviors/world_events.py` for a complete example.

---

#### darkness_lib - Visibility and Darkness

**Purpose:** Enforce darkness in locations requiring light sources.

**Location properties:**
```json
{
  "requires_light": true,
  "ambient_light": false,
  "darkness_description": "It's pitch black. You can't see anything."
}
```

**API:**
```python
from behavior_libraries.darkness_lib import (
    check_visibility, get_light_sources, get_darkness_description
)

# Check if location has light
if check_visibility(accessor, "loc_cave"):
    # Location is lit
    ...

# Get active light sources
sources = get_light_sources(accessor, "loc_cave")
```

**Actions allowed in darkness:** go, inventory, drop, movement directions

**Actions blocked in darkness:** examine, look, take, attack, use (most others)

**Example location:**
```json
{
  "id": "loc_deep_cave",
  "name": "Deep Cave",
  "description": "A vast underground chamber.",
  "properties": {
    "requires_light": true,
    "darkness_description": "The darkness here is absolute."
  }
}
```

---

#### companion_lib - Companion Following

**Purpose:** Make NPCs/creatures follow the player between locations.

**Actor properties:**
```json
{
  "is_companion": true,
  "location_restrictions": ["loc_fire_pit"],
  "terrain_restrictions": ["water"],
  "follow_message": "The wolf trots after you.",
  "cannot_follow_message": "The wolf whimpers and stays behind."
}
```

**API:**
```python
from behavior_libraries.companion_lib import (
    get_companions, make_companion, dismiss_companion, check_can_follow
)

# Make NPC a companion
make_companion(accessor, "npc_wolf")

# Get all companions at player's location
companions = get_companions(accessor)

# Dismiss a companion
dismiss_companion(accessor, "npc_wolf")

# Check if companion can follow to destination
can_follow, message = check_can_follow(accessor, companion, "loc_volcano")
```

**Automatic following:** Companions automatically follow player on movement (via LOCATION_ENTERED hook).

---

#### npc_movement_lib - NPC Patrol and Wandering

**Purpose:** NPCs move along patrol routes or wander randomly.

**Patrol configuration (actor properties):**
```json
{
  "patrol_route": ["loc_gate", "loc_courtyard", "loc_tower"],
  "patrol_index": 0,
  "patrol_frequency": 3
}
```

**API:**
```python
from behavior_libraries.npc_movement_lib import (
    patrol_step, set_patrol_route
)

# Set a patrol route
set_patrol_route(accessor, "npc_guard",
                ["loc_gate", "loc_courtyard", "loc_tower"])

# Manually advance patrol (usually automatic via hook)
message = patrol_step(accessor, guard)
```

**patrol_frequency:** NPC moves every N turns (default 1).

**Automatic movement:** NPCs move during NPC_ACTION turn phase.

---

#### crafting_lib - Item Crafting and Combining

**Purpose:** Combine items to create new items.

**Recipe storage (in state.extra):**
```python
state.extra['recipes'] = {
    "iron_sword": {
        "ingredients": ["item_iron_bar", "item_leather_grip"],
        "creates": "item_iron_sword",
        "requires_location": "loc_forge",
        "requires_skill": "blacksmithing",
        "consumes_ingredients": True,
        "success_message": "You forge a sturdy iron sword."
    }
}

state.extra['item_templates'] = {
    "item_iron_sword": {
        "name": "iron sword",
        "description": "A sturdy sword with a leather grip."
    }
}
```

**API:**
```python
from behavior_libraries.crafting_lib.recipes import (
    find_recipe, check_requirements, execute_craft
)

# Find a recipe matching items
recipe = find_recipe(accessor, ["item_iron_bar", "item_leather_grip"])

# Check if player meets requirements
can_craft, message = check_requirements(accessor, recipe)

# Execute the craft
result = execute_craft(accessor, recipe, item_ids)
if result.success:
    print(result.message)  # "You forge a sturdy iron sword."
```

---

#### dialog_lib - NPC Dialog and Topics

**Purpose:** Structured NPC conversations with topics, prerequisites, and unlocking.

**NPC configuration:**
```json
{
  "dialog_topics": {
    "infection": {
      "keywords": ["infection", "sick", "illness"],
      "summary": "'The infection spreads from the eastern caves...'",
      "unlocks_topics": ["cure"],
      "sets_flags": {"knows_about_infection": true},
      "requires_flags": {},
      "requires_items": [],
      "grants_items": [],
      "one_time": false
    },
    "cure": {
      "keywords": ["cure", "remedy", "healing"],
      "summary": "'You'll need the moonflower from the garden...'",
      "requires_flags": {"knows_about_infection": true}
    }
  },
  "default_topic_summary": "The scholar shakes his head."
}
```

**API:**
```python
from behavior_libraries.dialog_lib.topics import (
    get_available_topics, get_topic_hints,
    handle_ask_about, handle_talk_to
)

# Get available topics for NPC
topics = get_available_topics(accessor, npc)

# Get hint keywords
hints = get_topic_hints(accessor, npc)  # ["infection", "garden"]

# Handle asking about a topic
result = handle_ask_about(accessor, npc, "infection")
print(result.message)  # "'The infection spreads from..."

# Handle general talk (lists available topics)
result = handle_talk_to(accessor, npc)
print(result.message)  # "You could ask about: infection, garden"
```

**Topic features:**
- **keywords:** Words that match this topic
- **requires_flags:** Actor must have these flags set
- **requires_items:** Actor must have these items
- **unlocks_topics:** Topics unlocked after discussing
- **sets_flags:** Flags set on actor after discussing
- **grants_items:** Items given to actor
- **one_time:** Only discuss once

---

#### puzzle_lib - Puzzle Mechanics

**Purpose:** Common puzzle patterns (sequences, thresholds, revelation).

**Sequence tracking:**
```python
from behavior_libraries.puzzle_lib import sequence_tracker

def on_turn(entity, accessor, context):
    """Track turning the dial."""
    digit = context.get("digit")
    sequence_tracker.track_action(entity, digit)

    if sequence_tracker.check_sequence(entity, [3, 7, 2, 1]):
        return EventResult(allow=True, message="Click! The safe opens.")

    if len(entity.states.get("sequence", [])) >= 4:
        sequence_tracker.reset_sequence(entity)
        return EventResult(allow=True, message="Wrong combination. Try again.")

    return EventResult(allow=True)
```

**Threshold checking:**
```python
from behavior_libraries.puzzle_lib import threshold_checker

def on_put(entity, accessor, context):
    """Check weight on scale."""
    items = accessor.get_items_in_container("item_scale")
    total = sum(item.properties.get("weight", 0) for item in items)

    if threshold_checker.check_threshold(total, 50, tolerance=2):
        return EventResult(allow=True, message="The scale balances perfectly!")

    feedback = threshold_checker.get_threshold_feedback(total, 50)
    return EventResult(allow=True, message=feedback)
```

---

#### offering_lib - Offerings and Blessings

**Purpose:** Item offerings to altars with blessing/curse effects.

**Altar configuration:**
```json
{
  "id": "item_altar",
  "properties": {
    "accepts_offerings": ["item_gem", "item_gold"],
    "blessing_for": {"item_gem": "protection", "item_gold": "wealth"}
  }
}
```

**API:**
```python
from behavior_libraries.offering_lib import (
    offering_handler, blessing_manager, alignment_tracker
)

# Process offering
offering_handler.process_offering(accessor, altar, item)

# Apply blessing
blessing_manager.apply_blessing(accessor, player, "protection")

# Track alignment
alignment_tracker.modify_alignment(accessor, player, +1)
```

## 5.5 Writing Custom Behaviors

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

## 5.6 Behavior Precedence and Chaining

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

> **Next:** [Common Patterns](06_patterns.md) - Recipes for puzzles, interactive objects, NPCs, and locations
