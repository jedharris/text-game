# Combat Implementation Quick Guide

**Status: VALIDATED - Confirmed working with golem combat (Issue #274)**

Quick reference for implementing combat in big_game. All patterns have been validated through the golem puzzle combat implementation.

## 1. Prerequisites

### Load Combat Library
```bash
cd examples/big_game/behaviors/shared/lib/actor_lib
ln -s ../../../../../../behavior_libraries/actor_lib/combat.py combat.py
ln -s ../../../../../../behavior_libraries/actor_lib/conditions.py conditions.py
ln -s ../../../../../../behavior_libraries/actor_lib/npc_actions.py npc_actions.py
```

### Configure Turn Phases
In `game_state.json` metadata:
```json
{
  "metadata": {
    "extra_turn_phases": [
      "turn_phase_scheduled",
      "turn_phase_commitment",
      "turn_phase_gossip",
      "turn_phase_spread"
    ]
  }
}
```

**Note**: Do NOT add `npc_action` or `death_check` - they're in BASE_TURN_PHASE_HOOKS.

## 2. Actor Combat Properties

### Player Setup
```json
{
  "actors": {
    "player": {
      "properties": {
        "health": 100,
        "max_health": 100,
        "armor": 0,
        "attacks": [
          {
            "name": "sword slash",
            "damage": 15,
            "type": "melee"
          }
        ]
      }
    }
  }
}
```

### Hostile NPC Setup
```json
{
  "npc_golem": {
    "behaviors": ["behaviors.regions.frozen_reaches.golem_puzzle"],
    "properties": {
      "health": 150,
      "max_health": 150,
      "armor": 10,
      "attacks": [
        {
          "name": "stone fist",
          "damage": 30,
          "type": "melee"
        }
      ],
      "ai": {
        "disposition": "hostile"  // NPC attacks each turn
      }
    }
  }
}
```

**Key points:**
- `behaviors`: Array of modules containing event handlers for this entity
- `ai.disposition`: "hostile" makes NPC attack player each turn
- `armor`: Flat damage reduction
- `attacks`: Array - combat system selects best attack

## 3. Attack Command Handler

Create `behaviors/shared/lib/core/attack_handler.py`:

```python
from src.state_accessor import HandlerResult
from utilities.handler_utils import validate_actor_and_location, get_display_name
from utilities.utils import name_matches, find_accessible_item

vocabulary = {
    "verbs": [
        {
            "word": "attack",
            "handler": "handle_attack",
            "synonyms": ["hit", "strike", "fight", "kill"],
            "object_required": True,
            "narration_mode": "brief"
        }
    ]
}

def handle_attack(accessor, action):
    """Route attack command to combat system."""
    actor_id, attacker, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    target_name = action.get("object")

    # Find target NPC in same location
    target_actor = None
    for actor in accessor.game_state.actors.values():
        if actor.id != actor_id and actor.location == location.id:
            if name_matches(target_name, actor.name):
                target_actor = actor
                break

    if target_actor:
        # Call combat system
        from behaviors.shared.lib.actor_lib import combat

        result = combat.on_attack(
            attacker,
            accessor,
            {"target_id": target_actor.id}
        )

        if result and hasattr(result, 'feedback') and result.feedback:
            return HandlerResult(success=result.allow, primary=result.feedback)

        return HandlerResult(
            success=True,
            primary=f"You attack the {target_actor.name}!"
        )

    # Can't attack items
    item = find_accessible_item(accessor, target_name, actor_id)
    if item:
        return HandlerResult(
            success=False,
            primary=f"You can't attack the {item.name}."
        )

    return HandlerResult(
        success=False,
        primary=f"You don't see any {get_display_name(target_name)} here."
    )
```

## 4. Dynamic State Changes (on_damage hook)

When NPCs should react to being attacked, implement `on_damage` event handler:

```python
from typing import Any
from src.behavior_manager import EventResult
from src.infrastructure_utils import transition_state, get_current_state

vocabulary = {
    "events": [
        {
            "event": "on_damage",
            "description": "Called when entity takes damage"
        }
    ]
}

def on_damage(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle entity taking damage.

    Context contains:
        damage: int - Amount of damage dealt
        attacker_id: str - ID of attacking actor
        attack_type: str - Type of attack
    """
    # Validate this is the right entity type
    entity_id = entity.id if hasattr(entity, "id") else None
    if not entity_id or "golem" not in entity_id.lower():
        return EventResult(allow=True, feedback=None)

    # Get game state
    state = accessor.game_state

    # Check current state
    sm = entity.properties.get("state_machine")
    if sm:
        current = get_current_state(sm)
        if current != "hostile":
            transition_state(sm, "hostile")

    # Set AI to hostile for NPC action phase
    if "ai" not in entity.properties:
        entity.properties["ai"] = {}
    entity.properties["ai"]["disposition"] = "hostile"

    # Can also affect linked entities
    linked_id = entity.properties.get("linked_to")
    if linked_id:
        linked = state.get_actor(linked_id)  # Fail-fast
        linked_sm = linked.properties.get("state_machine")
        if linked_sm:
            if get_current_state(linked_sm) != "hostile":
                transition_state(linked_sm, "hostile")
        if "ai" not in linked.properties:
            linked.properties["ai"] = {}
        linked.properties["ai"]["disposition"] = "hostile"

    return EventResult(
        allow=True,
        feedback="The enemy becomes hostile!"
    )
```

**Critical points:**
- Function name MUST match event name (`on_damage`, not `on_golem_damaged`)
- Entity must have this module in its `behaviors` array
- Use `state.get_actor(id)` for fail-fast (NOT `state.actors.get()`)
- Return `EventResult` with `feedback` to show message

## 5. Combat System Integration

### How Combat Works

1. **Player attacks**: `attack guardian` → `handle_attack()` → `combat.on_attack()`
2. **Combat executes**: Damage calculated, `on_damage` event fires on target
3. **Target reacts**: `on_damage` handler sets `ai.disposition = "hostile"`
4. **Turn advances**: After successful command, turn phases fire
5. **NPC action phase**: `npc_actions.on_npc_action()` runs
6. **NPC attacks back**: Finds hostile NPCs, calls `combat.on_attack()` from their perspective
7. **Condition tick**: Poison, bleeding, etc. progress
8. **Death check**: Any actor with `health <= 0` triggers `on_death`

### Events vs Hooks

**Event**: Function name in a behavior module (e.g., `on_damage`, `on_attack`)
**Hook**: Engine trigger point (e.g., `npc_action`, `death_check`)

Events can register to hooks via vocabulary:
```python
vocabulary = {
    "events": [
        {
            "event": "on_npc_action",
            "hook": "npc_action",  # Fires during NPC action turn phase
            "description": "..."
        }
    ]
}
```

## 6. Combat Feedback Integration

The combat system's `execute_attack()` must return feedback from `on_damage`:

In `behavior_libraries/actor_lib/combat.py` at line ~197:
```python
# Fire on_damage behavior on target
if accessor and accessor.behavior_manager:
    damage_context = {
        "damage": damage,
        "attacker_id": attacker.id,
        "attack_type": attack.get("type")
    }
    damage_result = accessor.behavior_manager.invoke_behavior(
        target, "on_damage", accessor, damage_context
    )
    # Append on_damage feedback to narration
    if damage_result and damage_result.feedback:
        messages.append(damage_result.feedback)
```

## 7. Common Pitfalls

### ❌ Wrong: Using .get() when entity should exist
```python
linked = state.actors.get(linked_id)
if linked:  # Defensive None check hides authoring errors
    ...
```

### ✅ Right: Using fail-fast get_actor()
```python
linked = state.get_actor(linked_id)  # Raises KeyError if missing
# Entity guaranteed to exist here
```

### ❌ Wrong: Event name doesn't match function name
```python
vocabulary = {"events": [{"event": "on_damage", "hook": "on_golem_damaged"}]}
def on_golem_damaged(entity, accessor, context):  # Won't be called!
```

### ✅ Right: Function name matches event
```python
vocabulary = {"events": [{"event": "on_damage"}]}
def on_damage(entity, accessor, context):  # Will be called
```

### ❌ Wrong: Missing behaviors array
```json
{
  "npc_golem": {
    "properties": { ... }
  }
}
```

### ✅ Right: Behaviors array present
```json
{
  "npc_golem": {
    "behaviors": ["behaviors.regions.frozen_reaches.golem_puzzle"],
    "properties": { ... }
  }
}
```

## 8. Testing Pattern

Create walkthrough file `walkthroughs/test_combat_X.txt`:
```
go north
go north
# Attack should trigger hostile response
attack guardian
# Any command advances turn - NPC should counter-attack
inventory
# Continue combat
attack guardian
attack guardian
```

Run: `python tools/walkthrough.py examples/big_game --file walkthroughs/test_combat_X.txt`

Expected output:
```
> attack guardian
[✓] Wanderer hits Stone Guardian with sword slash for 5 damage; The enemy becomes hostile!

> inventory
[✓] You are carrying nothing.
Stone Guardian hits Wanderer with stone fist for 20 damage!
```

## 9. Critical Engine Fix Required

**IMPORTANT**: The base engine had a bug preventing turn phase hooks from firing.

In `src/behavior_manager.py`, the `invoke_behavior()` method returned `None` when `entity is None`, which prevented global event handlers (turn phases) from running.

**Fix applied** (lines 731-752):
```python
# For global events (turn phases, etc.), invoke all modules that register this event
if entity is None:
    event_info = self._event_registry.get(event_name)
    if not event_info or not event_info.registered_by:
        return None

    results = []
    for module_name in event_info.registered_by:
        module = self._modules.get(module_name)
        if module and hasattr(module, event_name):
            handler = getattr(module, event_name)
            result = handler(None, accessor, context)
            if isinstance(result, EventResult):
                results.append(result)

    if not results:
        return None

    # Combine results
    combined_allow = all(r.allow for r in results)
    combined_feedback = "; ".join(r.feedback for r in results if r.feedback)
    return EventResult(allow=combined_allow, feedback=combined_feedback if combined_feedback else None)
```

This enables turn phase events like `on_npc_action`, `on_death_check_all`, etc. to fire correctly.

## 10. Walkthrough Tool Fix

The walkthrough tool wasn't displaying turn phase messages (NPC attacks, death checks).

**Fix applied** in `tools/walkthrough.py`:
```python
def extract_result_message(result: Dict[str, Any]) -> str:
    """Extract human-readable message from result."""
    parts = []

    if "narration" in result:
        narration = result["narration"]
        if narration.get("primary_text"):
            parts.append(narration.get("primary_text"))
        if "secondary_beats" in narration:
            parts.extend(narration["secondary_beats"])

    # Add turn phase messages (NPC actions, death checks, etc.)
    if "turn_phase_messages" in result:
        parts.extend(result["turn_phase_messages"])

    if parts:
        return "\n".join(p for p in parts if p)
    # ... rest of function
```

## Status Checklist

- [x] Combat library symlinked
- [x] Turn phases configured (removed duplicates)
- [x] Player combat properties added
- [x] Attack handler created
- [x] on_damage feedback integrated into combat.py
- [x] on_npc_action function renamed (was fire_npc_actions)
- [x] invoke_behavior fixed for global events (CRITICAL ENGINE FIX)
- [x] Walkthrough tool fixed to show turn phase messages
- [x] Golem on_damage handler working ✅
- [x] Golem counter-attacks verified ✅
- [x] Full combat loop tested ✅
- [x] Death handling working ✅

## Confirmed Working Output

```
> attack guardian
[✓] Wanderer hits Stone Guardian with sword slash for 5 damage;
The Stone Guardian's runes flare bright crimson! Both guardians move forward with grinding purpose, ready to crush any threat.
Stone Guardian hits Wanderer with stone fist for 30 damage
Stone Guardian hits Wanderer with stone fist for 30 damage

> look
[✓] Temple Sanctum
...
Stone Guardian hits Wanderer with stone fist for 30 damage
Stone Guardian hits Wanderer with stone fist for 30 damage
Wanderer has died
```

Both golems attack each turn (2 attacks), player dies after taking 120 damage total (60 per turn, 2 turns).

## Real Implementation Example: Golem Puzzle

The actual golem implementation in [golem_puzzle.py](../../examples/big_game/behaviors/regions/frozen_reaches/golem_puzzle.py) shows the complete pattern:

**Key differences from simplified example:**
1. Custom feedback message referencing lore ("runes flare bright crimson")
2. Linked entity handling (both golems transition together via `linked_to` property)
3. State machine transitions in addition to AI disposition
4. Early return when already hostile (prevents duplicate messages)

**Actual on_damage handler:**
```python
def on_damage(entity, accessor, context) -> EventResult:
    """Handle golem taking damage - transitions both golems to hostile."""
    # Validate this is a golem
    golem_id = entity.id if hasattr(entity, "id") else None
    if not golem_id or "golem" not in golem_id.lower():
        return EventResult(allow=True, feedback=None)

    # Get state machine
    sm = entity.properties.get("state_machine")
    if not sm:
        return EventResult(allow=True, feedback=None)

    # If already hostile, no need to transition
    current_state = get_current_state(sm)
    if current_state == "hostile":
        return EventResult(allow=True, feedback=None)

    # Get game state
    state = accessor.game_state

    # Transition this golem to hostile
    transition_state(sm, "hostile")

    # Set AI disposition to hostile for NPC action phase
    if "ai" not in entity.properties:
        entity.properties["ai"] = {}
    entity.properties["ai"]["disposition"] = "hostile"

    # Find and transition linked golem
    linked_id = entity.properties.get("linked_to")
    if linked_id:
        linked = state.get_actor(linked_id)  # Fail-fast
        linked_sm = linked.properties.get("state_machine")
        if linked_sm:
            linked_state = get_current_state(linked_sm)
            if linked_state != "hostile":
                transition_state(linked_sm, "hostile")
        # Set linked golem's AI disposition
        if "ai" not in linked.properties:
            linked.properties["ai"] = {}
        linked.properties["ai"]["disposition"] = "hostile"

    # Set flag that combat has begun
    state.extra["golem_combat_initiated"] = True

    return EventResult(
        allow=True,
        feedback=(
            f"The {entity.name}'s runes flare bright crimson! "
            "Both guardians move forward with grinding purpose, ready to crush any threat."
        )
    )
```

This shows the full production pattern: validation, state checks, state transitions, AI updates, linked entity handling, and custom narrative feedback.
