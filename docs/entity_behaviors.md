# Entity Behaviors - Design Document

## Overview

This document describes the system for attaching custom Python behavior to game entities and extending the game engine through external behavior modules. The design allows new functionality to be added by loading information from behavior modules and augmenting the game's internal data structures—without modifying core engine code.

## Problem Statement

Game authors need to:
1. Define custom behavior for specific entities (e.g., a talking parrot NPC, a trapped chest, a magical door)
2. Add new verbs and commands without modifying core engine code
3. Write this behavior in Python for maximum flexibility
4. Have behavior invoked at appropriate game events
5. Package complete features (vocabulary, handlers, behaviors) in self-contained modules

## Design Goals

1. **Extensibility**: New verbs, handlers, and behaviors load from external modules
2. **Simplicity**: Minimal boilerplate to add new functionality
3. **Safety**: Isolate custom code from core engine (error handling)
4. **Discoverability**: Clear module structure for finding behaviors
5. **Testability**: Behaviors can be unit tested independently
6. **Data-driven**: Behavior attachment expressible in game state JSON

## Terminology

To avoid confusion, this document uses these terms consistently:

- **JSONProtocolHandler**: The main protocol class that processes commands and manages game state
- **Command handler** (or `handle_*` function): A function that processes a specific verb and returns a result dict
- **Entity behavior** (or `on_*` function): A function attached to an entity that responds to events and returns EventResult
- **Behavior module**: A Python file that can export vocabulary, command handlers, and entity behaviors

## Architecture Overview

The behavior system has three extension points:

1. **Vocabulary Extensions**: New verbs and their properties
2. **Command Handlers**: Functions that process commands for those verbs
3. **Entity Behaviors**: Custom responses to events on specific entities

All three can be provided by behavior modules and loaded at startup.

```
┌─────────────────┐     ┌──────────────────┐
│ Behavior Module │────▶│ BehaviorManager  │
│  - vocabulary   │     │  - load modules  │
│  - handle_*     │     │  - merge vocab   │
│  - on_*         │     │  - register      │
└─────────────────┘     └────────┬─────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
     │  Vocabulary │    │   Command   │    │   Entity    │
     │   (merged)  │    │  Handlers   │    │  Behaviors  │
     └─────────────┘    └─────────────┘    └─────────────┘
```

## Behavior Module Structure

### Module Exports

A behavior module can export any combination of:

```python
# behaviors/items/rubber_duck.py

# 1. Vocabulary extensions (optional) - only for NEW verbs not in base vocabulary
vocabulary = {
    "verbs": [
        {
            "word": "squeeze",
            "synonyms": ["squish", "honk"],
            "object_required": True
        }
    ]
}

# 2. Command handler (optional)
def handle_squeeze(handler, action):
    """Handle the squeeze command.

    Args:
        handler: JSONProtocolHandler instance
        action: Action dict with verb, object, etc.

    Returns:
        Result dict with entity_obj for behavior invocation
    """
    obj_name = action.get("object")
    item = handler._find_accessible_item(obj_name)

    if not item:
        return {
            "type": "result",
            "success": False,
            "action": "squeeze",
            "error": {"message": "You don't see that here."}
        }

    return {
        "type": "result",
        "success": True,
        "action": "squeeze",
        "entity": handler._entity_to_dict(item),
        "entity_obj": item  # Required for behavior invocation
    }

# 3. Entity behaviors (optional)
def on_squeeze(entity, state, context):
    """Called when this entity is squeezed."""
    return EventResult(
        allow=True,
        message="The rubber duck lets out a satisfying squeak!"
    )
```

**Note**: The `entity_obj` field is an internal reference used by `_apply_behavior()` to invoke entity behaviors. It's removed before the result is returned to the caller.

**Important**: Both registered handlers (from behavior modules) and built-in handlers must include `entity_obj` in successful results for behaviors to be invoked. When migrating to this system, existing built-in handlers in `json_protocol.py` need to be updated to include this field.

### Directory Structure

```
text-game/
├── behaviors/
│   ├── __init__.py
│   ├── core/                    # Core behaviors (shipped with engine)
│   │   ├── __init__.py
│   │   ├── consumables.py       # drink, eat handlers + potion/food behaviors
│   │   ├── light_sources.py     # lantern auto-light behavior
│   │   └── containers.py        # chest open/win behaviors
│   ├── items/                   # Game-specific item behaviors
│   │   ├── __init__.py
│   │   ├── trapped_chest.py
│   │   └── magical_harp.py
│   ├── npcs/
│   │   ├── __init__.py
│   │   ├── parrot.py
│   │   └── merchant.py
│   ├── doors/
│   │   ├── __init__.py
│   │   └── time_locked_door.py
│   └── locations/
│       ├── __init__.py
│       └── throne_room.py
├── src/
│   ├── behavior_manager.py
│   └── json_protocol.py
└── data/
    ├── vocabulary.json          # Base vocabulary
    └── game_state.json
```

## Dynamic Event Naming

Events are derived from verbs automatically using the `on_<verb>` convention:

| Verb | Event Name | Entity Types |
|------|------------|--------------|
| examine | on_examine | item, npc, door, location |
| take | on_take | item |
| drop | on_drop | item |
| use | on_use | item |
| open | on_open | item, door |
| close | on_close | item, door |
| unlock | on_unlock | door |
| lock | on_lock | door |
| talk | on_talk | npc |
| attack | on_attack | npc, item |
| give | on_give | npc |
| drink | on_drink | item |
| eat | on_eat | item |
| squeeze | on_squeeze | item |
| *any verb* | on_*verb* | *depends on handler* |

**Special events** not derived from verbs:
- `on_enter` - When player enters a location
- `on_exit` - When player leaves a location
- `on_pass_through` - When player moves through a door
- `on_use_with` - When using one item with another (see below)
- `on_tick` - Periodic updates (see below)

This means adding a new verb automatically creates the corresponding event—no predefined event list needed.

### Advanced Events (May Be Deferred)

These events add complexity and may be omitted from the initial implementation:

#### on_use_with Event

Triggered when a player uses one item with another, such as "use key with door" or "use matches with candle".

**Vocabulary support required**: The JSON protocol would need to support a `target` field:
```json
{"verb": "use", "object": "key", "target": "door"}
```

**Handler invocation**: The event is invoked on the primary object (key), with the target in context:
```python
def on_use_with(entity, state, context):
    target = context["target"]  # The door
    if target.locked:
        target.locked = False
        return EventResult(
            allow=True,
            message="You unlock the door with the key."
        )
    return EventResult(
        allow=False,
        message="The door is already unlocked."
    )
```

**Complexity**: Requires changes to vocabulary, LLM prompt, and protocol handler. Consider implementing as a separate "unlock" verb instead for simpler cases.

#### on_tick Event

Periodic event for time-based behaviors like NPC wandering, torch burning out, or ambient effects.

**Game loop integration**: The engine must call tick handlers at regular intervals:
```python
# In game loop
tick_count += 1
if tick_count % TICKS_PER_TURN == 0:
    behavior_manager.invoke_tick_events(state)
```

**Entity context**: Tick handlers receive minimal context since they're not triggered by player action:
```python
def on_tick(entity, state, context):
    # context contains only {"location": entity_location}

    # Example: NPC wanders randomly
    if random.random() < 0.3:
        new_loc = random.choice(adjacent_locations)
        entity.location = new_loc
        return EventResult(
            allow=True,
            message=f"The {entity.name} wanders away."
        )
    return EventResult(allow=True)
```

**Complexity**: Requires game loop changes, decisions about tick frequency, and handling of tick messages (should they be shown to player?). Consider deferring until core behavior system is stable.

## Event Handler Signature

All event handlers follow a consistent signature:

```python
def on_verb(entity, state, context) -> EventResult:
    """
    Handle an event for this entity.

    Args:
        entity: The entity object (Item, NPC, Door, Location)
        state: Current GameState
        context: Dict with event-specific data

    Returns:
        EventResult object
    """
    pass
```

### Event Context

Standard fields present in all contexts:

```python
context = {
    "location": current_location,     # Location object (current player location)
}
```

**Note**: Behaviors access the player via `state.player` rather than through context, since state is always passed to handlers.

Event-specific additional fields:

```python
# on_give: When giving item to NPC
context["item"] = item_being_given

# on_pass_through: When moving through door
context["direction"] = "north"
context["from_location"] = origin_loc
context["to_location"] = dest_loc

# For door events involving locks
context["lock"] = lock_object
context["has_key"] = True/False
```

### EventResult Object

```python
@dataclass
class EventResult:
    """Result from an event handler."""
    allow: bool = True                # Allow default behavior to proceed?
    message: Optional[str] = None     # Message for LLM narrator
```

Behaviors modify state directly rather than using callbacks. This is simpler and matches the pattern used by command handlers.

## Core Behavior Modules

These modules ship with the engine and provide standard functionality that's been moved out of the hardcoded engine:

### behaviors/core/consumables.py

Handles drink and eat commands, plus potion/food behaviors.

**Note**: The `drink` and `eat` verbs should be defined in the base `vocabulary.json`, not in this module. Only NEW verbs need vocabulary extensions.

```python
"""Consumable items - drink and eat functionality."""

from src.behavior_manager import EventResult

# Helper for consume commands (drink/eat share same pattern)
def _handle_consume(handler, action, verb):
    """Common handler for drink/eat commands."""
    obj_name = action.get("object")

    if not obj_name:
        return {
            "type": "result",
            "success": False,
            "action": verb,
            "error": {"message": f"{verb.capitalize()} what?"}
        }

    # Find item in inventory
    item = None
    for item_id in handler.state.player.inventory:
        i = handler._get_item_by_id(item_id)
        if i and i.name == obj_name:
            item = i
            break

    if not item:
        return {
            "type": "result",
            "success": False,
            "action": verb,
            "error": {"message": "You're not carrying that."}
        }

    return {
        "type": "result",
        "success": True,
        "action": verb,
        "entity": handler._entity_to_dict(item),
        "entity_obj": item
    }

# Command handlers
def handle_drink(handler, action):
    """Handle drink command."""
    return _handle_consume(handler, action, "drink")

def handle_eat(handler, action):
    """Handle eat command."""
    return _handle_consume(handler, action, "eat")

# Entity behaviors for specific items

def on_drink_health_potion(entity, state, context):
    """Health potion drinking behavior."""
    # Remove from inventory
    state.player.inventory.remove(entity.id)
    entity.location = ""  # Consumed
    # Heal player
    state.player.stats["health"] = min(
        state.player.stats.get("health", 100) + 20,
        100
    )

    return EventResult(
        allow=True,
        message="You drink the glowing red potion. Warmth spreads through your body as your wounds heal."
    )
```

### behaviors/core/light_sources.py

Handles lantern and other light source behaviors:

```python
"""Light source behaviors - lanterns, torches, etc."""

from src.behavior_manager import EventResult

def on_take(entity, state, context):
    """Auto-light when taken (magical runes activate on touch)."""
    entity.states['lit'] = True

    return EventResult(
        allow=True,
        message="As your hand closes around the lantern, the runes flare to life, casting a warm glow."
    )


def on_drop(entity, state, context):
    """Extinguish when dropped (magical runes deactivate)."""
    entity.states['lit'] = False

    return EventResult(
        allow=True,
        message="The lantern's runes fade as you set it down, leaving it dark and cold."
    )
```

### behaviors/core/containers.py

Handles chest and container behaviors:

```python
"""Container behaviors - chests, boxes, etc."""

from src.behavior_manager import EventResult

def on_open_treasure_chest(entity, state, context):
    """Win condition when opening treasure chest."""
    state.player.flags["won"] = True

    return EventResult(
        allow=True,
        message="You open the chest and find glittering treasure! You win!"
    )
```

## Data Model

### Behaviors Field

All entity types support a `behaviors` dict mapping event names to module paths:

```python
@dataclass
class Item:
    id: str
    name: str
    description: str
    type: str
    portable: bool
    location: str
    states: Dict[str, Any] = field(default_factory=dict)
    container: Optional[ContainerInfo] = None
    provides_light: bool = False
    behaviors: Dict[str, str] = field(default_factory=dict)  # event -> module:function
```

### JSON Schema

```json
{
  "items": [
    {
      "id": "item_potion",
      "name": "potion",
      "description": "A glowing red potion.",
      "portable": true,
      "location": "loc_tower",
      "behaviors": {
        "on_drink": "behaviors.core.consumables:on_drink_health_potion"
      }
    },
    {
      "id": "item_lantern",
      "name": "lantern",
      "description": "A copper lantern with runes.",
      "portable": true,
      "provides_light": true,
      "location": "loc_hallway",
      "behaviors": {
        "on_take": "behaviors.core.light_sources:on_take",
        "on_drop": "behaviors.core.light_sources:on_drop"
      }
    },
    {
      "id": "item_chest",
      "name": "chest",
      "description": "A large golden chest.",
      "portable": false,
      "location": "loc_treasure_room",
      "behaviors": {
        "on_open": "behaviors.core.containers:on_open_treasure_chest"
      }
    }
  ]
}
```

## Behavior Manager Implementation

The BehaviorManager loads modules, merges vocabulary, and registers handlers.

### Two Loading Mechanisms

The BehaviorManager uses two different mechanisms for loading code:

1. **`load_module()`** - Called at startup to register command handlers and vocabulary extensions. Scans a module for `handle_*` functions and `vocabulary` dict.

2. **`load_behavior()`** - Called during gameplay to load entity-specific behaviors referenced in game state JSON (e.g., `"behaviors.core.light_sources:on_take"`). Uses `module:function` string format.

This separation allows:
- Core handlers to be registered once at startup
- Entity behaviors to be loaded on-demand when first invoked
- Hot reload of behaviors during development (clear cache, re-invoke)

```python
"""Behavior management system for entity events."""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import importlib
import json
from pathlib import Path

@dataclass
class EventResult:
    """Result from an event handler."""
    allow: bool = True
    message: Optional[str] = None


class BehaviorManager:
    """
    Manages loading and invoking entity behaviors.

    Also handles vocabulary extensions and protocol handler registration.
    """

    def __init__(self):
        self._behavior_cache: Dict[str, Callable] = {}
        self._handlers: Dict[str, Callable] = {}  # verb -> handler function
        self._vocabulary_extensions: List[Dict] = []

    def load_module(self, module_path: str) -> None:
        """
        Load a behavior module and register its extensions.

        Args:
            module_path: Python module path (e.g., "behaviors.core.consumables")
        """
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            print(f"Warning: Could not load behavior module {module_path}: {e}")
            return

        # Register vocabulary extensions
        if hasattr(module, 'vocabulary'):
            self._vocabulary_extensions.append(module.vocabulary)

        # Register protocol handlers
        for name in dir(module):
            if name.startswith('handle_'):
                verb = name[7:]  # Remove 'handle_' prefix
                handler = getattr(module, name)
                self._handlers[verb] = handler

    def load_modules(self, module_paths: List[str]) -> None:
        """Load multiple behavior modules."""
        for path in module_paths:
            self.load_module(path)

    def get_merged_vocabulary(self, base_vocab: Dict) -> Dict:
        """
        Merge base vocabulary with all extensions.

        Args:
            base_vocab: Base vocabulary dict from vocabulary.json

        Returns:
            Merged vocabulary dict
        """
        result = {
            "verbs": list(base_vocab.get("verbs", [])),
            "directions": list(base_vocab.get("directions", []))
        }

        for ext in self._vocabulary_extensions:
            # Merge verbs (avoid duplicates by word)
            existing_words = {v["word"] for v in result["verbs"]}
            for verb in ext.get("verbs", []):
                if verb["word"] not in existing_words:
                    result["verbs"].append(verb)
                    existing_words.add(verb["word"])

            # Merge directions
            existing_dirs = {d["word"] for d in result["directions"]}
            for direction in ext.get("directions", []):
                if direction["word"] not in existing_dirs:
                    result["directions"].append(direction)
                    existing_dirs.add(direction["word"])

        return result

    def get_handler(self, verb: str) -> Optional[Callable]:
        """
        Get registered handler for a verb.

        Args:
            verb: The verb to handle

        Returns:
            Handler function or None
        """
        return self._handlers.get(verb)

    def has_handler(self, verb: str) -> bool:
        """Check if a handler is registered for this verb."""
        return verb in self._handlers

    def load_behavior(self, behavior_path: str) -> Optional[Callable]:
        """
        Load a behavior function from module path.

        Args:
            behavior_path: "module.path:function_name"

        Returns:
            Callable behavior function or None
        """
        if behavior_path in self._behavior_cache:
            return self._behavior_cache[behavior_path]

        try:
            module_path, function_name = behavior_path.split(':')
            module = importlib.import_module(module_path)
            behavior_func = getattr(module, function_name)
            self._behavior_cache[behavior_path] = behavior_func
            return behavior_func

        except (ValueError, ImportError, AttributeError) as e:
            print(f"Warning: Could not load behavior {behavior_path}: {e}")
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
            event_name: Event name (e.g., "on_drink")
            state: Current GameState
            context: Event context dict

        Returns:
            EventResult or None if no behavior attached
        """
        if not hasattr(entity, 'behaviors') or not entity.behaviors:
            return None

        behavior_path = entity.behaviors.get(event_name)
        if not behavior_path:
            return None

        behavior_func = self.load_behavior(behavior_path)
        if not behavior_func:
            return None

        try:
            result = behavior_func(entity, state, context)

            if not isinstance(result, EventResult):
                return None

            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    def clear_cache(self):
        """Clear behavior cache (useful for hot reload)."""
        self._behavior_cache.clear()


# Global instance
_behavior_manager = BehaviorManager()

def get_behavior_manager() -> BehaviorManager:
    """Get the global behavior manager instance."""
    return _behavior_manager
```

## Protocol Handler Integration

The JSON protocol handler checks for registered handlers before built-in ones:

```python
class JSONProtocolHandler:
    def __init__(self, state, behavior_manager=None):
        self.state = state
        self.behavior_manager = behavior_manager or get_behavior_manager()

        # Built-in command handlers
        self._builtin_handlers = {
            "go": self._cmd_go,
            "take": self._cmd_take,
            "drop": self._cmd_drop,
            "examine": self._cmd_examine,
            "open": self._cmd_open,
            "close": self._cmd_close,
            "unlock": self._cmd_unlock,
            "lock": self._cmd_lock,
            "inventory": self._cmd_inventory,
            "look": self._cmd_look,
        }

    def _process_command(self, message: Dict) -> Dict:
        """Process a command message."""
        action = message.get("action", {})
        verb = action.get("verb")

        if not verb:
            return self._error_result("unknown", "No verb specified")

        # Check for registered handler first (from behavior modules)
        handler = self.behavior_manager.get_handler(verb)
        if handler:
            result = handler(self, action)
            return self._apply_behavior(result, action)

        # Fall back to built-in handler
        # Note: Built-in handlers must also include entity_obj for behaviors to be invoked
        builtin = self._builtin_handlers.get(verb)
        if builtin:
            result = builtin(action)
            return self._apply_behavior(result, action)

        return self._error_result(verb, f"Unknown command: {verb}")

    def _apply_behavior(self, result: Dict, action: Dict) -> Dict:
        """Apply entity behavior to command result."""
        if not result.get("success"):
            return result

        entity = result.get("entity_obj")  # Internal reference
        if not entity:
            return result

        # Build event name from verb
        verb = action.get("verb")
        event_name = f"on_{verb}"

        # Build context
        context = {
            "location": self._get_current_location()
        }

        # Invoke behavior
        behavior_result = self.behavior_manager.invoke_behavior(
            entity, event_name, self.state, context
        )

        if behavior_result:
            if not behavior_result.allow:
                # Behavior prevented action
                result["success"] = False
                result["error"] = {
                    "message": behavior_result.message or "Action prevented.",
                    "reason": "behavior_prevented"
                }
            elif behavior_result.message:
                # Add behavior message
                result["message"] = behavior_result.message

        # Remove internal reference before returning
        result.pop("entity_obj", None)
        return result
```

## Initialization Flow

At game startup:

```python
from src.behavior_manager import get_behavior_manager
from src.json_protocol import JSONProtocolHandler
from src.loader import load_game_state
import json

def initialize_game(game_state_path: str, behavior_modules: list = None):
    """Initialize game with behaviors loaded."""

    # Default core modules
    if behavior_modules is None:
        behavior_modules = [
            "behaviors.core.consumables",
            "behaviors.core.light_sources",
            "behaviors.core.containers",
        ]

    # Load behavior modules
    manager = get_behavior_manager()
    manager.load_modules(behavior_modules)

    # Load and merge vocabulary
    with open("data/vocabulary.json") as f:
        base_vocab = json.load(f)
    merged_vocab = manager.get_merged_vocabulary(base_vocab)

    # Load game state
    state = load_game_state(game_state_path)

    # Create protocol handler
    handler = JSONProtocolHandler(state, manager)

    return handler, merged_vocab
```

## Custom Behavior Module Example

A complete custom module adding a new verb:

```python
# behaviors/items/rubber_duck.py
"""Rubber duck - squeezable toy with custom verb."""

from src.behavior_manager import EventResult

# Vocabulary extension - adds 'squeeze' verb
vocabulary = {
    "verbs": [
        {
            "word": "squeeze",
            "synonyms": ["squish", "honk", "squash"],
            "object_required": True
        }
    ]
}

# Protocol handler for squeeze command
def handle_squeeze(handler, action):
    """Handle squeeze command - find item and invoke behavior."""
    obj_name = action.get("object")

    if not obj_name:
        return {
            "type": "result",
            "success": False,
            "action": "squeeze",
            "error": {"message": "Squeeze what?"}
        }

    # Find item in inventory or location
    item = handler._find_accessible_item(obj_name)
    if not item:
        return {
            "type": "result",
            "success": False,
            "action": "squeeze",
            "error": {"message": "You don't see that here."}
        }

    return {
        "type": "result",
        "success": True,
        "action": "squeeze",
        "entity": handler._entity_to_dict(item),
        "entity_obj": item  # For behavior invocation
    }


# Entity behavior - specific to rubber duck
def on_squeeze(entity, state, context):
    """Rubber duck squeaking behavior."""
    squeeze_count = entity.states.get("squeeze_count", 0) + 1
    entity.states["squeeze_count"] = squeeze_count

    if squeeze_count == 1:
        message = "The rubber duck lets out a satisfying squeak!"
    elif squeeze_count < 5:
        message = "Squeak! The duck seems to enjoy the attention."
    elif squeeze_count == 5:
        message = "SQUEAK! The duck produces an unusually loud noise. Something falls from a nearby shelf..."
        # Could trigger a puzzle effect here
    else:
        message = "The duck squeaks contentedly."

    return EventResult(
        allow=True,
        message=message
    )
```

To use this module, just add it to the load list and attach the behavior to an entity:

```json
{
  "id": "item_duck",
  "name": "rubber duck",
  "description": "A yellow rubber duck.",
  "portable": true,
  "location": "loc_bathroom",
  "behaviors": {
    "on_squeeze": "behaviors.items.rubber_duck:on_squeeze"
  }
}
```

## LLM Narrator Integration

The protocol returns behavior messages for the LLM narrator to render:

```python
# Result with behavior message
{
    "type": "result",
    "success": True,
    "action": "squeeze",
    "entity": {
        "id": "item_duck",
        "name": "rubber duck",
        "description": "A yellow rubber duck.",
        "llm_context": {...}
    },
    "message": "The rubber duck lets out a satisfying squeak!"
}
```

The LLM narrator incorporates this message into its narrative.

### Error Reasons

When behaviors prevent actions:

```python
{
    "type": "result",
    "success": False,
    "action": "open",
    "entity": {...},
    "error": {
        "message": "A poison needle pricks your finger!",
        "reason": "behavior_prevented"
    }
}
```

Error reason codes:
- `behavior_prevented`: Custom behavior blocked the action
- `not_found`: Entity not in location
- `locked`: Door/container is locked
- `no_light`: Too dark to perform action

## Win Condition Checking

After processing any command, check for game-ending conditions:

```python
# In game loop
result = handler.process_message(command)

# Check win condition
if state.player.flags.get("won"):
    print("\nCongratulations! You win!")
    break

# Check lose condition
if state.player.stats.get("health", 100) <= 0:
    print("\nGame Over!")
    break
```

## Testing Strategy

### Unit Testing Behaviors

```python
# tests/behaviors/test_rubber_duck.py

from behaviors.items.rubber_duck import on_squeeze
from src.behavior_manager import EventResult
from unittest.mock import Mock

def test_squeeze_first_time():
    """Test first squeeze."""
    entity = Mock()
    entity.states = {}

    state = Mock()
    context = {"location": Mock()}

    result = on_squeeze(entity, state, context)

    assert result.allow == True
    assert "squeak" in result.message.lower()
    assert entity.states["squeeze_count"] == 1


def test_squeeze_fifth_time():
    """Test fifth squeeze triggers special event."""
    entity = Mock()
    entity.states = {"squeeze_count": 4}

    state = Mock()
    context = {"location": Mock()}

    result = on_squeeze(entity, state, context)

    assert "loud" in result.message.lower()
    assert entity.states["squeeze_count"] == 5
```

### Testing Handler Registration

```python
# tests/test_behavior_manager.py

def test_handler_registration():
    """Test that handlers are registered from modules."""
    manager = BehaviorManager()
    manager.load_module("behaviors.items.rubber_duck")

    assert manager.has_handler("squeeze")

    handler = manager.get_handler("squeeze")
    assert callable(handler)


def test_vocabulary_merge():
    """Test vocabulary extensions are merged."""
    manager = BehaviorManager()
    manager.load_module("behaviors.items.rubber_duck")

    base_vocab = {"verbs": [{"word": "take"}], "directions": []}
    merged = manager.get_merged_vocabulary(base_vocab)

    words = [v["word"] for v in merged["verbs"]]
    assert "take" in words
    assert "squeeze" in words
```

## Migration Path

### Phase 1: Infrastructure
1. Implement BehaviorManager with module loading
2. Add vocabulary merging
3. Add handler registration

### Phase 2: Move Core Behaviors
1. Create behaviors/core/consumables.py (drink, eat)
2. Create behaviors/core/light_sources.py (lantern)
3. Create behaviors/core/containers.py (chest win)
4. Remove hardcoded handlers from json_protocol.py

### Phase 3: Protocol Integration
1. Modify protocol handler to check registered handlers
2. Add behavior invocation after command processing
3. Update result format with behavior messages

### Phase 4: Documentation
1. Write behavior authoring guide
2. Create example modules
3. Add test fixtures

## Benefits of This Design

1. **No engine modifications**: New verbs/behaviors just require loading modules
2. **Self-contained packages**: Vocabulary + handler + behavior in one file
3. **Gradual migration**: Move existing functionality module by module
4. **Clear ownership**: Each module owns its complete functionality
5. **Easy testing**: Test vocabulary, handlers, and behaviors independently
6. **Hot reload support**: Clear cache and reload modules during development

## What Remains in Core Engine

After migration, the core engine contains only:

- **State management**: Moving items, updating locations
- **Command routing**: Parse → find handler → invoke → apply behavior
- **Default handlers**: Basic take/drop/examine/go that most games need
- **Meta-commands**: Save/load/quit/inventory
- **Condition checking**: Win/lose flags after commands

All entity-specific logic lives in behavior modules.

## Best Practices

### For Behavior Authors

1. **Return EventResult from behaviors**: Every `on_*` entity behavior must return EventResult
2. **Return result dict from handlers**: Every `handle_*` command handler must return a result dict
3. **Modify state directly**: Behaviors modify state directly before returning EventResult
4. **Include vocabulary for new verbs only**: Export vocabulary dict only for verbs not in base vocabulary
5. **Keep modules focused**: One feature per module
6. **Test thoroughly**: Unit test each function

### For Engine Integration

1. **Check registered handlers first**: Before built-in handlers
2. **Respect allow=False**: Don't proceed if behavior denies
3. **Preserve messages**: Include in result for LLM
4. **Handle errors gracefully**: Don't crash on behavior errors

## Summary

This behavior system provides:

- **Dynamic event naming**: `on_<verb>` derived from any verb
- **Module-based extensions**: Vocabulary + handlers + behaviors in one file
- **Automatic registration**: Load module → get everything registered
- **Clean separation**: Core engine vs. game-specific logic
- **LLM integration**: Messages flow through to narrator
- **Testability**: Each piece testable in isolation

The design allows the game engine to remain simple while supporting unlimited extension through behavior modules.
