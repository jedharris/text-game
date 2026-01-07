# Companion Activation Pattern

## Overview

This document describes the generalized companion activation pattern established during Frozen Reaches salamander implementation. This pattern should be used for ALL future companion recruitment in the big game.

## Infrastructure Location

All companion infrastructure lives in `behavior_libraries/companion_lib/`:
- `following.py` - Companion following mechanics (existing)
- `activation.py` - Companion activation utilities (NEW - created Jan 2026)

## Key Principle

**Use `companion_lib` consistently across all handlers.**

DO NOT create custom `player.properties.companions` lists or ad-hoc following logic. The companion_lib provides standardized infrastructure that works for all companion types.

## Pattern: Trust-Based Companion Activation

### Step 1: Configure Actor with Trust State

In `game_state.json`, configure the actor with:

```json
{
  "id": "salamander",
  "properties": {
    "trust_state": {
      "current": 0,
      "floor": 0,
      "ceiling": 5
    },
    "state_machine": {
      "states": ["neutral", "friendly", "companion"],
      "initial": "neutral"
    }
  }
}
```

### Step 2: Wire Trust Increase in Behavior Handler

In your behavior module (e.g., `salamanders.py`), import the activation utility:

```python
from behavior_libraries.companion_lib.activation import activate_companion_on_trust_threshold
from src.infrastructure_utils import apply_trust_change
```

In your gift/interaction handler:

```python
# Increase trust with state transitions
result = apply_trust_change(
    entity=actor,
    delta=1,
    transitions={"1": "friendly", "3": "companion"},
)

# Activate companion status when trust reaches threshold
if result["new_trust"] >= 3 and result["state_changed"]:
    companion_result = activate_companion_on_trust_threshold(
        actor=actor,
        accessor=accessor,
        trust_threshold=3,
        companion_message=(
            f"{actor.name} has become your companion! "
            f"They will follow wherever you go."
        ),
    )
    if companion_result:
        return companion_result
```

### Step 3: Check Companion Benefits in Other Handlers

In handlers that grant benefits to companions (e.g., hypothermia immunity), use:

```python
from behavior_libraries.companion_lib.activation import check_companion_benefit

# Check for salamander companion (cold immunity)
if check_companion_benefit(accessor, "salamander"):
    return EventResult(allow=True, feedback=None)  # Grant immunity
```

This replaces ad-hoc checks like:
```python
# DON'T DO THIS:
companions = player.properties.get("companions", [])
for comp in companions:
    if "salamander" in comp.get("id", ""):
        ...
```

## Companion Types and Use Cases

### Salamander (Frozen Reaches) ✅ IMPLEMENTED
- **Trigger**: Trust level 3 via fire gifts
- **Benefit**: Hypothermia immunity (full cold protection)
- **Implementation**: [salamanders.py](../examples/big_game/behaviors/regions/frozen_reaches/salamanders.py)
- **Validation**: [test_salamander_companion.txt](../walkthroughs/test_salamander_companion.txt)

### Wolf Pack (Beast Wilds) - FUTURE
- **Trigger**: Trust level 3 via bear cub rescue + food gifts
- **Benefits**: Combat support, tracking ability
- **Restrictions**: Cannot enter water zones (salamander zones)
- **Pattern to use**: Same `activate_companion_on_trust_threshold()` pattern

### Sira (Beast Wilds) - FUTURE
- **Trigger**: Rescue from trap within 15 turns
- **Benefits**: Combat support, herb identification
- **Restrictions**: Human companion - needs spore mask in fungal zones
- **Pattern to use**: Same activation pattern, different trigger event

### Echo (Endgame) - FUTURE
- **Trigger**: Trust level 5+ at waystone completion
- **Benefits**: Permanent companion, special abilities
- **Triumphant ending requirement**
- **Pattern to use**: Same activation pattern at endgame trigger

## API Reference

### activate_companion_on_trust_threshold()

```python
def activate_companion_on_trust_threshold(
    actor: Any,
    accessor: Any,
    trust_threshold: int = 3,
    companion_message: str = None,
) -> EventResult | None
```

Activates companion status when actor's trust reaches threshold.

**Parameters:**
- `actor`: The actor to potentially activate as companion
- `accessor`: StateAccessor instance
- `trust_threshold`: Minimum trust level to activate (default 3)
- `companion_message`: Custom message when companion activates

**Returns:**
- `EventResult` with activation message if trust >= threshold and not already companion
- `None` if trust insufficient or already a companion

**Usage Example:**
```python
companion_result = activate_companion_on_trust_threshold(
    actor=salamander,
    accessor=accessor,
    trust_threshold=3,
    companion_message="The salamander becomes your loyal companion!",
)
if companion_result:
    return companion_result
```

### activate_companion_on_state_transition()

```python
def activate_companion_on_state_transition(
    actor: Any,
    accessor: Any,
    context: dict[str, Any],
    companion_state: str = "companion",
    companion_message: str = None,
) -> EventResult | None
```

Activates companion status when state machine transitions to specific state.

**Usage Example:**
```python
# In a state change event handler
companion_result = activate_companion_on_state_transition(
    actor=wolf,
    accessor=accessor,
    context=context,  # Contains new_state
    companion_state="ally",
    companion_message="The wolf pledges loyalty!",
)
if companion_result:
    return companion_result
```

### check_companion_benefit()

```python
def check_companion_benefit(
    accessor: Any,
    companion_type: str,
    benefit_check: callable = None,
) -> bool
```

Checks if player has a companion that provides a specific benefit.

**Parameters:**
- `accessor`: StateAccessor instance
- `companion_type`: String to match in companion ID (e.g., "salamander", "wolf")
- `benefit_check`: Optional callable(companion) -> bool for custom validation

**Returns:**
- `True` if player has matching companion at current location
- `False` otherwise

**Usage Examples:**
```python
# Simple type check (hypothermia immunity)
if check_companion_benefit(accessor, "salamander"):
    return EventResult(allow=True, feedback=None)  # No cold damage

# Custom check (only alpha wolves provide tracking)
def is_alpha(comp):
    return "alpha" in comp.id.lower()

if check_companion_benefit(accessor, "wolf", is_alpha):
    # Grant tracking ability
    ...
```

## Migration Notes

### Before (Ad-hoc Pattern)
```python
# Custom companions list
companions = player.properties.get("companions", [])
for comp in companions:
    comp_id = comp.get("id", "") if isinstance(comp, dict) else str(comp)
    if "salamander" in comp_id.lower():
        # Grant benefit
        ...
```

### After (Standardized Pattern)
```python
from behavior_libraries.companion_lib.activation import check_companion_benefit

if check_companion_benefit(accessor, "salamander"):
    # Grant benefit
    ...
```

## Testing Pattern

Every companion recruitment should have a comprehensive walkthrough:

1. **Trust building** - Verify trust progression (0 → 1 → 2 → 3)
2. **State transitions** - Verify state machine changes
3. **Companion activation** - Verify `is_companion` property set
4. **Following behavior** - Verify companion moves with player
5. **Benefits** - Verify companion-specific benefits work
6. **Restrictions** - Verify companion can't enter restricted zones (future)

See [test_salamander_companion.txt](../walkthroughs/test_salamander_companion.txt) for reference.

## Cross-References

- **Infrastructure**: [companion_lib/following.py](../behavior_libraries/companion_lib/following.py)
- **Infrastructure**: [companion_lib/activation.py](../behavior_libraries/companion_lib/activation.py)
- **Implementation**: [salamanders.py](../examples/big_game/behaviors/regions/frozen_reaches/salamanders.py)
- **Implementation**: [hypothermia.py](../examples/big_game/behaviors/regions/frozen_reaches/hypothermia.py)
- **Validation**: [test_salamander_companion.txt](../walkthroughs/test_salamander_companion.txt)
- **Design**: [big_game_overview.md](big_game_overview.md#companion-system)

## Changelog

- **Jan 2, 2026**: Created companion_lib.activation with generalized utilities
- **Jan 2, 2026**: Migrated hypothermia handler to use check_companion_benefit()
- **Jan 2, 2026**: Implemented salamander trust→companion activation
- **Jan 2, 2026**: Validated pattern with test_salamander_companion.txt walkthrough
