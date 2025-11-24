# Behavior Refactoring Design

## Goals

1. Centralize state modifications through a StateAccessor for consistent error reporting
2. Move domain logic from game_engine.py to appropriate behavior modules
3. Treat player and NPCs ("beings") uniformly for movement and manipulation
4. Keep behaviors focused on domain rules, not state management mechanics

## Use Cases

- Being moves through a door (checks: door exists, door open, door unlocked)
- Being takes/drops an item (checks: item exists, item portable, capacity limits)
- Being puts item in/on container (checks: container exists, container open, item fits)
- Being unlocks/locks a door (checks: has correct key, door is lockable)
- Consumable items modify state (e.g., eating food removes it from inventory)

## StateAccessor

A single object passed to behaviors for all state queries and modifications.

```python
# src/state_accessor.py

from dataclasses import dataclass, field
from typing import Any, List, Optional

@dataclass
class StateAccessor:
    """Provides behaviors with state query and modification capabilities."""

    game_state: dict  # Reference to the full game state
    errors: List[str] = field(default_factory=list)

    def get(self, entity_type: str, entity_id: str, path: str = "") -> Optional[Any]:
        """Get entity or property value. Returns None if not found."""
        # entity_type: "items", "locations", "doors", "locks", "beings"
        # path: dot-separated property path, e.g., "properties.locked"
        pass

    def set(self, entity_type: str, entity_id: str, path: str, value: Any) -> bool:
        """Set property value. Returns False and logs error on failure."""
        pass

    def append(self, entity_type: str, entity_id: str, path: str, value: Any) -> bool:
        """Append to list property. Returns False and logs error on failure."""
        pass

    def remove(self, entity_type: str, entity_id: str, path: str, value: Any) -> bool:
        """Remove from list property. Returns False and logs error on failure."""
        pass

    def has_errors(self) -> bool:
        """Check if any operations failed."""
        return len(self.errors) > 0
```

### Entity Types

- `"items"` - Objects that can be taken, used, etc.
- `"locations"` - Rooms and areas
- `"doors"` - Connections between locations
- `"locks"` - Lock mechanisms on doors
- `"beings"` - Player and NPCs (indexed by ID; player has ID "player")

### Path Syntax

Dot-separated property access:
- `""` - Returns the entire entity
- `"location"` - Direct property
- `"properties.locked"` - Nested property
- `"inventory"` - List property (for append/remove)

## Behavior Signatures

Behaviors receive the accessor and return a message string:

```python
def handle_unlock(
    accessor: StateAccessor,
    actor_id: str,  # "player" or NPC ID
    target_id: str,
    tool_id: Optional[str] = None
) -> str:
    """Attempt to unlock target. Returns message describing result."""
    pass
```

The game engine checks `accessor.has_errors()` after the behavior returns to determine if the action succeeded.

## Behavior Module Organization

### behaviors/core/movement.py

Handles being movement between locations.

```python
def handle_go(accessor: StateAccessor, actor_id: str, direction: str) -> str:
    """Move being in direction. Checks exits, doors, locks."""
    # 1. Get actor's current location
    # 2. Find exit in direction
    # 3. If door exists, check if open (and unlocked)
    # 4. Update actor's location
    # 5. Return arrival description
    pass
```

### behaviors/core/manipulation.py

Handles all item movement: take, drop, put, give.

```python
def handle_take(accessor: StateAccessor, actor_id: str, item_id: str) -> str:
    """Being takes item from current location or container."""
    pass

def handle_drop(accessor: StateAccessor, actor_id: str, item_id: str) -> str:
    """Being drops item at current location."""
    pass

def handle_put(accessor: StateAccessor, actor_id: str, item_id: str,
               container_id: str, preposition: str) -> str:
    """Being puts item in/on container."""
    # preposition: "in" or "on"
    pass
```

### behaviors/core/locks.py

Handles lock and unlock actions.

```python
def handle_unlock(accessor: StateAccessor, actor_id: str,
                  door_id: str, key_id: Optional[str] = None) -> str:
    """Unlock door with key. Auto-selects key if not specified."""
    # 1. Get lock for door
    # 2. Check if door is locked
    # 3. Find valid key in actor's inventory
    # 4. Set lock state to unlocked
    pass

def handle_lock(accessor: StateAccessor, actor_id: str,
                door_id: str, key_id: Optional[str] = None) -> str:
    """Lock door with key."""
    pass
```

### behaviors/core/containers.py

Container-specific validation, used by manipulation.py.

```python
def can_accept_item(accessor: StateAccessor, container_id: str, item_id: str) -> bool:
    """Check if container can accept item (open, capacity, etc.)."""
    pass

def get_container_contents(accessor: StateAccessor, container_id: str) -> List[str]:
    """Get list of item IDs in container."""
    pass
```

## Game Engine Integration

The game engine creates a StateAccessor and passes it to behaviors:

```python
# In game_engine.py

def process_command(self, command: ParsedCommand) -> str:
    accessor = StateAccessor(self.game_state)

    # Dispatch to appropriate behavior
    if command.verb == "go":
        message = movement.handle_go(accessor, "player", command.direction)
    elif command.verb == "take":
        message = manipulation.handle_take(accessor, "player", command.object_id)
    # ... etc

    # Check for errors
    if accessor.has_errors():
        return accessor.errors[0]  # Return first error as message

    return message
```

## Beings Data Structure

Player and NPCs share structure under `game_state["beings"]`:

```python
{
    "beings": {
        "player": {
            "location": "start_room",
            "inventory": ["key", "lamp"],
            "properties": {}
        },
        "guard": {
            "location": "treasury",
            "inventory": ["sword"],
            "properties": {"hostile": True}
        }
    }
}
```

Note: This requires migrating current player data from `game_state["player"]` to `game_state["beings"]["player"]`.

## Migration Path

1. Implement StateAccessor class
2. Add "beings" structure to game state, migrate player data
3. Refactor movement.py to use accessor
4. Refactor manipulation.py to use accessor
5. Move lock logic from game_engine.py to locks.py
6. Update game_engine.py to use new behavior signatures
7. Remove duplicated logic from game_engine.py

## Deferred

- Undo/rollback support in StateAccessor
- Transaction batching for complex operations
- NPC AI that uses these behaviors
