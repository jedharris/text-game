# Behavior Refactoring Design

## Status

This document describes the next phase of the behavior system. Phase 1 (entity behaviors) is implemented and documented in `entity_behaviors.md`. This phase moves command-level logic from `json_protocol.py` into behavior modules.

## Current State

The entity behaviors system (Phase 1) provides:
- Entity-specific event handlers (`on_take`, `on_drop`, etc.)
- Behavior modules with vocabulary extensions
- BehaviorManager for loading and invoking behaviors
- All entities have `behaviors: Dict[str, str]` field mapping event names to module names

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
- Entity type validation (locations, items, doors, locks, actors)
- Valid location types for items (location, item, actor)
- Exit references and door_id validation
- Lock/key relationships

**vocabulary_generator.py** contains game semantics:
- Extracts item and NPC names as nouns
- Knows entity structure for vocabulary generation

**state_manager.py** contains game entity definitions:
- Entity dataclasses (Item, Location, Door, Lock, Actor)
- Convenience methods like `move_item()`, `set_player_location()`
- Property accessors for game concepts (portable, container, locked, etc.)

The behavior modules (e.g., `manipulation.py`, `movement.py`, `locks.py`) only define vocabulary, not handlers.

This dispersion of game knowledge is a maintenance burden and source of bugs when changes are made to one file but not the others.

## Goals

1. Move command logic from json_protocol.py to behavior modules
2. Allow game developers to override or extend core behaviors without modifying engine code
3. Make json_protocol.py pure infrastructure with no game-specific knowledge
4. Support player/NPC unification when NPC AI is implemented

## Error Handling Convention

**Developer errors vs. User errors:**

This design distinguishes between two types of errors:

1. **User errors**: Expected conditions like "you don't see that here" or "the door is locked"
   - Returned as normal HandlerResult messages
   - Displayed to the player directly
   - Part of normal gameplay

2. **Developer errors**: Bugs in handler code or game data like "field not found" or "cannot append to non-list"
   - Indicate implementation bugs, not player mistakes
   - Should never occur in production if properly tested
   - Logged to stderr for developer visibility
   - May show generic fallback message to players in production

**Logging convention:**

All developer-oriented error messages are logged to stderr with context. The following locations implement this convention:

1. **StateAccessor.update()** - logs `_set_path()` errors with entity and path details
2. **BehaviorManager.load_module()** - raises ValueError for vocabulary/conflict errors (caller logs)
3. **BehaviorManager.invoke_previous_handler()** - raises RuntimeError if position list not initialized
4. **LLMProtocolHandler._handle_inconsistent_state()** - logs full error with timestamp, command, action
5. **Module loading code** - wraps load_module() and importlib.import_module() to catch SyntaxError, ImportError, ValueError, and logs all to stderr

See "Design Rationale: Module Loading Error Handling" section for comprehensive specification of error handling during module loading.

**Example stderr output:**

```
# Module loading errors (syntax, import, vocabulary, conflicts)
ERROR loading module behaviors.core.manipulation: SyntaxError: invalid syntax (manipulation.py, line 42)
ERROR loading module behaviors.custom.magic: ModuleNotFoundError: No module named 'behaviors.custom.spells'
ERROR loading module behaviors.manipulation: Module 'behaviors.manipulation': vocabulary['verbs'] must be a list, got str
ERROR loading module behaviors.custom.take_extended: Handler conflict for verb 'take': Multiple regular modules define handle_take: manipulation, take_extended

# Runtime state mutation errors
ERROR: _set_path() failed in update(): Field not found: loaction
  Entity: Item(id='sword', name='sword', ...)
  Path: loaction, Value: room1

# Inconsistent state errors (handler bugs)
FATAL ERROR: Inconsistent State Detected
Timestamp: 2025-01-15T10:30:45.123456
Command: give
Actor: player
Action: {'verb': 'give', 'object': 'sword', 'target': 'guard', 'actor_id': 'player'}
Error: INCONSISTENT STATE: Item location changed but inventory update failed: Cannot remove from non-list field: inventory
```

This ensures developers see technical details during development/testing while keeping the player experience clean.

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

Entity behaviors can look up additional context and return rich messages:

```python
# Entity behavior (on_open for a lockable container)
def on_open_locked(entity, accessor, context):
    container_props = entity.properties.get("container", {})
    if container_props.get("locked"):
        # Behavior looks up hint itself
        lock_id = container_props.get("lock_id")
        lock = accessor.get_lock(lock_id)
        key_hint = lock.properties.get("hint", "a key") if lock else "a key"
        return EventResult(
            allow=False,
            message=f"The {entity.name} is locked. Perhaps {key_hint} would help."
        )
    return EventResult(allow=True)

# Command handler
def handle_open(accessor, action):
    actor_id = action.get("actor_id", "player")
    target_name = action.get("object")
    container = find_accessible_item(accessor, target_name)
    if not container:
        return HandlerResult(success=False, message="You don't see that here.")

    result = accessor.update(
        entity=container,
        changes={"properties.container.open": True},
        verb="open",
        actor_id=actor_id
    )

    if not result.success:
        return HandlerResult(success=False, message=result.message or f"You can't open the {container.name}.")

    return HandlerResult(success=True, message=result.message or f"You open the {container.name}.")
```

The behavior has access to the accessor and can look up any information it needs to provide a helpful message. This keeps the command handler simple.

### Advanced: Multi-step Operations

These examples show more complex patterns. They're not required for basic refactoring but demonstrate the system's capabilities.

**Alchemical brewing** (multi-ingredient consumption):
```python
def handle_brew(accessor, action):
    actor_id = action.get("actor_id", "player")
    recipe_name = action.get("object")
    recipe = find_accessible_item(accessor, recipe_name, actor_id)
    if not recipe:
        return HandlerResult(success=False, message="You don't see that recipe here.")

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(success=False, message="Actor not found.")

    messages = []

    for ingredient_id in recipe.properties.get("ingredients", []):
        if ingredient_id not in actor.inventory:
            ingredient = accessor.get_item(ingredient_id)
            if not ingredient:
                messages.append(f"Missing ingredient: {ingredient_id} (not found in game)")
                continue
            messages.append(f"Missing ingredient: {ingredient.name}")
            continue

        ingredient = accessor.get_item(ingredient_id)
        if not ingredient:
            messages.append(f"Error: Ingredient {ingredient_id} not found")
            continue

        # Update ingredient location
        accessor.update(
            entity=ingredient,
            changes={"location": "consumed"},
            verb="consume",
            actor_id=actor_id
        )
        # Update actor inventory
        accessor.update(
            entity=actor,
            changes={"-inventory": ingredient_id}
        )
        messages.append(f"Added {ingredient.name} to the cauldron.")

    if any("Missing" in m or "Error" in m for m in messages):
        return HandlerResult(success=False, message="\n".join(messages))

    result_id = recipe.properties.get("creates")
    result_item = accessor.get_item(result_id)
    if not result_item:
        return HandlerResult(success=False, message="Recipe result item not found in game data.")

    # Update result item location
    accessor.update(
        entity=result_item,
        changes={"location": actor_id}
    )
    # Update actor inventory
    accessor.update(
        entity=actor,
        changes={"+inventory": result_id}
    )
    messages.append(f"Success! You created a {result_item.name}.")

    return HandlerResult(success=True, message="\n".join(messages))
```

## StateAccessor

The StateAccessor provides generic state operations with automatic behavior invocation. A single accessor can be reused across commands.

### Design Principles

1. **Generic API**: StateAccessor has no game-specific knowledge
2. **Explicit actor_id**: All operations requiring an actor take actor_id as a parameter
3. **Verb-driven events**: Handlers specify action verbs (e.g., "take", "open"); vocabulary maps verbs to events
4. **Atomic updates**: Behavior is checked before changes are applied
5. **Direct entity access**: Behaviors get entity objects directly, use existing dataclass properties
6. **Consistent returns**: Handlers return `HandlerResult` dataclass with `success` and `message` fields
7. **Handler chaining**: Custom handlers can delegate to previous handlers via `invoke_previous_handler()`

### Multi-Update Limitation

**Important:** Individual `update()` calls are atomic (behavior is checked before applying changes), but handlers that make multiple sequential `update()` calls lack transaction support. If a second update fails after the first succeeds, state will be inconsistent.

**Convention for error reporting:** When a follow-up update fails, return a HandlerResult with the prefix `"INCONSISTENT STATE:"` in the message. The infrastructure (llm_protocol.py) detects this prefix and handles it specially:

```python
# First update succeeded
result = accessor.update(entity=item, changes={"location": actor_id}, verb="take")

# Check second update for errors
inventory_result = accessor.update(entity=actor, changes={"+inventory": item.id})

if not inventory_result.success:
    return HandlerResult(
        success=False,
        message=f"INCONSISTENT STATE: Item location changed but inventory update failed: {inventory_result.message}"
    )
```

**Infrastructure handling of inconsistent state:**

When llm_protocol.py receives a HandlerResult with message starting with `"INCONSISTENT STATE:"`, it:

1. **Logs full error details** for the developer (to file or stderr):
   - Full error message with technical details
   - Command that triggered the error
   - Actor ID
   - Timestamp

2. **Returns user-facing error** to the player:
   - Generic message: "An error occurred. The game cannot continue safely. Please report this to the developer."
   - Optionally includes a sanitized error ID for bug reports

3. **Sets a flag** indicating the game state is corrupted:
   - Future commands should be rejected with "Game state corrupted" message
   - Only meta-commands (save, quit) are allowed
   - This prevents cascading errors from corrupted state

**Benefits of this approach:**

1. **Developer gets full debugging information**: Complete error message, command, action, timestamp logged to stderr
2. **Player gets graceful failure**: Generic message prevents confusion from technical details
3. **Prevents cascading errors**: state_corrupted flag stops further commands that could worsen corruption
4. **Allows emergency save**: Meta-commands (save, quit) still work so player doesn't lose all progress
5. **Clear bug reports**: Player can save corrupted state file and send to developer for debugging
6. **Testing catches issues**: "INCONSISTENT STATE:" prefix makes these errors visible during development

This approach provides full debugging information for developers while presenting a graceful failure to players without attempting complex rollback. Transaction support is deferred (see Deferred section).

### Core API

All result dataclasses and StateAccessor live in `src/state_accessor.py`. Handlers import from this module:

```python
# In src/state_accessor.py
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union

@dataclass
class EventResult:
    """
    Result from an entity behavior event handler.

    Entity behaviors can provide messages for both success and failure cases:
    - When allow=False: message explains why the action was denied (e.g., "The chest is locked")
    - When allow=True: message provides flavor text or feedback (e.g., "The lantern's runes flare to life")
    - When allow=True and message=None: handler uses its default message
    """
    allow: bool = True
    message: Optional[str] = None  # Human-readable message (can be provided for both allow=True and allow=False)

@dataclass
class UpdateResult:
    """Result from a state update operation."""
    success: bool = True
    message: Optional[str] = None  # Human-readable message from behavior

@dataclass
class HandlerResult:
    """Result from a command handler."""
    success: bool
    message: str

@dataclass
class StateAccessor:
    """Provides behaviors with state query and modification capabilities."""

    game_state: GameState
    behavior_manager: BehaviorManager

    # Entity retrieval - returns dataclass objects directly

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get item by ID."""
        pass

    def get_actor(self, actor_id: str) -> Optional[Actor]:
        """
        Get actor by ID.

        All actors (including the player) are stored in game_state.actors dict.
        The player is just an actor with id="player".
        """
        return self.game_state.actors.get(actor_id)

    def get_location(self, location_id: str) -> Optional[Location]:
        """Get location by ID."""
        pass

    def get_door(self, door_id: str) -> Optional[Door]:
        """Get door by ID."""
        pass

    def get_lock(self, lock_id: str) -> Optional[Lock]:
        """Get lock by ID."""
        pass

    def get_current_location(self, actor_id: str) -> Location:
        """Get the actor's current location."""
        actor = self.get_actor(actor_id)
        return self.game_state.get_location(actor.location)

    def get_items_in_location(self, location_id: str) -> List[Item]:
        """Get all items directly in a location (or container)."""
        pass

    def get_actors_in_location(self, location_id: str) -> List[Actor]:
        """Get all actors in a location (including player if present)."""
        pass

    # State modification with behavior invocation

    def update(self, entity, changes: Dict[str, Any],
               verb: str = None, actor_id: str = "player") -> UpdateResult:
        """
        Invoke behavior event (if any) then apply changes to entity.

        Args:
            entity: The entity object to update
            changes: Dict mapping string paths to new values
                - Keys are ALWAYS strings (never nested dicts)
                - Use dot notation for nested properties: "properties.container.open"
                - Use "+" prefix for list append: "+inventory" (accesses field "inventory")
                - Use "-" prefix for list remove: "-inventory" (accesses field "inventory")
                - Prefixes are metadata indicating the operation, not part of the field name
                Examples:
                  {"location": "room1"}  # Simple field
                  {"properties.health": 50}  # Nested dict field
                  {"+inventory": "sword"}  # Append to "inventory" list
                  {"-inventory": "sword"}  # Remove from "inventory" list
            verb: Optional action verb (e.g., "take", "open") - mapped to event via vocabulary
            actor_id: The actor performing the action (default "player")

        Returns:
            UpdateResult with success and message
        """
        # Look up event name from verb using vocabulary
        event_name = None
        if verb:
            event_name = self.behavior_manager.get_event_for_verb(verb)
            # Returns None if verb has no event mapping - this is valid
            # (e.g., "quit" might be in vocabulary but not trigger entity behaviors)

        # Invoke behavior first to check if action is allowed
        # All entities have a behaviors field (may be empty list)
        if event_name:
            context = {"actor_id": actor_id, "changes": changes, "verb": verb}
            behavior_result = self.behavior_manager.invoke_behavior(
                entity, event_name, self, context
            )
            # behavior_result is None if entity.behaviors is empty or no behaviors matched
            if behavior_result:
                if not behavior_result.allow:
                    return UpdateResult(
                        success=False,
                        message=behavior_result.message
                    )
                # Behavior allowed; apply all changes
                for path, value in changes.items():
                    error = self._set_path(entity, path, value)
                    if error:
                        # Log developer error to stderr
                        import sys
                        print(f"ERROR: _set_path() failed in update(): {error}", file=sys.stderr)
                        print(f"  Entity: {entity}", file=sys.stderr)
                        print(f"  Path: {path}, Value: {value}", file=sys.stderr)
                        return UpdateResult(success=False, message=error)
                return UpdateResult(
                    success=True,
                    message=behavior_result.message
                )

        # No event or no matching behavior; just apply changes
        # This happens when:
        # - verb has no event mapping (event_name is None)
        # - entity.behaviors is empty (behavior_result is None)
        # - no behaviors matched the event (behavior_result is None)
        for path, value in changes.items():
            error = self._set_path(entity, path, value)
            if error:
                # Log developer error to stderr
                import sys
                print(f"ERROR: _set_path() failed in update(): {error}", file=sys.stderr)
                print(f"  Entity: {entity}", file=sys.stderr)
                print(f"  Path: {path}, Value: {value}", file=sys.stderr)
                return UpdateResult(success=False, message=error)
        return UpdateResult(success=True)

    # Handler chaining support

    def invoke_previous_handler(self, verb: str, action: Dict) -> HandlerResult:
        """
        Invoke the handler that was registered before the current one.

        This allows custom handlers to extend core functionality without
        knowing the specific module name to import.

        Args:
            verb: The command verb
            action: The action dict

        Returns:
            HandlerResult from handler
        """
        return self.behavior_manager.invoke_previous_handler(verb, self, action)

    # Internal helpers

    def _set_path(self, entity, path: str, value: Any) -> Optional[str]:
        """
        Set a property value using dot-separated path.

        Path format (string keys only, never nested dicts):
        - Simple field: "location"
        - Nested dict: "properties.container.open"
        - List append: "+inventory" (prefix + is stripped, field is "inventory")
        - List remove: "-inventory" (prefix - is stripped, field is "inventory")

        The + and - prefixes are operation indicators that are stripped before
        accessing the field. For example, "+inventory" means "append to the
        'inventory' field", not "access a field literally named '+inventory'".

        Supported operations:
        - "+field": append value to list field
        - "-field": remove value from list field
        - "field": set field value

        Returns:
            None on success, error message string on failure.
            Errors include: path not found, remove from missing list,
            value not in list for remove operation.
        """
        # Check for list operation prefix
        if path.startswith("+"):
            path = path[1:]
            operation = "append"
        elif path.startswith("-"):
            path = path[1:]
            operation = "remove"
        else:
            operation = "set"

        parts = path.split(".")
        obj = entity
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict):
                obj = obj.setdefault(part, {})
            else:
                return f"Path not found: {'.'.join(parts[:-1])}"

        final = parts[-1]

        if operation == "append":
            if hasattr(obj, final):
                target = getattr(obj, final)
                if not isinstance(target, list):
                    return f"Cannot append to non-list field: {path}"
                target.append(value)
            elif isinstance(obj, dict):
                obj.setdefault(final, []).append(value)
        elif operation == "remove":
            if hasattr(obj, final):
                target = getattr(obj, final)
                if not isinstance(target, list):
                    return f"Cannot remove from non-list field: {path}"
                try:
                    target.remove(value)
                except ValueError:
                    return f"Value {value} not in list: {path}"
            elif isinstance(obj, dict) and final in obj:
                try:
                    obj[final].remove(value)
                except ValueError:
                    return f"Value {value} not in list: {path}"
            else:
                return f"Field not found: {path}"
        else:  # set
            if hasattr(obj, final):
                setattr(obj, final, value)
            elif isinstance(obj, dict):
                obj[final] = value
            else:
                return f"Field not found: {path}"

        return None
```

### Error Handling: None Returns from get_* Methods

**Type Contract:** All `get_*` methods return `Optional[Entity]`, meaning they return `None` when the requested entity doesn't exist.

**When None occurs:**
1. **Malformed game data** - Entity references non-existent entity (developer error)
2. **Corrupted state** - Previous operation left dangling references (implementation bug)
3. **Race conditions** - Entity was deleted while being referenced (future multi-user scenarios)

Handlers must treat None returns as error conditions and return appropriate HandlerResult messages.

#### When to Check for None

**ALWAYS check when the ID comes from:**
- Entity properties: `entity.properties.get("lock_id")`
- External references: `exit_desc.door_id`, items from `actor.inventory`
- Computed values or loops
- User input or search results

```python
# Correct pattern for property references
lock_id = container.properties.get("lock_id")
if lock_id:
    lock = accessor.get_lock(lock_id)
    if lock and lock.properties.get("locked", False):
        return HandlerResult(success=False, message="It's locked.")
```

**Optional (but recommended) when the ID comes from:**
- Infrastructure-provided `actor_id` (from action dict passed by llm_protocol)
- Entity location fields: `actor.location`

These *should* never be None if game state is consistent, but defensive checking improves robustness:

```python
# Defensive style (recommended for production code)
actor = accessor.get_actor(actor_id)
if not actor:
    return HandlerResult(success=False, message="Actor not found.")
# Proceed with actor operations

# Trust-based style (acceptable for infrastructure-provided IDs in development)
actor = accessor.get_actor(actor_id)
# Proceed assuming actor is not None
# Will raise AttributeError if assumption is violated (fast failure)
```

#### Anti-Patterns

**DO NOT do this:**
```python
# ✗ BAD: No None check before accessing attributes
actor = accessor.get_actor(actor_id)
for item_id in actor.inventory:  # Crashes with AttributeError if actor is None
    ...

# ✗ BAD: No None check with property reference
lock_id = door.properties.get("lock_id")
lock = accessor.get_lock(lock_id)
if lock.locked:  # Crashes with AttributeError if lock is None
    ...

# ✗ BAD: Assuming get_item always returns an item
ingredient = accessor.get_item(ingredient_id)
messages.append(f"Missing: {ingredient.name}")  # Crashes if ingredient is None
```

**DO this instead:**
```python
# ✓ GOOD: Check before use
actor = accessor.get_actor(actor_id)
if not actor:
    return HandlerResult(success=False, message="Actor not found.")
for item_id in actor.inventory:
    ...

# ✓ GOOD: Check lock exists before checking locked state
lock_id = door.properties.get("lock_id")
if lock_id:
    lock = accessor.get_lock(lock_id)
    if lock and lock.properties.get("locked", False):
        return HandlerResult(success=False, message="The door is locked.")

# ✓ GOOD: Handle missing item gracefully
ingredient = accessor.get_item(ingredient_id)
if not ingredient:
    messages.append(f"Error: Missing ingredient {ingredient_id}")
    continue
messages.append(f"Missing: {ingredient.name}")
```

#### Development vs Production Trade-offs

**Development/Testing:** Trust-based style can be acceptable for infrastructure-provided IDs because:
- Failures produce clear AttributeError tracebacks
- Bugs are caught immediately during testing
- Less defensive code is easier to read

**Production:** Defensive style is strongly recommended because:
- Graceful error messages are better than crashes
- Helps diagnose state corruption issues
- Provides better user experience when data is malformed

**Recommendation:** Start with defensive style by default. Only relax checking for infrastructure-provided IDs after thorough testing proves it's safe.

### Helper Functions

The behavior system provides helper functions in `behaviors.core.utils` for common operations.

#### find_accessible_item()

```python
def find_accessible_item(accessor: StateAccessor, item_name: str, actor_id: str = "player") -> Optional[Item]:
    """
    Find an item accessible to an actor by name.

    Search order (first match wins):
    1. Items in actor's current location
    2. Items in actor's inventory
    3. Items on surface containers in location
    4. Items in open enclosed containers in location

    Args:
        accessor: StateAccessor instance for querying state
        item_name: Name of item to find (case-sensitive)
        actor_id: Actor performing the search (default "player")

    Returns:
        First matching Item, or None if not found

    Example:
        item = find_accessible_item(accessor, "key", actor_id)
        if not item:
            return HandlerResult(success=False, message="You don't see that here.")
    """
```

**Duplicate name handling:**

If multiple items have the same name, `find_accessible_item()` returns the **first match** according to the search order above. This means:
- An item in the location takes precedence over an item in inventory with the same name
- An item in inventory takes precedence over an item in a container
- Items are not disambiguated - the first found is returned

For games requiring disambiguation, implement custom search logic in your handler.

### Design Rationale: StateAccessor and BehaviorManager Coupling

StateAccessor requires a BehaviorManager instance in its constructor. This tight coupling is **intentional and justified** by the design goals.

**Why the coupling exists:**

StateAccessor's core responsibility (Goal #1) is to "provide clean abstraction over state mutations with **automatic behavior invocation**" (emphasis added). The `update()` method implements this by:

1. Applying state changes via `_set_path()`
2. Automatically invoking entity behaviors via `behavior_manager.invoke_behavior()`

This makes "state update with behavior invocation" an atomic operation from the caller's perspective.

**Why making BehaviorManager optional would be wrong:**

Making `behavior_manager` optional would:
- Undermine the design principle that all updates trigger behaviors automatically
- Require `if self.behavior_manager:` checks before every invocation, adding complexity
- Create an unsupported mode where updates bypass the behavior system
- Force callers to decide whether behaviors should run, violating encapsulation

**For testing:**

Tests should use a real BehaviorManager instance, potentially with no modules loaded if testing pure state mutations without behaviors. This aligns with the testing principle: "No mocking required: Tests use real GameState objects and real handlers."

**Conclusion:**

This coupling enforces the architectural invariant that state changes always go through the behavior system. It's a feature of the design, not a limitation.

### Design Rationale: Unified Actor Model

The design uses a single `Actor` type for all actors (player and NPCs) stored in an `actors` dict, rather than separate `player` and `npcs` fields with different types.

**Benefits:**

1. **No special-casing**: StateAccessor has no game-specific vocabulary. `get_actor(actor_id)` is a simple dict lookup with no conditionals.

2. **Multi-player ready**: Supporting multiple players later only requires:
   - Adding more actors to the dict with different IDs
   - No changes to StateAccessor or behavior handlers
   - Handlers already use `actor_id` throughout

3. **Consistent APIs**: All actor operations work the same way:
   - `accessor.get_actor("player")` - gets player
   - `accessor.get_actor("npc_guard")` - gets NPC
   - `accessor.get_actors_in_location(loc_id)` - gets all actors (including player)

4. **Simpler code**: No branching logic needed:
   ```python
   # Before (special-casing):
   if actor_id == "player":
       return self.game_state.player
   return self.game_state.get_npc(actor_id)

   # After (unified):
   return self.game_state.actors.get(actor_id)
   ```

5. **Natural iteration**: Finding actors in a location is straightforward:
   ```python
   for actor in accessor.get_actors_in_location(location_id):
       # Process all actors uniformly
   ```

**Migration considerations:**

- Breaking change to GameState structure
- Save file compatibility: loader should migrate old format (player/npcs fields) to new format (actors dict)
- Not a concern for this project since nothing has shipped yet

**Single Actor type:**

The design uses a single `Actor` dataclass for all actors. The player is just an actor with `id="player"`. If future requirements necessitate player-specific fields (e.g., skill trees, quest logs), these can be added as optional fields in the Actor dataclass that are `None` for NPCs.

### Design Rationale: _set_path() Error Messages

The `_set_path()` method returns developer-oriented error messages like `"Field not found: location"` or `"Cannot append to non-list field: inventory"`. These errors expose internal field names and are **intentionally not user-friendly**.

**Why this is acceptable:**

These errors indicate **bugs in handler code**, not user errors. They occur in two scenarios:

1. **Developer typos**: Handler code uses wrong field names
   ```python
   # BUG: typo in field name
   accessor.update(entity=item, changes={"loaction": "room1"})
   # Returns: "Field not found: loaction"
   ```

2. **Data structure mismatches**: Entity structure doesn't match handler expectations
   ```python
   # BUG: inventory is not a list
   accessor.update(entity=actor, changes={"+inventory": "sword"})
   # Returns: "Cannot append to non-list field: inventory"
   ```

**These errors should never occur in production** because:
- They represent bugs in handler implementation
- Testing (especially the comprehensive test suite described in this document) should catch all such errors before deployment
- The NPC test pattern specifically validates that handlers work with any actor, not just the player

**Error message design philosophy:**

The error messages are deliberately technical because:
- They help developers debug handler code quickly
- They provide exact information about what failed (field path, operation, entity)
- They appear during development and testing, not in production
- User-friendly messages would obscure the actual problem and slow debugging

**Error logging and reporting:**

Following the Error Handling Convention (see above), `_set_path()` errors are developer errors that should be logged:

1. **During development/testing**: Errors are raised immediately with technical details, failing fast
2. **In production** (if these bugs slip through):
   - Log technical error to stderr with full context
   - Return generic UpdateResult to prevent cascading failures
   - Handler converts to user-facing error message

**Implementation approach:**

`_set_path()` returns error strings (not exceptions) so callers can handle them appropriately:
- `update()` receives error string and returns `UpdateResult(success=False, message=error)`
- Handler receives UpdateResult and can log to stderr before returning user-facing message
- This preserves the call chain while allowing proper error handling

**Recommended development approach:**

Treat `_set_path()` errors as assertions that should never trigger in production:
1. During development: Fix the handler code bug immediately
2. During testing: Write a test that reproduces the bug, then fix it
3. In production: Log to stderr, return generic error, investigate and deploy fix

The error messages are a **debugging tool**, not a user-facing feature.

### Design Rationale: Multiple Behaviors Per Entity

Entities can reference multiple behavior modules (e.g., `behaviors=["lockable", "cursed"]`). When multiple behaviors define handlers for the same event (e.g., both define `on_take`), the design invokes **all matching behaviors** and combines their results.

**Combination strategy: All must allow (AND logic)**

When `invoke_behavior()` finds multiple matching event handlers:
1. All handlers are invoked in the order listed in `entity.behaviors`
2. Results are combined:
   - `allow = all(r.allow for r in results)` - ANY deny vetoes the action
   - Messages are concatenated with newlines - player sees all feedback

**Rationale for invoking all behaviors:**

1. **Complete player feedback**: If an item is both locked AND cursed, the player should learn about both constraints, not just the first one encountered. This provides better information for problem-solving.

2. **Composable constraints**: Multiple behaviors can each impose independent constraints. A lockable cursed container must pass BOTH the lock check AND the curse check.

3. **Qualitative effects accumulate**: Beyond allow/deny, behaviors can provide success messages describing effects. If taking a glowing sword both triggers its magic glow AND alerts nearby guards, both messages should be shown.

4. **Simple mental model**: "All behaviors listed in the entity apply" is easier to understand than "first behavior wins" or priority systems.

**Order matters**: Behaviors are invoked in list order, so `behaviors=["cursed", "lockable"]` shows the curse message before the lock message. Entity designers control message ordering by listing behaviors in priority order.

**Alternatives considered:**

- **First behavior wins** (original implementation): Simple but loses information - player wouldn't learn about all constraints
- **Priority/weighting system**: Complex and not motivated by real use cases - no current scenarios require fine-grained control beyond list ordering

**Example:**

```python
# Entity with multiple behaviors
cursed_chest = Item(
    id="cursed_chest",
    behaviors=["cursed_items", "lockable_containers"],
    properties={
        "cursed": True,
        "lock_id": "lock_chest_01"
    }
)

# Both behaviors' on_open handlers are invoked:
# 1. cursed_items.on_open returns EventResult(allow=False, message="Dark energy prevents you from opening it!")
# 2. lockable_containers.on_open returns EventResult(allow=False, message="The chest is locked.")
# Combined result: EventResult(allow=False, message="Dark energy prevents you from opening it!\nThe chest is locked.")
```

This approach maximizes information to the player while keeping the implementation straightforward.

**Key insight:** Multiple behaviors per entity eliminates the need for entity behavior chaining. Game developers can add custom entity behaviors (like `magic_items.py`) alongside core behaviors (like `light_sources.py`) in the entity's `behaviors` list. Both behaviors run and their results combine, providing full customization without the complexity of a chaining mechanism. See "Entity-Specific Customization Without Handler Chaining" section for detailed examples.

### Design Rationale: Module Loading Error Handling

When loading behavior modules, various errors can occur due to developer mistakes. All such errors are **developer errors** that should be caught at load time and reported via stderr.

**Philosophy: Fail fast during development**

Module loading errors indicate bugs in behavior module code, not user errors or runtime conditions. The system should:
1. **Detect errors at load time** - catch problems before handlers are invoked
2. **Report via stderr** - technical details for developers, not end users
3. **Fail loudly** - make errors impossible to ignore during development
4. **Provide actionable messages** - clearly explain what's wrong and how to fix it

**Error categories and handling:**

1. **Module syntax errors** (Python SyntaxError):
   - Cause: Invalid Python syntax in behavior module file
   - Detection: Caught during `import` or `importlib.import_module()`
   - Handling: Module loading code catches SyntaxError, logs to stderr with filename and line number
   - Example: `ERROR loading module behaviors.core.manipulation: SyntaxError: invalid syntax (manipulation.py, line 42)`

2. **Module import failures** (ImportError, ModuleNotFoundError):
   - Cause: Missing dependencies, broken import paths, circular imports
   - Detection: Caught during module import
   - Handling: Module loading code catches ImportError, logs to stderr with module name and missing dependency
   - Example: `ERROR loading module behaviors.custom.magic: ModuleNotFoundError: No module named 'behaviors.custom.spells'`

3. **Malformed vocabulary structure** (ValueError):
   - Cause: vocabulary not a dict, verbs not a list, missing required fields, wrong types
   - Detection: `_validate_vocabulary()` method checks structure and raises ValueError
   - Handling: Already specified in `load_module()` docstring - caller catches and logs to stderr
   - Example: `ERROR loading module behaviors.core.movement: Module 'movement': vocabulary['verbs'][2] missing required field 'word'`

4. **Handler/vocabulary conflicts** (ValueError):
   - Cause: Multiple handlers for same verb from same source type, same verb mapped to different events
   - Detection: `load_module()` checks for conflicts and raises ValueError
   - Handling: Already specified - caller catches and logs to stderr
   - Example: `ERROR loading module behaviors.custom.take_extended: Handler conflict for verb 'take': Multiple regular modules define handle_take: manipulation, take_extended`

5. **Handler function signature errors**:
   - Cause: Handler function doesn't accept required parameters (verb, args, state, behavior_manager)
   - Detection: **NOT checked at load time** - would require complex introspection and may have false positives
   - Handling: Deferred to runtime when handler is invoked - TypeError naturally occurs with clear traceback
   - Rationale: Python's dynamic typing means signature validation at load time is unreliable (decorators, *args, **kwargs, etc.). Runtime errors provide better debugging information with full call stack.

**Module loading code pattern:**

The code that loads behavior modules from the filesystem should follow this pattern:

```python
import sys
import importlib
import traceback

def load_behavior_modules(behavior_manager, base_path, source_type="regular"):
    """Load all behavior modules from directory tree."""
    for module_path in discover_modules(base_path):
        module_name = path_to_module_name(module_path)

        try:
            # Import the module (can raise SyntaxError, ImportError)
            module = importlib.import_module(module_name)

            # Load into behavior manager (can raise ValueError)
            behavior_manager.load_module(module, source_type=source_type)

        except SyntaxError as e:
            print(f"ERROR loading module {module_name}: SyntaxError: {e.msg} "
                  f"({e.filename}, line {e.lineno})", file=sys.stderr)
            # Continue loading other modules - don't abort entire load

        except (ImportError, ModuleNotFoundError) as e:
            print(f"ERROR loading module {module_name}: {type(e).__name__}: {e}",
                  file=sys.stderr)
            # Continue loading other modules

        except ValueError as e:
            # Vocabulary/conflict errors from load_module()
            print(f"ERROR loading module {module_name}: {e}", file=sys.stderr)
            # Continue loading other modules

        except Exception as e:
            # Catch-all for unexpected errors during module loading
            print(f"ERROR loading module {module_name}: Unexpected error during load:",
                  file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            # Continue loading other modules
```

**Key design decisions:**

1. **Continue loading after errors**: If one module fails, continue loading others. This allows developers to see all errors at once rather than fixing one at a time.

2. **No validation of handler signatures**: Attempting to validate function signatures at load time is error-prone and provides little value. Runtime TypeErrors give better debugging information.

3. **No validation of entity behavior event names**: Since entity behavior modules are loaded dynamically and may not all be loaded, we cannot validate that `event: "on_take"` in vocabulary corresponds to an actual `on_take` function in a behavior module. This is validated at runtime when events are invoked.

4. **stderr for all errors**: Module loading errors are always developer errors, never user errors. End users should never see module loading - it happens during game initialization, not in response to user actions.

5. **Technical error messages**: Since audience is developers, messages should include:
   - Full module name (`behaviors.core.manipulation`, not just `manipulation`)
   - Exception type and message
   - File and line number for syntax errors
   - Full context for ValueError messages from `load_module()`

**Testing approach:**

Phase 2a should include tests for error handling:

```python
def test_load_module_with_syntax_error():
    """Verify syntax errors are caught and reported."""
    # Create temp file with syntax error
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
        f.write("def handle_test(\n")  # Unclosed parenthesis
        f.flush()

        # Attempt to import - should raise SyntaxError
        with pytest.raises(SyntaxError):
            importlib.import_module(f.name)

def test_load_module_with_import_error():
    """Verify import errors are caught and reported."""
    # Create module that imports nonexistent module
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
        f.write("from nonexistent_module import something\n")
        f.flush()

        # Should raise ImportError
        with pytest.raises(ImportError):
            importlib.import_module(f.name)

def test_load_module_with_malformed_vocabulary():
    """Verify vocabulary validation catches structural errors."""
    behavior_manager = BehaviorManager()

    # Module with vocabulary that's not a dict
    module = types.ModuleType("test_module")
    module.vocabulary = "not a dict"  # Wrong type

    with pytest.raises(ValueError) as exc_info:
        behavior_manager.load_module(module)

    assert "vocabulary must be a dict" in str(exc_info.value)

def test_handler_signature_error_at_runtime():
    """Verify handler signature errors produce clear runtime errors."""
    behavior_manager = BehaviorManager()

    # Module with handler that has wrong signature
    module = types.ModuleType("test_module")
    def bad_handler():  # Missing required parameters
        return HandlerResult(success=True)
    module.handle_test = bad_handler

    # Load succeeds - no signature checking at load time
    behavior_manager.load_module(module)

    # Invoke handler - should raise TypeError
    with pytest.raises(TypeError) as exc_info:
        handler = behavior_manager.get_handler("test")
        handler("test", {}, state, behavior_manager)

    # Verify error message mentions missing parameters
    assert "missing" in str(exc_info.value).lower()
```

**Production considerations:**

In production, module loading happens once at game startup. If modules fail to load:
- Errors are logged to stderr (captured in server logs)
- Game may start with partial functionality (missing handlers)
- OR game startup can be aborted if critical modules fail (design choice)

The design does not mandate abort-on-error vs. continue-with-warnings. This is an implementation decision based on deployment requirements.

### Handler Registration

Handlers are discovered automatically when behavior modules are loaded. Any function named `handle_<verb>` in a behavior module is registered. Multiple handlers for the same verb create a stack, with later registrations taking precedence:

```python
# In behavior_manager.py
class BehaviorManager:
    def __init__(self):
        self._handlers = {}  # verb -> list of handlers (in load order)
        self._verb_events = {}  # verb -> event_name mapping
        self._handler_position_list = []  # List of handler positions tracking delegation chain
        self._module_sources = {}  # verb -> list of (module_name, source_type) for handler conflict detection
        self._verb_event_sources = {}  # verb -> (event_name, module_name, source_type) for vocabulary conflict detection
        self._current_load_source = None  # Track current loading source (regular vs symlink)

    def load_module(self, module, source_type: str = "regular"):
        """
        Load a behavior module and register its handlers and vocabulary.

        Raises ValueError for developer errors (logged to stderr by caller):
        - Malformed vocabulary structure
        - Duplicate handler definitions
        - Duplicate vocabulary mappings

        Args:
            module: The module to load
            source_type: "regular" for local files, "symlink" for symlinked directories
        """
        self._current_load_source = source_type
        module_name = getattr(module, '__name__', str(module))

        # Validate vocabulary structure first (raises ValueError on error)
        self._validate_vocabulary(module, module_name)

        # Register handlers
        for name in dir(module):
            if name.startswith('handle_'):
                verb = name[7:]  # Remove 'handle_' prefix
                handler = getattr(module, name)

                # Track module source for conflict detection
                if verb not in self._module_sources:
                    self._module_sources[verb] = []
                self._module_sources[verb].append((module_name, source_type))

                # Detect conflicts: multiple handlers from same source type
                same_source_modules = [
                    mod_name for mod_name, src_type in self._module_sources[verb]
                    if src_type == source_type
                ]
                if len(same_source_modules) > 1:
                    conflict_list = ", ".join(same_source_modules)
                    raise ValueError(
                        f"Handler conflict for verb '{verb}': Multiple {source_type} modules define "
                        f"handle_{verb}: {conflict_list}. "
                        f"Each verb should be defined in only one module per source type. "
                        f"To override, use handler chaining instead of duplicate definitions."
                    )

                # Append to end of list (loaded in order)
                if verb not in self._handlers:
                    self._handlers[verb] = []
                self._handlers[verb].append(handler)

        # Register verb-to-event mappings from vocabulary
        if hasattr(module, 'vocabulary') and 'verbs' in module.vocabulary:
            for verb_spec in module.vocabulary['verbs']:
                verb = verb_spec['word']
                if 'event' in verb_spec:
                    event_name = verb_spec['event']

                    # Detect vocabulary conflicts: same verb with different events
                    if verb in self._verb_event_sources:
                        existing_event, existing_module, existing_source = self._verb_event_sources[verb]

                        # Different event = always conflict (regardless of source type)
                        if existing_event != event_name:
                            raise ValueError(
                                f"Vocabulary conflict for verb '{verb}': "
                                f"Module '{module_name}' ({source_type}) maps to event '{event_name}' but "
                                f"module '{existing_module}' ({existing_source}) maps to event '{existing_event}'. "
                                f"Cannot have same verb map to different events. "
                                f"If you need different behavior, use entity behaviors or handler chaining."
                            )

                    # Register the mapping
                    self._verb_events[verb] = event_name
                    self._verb_event_sources[verb] = (event_name, module_name, source_type)

                # Also map synonyms to the same event
                for synonym in verb_spec.get('synonyms', []):
                    if 'event' in verb_spec:
                        event_name = verb_spec['event']

                        # Detect synonym conflicts
                        if synonym in self._verb_event_sources:
                            existing_event, existing_module, existing_source = self._verb_event_sources[synonym]

                            # Different event = always conflict (regardless of source type)
                            if existing_event != event_name:
                                raise ValueError(
                                    f"Vocabulary conflict for synonym '{synonym}': "
                                    f"Module '{module_name}' ({source_type}) maps to event '{event_name}' but "
                                    f"module '{existing_module}' ({existing_source}) maps to event '{existing_event}'. "
                                    f"Cannot have same verb/synonym map to different events. "
                                    f"If you need different behavior, use entity behaviors or handler chaining."
                                )

                        self._verb_events[synonym] = event_name
                        self._verb_event_sources[synonym] = (event_name, module_name, source_type)

    def _validate_vocabulary(self, module, module_name: str):
        """
        Validate vocabulary structure and provide helpful error messages.

        Validates structure and types to catch common developer mistakes:
        - vocabulary is not a dict
        - 'verbs' is not a list
        - Missing required 'word' field
        - Wrong types for fields (word, synonyms, event, object_required)
        - Empty strings for string fields

        Does NOT validate semantic/runtime constraints (these cannot be checked at load time):
        - Event function existence → cannot validate (event="on_take" might not have corresponding function)
        - Verb without event mapping → valid (verb may not trigger entity behaviors, e.g., "quit")
        - Multiple verbs mapping to same event → valid (synonyms like "take"/"grab" both → "on_take")
        - Handler function signatures → cannot validate reliably (Python's dynamic typing)
        - Vocabulary without handler → valid (module may define vocab delegating to handler in another module)

        Note: If vocabulary is registered for a verb but no handle_<verb> function exists in any
        loaded module, invoking that verb will return HandlerResult(success=False, message="Unknown command: {verb}")

        Does validate semantic conflicts (these ARE errors):
        - Same verb mapping to different events → ValueError (regardless of source type)
        - Same synonym mapping to different events → ValueError (regardless of source type)

        Raises ValueError with descriptive message if validation fails.
        """
        if not hasattr(module, 'vocabulary'):
            return  # No vocabulary is fine

        vocab = module.vocabulary

        # Check top-level structure
        if not isinstance(vocab, dict):
            raise ValueError(
                f"Module '{module_name}': vocabulary must be a dict, got {type(vocab).__name__}"
            )

        if 'verbs' not in vocab:
            return  # No verbs is fine (maybe only entity behaviors)

        if not isinstance(vocab['verbs'], list):
            raise ValueError(
                f"Module '{module_name}': vocabulary['verbs'] must be a list, got {type(vocab['verbs']).__name__}"
            )

        # Check each verb spec
        for i, verb_spec in enumerate(vocab['verbs']):
            if not isinstance(verb_spec, dict):
                raise ValueError(
                    f"Module '{module_name}': vocabulary['verbs'][{i}] must be a dict, got {type(verb_spec).__name__}"
                )

            # Required field
            if 'word' not in verb_spec:
                raise ValueError(
                    f"Module '{module_name}': vocabulary['verbs'][{i}] missing required field 'word'"
                )

            word = verb_spec['word']
            if not isinstance(word, str) or not word:
                raise ValueError(
                    f"Module '{module_name}': vocabulary['verbs'][{i}]['word'] must be a non-empty string"
                )

            # Optional fields with type checking
            if 'synonyms' in verb_spec:
                if not isinstance(verb_spec['synonyms'], list):
                    raise ValueError(
                        f"Module '{module_name}': verb '{word}' synonyms must be a list, got {type(verb_spec['synonyms']).__name__}"
                    )
                for j, synonym in enumerate(verb_spec['synonyms']):
                    if not isinstance(synonym, str) or not synonym:
                        raise ValueError(
                            f"Module '{module_name}': verb '{word}' synonyms[{j}] must be a non-empty string"
                        )

            if 'event' in verb_spec:
                if not isinstance(verb_spec['event'], str) or not verb_spec['event']:
                    raise ValueError(
                        f"Module '{module_name}': verb '{word}' event must be a non-empty string"
                    )

            if 'object_required' in verb_spec and not isinstance(verb_spec['object_required'], bool):
                raise ValueError(
                    f"Module '{module_name}': verb '{word}' object_required must be a bool, got {type(verb_spec['object_required']).__name__}"
                )

    def get_handler(self, verb: str):
        """Get the first loaded handler for a verb (game-specific code)."""
        handlers = self._handlers.get(verb, [])
        return handlers[0] if handlers else None

    def invoke_handler(self, verb: str, accessor, action: Dict) -> HandlerResult:
        """
        Invoke the handler chain for a verb, managing the position list lifecycle.

        This method owns the complete lifecycle of the position list, ensuring it's
        always properly initialized and cleaned up even if handlers raise exceptions.

        Args:
            verb: The command verb
            accessor: StateAccessor instance
            action: The action dict

        Returns:
            HandlerResult from handler
        """
        handler = self.get_handler(verb)
        if not handler:
            return HandlerResult(success=False, message=f"Unknown command: {verb}")

        # Initialize position list for this command invocation
        self._handler_position_list = [0]
        try:
            # Call first handler - it may delegate via invoke_previous_handler()
            return handler(accessor, action)
        finally:
            # Always clean up position list, even if handler raised exception
            self._handler_position_list = []

    def get_event_for_verb(self, verb: str) -> Optional[str]:
        """
        Get the event name associated with a verb.

        Each verb maps to exactly one event name. Multiple modules cannot map
        the same verb to different events - the vocabulary conflict detection
        ensures this at module load time.

        Args:
            verb: The action verb (e.g., "take", "get", "grab")

        Returns:
            Event name (e.g., "on_take") or None if no event is defined
        """
        return self._verb_events.get(verb)

    def invoke_previous_handler(self, verb: str, accessor, action: Dict) -> HandlerResult:
        """
        Invoke the next handler in the load order (toward core).

        Uses an instance variable list to track the current position in the handler chain,
        allowing proper delegation through game → library → core layers. The position list
        grows and shrinks as we walk down and back up the static handler list.

        Note: This implementation assumes single-threaded execution. The position list is
        managed by invoke_handler() and is transparent to game developers.

        Args:
            verb: The command verb
            accessor: StateAccessor instance
            action: The action dict

        Returns:
            HandlerResult from handler
        """
        handlers = self._handlers.get(verb, [])
        if len(handlers) <= 1:
            return HandlerResult(success=False, message=f"No previous handler for {verb}")

        # Get current position from list
        if not self._handler_position_list:
            # Should never happen - invoke_handler() initializes this
            raise RuntimeError(
                "Handler position list not initialized. "
                "Handlers should be invoked via BehaviorManager.invoke_handler(), not called directly."
            )

        current_position = self._handler_position_list[-1]
        next_position = current_position + 1

        if next_position >= len(handlers):
            return HandlerResult(success=False, message=f"No more handlers in chain for {verb}")

        # Add next position to list and call handler
        self._handler_position_list.append(next_position)
        try:
            next_handler = handlers[next_position]
            return next_handler(accessor, action)
        finally:
            # Remove position when handler returns
            self._handler_position_list.pop()
```

### Entity Behaviors

Entity behaviors are event handler functions that respond to actions on specific entities. They are distinct from command handlers.

**Motivation: Why both `handle_*` and `on_*`?**

These two constructs serve fundamentally different purposes:

- **`handle_<verb>`** (Command Handlers): Implement game logic for *commands*
  - Purpose: Parse player intent, find entities, validate preconditions, orchestrate state changes
  - Scope: Global - one handler per verb applies to all uses of that command
  - Returns: `HandlerResult(success: bool, message: str)` - final result to show the player
  - Example: `handle_take` finds the item, checks if portable, updates item location and actor inventory
  - Question answered: "How does the TAKE command work in this game?"

- **`on_<event>`** (Entity Behaviors): Define entity-specific reactions to *events*
  - Purpose: Allow/deny actions based on entity-specific state, provide custom messages
  - Scope: Per-entity - only invoked for entities that reference this behavior module
  - Returns: `EventResult(allow: bool, message: Optional[str])` - permission and explanation
  - Example: `on_take` checks if a specific item is cursed and prevents pickup if so
  - Question answered: "What happens when someone tries to take THIS particular item?"

**Command Handler Signature:**

Command handlers must follow this signature:

```python
def handle_<verb>(accessor: StateAccessor, action: Dict[str, Any]) -> HandlerResult:
    """
    Handle a command.

    Args:
        accessor: StateAccessor for querying/modifying state and invoking behaviors
        action: Dict containing:
            - actor_id: str - ID of actor performing command (default "player")
            - object: str - Primary target of command (item/actor/direction name)
            - indirect_object: str - Secondary target (for commands like PUT X IN Y)
            - Additional action-specific fields

    Returns:
        HandlerResult with success=True/False and message to display to player
    """
    pass
```

**Why this separation?**

Without entity behaviors, command handlers would need to contain all entity-specific logic:

```python
# Without entity behaviors - game logic pollutes handler
def handle_take(accessor, action):
    item = find_accessible_item(accessor, action.get("object"))

    # Handler now contains cursed item logic
    if item.id == "cursed_sword" and item.states.get("cursed"):
        return HandlerResult(success=False, message="The sword burns your hand! You can't pick it up.")

    # Handler contains locked container logic
    if item.properties.get("container") and item.properties.get("locked"):
        return HandlerResult(success=False, message=f"The {item.name} is locked.")

    # ... hundreds more special cases ...

    # Finally, the actual generic take logic
    result = accessor.update(entity=item, changes={"location": actor_id})
```

With entity behaviors, handlers stay generic and entities control their own behavior:

```python
# With entity behaviors - handler stays clean
def handle_take(accessor, action):
    item = find_accessible_item(accessor, action.get("object"))
    # Entity-specific behavior is checked automatically
    result = accessor.update(entity=item, changes={"location": actor_id}, verb="take")
    # Entity's on_take decides if this is allowed
```

This separation enables:
1. **Reusable command handlers** - `handle_take` doesn't change as new item types are added
2. **Composable entity behaviors** - An item can have both "lockable" and "cursed" behaviors
3. **Data-driven content** - Designers add new entity behaviors without modifying engine code

**Entity Behavior Registration:**

**All entities support behaviors.** Each entity dataclass has a `behaviors` field that lists the behavior modules it uses:

```python
@dataclass
class Item:
    id: str
    name: str
    behaviors: List[str] = field(default_factory=list)  # Module names
    # ... other fields

@dataclass
class Actor:
    id: str
    name: str
    behaviors: List[str] = field(default_factory=list)  # Module names
    location: str
    inventory: List[str] = field(default_factory=list)  # Must be initialized, never None
    # ... other fields

@dataclass
class Location:
    id: str
    name: str
    behaviors: List[str] = field(default_factory=list)  # Module names
    description: str
    exits: Dict[str, ExitDescription]
    # ... other fields

@dataclass
class Door:
    id: str
    behaviors: List[str] = field(default_factory=list)  # Module names
    # ... other fields

@dataclass
class Lock:
    id: str
    behaviors: List[str] = field(default_factory=list)  # Module names
    # ... other fields
```

**Rationale:** All entity types support behaviors to enable maximum flexibility. While Items are the most common use case for behaviors (e.g., cursed items, lockable containers), other entity types can benefit:
- **Actors:** Could have behaviors for special abilities, status effects, AI personalities
- **Locations:** Could have behaviors for traps (`on_enter`), magical effects, environmental hazards
- **Doors:** Could have behaviors for special unlocking mechanisms, magical wards
- **Locks:** Could have behaviors for puzzle locks, time-based locks

The `behaviors` field defaults to an empty list, so entities without custom behaviors simply have `behaviors=[]` with no runtime cost.

Example entity definition:
```python
chest = Item(
    id="item_chest",
    name="wooden chest",
    behaviors=["lockable_containers"],  # References behavior module
    properties={
        "container": {"open": False},
        "lock_id": "lock_chest_01"
    }
)
```

**Entity Behavior Functions:**

Behavior modules can define entity behavior event handlers alongside command handlers. These functions must follow this signature:

```python
def on_<event>(entity, accessor: StateAccessor, context: dict) -> EventResult:
    """
    Handle an entity behavior event.

    Args:
        entity: The entity object (Item, Actor, Location, etc.)
        accessor: StateAccessor for querying/modifying state
        context: Dict containing:
            - actor_id: str - ID of actor performing the action
            - changes: Dict[str, Any] - Proposed state changes
            - verb: str - The action verb that triggered this event

    Returns:
        EventResult with allow=True/False and optional message.

        The message field can be used for both success and failure:
        - allow=False, message="...": Denies action with explanation
        - allow=True, message="...": Allows action with custom feedback
        - allow=True, message=None: Allows action, handler uses default message
    """
    pass
```

**BehaviorManager.invoke_behavior():**

The BehaviorManager must implement `invoke_behavior()` to find and call entity behaviors:

```python
class BehaviorManager:
    def __init__(self):
        self._handlers = {}  # verb -> list of handlers (in load order)
        self._verb_events = {}  # verb -> event_name mapping
        self._modules = {}  # module_name -> loaded module object

    def load_module(self, module):
        """Load a behavior module and register its handlers and vocabulary."""
        # ... existing handler registration code ...

        # Store module reference for entity behavior lookup
        if hasattr(module, '__name__'):
            self._modules[module.__name__] = module

    def invoke_behavior(self, entity, event_name: str, accessor, context: dict) -> Optional[EventResult]:
        """
        Invoke entity behavior event handlers for all matching behaviors.

        If entity has multiple behaviors that define the same event (e.g., both
        "lockable" and "cursed" define on_take), ALL matching behaviors are invoked
        in the order listed in entity.behaviors.

        Results are combined using AND logic:
        - If ANY behavior returns allow=False, the final result is allow=False
        - All messages are collected and combined (newline-separated)
        - This allows multiple constraints to apply and gives player full feedback

        Args:
            entity: Entity with behaviors field
            event_name: Event name (e.g., "on_take", "on_open")
            accessor: StateAccessor instance
            context: Context dict for behavior

        Returns:
            Combined EventResult from all matching behaviors, or None if:
            - entity.behaviors is empty (no behaviors to invoke)
            - No behavior modules matched (e.g., modules not loaded)
            - No behaviors define the requested event
        """
        # All entities have behaviors field (may be empty list)
        if not entity.behaviors:
            return None

        results = []

        # Invoke ALL matching behaviors (not just first)
        for behavior_module_name in entity.behaviors:
            if behavior_module_name not in self._modules:
                # Warn about missing module (helps catch typos and loading issues)
                import sys
                print(f"WARNING: Entity {entity.id} references behavior module '{behavior_module_name}' which is not loaded", file=sys.stderr)
                continue

            module = self._modules[behavior_module_name]
            if hasattr(module, event_name):
                handler = getattr(module, event_name)
                result = handler(entity, accessor, context)
                if result:
                    results.append(result)

        if not results:
            return None

        # Combine results: all must allow (AND logic)
        final_allow = all(r.allow for r in results)

        # Combine messages from all behaviors
        messages = [r.message for r in results if r.message]
        final_message = "\n".join(messages) if messages else None

        return EventResult(allow=final_allow, message=final_message)
```

**Example:**

```python
# In lockable_containers.py behavior module

# Entity behavior - responds to events on entities
def on_open(entity, accessor, context):
    """Check if container is locked before allowing open."""
    lock_id = entity.properties.get("lock_id")
    if not lock_id:
        return EventResult(allow=True)

    lock = accessor.get_lock(lock_id)
    if lock and lock.locked:
        key_hint = lock.properties.get("key_hint", "a key")
        return EventResult(
            allow=False,
            message=f"The {entity.name} is locked. Perhaps {key_hint} would help."
        )
    return EventResult(allow=True)

# Command handler - processes user commands
def handle_open(accessor, action):
    """Handle open command."""
    # ... find container, check conditions ...
    result = accessor.update(
        entity=container,
        changes={"properties.container.open": True},
        verb="open",
        actor_id=actor_id
    )
    # ... return result
```

**Example with success message:**

```python
# In light_sources.py behavior module

# Entity behavior that provides flavor text on success
def on_take(entity, accessor, context):
    """Magic lantern lights itself when taken."""
    # Allow the action but provide custom message
    if not entity.states.get("lit"):
        entity.states["lit"] = True
        return EventResult(
            allow=True,
            message=f"You take the {entity.name}. Its runes flare to life, casting a warm glow."
        )
    return EventResult(
        allow=True,
        message=f"You take the {entity.name}."
    )

# Command handler
def handle_take(accessor, action):
    """Handle take command."""
    # ... find item, check portable ...
    result = accessor.update(
        entity=item,
        changes={"location": actor_id},
        verb="take",
        actor_id=actor_id
    )

    if not result.success:
        return HandlerResult(success=False, message=result.message or "You can't take that.")

    # Use behavior's message if provided, otherwise use default
    return HandlerResult(success=True, message=result.message or f"You take the {item.name}.")
```

When `accessor.update(entity=chest, verb="open")` is called:
1. StateAccessor looks up "open" → "on_open" via vocabulary
2. StateAccessor calls `behavior_manager.invoke_behavior(chest, "on_open", accessor, context)`
3. BehaviorManager finds "lockable_containers" in `chest.behaviors`
4. BehaviorManager calls `lockable_containers.on_open(chest, accessor, context)`
5. The `on_open` function returns EventResult(allow=True/False)

### Vocabulary and Event Mapping

Behavior modules define vocabularies that specify both command verbs and their associated events. The BehaviorManager automatically registers these mappings when loading modules.

**Terminology Note:** This document uses two distinct terms:
- **verb**: A command word that players type (e.g., "take", "open", "attack")
- **event**: An entity behavior hook that responds to actions (e.g., "on_take", "on_open", "on_attacked")

Command handlers pass verbs to `update()`, which looks up the corresponding event name via vocabulary and invokes the appropriate entity behavior (if any).

**Motivation:** This indirection solves a coupling problem. Without it, command handlers must hardcode entity behavior event names (e.g., `event="on_take"`), which means:
- Handlers contain game-semantic knowledge they shouldn't have
- Multiple verbs requiring the same entity response (e.g., "attack" and "stab" both triggering armor checks) must duplicate the event name
- Changing an event name requires finding and updating all handler call sites

By putting the verb-to-event mapping in vocabulary definitions, handlers only know about commands ("take", "open"), entity behaviors only know about semantic events ("on_take", "on_attacked"), and the vocabulary provides the bridge between them.

**Key points:**
- The `event` field in vocabulary specifications maps verbs to entity behavior events
- All synonyms of a verb map to the same event (e.g., "take", "get", "grab" → "on_take")
- Multiple different verbs can map to the same event if semantically appropriate
- Handlers pass the verb to `accessor.update()`, which looks up the event name automatically
- This decouples handlers from entity behavior event names

**Example with multiple verbs mapping to same event:**

```python
# In a combat behavior module
vocabulary = {
    "verbs": [
        {
            "word": "attack",
            "synonyms": ["hit", "strike"],
            "object_required": True,
            "event": "on_attacked"  # Entity receives attack
        },
        {
            "word": "stab",
            "synonyms": ["pierce"],
            "object_required": True,
            "event": "on_attacked"  # Also uses on_attacked
        }
    ]
}

def handle_attack(accessor, action):
    # ... combat logic ...
    result = accessor.update(
        entity=target,
        changes={"properties.health": new_health},
        verb="attack",  # Maps to "on_attacked" event
        actor_id=actor_id
    )

def handle_stab(accessor, action):
    # ... different damage calculation ...
    result = accessor.update(
        entity=target,
        changes={"properties.health": new_health},
        verb="stab",  # Also maps to "on_attacked" event
        actor_id=actor_id
    )
```

The entity behavior responds to "on_attacked" regardless of which verb was used:

```python
def on_attacked(entity, accessor, context):
    if entity.properties.get("armored"):
        return EventResult(
            allow=False,
            message=f"The {entity.name}'s armor deflects the blow!"
        )
    return EventResult(allow=True)
```

### Module Loading Order

Modules are discovered by walking the behaviors directory tree. Handlers are appended to a list in load order. The first loaded handler is called first.

**Loading order rules:**
1. Regular files and directories are loaded first (marked as source_type="regular")
2. Symlinked directories are loaded last (marked as source_type="symlink")

**Conflict Detection:** The BehaviorManager has different conflict rules for handlers vs. vocabulary:

**Handler conflicts (source-type-aware):**
- Multiple modules of the same source type defining the same handler → ValueError
- Regular module + symlink module defining the same handler → Allowed (enables handler chaining)
- Example error: If both `manipulation.py` and `extended_manipulation.py` (both regular files) define `handle_take`:
  ```
  ValueError: Handler conflict for verb 'take': Multiple regular modules define handle_take:
  manipulation, extended_manipulation. Each verb should be defined in only one module per source type.
  To override, use handler chaining instead of duplicate definitions.
  ```

**Vocabulary conflicts (always error):**
- Any two modules mapping the same verb to different events → ValueError (regardless of source type)
- This prevents silent overrides where a library could change the event mapping defined by game code
- Example error: If `my_custom.py` maps "take"→"on_grab" and `core/manipulation.py` maps "take"→"on_take":
  ```
  ValueError: Vocabulary conflict for verb 'take': Module 'core.manipulation' (symlink) maps to event 'on_take'
  but module 'my_custom' (regular) maps to event 'on_grab'. Cannot have same verb map to different events.
  ```

**Rationale:** Handler chaining allows extending behavior while vocabulary mappings must be consistent to prevent confusion about which entity events are triggered.

This ensures that:
- Game developer's current work (regular files/directories in local behaviors/) loads first and is appended to the handler list at position 0, 1, 2...
- Symlinked behavior directories (e.g., from shared libraries or core) load last and are appended after local modules
- `get_handler()` returns the first item in the list (position 0 = game-specific code)
- `invoke_previous_handler()` walks forward through the list (position 1, 2, 3...), allowing game code to delegate to symlinked libraries and eventually to core
- The delegation chain flows: game-specific work → symlinked behaviors → core, corresponding to positions 0 → 1 → 2 in the handler list

### Handler Override and Command Handler Chaining

Game developers write their custom behaviors as regular files in their local `behaviors/` directory. These are loaded first and called first, allowing them to delegate to symlinked libraries and core using `accessor.invoke_previous_handler()`.

**When is command handler chaining needed?**

Handler chaining is for modifying **command logic** itself - the general rules for how a command works across all entities. For example:
- Adding weight limits to the `take` command
- Adding stamina costs to the `go` command
- Adding skill checks to the `unlock` command

**When is handler chaining NOT needed?**

For **entity-specific behaviors**, use the entity behavior system instead of handler chaining. For example:
- A magic lantern that glows when taken → entity behavior (`on_take` in `magic_items.py`)
- A cursed sword that can't be dropped → entity behavior (`on_drop` in `cursed_items.py`)
- A locked chest that requires a key → entity behavior (`on_open` in `lockable_containers.py`)

**Example use case: Adding weight limits to all take commands**

Without handler chaining, you'd need to modify the core `handle_take` directly. With chaining, you can add weight checking while delegating the actual take logic to core:

```python
# In behaviors/extended_manipulation.py (local regular file, loaded last)
from behaviors.core.utils import find_accessible_item

def handle_take(accessor, action):
    """Extended take with weight limit checking."""
    actor_id = action.get("actor_id", "player")
    item_name = action.get("object")

    item = find_accessible_item(accessor, item_name, actor_id)
    if item:
        actor = accessor.get_actor(actor_id)
        if not actor:
            return HandlerResult(success=False, message="Actor not found.")

        current_weight = calculate_inventory_weight(accessor, actor)
        item_weight = item.properties.get("weight", 0)
        max_weight = actor.properties.get("max_carry_weight", 100)

        if current_weight + item_weight > max_weight:
            return HandlerResult(success=False, message="That would be too heavy to carry.")

    # Delegate to previous handler (from symlinked library or core)
    return accessor.invoke_previous_handler("take", action)

def calculate_inventory_weight(accessor, actor):
    """Helper to sum weight of all items in inventory."""
    if not actor:
        return 0

    total = 0
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item:
            total += item.properties.get("weight", 0)
    return total
```

**Directory structure example:**
```
my_game/
  behaviors/
    extended_manipulation.py      # Game-specific (regular file, loads first)
    core -> /usr/share/game-engine/behaviors/  # Symlink to core (loads last)
```

With this structure:
1. `extended_manipulation.py` (regular file) loads first → handler appended at position 0
2. `core/` (symlink) loads last → handler appended at position 1

When a command runs:
- `get_handler()` returns position 0 → `extended_manipulation.py` is called first
- If it calls `invoke_previous_handler()`, that returns position 1 → `core/` handler

This gives game developers the first opportunity to handle commands, with core as the delegation target.

### Entity-Specific Customization Without Handler Chaining

**Use case: Magic lantern that glows with arcane energy when taken**

Entity-specific behaviors should use the entity behavior system, not command handler chaining. The game developer creates a new behavior module for magic items and adds it to the entity's behaviors list alongside core behaviors.

**Solution: Use multiple behaviors**

```python
# In behaviors/magic_items.py (game-specific behavior module)
from src.state_accessor import EventResult

def on_take(entity, accessor, context):
    """Magic items glow when taken."""
    if entity.properties.get("magic_type") == "arcane":
        # Set the glow state
        entity.states["glowing"] = True
        return EventResult(
            allow=True,
            message="The lantern pulses with arcane energy as you pick it up!"
        )
    return EventResult(allow=True)

# Entity definition
magic_lantern = Item(
    id="magic_lantern",
    name="magic lantern",
    behaviors=["light_sources", "magic_items"],  # Multiple behaviors!
    properties={"magic_type": "arcane"},
    states={"lit": False, "glowing": False}
)
```

When the player takes the magic lantern:
1. Core's `handle_take` runs (finds item, validates, etc.)
2. `accessor.update()` is called with `event="on_take"`
3. BehaviorManager invokes ALL behaviors: `light_sources.on_take` AND `magic_items.on_take`
4. Both behaviors' messages are combined and shown to the player

**Result:**
```
> take lantern
The lantern's runes flare to life as you pick it up.
The lantern pulses with arcane energy as you pick it up!
```

**Why this is better than handler chaining:**
- No need to override core `handle_take` command logic
- Magic behavior is modular and reusable (any item can have `magic_items` behavior)
- Core `light_sources` behavior still works unchanged
- Multiple behaviors compose naturally via the multiple-behaviors mechanism

**Alternative: Use entity properties for simple variations**

If the variation is simple, use entity properties instead of a separate module:

```python
# In core's light_sources.py
def on_take(entity, accessor, context):
    """Light sources activate when taken."""
    if entity.states.get("lit"):
        return EventResult(allow=True)  # Already lit

    # Check for magic variant
    magic_type = entity.properties.get("magic_type")
    if magic_type == "arcane":
        entity.states["lit"] = True
        return EventResult(
            allow=True,
            message="The lantern pulses with arcane energy and lights itself!"
        )

    # Normal lighting behavior
    entity.states["lit"] = True
    return EventResult(
        allow=True,
        message="The lantern's runes flare to life as you pick it up."
    )
```

This keeps all lighting logic in one place while allowing entity-specific variations through properties.

### Handler Chaining Implementation

The `invoke_previous_handler()` mechanism uses a simple instance variable list to track the current position in the handler chain. This allows proper delegation through multi-layer chains (game → library → core).

**Note:** This implementation assumes single-threaded execution. The position tracking is managed entirely by the infrastructure (BehaviorManager and llm_protocol) and is transparent to game developers.

**How it works:**

1. When a command is dispatched, `llm_protocol.py` initializes the position list and adds position 0
2. The first handler (position 0, game code) is called
3. If that handler calls `invoke_previous_handler()`:
   - The current position (0) is read from the position list
   - Next position (1) is calculated
   - Position 1 is added to the position list
   - Handler at position 1 is called
   - When it returns, position 1 is removed from the list
4. If the position 1 handler also calls `invoke_previous_handler()`:
   - Current position (1) is read from the position list
   - Next position (2) is calculated
   - Position 2 is added to the position list
   - Handler at position 2 is called
   - When it returns, position 2 is removed from the list
5. The position list shrinks as each handler returns

**Example chain execution:**

```
handlers = [game_handler, library_handler, core_handler]  # positions 0, 1, 2

Command dispatch:
  position_list: [0]
  → game_handler() called
    → calls invoke_previous_handler()
      position_list: [0, 1]
      → library_handler() called
        → calls invoke_previous_handler()
          position_list: [0, 1, 2]
          → core_handler() called
            → returns result
          position_list: [0, 1]
        → returns result
      position_list: [0]
    → returns result
  position_list: []
```


## Implementation

See [behavior_refactoring_implementation.md](behavior_refactoring_implementation.md) for:
- Module organization and file structure
- Shared utilities and helper functions
- Code examples (llm_protocol.py, manipulation.py)
- Complete migration path with step-by-step phases
- Handler migration map (which functions move where)

## Testing

See [behavior_refactoring_testing.md](behavior_refactoring_testing.md) for comprehensive testing strategy, test setup utilities, and test specifications.

**Key testing requirements:**
- Write tests before implementing handlers
- Test both player and NPC actors for all manipulation commands
- Verify handler load order and delegation chains
- Test multiple behaviors per entity
- No mocking required - tests use real GameState objects

The StateAccessor design enables straightforward testing without mocks. Tests verify both handler return values and actual state changes.


## Benefits

1. **Extensibility**: Override `handle_take` without modifying engine
2. **Organization**: Related code in one module (vocab + handler)
3. **Testability**: Handlers tested with real StateAccessor, no mocks needed
4. **Consistency**: All commands and queries follow same pattern
5. **Clean separation**: llm_protocol.py has no game knowledge - pure infrastructure for routing and JSON serialization
6. **Future-proofing**: Ready for NPC AI with actor_id parameter
7. **Simple error flow**: Handlers return HandlerResult with success and message, no separate error tracking
8. **Customizable visibility**: Games can override visibility rules without touching infrastructure code

## Query Handling

**Motivation:** Query handlers (location, inventory, entities) currently contain game-specific logic embedded in llm_protocol.py. This violates Goal #3 (make llm_protocol.py pure infrastructure with no game-specific knowledge). Like command handlers, queries need to use game-specific visibility and access rules that belong in behavior modules.

**Solution:** Query handlers in llm_protocol.py become thin wrappers that:
1. Call utility functions from behavior modules (e.g., `get_visible_items_in_location()`)
2. Serialize the results to JSON using `_entity_to_dict()` helpers
3. Contain no game logic about what is visible, accessible, or how containers work

**Example refactoring of `_query_location`:**

```python
# In llm_protocol.py - pure infrastructure, no game logic
def _query_location(self, message: Dict) -> Dict:
    """Query current location."""
    from behaviors.core.visibility import get_visible_items_in_location, get_visible_actors_in_location
    from behaviors.core.visibility import get_doors_in_location

    accessor = StateAccessor(self.state, self.behavior_manager)
    actor_id = message.get("actor_id", "player")  # Extract actor_id from message
    loc = accessor.get_current_location(actor_id)
    include = message.get("include", [])

    data = {"location": self._location_to_dict(loc)}

    if "items" in include or not include:
        items = get_visible_items_in_location(accessor, loc.id, actor_id)
        data["items"] = [self._entity_to_dict(item) for item in items]

    if "doors" in include or not include:
        doors = get_doors_in_location(accessor, loc.id, actor_id)
        data["doors"] = [self._door_to_dict(door) for door in doors]

    if "exits" in include or not include:
        data["exits"] = {
            direction: {"type": exit_desc.type, "to": exit_desc.to}
            for direction, exit_desc in loc.exits.items()
        }

    if "actors" in include or not include:
        actors = get_visible_actors_in_location(accessor, loc.id, actor_id)
        data["actors"] = [self._actor_to_dict(actor) for actor in actors]

    return {
        "type": "query_response",
        "query_type": "location",
        "data": data
    }
```

```python
# In utilities/utils.py - game-specific visibility rules
def get_visible_items_in_location(accessor: StateAccessor, location_id: str, actor_id: str = "player") -> List[Item]:
    """
    Get items visible in a location according to game visibility rules.

    Includes:
    - Items directly in the location
    - Items in/on accessible containers (surface containers, open enclosed containers)

    Scope and depth limitations:
    - **One level of nesting only**: Shows items IN containers at the location, but not
      items in containers within containers (e.g., shows box on table and box's contents
      if open, but not contents of a smaller box inside the first box)
    - **Location containers only**: Only checks containers in the location itself, not
      containers in the actor's inventory (use separate inventory query for that)
    - **Rationale**: Prevents infinite recursion with nested containers, matches "look
      around the room" semantics (inventory queries use separate function)

    Game-specific behavior: Different games can customize visibility by
    overriding this function (e.g., dark locations, fog, magical concealment).
    """
    visible_items = []

    # Items directly in location
    for item in accessor.get_items_in_location(location_id):
        visible_items.append(item)

    # Items in containers at this location
    for container in accessor.get_items_in_location(location_id):
        container_props = container.properties.get("container")
        if not container_props:
            continue

        # Surface containers: always show contents
        if container_props.get("is_surface", False):
            visible_items.extend(accessor.get_items_in_location(container.id))
        # Enclosed containers: only show if open
        elif container_props.get("open", False):
            visible_items.extend(accessor.get_items_in_location(container.id))

    return visible_items

def get_visible_actors_in_location(accessor: StateAccessor, location_id: str, actor_id: str = "player") -> List[Actor]:
    """
    Get actors visible in a location.

    Excludes the viewing actor themselves (an actor doesn't see themselves in the room).
    """
    all_actors = accessor.get_actors_in_location(location_id)
    return [actor for actor in all_actors if actor.id != actor_id]

def get_doors_in_location(
    accessor: StateAccessor,
    location_id: str = None,
    actor_id: str = "player"
) -> List[Tuple[Door, str]]:
    """
    Get doors accessible from a location, with their directions.

    This function applies game-specific visibility rules - different actors
    may perceive doors differently (e.g., a bat using sonar might detect
    hidden doors that a human cannot see).

    Args:
        accessor: StateAccessor instance
        location_id: Location ID (if None, uses actor's current location)
        actor_id: ID of the actor perceiving the doors (default "player")
                  IMPORTANT: When called from handlers, pass the actor_id variable from action

    Returns:
        List of (door, direction) tuples for doors accessible to this actor
        Direction may be None if door has no associated exit direction
    """
    if location_id is None:
        current_location = accessor.get_current_location(actor_id)
        if not current_location:
            return []  # No location = no doors
        location_id = current_location.id

    location = accessor.get_location(location_id)
    if not location:
        return []  # Location not found = no doors

    doors_with_direction = []

    for direction, exit_desc in location.exits.items():
        if exit_desc.door_id:
            door = accessor.get_door(exit_desc.door_id)
            if door:
                # Apply door visibility rules via behaviors (if any)
                if door.behaviors:
                    context = {"actor_id": actor_id, "location_id": location_id, "direction": direction}
                    visibility_result = accessor.behavior_manager.invoke_behavior(
                        door, "on_query_visibility", accessor, context
                    )
                    if visibility_result and not visibility_result.allow:
                        continue  # Door is hidden from this actor

                doors_with_direction.append((door, direction))

    return doors_with_direction
```

**Example: Adding hidden doors**

A developer can add hidden door functionality by creating a behavior module:

```python
# In behaviors/hidden_doors.py

def on_query_visibility(door, accessor, context):
    """Hide doors from actors without detection ability."""
    actor_id = context.get("actor_id")
    actor = accessor.get_actor(actor_id)
    if not actor:
        # No actor = show door by default (shouldn't happen in practice)
        return EventResult(allow=True)

    # Check if door is marked as hidden
    if door.properties.get("hidden", False):
        # Check if actor has ability to detect hidden doors
        if not actor.properties.get("detect_hidden", False):
            return EventResult(allow=False)  # Don't show this door

    return EventResult(allow=True)  # Show the door
```

Then reference the behavior in the door definition:

```python
secret_door = Door(
    id="secret_door_north",
    locations=("hall", "secret_room"),
    behaviors=["hidden_doors"],
    properties={"hidden": True, "description": "A concealed door in the wall"}
)
```

The door will only appear in queries and the "look" command output for actors with `detect_hidden` property set to True.

**How this works:**
1. Player types "look" → `handle_look()` in `behaviors/core/perception.py` is invoked
2. `handle_look()` calls `get_doors_in_location(accessor, location_id, actor_id)` to get visible doors
3. `get_doors_in_location()` iterates through doors and invokes `on_query_visibility` behavior for each
4. Hidden doors behavior returns `allow=False` for actors without `detect_hidden`, so door is filtered out
5. Only non-hidden doors (or doors visible to this actor) are included in the response

This same mechanism works for:
- The "look" command (text mode via `handle_look`)
- Location queries (LLM mode via `_query_location` in llm_protocol)
- Any other code that calls `get_doors_in_location()`

No modification to core code needed - just add the behavior module and reference it in door definitions.

**Key differences from commands:**
- Queries use StateAccessor's read-only methods (`get_item`, `get_items_in_location`, etc.)
- Queries never call `accessor.update()` - no state modification
- Query utility functions can be shared across multiple query handlers
- Game-specific visibility logic lives in behavior modules, not llm_protocol.py

**Other query handlers:** `_query_inventory`, `_query_entity`, `_query_entities` follow the same pattern - thin wrappers in llm_protocol.py that call game-specific utilities from behavior modules.

## Out of Scope

**Meta commands** (quit, save, load, help) remain in game_engine.py as they're not game behaviors.

## Deferred

### Transaction Support

The current design lacks transaction support for multi-update operations. Handlers that make multiple sequential `update()` calls (e.g., `handle_take` updating both item location and actor inventory) can leave state inconsistent if a later update fails after earlier updates succeed.

**Current mitigation:** Handlers check all follow-up updates for errors and report inconsistencies with `"INCONSISTENT STATE:"` message prefix. This makes failures visible during development and testing.

**Future transaction support could provide:**
- Batch multiple updates into a single atomic operation
- Automatic rollback if any update in the batch fails
- Validation of all changes before applying any

**Complexity:** Transaction support requires:
- Capturing original state before changes (for rollback)
- Determining rollback strategy for entity behaviors (some state changes may not be reversible)
- Handling nested transactions when handlers delegate to other handlers
- Managing transaction context across multiple `update()` calls

Until real use cases demonstrate this complexity is justified, the current check-and-report approach provides sufficient error visibility for development.

### Other Deferred Items

- Undo/rollback support in StateAccessor (related to transaction support)
- NPC AI using behavior handlers (framework is ready, AI decision-making not implemented)
- Multi-participant event invocation (e.g., notifying actor or location when item is taken). Currently only the primary entity's behavior is invoked. We are open to real use cases that would justify this complexity.
- **Behavior module unloading/reloading**: No `unload_module` method specified. During development, if behaviors need to be modified and reloaded, the game must be restarted. However, developers can use save/load to quickly return to their testing state, making hot-reload less critical. If needed in the future, would require:
  - Clear specification of cleanup (removing handlers, vocabulary, module references)
  - Handling of entities that reference unloaded behaviors
  - Order-dependent reload semantics
- **Container cycle detection**: Current validators.py has cycle detection to prevent infinite containment loops (e.g., box contains bag, bag contains box). This validation is deferred because:
  - Users cannot cause cycles through normal gameplay (only developer errors in setup)
  - Cycles manifest as obvious runtime errors (stack overflow, infinite loops) during development
  - Developer will quickly identify and fix when testing
  - If needed later, could add cycle detection to StateAccessor._set_path for location changes
- **Inter-behavior-module dependencies**: Behavior modules importing from other behavior modules is not addressed. Current design expects behavior modules to be self-contained and only import from `utilities/utils.py`. If cross-module dependencies are needed, would require explicit design for:
  - Module loading order based on dependency graph
  - Circular dependency detection and prevention
  - Clear specification of which imports are allowed
  - Not expected to be needed in practice - shared functionality should go in utility modules
