# Entity Behaviors - Design Document

## Overview

This document explores approaches for attaching custom Python behavior to game entities (items, NPCs, doors, locations) and mechanisms for invoking that behavior during gameplay.

## Problem Statement

Game authors need to:
1. Define custom behavior for specific entities (e.g., a talking parrot NPC, a trapped chest, a magical door)
2. Write this behavior in Python for maximum flexibility
3. Attach behavior to entities without modifying core engine code
4. Have behavior invoked at appropriate game events (examine, use, enter room, etc.)

## Design Goals

1. **Flexibility**: Support arbitrary Python code for complex behaviors
2. **Safety**: Isolate custom code from core engine (sandboxing, error handling)
3. **Discoverability**: Easy for authors to find what behaviors are available
4. **Maintainability**: Clear separation between data, engine, and custom behavior
5. **Testability**: Behaviors can be unit tested independently
6. **Performance**: Minimal overhead for entities without custom behavior
7. **JSON-friendly**: Behavior attachment should be expressible in game state JSON

## Use Cases

### Use Case 1: Interactive NPC
**Scenario**: A parrot that responds differently based on what the player is carrying

```python
# When player examines the parrot
if "cracker" in player.inventory:
    print("The parrot squawks: 'CRACKER! CRACKER!'")
    # Take the cracker
    player.inventory.remove("cracker")
else:
    print("The parrot ignores you.")
```

### Use Case 2: Trapped Chest
**Scenario**: Opening a chest triggers a trap unless player has specific item

```python
# When player opens the chest
if "gloves" in player.inventory:
    print("Your gloves protect you from the poison needle!")
    return True  # Allow opening
else:
    print("A poison needle pricks your finger! You feel dizzy...")
    player.stats["health"] -= 10
    return False  # Prevent opening
```

### Use Case 3: Magical Door
**Scenario**: Door only opens at certain times or with certain items

```python
# When player tries to open the door
import datetime
hour = datetime.datetime.now().hour

if hour >= 18 or hour < 6:  # Night time
    print("The door glows and swings open. It only opens at night.")
    return True
else:
    print("The door remains firmly shut. Ancient runes glow faintly.")
    return False
```

### Use Case 4: Location Entry Trigger
**Scenario**: When player enters a location, something happens

```python
# When player enters the throne room
if not state.player.flags.get("king_greeted"):
    print("\nThe king looks up from his throne.")
    print("'Welcome, traveler,' he says warmly.")
    state.player.flags["king_greeted"] = True
```

### Use Case 5: Custom Command Handler
**Scenario**: Item responds to custom verb (e.g., "play harp")

```python
# When player uses "play" command on harp
melodies = ["a sad tune", "a joyful song", "an eerie melody"]
import random
melody = random.choice(melodies)
print(f"You pluck the harp strings. It plays {melody}.")

# Side effect: nearby NPC reacts
if "bard" in current_location.npcs:
    print("The bard nods approvingly.")
```

## Event System

### Core Events

Behaviors are triggered by game events. Each entity type supports different events:

#### Item Events
- `on_examine` - When player examines the item
- `on_take` - When player tries to take the item
- `on_drop` - When player drops the item
- `on_use` - When player uses the item
- `on_use_with` - When player uses item with another item/entity
- `on_open` - When player opens the item (chests, containers)
- `on_close` - When player closes the item

#### NPC Events
- `on_examine` - When player examines the NPC
- `on_talk` - When player talks to the NPC
- `on_attack` - When player attacks the NPC
- `on_give` - When player gives item to NPC
- `on_tick` - Called periodically (NPC AI)

#### Door Events
- `on_examine` - When player examines the door
- `on_open` - When player tries to open the door
- `on_close` - When player tries to close the door
- `on_unlock` - When player tries to unlock the door
- `on_pass_through` - When player moves through the door

#### Location Events
- `on_enter` - When player enters the location
- `on_exit` - When player leaves the location
- `on_examine` - When player looks around (examine/look command)
- `on_tick` - Called periodically (ambient effects)

### Event Handler Signature

All event handlers follow a consistent signature:

```python
def event_handler(
    entity,      # The entity this behavior is attached to
    state,       # Current GameState
    context      # Event-specific context (command, target, etc.)
) -> EventResult:
    """
    Handle an event for this entity.

    Args:
        entity: The entity object (Item, NPC, Door, Location)
        state: Current game state
        context: Dict with event-specific data:
            - "command": ParsedCommand object
            - "player": Player object (shortcut)
            - "location": Current Location object
            - "target": Target of action (for use_with, give, etc.)

    Returns:
        EventResult object with:
            - allow: bool (allow default behavior to proceed?)
            - message: Optional[str] (override default message)
            - side_effects: Optional[callable] (function to call after)
    """
    pass
```

### EventResult Object

```python
@dataclass
class EventResult:
    """Result of an event handler."""
    allow: bool = True           # Allow default behavior?
    message: Optional[str] = None  # Override default message
    abort: bool = False           # Completely abort action

    # Optional callback for side effects after main action
    side_effects: Optional[Callable[[GameState], None]] = None
```

## Approach 1: Behavior Modules (Recommended)

### Concept

Store behaviors as Python modules in a `behaviors/` directory. Reference them in JSON by module path.

### Directory Structure

```
text-game/
├── behaviors/
│   ├── __init__.py
│   ├── items/
│   │   ├── __init__.py
│   │   ├── trapped_chest.py
│   │   ├── magical_harp.py
│   │   └── talking_scroll.py
│   ├── npcs/
│   │   ├── __init__.py
│   │   ├── parrot.py
│   │   ├── guard.py
│   │   └── merchant.py
│   ├── doors/
│   │   ├── __init__.py
│   │   ├── time_locked_door.py
│   │   └── riddle_door.py
│   └── locations/
│       ├── __init__.py
│       ├── throne_room.py
│       └── haunted_corridor.py
├── examples/
│   └── simple_game_state.json
└── src/
    └── behavior_manager.py (new)
```

### JSON Attachment

```json
{
  "items": [
    {
      "id": "item_chest",
      "name": "chest",
      "description": "A large golden chest.",
      "portable": false,
      "location": "loc_treasure_room",
      "behaviors": {
        "on_open": "behaviors.items.trapped_chest:on_open",
        "on_examine": "behaviors.items.trapped_chest:on_examine"
      }
    }
  ],
  "npcs": [
    {
      "id": "npc_parrot",
      "name": "parrot",
      "description": "A colorful parrot perched on a stand.",
      "location": "loc_start",
      "behaviors": {
        "on_examine": "behaviors.npcs.parrot:on_examine",
        "on_talk": "behaviors.npcs.parrot:on_talk"
      }
    }
  ],
  "doors": [
    {
      "id": "door_magical",
      "description": "A shimmering magical door.",
      "locations": ["loc_tower", "loc_secret"],
      "locked": true,
      "open": false,
      "behaviors": {
        "on_open": "behaviors.doors.time_locked_door:on_open"
      }
    }
  ],
  "locations": [
    {
      "id": "loc_throne_room",
      "name": "Throne Room",
      "description": "A grand throne room.",
      "behaviors": {
        "on_enter": "behaviors.locations.throne_room:on_enter"
      }
    }
  ]
}
```

### Behavior Module Example

**File**: `behaviors/items/trapped_chest.py`

```python
"""Trapped chest behavior - requires gloves to open safely."""

from src.behavior_manager import EventResult

def on_examine(entity, state, context):
    """Enhanced examine - hint at the trap."""
    # Let default examine happen, but add extra detail
    result = EventResult(allow=True)

    def show_hint(state):
        print("You notice a tiny hole in the lock. Suspicious...")

    result.side_effects = show_hint
    return result


def on_open(entity, state, context):
    """Check for gloves before allowing open."""
    player = context["player"]

    # Check if player has protective gloves
    has_gloves = any(
        item_id for item_id in player.inventory
        if state.get_item_by_id(item_id).name == "gloves"
    )

    if has_gloves:
        result = EventResult(
            allow=True,
            message="Your gloves protect you from the poison needle!"
        )
    else:
        result = EventResult(
            allow=False,  # Prevent opening
            message="A poison needle pricks your finger! You feel dizzy..."
        )

        def apply_damage(state):
            state.player.stats["health"] = state.player.stats.get("health", 100) - 10
            print(f"Health: {state.player.stats['health']}")

        result.side_effects = apply_damage

    return result
```

**File**: `behaviors/npcs/parrot.py`

```python
"""Parrot NPC - reacts to crackers."""

from src.behavior_manager import EventResult

def on_examine(entity, state, context):
    """Parrot reacts differently based on inventory."""
    player = context["player"]

    # Check if player has cracker
    has_cracker = any(
        item_id for item_id in player.inventory
        if state.get_item_by_id(item_id).name == "cracker"
    )

    if has_cracker:
        message = (
            "A colorful parrot perched on a stand.\n"
            "The parrot's eyes light up when it sees your cracker.\n"
            "'CRACKER! CRACKER!' it squawks loudly."
        )
    else:
        message = (
            "A colorful parrot perched on a stand.\n"
            "It looks at you with disinterest."
        )

    return EventResult(allow=False, message=message)


def on_talk(entity, state, context):
    """Parrot talks back."""
    import random

    phrases = [
        "The parrot squawks: 'HELLO!'",
        "The parrot tilts its head: 'PRETTY BIRD!'",
        "The parrot ruffles its feathers: 'CRACKER!'",
    ]

    return EventResult(
        allow=False,
        message=random.choice(phrases)
    )
```

### Behavior Manager Implementation

**File**: `src/behavior_manager.py`

```python
"""Behavior management system for entity events."""

from typing import Optional, Dict, Callable, Any
from dataclasses import dataclass
import importlib

@dataclass
class EventResult:
    """Result from an event handler."""
    allow: bool = True
    message: Optional[str] = None
    abort: bool = False
    side_effects: Optional[Callable] = None


class BehaviorManager:
    """
    Manages loading and invoking entity behaviors.

    Behaviors are Python functions loaded from module paths.
    """

    def __init__(self):
        self._cache: Dict[str, Callable] = {}

    def load_behavior(self, behavior_path: str) -> Optional[Callable]:
        """
        Load a behavior function from module path.

        Args:
            behavior_path: "module.path:function_name"

        Returns:
            Callable behavior function or None if not found
        """
        # Check cache first
        if behavior_path in self._cache:
            return self._cache[behavior_path]

        try:
            # Split module path and function name
            module_path, function_name = behavior_path.split(':')

            # Import the module
            module = importlib.import_module(module_path)

            # Get the function
            behavior_func = getattr(module, function_name)

            # Cache it
            self._cache[behavior_path] = behavior_func

            return behavior_func

        except (ValueError, ImportError, AttributeError) as e:
            print(f"Warning: Could not load behavior '{behavior_path}': {e}")
            return None

    def invoke_behavior(
        self,
        entity: Any,
        event_name: str,
        state: Any,
        context: Dict[str, Any]
    ) -> Optional[EventResult]:
        """
        Invoke a behavior for an entity event.

        Args:
            entity: Entity object with 'behaviors' dict
            event_name: Event name (e.g., "on_open")
            state: Current GameState
            context: Event context dict

        Returns:
            EventResult or None if no behavior attached
        """
        # Check if entity has behaviors
        if not hasattr(entity, 'behaviors') or not entity.behaviors:
            return None

        # Check if this event has a behavior
        behavior_path = entity.behaviors.get(event_name)
        if not behavior_path:
            return None

        # Load the behavior function
        behavior_func = self.load_behavior(behavior_path)
        if not behavior_func:
            return None

        # Invoke it
        try:
            result = behavior_func(entity, state, context)

            # Ensure result is EventResult
            if not isinstance(result, EventResult):
                print(f"Warning: Behavior {behavior_path} didn't return EventResult")
                return None

            return result

        except Exception as e:
            print(f"Error in behavior {behavior_path}: {e}")
            import traceback
            traceback.print_exc()
            return None


# Global instance
_behavior_manager = BehaviorManager()

def get_behavior_manager() -> BehaviorManager:
    """Get the global behavior manager instance."""
    return _behavior_manager
```

### Integration with Game Engine

Modify entity interaction functions to check for behaviors:

**Example**: Modified `open_item()` function

```python
def open_item(state: GameState, command: ParsedCommand):
    """Open an item or door, with behavior support."""
    from src.behavior_manager import get_behavior_manager

    # ... existing door/item finding logic ...

    if item_name == "chest":
        # Get the chest entity
        chest = # ... find chest ...

        # Prepare event context
        context = {
            "command": command,
            "player": state.player,
            "location": get_current_location(state)
        }

        # Check for custom behavior
        behavior_mgr = get_behavior_manager()
        result = behavior_mgr.invoke_behavior(chest, "on_open", state, context)

        if result:
            # Custom behavior handled it
            if result.message:
                print(result.message)

            if result.abort:
                return False

            if not result.allow:
                # Behavior prevented opening
                if result.side_effects:
                    result.side_effects(state)
                return False

        # Either no behavior or behavior allowed default
        # ... existing chest opening logic ...

        if result and result.side_effects:
            result.side_effects(state)

        return "win"
```

### Advantages

✅ **Clean separation**: Behaviors live in separate files
✅ **Easy to add**: Just create new Python file and reference in JSON
✅ **Testable**: Each behavior module can be unit tested
✅ **Version control friendly**: Behaviors are code files, not embedded strings
✅ **IDE support**: Full syntax highlighting, autocomplete, debugging
✅ **Reusable**: Same behavior can be attached to multiple entities
✅ **Hot reload**: Can reload behaviors without restarting game (in development)

### Disadvantages

❌ **More files**: Each behavior needs its own file
❌ **No true sandboxing**: Behaviors have full Python access
❌ **Import overhead**: First load of each behavior requires import

## Approach 2: Inline Python Strings

### Concept

Embed Python code directly in JSON as strings. Execute with `exec()`.

### JSON Example

```json
{
  "items": [
    {
      "id": "item_chest",
      "name": "chest",
      "behaviors": {
        "on_open": "if 'gloves' not in [state.get_item_by_id(i).name for i in player.inventory]:\n    print('Poison needle!')\n    player.stats['health'] -= 10\n    return False"
      }
    }
  ]
}
```

### Advantages

✅ **Simple**: Everything in one file
✅ **No imports**: No module loading needed

### Disadvantages

❌ **Unreadable**: Multiline code in JSON strings is terrible
❌ **No syntax checking**: Errors only found at runtime
❌ **No IDE support**: No highlighting, autocomplete
❌ **Hard to test**: Can't unit test inline strings easily
❌ **Security risk**: `exec()` is dangerous
❌ **Version control**: Diffs are messy

**Verdict**: ❌ Not recommended

## Approach 3: External Script Files

### Concept

Store behaviors as standalone `.py` files. Reference by filename in JSON.

### Directory Structure

```
game_data/
├── game_state.json
└── scripts/
    ├── trapped_chest_open.py
    ├── parrot_examine.py
    └── throne_room_enter.py
```

### JSON Example

```json
{
  "items": [
    {
      "id": "item_chest",
      "behaviors": {
        "on_open": "scripts/trapped_chest_open.py"
      }
    }
  ]
}
```

### Script Example

**File**: `scripts/trapped_chest_open.py`

```python
# Trapped chest open behavior
# Available: entity, state, context

player = context["player"]
has_gloves = any(
    state.get_item_by_id(item_id).name == "gloves"
    for item_id in player.inventory
)

if has_gloves:
    result.allow = True
    result.message = "Your gloves protect you!"
else:
    result.allow = False
    result.message = "A poison needle pricks you!"

    def damage():
        state.player.stats["health"] -= 10

    result.side_effects = damage
```

### Advantages

✅ **One script per behavior**: Simple organization
✅ **Editable**: Game authors can edit scripts directly
✅ **Syntax highlighting**: IDEs recognize `.py` files

### Disadvantages

❌ **Global namespace pollution**: Scripts execute in shared namespace
❌ **No structure**: Scripts are free-form
❌ **Hard to debug**: Stack traces don't work well
❌ **Coupling**: Scripts need to know about result object structure

**Verdict**: ⚠️ Workable but not ideal

## Approach 4: Behavior Classes

### Concept

Define behaviors as classes inheriting from base `Behavior` class.

### Example

```python
# behaviors/items/trapped_chest.py

from src.behavior import ItemBehavior, EventResult

class TrappedChestBehavior(ItemBehavior):
    """Chest that poisons player without gloves."""

    def on_open(self, entity, state, context):
        player = context["player"]

        if self.player_has_item(player, state, "gloves"):
            return EventResult(
                allow=True,
                message="Your gloves protect you from the poison needle!"
            )
        else:
            return EventResult(
                allow=False,
                message="A poison needle pricks your finger!",
                side_effects=lambda s: self.damage_player(s, 10)
            )

    def on_examine(self, entity, state, context):
        return EventResult(
            allow=True,
            side_effects=lambda s: print("You notice a tiny hole in the lock...")
        )

    # Helper methods
    def player_has_item(self, player, state, item_name):
        return any(
            state.get_item_by_id(i).name == item_name
            for i in player.inventory
        )

    def damage_player(self, state, amount):
        state.player.stats["health"] -= amount
        print(f"Health: {state.player.stats['health']}")
```

### JSON Reference

```json
{
  "items": [
    {
      "id": "item_chest",
      "behavior_class": "behaviors.items.trapped_chest:TrappedChestBehavior"
    }
  ]
}
```

### Advantages

✅ **Structured**: Clear methods for each event
✅ **Inheritance**: Can share common functionality in base class
✅ **Helper methods**: Easy to add reusable utilities
✅ **Type hints**: Full IDE support

### Disadvantages

❌ **Boilerplate**: Need full class for simple behaviors
❌ **Overhead**: Creating class instances for each entity

**Verdict**: ✅ Good for complex behaviors, overkill for simple ones

## Hybrid Approach (Recommended)

Combine **Approach 1** (modules) with **Approach 4** (classes) for flexibility:

- **Simple behaviors**: Use module functions (Approach 1)
- **Complex behaviors**: Use behavior classes (Approach 4)

### JSON Syntax

```json
{
  "items": [
    {
      "id": "item_simple",
      "behaviors": {
        "on_examine": "behaviors.items.simple:on_examine"
      }
    },
    {
      "id": "item_complex",
      "behavior_class": "behaviors.items.complex:ComplexBehavior"
    }
  ]
}
```

### Behavior Manager Enhancement

```python
def invoke_behavior(self, entity, event_name, state, context):
    """Invoke behavior - supports both functions and classes."""

    # Check for behavior class first
    if hasattr(entity, 'behavior_class'):
        behavior_instance = self.load_behavior_class(entity.behavior_class)
        if behavior_instance and hasattr(behavior_instance, event_name):
            method = getattr(behavior_instance, event_name)
            return method(entity, state, context)

    # Fall back to event-specific function behaviors
    if hasattr(entity, 'behaviors') and entity.behaviors:
        behavior_path = entity.behaviors.get(event_name)
        if behavior_path:
            behavior_func = self.load_behavior(behavior_path)
            if behavior_func:
                return behavior_func(entity, state, context)

    return None
```

## Safety and Sandboxing

### Execution Context

Provide limited context to behaviors:

```python
# Safe context - only expose what's needed
safe_context = {
    "player": state.player,
    "location": get_current_location(state),
    "command": context["command"],
    "state": state,  # Provide whole state but trust behavior code
}

# Don't expose:
# - File system access
# - Network access
# - Other sensitive modules
```

### Error Handling

Wrap all behavior invocations in try/except:

```python
try:
    result = behavior_func(entity, state, context)
except Exception as e:
    print(f"⚠️  Behavior error: {e}")
    # Log error but don't crash game
    # Optionally: disable this behavior for remainder of session
    return None
```

### Timeout Protection

For behaviors that might infinite loop:

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Behavior took too long")

# Set 1-second timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(1)

try:
    result = behavior_func(entity, state, context)
finally:
    signal.alarm(0)  # Cancel alarm
```

## Testing Strategy

### Unit Testing Behaviors

```python
# tests/behaviors/test_trapped_chest.py

from behaviors.items.trapped_chest import on_open
from src.behavior_manager import EventResult

def test_trapped_chest_with_gloves():
    """Test chest opens safely with gloves."""
    # Create mock state
    state = create_mock_state()
    state.player.inventory = ["item_gloves"]

    entity = Mock(name="chest")
    context = {"player": state.player}

    result = on_open(entity, state, context)

    assert result.allow == True
    assert "protect" in result.message.lower()


def test_trapped_chest_without_gloves():
    """Test chest poisons player without gloves."""
    state = create_mock_state()
    state.player.inventory = []
    state.player.stats["health"] = 100

    entity = Mock(name="chest")
    context = {"player": state.player}

    result = on_open(entity, state, context)

    assert result.allow == False
    assert "poison" in result.message.lower()

    # Execute side effect
    result.side_effects(state)
    assert state.player.stats["health"] == 90
```

### Integration Testing

```python
# tests/integration/test_behavior_system.py

def test_behavior_invoked_on_open():
    """Test that opening chest triggers behavior."""
    game_state = load_game_state("test_game_with_behaviors.json")

    # Player doesn't have gloves
    assert "item_gloves" not in game_state.player.inventory

    # Try to open trapped chest
    result = open_item(game_state, "chest")

    # Should fail due to behavior
    assert result == False

    # Player should be damaged
    assert game_state.player.stats["health"] < 100
```

## Documentation for Game Authors

### Behavior Authoring Guide

Create `docs/behavior_authoring.md`:

```markdown
# Writing Custom Behaviors

## Quick Start

1. Create a new file in `behaviors/items/` (or npcs/, doors/, locations/)
2. Define event handler functions
3. Reference in your game JSON

## Example: Simple Behavior

**File**: behaviors/items/magic_sword.py

```python
from src.behavior_manager import EventResult

def on_examine(entity, state, context):
    """Sword glows when examined."""
    return EventResult(
        allow=True,  # Show normal description too
        side_effects=lambda s: print("✨ The sword glows with magical energy!")
    )

def on_take(entity, state, context):
    """Sword can only be taken by worthy players."""
    player = context["player"]

    if player.stats.get("strength", 0) >= 10:
        return EventResult(
            allow=True,
            message="The sword accepts you as its wielder!"
        )
    else:
        return EventResult(
            allow=False,
            message="The sword is too heavy for you to lift."
        )
```

**JSON**:
```json
{
  "id": "item_magic_sword",
  "name": "sword",
  "behaviors": {
    "on_examine": "behaviors.items.magic_sword:on_examine",
    "on_take": "behaviors.items.magic_sword:on_take"
  }
}
```

## Available Events

[List all events for each entity type]

## EventResult Object

[Document EventResult fields and their effects]

## Helper Functions

[Document utility functions available to behaviors]

## Best Practices

1. Keep behaviors focused (one file per item/NPC)
2. Return EventResult from all handlers
3. Use side_effects for actions after main behavior
4. Test your behaviors!
```

## Performance Considerations

### Lazy Loading

Only load behaviors when first needed:

```python
def load_behavior(self, behavior_path):
    # Check cache first
    if behavior_path in self._cache:
        return self._cache[behavior_path]

    # Load on demand
    behavior = self._import_behavior(behavior_path)
    self._cache[behavior_path] = behavior
    return behavior
```

### Behavior Pre-compilation

For frequently-used behaviors, pre-compile:

```python
def preload_common_behaviors(self):
    """Load common behaviors at startup."""
    common = [
        "behaviors.items.chest:on_open",
        "behaviors.npcs.merchant:on_talk",
        # ... other common behaviors
    ]
    for behavior_path in common:
        self.load_behavior(behavior_path)
```

### Entity Behavior Caching

Cache behavior references on entities:

```python
class Item:
    def __init__(self, ...):
        self.behaviors = {}
        self._behavior_cache = {}  # Cached callable references
```

## Migration Path

### Phase 1: Infrastructure
1. Implement BehaviorManager
2. Add EventResult dataclass
3. Create behaviors/ directory structure
4. Add behavior support to entity models

### Phase 2: Integration
1. Modify entity interaction functions to check behaviors
2. Add behavior invocation before/after default actions
3. Implement error handling and logging

### Phase 3: Examples
1. Create example behaviors for common patterns
2. Write behavior authoring documentation
3. Convert some existing special-case code to behaviors

### Phase 4: Advanced Features
1. Add behavior inheritance/composition
2. Implement behavior state persistence
3. Add behavior debugging tools
4. Create behavior testing utilities

## Recommended Implementation

**Use Hybrid Approach**:
- Module functions for simple behaviors (80% of cases)
- Behavior classes for complex multi-event behaviors (20% of cases)
- BehaviorManager to handle both
- EventResult for consistent return values
- Comprehensive error handling
- Good documentation for game authors

This provides maximum flexibility while keeping simple cases simple.
