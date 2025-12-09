# Actor Interaction System - Implementation Plan

## Document Purpose

This document provides a detailed implementation plan for the actor interaction system described in [Actor Interaction Conceptual Design v3](actor_interaction_conceptual_design_v3.md). It includes phasing, testing strategy, and integration points with the existing engine.

**Companion Documents**:
- [Actor Interaction Conceptual Design v3](actor_interaction_conceptual_design_v3.md) - Design specification
- [Actor Interaction Library Design](actor_interaction_library_design.md) - Behavior module designs
- [Actor Interaction Simplified Cases](actor_interaction_simplified_cases.md) - Use cases for validation
- [Actor Interaction Integration Testing](actor_interaction_integration_testing.md) - Follow-on integration testing (Phase 10)

---

## Implementation Overview

### Goals

1. **Turn Phase System**: Implement post-command hook firing for NPC actions, environmental effects, condition progression, and death checks
2. **Condition System**: Complete lifecycle management for actor conditions
3. **Environmental Effects**: Location part properties affecting actors
4. **Combat Foundation**: Multi-attack actors, damage, and armor
5. **Social Systems**: Services, relationships, morale
6. **Pack Coordination**: Simple follow-the-leader group behavior

### Architecture Approach

The implementation builds on existing engine infrastructure:
- **Hooks system** (`src/hooks.py`): Add new turn phase hooks
- **Behavior manager**: Use existing module loading and vocabulary merging
- **StateAccessor**: Extend with new query methods where needed
- **Event registry**: Register new events via vocabulary

New code lives in:
- `behaviors/library/actors/` - Behavior library modules
- `src/hooks.py` - New hook constants
- Engine integration points for turn phase firing

---

## Phase 0: Infrastructure Prerequisites

**Goal**: Establish engine-level infrastructure required by all subsequent phases.

### 0.1 Turn Phase Hook Constants

**File**: `src/hooks.py`

Add new hook constants:

```python
# Turn phase hooks (fire after successful player command)
TURN_END = "turn_end"
NPC_ACTION = "npc_action"
ENVIRONMENTAL_EFFECT = "environmental_effect"
CONDITION_TICK = "condition_tick"
DEATH_CHECK = "death_check"
```

**Test**: Verify constants are importable and have correct values.

### 0.2 Turn Phase Firing in Engine

**File**: `src/llm_protocol.py` (or `src/game_engine.py`)

After a successful command execution, fire turn phase hooks in order:

```python
def _fire_turn_phases(self, accessor: StateAccessor) -> List[str]:
    """Fire all turn phase hooks after successful command."""
    messages = []

    # 1. NPC Action Phase
    event = self.behavior_manager.get_event_for_hook(hooks.NPC_ACTION)
    if event:
        result = self._fire_npc_actions(accessor, event)
        if result:
            messages.extend(result)

    # 2. Environmental Effects Phase
    event = self.behavior_manager.get_event_for_hook(hooks.ENVIRONMENTAL_EFFECT)
    if event:
        result = self._fire_environmental_effects(accessor, event)
        if result:
            messages.extend(result)

    # 3. Condition Tick Phase
    event = self.behavior_manager.get_event_for_hook(hooks.CONDITION_TICK)
    if event:
        result = self._fire_condition_ticks(accessor, event)
        if result:
            messages.extend(result)

    # 4. Death Check Phase
    event = self.behavior_manager.get_event_for_hook(hooks.DEATH_CHECK)
    if event:
        result = self._fire_death_checks(accessor, event)
        if result:
            messages.extend(result)

    return messages
```

**Key Design Decision**: Turn phases only fire after **successful** commands. Failed commands do not advance game time.

**Test**:
- Verify hooks fire in correct order after successful command
- Verify hooks do NOT fire after failed command
- Verify hook results are collected and returned

### 0.3 Part Access API

**File**: `src/state_accessor.py`

Add method to get actor's current spatial part:

```python
def get_actor_part(self, actor: Actor) -> Optional[Part]:
    """
    Get the spatial part an actor currently occupies.

    Returns the Part entity based on actor's focused_on property
    or location, or None if not in a spatial location.
    """
    # If actor is focused on a part, return that part
    focused_on = actor.properties.get("focused_on")
    if focused_on:
        part = self.get_part(focused_on)
        if part:
            return part

    # Otherwise check if location has parts
    location = self.get_location(actor.location)
    if not location:
        return None

    # Return default part if exists
    parts = self.get_parts_of(actor.location)
    if parts:
        # Return first part as default (or could have "default_part" property)
        return parts[0]

    return None
```

**Test**:
- Actor focused on a part returns that part
- Actor in location with parts returns default part
- Actor in location without parts returns None

### 0.4 Effect String Registry

**Approach**: Effects are registered via vocabulary and validated at load time.

**File**: `behaviors/library/actors/effects.py` (new module, just for effect registration)

```python
vocabulary = {
    "effects": [
        {"effect": "cannot_move", "description": "Prevents movement commands"},
        {"effect": "cannot_swim", "description": "Prevents swimming/self-rescue"},
        {"effect": "cannot_attack", "description": "Prevents attack commands"},
        {"effect": "agility_reduced", "description": "Flavor - behaviors may check"},
        {"effect": "strength_reduced", "description": "Flavor - behaviors may check"},
        {"effect": "blinded", "description": "Affects perception, targeting"},
        {"effect": "slowed", "description": "Movement costs extra turns"}
    ]
}
```

**Validation**: BehaviorManager validates effect strings in condition definitions at load time.

**Test**:
- Valid effects pass validation
- Invalid effects raise error at load time
- Custom effects can be registered by author modules

### Phase 0 Testing Summary

| Test | Description |
|------|-------------|
| `test_hook_constants_exist` | All new hooks defined in hooks.py |
| `test_turn_phases_fire_on_success` | Hooks fire after successful command |
| `test_turn_phases_skip_on_failure` | Hooks don't fire after failed command |
| `test_turn_phase_order` | Hooks fire in correct sequence |
| `test_get_actor_part_focused` | Returns focused part |
| `test_get_actor_part_default` | Returns default part in spatial location |
| `test_get_actor_part_none` | Returns None for non-spatial location |
| `test_effect_validation_pass` | Valid effects accepted |
| `test_effect_validation_fail` | Invalid effects rejected |

---

## Phase 1: Condition System

**Goal**: Implement complete condition lifecycle - apply, progress, treat, remove.

**Depends on**: Phase 0 (turn phase hooks, effect registry)

### 1.1 Condition Module

**File**: `behaviors/library/actors/conditions.py`

**Public API**:

```python
def apply_condition(
    accessor: StateAccessor,
    actor: Actor,
    condition_name: str,
    condition_data: Dict[str, Any],
    source_id: Optional[str] = None
) -> ConditionResult:
    """Apply or increase a condition on an actor."""

def remove_condition(
    accessor: StateAccessor,
    actor: Actor,
    condition_name: str,
    amount: Optional[int] = None
) -> ConditionResult:
    """Remove or reduce a condition's severity."""

def has_condition(actor: Actor, condition_name: str) -> bool:
    """Check if actor has a condition."""

def get_condition(actor: Actor, condition_name: str) -> Optional[Dict]:
    """Get condition data, or None if not present."""

def has_effect(actor: Actor, effect_name: str) -> bool:
    """Check if actor has any condition with given effect."""

def is_immune(actor: Actor, condition_type: str) -> bool:
    """Check if actor is immune to a condition type."""

def get_resistance(actor: Actor, condition_type: str) -> int:
    """Get resistance percentage (0-100) for condition type."""
```

**Condition Application Logic**:

1. Check immunities array - if immune, return blocked
2. Check `body.form == "construct"` for automatic poison/disease/bleeding immunity
3. Calculate resistance reduction: `severity * (1 - resistance/100)`, round up
4. If condition exists, add severities (stack), cap at 100
5. Take longer duration of existing vs new
6. Fire `on_condition_apply` behavior on actor
7. Update actor properties via StateAccessor

**Vocabulary**:

```python
vocabulary = {
    "events": [
        {
            "event": "on_condition_apply",
            "description": "Called when applying a condition to an actor"
        },
        {
            "event": "on_condition_remove",
            "description": "Called when removing a condition from an actor"
        },
        {
            "event": "on_condition_tick",
            "hook": "condition_tick",
            "description": "Called each turn to progress all conditions"
        }
    ]
}
```

### 1.2 Condition Tick Handler

**Event Handler** (registered to `condition_tick` hook):

```python
def on_condition_tick(entity, accessor, context) -> Optional[EventResult]:
    """Progress all conditions on an actor each turn."""
    conditions = entity.properties.get("conditions", {})
    if not conditions:
        return None

    messages = []
    conditions_to_remove = []

    for name, data in conditions.items():
        # Apply damage_per_turn
        damage = data.get("damage_per_turn", 0)
        if damage > 0:
            health = entity.properties.get("health", 100)
            entity.properties["health"] = health - damage
            messages.append(f"{entity.name} takes {damage} damage from {name}")

        # Increase severity by progression_rate
        progression = data.get("progression_rate", 0)
        if progression > 0:
            data["severity"] = min(100, data.get("severity", 0) + progression)

        # Decrease duration
        duration = data.get("duration")
        if duration is not None:
            data["duration"] = duration - 1
            if data["duration"] <= 0:
                conditions_to_remove.append(name)

        # Check severity
        if data.get("severity", 0) <= 0:
            conditions_to_remove.append(name)

    # Remove expired conditions
    for name in conditions_to_remove:
        del conditions[name]
        messages.append(f"{name} condition ends on {entity.name}")

    if messages:
        return EventResult(allow=True, message="; ".join(messages))
    return None
```

### 1.3 Resistance Calculation Utility

```python
def calculate_resisted_value(base_value: int, resistance_percent: int, round_up: bool = True) -> int:
    """
    Apply resistance to reduce a value.

    Formula: actual = base * (1 - resistance/100)
    Rounding: ceiling for severity increases (round_up=True), standard for damage
    Minimum: 0
    """
    if resistance_percent >= 100:
        return 0

    reduced = base_value * (1 - resistance_percent / 100)

    if round_up:
        return max(0, math.ceil(reduced))
    return max(0, round(reduced))
```

### Phase 1 Testing Summary

| Test | Description |
|------|-------------|
| `test_apply_condition_new` | Apply new condition to actor |
| `test_apply_condition_stack` | Stacking increases severity |
| `test_apply_condition_immune` | Immune actors block condition |
| `test_apply_condition_construct_immune` | Constructs immune to poison/disease/bleeding |
| `test_apply_condition_resistance` | Resistance reduces severity |
| `test_remove_condition_full` | Remove condition entirely |
| `test_remove_condition_partial` | Reduce severity by amount |
| `test_has_condition` | Check condition presence |
| `test_has_effect` | Check effect across conditions |
| `test_condition_tick_damage` | damage_per_turn applies |
| `test_condition_tick_progression` | severity increases by progression_rate |
| `test_condition_tick_duration` | duration decrements, removes at 0 |
| `test_resistance_calculation` | Correct reduction with rounding |

---

## Phase 2: Environmental Effects

**Goal**: Location part properties affect actors each turn.

**Depends on**: Phase 0 (part access API), Phase 1 (condition system)

### 2.1 Environment Module

**File**: `behaviors/library/actors/environment.py`

**Public API**:

```python
def apply_environmental_effects(
    accessor: StateAccessor,
    actor: Actor,
    part: Part
) -> List[EnvironmentResult]:
    """Apply all environmental effects from a part to an actor."""

def check_breath(accessor: StateAccessor, actor: Actor, part: Part) -> Optional[EnvironmentResult]:
    """Check and update breath for an actor in a part."""

def needs_breath(actor: Actor) -> bool:
    """Check if actor needs to breathe (not a construct)."""

def get_cover_value(part: Part) -> int:
    """Get cover percentage (0-100) provided by a part."""
```

### 2.2 Environmental Effect Handler

**Event Handler** (registered to `environmental_effect` hook):

```python
def on_environmental_effect(entity, accessor, context) -> Optional[EventResult]:
    """Apply environmental effects to actor based on their current part."""
    part = accessor.get_actor_part(entity)
    if not part:
        return None

    results = apply_environmental_effects(accessor, entity, part)
    if results:
        messages = [r.message for r in results if r.message]
        return EventResult(allow=True, message="; ".join(messages))
    return None
```

### 2.3 Breath System

```python
def check_breath(accessor: StateAccessor, actor: Actor, part: Part) -> Optional[EnvironmentResult]:
    """Handle breath tracking in breathable/non-breathable areas."""
    if not needs_breath(actor):
        return None

    breathable = part.properties.get("breathable", True)

    if breathable:
        # Restore breath to max
        max_breath = actor.properties.get("max_breath", 60)
        if actor.properties.get("breath", max_breath) < max_breath:
            actor.properties["breath"] = max_breath
            return EnvironmentResult(message=f"{actor.name} catches their breath")
        return None

    # Non-breathable area
    # Check for breathing items
    if has_breathing_item(accessor, actor, part):
        return None

    # Decrease breath
    breath = actor.properties.get("breath", 60)
    breath -= 10
    actor.properties["breath"] = breath

    if breath <= 0:
        # Apply drowning damage
        health = actor.properties.get("health", 100)
        actor.properties["health"] = health - 10
        return EnvironmentResult(
            message=f"{actor.name} is drowning! (breath: {breath}, -10 health)"
        )

    return EnvironmentResult(message=f"{actor.name}'s breath: {breath}")
```

### 2.4 Spore/Temperature Effects

```python
SPORE_SEVERITY = {"none": 0, "low": 5, "medium": 10, "high": 15}
TEMPERATURE_CONDITIONS = {
    "freezing": ("hypothermia", 10),
    "cold": ("hypothermia", 5),
    "hot": ("heat_exhaustion", 5),
    "burning": ("heat_exhaustion", 10)
}

def apply_environmental_effects(accessor, actor, part):
    results = []

    # Breath
    breath_result = check_breath(accessor, actor, part)
    if breath_result:
        results.append(breath_result)

    # Spores
    spore_level = part.properties.get("spore_level", "none")
    if spore_level != "none" and not is_immune(actor, "disease"):
        severity = SPORE_SEVERITY.get(spore_level, 0)
        severity = calculate_resisted_value(severity, get_resistance(actor, "disease"))
        if severity > 0:
            apply_condition(accessor, actor, "fungal_infection", {
                "severity": severity,
                "damage_per_turn": 1,
                "contagious_range": "touch"
            })
            results.append(EnvironmentResult(
                message=f"{actor.name} exposed to spores (+{severity} infection)"
            ))

    # Temperature
    temperature = part.properties.get("temperature", "normal")
    if temperature in TEMPERATURE_CONDITIONS and not is_immune(actor, "cold"):
        condition_name, severity = TEMPERATURE_CONDITIONS[temperature]
        severity = calculate_resisted_value(severity, get_resistance(actor, "cold"))
        if severity > 0:
            apply_condition(accessor, actor, condition_name, {
                "severity": severity,
                "damage_per_turn": 2
            })
            results.append(EnvironmentResult(
                message=f"{actor.name} affected by {temperature} temperature"
            ))

    return results
```

### Phase 2 Testing Summary

| Test | Description |
|------|-------------|
| `test_breath_decrease_non_breathable` | Breath decreases in non-breathable areas |
| `test_breath_drowning_damage` | Drowning damage when breath depleted |
| `test_breath_restore_breathable` | Breath restores in breathable areas |
| `test_breath_item_prevents_loss` | Breathing items prevent breath loss |
| `test_construct_no_breath` | Constructs don't need breath |
| `test_spore_applies_condition` | Spores apply fungal infection |
| `test_spore_resistance_reduces` | Resistance reduces spore severity |
| `test_temperature_applies_condition` | Temperature extremes apply conditions |
| `test_environmental_hook_fires` | Hook fires for all actors |

---

## Phase 3: Combat Foundation

**Goal**: Multi-attack actors, damage application, armor, death checks.

**Depends on**: Phase 1 (condition system for attack conditions)

### 3.1 Combat Module

**File**: `behaviors/library/actors/combat.py`

**Public API**:

```python
def get_attacks(actor: Actor) -> List[Dict]:
    """Get all attacks available to an actor."""

def select_attack(attacker: Actor, target: Actor, context: Dict) -> Optional[Dict]:
    """Select an appropriate attack based on situation."""

def execute_attack(
    accessor: StateAccessor,
    attacker: Actor,
    target: Actor,
    attack: Dict
) -> AttackResult:
    """Execute an attack against a target."""

def calculate_damage(attack: Dict, attacker: Actor, target: Actor, context: Dict) -> int:
    """Calculate final damage after armor and modifiers."""
```

### 3.2 Attack Execution

```python
def execute_attack(accessor, attacker, target, attack):
    """Execute an attack against a target."""
    # Calculate damage
    base_damage = attack.get("damage", 0)
    armor = target.properties.get("armor", 0)
    damage = max(0, base_damage - armor)

    # Apply cover reduction if target in cover
    if target.properties.get("posture") == "cover":
        cover_obj_id = target.properties.get("focused_on")
        if cover_obj_id:
            cover_obj = accessor.get_item(cover_obj_id)
            if cover_obj:
                cover_value = cover_obj.properties.get("cover_value", 0)
                damage = int(damage * (1 - cover_value / 100))

    # Apply damage
    health = target.properties.get("health", 100)
    target.properties["health"] = health - damage

    messages = [f"{attacker.name} hits {target.name} with {attack['name']} for {damage} damage"]
    conditions_applied = []

    # Apply condition if attack has one
    applies_condition = attack.get("applies_condition")
    if applies_condition:
        condition_name = applies_condition.get("name")
        result = apply_condition(accessor, target, condition_name, applies_condition, attacker.id)
        if result.success:
            conditions_applied.append(condition_name)
            messages.append(f"{target.name} is affected by {condition_name}")

    # Fire on_damage behavior on target
    context = {
        "damage": damage,
        "attacker_id": attacker.id,
        "attack_type": attack.get("type")
    }
    accessor.behavior_manager.invoke_behavior(target, "on_damage", accessor, context)

    return AttackResult(
        success=True,
        damage=damage,
        conditions_applied=conditions_applied,
        message="; ".join(messages)
    )
```

### 3.3 Attack Selection Logic

```python
def select_attack(attacker, target, context):
    """Select appropriate attack based on situation."""
    attacks = get_attacks(attacker)
    if not attacks:
        return None

    target_health_pct = (target.properties.get("health", 100) /
                         target.properties.get("max_health", 100))

    # Prefer control effects when target is healthy
    for attack in attacks:
        if target_health_pct > 0.5 and attack.get("effect") == "knockdown":
            return attack

    # Prefer condition attacks if target doesn't have condition
    for attack in attacks:
        applies_condition = attack.get("applies_condition")
        if applies_condition:
            condition_name = applies_condition.get("name")
            if not has_condition(target, condition_name):
                return attack

    # Default: highest damage
    return max(attacks, key=lambda a: a.get("damage", 0))
```

### 3.4 Death Check Handler

**Event Handler** (registered to `death_check` hook):

```python
def on_death_check(entity, accessor, context) -> Optional[EventResult]:
    """Check if actor's health <= 0 and invoke on_death behavior."""
    health = entity.properties.get("health")
    if health is None:
        return None  # Actor doesn't have health tracking

    if health <= 0:
        # Invoke on_death behavior - author implements death handling
        result = accessor.behavior_manager.invoke_behavior(
            entity, "on_death", accessor, {}
        )
        if result and result.message:
            return result
        return EventResult(allow=True, message=f"{entity.name} has died")

    return None
```

### 3.5 Vocabulary

```python
vocabulary = {
    "verbs": [
        {
            "word": "attack",
            "event": "on_attack",
            "synonyms": ["hit", "strike", "fight"],
            "object_required": True
        }
    ],
    "events": [
        {
            "event": "on_attack",
            "description": "Called when an actor attacks"
        },
        {
            "event": "on_damage",
            "description": "Called when an actor takes damage"
        },
        {
            "event": "on_death",
            "hook": "death_check",
            "description": "Called when health reaches 0"
        }
    ]
}
```

### Phase 3 Testing Summary

| Test | Description |
|------|-------------|
| `test_get_attacks` | Retrieve actor's attack array |
| `test_select_attack_knockdown` | Prefers knockdown vs healthy target |
| `test_select_attack_condition` | Prefers condition if target doesn't have it |
| `test_select_attack_damage` | Falls back to highest damage |
| `test_execute_attack_damage` | Applies damage to target |
| `test_execute_attack_armor` | Armor reduces damage |
| `test_execute_attack_cover` | Cover reduces damage |
| `test_execute_attack_condition` | Attack applies condition |
| `test_death_check_triggers` | Death check fires on_death at health <= 0 |
| `test_death_check_skips_alive` | Death check skips actors with health > 0 |

---

## Phase 4: NPC Actions

**Goal**: NPCs take actions after player commands.

**Depends on**: Phase 3 (combat for hostile NPC attacks)

### 4.1 NPC Action Phase Handler

**Event Handler** (registered to `npc_action` hook):

```python
def fire_npc_actions(accessor, event_name):
    """Fire NPC actions for all actors, alphas first."""
    messages = []

    # Get all actors except player
    all_actors = []
    for location in accessor.state.locations:
        actors = accessor.get_actors_in_location(location.id)
        all_actors.extend([a for a in actors if a.id != "player"])

    # Sort: alphas before followers
    def pack_sort_key(actor):
        role = actor.properties.get("ai", {}).get("pack_role", "")
        return 0 if role == "alpha" else 1

    all_actors.sort(key=pack_sort_key)

    for actor in all_actors:
        result = accessor.behavior_manager.invoke_behavior(
            actor, event_name, accessor, {}
        )
        if result and result.message:
            messages.append(result.message)

    return messages
```

### 4.2 Basic NPC Action Behavior

Entities with the NPC action behavior implement `npc_take_action`:

```python
def npc_take_action(entity, accessor, context) -> Optional[EventResult]:
    """Default NPC action behavior - early out if nothing to do."""
    ai = entity.properties.get("ai", {})
    disposition = ai.get("disposition", "neutral")

    # Early out: not hostile, nothing to do
    if disposition != "hostile":
        return None

    # Check if player is in same location
    player = accessor.get_actor("player")
    if not player or entity.location != player.location:
        return None

    # Attack player
    attacks = get_attacks(entity)
    if not attacks:
        return None

    attack = select_attack(entity, player, {})
    if attack:
        result = execute_attack(accessor, entity, player, attack)
        return EventResult(allow=True, message=result.message)

    return None
```

### 4.3 Vocabulary

```python
vocabulary = {
    "events": [
        {
            "event": "npc_take_action",
            "hook": "npc_action",
            "description": "Called each turn for NPC to take action"
        }
    ]
}
```

### Phase 4 Testing Summary

| Test | Description |
|------|-------------|
| `test_npc_action_hostile_attacks` | Hostile NPC in same location attacks player |
| `test_npc_action_neutral_skips` | Neutral NPC does nothing |
| `test_npc_action_different_location` | NPC in different location does nothing |
| `test_npc_action_alpha_first` | Alphas processed before followers |
| `test_npc_action_all_locations` | NPCs everywhere processed |

---

## Phase 5: Cure/Treatment

**Goal**: Items with `cures` property can treat conditions.

**Depends on**: Phase 1 (condition system)

### 5.1 Treatment Module

**File**: `behaviors/library/actors/treatment.py`

**Public API**:

```python
def can_treat(item: Item, condition_name: str) -> bool:
    """Check if item can treat a condition."""

def treat_condition(
    accessor: StateAccessor,
    item: Item,
    target_actor: Actor,
    condition_name: Optional[str] = None
) -> TreatmentResult:
    """Use an item to treat conditions on an actor."""

def get_treatable_conditions(item: Item) -> List[str]:
    """Get list of conditions this item can treat."""
```

### 5.2 Treatment Logic

```python
def treat_condition(accessor, item, target_actor, condition_name=None):
    """Use item to treat conditions."""
    treatable = get_treatable_conditions(item)
    if not treatable:
        return TreatmentResult(success=False, message="Item cannot treat conditions")

    cure_amount = item.properties.get("cure_amount", 100)
    conditions_treated = []

    target_conditions = target_actor.properties.get("conditions", {})

    for cond_name in treatable:
        if condition_name and cond_name != condition_name:
            continue

        if cond_name in target_conditions:
            result = remove_condition(accessor, target_actor, cond_name, cure_amount)
            if result.success:
                conditions_treated.append(cond_name)

    if not conditions_treated:
        return TreatmentResult(
            success=False,
            message=f"{target_actor.name} doesn't have any conditions this can treat"
        )

    # Consume item if consumable
    if item.properties.get("consumable", False):
        # Remove from inventory or location
        player = accessor.get_actor("player")
        if item.id in player.inventory:
            player.inventory.remove(item.id)
        # Mark item as consumed
        accessor.state.items.remove(item)

    return TreatmentResult(
        success=True,
        conditions_treated=conditions_treated,
        item_consumed=item.properties.get("consumable", False),
        message=f"Treated {', '.join(conditions_treated)} on {target_actor.name}"
    )
```

### 5.3 on_receive Auto-Treatment

When an actor receives a curative item, check if it can treat their conditions:

```python
def on_receive_treatment(entity, accessor, context) -> Optional[EventResult]:
    """Auto-apply treatment when receiving curative item."""
    item_id = context.get("item_id")
    item = accessor.get_item(item_id)
    if not item:
        return None

    treatable = get_treatable_conditions(item)
    if not treatable:
        return None

    # Check if this actor has treatable conditions
    conditions = entity.properties.get("conditions", {})
    matching = [c for c in treatable if c in conditions]

    if matching:
        result = treat_condition(accessor, item, entity)
        if result.success:
            return EventResult(allow=True, message=result.message)

    return None
```

### Phase 5 Testing Summary

| Test | Description |
|------|-------------|
| `test_can_treat_matching` | Item with matching cures returns True |
| `test_can_treat_no_match` | Item without match returns False |
| `test_treat_removes_condition` | Treatment removes condition |
| `test_treat_reduces_severity` | Partial cure reduces severity |
| `test_treat_consumes_item` | Consumable items are consumed |
| `test_on_receive_auto_treats` | Receiving curative item auto-treats |

---

## Phase 6: Services Framework

**Goal**: NPCs offer services in exchange for payment.

**Depends on**: Phase 5 (treatment for cure services), Phase 7 (relationships for discounts)

### 6.1 Services Module

**File**: `behaviors/library/actors/services.py`

**Public API**:

```python
def get_available_services(actor: Actor) -> Dict[str, Dict]:
    """Get all services an NPC offers."""

def can_afford_service(accessor, customer, service_name, npc) -> Tuple[bool, Optional[str]]:
    """Check if customer can afford a service."""

def execute_service(accessor, customer, npc, service_name, payment_item) -> ServiceResult:
    """Execute a service transaction."""

def get_service_cost(npc, service_name, customer) -> int:
    """Get effective cost accounting for trust discounts."""
```

### 6.2 Service Execution

```python
def execute_service(accessor, customer, npc, service_name, payment_item):
    """Execute service transaction."""
    services = npc.properties.get("services", {})
    service = services.get(service_name)
    if not service:
        return ServiceResult(success=False, message=f"{npc.name} doesn't offer {service_name}")

    # Verify payment
    accepts = service.get("accepts", [])
    item_type = payment_item.properties.get("type", payment_item.name)
    if item_type not in accepts and payment_item.name not in accepts:
        return ServiceResult(success=False, message=f"{npc.name} doesn't accept that")

    # Check amount
    required = get_service_cost(npc, service_name, customer)
    amount = payment_item.properties.get("amount", 1)
    if amount < required:
        return ServiceResult(success=False, message=f"Not enough - {npc.name} requires {required}")

    # Execute service effect
    messages = [f"{npc.name} provides {service_name}"]

    # Cure service
    if "cure_amount" in service:
        # Remove conditions from customer
        for condition in customer.properties.get("conditions", {}).keys():
            remove_condition(accessor, customer, condition, service["cure_amount"])
        messages.append("conditions treated")

    # Teaching service
    if "grants" in service:
        knows = customer.properties.setdefault("knows", [])
        if service["grants"] not in knows:
            knows.append(service["grants"])
        messages.append(f"learned {service['grants']}")

    # Healing service
    if "restore_amount" in service:
        health = customer.properties.get("health", 100)
        max_health = customer.properties.get("max_health", 100)
        customer.properties["health"] = min(max_health, health + service["restore_amount"])
        messages.append("health restored")

    # Consume payment
    player = accessor.get_actor("player")
    if payment_item.id in player.inventory:
        player.inventory.remove(payment_item.id)

    # Increment trust
    modify_relationship(accessor, npc, customer.id, "trust", 1)

    return ServiceResult(success=True, message="; ".join(messages))
```

### 6.3 Trust Discounts

```python
def get_service_cost(npc, service_name, customer):
    """Calculate cost with trust discount."""
    services = npc.properties.get("services", {})
    service = services.get(service_name, {})
    base_cost = service.get("amount_required", 1)

    # Check trust level
    relationships = npc.properties.get("relationships", {})
    trust = relationships.get(customer.id, {}).get("trust", 0)

    if trust >= 3:
        return base_cost // 2  # 50% discount

    return base_cost
```

### Phase 6 Testing Summary

| Test | Description |
|------|-------------|
| `test_get_services` | Retrieve NPC's services |
| `test_execute_service_cure` | Cure service removes conditions |
| `test_execute_service_teach` | Teaching service grants knowledge |
| `test_execute_service_heal` | Healing service restores health |
| `test_service_payment_accepted` | Correct payment accepted |
| `test_service_payment_rejected` | Wrong payment rejected |
| `test_service_trust_discount` | High trust gives 50% discount |

---

## Phase 7: Relationship Tracking

**Goal**: Track progressive relationship values with threshold effects.

**Depends on**: None (but used by Phase 6)

### 7.1 Relationships Module

**File**: `behaviors/library/actors/relationships.py`

**Public API**:

```python
def get_relationship(actor: Actor, target_id: str) -> Dict[str, int]:
    """Get relationship values toward a target."""

def modify_relationship(accessor, actor, target_id, metric, delta) -> RelationshipResult:
    """Modify a relationship metric."""

def check_threshold(actor, target_id, metric, threshold) -> bool:
    """Check if relationship metric meets a threshold."""

def get_disposition_from_relationships(actor, target_id) -> str:
    """Determine disposition toward target based on relationships."""
```

### 7.2 Relationship Modification

```python
def modify_relationship(accessor, actor, target_id, metric, delta):
    """Modify relationship metric and check thresholds."""
    relationships = actor.properties.setdefault("relationships", {})
    target_rel = relationships.setdefault(target_id, {"trust": 0, "gratitude": 0, "fear": 0})

    old_value = target_rel.get(metric, 0)
    new_value = max(0, min(10, old_value + delta))
    target_rel[metric] = new_value

    # Check threshold crossings
    threshold_crossed = None
    if metric == "gratitude" and old_value < 3 and new_value >= 3:
        threshold_crossed = "domestication"
    elif metric == "trust" and old_value < 3 and new_value >= 3:
        threshold_crossed = "discount"
    elif metric == "trust" and old_value < 5 and new_value >= 5:
        threshold_crossed = "loyalty"
    elif metric == "fear" and old_value < 5 and new_value >= 5:
        threshold_crossed = "intimidation"

    return RelationshipResult(
        old_value=old_value,
        new_value=new_value,
        threshold_crossed=threshold_crossed
    )
```

### Phase 7 Testing Summary

| Test | Description |
|------|-------------|
| `test_get_relationship_new` | Creates relationship entry if missing |
| `test_modify_relationship_increase` | Increases metric |
| `test_modify_relationship_decrease` | Decreases metric |
| `test_modify_relationship_bounds` | Values clamped 0-10 |
| `test_threshold_domestication` | Gratitude >= 3 triggers domestication |
| `test_threshold_discount` | Trust >= 3 triggers discount |

---

## Phase 8: Morale and Fleeing

**Goal**: NPCs flee when morale drops below threshold.

**Depends on**: Phase 3 (triggered by on_damage)

### 8.1 Morale Module

**File**: `behaviors/library/actors/morale.py`

**Public API**:

```python
def get_morale(actor: Actor) -> int:
    """Get current morale (default 100)."""

def set_morale(accessor, actor, value) -> None:
    """Set morale value (clamped 0-100)."""

def reduce_morale(accessor, actor, amount) -> MoraleResult:
    """Reduce morale and check flee threshold."""

def check_morale_from_health(actor) -> int:
    """Calculate morale based on health percentage."""

def should_flee(actor) -> bool:
    """Check if actor's morale is below flee threshold."""

def execute_flee(accessor, actor) -> FleeResult:
    """Execute flee behavior."""
```

### 8.2 Integration with on_damage

```python
def on_damage_morale_check(entity, accessor, context) -> Optional[EventResult]:
    """Check morale after taking damage."""
    # Update morale based on health
    new_morale = check_morale_from_health(entity)
    current_morale = get_morale(entity)

    if new_morale != current_morale:
        set_morale(accessor, entity, new_morale)

    # Check if should flee
    if should_flee(entity):
        result = execute_flee(accessor, entity)
        return EventResult(allow=True, message=f"{entity.name} flees!")

    return None

def check_morale_from_health(actor):
    """Calculate morale based on health percentage."""
    health = actor.properties.get("health", 100)
    max_health = actor.properties.get("max_health", 100)
    health_pct = health / max_health

    if health_pct < 0.3:
        return 0
    elif health_pct < 0.5:
        return get_morale(actor) // 2

    return get_morale(actor)
```

### Phase 8 Testing Summary

| Test | Description |
|------|-------------|
| `test_morale_from_health_critical` | Health < 30% sets morale to 0 |
| `test_morale_from_health_low` | Health < 50% halves morale |
| `test_should_flee_below_threshold` | Morale below threshold triggers flee |
| `test_execute_flee_moves_actor` | Flee moves actor to flee destination |

---

## Phase 9: Pack Coordination

**Goal**: Pack followers copy alpha's disposition.

**Depends on**: Phase 4 (NPC action ordering)

### 9.1 Pack Module

**File**: `behaviors/library/actors/packs.py`

**Public API**:

```python
def get_pack_members(accessor, pack_id) -> List[Actor]:
    """Get all actors in a pack."""

def get_alpha(accessor, actor) -> Optional[Actor]:
    """Get the alpha for an actor's pack."""

def sync_pack_disposition(accessor, pack_id) -> List[Actor]:
    """Sync all followers to their alpha's disposition."""

def is_alpha(actor) -> bool:
    """Check if actor is a pack alpha."""
```

### 9.2 Pack Sync Logic

```python
def sync_pack_disposition(accessor, pack_id):
    """Sync followers to alpha disposition."""
    members = get_pack_members(accessor, pack_id)
    if not members:
        return []

    # Find alpha
    alpha = None
    for member in members:
        if is_alpha(member):
            alpha = member
            break

    if not alpha:
        return []

    alpha_disposition = alpha.properties.get("ai", {}).get("disposition", "neutral")
    changed = []

    for member in members:
        if member.id == alpha.id:
            continue

        ai = member.properties.setdefault("ai", {})
        if ai.get("disposition") != alpha_disposition:
            ai["disposition"] = alpha_disposition
            changed.append(member)

    return changed
```

### 9.3 Integration with NPC Action Phase

Pack sync happens automatically because:
1. NPC action phase sorts actors (alphas first)
2. Before processing each follower, check `follows_alpha`
3. Copy disposition from alpha

```python
# In fire_npc_actions:
for actor in all_actors:
    ai = actor.properties.get("ai", {})

    # Followers sync before acting
    if ai.get("pack_role") == "follower":
        alpha_id = ai.get("follows_alpha")
        if alpha_id:
            alpha = accessor.get_actor(alpha_id)
            if alpha:
                alpha_disposition = alpha.properties.get("ai", {}).get("disposition")
                if alpha_disposition:
                    ai["disposition"] = alpha_disposition

    # Then take action
    result = accessor.behavior_manager.invoke_behavior(actor, event_name, accessor, {})
    # ...
```

### Phase 9 Testing Summary

| Test | Description |
|------|-------------|
| `test_get_pack_members` | Returns all actors with same pack_id |
| `test_get_alpha` | Returns pack alpha |
| `test_sync_disposition` | Followers copy alpha disposition |
| `test_npc_action_alpha_first` | Alphas processed before followers |
| `test_pack_becomes_hostile` | All followers hostile when alpha hostile |

---

**Note**: Phase 10 (Integration Testing) has been moved to a separate document: [Actor Interaction Integration Testing](actor_interaction_integration_testing.md)

---

## Implementation Order Summary

| Phase | Name | Depends On | Estimated Effort |
|-------|------|------------|------------------|
| 0 | Infrastructure Prerequisites | - | 2-3 days |
| 1 | Condition System | Phase 0 | 3-4 days |
| 2 | Environmental Effects | Phase 0, 1 | 2-3 days |
| 3 | Combat Foundation | Phase 1 | 3-4 days |
| 4 | NPC Actions | Phase 3 | 2 days |
| 5 | Cure/Treatment | Phase 1 | 1-2 days |
| 6 | Services Framework | Phase 5, 7 | 2-3 days |
| 7 | Relationship Tracking | - | 1-2 days |
| 8 | Morale and Fleeing | Phase 3 | 1-2 days |
| 9 | Pack Coordination | Phase 4 | 1-2 days |

**Note**: Phase 10 (Integration Testing) is documented separately in [actor_interaction_integration_testing.md](actor_interaction_integration_testing.md)

**Total Estimated Effort for Phases 0-9**: 3-4 weeks

---

## Risk Mitigation

### Risk: Turn phase system impacts performance

**Mitigation**:
- Process only actors with relevant properties (early-out pattern)
- Profile after implementation, optimize if needed
- Consider location-scoped processing for very large games

### Risk: Condition stacking creates balance issues

**Mitigation**:
- Severity capped at 100
- Authors control condition parameters
- Test with extreme cases (multiple conditions, high severity)

### Risk: NPC action phase causes unexpected behavior

**Mitigation**:
- Clear ordering (alphas first)
- Early-out pattern for NPCs with nothing to do
- Deterministic mode for testing

### Risk: Integration complexity grows

**Mitigation**:
- Each module has clear public API
- Dependencies explicit in phase ordering
- Integration tests catch cross-module issues early
