# Behavior Refactoring Design

## Status

This document describes the next phase of the behavior system. Phase 1 (entity behaviors) is implemented and documented in `entity_behaviors.md`. This phase moves command-level logic from `json_protocol.py` into behavior modules.

## Current State

The entity behaviors system (Phase 1) provides:
- Entity-specific event handlers (`on_take`, `on_drop`, etc.)
- Behavior modules with vocabulary extensions
- BehaviorManager for loading and invoking behaviors

However, game-specific logic is spread across multiple files:

**json_protocol.py** contains:
- `_cmd_take`, `_cmd_drop`, `_cmd_put`
- `_cmd_go`, `_cmd_open`, `_cmd_close`
- `_cmd_unlock`, `_cmd_lock`
- `_cmd_examine`, `_cmd_inventory`, `_cmd_look`
- `_cmd_drink`, `_cmd_eat`, `_cmd_attack`, `_cmd_use`
- `_cmd_read`, `_cmd_climb`, `_cmd_pull`, `_cmd_push`
- Helper methods: `_find_accessible_item()`, `_player_has_key_for_door()`, etc.

**game_engine.py** contains parallel implementations:
- `move_player()`, `take_item()`, `drop_item()`, `put_item()`
- `examine_item()`, `open_item()`, `close_door()`, `drink_item()`
- `describe_location()`, `show_inventory()`
- Helper functions: `get_current_location()`, `get_item_by_id()`, `get_door_by_id()`, `player_has_key_for_door()`, etc.

**validators.py** contains game entity knowledge:
- Entity type validation (locations, items, doors, locks, NPCs)
- Valid location types for items (location, item, npc, player)
- Exit references and door_id validation
- Lock/key relationships
- Container cycle detection

**vocabulary_generator.py** contains game semantics:
- Extracts item and NPC names as nouns
- Knows entity structure for vocabulary generation

**state_manager.py** contains game entity definitions:
- Entity dataclasses (Item, Location, Door, Lock, NPC, PlayerState)
- Convenience methods like `move_item()`, `set_player_location()`
- Property accessors for game concepts (portable, container, locked, etc.)

The behavior modules (e.g., `manipulation.py`, `movement.py`, `locks.py`) only define vocabulary, not handlers.

This dispersion of game knowledge is a maintenance burden and source of bugs when changes are made to one file but not the others.

## Goals

1. Move command logic from json_protocol.py to behavior modules
2. Allow game developers to override or extend core behaviors without modifying engine code
3. Make json_protocol.py pure infrastructure with no game-specific knowledge
4. Support player/NPC unification when NPC AI is implemented

### Why StateAccessor (Sub-goals justifying the complexity)

The StateAccessor pattern adds complexity but provides two key capabilities:

**a) Semantic error context**: When behaviors call state accessors, errors are reported back to the behavior with meaningful context. The behavior can then:
- Report the error to the user with domain-appropriate messaging
- Attempt to fix the problem internally (e.g., retry with different parameters)
- Provide partial success feedback

**b) Incremental operation with feedback**: StateAccessor lets behaviors carry out multi-step actions, getting feedback at each step. This enables:
- Rich progress reporting for extended procedures
- Dynamic decision-making based on intermediate results

**c) Automatic behavior invocation**: StateAccessor ties state updates to behavior events, ensuring entity behaviors are always invoked correctly without handlers needing to remember to call them.

## Use Cases

### Basic Extensibility
- Game developer wants to add weight limits to "take" command
- Game developer wants custom movement rules (e.g., stealth mode)
- Game developer wants to add new container types with special rules
- Game developer wants NPCs that can take/drop/move using same logic as player

### Error Reporting with Context

**Locked container with hints**:

Entity behaviors can return either a simple string or a dict with structured information. This lets the command handler provide context-aware responses:

```python
# Entity behavior (on_open for a lockable container)
def on_open_locked(entity, state, context):
    if entity.properties.get("container", {}).get("locked"):
        return EventResult(
            allow=False,
            message={
                "text": "It's locked.",
                "reason": "locked",
                "lock_id": entity.properties.get("container", {}).get("lock_id")
            }
        )
    return EventResult(allow=True)

# Command handler
def handle_open(accessor, action):
    target_name = action.get("object")
    container = find_accessible_item(accessor, target_name)
    if not container:
        return (False, "You don't see that here.")

    result = accessor.update(
        entity=container,
        changes={"properties.container.open": True},
        event="on_open"
    )

    if not result.success:
        msg = result.message
        if isinstance(msg, dict):
            if msg.get("reason") == "locked":
                lock = accessor.get_lock(msg.get("lock_id"))
                key_hint = lock.properties.get("hint", "a key")
                return (False, f"The {container.name} is locked. Perhaps {key_hint} would help.")
            return (False, msg.get("text", f"You can't open the {container.name}."))
        return (False, msg or f"You can't open the {container.name}.")

    return (True, result.message or f"You open the {container.name}.")
```

Most entity behaviors just return a string message. Use structured messages when the command handler needs additional context to provide a better player experience.

See `weight_example.md` for an example of extending `handle_take` with weight limits.

### Advanced: Multi-step Operations

These examples show more complex patterns. They're not required for basic refactoring but demonstrate the system's capabilities.

**Alchemical brewing** (multi-ingredient consumption):
```python
def handle_brew(accessor, action):
    recipe_name = action.get("object")
    recipe = find_accessible_item(accessor, recipe_name)
    actor = accessor.get_actor()
    messages = []

    for ingredient_id in recipe.properties.get("ingredients", []):
        if ingredient_id not in actor.inventory:
            ingredient = accessor.get_item(ingredient_id)
            messages.append(f"Missing ingredient: {ingredient.name}")
            continue

        ingredient = accessor.get_item(ingredient_id)
        accessor.update(
            entity=ingredient,
            changes={"location": "consumed"},
            event="on_consume"
        )
        accessor.remove_from_list(actor, "inventory", ingredient_id)
        messages.append(f"Added {ingredient.name} to the cauldron.")

    if any("Missing" in m for m in messages):
        return (False, "\n".join(messages))

    result_id = recipe.properties.get("creates")
    accessor.append_to_list(actor, "inventory", result_id)
    result_item = accessor.get_item(result_id)
    messages.append(f"Success! You created a {result_item.name}.")

    return (True, "\n".join(messages))
```

## StateAccessor

The StateAccessor provides generic state operations with automatic behavior invocation. A new accessor is created for each command with the acting entity baked in.

### Design Principles

1. **Generic API**: StateAccessor has no game-specific knowledge
2. **Actor-scoped**: Each accessor knows its actor; `get_actor()` and `get_current_location()` work without arguments
3. **Handlers specify events**: The handler tells StateAccessor which behavior event to invoke
4. **Atomic updates**: Behavior is checked before changes are applied
5. **Direct entity access**: Behaviors get entity objects directly, use existing dataclass properties
6. **Simple returns**: Handlers return `(success: bool, message: str)` tuples

### Core API

```python
@dataclass
class UpdateResult:
    """Result from a state update operation."""
    success: bool = True
    message: Any = None  # String or dict with structured info from entity behavior

@dataclass
class StateAccessor:
    """Provides behaviors with state query and modification capabilities."""

    game_state: GameState
    behavior_manager: BehaviorManager
    actor_id: str = "player"  # The entity performing the action

    # Entity retrieval - returns dataclass objects directly

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get item by ID."""
        pass

    def get_actor(self, actor_id: str = None) -> Optional[Union[PlayerState, NPC]]:
        """Get actor by ID. If no ID given, returns the current actor."""
        if actor_id is None:
            actor_id = self.actor_id
        if actor_id == "player":
            return self.game_state.player
        return self.game_state.get_npc(actor_id)

    def get_location(self, location_id: str) -> Optional[Location]:
        """Get location by ID."""
        pass

    def get_door(self, door_id: str) -> Optional[Door]:
        """Get door by ID."""
        pass

    def get_lock(self, lock_id: str) -> Optional[Lock]:
        """Get lock by ID."""
        pass

    def get_current_location(self) -> Location:
        """Get the current actor's location."""
        actor = self.get_actor()
        return self.game_state.get_location(actor.location)

    def get_items_in_location(self, location_id: str) -> List[Item]:
        """Get all items directly in a location (or container)."""
        pass

    def get_npcs_in_location(self, location_id: str) -> List[NPC]:
        """Get all NPCs in a location."""
        pass

    # State modification with behavior invocation

    def update(self, entity, changes: Dict[str, Any],
               event: str = None) -> UpdateResult:
        """
        Invoke behavior event (if any) then apply changes to entity.

        Args:
            entity: The entity object to update
            changes: Dict of property paths to new values
            event: Optional behavior event name (e.g., "on_take")

        Returns:
            UpdateResult with success and message (string or dict)
        """
        # Invoke behavior first to check if action is allowed
        if event and hasattr(entity, 'behaviors'):
            context = {"actor_id": self.actor_id, "changes": changes}
            behavior_result = self.behavior_manager.invoke_behavior(
                entity, event, self.game_state, context
            )
            if behavior_result:
                if not behavior_result.allow:
                    return UpdateResult(
                        success=False,
                        message=behavior_result.message
                    )
                # Behavior allowed; apply changes and return behavior's message
                for path, value in changes.items():
                    self._set_path(entity, path, value)
                return UpdateResult(
                    success=True,
                    message=behavior_result.message
                )

        # No behavior or no behavior attached; just apply changes
        for path, value in changes.items():
            self._set_path(entity, path, value)
        return UpdateResult(success=True)

    # List operations

    def append_to_list(self, entity, list_path: str, value: Any) -> bool:
        """Append value to a list property."""
        pass

    def remove_from_list(self, entity, list_path: str, value: Any) -> bool:
        """Remove value from a list property."""
        pass

    # Internal helpers

    def _set_path(self, entity, path: str, value: Any) -> None:
        """Set a property value using dot-separated path."""
        parts = path.split(".")
        obj = entity
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict):
                obj = obj.setdefault(part, {})

        final = parts[-1]
        if hasattr(obj, final):
            setattr(obj, final, value)
        elif isinstance(obj, dict):
            obj[final] = value
```

### Handler Registration

Handlers are discovered automatically when behavior modules are loaded. Any function named `handle_<verb>` in a behavior module is registered:

```python
# In behavior_manager.py load_module():
for name in dir(module):
    if name.startswith('handle_'):
        verb = name[7:]  # Remove 'handle_' prefix
        handler = getattr(module, name)
        self._handlers[verb] = handler
```

To override a core behavior, load your module after the core modules. The later registration wins.

## Module Organization

After refactoring, command handlers are organized by domain:

- **manipulation.py** - `handle_take`, `handle_drop`, `handle_put`, `handle_give`
- **movement.py** - `handle_go`
- **perception.py** - `handle_look`, `handle_examine`, `handle_inventory`
- **locks.py** - `handle_unlock`, `handle_lock`
- **interaction.py** - `handle_open`, `handle_close`
- **consumables.py** - `handle_drink`, `handle_eat`
- **combat.py** - `handle_attack`

Additional modules as needed for: `handle_use`, `handle_read`, `handle_climb`, `handle_pull`, `handle_push`

## Shared Utilities

Game-specific helper functions live in `behaviors/core/utils.py`, not in StateAccessor. This keeps StateAccessor generic and allows game authors to override helpers.

```python
# behaviors/core/utils.py
"""Shared utility functions for behavior modules."""

from typing import List, Optional

def find_accessible_item(accessor, name: str, adjectives: List[str] = None):
    """
    Find item by name in current location, on surfaces, or in inventory.
    Matching is case-insensitive.

    Args:
        accessor: StateAccessor instance
        name: Item name to find
        adjectives: Optional adjectives to filter by

    Returns:
        Item or None
    """
    name_lower = name.lower()
    location = accessor.get_current_location()

    # Check items in location
    for item in accessor.get_items_in_location(location.id):
        if item.name.lower() == name_lower:
            if not adjectives or matches_adjectives(item, adjectives):
                return item

    # Check items on surface containers
    for container in accessor.get_items_in_location(location.id):
        if container.properties.get("container", {}).get("is_surface"):
            for item in accessor.get_items_in_location(container.id):
                if item.name.lower() == name_lower:
                    if not adjectives or matches_adjectives(item, adjectives):
                        return item

    # Check inventory
    actor = accessor.get_actor()
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and item.name.lower() == name_lower:
            if not adjectives or matches_adjectives(item, adjectives):
                return item

    return None

def find_item_in_inventory(accessor, name: str):
    """
    Find item by name in the current actor's inventory.
    Matching is case-insensitive.

    Args:
        accessor: StateAccessor instance
        name: Item name to find

    Returns:
        Item or None
    """
    name_lower = name.lower()
    actor = accessor.get_actor()
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and item.name.lower() == name_lower:
            return item
    return None

def find_container_by_name(accessor, name: str, location_id: str):
    """Find a container item by name in the specified location. Case-insensitive."""
    name_lower = name.lower()
    for item in accessor.get_items_in_location(location_id):
        if item.name.lower() == name_lower and item.properties.get("container"):
            return item
    return None

def get_doors_in_location(accessor, location_id: str = None):
    """Get all doors accessible from a location."""
    if location_id is None:
        location_id = accessor.get_current_location().id

    location = accessor.get_location(location_id)
    doors = []
    for direction, exit_desc in location.exits.items():
        if exit_desc.door_id:
            door = accessor.get_door(exit_desc.door_id)
            if door:
                doors.append(door)
    return doors

def actor_has_key_for_door(accessor, actor_id: str, door) -> bool:
    """Check if actor has a key that fits the door's lock."""
    lock_id = door.properties.get("lock_id")
    if not lock_id:
        return False

    lock = accessor.get_lock(lock_id)
    if not lock:
        return False

    actor = accessor.get_actor(actor_id)
    opens_with = lock.properties.get("opens_with", [])
    return any(key_id in actor.inventory for key_id in opens_with)

def matches_adjectives(item, adjectives: List[str]) -> bool:
    """Check if item matches all given adjectives. Case-insensitive."""
    item_adjs = [adj.lower() for adj in item.properties.get("adjectives", [])]
    return all(adj.lower() in item_adjs for adj in adjectives)
```

Behavior modules import these helpers:

```python
# In manipulation.py
from behaviors.core.utils import find_accessible_item, find_container_by_name

def handle_take(accessor, action):
    item = find_accessible_item(accessor, action.get("object"))
    # ...
```

## json_protocol.py After Refactoring

The protocol becomes pure infrastructure with no game-specific knowledge:

```python
class JSONProtocolHandler:
    def __init__(self, state, behavior_manager):
        self.state = state
        self.behavior_manager = behavior_manager

    def handle_message(self, message: Dict) -> Dict:
        """Route message to appropriate handler."""
        if message.get("type") == "command":
            return self._process_command(message)
        elif message.get("type") == "query":
            return self._process_query(message)
        # ...

    def _process_command(self, message: Dict) -> Dict:
        """Process a command by routing to registered handler."""
        action = message.get("action", {})
        verb = action.get("verb")

        if not verb:
            return {"type": "result", "success": False,
                    "error": {"message": "No verb specified"}}

        # Get handler from behavior manager
        handler = self.behavior_manager.get_handler(verb)
        if not handler:
            return {"type": "result", "success": False,
                    "error": {"message": f"Unknown command: {verb}"}}

        # Create accessor for this command with actor baked in
        actor_id = action.get("actor_id", "player")
        accessor = StateAccessor(self.state, self.behavior_manager, actor_id)

        # Call handler - returns (success, message) tuple
        success, result_message = handler(accessor, action)

        if not success:
            return {
                "type": "result",
                "success": False,
                "action": verb,
                "error": {"message": result_message}
            }

        return {
            "type": "result",
            "success": True,
            "action": verb,
            "message": result_message
        }
```

## Example: Refactored manipulation.py

```python
"""Manipulation behaviors - take, drop, put, give.

Vocabulary and handlers for item manipulation.
"""

from behaviors.core.utils import (
    find_accessible_item,
    find_item_in_inventory,
    find_container_by_name
)

# Vocabulary
vocabulary = {
    "verbs": [
        {
            "word": "take",
            "synonyms": ["get", "grab", "pick"],
            "object_required": True
        },
        {
            "word": "drop",
            "synonyms": ["release"],
            "object_required": True
        },
        {
            "word": "put",
            "synonyms": ["place"],
            "object_required": True
        },
        {
            "word": "give",
            "synonyms": ["hand", "offer"],
            "object_required": True
        }
    ]
}

# Command handlers

def handle_take(accessor, action):
    """Handle take command."""
    obj_name = action.get("object")

    if not obj_name:
        return (False, "Take what?")

    # Find item
    adjectives = action.get("adjectives", [])
    item = find_accessible_item(accessor, obj_name, adjectives)

    if not item:
        return (False, "You don't see that here.")

    if not item.portable:
        return (False, "You can't take that.")

    # Get actor
    actor = accessor.get_actor()

    # Update item location and invoke on_take behavior
    result = accessor.update(
        entity=item,
        changes={"location": accessor.actor_id},
        event="on_take"
    )

    if not result.success:
        return (False, result.message or "You can't take that.")

    # Add to inventory
    accessor.append_to_list(actor, "inventory", item.id)

    return (True, result.message or f"You take the {item.name}.")

def handle_drop(accessor, action):
    """Handle drop command."""
    obj_name = action.get("object")

    if not obj_name:
        return (False, "Drop what?")

    item = find_item_in_inventory(accessor, obj_name)
    if not item:
        return (False, "You're not carrying that.")

    actor = accessor.get_actor()

    # Update item location and invoke on_drop behavior
    location = accessor.get_current_location()
    result = accessor.update(
        entity=item,
        changes={"location": location.id},
        event="on_drop"
    )

    if not result.success:
        return (False, result.message or "You can't drop that.")

    # Remove from inventory
    accessor.remove_from_list(actor, "inventory", item.id)

    return (True, result.message or f"You drop the {item.name}.")

def handle_put(accessor, action):
    """Handle put command."""
    obj_name = action.get("object")
    container_name = action.get("indirect_object")

    if not obj_name:
        return (False, "Put what?")

    if not container_name:
        return (False, "Put it where?")

    item = find_item_in_inventory(accessor, obj_name)
    if not item:
        return (False, "You're not carrying that.")

    actor = accessor.get_actor()

    # Find container
    location = accessor.get_current_location()
    container = find_container_by_name(accessor, container_name, location.id)

    if not container:
        return (False, f"You don't see any {container_name} here.")

    # Check if container is accessible
    container_props = container.properties.get("container", {})
    if not container_props.get("is_surface", False) and not container_props.get("open", False):
        return (False, f"The {container_name} is closed.")

    # Update item location and invoke on_drop behavior (putting is like dropping)
    result = accessor.update(
        entity=item,
        changes={"location": container.id},
        event="on_drop"
    )

    if not result.success:
        return (False, result.message or "You can't put that there.")

    # Remove from inventory
    accessor.remove_from_list(actor, "inventory", item.id)

    preposition = "on" if container_props.get("is_surface", False) else "in"
    return (True, result.message or f"You put the {item.name} {preposition} the {container_name}.")

def handle_give(accessor, action):
    """Handle give command."""
    obj_name = action.get("object")
    recipient_name = action.get("indirect_object")

    if not obj_name:
        return (False, "Give what?")

    if not recipient_name:
        return (False, "Give it to whom?")

    item = find_item_in_inventory(accessor, obj_name)
    if not item:
        return (False, "You're not carrying that.")

    # Find recipient NPC in current location
    location = accessor.get_current_location()
    recipient = None
    for npc in accessor.get_npcs_in_location(location.id):
        if npc.name.lower() == recipient_name.lower():
            recipient = npc
            break

    if not recipient:
        return (False, f"You don't see {recipient_name} here.")

    # Invoke on_give behavior on recipient to check if they accept
    result = accessor.update(
        entity=recipient,
        changes={},  # No direct changes to recipient
        event="on_give"
    )

    if not result.success:
        return (False, result.message or f"{recipient.name} doesn't want that.")

    # Transfer item location
    accessor.update(
        entity=item,
        changes={"location": recipient.id}
    )

    # Update inventories
    actor = accessor.get_actor()
    accessor.remove_from_list(actor, "inventory", item.id)
    accessor.append_to_list(recipient, "inventory", item.id)

    return (True, result.message or f"You give the {item.name} to {recipient.name}.")
```

## Migration Path

### Phase 2a: Implement StateAccessor and Utils

1. Create `src/state_accessor.py` with core API (entity retrieval, update, list operations)
2. Create `behaviors/core/utils.py` with shared helpers
3. Move helper methods from json_protocol.py to utils.py
4. Move helper functions from game_engine.py to utils.py
5. Implement `update()` with behavior invocation
6. Write tests for StateAccessor and utils

### Phase 2b: Move Command Handlers

1. Move `_cmd_take` to `manipulation.py` as `handle_take`
2. Move `_cmd_drop` to `manipulation.py` as `handle_drop`
3. Move `_cmd_put` to `manipulation.py` as `handle_put`
4. Add `handle_give` to `manipulation.py`
5. Move `_cmd_go` to `movement.py` as `handle_go`
6. Move `_cmd_look`, `_cmd_examine`, `_cmd_inventory` to `perception.py`
7. Move `_cmd_open`, `_cmd_close` to `interaction.py`
8. Move `_cmd_unlock`, `_cmd_lock` to `locks.py`
9. Move remaining commands to appropriate modules

### Phase 2c: Simplify Infrastructure

1. Update json_protocol.py to route all commands through behavior_manager
2. Remove all `_cmd_*` methods from json_protocol.py
3. Remove game-specific helper methods from json_protocol.py
4. Remove parallel implementations from game_engine.py
5. game_engine.py keeps only: main loop, save/load, and calls to behavior handlers
6. json_protocol.py becomes pure routing infrastructure

### Modules with Game Knowledge: What to Keep

Some modules will retain game entity knowledge because they define the core data model:

**state_manager.py - Keep as infrastructure**
- Entity dataclasses (Item, Location, Door, Lock, NPC, PlayerState) define the data model
- Serialization/parsing is necessary infrastructure
- GameState methods like `get_item()`, `get_location()` are used by StateAccessor
- The convenience methods `move_item()`, `set_player_location()` should eventually be replaced by StateAccessor calls in behavior handlers

**validators.py - Keep as infrastructure**
- Structural validation ensures data integrity on load/save
- Entity type knowledge is acceptable here as it validates the data model
- Does not contain game behavior logic, only structural rules
- Consider: could validators be made pluggable if game authors add new entity types?

**vocabulary_generator.py - Keep but simplify**
- Currently extracts nouns from items/NPCs by knowing their structure
- This is acceptable infrastructure - it builds the parser vocabulary
- Alternative: behavior modules could register their own nouns (more complex)

**Summary**: These modules define what entities exist and how they're structured, not what happens when you interact with them. Game behavior belongs in behavior modules; game data model stays in infrastructure.

### Phase 2d: NPC AI (Future)

1. Implement NPC decision-making
2. NPCs call same handlers with their actor_id
3. Add perception system for NPC awareness

## Testing Strategy

With StateAccessor, handlers are easily testable:

```python
def test_handle_take_success():
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager, "player")

    action = {"object": "sword"}
    success, message = handle_take(accessor, action)

    assert success
    assert "sword" in message
    assert state.get_item("item_sword").location == "player"
    assert "item_sword" in state.player.inventory

def test_handle_take_not_portable():
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager, "player")

    action = {"object": "table"}
    success, message = handle_take(accessor, action)

    assert not success
    assert "can't take" in message.lower()

def test_handle_take_with_behavior():
    state = create_test_state()
    behavior_manager = BehaviorManager()
    # Load light_sources behavior module
    behavior_manager.load_module("behaviors.core.light_sources")
    accessor = StateAccessor(state, behavior_manager, "player")

    action = {"object": "lantern"}
    success, message = handle_take(accessor, action)

    assert success
    assert "runes flare to life" in message  # From on_take behavior
    assert state.get_item("item_lantern").states.get("lit") == True
```

## Benefits

1. **Extensibility**: Override `handle_take` without modifying engine
2. **Organization**: Related code in one module (vocab + handler)
3. **Testability**: Handlers tested with real StateAccessor, no mocks needed
4. **Consistency**: All commands follow same pattern
5. **Clean separation**: json_protocol.py has no game knowledge
6. **Future-proofing**: Ready for NPC AI with actor_id parameter
7. **Simple error flow**: Handlers return (success, message) tuples, no separate error tracking

## Out of Scope

**Meta commands** (quit, save, load, help) remain in game_engine.py as they're not game behaviors.

**Query handling** in json_protocol.py is not addressed by this refactoring. Queries return state information without modifying it, so they don't need the StateAccessor pattern.

## Deferred

- Undo/rollback support in StateAccessor
- Transaction batching for complex operations
- NPC AI using behavior handlers
- Behavior override/priority system
