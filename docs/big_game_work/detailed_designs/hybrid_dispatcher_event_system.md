# Hybrid Dispatcher Event System Design

**Status**: Design Phase
**Issue**: #287
**Author**: Claude (Session: golem combat completion)
**Date**: 2025-12-26

## 1. Executive Summary

This design eliminates `None` returns from the event system and implements the hybrid dispatcher pattern for combat events (`on_attack`, `on_damage`, `on_death`). The goals are:

1. **Fail-fast validation**: Missing handlers detected immediately during development
2. **Minimal authoring burden**: Simple entities need only JSON, complex entities write only game logic
3. **Clean type system**: Replace `Optional[EventResult]` with always-returning `EventResult`
4. **Consistent patterns**: Match existing infrastructure (gift_reactions, pack_mirroring)

## 2. Current System Analysis

### 2.1 Identified Problems

#### Problem 1: Ambiguous None Returns

**Current behavior**:
```python
def invoke_behavior(...) -> Optional[EventResult]:
    # ... logic ...
    if not results:
        return None  # Means "no handler found"
```

**Issues**:
- `None` means "no handler" OR "handler returned None" - ambiguous
- Requires defensive checks: `if result and result.feedback:`
- Type system is `Optional[EventResult]` instead of clean `EventResult`
- Silent failures when handlers are missing

#### Problem 2: Boilerplate in Custom Handlers

**Current pattern** (golem_puzzle.py):
```python
def on_damage(entity, accessor, context) -> EventResult:
    # Entity type checking (boilerplate - repeated in every handler)
    golem_id = entity.id if hasattr(entity, "id") else None
    if not golem_id or "golem" not in golem_id.lower():
        return EventResult(allow=True, feedback=None)

    # State machine checking (boilerplate)
    sm = entity.properties.get("state_machine")
    if not sm:
        return EventResult(allow=True, feedback=None)

    # Actual game logic (40 lines)
    # ... state transitions, linked entities ...
```

**Issues**:
- Every handler needs entity type checking
- Non-combat entities (chairs) need explicit ignore handlers
- No centralized validation of combat properties
- Authoring burden even for simple combat entities

#### Problem 3: No Distinction Between Event Types

**Current behavior**: All events treated equally
- Global events (turn phases) returning None is **OK** (no NPCs acting)
- Entity-specific events returning None is **ERROR** (missing handler)

**Current code doesn't distinguish** - both return None silently.

#### Problem 4: Defensive None Checks Everywhere

**Current code**:
```python
# attack_handler.py:65-66
if result and hasattr(result, 'feedback') and result.feedback:
    return HandlerResult(success=result.allow, primary=result.feedback)

# combat.py:201-202
if damage_result and damage_result.feedback:
    messages.append(damage_result.feedback)

# npc_actions.py:126-127
if not result or not result.feedback:
    result = npc_take_action(npc, accessor, context)
```

**Issues**:
- Repeated pattern across codebase
- Verbose and error-prone
- Hides the actual issue (missing handlers)

### 2.2 Existing Hybrid Dispatcher Pattern

**Reference implementation**: `gift_reactions.py`

**Key features**:
1. **Infrastructure dispatcher** registers hook, receives all events
2. **Entity configuration** specifies behavior mode:
   - Data-driven: JSON properties define behavior
   - Handler escape hatch: Path to custom Python function
3. **Automatic ignore**: Entities without config are silently ignored
4. **load_handler utility**: Cached handler loading with error recovery

**Pattern validation**:
- ✅ Used by: gift_reactions, pack_mirroring, dialog_reactions, item_use_reactions
- ✅ Well-tested in production (big_game)
- ✅ Clear separation: infrastructure handles dispatch, game handles logic

### 2.3 Event System Architecture Holes

#### Hole 1: Entity Parameter Semantics Inconsistency

**Gift reactions**:
```python
def on_gift_given(entity, accessor, context):
    target = context.get("target_actor")  # entity is the ITEM being given
    gift_config = target.properties.get("gift_reactions")  # target is the RECIPIENT
```

**Combat damage**:
```python
def on_damage(entity, accessor, context):
    # entity is the TARGET taking damage
    damage = context.get("damage")
    attacker_id = context.get("attacker_id")  # attacker is in context
```

**Inconsistency**: Sometimes `entity` is the primary actor, sometimes it's a related object.

**Impact on hybrid dispatcher**:
- Combat handlers: `entity` parameter is correct (the damaged actor)
- Need to check `entity.properties` for handler config
- Context provides additional actors (attacker)

**Design decision**: Keep existing semantics, document clearly.

#### Hole 2: Handler vs Function Naming

**Current inconsistency**:
```python
# combat.py registers events
vocabulary = {
    "events": [
        {"event": "on_attack", "description": "..."},
        {"event": "on_damage", "description": "..."}
    ]
}

# combat.py also provides the DEFAULT implementation
def on_attack(entity, accessor, context):
    """Default implementation."""
    # ... but this is ALSO called directly from attack_handler.py!

# attack_handler.py line 59
result = combat.on_attack(attacker, accessor, {"target_id": target_actor.id})
```

**Problem**: `combat.on_attack()` is:
1. A registered event handler (behavior_manager finds it)
2. A directly-called function (attack_handler imports and calls it)

**This is actually CORRECT** - it's the library's default implementation:
- attack_handler calls it explicitly (command routing)
- behavior_manager also finds it for entity-specific overrides

**Design decision**: This dual role is fine, document it.

#### Hole 3: Turn Phase Return Values

**Current code** (npc_actions.py:134):
```python
if messages:
    return EventResult(allow=True, feedback="\n".join(messages))
return EventResult(allow=True, feedback=None)  # No NPCs acted
```

**Current code** (combat.py:270):
```python
if all_messages:
    return EventResult(allow=True, feedback="\n".join(all_messages))
return EventResult(allow=True, feedback=None)  # No one died
```

**Pattern**: Turn phases ALWAYS return EventResult, even when no work done.
- `feedback=None` means "no work this turn" (not an error)
- This is CORRECT behavior

**Design decision**: Turn phases already follow the pattern, keep it.

#### Hole 4: Handler Return Type Enforcement

**Current issue**: Handlers can return:
- `EventResult` (correct)
- `None` (ambiguous - no handler? or handler chose None?)
- Any other type (error, but not caught)

**Example** (combat.py:212-241):
```python
def on_death_check(entity, accessor, context) -> Optional[Any]:  # Return type: Optional[Any]!
    # ...
    if health <= 0:
        result = accessor.behavior_manager.invoke_behavior(entity, "on_death", ...)
        if result and result.feedback:
            return result
        return EventResult(allow=True, feedback=f"{entity.name} has died")
    return None  # Actor alive
```

**Problems**:
- Return type `Optional[Any]` is too loose
- Returning `None` for "alive" is semantically unclear
- Should return `EventResult(allow=True, feedback=None)` for "alive"

**Design decision**: Enforce `EventResult` returns, use sentinels for special cases.

## 3. Solution Design

### 3.1 EventResult Enhancements

**Add internal flags to EventResult**:

```python
@dataclass
class EventResult:
    """Result from entity behavior event handler.

    Always returned - never None. Use internal flags to indicate special cases.
    """
    allow: bool
    feedback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    hints: list[str] = field(default_factory=list)
    fragments: Optional[Dict[str, Any]] = None

    # Internal flags (not for author use)
    _no_handler: bool = False  # No handler registered for this event
    _ignored: bool = False     # Handler explicitly ignored (entity doesn't care)
```

**Define sentinels** (in state_accessor.py):

```python
# Sentinel for "no handler found"
NO_HANDLER = EventResult(allow=True, feedback=None, _no_handler=True)

# Sentinel for "handler explicitly ignores this entity"
IGNORE_EVENT = EventResult(allow=True, feedback=None, _ignored=True)
```

**Rationale**:
- Eliminates `None` returns
- Clear semantics: NO_HANDLER vs IGNORE_EVENT vs normal result
- Internal flags (`_`) indicate not for author use
- Type system becomes `EventResult` instead of `Optional[EventResult]`

### 3.2 invoke_behavior() Fail-Fast Logic

**Update behavior_manager.py**:

```python
def invoke_behavior(
    self,
    entity: Optional["Entity"],
    event_name: EventName,
    accessor: "StateAccessor",
    context: Dict[str, Any]
) -> EventResult:  # Changed from Optional[EventResult]
    """
    Invoke entity behaviors for an event, with fail-fast for missing handlers.

    ALWAYS returns EventResult (never None).
    Raises ValueError if entity-specific event has no handler.
    """
    # Global events (turn phases) - entity is None
    if entity is None:
        result = self._invoke_global_event(event_name, accessor, context)
        # Turn phases with no handlers are OK (no NPCs acting, no one died, etc.)
        if result._no_handler:
            return IGNORE_EVENT
        return result

    # Entity-specific events
    result = self._invoke_behavior_internal(entity, event_name, accessor, context)

    if result._no_handler:
        # FAIL FAST: Entity-specific event with no handler = authoring error
        raise ValueError(
            f"Event '{event_name}' triggered on entity '{entity.id}' but no handler found.\n"
            f"Entity behaviors: {getattr(entity, 'behaviors', [])}\n"
            f"Registered modules: {self._get_registered_modules(event_name)}\n"
            f"If this entity should ignore this event, add a handler that returns IGNORE_EVENT."
        )

    return result
```

**Update _invoke_behavior_internal()**:

```python
def _invoke_behavior_internal(
    self,
    entity: "Entity",
    event_name: EventName,
    accessor: "StateAccessor",
    context: Dict[str, Any]
) -> EventResult:  # Changed from Optional[EventResult]
    """Internal implementation - always returns EventResult."""
    if entity is None or not hasattr(entity, 'behaviors') or not entity.behaviors:
        return NO_HANDLER  # Changed from: return None

    if not isinstance(entity.behaviors, list):
        return NO_HANDLER  # Changed from: return None

    results = []

    for behavior_module_name in entity.behaviors:
        module = self._modules.get(behavior_module_name)
        if not module:
            continue

        if not hasattr(module, event_name):
            continue

        handler = getattr(module, event_name)
        event_result = handler(entity, accessor, context)  # Renamed from 'result'

        if isinstance(event_result, EventResult):
            results.append(event_result)

    if not results:
        return NO_HANDLER  # Changed from: return None

    # Combine results: AND logic for allow, concatenate feedback
    combined_allow = all(r.allow for r in results)
    messages = [r.feedback for r in results if r.feedback]
    combined_message = "\n".join(messages) if messages else None

    return EventResult(allow=combined_allow, feedback=combined_message)
```

**Update _invoke_global_event()** (for turn phases):

```python
def _invoke_global_event(
    self,
    event_name: EventName,
    accessor: "StateAccessor",
    context: Dict[str, Any]
) -> EventResult:  # Changed from Optional[EventResult]
    """Invoke global event (turn phase) - always returns EventResult."""
    event_info = self._event_registry.get(event_name)
    if not event_info or not event_info.registered_by:
        return NO_HANDLER  # Changed from: return None

    results = []
    for module_name in event_info.registered_by:
        module = self._modules.get(module_name)
        if module and hasattr(module, event_name):
            handler = getattr(module, event_name)
            event_result = handler(None, accessor, context)
            if isinstance(event_result, EventResult):
                results.append(event_result)

    if not results:
        return NO_HANDLER  # Changed from: return None

    # Combine results
    combined_allow = all(r.allow for r in results)
    combined_feedback = "; ".join(r.feedback for r in results if r.feedback)
    return EventResult(
        allow=combined_allow,
        feedback=combined_feedback if combined_feedback else None
    )
```

**Helper method**:

```python
def _get_registered_modules(self, event_name: str) -> List[str]:
    """Get list of module names that register this event (for error messages)."""
    event_info = self._event_registry.get(event_name)
    if event_info:
        return list(event_info.registered_by)
    return []
```

### 3.3 Combat Library Hybrid Dispatcher

**Update combat.py to add handler escape hatch support**:

```python
# At top of file
from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.state_accessor import EventResult, IGNORE_EVENT

# Update on_attack to support handler escape hatch
def on_attack(entity, accessor, context) -> EventResult:  # Changed from Optional[Any]
    """
    Handle attack command with hybrid dispatcher pattern.

    Modes:
    1. Handler escape hatch: entity.properties["attack_handler"] specifies custom function
    2. Default: Standard attack execution using entity.properties["attacks"]

    Non-combat entities (no attacks property) automatically ignored.
    """
    # Check for custom handler escape hatch
    if entity and hasattr(entity, 'properties'):
        handler_path = entity.properties.get("attack_handler")
        if handler_path:
            handler = load_handler(handler_path)
            if handler:
                return handler(entity, accessor, context)

    # Validate entity
    if not entity or not hasattr(entity, 'properties'):
        return EventResult(allow=False, feedback="Invalid attacker")

    # Get target
    target_id = context.get("target_id")
    if not target_id:
        return EventResult(allow=False, feedback="Attack what?")

    target = accessor.get_actor(target_id)  # Fail-fast

    # Check location
    if entity.location != target.location:
        return EventResult(allow=False, feedback=f"{target.name} is not here.")

    # Get attacker's attacks - FAIL FAST if missing for combat entity
    attacks = get_attacks(entity)
    if not attacks:
        # If entity has attack_handler configured but no attacks, that's an error
        if entity.properties.get("attack_handler"):
            raise ValueError(
                f"Entity {entity.id} has attack_handler but no 'attacks' property"
            )
        # Otherwise, not a combat entity
        return EventResult(allow=False, feedback="You don't have any attacks.")

    # Select and execute attack
    attack = select_attack(entity, target, {})
    if not attack:
        return EventResult(allow=False, feedback="No suitable attack available.")

    result = execute_attack(accessor, entity, target, attack)
    return EventResult(allow=result.success, feedback=result.narration)


def on_damage(entity, accessor, context) -> EventResult:  # Changed from not existing
    """
    Handle damage with hybrid dispatcher pattern.

    Modes:
    1. Handler escape hatch: entity.properties["damage_handler"] specifies custom function
    2. Default: Apply damage to health, subtract armor
    3. Automatic ignore: Entities without health property

    Custom handlers receive damage BEFORE it's applied (can modify or prevent).
    """
    # Validate entity
    if not entity or not hasattr(entity, 'properties'):
        return IGNORE_EVENT

    # Check for custom handler escape hatch FIRST (before applying damage)
    handler_path = entity.properties.get("damage_handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            # Custom handler handles ALL damage logic
            return handler(entity, accessor, context)

    # Automatic ignore for non-combat entities
    if "health" not in entity.properties:
        return IGNORE_EVENT

    # Validate health property
    health = entity.properties.get("health")
    if not isinstance(health, (int, float)):
        raise ValueError(
            f"Entity {entity.id} has invalid health property: {health} (type: {type(health)})"
        )

    # Default damage application
    damage = context.get("damage", 0)
    armor = entity.properties.get("armor", 0)
    actual_damage = max(0, damage - armor)

    entity.properties["health"] -= actual_damage

    # Return feedback
    if actual_damage > 0:
        return EventResult(
            allow=True,
            feedback=f"{entity.name} takes {actual_damage} damage!"
        )
    else:
        return EventResult(
            allow=True,
            feedback=f"{entity.name}'s armor absorbs the blow!"
        )


def on_death(entity, accessor, context) -> EventResult:  # Changed from not existing
    """
    Handle death with hybrid dispatcher pattern.

    Modes:
    1. Handler escape hatch: entity.properties["death_handler"] specifies custom function
    2. Default: Remove actor from game, drop inventory
    3. Automatic ignore: Entities without health (can't die)

    Called when health <= 0 by on_death_check_all turn phase.
    """
    if not entity or not hasattr(entity, 'properties'):
        return IGNORE_EVENT

    # Check for custom handler escape hatch
    handler_path = entity.properties.get("death_handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)

    # Automatic ignore for non-combat entities
    if "health" not in entity.properties:
        return IGNORE_EVENT

    # Default death handling: remove from actors, drop inventory
    state = accessor.game_state

    # Drop inventory items at location
    if hasattr(entity, 'inventory') and entity.inventory:
        for item_id in entity.inventory:
            item = state.get_item(item_id)
            item.location = entity.location

    # Remove actor
    if entity.id in state.actors:
        del state.actors[entity.id]

    return EventResult(allow=True, feedback=f"{entity.name} has died")
```

**Update on_death_check**:

```python
def on_death_check(entity, accessor, context) -> EventResult:  # Changed from Optional[Any]
    """
    Check if an actor's health <= 0 and invoke on_death behavior.

    Returns EventResult with death message, or IGNORE_EVENT if actor alive or no health.
    """
    if not entity or not hasattr(entity, 'properties'):
        return IGNORE_EVENT

    health = entity.properties.get("health")
    if health is None:
        return IGNORE_EVENT  # Changed from: return None

    if health <= 0:
        # Invoke on_death behavior
        if accessor and accessor.behavior_manager:
            result = accessor.behavior_manager.invoke_behavior(
                entity, "on_death", accessor, {}
            )
            # on_death handler provides feedback
            return result

        # No behavior manager - shouldn't happen in normal game
        return EventResult(allow=True, feedback=f"{entity.name} has died")

    return IGNORE_EVENT  # Changed from: return None (actor alive)
```

**Update vocabulary**:

```python
vocabulary = {
    "events": [
        {
            "event": "on_attack",
            "description": "Called when an actor attacks. Supports attack_handler escape hatch."
        },
        {
            "event": "on_damage",
            "description": "Called when an actor takes damage. Supports damage_handler escape hatch."
        },
        {
            "event": "on_death",
            "description": "Called when an actor dies (health <= 0). Supports death_handler escape hatch."
        },
        {
            "event": "on_death_check_all",
            "hook": "death_check",
            "description": "Turn phase: checks all actors for death"
        }
    ]
}
```

### 3.4 Migration of Existing Handlers

#### attack_handler.py

**Current code** (lines 59-72):
```python
result = combat.on_attack(attacker, accessor, {"target_id": target_actor.id})

if result and hasattr(result, 'feedback') and result.feedback:
    return HandlerResult(success=result.allow, primary=result.feedback)

# Fallback if no feedback
return HandlerResult(success=True, primary=f"You attack the {target_actor.name}!")
```

**New code**:
```python
result = combat.on_attack(attacker, accessor, {"target_id": target_actor.id})

# result is always EventResult, never None
if result.feedback:
    return HandlerResult(success=result.allow, primary=result.feedback)

# Fallback if no feedback (shouldn't happen with new combat.py)
return HandlerResult(success=True, primary=f"You attack the {target_actor.name}!")
```

#### golem_puzzle.py

**Current approach**: Module defines `on_damage` with entity type checking.

**New approach**: Use handler escape hatch.

**game_state.json**:
```json
{
  "stone_golem_1": {
    "behaviors": ["behaviors.shared.lib.actor_lib.combat"],
    "properties": {
      "health": 150,
      "max_health": 150,
      "armor": 10,
      "attacks": [...],
      "damage_handler": "behaviors.regions.frozen_reaches.golem_puzzle:on_golem_damaged",
      "state_machine": {...},
      "linked_to": "stone_golem_2"
    }
  }
}
```

**golem_puzzle.py** (simplified):
```python
# Remove on_damage from vocabulary - no longer needed

# Rename function to match handler path
def on_golem_damaged(entity, accessor, context) -> EventResult:
    """
    Custom golem damage reaction - transitions both golems to hostile.

    Called via damage_handler escape hatch.
    Combat library has already validated entity and applied damage.
    """
    # No entity type checking needed - only called for golems
    # No health property checking needed - combat library handles it

    # Get state machine
    sm = entity.properties.get("state_machine")
    if not sm:
        # Shouldn't happen - golem should have state machine
        return EventResult(allow=True, feedback=None)

    # If already hostile, no transition needed
    current_state = get_current_state(sm)
    if current_state == "hostile":
        return EventResult(allow=True, feedback=None)

    # Game-specific logic: state transitions
    state = accessor.game_state
    transition_state(sm, "hostile")

    # Set AI disposition
    entity.properties.setdefault("ai", {})["disposition"] = "hostile"

    # Linked entity handling
    linked_id = entity.properties.get("linked_to")
    if linked_id:
        linked = state.get_actor(linked_id)
        linked_sm = linked.properties.get("state_machine")
        if linked_sm and get_current_state(linked_sm) != "hostile":
            transition_state(linked_sm, "hostile")
        linked.properties.setdefault("ai", {})["disposition"] = "hostile"

    # Set flag
    state.extra["golem_combat_initiated"] = True

    return EventResult(
        allow=True,
        feedback=(
            f"The {entity.name}'s runes flare bright crimson! "
            "Both guardians move forward with grinding purpose, ready to crush any threat."
        )
    )
```

**Benefits of new approach**:
- ✅ No entity type checking boilerplate
- ✅ No health/armor checking boilerplate
- ✅ Only game-specific logic remains
- ✅ Function name matches handler path (clear)
- ✅ Combat library provides default damage handling

#### npc_actions.py

**Current code** (lines 121-127):
```python
result = accessor.behavior_manager.invoke_behavior(
    npc, "npc_take_action", accessor, context
)

if not result or not result.feedback:
    result = npc_take_action(npc, accessor, context)
```

**New code**:
```python
result = accessor.behavior_manager.invoke_behavior(
    npc, "npc_take_action", accessor, context
)

# result is always EventResult
if result._ignored or not result.feedback:
    # No custom action, use default hostile attack
    result = npc_take_action(npc, accessor, context)
```

**Update npc_take_action**:
```python
def npc_take_action(entity, accessor, context) -> EventResult:  # Changed from Optional
    """Default NPC action behavior."""
    if not entity:
        return IGNORE_EVENT  # Changed from: return None

    ai = entity.properties.get("ai", {})
    disposition = ai.get("disposition", "neutral")

    if disposition != "hostile":
        return IGNORE_EVENT  # Changed from: return None

    player = accessor.get_actor(PLAYER_ID)
    if not player or entity.location != player.location:
        return IGNORE_EVENT  # Changed from: return None

    attacks = get_attacks(entity)
    if not attacks:
        return IGNORE_EVENT  # Changed from: return None

    attack = select_attack(entity, player, {})
    if attack:
        result = execute_attack(accessor, entity, player, attack)
        return EventResult(allow=True, feedback=result.narration)

    return IGNORE_EVENT  # Changed from: return None
```

### 3.5 Type Annotation Updates

**Files to update**:

1. **src/state_accessor.py**: Add sentinels, update EventResult
2. **src/behavior_manager.py**: Change return types `Optional[EventResult]` → `EventResult`
3. **behavior_libraries/actor_lib/combat.py**: Update all function return types
4. **behavior_libraries/actor_lib/npc_actions.py**: Update return types
5. **examples/big_game/behaviors/shared/lib/core/attack_handler.py**: Remove defensive checks
6. **All custom event handlers**: Update to return IGNORE_EVENT instead of None

### 3.6 Handler Escape Hatch Property Names

**Convention**: `<event_name>_handler` format

| Event | Property Name | Example Value |
|-------|---------------|---------------|
| `on_attack` | `attack_handler` | `"behaviors.regions.boss:on_boss_attack"` |
| `on_damage` | `damage_handler` | `"behaviors.regions.golem:on_golem_damaged"` |
| `on_death` | `death_handler` | `"behaviors.regions.lich:on_lich_death"` |
| `npc_take_action` | `npc_action_handler` | `"behaviors.regions.echo:on_echo_action"` |

**Rationale**:
- Consistent naming pattern
- Clear which event the handler overrides
- Searchable in codebase

## 4. Implementation Strategy

### 4.1 Phase 1: Add Sentinels (Backwards Compatible)

**Goal**: Add sentinels without breaking existing code.

1. Add `_no_handler` and `_ignored` flags to EventResult
2. Define NO_HANDLER and IGNORE_EVENT sentinels
3. Update behavior_manager to return sentinels but still ACCEPT None from old handlers
4. Add compatibility layer that converts None → NO_HANDLER

**Compatibility layer**:
```python
def _normalize_result(result: Optional[EventResult]) -> EventResult:
    """Convert None to NO_HANDLER for backwards compatibility."""
    if result is None:
        return NO_HANDLER
    return result
```

**Testing**: All existing tests should pass.

### 4.2 Phase 2: Update Combat Library

**Goal**: Add hybrid dispatcher to combat.py.

1. Add load_handler import
2. Add on_damage and on_death handlers with escape hatch support
3. Update on_attack to add escape hatch support
4. Update on_death_check to return EventResult instead of Optional
5. Update vocabulary registration

**Testing**:
- Simple combat entity (no custom handler) - should work
- Test with chair (no health) - should auto-ignore
- Test with missing attacks property - should raise ValueError

### 4.3 Phase 3: Migrate Golem Combat

**Goal**: Convert golem_puzzle to use handler escape hatch.

1. Update game_state.json: add `damage_handler` property
2. Rename `on_damage` → `on_golem_damaged` in golem_puzzle.py
3. Remove on_damage from vocabulary
4. Remove entity type checking boilerplate
5. Remove health/armor checking boilerplate

**Testing**: Run golem walkthrough, verify:
- Player can attack golems
- Golems take damage (armor reduction works)
- Golems become hostile (both)
- Golems counter-attack
- Player dies when health <= 0

### 4.4 Phase 4: Update Call Sites

**Goal**: Remove defensive None checks.

1. attack_handler.py: Remove `if result and hasattr(result, 'feedback')`
2. npc_actions.py: Update to check `_ignored` flag
3. Any other None checks for EventResult

**Testing**: All existing tests should still pass.

### 4.5 Phase 5: Enforce EventResult Returns

**Goal**: Make invoke_behavior fail-fast.

1. Remove compatibility layer
2. Add fail-fast logic for entity-specific events
3. Update all remaining handlers to return IGNORE_EVENT instead of None

**Testing**: Should get clear errors for any missing handlers.

### 4.6 Phase 6: Type Annotation Sweep

**Goal**: Update type annotations throughout codebase.

1. Change `Optional[EventResult]` → `EventResult`
2. Run mypy on changed files
3. Fix any type errors

**Testing**: `mypy src/ behavior_libraries/ examples/big_game/` should pass.

## 5. Error Messages

### 5.1 Missing Handler Error

```
ValueError: Event 'on_damage' triggered on entity 'stone_golem_1' but no handler found.
Entity behaviors: ['behaviors.regions.frozen_reaches.golem_puzzle']
Registered modules: ['behaviors.shared.lib.actor_lib.combat']
If this entity should ignore this event, add a handler that returns IGNORE_EVENT.

Context: This usually means:
1. Entity is missing a behavior module in 'behaviors' array
2. Module doesn't have the expected event handler function
3. Function name doesn't exactly match event name
```

### 5.2 Invalid Property Error

```
ValueError: Entity stone_golem_1 has invalid health property: "one hundred" (type: <class 'str'>)

Context: health property must be int or float.
```

### 5.3 Handler Load Failure

```
WARNING: Handler behaviors.regions.golem:on_golem_damaged failed to load for damage_handler
  Cause: ModuleNotFoundError: No module named 'behaviors.regions.golem'
  Falling back to default damage handling.

Context: Check handler path format: "module.path:function_name"
```

## 6. Testing Plan

### 6.1 Unit Tests

**New tests** (in test_behavior_manager.py):
- `test_invoke_behavior_returns_eventresult_not_none`
- `test_invoke_behavior_fails_fast_on_missing_entity_handler`
- `test_invoke_behavior_global_event_returns_ignore_when_no_handler`
- `test_sentinel_no_handler_identity`
- `test_sentinel_ignore_event_identity`

**New tests** (in test_combat.py):
- `test_on_damage_with_handler_escape_hatch`
- `test_on_damage_auto_ignore_no_health`
- `test_on_damage_default_applies_armor`
- `test_on_attack_with_custom_handler`
- `test_on_death_with_custom_handler`
- `test_on_death_default_removes_actor`

### 6.2 Integration Tests

**Golem combat walkthrough** (existing):
- Should work unchanged after migration
- Verify custom damage handler is called
- Verify both golems transition to hostile
- Verify player death handling

**New walkthroughs**:
- Simple combat entity (no custom handlers)
- Non-combat entity attacked (chair)
- NPC with custom action handler

### 6.3 Regression Tests

Run existing test suite to ensure no breaks:
- `python -m pytest tests/`
- `python tools/walkthrough.py examples/big_game --file walkthroughs/test_combat_golem.txt`

## 7. Documentation Updates

### 7.1 Combat Implementation Guide

**Updates needed** (combat_implementation_guide.md):

1. Section 4 (on_damage hook): Update to show handler escape hatch pattern
2. Section 7 (Common Pitfalls): Add handler escape hatch examples
3. Section 11 (Real Implementation): Show new simplified golem handler

**New section**: "Handler Escape Hatch Pattern"
```markdown
## Handler Escape Hatch for Custom Logic

For entities with complex combat behavior, use the handler escape hatch:

**Configuration**:
```json
{
  "properties": {
    "damage_handler": "behaviors.regions.golem:on_golem_damaged"
  }
}
```

**Handler**:
```python
def on_golem_damaged(entity, accessor, context) -> EventResult:
    # Only game-specific logic - no boilerplate
    # Combat library already validated and applied damage
    return EventResult(allow=True, feedback="Custom behavior!")
```
```

### 7.2 Authoring Manual

**New section** (05_behaviors.md): "Hybrid Dispatcher Pattern"

Document:
- When to use data-driven vs handler escape hatch
- Property naming convention (`<event>_handler`)
- Example of simple entity (JSON only)
- Example of complex entity (handler escape hatch)
- How library provides default + custom overrides

### 7.3 API Documentation

**Update docstrings**:
- `invoke_behavior()`: Document that it always returns EventResult, fails fast
- `on_damage()`, `on_attack()`, `on_death()`: Document escape hatch support
- `EventResult`: Document internal flags, sentinels

## 8. Migration Guide for Authors

### 8.1 Before (Current Pattern)

```python
# Custom handler with boilerplate
def on_damage(entity, accessor, context) -> EventResult:
    # Entity type checking
    if not entity or "golem" not in entity.id.lower():
        return EventResult(allow=True, feedback=None)

    # Health checking
    if "health" not in entity.properties:
        return EventResult(allow=True, feedback=None)

    # Damage application
    damage = context.get("damage", 0)
    armor = entity.properties.get("armor", 0)
    actual_damage = max(0, damage - armor)
    entity.properties["health"] -= actual_damage

    # Custom logic
    transition_state(sm, "hostile")

    return EventResult(allow=True, feedback="Golem damaged!")
```

### 8.2 After (Hybrid Dispatcher)

**game_state.json**:
```json
{
  "stone_golem": {
    "behaviors": ["behaviors.shared.lib.actor_lib.combat"],
    "properties": {
      "health": 150,
      "armor": 10,
      "damage_handler": "behaviors.regions.golem:on_golem_damaged"
    }
  }
}
```

**golem.py**:
```python
# Custom handler - only game logic
def on_golem_damaged(entity, accessor, context) -> EventResult:
    # Combat library already applied damage
    # Only custom logic needed
    transition_state(entity.properties["state_machine"], "hostile")
    return EventResult(allow=True, feedback="Golem becomes hostile!")
```

**Benefits**:
- 15 lines → 3 lines
- No boilerplate
- Clear separation: library handles mechanics, game handles narrative

## 9. Risks and Mitigations

### 9.1 Risk: Breaking Existing Code

**Mitigation**: Phased implementation with compatibility layer in Phase 1.

### 9.2 Risk: Handler Path Typos

**Mitigation**:
- load_handler() logs warnings for failures
- Falls back to default behavior
- Clear error messages during development

### 9.3 Risk: Confusion About When to Use Escape Hatch

**Mitigation**:
- Clear documentation with decision tree
- Examples for common cases
- Default behavior handles 90% of cases

**Decision tree**:
- Standard combat behavior? → JSON only
- Custom reactions/state changes? → Handler escape hatch
- Non-combat entity? → No configuration needed (auto-ignore)

### 9.4 Risk: Performance Impact of Handler Loading

**Mitigation**:
- Handler cache in dispatcher_utils.py
- One-time load per handler path
- Negligible impact (milliseconds)

## 10. Success Criteria

✅ **Phase 1**: No test failures after adding sentinels
✅ **Phase 2**: Simple combat entity works with JSON only
✅ **Phase 3**: Golem walkthrough passes after migration
✅ **Phase 4**: All defensive None checks removed
✅ **Phase 5**: Missing handlers fail fast with clear errors
✅ **Phase 6**: Mypy passes on updated files

**Final validation**:
- Run all existing walkthroughs
- Create new simple combat NPC - should work with JSON only
- Attack chair - should auto-ignore
- Remove attacks from combat entity - should get clear error

## 11. Parameter Naming Standardization

### 11.1 Current Inconsistency

**Analysis**: Event handlers have inconsistent parameter naming across the codebase.

**Files using `state` parameter** (OLD pattern):
- `behaviors/core/consumables.py` (on_drink, on_eat)
- `behaviors/core/containers.py` (on_open)
- `behaviors/core/light_sources.py` (on_take, on_drop, on_put)

**Files using `accessor` parameter** (CORRECT pattern):
- `behavior_libraries/actor_lib/combat.py`
- `behavior_libraries/actor_lib/conditions.py`
- `behavior_libraries/actor_lib/environment.py`
- `behavior_libraries/actor_lib/npc_actions.py`
- `behavior_libraries/actor_lib/services.py`
- `behavior_libraries/actor_lib/trading.py`
- `behavior_libraries/actor_lib/treatment.py`
- All infrastructure dispatchers in `examples/big_game/behaviors/shared/infrastructure/`

**Inconsistency impact**:
```python
# OLD pattern (core behaviors)
def on_drink(entity: Any, state: Any, context: Dict) -> Optional[EventResult]:
    # 'state' is actually a StateAccessor instance, not GameState
    # Confusing and misleading parameter name

# CORRECT pattern (libraries, infrastructure)
def on_gift_given(entity: Any, accessor: Any, context: Dict[str, Any]) -> EventResult:
    # 'accessor' correctly indicates StateAccessor instance
    # Can access: accessor.game_state, accessor.behavior_manager, etc.
```

### 11.2 Standardization Required

**Decision**: Rename `state` → `accessor` throughout codebase.

**Rationale**:
1. **Semantic clarity**: Parameter IS a StateAccessor, not GameState
2. **Consistency**: Matches all modern code (libraries, infrastructure)
3. **Discoverability**: Clear what methods are available (accessor.*)
4. **Documentation**: Aligns with API docs and authoring manual

**Files requiring updates**:

| File | Handlers | Lines Est. |
|------|----------|------------|
| `behaviors/core/consumables.py` | on_drink, on_eat | ~60 |
| `behaviors/core/containers.py` | on_open | ~30 |
| `behaviors/core/light_sources.py` | on_take, on_drop, on_put | ~50 |

**Update pattern**:
```python
# BEFORE
def on_drink(entity: Any, state: Any, context: Dict) -> Optional[EventResult]:
    """Handle drink event."""
    if not entity or not hasattr(entity, 'properties'):
        return EventResult(allow=True)

    # Access game state
    game = state.game_state  # Confusing - state.game_state?
    player = state.get_actor("player")

    return EventResult(allow=True, feedback="You drink.")

# AFTER
def on_drink(entity: Any, accessor: Any, context: Dict) -> EventResult:  # Note: EventResult not Optional
    """Handle drink event."""
    if not entity or not hasattr(entity, 'properties'):
        return IGNORE_EVENT  # Note: Use sentinel

    # Access game state (clear)
    game = accessor.game_state
    player = accessor.get_actor("player")

    return EventResult(allow=True, feedback="You drink.")
```

### 11.3 Additional Standardization

While updating parameter names, also standardize:

1. **Return types**: `Optional[EventResult]` → `EventResult`
2. **None returns**: `return None` → `return IGNORE_EVENT`
3. **Type annotations**: Add where missing
4. **Docstrings**: Update parameter documentation

**Example complete update**:
```python
# BEFORE
def on_eat(entity: Any, state: Any, context: Dict) -> Optional[EventResult]:
    """
    Handle eat event for food items.

    Args:
        entity: The food item
        state: Game state accessor
        context: Event context
    """
    if not entity or not hasattr(entity, 'properties'):
        return None

    food_type = entity.properties.get("food_type")
    if not food_type:
        return None

    # ... logic ...
    return EventResult(allow=True, feedback="You eat the food.")

# AFTER
def on_eat(entity: Any, accessor: Any, context: Dict[str, Any]) -> EventResult:
    """
    Handle eat event for food items.

    Args:
        entity: The food item being eaten
        accessor: StateAccessor for game state and behavior queries
        context: Event context (actor_id, changes, verb)

    Returns:
        EventResult with consumption result, or IGNORE_EVENT if not food
    """
    if not entity or not hasattr(entity, 'properties'):
        return IGNORE_EVENT

    food_type = entity.properties.get("food_type")
    if not food_type:
        return IGNORE_EVENT

    # ... logic ...
    return EventResult(allow=True, feedback="You eat the food.")
```

### 11.4 Implementation Plan

**Add to Phase 6 (Type Annotation Sweep)**:

**Step 6a: Core Behaviors Parameter Rename** (BEFORE type annotations)
1. Update `behaviors/core/consumables.py`: Rename `state` → `accessor`, update returns
2. Update `behaviors/core/containers.py`: Rename `state` → `accessor`, update returns
3. Update `behaviors/core/light_sources.py`: Rename `state` → `accessor`, update returns
4. Run tests: `python -m pytest tests/` - should pass
5. Run sample walkthrough - should pass

**Step 6b: Type Annotation Updates** (AFTER parameter rename)
1. Change return types `Optional[EventResult]` → `EventResult`
2. Add Dict type annotations where missing
3. Update docstrings
4. Run mypy

**Verification**:
```bash
# Check for remaining 'state' parameters
grep -r "def on_.*entity.*state.*context" behaviors/ behavior_libraries/

# Should return zero results after standardization
```

### 11.5 Estimation

**Additional work**: ~3 files, ~140 lines total
- Mechanical changes (rename, update types)
- Low risk (well-defined pattern)
- High value (eliminates confusion, technical debt)

**Testing impact**: Existing tests should pass unchanged (StateAccessor supports both patterns during transition)

## 12. Open Questions

1. **Should we support data-driven damage modifications?**
   - e.g., `"damage_multiplier": 0.5` in properties
   - Decision: DEFER - handler escape hatch is sufficient

2. **Should non-handler EventResults have _ignored or _no_handler flags?**
   - Currently only sentinels have flags
   - Decision: No - flags are implementation details

3. **Should we add DEFER_TO_DEFAULT sentinel for partial overrides?**
   - e.g., custom handler wants to run default logic afterward
   - Decision: DEFER - can explicitly call combat library functions

4. **Should turn phases use IGNORE_EVENT or custom EventResult(feedback=None)?**
   - Current: Return EventResult(feedback=None) for "no work"
   - Decision: Keep current behavior - more explicit

## 13. References

- Issue #274: Golem combat implementation
- Issue #285: Global event handler fix (turn phase infrastructure)
- Issue #286: Tier-based entity behavior override (deferred)
- Issue #287: This design
- `examples/big_game/behaviors/shared/infrastructure/gift_reactions.py`: Reference implementation
- `docs/big_game_work/combat_implementation_guide.md`: Combat patterns
- `user_docs/authoring_manual/05_behaviors.md`: Behavior system documentation
