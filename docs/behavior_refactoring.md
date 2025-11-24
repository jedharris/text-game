# Behavior Refactoring Design

## Status

This document describes the next phase of the behavior system. Phase 1 (entity behaviors) is implemented and documented in `entity_behaviors.md`. This phase moves command-level logic from `json_protocol.py` into behavior modules.

## Current State

The entity behaviors system (Phase 1) provides:
- Entity-specific event handlers (`on_take`, `on_drop`, etc.)
- Behavior modules with vocabulary extensions
- BehaviorManager for loading and invoking behaviors

However, command logic remains in `json_protocol.py`:
- `_cmd_take`, `_cmd_drop`, `_cmd_put` in json_protocol.py
- `_cmd_go`, `_cmd_open`, `_cmd_close` in json_protocol.py
- `_cmd_unlock`, `_cmd_lock` in json_protocol.py
- `_cmd_examine`, `_cmd_inventory`, `_cmd_look` in json_protocol.py
- `_cmd_drink`, `_cmd_eat`, `_cmd_attack`, `_cmd_use` in json_protocol.py
- `_cmd_read`, `_cmd_climb`, `_cmd_pull`, `_cmd_push` in json_protocol.py

The behavior modules (e.g., `manipulation.py`, `movement.py`, `locks.py`) only define vocabulary, not handlers.

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
- Partial rollback on failure
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
```python
def handle_open(accessor, actor_id, target_id):
    container = accessor.get_item(target_id)

    result = accessor.update(
        entity=container,
        changes={"properties.open": True},
        event="on_open",
        context={"actor_id": actor_id}
    )

    if not result.success:
        if result.error_code == "locked":
            lock_id = container.properties.get("lock_id")
            lock = accessor.get_lock(lock_id)
            key_hint = lock.properties.get("hint", "a key")
            return f"The {container.name} is locked. Perhaps {key_hint} would help."
        return f"You can't open the {container.name}."

    return result.message or f"You open the {container.name}."
```

**Take with weight check and suggestion**:
```python
def handle_take(accessor, actor_id, item_id):
    item = accessor.get_item(item_id)
    if not item:
        return "You don't see that here."

    actor = accessor.get_actor(actor_id)
    weight = item.properties.get("weight", 1)
    current_weight = actor.properties.get("carried_weight", 0)
    max_weight = actor.properties.get("max_carry", 100)

    if current_weight + weight > max_weight:
        lightest = find_lightest_carried_item(accessor, actor_id)
        return f"The {item.name} is too heavy. You could drop the {lightest.name} first."

    # Update with automatic on_take behavior invocation
    result = accessor.update(
        entity=item,
        changes={"location": actor_id},
        event="on_take",
        context={"actor_id": actor_id}
    )

    # Also update actor's inventory
    accessor.append_to_list(actor, "inventory", item.id)

    return result.message or f"You take the {item.name}."
```

### Incremental Progress Reporting

**Alchemical brewing**:
```python
def handle_brew(accessor, actor_id, recipe_id):
    recipe = accessor.get_item(recipe_id)  # or get_recipe if separate
    actor = accessor.get_actor(actor_id)
    messages = []

    # Check each ingredient
    for ingredient_id in recipe.properties.get("ingredients", []):
        if ingredient_id not in actor.inventory:
            ingredient = accessor.get_item(ingredient_id)
            messages.append(f"Missing ingredient: {ingredient.name}")
            continue

        # Remove ingredient from inventory
        ingredient = accessor.get_item(ingredient_id)
        result = accessor.update(
            entity=ingredient,
            changes={"location": "consumed"},
            event="on_consume",
            context={"actor_id": actor_id, "recipe_id": recipe_id}
        )
        accessor.remove_from_list(actor, "inventory", ingredient_id)
        messages.append(f"Added {ingredient.name} to the cauldron.")

    if accessor.has_errors():
        return "\n".join(messages) + "\nThe brewing fails! Some ingredients are lost."

    # Create result item
    result_id = recipe.properties.get("creates")
    result_item = accessor.get_item(result_id)
    accessor.append_to_list(actor, "inventory", result_id)
    messages.append(f"Success! You created a {result_item.name}.")

    return "\n".join(messages)
```

**Combat with multiple attacks**:
```python
def handle_attack(accessor, actor_id, target_id):
    messages = []
    actor = accessor.get_actor(actor_id)
    target = accessor.get_actor(target_id)

    weapon_id = actor.properties.get("equipped_weapon")
    weapon = accessor.get_item(weapon_id) if weapon_id else None

    num_hits = weapon.properties.get("hits", 1) if weapon else 1

    for i in range(num_hits):
        damage = calculate_damage(accessor, actor_id, weapon_id)

        current_health = target.properties.get("health", 100)
        new_health = current_health - damage

        result = accessor.update(
            entity=target,
            changes={"properties.health": new_health},
            event="on_damage",
            context={"actor_id": actor_id, "damage": damage}
        )

        if not result.success:
            messages.append(f"Strike {i+1}: Miss!")
            continue

        messages.append(f"Strike {i+1}: {damage} damage!")

        if new_health <= 0:
            messages.append(f"The {target.name} is defeated!")
            break

    return "\n".join(messages)
```

## StateAccessor

The StateAccessor provides generic state operations with error feedback and automatic behavior invocation.

### Design Principles

1. **Generic API**: StateAccessor has no game-specific knowledge
2. **Handlers specify events**: The handler tells StateAccessor which behavior event to invoke
3. **Atomic updates**: State change + behavior invocation happen together
4. **Direct entity access**: Behaviors get entity objects directly, use existing dataclass properties

### Core API

```python
@dataclass
class UpdateResult:
    """Result from a state update operation."""
    success: bool = True
    message: Optional[str] = None
    error_code: str = ""

@dataclass
class StateAccessor:
    """Provides behaviors with state query and modification capabilities."""

    game_state: GameState
    behavior_manager: BehaviorManager
    errors: List[str] = field(default_factory=list)
    last_error: str = ""

    # Entity retrieval - returns dataclass objects directly

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get item by ID."""
        pass

    def get_actor(self, actor_id: str) -> Optional[Union[PlayerState, NPC]]:
        """Get player or NPC by ID. 'player' returns PlayerState, others search NPCs."""
        pass

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
        """Get player's current location."""
        pass

    # State modification with behavior invocation

    def update(self, entity, changes: Dict[str, Any],
               event: str = None, context: Dict = None) -> UpdateResult:
        """
        Apply changes to entity and optionally invoke behavior event.

        Args:
            entity: The entity object to update
            changes: Dict of property paths to new values
            event: Optional behavior event name (e.g., "on_take")
            context: Optional context dict for behavior

        Returns:
            UpdateResult with success, message, and error_code
        """
        # Apply changes
        for path, value in changes.items():
            self._set_path(entity, path, value)

        # Invoke behavior if specified
        if event and hasattr(entity, 'behaviors'):
            behavior_result = self.behavior_manager.invoke_behavior(
                entity, event, self.game_state, context or {}
            )
            if behavior_result:
                if not behavior_result.allow:
                    return UpdateResult(
                        success=False,
                        message=behavior_result.message,
                        error_code="behavior_prevented"
                    )
                return UpdateResult(
                    success=True,
                    message=behavior_result.message
                )

        return UpdateResult(success=True)

    # List operations

    def append_to_list(self, entity, list_path: str, value: Any) -> bool:
        """Append value to a list property."""
        pass

    def remove_from_list(self, entity, list_path: str, value: Any) -> bool:
        """Remove value from a list property."""
        pass

    # Query helpers (moved from json_protocol.py)

    def find_accessible_item(self, name: str, adjectives: List[str] = None) -> Optional[Item]:
        """Find item by name in current location, on surfaces, or in inventory."""
        pass

    def find_container_by_name(self, name: str, location_id: str) -> Optional[Item]:
        """Find a container item by name in the specified location."""
        pass

    def get_doors_in_location(self, location_id: str = None) -> List[Door]:
        """Get all doors in a location (defaults to current)."""
        pass

    def actor_has_key_for_door(self, actor_id: str, door) -> bool:
        """Check if actor has a key that fits the door's lock."""
        pass

    # Error handling

    def error(self, message: str, code: str = "") -> None:
        """Record an error with optional code for programmatic handling."""
        self.errors.append(message)
        self.last_error = code or message

    def has_errors(self) -> bool:
        """Check if any operations failed."""
        return len(self.errors) > 0

    def clear_errors(self) -> None:
        """Clear error state for new operation sequence."""
        self.errors.clear()
        self.last_error = ""

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

## json_protocol.py After Refactoring

The protocol becomes pure infrastructure with no game-specific knowledge:

```python
class JSONProtocolHandler:
    def __init__(self, state, behavior_manager):
        self.state = state
        self.behavior_manager = behavior_manager
        self.accessor = StateAccessor(state, behavior_manager)

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

        # Call handler with accessor and action
        # Handler returns a message string
        result_message = handler(self.accessor, action)

        # Convert to result dict
        if self.accessor.has_errors():
            return {
                "type": "result",
                "success": False,
                "action": verb,
                "error": {"message": self.accessor.errors[0]}
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

from typing import Dict, Any

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
    actor_id = "player"  # For now; NPC AI would pass different actor_id

    if not obj_name:
        accessor.error("Take what?")
        return ""

    # Find item
    adjectives = action.get("adjectives", [])
    item = accessor.find_accessible_item(obj_name, adjectives)

    if not item:
        accessor.error("You don't see that here.")
        return ""

    if not item.portable:
        accessor.error("You can't take that.")
        return ""

    # Get actor
    actor = accessor.get_actor(actor_id)

    # Update item location and invoke on_take behavior
    result = accessor.update(
        entity=item,
        changes={"location": actor_id},
        event="on_take",
        context={"actor_id": actor_id, "location": accessor.get_current_location()}
    )

    if not result.success:
        accessor.error(result.message or "You can't take that.")
        return ""

    # Add to inventory
    accessor.append_to_list(actor, "inventory", item.id)

    return result.message or f"You take the {item.name}."

def handle_drop(accessor, action):
    """Handle drop command."""
    obj_name = action.get("object")
    actor_id = "player"

    if not obj_name:
        accessor.error("Drop what?")
        return ""

    actor = accessor.get_actor(actor_id)

    # Find item in inventory
    item = None
    for item_id in actor.inventory:
        i = accessor.get_item(item_id)
        if i and i.name == obj_name:
            item = i
            break

    if not item:
        accessor.error("You're not carrying that.")
        return ""

    # Update item location and invoke on_drop behavior
    location = accessor.get_current_location()
    result = accessor.update(
        entity=item,
        changes={"location": location.id},
        event="on_drop",
        context={"actor_id": actor_id, "location": location}
    )

    if not result.success:
        accessor.error(result.message or "You can't drop that.")
        return ""

    # Remove from inventory
    accessor.remove_from_list(actor, "inventory", item.id)

    return result.message or f"You drop the {item.name}."

def handle_put(accessor, action):
    """Handle put command."""
    obj_name = action.get("object")
    container_name = action.get("indirect_object")
    actor_id = "player"

    if not obj_name:
        accessor.error("Put what?")
        return ""

    if not container_name:
        accessor.error("Put it where?")
        return ""

    actor = accessor.get_actor(actor_id)

    # Find item in inventory
    item = None
    for item_id in actor.inventory:
        i = accessor.get_item(item_id)
        if i and i.name == obj_name:
            item = i
            break

    if not item:
        accessor.error("You're not carrying that.")
        return ""

    # Find container
    location = accessor.get_current_location()
    container = accessor.find_container_by_name(container_name, location.id)

    if not container:
        accessor.error(f"You don't see any {container_name} here.")
        return ""

    # Check if container is accessible
    container_props = container.properties.get("container", {})
    if not container_props.get("is_surface", False) and not container_props.get("open", False):
        accessor.error(f"The {container_name} is closed.")
        return ""

    # Update item location and invoke on_drop behavior (putting is like dropping)
    result = accessor.update(
        entity=item,
        changes={"location": container.id},
        event="on_drop",
        context={"actor_id": actor_id, "location": location, "container": container}
    )

    if not result.success:
        accessor.error(result.message or f"You can't put that there.")
        return ""

    # Remove from inventory
    accessor.remove_from_list(actor, "inventory", item.id)

    preposition = "on" if container_props.get("is_surface", False) else "in"
    return result.message or f"You put the {item.name} {preposition} the {container_name}."

def handle_give(accessor, action):
    """Handle give command."""
    obj_name = action.get("object")
    recipient_name = action.get("indirect_object")
    actor_id = "player"

    if not obj_name:
        accessor.error("Give what?")
        return ""

    if not recipient_name:
        accessor.error("Give it to whom?")
        return ""

    actor = accessor.get_actor(actor_id)

    # Find item in inventory
    item = None
    for item_id in actor.inventory:
        i = accessor.get_item(item_id)
        if i and i.name == obj_name:
            item = i
            break

    if not item:
        accessor.error("You're not carrying that.")
        return ""

    # Find recipient NPC
    recipient = None
    for npc in accessor.game_state.npcs:
        if npc.name.lower() == recipient_name.lower():
            recipient = npc
            break

    if not recipient:
        accessor.error(f"You don't see {recipient_name} here.")
        return ""

    # Update item location and invoke on_give behavior on recipient
    result = accessor.update(
        entity=recipient,
        changes={},  # No direct changes to recipient
        event="on_give",
        context={"actor_id": actor_id, "item": item}
    )

    if not result.success:
        accessor.error(result.message or f"{recipient.name} doesn't want that.")
        return ""

    # Transfer item
    item.location = recipient.id
    accessor.remove_from_list(actor, "inventory", item.id)
    accessor.append_to_list(recipient, "inventory", item.id)

    return result.message or f"You give the {item.name} to {recipient.name}."
```

## Migration Path

### Phase 2a: Implement StateAccessor

1. Create `src/state_accessor.py` with core API
2. Move helper methods from json_protocol.py to StateAccessor
3. Add entity retrieval methods (`get_item`, `get_actor`, etc.)
4. Implement `update()` with behavior invocation
5. Write tests for StateAccessor

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

### Phase 2c: Simplify json_protocol.py

1. Update json_protocol.py to route all commands through behavior_manager
2. Remove all `_cmd_*` methods
3. Remove game-specific helper methods (now in StateAccessor)
4. json_protocol.py becomes pure routing infrastructure

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
    accessor = StateAccessor(state, behavior_manager)

    action = {"object": "sword"}
    message = handle_take(accessor, action)

    assert not accessor.has_errors()
    assert "sword" in message
    assert state.get_item("item_sword").location == "player"
    assert "item_sword" in state.player.inventory

def test_handle_take_not_portable():
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    action = {"object": "table"}
    message = handle_take(accessor, action)

    assert accessor.has_errors()
    assert "can't take" in accessor.errors[0].lower()

def test_handle_take_with_behavior():
    state = create_test_state()
    behavior_manager = BehaviorManager()
    # Load light_sources behavior module
    behavior_manager.load_module("behaviors.core.light_sources")
    accessor = StateAccessor(state, behavior_manager)

    action = {"object": "lantern"}
    message = handle_take(accessor, action)

    assert not accessor.has_errors()
    assert "runes flare to life" in message  # From on_take behavior
    assert state.get_item("item_lantern").states.get("lit") == True
```

## Benefits

1. **Extensibility**: Override `handle_take` without modifying engine
2. **Organization**: Related code in one module (vocab + handler)
3. **Testability**: Handlers tested with real StateAccessor, no mocks needed
4. **Consistency**: All commands follow same pattern
5. **No silent errors**: Behavior invocation tied to state updates
6. **Clean separation**: json_protocol.py has no game knowledge
7. **Future-proofing**: Ready for NPC AI with actor_id parameter

## Deferred

- Undo/rollback support in StateAccessor
- Transaction batching for complex operations
- NPC AI using behavior handlers
- Behavior override/priority system
- `actors.py` module if needed for behaviors that don't fit elsewhere
