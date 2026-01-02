# Hook System Guide

## Overview

The hook system allows game behaviors to respond to engine events through vocabulary-based hook definitions. Hooks provide clean extension points where game code can inject custom logic without modifying engine internals.

**Key Benefits:**
- **No engine dependencies**: Authors never reference `src/` files
- **Self-documenting**: Hook names indicate invocation pattern (`turn_*` vs `entity_*`)
- **Load-time validation**: 90%+ of errors caught before gameplay
- **Explicit dependencies**: Turn phases use declarative ordering
- **Layer separation**: Games extend libraries without modifying them

## Hook Types

### Turn Phase Hooks (`turn_*`)

Turn phase hooks execute once per turn, after a successful player command. They advance game time and apply global effects.

**Naming**: Must start with `turn_` prefix

**Invocation**: Called once per turn with `entity=None`

**Use cases**:
- NPC actions
- Environmental effects
- Condition progression
- Scheduled events
- Death checks

**Example**:
```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_environmental_effect",
            "invocation": "turn_phase",
            "after": ["turn_npc_action"],
            "description": "Apply environmental hazards"
        }
    ],
    "events": [
        {
            "event": "on_environmental_effect",
            "hook": "turn_environmental_effect"
        }
    ]
}

def on_environmental_effect(entity, accessor, context):
    """Called once per turn to process all environmental effects."""
    # entity is None for turn phases
    # Process all actors for environmental damage
    messages = []
    for actor in accessor.game_state.actors.values():
        # Apply cold damage, poison, etc.
        pass
    return EventResult(allow=True, feedback="\n".join(messages) if messages else None)
```

### Entity Hooks (`entity_*`)

Entity hooks execute for specific entities, providing per-entity behavior customization.

**Naming**: Must start with `entity_` prefix

**Invocation**: Called once per matching entity

**Use cases**:
- Visibility checks
- Custom interactions
- Entity-specific validation
- State transitions

**Example**:
```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_visibility_check",
            "invocation": "entity",
            "description": "Check if entity is visible to observer"
        }
    ],
    "events": [
        {
            "event": "on_observe",
            "hook": "entity_visibility_check"
        }
    ]
}

def on_observe(entity, accessor, context):
    """Called to check if entity is visible."""
    observer_id = context.get("actor_id")

    # Check for invisibility
    if entity.states.get("invisible"):
        return EventResult(allow=False)  # Hide entity

    return EventResult(allow=True)  # Entity is visible
```

## Defining Hooks in Vocabularies

Hooks are defined in behavior module vocabularies, making them part of the module's public API.

### Basic Hook Definition

```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_my_custom_phase",      # Required: Hook identifier
            "invocation": "turn_phase",              # Required: "turn_phase" or "entity"
            "description": "Human-readable purpose"  # Required: What this hook does
        }
    ]
}
```

### Turn Phase with Dependencies

Turn phases can declare execution order using `after` and `before` fields:

```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_condition_tick",
            "invocation": "turn_phase",
            "after": ["turn_environmental_effect"],    # Run after environmental effects
            "before": [],                              # Optional, can be omitted
            "description": "Progress all actor conditions"
        }
    ]
}
```

### Wiring Events to Hooks

Events connect handler functions to hooks:

```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_npc_action",
            "invocation": "turn_phase",
            "after": [],
            "description": "Execute NPC actions"
        }
    ],
    "events": [
        {
            "event": "on_npc_action",           # Event name (maps to handler function)
            "hook": "turn_npc_action",          # Hook to invoke
            "description": "Called each turn for NPC actions"
        }
    ]
}

def on_npc_action(entity, accessor, context):
    """Handler function - name matches event name."""
    # Implementation
    pass
```

## Turn Phase Dependencies

Turn phases execute in dependency order, determined by `after` and `before` constraints.

### Using `after`

The `after` field declares dependencies - hooks that must run first:

```python
{
    "hook_id": "turn_death_check",
    "invocation": "turn_phase",
    "after": ["turn_condition_tick"],  # Death check runs after conditions tick
    "description": "Check for actor deaths"
}
```

This creates a dependency edge: `turn_condition_tick → turn_death_check`

### Using `before`

The `before` field declares hooks that must run later:

```python
{
    "hook_id": "turn_condition_spread",
    "invocation": "turn_phase",
    "after": ["turn_gossip_spread"],
    "before": ["turn_npc_action"],  # Spread runs before NPC actions
    "description": "Spread conditions between locations"
}
```

This creates a dependency edge: `turn_condition_spread → turn_npc_action`

### Layer Ordering Pattern

The `before` field enables clean layer separation. Game-specific hooks can insert themselves into library execution order without modifying library code:

**Library Code** (doesn't know about games):
```python
# behavior_libraries/actor_lib/npc_actions.py
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_npc_action",
            "invocation": "turn_phase",
            "after": [],   # No dependencies - accepts game hooks via 'before'
            "description": "Execute NPC actions"
        }
    ]
}
```

**Game Code** (extends library):
```python
# examples/my_game/behaviors/infrastructure/spreads.py
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_condition_spread",
            "invocation": "turn_phase",
            "after": ["turn_gossip_spread"],
            "before": ["turn_npc_action"],  # Game declares it runs before library
            "description": "Spread conditions"
        }
    ]
}
```

Result: `turn_gossip_spread → turn_condition_spread → turn_npc_action`

The library code remains unchanged - the game cleanly extends the execution order.

### Common Dependency Patterns

**Linear Chain**:
```python
# A → B → C
hook_a: after=[]
hook_b: after=["hook_a"]
hook_c: after=["hook_b"]
```

**Parallel + Converge**:
```python
# A → B, A → C, B → D, C → D
hook_a: after=[]
hook_b: after=["hook_a"]
hook_c: after=["hook_a"]
hook_d: after=["hook_b", "hook_c"]
```

**Game Extension**:
```python
# Library: A → B
# Game adds C between them: A → C → B
hook_a: after=[]              # Library
hook_b: after=["hook_a"]      # Library
hook_c: after=["hook_a"], before=["hook_b"]  # Game extension
```

## Validation and Error Handling

The engine validates all hook definitions at game load time, catching authoring errors before gameplay.

### Validation Checks

1. **Prefix consistency**: `turn_*` hooks must have `invocation: "turn_phase"`, `entity_*` hooks must have `invocation: "entity"`
2. **Defined hooks**: All `after`/`before` dependencies must reference defined hooks
3. **No circular dependencies**: Dependency graph must be acyclic
4. **No turn phases on entities**: Turn phase behaviors cannot be in entity behaviors lists
5. **Event hook references**: All event `hook` fields must reference defined hooks

### Common Validation Errors

#### Error: Prefix mismatch
```
Hook 'turn_my_hook' has invocation 'entity' but name starts with 'turn_'
  Defined in: game.behaviors.custom
  Fix: Either rename to 'entity_my_hook' or change invocation to 'turn_phase'
```

**Fix**: Match the prefix to the invocation type.

#### Error: Undefined dependency
```
Hook 'turn_death_check' declares after=['turn_nonexistent'] but 'turn_nonexistent' is not a defined turn phase hook
  Defined in: actor_lib.death
  Fix: Check spelling or ensure the dependency is defined in a loaded module
```

**Fix**: Verify the dependency hook exists and is spelled correctly.

#### Error: Circular dependency
```
Circular dependency detected in turn phase hooks (authoring error):
  turn_a → turn_b → turn_c → turn_a
  Defined by: test.a, test.b, test.c
```

**Fix**: Remove one of the dependencies to break the cycle. Circular dependencies are ambiguous and must be resolved by the author.

#### Error: Turn phase on entity
```
Actor 'guard' has turn phase behavior 'actor_lib.npc_actions' in behaviors list
  Turn phases should not be attached to entities
```

**Fix**: Remove the turn phase module from the entity's behaviors list. Turn phases execute globally, not per-entity.

## Hook Invocation Patterns

### Turn Phase Invocation

Turn phases are invoked by the turn executor after a successful player command:

1. Player command succeeds
2. Turn count increments
3. Turn phases execute in dependency order
4. Each phase handler is called with `entity=None`
5. Narration messages collected and returned

**Handler Signature**:
```python
def on_turn_phase(entity, accessor, context):
    """
    Args:
        entity: Always None for turn phases
        accessor: StateAccessor for game state access
        context: Dict with:
            - "hook": Hook name (e.g., "turn_npc_action")
            - "actor_id": Actor who triggered the turn
            - "current_turn": Current turn number

    Returns:
        EventResult with:
            - allow: Always True for turn phases
            - feedback: Optional narration message
    """
    pass
```

### Entity Hook Invocation

Entity hooks are invoked when code specifically calls `behavior_manager.invoke_behavior()` or `accessor.update()` with an event that maps to the hook:

```python
# Example: Visibility check
from src.behavior_manager import BehaviorManager

def is_entity_visible(entity, observer_id, behavior_manager, accessor):
    """Check if entity is visible to observer."""
    context = {
        "actor_id": observer_id,
        "method": "examine"
    }

    # Invoke entity_visibility_check hook
    result = behavior_manager.invoke_behavior(
        entity,
        "on_observe",  # Event name
        accessor,
        context
    )

    return result.allow
```

## Complete Examples

### Example 1: Simple Turn Phase

```python
# File: behavior_libraries/infrastructure_lib/scheduled_events.py

vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_scheduled_events",
            "invocation": "turn_phase",
            "after": [],  # Runs first
            "description": "Process scheduled events"
        }
    ],
    "events": [
        {
            "event": "on_turn_scheduled",
            "hook": "turn_scheduled_events"
        }
    ]
}

def on_turn_scheduled(entity, accessor, context):
    """Process all scheduled events for current turn."""
    current_turn = context["current_turn"]
    messages = []

    for event in accessor.game_state.scheduled_events:
        if event.properties.get("trigger_turn") == current_turn:
            messages.append(f"Event triggered: {event.name}")

            # Mark as processed if not repeating
            if not event.properties.get("repeating"):
                event.properties["processed"] = True

    return EventResult(
        allow=True,
        feedback="\n".join(messages) if messages else None
    )
```

### Example 2: Turn Phase with Dependencies

```python
# File: behavior_libraries/actor_lib/environment.py

vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_environmental_effect",
            "invocation": "turn_phase",
            "after": ["turn_npc_action"],  # Run after NPCs act
            "description": "Apply environmental hazards"
        }
    ],
    "events": [
        {
            "event": "on_environmental_effect",
            "hook": "turn_environmental_effect"
        }
    ]
}

def on_environmental_effect(entity, accessor, context):
    """Apply environmental damage to all actors."""
    messages = []

    for actor in accessor.game_state.actors.values():
        location = accessor.get_location(actor.location)

        # Check for cold damage
        if location.properties.get("temperature") == "FREEZING":
            if not actor.properties.get("cold_resistant"):
                damage = 2
                actor.states["health"] = actor.states.get("health", 100) - damage
                messages.append(f"{actor.name} takes {damage} cold damage.")

    return EventResult(
        allow=True,
        feedback="\n".join(messages) if messages else None
    )
```

### Example 3: Entity Hook

```python
# File: examples/my_game/behaviors/stealth.py

vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_visibility_check",
            "invocation": "entity",
            "description": "Check stealth and invisibility"
        }
    ],
    "events": [
        {
            "event": "on_observe",
            "hook": "entity_visibility_check"
        }
    ]
}

def on_observe(entity, accessor, context):
    """Check if entity is visible considering stealth."""
    observer_id = context.get("actor_id")

    # Invisible entities always hidden
    if entity.states.get("invisible"):
        return EventResult(allow=False)

    # Stealthed entities - check observer perception
    if entity.states.get("stealthed"):
        observer = accessor.get_actor(observer_id)
        perception = observer.properties.get("perception", 5)
        stealth = entity.properties.get("stealth", 5)

        if stealth > perception:
            return EventResult(allow=False)  # Hidden

    return EventResult(allow=True)  # Visible
```

## Migration from Old System

If you have code using the old `src/hooks.py` constants, here's how to migrate:

### Step 1: Replace Hook Constants

**Old**:
```python
from src import hooks

# Using constants
hook_name = hooks.NPC_ACTION
```

**New**:
```python
# Use string literals directly
hook_name = "turn_npc_action"
```

### Step 2: Add Hook Definitions

**Old** (implicit):
```python
# Hook defined in src/hooks.py
# No vocabulary needed
```

**New** (explicit):
```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_npc_action",
            "invocation": "turn_phase",
            "after": [],
            "description": "Execute NPC actions"
        }
    ]
}
```

### Step 3: Update Hook Names

Old hook names didn't follow prefix conventions. Update them:

| Old Hook | New Hook | Type |
|----------|----------|------|
| `npc_action` | `turn_npc_action` | Turn phase |
| `environmental_effect` | `turn_environmental_effect` | Turn phase |
| `condition_tick` | `turn_condition_tick` | Turn phase |
| `death_check` | `turn_death_check` | Turn phase |
| `location_entered` | `entity_location_entered` | Entity |
| `visibility_check` | `entity_visibility_check` | Entity |

### Step 4: Replace extra_turn_phases

**Old**:
```json
{
  "metadata": {
    "extra_turn_phases": [
      "turn_scheduled_events",
      "turn_commitments"
    ]
  }
}
```

**New**:
Remove `extra_turn_phases` entirely. Turn phases are discovered from behavior vocabularies and ordered by dependencies.

## Best Practices

### 1. Use Descriptive Hook Names

Good: `turn_environmental_effect`, `entity_visibility_check`

Bad: `turn_phase1`, `entity_check`

### 2. Document Hook Purpose

Always include a clear description:

```python
{
    "hook_id": "turn_condition_tick",
    "invocation": "turn_phase",
    "after": ["turn_environmental_effect"],
    "description": "Progress all actor conditions (poison, disease, etc.)"
}
```

### 3. Minimize Dependencies

Only declare dependencies you actually need:

```python
# Good - only depends on what's needed
{
    "hook_id": "turn_death_check",
    "after": ["turn_condition_tick"]  # Must run after conditions update
}

# Bad - unnecessary dependencies
{
    "hook_id": "turn_death_check",
    "after": ["turn_npc_action", "turn_environmental_effect", "turn_condition_tick"]
}
```

### 4. Use before for Game Extensions

When extending library code, use `before` to avoid modifying libraries:

```python
# In game code
{
    "hook_id": "turn_my_game_hook",
    "invocation": "turn_phase",
    "before": ["turn_npc_action"]  # Insert before library hook
}
```

### 5. Handle Missing Context Gracefully

Context dict may not have all fields:

```python
def on_turn_phase(entity, accessor, context):
    current_turn = context.get("current_turn", 0)  # Default if missing
    actor_id = context.get("actor_id", ActorId("player"))
```

### 6. Return Meaningful Feedback

Turn phase feedback appears in narration:

```python
# Good
return EventResult(allow=True, feedback="The wind howls through the mountains.")

# Bad - too verbose or technical
return EventResult(allow=True, feedback="Environmental effect phase completed successfully.")
```

## Troubleshooting

### Game won't load - validation error

Read the error message carefully. It will identify:
- Which hook has the problem
- What the problem is
- Which module defined the hook

Fix the hook definition in that module's vocabulary.

### Turn phases execute in wrong order

Check dependency declarations:
- Use `after` to declare hooks that must run first
- Use `before` to declare hooks that must run later
- Verify you're not creating circular dependencies

Enable debug logging to see execution order:
```python
# In turn_executor.py or game engine
print(f"Turn phases will execute in order: {turn_executor._ordered_turn_phases}")
```

### Entity hook not firing

Verify:
1. Hook is defined in vocabulary with `invocation: "entity"`
2. Event is wired to the hook in vocabulary
3. Code is actually invoking the event (via `invoke_behavior` or `accessor.update`)
4. Entity has the behavior module in its `behaviors` list

### Turn phase appears twice

This happens if two different modules define the same hook. The engine will raise an error at load time showing both modules. Decide which module should own the hook and remove it from the other.

## See Also

- [Authoring Guide](authoring_guide.md) - General game authoring patterns
- [Quick Reference](quick_reference.md) - Syntax quick reference
- [Architectural Conventions](../user_docs/architectural_conventions.md) - System architecture
- [Hook System Redesign](designs/hook_system_redesign.md) - Complete implementation details
