# Behavior Refactoring Implementation Guide

This document provides implementation details, code examples, and migration steps for the behavior system refactoring described in [behavior_refactoring.md](behavior_refactoring.md).

**See also:**
- [behavior_refactoring.md](behavior_refactoring.md) - Design and architecture
- [behavior_refactoring_testing.md](behavior_refactoring_testing.md) - Testing strategy

## Module Organization

After refactoring, command handlers and utilities are organized by domain:

### Command Handler Modules

- **manipulation.py** - `handle_take`, `handle_drop`, `handle_put`, `handle_give`
- **movement.py** - `handle_go`
- **perception.py** - `handle_look`, `handle_examine`, `handle_inventory`
- **locks.py** - `handle_unlock`, `handle_lock`

### Utility Modules

- **utils.py** - Helper functions used by command handlers and query handlers:
  - **Search/lookup functions** (find specific things by name for commands):
    - `find_accessible_item()` - Find item by name in current location
    - `find_item_in_inventory()` - Find item by name in actor's inventory
    - `find_container_by_name()` - Find container in location
  - **Visibility/enumeration functions** (list all visible things for queries/display):
    - `get_visible_items_in_location()` - Items visible to actor in location
    - `get_visible_actors_in_location()` - Actors visible to actor in location (excludes viewing actor)
    - `get_doors_in_location()` - Doors accessible from location
  - **Other utilities:**
    - `actor_has_key_for_door()` - Check if actor has key for door
- **interaction.py** - `handle_open`, `handle_close`
- **consumables.py** - `handle_drink`, `handle_eat`
- **combat.py** - `handle_attack`

Additional modules as needed for: `handle_use`, `handle_read`, `handle_climb`, `handle_pull`, `handle_push`

## Shared Utilities

Game-specific helper functions live in `utilities/utils.py`, not in StateAccessor. This keeps StateAccessor generic and allows game authors to override helpers.

**Directory Structure:** Utilities are in a separate top-level `utilities/` directory (parallel to `behaviors/`) because they are **not behavior modules** - they don't define handlers, entity behaviors, or vocabularies.

```
my_game/
  behaviors/           # Behavior modules (define handlers, entity behaviors, vocabularies)
    core/
      manipulation.py
      movement.py
  utilities/           # Utility modules (helper functions only, NO handlers/behaviors/vocabularies)
    utils.py           # Search/lookup + visibility/enumeration functions
  src/
    state_accessor.py
    behavior_manager.py
```

**Module Import Guidelines:**

- **Behavior modules MAY import from `utilities/utils.py`** - This is the expected pattern for shared functionality
- **Behavior modules SHOULD NOT import from other behavior modules** - Each behavior module should be self-contained
- **Inter-module dependencies are not addressed** - If needed in future, would require explicit design for dependency ordering and circular dependency prevention
- **`utilities/utils.py` is NOT a behavior module** - It provides helper functions but does NOT define:
  - Command handlers (`handle_*`)
  - Entity behaviors (`on_*`)
  - Vocabularies
  - It's a pure utility module imported by both behavior modules and query handlers

**Example:**
```python
# behaviors/core/manipulation.py
from utilities.utils import find_accessible_item  # ✓ Allowed - importing shared utilities

def handle_take(accessor, action):
    item = find_accessible_item(accessor, action.get("object"), action.get("actor_id"))
    # ...
```

**utils.py Structure:**

```python
# utilities/utils.py
"""Shared utility functions for behavior modules."""

from typing import List, Optional

def find_accessible_item(accessor: StateAccessor, name: str, actor_id: str) -> Optional[Item]:
    """
    Find item by name in current location, on surfaces, or in inventory.
    Matching is case-insensitive.

    Args:
        accessor: StateAccessor instance
        name: Item name to find
        actor_id: ID of the actor (e.g., "player" or NPC id)
                  IMPORTANT: Do not hardcode "player" - use the actor_id variable from action

    Returns:
        Item or None
    """
    name_lower = name.lower()
    location = accessor.get_current_location(actor_id)

    # Check items in location
    for item in accessor.get_items_in_location(location.id):
        if item.name.lower() == name_lower:
            return item

    # Check items on surface containers
    for container in accessor.get_items_in_location(location.id):
        if container.properties.get("container", {}).get("is_surface"):
            for item in accessor.get_items_in_location(container.id):
                if item.name.lower() == name_lower:
                    return item

    # Check inventory
    actor = accessor.get_actor(actor_id)
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and item.name.lower() == name_lower:
            return item

    return None

def find_item_in_inventory(accessor: StateAccessor, name: str, actor_id: str) -> Optional[Item]:
    """
    Find item by name in the specified actor's inventory.
    Matching is case-insensitive.

    Args:
        accessor: StateAccessor instance
        name: Item name to find
        actor_id: ID of the actor (e.g., "player" or NPC id)
                  IMPORTANT: Do not hardcode "player" - use the actor_id variable from action

    Returns:
        Item or None
    """
    name_lower = name.lower()
    actor = accessor.get_actor(actor_id)
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
```

Behavior modules import these helpers and result types:

```python
# In behaviors/core/manipulation.py - Command handlers
from src.state_accessor import HandlerResult, StateAccessor
from behaviors.core.utils import find_accessible_item, find_container_by_name
from typing import Dict

def handle_take(accessor: StateAccessor, action: Dict) -> HandlerResult:
    actor_id = action.get("actor_id", "player")  # Extract actor_id from action
    item = find_accessible_item(accessor, action.get("object"), actor_id)  # Pass to utilities

    if not item:
        return HandlerResult(success=False, message="You don't see that here.")
    # ...
    return HandlerResult(success=True, message=f"You take the {item.name}.")
```

```python
# In behaviors/game_specific/lockable_containers.py - Entity behaviors
from src.state_accessor import EventResult, StateAccessor

def on_open(entity, accessor: StateAccessor, context: dict) -> EventResult:
    """Check if container can be opened (lock check)."""
    lock_id = entity.properties.get("lock_id")
    if not lock_id:
        return EventResult(allow=True)

    lock = accessor.get_lock(lock_id)
    if lock and lock.properties.get("locked", False):
        hint = lock.properties.get("hint", "It's locked.")
        return EventResult(allow=False, message=hint)

    return EventResult(allow=True)
```

**Import Reference:**
- **Command handlers** import: `HandlerResult`, `StateAccessor`
- **Entity behaviors** import: `EventResult`, `StateAccessor`
- **Internal code** (if checking results) may import: `UpdateResult`
- All three result types live in: `src.state_accessor`

**Important:** All handlers must:
- Import `HandlerResult` from `src.state_accessor`
- Extract `actor_id` from the action at the top
- Pass `actor_id` to all utility functions
- Never hardcode `"player"` when calling utilities - use the `actor_id` variable

## llm_protocol.py After Refactoring

The file `json_protocol.py` is renamed to `llm_protocol.py` and reduced to query handling and JSON serialization. Command handling moves to behavior modules.

```python
class LLMProtocolHandler:
    """Handles queries and JSON serialization for LLM interface."""

    def __init__(self, state, behavior_manager):
        self.state = state
        self.behavior_manager = behavior_manager
        self.state_corrupted = False  # Flag for inconsistent state detection

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

        # Check if state is corrupted
        if self.state_corrupted:
            # Only allow meta-commands (save, quit, etc.)
            if verb not in ["save", "quit", "help"]:
                return {
                    "type": "result",
                    "success": False,
                    "action": verb,
                    "error": {"message": "Game state is corrupted. Please save and quit, then report this error to the developer."}
                }

        # Ensure action has actor_id
        if "actor_id" not in action:
            action["actor_id"] = "player"

        # Create accessor (can be reused across commands)
        accessor = StateAccessor(self.state, self.behavior_manager)

        # Invoke handler - BehaviorManager manages position list lifecycle
        result = self.behavior_manager.invoke_handler(verb, accessor, action)

        if not result.success:
            # Check for inconsistent state error
            if result.message and result.message.startswith("INCONSISTENT STATE:"):
                self._handle_inconsistent_state(verb, action, result.message)
                return {
                    "type": "result",
                    "success": False,
                    "action": verb,
                    "error": {
                        "message": "An error occurred. The game cannot continue safely. Please save and quit, then report this to the developer.",
                        "fatal": True
                    }
                }

            return {
                "type": "result",
                "success": False,
                "action": verb,
                "error": {"message": result.message}
            }

        return {
            "type": "result",
            "success": True,
            "action": verb,
            "message": result.message
        }

    def _handle_inconsistent_state(self, verb: str, action: Dict, error_message: str):
        """
        Handle detection of inconsistent state.

        Logs full error details for developer and sets state_corrupted flag.

        Args:
            verb: The command that caused the error
            action: The action dict
            error_message: Full error message from handler (includes "INCONSISTENT STATE:" prefix)
        """
        import sys
        import datetime

        # Set flag to prevent further state corruption
        self.state_corrupted = True

        # Log full error details for developer
        timestamp = datetime.datetime.now().isoformat()
        error_details = f"""
FATAL ERROR: Inconsistent State Detected
Timestamp: {timestamp}
Command: {verb}
Actor: {action.get('actor_id', 'unknown')}
Action: {action}
Error: {error_message}

The game state is now corrupted. No further commands will be processed except save/quit.
"""
        # Write to stderr for developer visibility
        print(error_details, file=sys.stderr)

        # Optionally write to log file
        # with open('game_errors.log', 'a') as f:
        #     f.write(error_details)

    # Query handlers (_query_location, _query_inventory, etc.) remain here
    # JSON serialization helpers (_entity_to_dict, _door_to_dict, etc.) remain here
```

The module retains:
- Command routing (thin layer that delegates to behavior handlers via BehaviorManager)
- Query routing (thin layer that calls visibility utilities from behavior modules)
- JSON serialization helpers for converting entities to dicts (`_entity_to_dict`, `_door_to_dict`, etc.)

All game-specific logic has moved to behavior modules. llm_protocol.py is now pure infrastructure.

All `_cmd_*` methods are removed - command logic lives in behavior modules.

### Design Rationale: Position List Lifecycle Management

**Why BehaviorManager.invoke_handler() owns the position list lifecycle:**

The position list tracks delegation state as handlers call `invoke_previous_handler()`. This state must be properly initialized and cleaned up, even if handlers raise exceptions.

**Previous approach (shared management):**
- llm_protocol: appends 0, pops in finally
- BehaviorManager: appends N+1, pops in finally
- Issues: Shared mutable state across two classes, multiple cleanup points, potential for incomplete cleanup

**Current approach (lifecycle ownership with controlled modification):**
- BehaviorManager.invoke_handler() owns the lifecycle:
  - Initializes list to [0] before calling first handler
  - Always cleans up (sets to []) in finally block, even if handler raises exception
- BehaviorManager.invoke_previous_handler() modifies state during lifecycle:
  - Appends next position when delegating deeper
  - Pops position when returning (in finally block)
- invoke_previous_handler() raises RuntimeError if list not initialized (detects misuse)

**Benefits:**
1. **Clear lifecycle ownership**: invoke_handler() controls creation/destruction
2. **Controlled state modification**: invoke_previous_handler() can only grow/shrink, not reinitialize
3. **Exception safety**: Both methods use try/finally for cleanup
4. **Better error detection**: RuntimeError immediately catches if handlers are called incorrectly
5. **Easier to test**: Position list lifecycle tests are isolated to BehaviorManager
6. **Reduced coupling**: llm_protocol doesn't touch BehaviorManager internals

**Testing implications:**
- Tests verify invoke_handler() properly initializes and cleans up
- Tests verify cleanup happens even when handler raises exception
- Tests verify RuntimeError when invoke_previous_handler() called without initialization

## Example: Refactored manipulation.py

```python
"""Manipulation behaviors - take, drop, put, give.

Vocabulary and handlers for item manipulation.
"""

from src.state_accessor import HandlerResult, StateAccessor
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
            "object_required": True,
            "event": "on_take"  # Event name for entity behaviors
        },
        {
            "word": "drop",
            "synonyms": ["release"],
            "object_required": True,
            "event": "on_drop"
        },
        {
            "word": "put",
            "synonyms": ["place"],
            "object_required": True,
            "event": "on_put"
        },
        {
            "word": "give",
            "synonyms": ["hand", "offer"],
            "object_required": True,
            "event": "on_give"
        }
    ]
}

# Command handlers

def handle_take(accessor, action):
    """Handle take command."""
    actor_id = action.get("actor_id", "player")  # This actor_id is passed to all utilities
    obj_name = action.get("object")

    if not obj_name:
        return HandlerResult(success=False, message="Take what?")

    # Find item - pass actor_id to find items accessible to this specific actor
    item = find_accessible_item(accessor, obj_name, actor_id)

    if not item:
        return HandlerResult(success=False, message="You don't see that here.")

    if not item.portable:
        return HandlerResult(success=False, message="You can't take that.")

    # Get actor
    actor = accessor.get_actor(actor_id)

    # Update item location (with behavior check)
    result = accessor.update(
        entity=item,
        changes={"location": actor_id},
        verb="take",
        actor_id=actor_id
    )

    if not result.success:
        return HandlerResult(success=False, message=result.message or "You can't take that.")

    # Update actor inventory
    inventory_result = accessor.update(
        entity=actor,
        changes={"+inventory": item.id}
    )

    if not inventory_result.success:
        # State is now inconsistent - report clearly
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Item location changed but inventory update failed: {inventory_result.message}"
        )

    return HandlerResult(success=True, message=result.message or f"You take the {item.name}.")

def handle_drop(accessor, action):
    """Handle drop command."""
    actor_id = action.get("actor_id", "player")  # This actor_id is passed to all utilities
    obj_name = action.get("object")

    if not obj_name:
        return HandlerResult(success=False, message="Drop what?")

    # Find item in this actor's inventory
    item = find_item_in_inventory(accessor, obj_name, actor_id)
    if not item:
        return HandlerResult(success=False, message="You're not carrying that.")

    actor = accessor.get_actor(actor_id)
    location = accessor.get_current_location(actor_id)

    # Update item location (with behavior check)
    result = accessor.update(
        entity=item,
        changes={"location": location.id},
        verb="drop",
        actor_id=actor_id
    )

    if not result.success:
        return HandlerResult(success=False, message=result.message or "You can't drop that.")

    # Update actor inventory
    inventory_result = accessor.update(
        entity=actor,
        changes={"-inventory": item.id}
    )

    if not inventory_result.success:
        # State is now inconsistent - report clearly
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Item location changed but inventory update failed: {inventory_result.message}"
        )

    return HandlerResult(success=True, message=result.message or f"You drop the {item.name}.")

def handle_put(accessor, action):
    """Handle put command."""
    actor_id = action.get("actor_id", "player")  # This actor_id is passed to all utilities
    obj_name = action.get("object")
    container_name = action.get("indirect_object")

    if not obj_name:
        return HandlerResult(success=False, message="Put what?")

    if not container_name:
        return HandlerResult(success=False, message="Put it where?")

    # Find item in this actor's inventory
    item = find_item_in_inventory(accessor, obj_name, actor_id)
    if not item:
        return HandlerResult(success=False, message="You're not carrying that.")

    actor = accessor.get_actor(actor_id)

    # Find container in actor's current location
    location = accessor.get_current_location(actor_id)
    container = find_container_by_name(accessor, container_name, location.id)

    if not container:
        return HandlerResult(success=False, message=f"You don't see any {container_name} here.")

    # Check if container is accessible
    container_props = container.properties.get("container", {})
    if not container_props.get("is_surface", False) and not container_props.get("open", False):
        return HandlerResult(success=False, message=f"The {container_name} is closed.")

    # Update item location (with behavior check)
    result = accessor.update(
        entity=item,
        changes={"location": container.id},
        verb="put",
        actor_id=actor_id
    )

    if not result.success:
        return HandlerResult(success=False, message=result.message or "You can't put that there.")

    # Update actor inventory
    inventory_result = accessor.update(
        entity=actor,
        changes={"-inventory": item.id}
    )

    if not inventory_result.success:
        # State is now inconsistent - report clearly
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Item location changed but inventory update failed: {inventory_result.message}"
        )

    preposition = "on" if container_props.get("is_surface", False) else "in"
    return HandlerResult(success=True, message=result.message or f"You put the {item.name} {preposition} the {container_name}.")

def handle_give(accessor, action):
    """Handle give command."""
    actor_id = action.get("actor_id", "player")  # This actor_id is passed to all utilities
    obj_name = action.get("object")
    recipient_name = action.get("indirect_object")

    if not obj_name:
        return HandlerResult(success=False, message="Give what?")

    if not recipient_name:
        return HandlerResult(success=False, message="Give it to whom?")

    # Find item in this actor's inventory
    item = find_item_in_inventory(accessor, obj_name, actor_id)
    if not item:
        return HandlerResult(success=False, message="You're not carrying that.")

    # Find recipient actor in actor's current location
    location = accessor.get_current_location(actor_id)
    recipient = None
    for other_actor in accessor.get_actors_in_location(location.id):
        if other_actor.id != actor_id and other_actor.name.lower() == recipient_name.lower():
            recipient = other_actor
            break

    if not recipient:
        return HandlerResult(success=False, message=f"You don't see {recipient_name} here.")

    actor = accessor.get_actor(actor_id)

    # Update item location (with behavior check)
    result = accessor.update(
        entity=item,
        changes={"location": recipient.id},
        verb="give",
        actor_id=actor_id
    )

    if not result.success:
        return HandlerResult(success=False, message=result.message or f"{recipient.name} doesn't want that.")

    # Update actor inventory
    inventory_result = accessor.update(
        entity=actor,
        changes={"-inventory": item.id}
    )

    if not inventory_result.success:
        # State is now inconsistent - report clearly
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Item location changed but actor inventory update failed: {inventory_result.message}"
        )

    # Update recipient inventory
    recipient_result = accessor.update(
        entity=recipient,
        changes={"+inventory": item.id}
    )

    if not recipient_result.success:
        # State is now inconsistent - report clearly
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Item location changed but recipient inventory update failed: {recipient_result.message}"
        )

    return HandlerResult(success=True, message=result.message or f"You give the {item.name} to {recipient.name}.")
```

## Migration Path

### Handler Migration Map

This refactoring moves all command handlers from `game_engine.py` and `json_protocol.py` into behavior modules:

**From game_engine.py → behavior modules:**
- `take_item()` → `behaviors/core/manipulation.py::handle_take()`
- `drop_item()` → `behaviors/core/manipulation.py::handle_drop()`
- `put_item()` → `behaviors/core/manipulation.py::handle_put()`
- `move_player()` → `behaviors/core/movement.py::handle_go()`
- `describe_location()` → `behaviors/core/perception.py::handle_look()`
- `show_inventory()` → `behaviors/core/perception.py::handle_inventory()`
- `examine_item()` → `behaviors/core/perception.py::handle_examine()`
- `open_item()` → `behaviors/core/interaction.py::handle_open()`
- `close_door()` → `behaviors/core/interaction.py::handle_close()`
- `drink_item()` → `behaviors/core/consumables.py::handle_drink()`

**From json_protocol.py → behavior modules:**
- `_cmd_take()` → removed (replaced by `behaviors/core/manipulation.py::handle_take()`)
- `_cmd_drop()` → removed (replaced by `behaviors/core/manipulation.py::handle_drop()`)
- `_cmd_put()` → removed (replaced by `behaviors/core/manipulation.py::handle_put()`)
- `_cmd_give()` → removed (added as `behaviors/core/manipulation.py::handle_give()`)
- `_cmd_go()` → removed (replaced by `behaviors/core/movement.py::handle_go()`)
- `_cmd_look()` → removed (replaced by `behaviors/core/perception.py::handle_look()`)
- `_cmd_inventory()` → removed (replaced by `behaviors/core/perception.py::handle_inventory()`)
- `_cmd_examine()` → removed (replaced by `behaviors/core/perception.py::handle_examine()`)
- `_cmd_open()` → removed (replaced by `behaviors/core/interaction.py::handle_open()`)
- `_cmd_close()` → removed (replaced by `behaviors/core/interaction.py::handle_close()`)
- `_cmd_unlock()` → removed (replaced by `behaviors/core/locks.py::handle_unlock()`)
- `_cmd_lock()` → removed (replaced by `behaviors/core/locks.py::handle_lock()`)
- `_cmd_drink()` → removed (replaced by `behaviors/core/consumables.py::handle_drink()`)
- `_cmd_eat()` → removed (deferred to future behavior module)
- `_cmd_attack()` → removed (deferred to future `behaviors/core/combat.py::handle_attack()`)
- `_cmd_use()`, `_cmd_read()`, `_cmd_climb()`, `_cmd_pull()`, `_cmd_push()` → removed (deferred to future behavior modules)

**Helper functions → utilities/utils.py:**
- `game_engine.py::get_item_by_name()` → `utilities/utils.py::find_accessible_item()`
- `game_engine.py::player_has_key_for_door()` → `utilities/utils.py::actor_has_key_for_door()`
- `json_protocol.py::_find_accessible_item()` → `utilities/utils.py::find_accessible_item()`
- Container/surface logic from both files → `utilities/utils.py::find_accessible_item()`

### Phase 2a: Implement StateAccessor and Utils

1. Refactor `src/state_manager.py` for unified actor model and universal behaviors support:
   - Replace `GameState.player: PlayerState` and `GameState.npcs: Dict[str, NPC]` with:
     - `GameState.actors: Dict[str, Actor]`
   - Initialize actors dict with player: `self.actors = {"player": Actor(id="player", ...)}`
   - Add NPCs to actors dict: `self.actors[npc.id] = npc`
   - Remove `get_npc()` method (use `actors.get()` directly)
   - **Change `behaviors` field type from `Dict[str, str]` to `List[str]` in ALL entity dataclasses:**
     - `Item`, `Actor`, `Location`, `Door`, `Lock`
     - Phase 1 used `behaviors: Dict[str, str]` mapping event names to module names
     - Phase 2 uses `behaviors: List[str]` listing module names (event names come from vocabulary)
     - This change eliminates redundancy: event→module mapping now lives only in vocabulary
     - Entities without custom behaviors have `behaviors=[]` (no runtime cost)
   - Update serialization to save/load from unified actors dict
   - **Migration required:** Old save files have dict-type behaviors, need conversion to list
   - **Test compatibility:** Ensure old save files migrate correctly (extract unique module names from dict values, convert to list)

2. Create `src/state_accessor.py` with:
   - Core dataclasses: `EventResult`, `UpdateResult`, `HandlerResult`
   - StateAccessor class with entity retrieval methods (`get_item`, `get_actor`, `get_location`, etc.)
   - StateAccessor.get_actor() uses `game_state.actors.get(actor_id)` - no special casing
   - StateAccessor.get_actors_in_location() returns all actors in location (including player)
   - `update()` method with `_set_path()` implementation
   - `invoke_previous_handler()` method

3. Update `src/behavior_manager.py`:
   - Add `self._handler_position_list = []` to `__init__` for tracking handler delegation
   - Add `self._module_sources = {}`, `self._verb_event_sources = {}`, and `self._current_load_source = None` for conflict detection
   - Update `load_module()` signature to accept `source_type` parameter ("regular" or "symlink")
   - Add conflict detection logic that raises ValueError for duplicate handlers and vocabulary mappings within same source type
   - Implement `_validate_vocabulary()` method
   - Implement `get_event_for_verb()` method
   - Implement `invoke_handler()` method that manages position list lifecycle (initialize, invoke, cleanup in finally)
   - Implement `invoke_previous_handler()` with instance variable position list tracking and RuntimeError if not initialized
   - Implement `invoke_behavior()` for entity behavior invocation

4. Create `utilities/utils.py` with **full type hints** - contains both search/lookup and visibility/enumeration functions:
   - **Search/lookup functions:**
     - `find_accessible_item(accessor: StateAccessor, name: str, actor_id: str) -> Optional[Item]`
     - `find_item_in_inventory(accessor: StateAccessor, name: str, actor_id: str) -> Optional[Item]`
     - `find_container_by_name(accessor: StateAccessor, name: str, location_id: str) -> Optional[Item]`
   - **Visibility/enumeration functions:**
     - `get_visible_items_in_location(accessor, location_id, actor_id)` - returns all visible items
     - `get_visible_actors_in_location(accessor, location_id, actor_id)` - returns actors except viewing actor
     - `get_doors_in_location(accessor: StateAccessor, location_id: str = None, actor_id: str = "player") -> List[Door]`
   - **Other utilities:**
     - `actor_has_key_for_door(accessor: StateAccessor, actor_id: str, door: Door) -> bool`
   - **IMPORTANT:** Include docstring warnings about not hardcoding "player"
   - **Note:** Utilities are in separate `utilities/` directory, NOT in `behaviors/`

5. Move existing helper methods from json_protocol.py and game_engine.py to utils.py
   - **Update all signatures** to include `actor_id` parameter
   - Add type hints to all functions
   - Add docstring warnings about actor_id

6. **Write tests first (TDD)** - Write failing tests for all infrastructure:
   - Test GameState.actors unified storage (player and NPCs in same dict)
   - Test StateAccessor.get_actor() with both "player" and NPC actor_ids
   - Test StateAccessor.get_actors_in_location() includes player when present
   - Test StateAccessor entity retrieval with explicit actor_id
   - Test save/load compatibility with old format (player/npcs fields)
   - Test `_set_path()` with all operations (+, -, set):
     - **Simple field access:**
       - Test setting top-level field: "location" on entity
       - Test reading/writing entity dataclass fields
     - **Nested dict access with dots:**
       - Test setting nested property: "properties.health"
       - Test setting deeply nested property: "properties.container.open"
       - Test creating intermediate dicts when they don't exist
       - Test setting on existing nested dict keys
       - Test mixing existing and new keys in nested path
     - **List operations:**
       - Test appending to list: "+inventory"
       - Test removing from list: "-inventory"
       - Test appending to nested list: "+properties.tags"
       - Test removing from nested list: "-properties.tags"
     - **Error cases:**
       - Test path not found (non-existent field)
       - Test appending to non-list field
       - Test removing from non-list field
       - Test removing value not in list
       - Test setting field on invalid object (neither dataclass nor dict)
   - Test `update()` with behavior invocation
   - **Write NPC tests for all utility functions** - verify utilities correctly use actor_id parameter:
     - Test `find_accessible_item()` finds items in NPC's location, not player's location
     - Test `find_item_in_inventory()` finds items in NPC's inventory, not player's inventory
     - Test `actor_has_key_for_door()` checks NPC's inventory, not player's inventory
     - **Note:** These tests do NOT require handlers (handle_take, etc.) to be implemented
     - They test that utilities properly accept and use the actor_id parameter
   - **Test None returns from get_* methods** - verify handlers handle missing entities:
     - Test handler with lock_id pointing to non-existent lock
     - Test handler with item_id in inventory that doesn't exist (simulates corruption)
     - Test handler with invalid actor_id
     - Test utilities receiving None parameters handle gracefully
     - Verify no AttributeError exceptions are raised (must return HandlerResult instead)
   - Test handler position list for chaining
   - **Test conflict detection** - verify ValueError is raised for duplicate handlers
   - **Test vocabulary validation** - verify ValueError is raised for:
     - vocabulary is not a dict
     - vocabulary['verbs'] is not a list
     - verb spec missing 'word' field
     - 'word' is not a string or is empty
     - 'synonyms' is not a list
     - synonym is not a string or is empty
     - 'event' is not a string or is empty
     - 'object_required' is not a bool
   - **Test vocabulary conflict detection** - verify ValueError is raised for:
     - Two regular modules mapping same verb to different events
     - Two regular modules mapping same synonym to different events
     - Verify that same verb mapping to same event is allowed (no error)
     - Verify that regular and symlink modules can map same verb to different events (handler chaining scenario)
   - **Test vocabulary event mapping behavior** - verify graceful handling of valid edge cases:
     - Verb without event mapping is allowed (accessor.update() with no event_name proceeds without behavior invocation)
     - Multiple different verbs mapping to same event is allowed (e.g., "take" and "grab" both → "on_take")
     - get_event_for_verb() returns None for unmapped verb (not an error)
   - **Test position list lifecycle** - verify proper initialization and cleanup:
     - Position list is properly initialized by invoke_handler()
     - Position list is cleaned up after successful handler execution
     - Position list is cleaned up after handler raises exception
     - invoke_previous_handler() raises RuntimeError if position list not initialized
     - Nested delegation (A→B→C) properly manages position list growth/shrinkage
   - **Test inconsistent state handling** - verify proper error handling:
     - Handler returning "INCONSISTENT STATE:" message triggers special handling
     - state_corrupted flag is set after inconsistent state detected
     - Error details are logged to stderr with full context
     - User receives generic error message (not technical details)
     - Subsequent commands (except save/quit/help) are rejected with corruption message
     - Meta-commands (save, quit, help) are still allowed after corruption
   - **Test multiple behaviors per entity** - verify all matching behaviors are invoked:
     - Entity with 2+ behaviors defining same event invokes all behaviors
     - Results are combined with AND logic (all must allow)
     - Messages from all behaviors are concatenated
     - Behaviors are invoked in the order listed in entity.behaviors
     - Any behavior returning allow=False vetoes the action
   - **Test vocabulary generation integration** - verify vocabulary_generator works with behavior system:
     - **Noun extraction:** vocabulary_generator extracts nouns from entity names
       - Test extracting Item names as nouns (e.g., item.name = "sword" → noun "sword")
       - Test extracting Actor names as nouns (e.g., actor.name = "guard" → noun "guard")
       - Test extracting Location names as nouns (e.g., location.name = "room" → noun "room")
     - **Verb registration:** vocabulary_generator combines verbs from behavior modules
       - Test that verbs defined in behavior module vocabularies are registered
       - Test that synonyms are registered (e.g., "get" and "grab" both map to "take")
       - Test that verb-to-event mappings are preserved (e.g., "take" → "on_take")
     - **Parser vocabulary integration:** vocabulary_generator provides complete vocabulary to parser
       - Test that generated vocabulary contains both nouns (from entities) AND verbs (from behaviors)
       - Test that parser receives correct structure (nouns list, verbs list with event mappings)
       - Test that vocabulary updates when new entities are added to game state
       - Test that vocabulary updates when new behavior modules are loaded
     - **Edge cases:**
       - Test handling entities with empty/missing names (should skip or use ID)
       - Test handling duplicate nouns from different entities (e.g., two items both named "key")
       - Test behavior modules with no vocabulary defined (should not error)
   - **Test module loading error handling** - verify load-time errors are caught and reported properly:
     - **Syntax errors:** Test that SyntaxError during import is caught
       - Create temp file with Python syntax error (unclosed parenthesis)
       - Attempt to import with importlib.import_module()
       - Verify SyntaxError is raised with filename and line number
     - **Import errors:** Test that ImportError/ModuleNotFoundError is caught
       - Create module that imports non-existent module
       - Verify ImportError is raised with missing module name
     - **Malformed vocabulary:** Test that vocabulary validation catches errors
       - vocabulary is not a dict (string, list, None, etc.)
       - vocabulary['verbs'] is not a list
       - verb spec missing 'word' field
       - verb spec fields have wrong types
       - All should raise ValueError with descriptive message
     - **Handler signature errors:** Test that wrong signatures are NOT caught at load time
       - Create handler with wrong signature (missing parameters)
       - Load module - should succeed (no signature checking at load)
       - Invoke handler - should raise TypeError at runtime
       - Verify TypeError message mentions missing parameters
     - **Continue-on-error behavior:** Test that module loading continues after errors
       - Create multiple modules, some with errors, some valid
       - Load all modules - verify valid modules load successfully
       - Verify errors are logged but don't abort entire load process
     - **Note:** These tests validate the error detection, not the stderr logging (which is tested separately)
   - **All tests written in step 6 will fail initially** - this is expected in TDD

7. **Implement infrastructure** to make tests pass:
   - Implement StateAccessor methods (steps 1-2)
   - Implement BehaviorManager methods (step 3)
   - Implement utility functions (steps 4-5)
   - Run tests frequently, implementing incrementally until all tests pass

8. **Implementation checkpoint:** Verify ALL tests from step 6 pass before proceeding to Phase 2b
   - All infrastructure tests must be green
   - This validates that utilities correctly handle both "player" and NPC actor_ids
   - This validates that StateAccessor, BehaviorManager, and utilities work correctly
   - **Do not proceed to Phase 2b until all Phase 2a tests pass**

**Note on module loading:** When loading behavior modules from the filesystem, the code that walks the directory tree should:
- Load regular files/directories first, calling `behavior_manager.load_module(module, source_type="regular")`
- Load symlinked directories last, calling `behavior_manager.load_module(module, source_type="symlink")`
- This allows conflict detection to distinguish between handlers in local code (which conflict) vs. handler chaining (regular + symlink, which is allowed)
- Wrap `load_module()` calls in try/except to log ValueError exceptions to stderr:
  ```python
  try:
      behavior_manager.load_module(module, source_type="regular")
  except ValueError as e:
      import sys
      print(f"ERROR loading module {module.__name__}: {e}", file=sys.stderr)
      raise  # Re-raise to stop loading if module is invalid
  ```

### Phase 2b: Move Command Handlers

**Entity behaviors are optional:** Command handlers in this phase work with or without entity behaviors. Handlers can be tested with simple entities (no behaviors) and entity behavior modules can be added incrementally as game content requires them.

**Critical Pattern:** Every handler must follow this pattern:
```python
def handle_<verb>(accessor, action):
    actor_id = action.get("actor_id", "player")  # Extract at top of handler
    # ... use actor_id variable in all utility calls, NEVER hardcode "player"
```

1. **Create `behaviors/core/manipulation.py`:**
   - Define vocabulary with event mappings
   - Implement `handle_take`:
     - Extract `actor_id` from action
     - Call `find_accessible_item(accessor, name, actor_id)`
     - Call `accessor.get_actor(actor_id)`
     - Pass `actor_id` to all `accessor.update()` calls
   - Implement `handle_drop`, `handle_put`, `handle_give` following same pattern
   - **Write NPC test for each handler before marking complete**

2. **Create other handler modules** following same pattern:
   - `movement.py` with `handle_go`
   - `perception.py` with `handle_look`, `handle_examine`, `handle_inventory`
   - `interaction.py` with `handle_open`, `handle_close`
   - `locks.py` with `handle_unlock`, `handle_lock`

3. **Testing requirement:** For each handler:
   - Write player test (success path)
   - Write error condition tests
   - **Write NPC test** to verify actor_id threading
   - Run tests and fix any hardcoded "player" strings found

4. **Code review checklist:**
   - [ ] All handlers extract `actor_id` at the top
   - [ ] No string literal `"player"` appears in utility calls
   - [ ] All utility calls pass `actor_id` variable
   - [ ] Type hints match utility function signatures
   - [ ] NPC tests pass for all manipulation commands
   - [ ] All `get_*` calls have appropriate None checks
   - [ ] Tests verify graceful handling of None returns (no AttributeError crashes)

### Phase 2c: Simplify Infrastructure

1. Rename json_protocol.py to llm_protocol.py
2. Update llm_protocol.py to route all commands through `behavior_manager.invoke_handler()`
3. Add inconsistent state detection and handling to llm_protocol.py:
   - Add `self.state_corrupted = False` flag to `__init__`
   - Add check for corrupted state at start of `_process_command()`
   - Add detection of "INCONSISTENT STATE:" prefix in handler results
   - Implement `_handle_inconsistent_state()` method for logging and flag-setting
   - Return generic error to user, log full details to stderr
4. Refactor query handlers in llm_protocol.py to use utilities from `utilities/utils.py`
5. Remove all `_cmd_*` methods from llm_protocol.py
6. Remove game-specific helper methods from llm_protocol.py (moved to `utilities/utils.py`)
7. Remove parallel implementations from game_engine.py
8. Remove convenience methods from state_manager.py (`move_item()`, `set_player_location()`)
9. game_engine.py keeps only: main loop, save/load, parser integration
10. llm_protocol.py retains: command routing, query routing, JSON serialization, inconsistent state handling (all pure infrastructure)

### Modules with Game Knowledge: What to Keep

Some modules will retain game entity knowledge because they define the core data model:

**state_manager.py - Unified actor model**
- Entity dataclasses (Item, Location, Door, Lock, Actor) define the data model
- **Refactor GameState to use unified actor storage:**
  - Replace `self.player` and `self.npcs` with single `self.actors: Dict[str, Actor]`
  - Player is stored as `actors["player"]`
  - All NPCs are stored as `actors[npc.id]`
  - Remove `get_npc()` method (use `actors.get()` directly)
  - **Breaking change rationale:** Prepares for multi-player support, eliminates special-casing
- Serialization/parsing updated to save/load from unified actors dict
- Convenience methods `move_item()`, `set_player_location()` will be removed (replaced by StateAccessor calls in behavior handlers)

**validators.py - Keep as infrastructure**
- Structural validation ensures data integrity on load/save
- Entity type knowledge is acceptable here as it validates the data model
- Does not contain game behavior logic, only structural rules
- Consider: could validators be made pluggable if game authors add new entity types?

**vocabulary_generator.py - Nouns come from entities, not behavior modules**

Nouns (object names recognized by the parser) are extracted directly from entity data (item names, NPC names, location names). This extraction happens in infrastructure code, not in behavior modules.

**Rationale for this design:**

1. **Separation of concerns**: Behavior modules define *what you can do with things* (verbs and handlers). Entity data defines *what things exist* (nouns). Vocabulary generation bridges these by extracting nouns from entity names.

2. **Avoids duplication**: Item names already exist in the data model (e.g., `item.name = "sword"`). Requiring behavior modules to re-register these as nouns would duplicate this information and risk inconsistencies.

3. **Game knowledge stays in data**: The vocabulary generator knows how to extract names from the entity data model (items have `.name`, NPCs have `.name`), but this is knowledge of the *data structure*, not game semantics. It doesn't know what a sword *does*, only that entities have names.

4. **Behavior modules focus on interactions**: Behavior modules register verbs (actions) and define handlers for those actions. They describe interactions, not the objects themselves.

**Where nouns come from:**
- Item names → from `Item.name` property in entity data
- NPC names → from `Actor.name` property in entity data (for non-player actors)
- Location names → from `Location.name` property in entity data
- Verb objects → from vocabulary defined in behavior modules

**What behavior modules provide:**
- Verbs and synonyms (e.g., "take", "get", "grab")
- Verb-to-event mappings (e.g., "take" → "on_take")
- Command handlers (`handle_take()`)
- Entity behaviors (`on_take()`)

**Summary**: Nouns come from entity data (what exists), verbs come from behavior modules (what you can do). The vocabulary generator extracts nouns from entities and combines them with verbs from behavior modules to build the parser vocabulary. This separates game knowledge (behavior) from game content (entities) and infrastructure (vocabulary generation).

### Phase 2d: NPC AI (Future)

1. Implement NPC decision-making
2. NPCs call same handlers with their actor_id
3. Add perception system for NPC awareness

## Testing

See [behavior_refactoring_testing.md](behavior_refactoring_testing.md) for comprehensive testing strategy, test setup utilities, and test specifications.
