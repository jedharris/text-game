# Actor Interaction Library Design

## Document Purpose

This document provides detailed designs for behavior library modules that implement the actor interaction system described in [Actor Interaction Conceptual Design v3](actor_interaction_conceptual_design_v3.md). These modules are designed to maximize reuse across the [Simplified Use Cases](actor_interaction_simplified_cases.md) while minimizing author effort.

**Scope**: This document covers Critical and High priority modules, plus Medium priority modules where the payoff justifies the complexity.

**Companion Documents**:
- [Actor Interaction Conceptual Design v3](actor_interaction_conceptual_design_v3.md) - Conceptual framework
- [Actor Interaction Simplified Cases](actor_interaction_simplified_cases.md) - Use case requirements
- [Event Registration](event_registration.md) - Event/hook infrastructure

---

## Module Overview

### Critical Priority (Foundation)

| Module | Use Cases | Purpose |
|--------|-----------|---------|
| **Condition System** | UC1, UC3, UC5, UC6, UC7 | Condition lifecycle: apply, progress, cure, remove |
| **Environmental Effects** | UC1, UC2, UC5, UC7 | Location properties affect actors |

### High Priority (Core Gameplay)

| Module | Use Cases | Purpose |
|--------|-----------|---------|
| **Cure/Treatment** | UC1, UC4, UC6, UC7 | Item-based condition treatment |
| **NPC Services** | UC1, UC4, UC6, UC8 | Service resolution on payment |
| **Relationship Tracking** | UC3, UC4, UC5, UC6 | Progressive bonds and thresholds |
| **Attack Selection** | UC2, UC3, UC7 | Multi-attack NPCs choose and execute attacks |

### Medium Priority (Evaluated)

| Module | Use Cases | Recommendation |
|--------|-----------|----------------|
| **Morale/Fleeing** | UC2, UC3, UC6 | **Include** - Simple, high impact |
| **Pack Coordination** | UC2, UC3, UC7 | **Include** - Modest complexity, enables rich scenarios |

---

## Architecture Overview

### Module Location

All library modules live in `behaviors/library/actors/`:

```
behaviors/
  core/           # Existing core behaviors (manipulation, perception, etc.)
  library/
    actors/
      conditions.py      # Condition System
      environment.py     # Environmental Effects
      treatment.py       # Cure/Treatment
      services.py        # NPC Services
      relationships.py   # Relationship Tracking
      combat.py          # Attack Selection
      morale.py          # Morale/Fleeing
      packs.py           # Pack Coordination
```

### Integration with Existing Infrastructure

These modules integrate with existing systems:

1. **StateAccessor**: All state mutations via `accessor.update()`
2. **Event Registry**: New events registered via vocabulary
3. **Hook System**: Engine hooks for turn phases (`turn_end`, `npc_action`)
4. **Behavior Invocation**: Entity behaviors via `on_*` methods

### New Engine Hooks Required

The turn-based system requires new hooks (from conceptual design):

```python
# src/hooks.py (additions)
TURN_END = "turn_end"              # After successful player command
NPC_ACTION = "npc_action"          # NPC action phase
ENVIRONMENTAL_EFFECT = "environmental_effect"  # Environmental effects phase
CONDITION_TICK = "condition_tick"  # Condition progression phase
DEATH_CHECK = "death_check"        # Death/incapacitation check
```

---

## Critical Priority Modules

### 1. Condition System Module

**File**: `behaviors/library/actors/conditions.py`

**Purpose**: Manage the complete lifecycle of conditions on actors: application, progression, damage-over-time, duration tracking, and removal.

#### Property Schema

**Actor conditions** (in `actor.properties`):
```json
{
  "conditions": {
    "poison": {
      "severity": 60,
      "damage_per_turn": 2,
      "duration": 10,
      "effect": "agility_reduced"
    },
    "entangled": {
      "severity": 50,
      "effect": "cannot_move"
    }
  },
  "immunities": ["poison", "disease"],
  "resistances": {
    "disease": 30,
    "cold": 50
  }
}
```

**Condition properties**:
| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `severity` | number | Yes | 0-100, condition strength |
| `damage_per_turn` | number | No | Health damage each turn |
| `duration` | number | No | Turns remaining (infinite if absent) |
| `effect` | string | No | Named effect for behavior queries |
| `progression_rate` | number | No | Severity increase per turn |
| `contagious_range` | string | No | "touch" if spreads to focused actors |

#### Public API

```python
def apply_condition(
    accessor: StateAccessor,
    actor: Actor,
    condition_name: str,
    condition_data: Dict[str, Any],
    source_id: Optional[str] = None
) -> ConditionResult:
    """
    Apply or increase a condition on an actor.

    Respects immunities (blocks entirely) and resistances (reduces severity).
    If actor already has condition, increases severity (stacking).

    Args:
        accessor: StateAccessor for state mutations
        actor: Target actor
        condition_name: Name of condition (e.g., "poison")
        condition_data: Condition properties (severity, damage_per_turn, etc.)
        source_id: Optional ID of entity causing condition

    Returns:
        ConditionResult with success status and message
    """

def remove_condition(
    accessor: StateAccessor,
    actor: Actor,
    condition_name: str,
    amount: Optional[int] = None
) -> ConditionResult:
    """
    Remove or reduce a condition's severity.

    Args:
        accessor: StateAccessor for state mutations
        actor: Target actor
        condition_name: Name of condition to remove
        amount: Severity to remove (None = remove entirely)

    Returns:
        ConditionResult with success status
    """

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

#### Event Handlers

```python
def on_condition_apply(entity, accessor, context) -> Optional[EventResult]:
    """
    Called when a condition is being applied.

    Context:
        - condition_name: str
        - condition_data: dict
        - source_id: Optional[str]

    Allows behaviors to modify or block condition application.
    """

def on_condition_remove(entity, accessor, context) -> Optional[EventResult]:
    """
    Called when a condition is being removed.

    Context:
        - condition_name: str
        - amount: Optional[int]
    """

def on_condition_tick(entity, accessor, context) -> Optional[EventResult]:
    """
    Called each turn to progress conditions.

    Hook: CONDITION_TICK

    For each condition:
    - Apply damage_per_turn to health
    - Increase severity by progression_rate (if present)
    - Decrease duration
    - Remove if duration <= 0 or severity <= 0
    """
```

#### Resistance Calculation

Following the conceptual design specification:

```python
def calculate_resisted_value(base_value: int, resistance_percent: int) -> int:
    """
    Apply resistance to reduce a value.

    Formula: actual = base * (1 - resistance/100)
    Rounding: ceiling for severity increases, standard for damage
    Minimum: 0

    Example: base=15, resistance=30 -> 15 * 0.7 = 10.5 -> 11
    """
```

#### Vocabulary Registration

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

#### Implementation Notes

1. **Stacking behavior**: When applying a condition that already exists, add the new severity to existing severity (capped at 100).

2. **Immunity check order**: Check immunities before resistances. Immunities block entirely.

3. **Material-based immunities**: Constructs (`body.material: "stone"`) are automatically immune to poison, disease, bleeding. This is checked via `body.form == "construct"` OR explicit `immunities` array.

4. **Condition type mapping**: For resistance lookup, use the condition name as the type (e.g., "poison" condition checks "poison" resistance). Authors can add custom mappings if needed.

---

### 2. Environmental Effects Module

**File**: `behaviors/library/actors/environment.py`

**Purpose**: Apply location part properties to actors each turn, handling breath, spores, temperature, and other environmental hazards.

#### Property Schema

**Location part properties** (in `part.properties`):
```json
{
  "breathable": false,
  "spore_level": "high",
  "temperature": "freezing",
  "web_density": "heavy",
  "cover_value": 80
}
```

**Actor environmental properties** (in `actor.properties`):
```json
{
  "breath": 60,
  "max_breath": 60,
  "body": {
    "form": "humanoid",
    "material": "flesh"
  }
}
```

#### Spore Level Values

| Level | Severity per turn | Description |
|-------|-------------------|-------------|
| `"none"` | 0 | No spores |
| `"low"` | 5 | Light contamination |
| `"medium"` | 10 | Moderate contamination |
| `"high"` | 15 | Heavy contamination |

#### Temperature Effects

| Temperature | Effect |
|-------------|--------|
| `"freezing"` | Apply/increase `hypothermia` condition (severity 10/turn) |
| `"cold"` | Apply/increase `hypothermia` condition (severity 5/turn) |
| `"normal"` | No effect |
| `"hot"` | Apply/increase `heat_exhaustion` condition (severity 5/turn) |
| `"burning"` | Apply/increase `heat_exhaustion` condition (severity 10/turn) |

#### Public API

```python
def apply_environmental_effects(
    accessor: StateAccessor,
    actor: Actor,
    part: Part
) -> List[EnvironmentResult]:
    """
    Apply all environmental effects from a part to an actor.

    Called during environmental effects phase for all actors.

    Checks:
    - breathable: Update breath, apply drowning if depleted
    - spore_level: Apply/increase fungal_infection
    - temperature: Apply temperature conditions
    - Other part properties as defined

    Returns:
        List of EnvironmentResult describing what happened
    """

def check_breath(accessor: StateAccessor, actor: Actor, part: Part) -> Optional[EnvironmentResult]:
    """
    Check and update breath for an actor in a part.

    - If part is breathable: restore breath to max
    - If not breathable: decrease breath by 10
    - If breath <= 0: apply 10 drowning damage

    Special items:
    - If actor has item with provides_breathing=true AND part allows it: don't decrease
    """

def get_cover_value(part: Part) -> int:
    """Get cover percentage (0-100) provided by a part."""
```

#### Event Handlers

```python
def on_environmental_effect(entity, accessor, context) -> Optional[EventResult]:
    """
    Called during environmental effects phase.

    Hook: ENVIRONMENTAL_EFFECT

    For each actor, determines their current part and applies effects.
    """

def on_enter_part(entity, accessor, context) -> Optional[EventResult]:
    """
    Called when an actor enters a new part.

    Context:
        - from_part: Optional[str] - previous part ID
        - to_part: str - new part ID

    Can trigger immediate effects or just record the transition.
    """
```

#### Breath System Details

**Breath tracking**:
- `breath` decreases by 10 per turn in non-breathable areas
- When `breath <= 0`: apply 10 damage per turn (drowning)
- Moving to breathable area: `breath` restores to `max_breath`

**Breathing items**:
- Items with `provides_breathing: true` prevent breath loss
- Part may restrict this (deep water vs shallow water) via `breathing_item_works: false`

#### Construct Handling

Constructs (`body.form: "construct"` or `body.material: "stone"`) are exempt from:
- Breath tracking (no need to breathe)
- Temperature effects (unless material-specific)
- Disease/spore effects

This is checked via:
```python
def needs_breath(actor: Actor) -> bool:
    body = actor.properties.get("body", {})
    return body.get("form") != "construct" and body.get("material") not in ["stone", "metal", "clockwork"]
```

#### Vocabulary Registration

```python
vocabulary = {
    "events": [
        {
            "event": "on_environmental_effect",
            "hook": "environmental_effect",
            "description": "Called each turn to apply environmental effects to all actors"
        },
        {
            "event": "on_enter_part",
            "description": "Called when an actor enters a location part"
        }
    ]
}
```

---

## High Priority Modules

### 3. Cure/Treatment Module

**File**: `behaviors/library/actors/treatment.py`

**Purpose**: Handle item-based condition treatment when items with `cures` or `treats` properties are used on actors.

#### Property Schema

**Item cure properties** (in `item.properties`):
```json
{
  "cures": ["poison", "fungal_infection"],
  "cure_amount": 100,
  "treats": ["bleeding"],
  "consumable": true
}
```

**Property definitions**:
| Property | Type | Description |
|----------|------|-------------|
| `cures` | string[] | Condition names this item can cure |
| `cure_amount` | number | Severity to remove (default: 100 = full cure) |
| `treats` | string[] | Alias for `cures` (author convenience) |
| `consumable` | boolean | If true, item is consumed on use |

#### Public API

```python
def can_treat(item: Item, condition_name: str) -> bool:
    """Check if item can treat a condition."""

def treat_condition(
    accessor: StateAccessor,
    item: Item,
    target_actor: Actor,
    condition_name: Optional[str] = None
) -> TreatmentResult:
    """
    Use an item to treat conditions on an actor.

    If condition_name is None, treats all conditions the item can cure.

    Args:
        accessor: StateAccessor for state mutations
        item: The treatment item
        target_actor: Actor to treat
        condition_name: Specific condition to treat (or None for all)

    Returns:
        TreatmentResult with success, conditions_treated, item_consumed
    """

def get_treatable_conditions(item: Item) -> List[str]:
    """Get list of conditions this item can treat."""
```

#### Event Handlers

```python
def on_use_treatment(entity, accessor, context) -> Optional[EventResult]:
    """
    Handler for "use X on Y" where X is a treatment item.

    Context:
        - item_id: str - the treatment item
        - target_id: str - the actor to treat

    Returns EventResult indicating success/failure with message.
    """
```

#### Integration with Give Command

When an actor receives a curative item, the `on_receive` behavior can auto-apply:

```python
def on_receive(entity, accessor, context) -> Optional[EventResult]:
    """
    When an actor receives an item, check if it treats their conditions.

    If item has cures/treats that match actor's conditions:
    - Apply treatment automatically
    - Generate appropriate message
    """
```

#### Treatment Flow

1. Player: `use bandages on merchant`
2. Handler validates item and target
3. `treat_condition()` called with item and target
4. For each condition in `item.cures`/`item.treats`:
   - If target has condition: reduce severity by `cure_amount`
   - If severity <= 0: remove condition
5. If `item.consumable`: remove item from inventory
6. Return result with narrative message

#### Vocabulary Registration

```python
vocabulary = {
    "verbs": [
        {
            "word": "treat",
            "event": "on_use_treatment",
            "synonyms": ["bandage", "heal"],
            "object_required": True,
            "indirect_object_required": True
        }
    ]
}
```

---

### 4. NPC Services Module

**File**: `behaviors/library/actors/services.py`

**Purpose**: Resolve NPC service interactions when the player gives acceptable payment.

#### Property Schema

**NPC service properties** (in `actor.properties`):
```json
{
  "services": {
    "cure_poison": {
      "accepts": ["rare_herbs", "gold"],
      "amount_required": 1,
      "cure_amount": 100
    },
    "teach_herbalism": {
      "accepts": ["gold"],
      "amount_required": 50,
      "grants": "knows_herbalism"
    },
    "trading": {
      "accepts": ["gold"],
      "sells": ["health_potion", "antidote"]
    }
  }
}
```

**Service properties**:
| Property | Type | Description |
|----------|------|-------------|
| `accepts` | string[] | Item types/names accepted as payment |
| `amount_required` | number | Quantity required (for stackable items) |
| `cure_amount` | number | For cure services: severity to remove |
| `grants` | string | For teaching: knowledge string to add to player.knows |
| `sells` | string[] | For trading: items available for purchase |
| `restore_amount` | number | For healing: health to restore |

#### Public API

```python
def get_available_services(actor: Actor) -> Dict[str, Dict]:
    """Get all services an NPC offers."""

def can_afford_service(
    accessor: StateAccessor,
    customer: Actor,
    service_name: str,
    npc: Actor
) -> Tuple[bool, Optional[str]]:
    """
    Check if customer can afford a service.

    Returns (can_afford, reason) where reason explains why not if False.
    """

def execute_service(
    accessor: StateAccessor,
    customer: Actor,
    npc: Actor,
    service_name: str,
    payment_item: Item
) -> ServiceResult:
    """
    Execute a service transaction.

    1. Verify payment matches service.accepts
    2. Verify amount meets service.amount_required
    3. Transfer payment to NPC (or consume)
    4. Apply service effect (cure, teach, sell)
    5. Update relationships

    Returns ServiceResult with success, message, and effects applied.
    """

def get_service_cost(
    npc: Actor,
    service_name: str,
    customer: Actor
) -> int:
    """
    Get effective cost for a service, accounting for trust discounts.

    Base cost from service.amount_required.
    If npc.relationships[customer].trust >= 3: 50% discount
    """
```

#### Service Resolution Flow

1. Player: `give 50 gold to healer`
2. `on_receive` behavior fires on healer
3. Check if payment matches any `service.accepts`
4. If match found:
   - Execute service (cure conditions / grant knowledge / provide item)
   - Consume payment
   - Increment relationship trust
5. Return result with narrative

#### Trust-Based Discounts

```python
def calculate_discounted_cost(base_cost: int, trust_level: int) -> int:
    """
    Apply trust discount to service cost.

    trust < 3: full price
    trust >= 3: 50% discount (floor division)
    """
    if trust_level >= 3:
        return base_cost // 2
    return base_cost
```

#### Event Handlers

```python
def on_receive_for_service(entity, accessor, context) -> Optional[EventResult]:
    """
    Check if received item is payment for a service.

    Context:
        - item_id: str
        - giver_id: str

    If item matches a service payment:
    - Execute the service
    - Return success with service description

    If not a service payment:
    - Return None to allow other behaviors
    """
```

#### Vocabulary Registration

```python
vocabulary = {
    "events": [
        {
            "event": "on_receive_for_service",
            "description": "Check if received item triggers a service"
        }
    ]
}
```

---

### 5. Relationship Tracking Module

**File**: `behaviors/library/actors/relationships.py`

**Purpose**: Manage progressive relationship values and threshold-based behavior changes.

#### Property Schema

**Actor relationship properties** (in `actor.properties`):
```json
{
  "relationships": {
    "player": {
      "trust": 2,
      "gratitude": 5,
      "fear": 0
    }
  }
}
```

**Relationship metrics**:
| Metric | Range | Description |
|--------|-------|-------------|
| `trust` | 0-10 | Built through trade, help, keeping promises |
| `gratitude` | 0-10 | Earned through gifts, rescue, healing |
| `fear` | 0-10 | Created through intimidation, violence |

#### Threshold Effects

| Metric | Threshold | Effect |
|--------|-----------|--------|
| `gratitude >= 3` | Domestication threshold | Creature becomes friendly, may follow |
| `trust >= 3` | Discount threshold | Services cost 50% less |
| `trust >= 5` | Loyalty threshold | NPC may provide special help |
| `fear >= 5` | Intimidation threshold | NPC may flee or comply |

#### Public API

```python
def get_relationship(actor: Actor, target_id: str) -> Dict[str, int]:
    """
    Get relationship values toward a target.

    Returns dict with trust, gratitude, fear (defaulting to 0).
    Creates relationship entry if doesn't exist.
    """

def modify_relationship(
    accessor: StateAccessor,
    actor: Actor,
    target_id: str,
    metric: str,
    delta: int
) -> RelationshipResult:
    """
    Modify a relationship metric.

    Args:
        accessor: StateAccessor for state mutations
        actor: Actor whose relationship to modify
        target_id: ID of target of relationship
        metric: "trust", "gratitude", or "fear"
        delta: Amount to add (can be negative)

    Returns RelationshipResult with new value and any threshold crossed.
    """

def check_threshold(actor: Actor, target_id: str, metric: str, threshold: int) -> bool:
    """Check if relationship metric meets a threshold."""

def get_disposition_from_relationships(actor: Actor, target_id: str) -> str:
    """
    Determine disposition toward target based on relationships.

    Returns: "friendly", "neutral", "hostile", "grateful", "fearful"

    Logic:
    - gratitude >= 3: "grateful" or "friendly"
    - fear >= 5: "fearful"
    - trust < 0: "hostile"
    - otherwise: "neutral"
    """
```

#### Event Handlers

```python
def on_relationship_change(entity, accessor, context) -> Optional[EventResult]:
    """
    Called when a relationship value changes.

    Context:
        - target_id: str
        - metric: str
        - old_value: int
        - new_value: int
        - threshold_crossed: Optional[str]

    Can trigger disposition changes, dialogue unlocks, etc.
    """
```

#### Integration Points

**With Services Module**: Check trust for discounts
```python
trust = get_relationship(npc, customer.id).get("trust", 0)
cost = calculate_discounted_cost(base_cost, trust)
```

**With Treatment/Give**: Increment gratitude when healed
```python
modify_relationship(accessor, npc, healer_id, "gratitude", 1)
```

**With Pack Coordination**: Domestication changes pack behavior
```python
if check_threshold(wolf, player_id, "gratitude", 3):
    # Wolf is domesticated, disposition becomes friendly
```

---

### 6. Attack Selection Module

**File**: `behaviors/library/actors/combat.py`

**Purpose**: Enable NPCs with multiple attacks to select and execute appropriate attacks.

#### Property Schema

**Actor attack properties** (in `actor.properties`):
```json
{
  "attacks": [
    {
      "name": "bite",
      "damage": 15,
      "type": "piercing",
      "range": "touch",
      "applies_condition": {
        "name": "bleeding",
        "severity": 30
      }
    },
    {
      "name": "tackle",
      "damage": 8,
      "range": "touch",
      "effect": "knockdown"
    }
  ],
  "armor": 5
}
```

**Attack properties**:
| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Attack identifier |
| `damage` | number | Base damage |
| `type` | string | Damage type (descriptive in Phase 1) |
| `range` | string | "touch", "near", "far" (for selection logic) |
| `applies_condition` | object | Condition to apply on hit |
| `effect` | string | Special effect (knockdown, etc.) |

#### Public API

```python
def select_attack(
    attacker: Actor,
    target: Actor,
    context: Dict[str, Any]
) -> Optional[Dict]:
    """
    Select an appropriate attack based on situation.

    Selection logic:
    1. Filter by range (if focus/distance info available)
    2. Prefer condition-applying attacks if target not already affected
    3. Prefer higher damage otherwise

    Returns attack dict or None if no valid attack.
    """

def execute_attack(
    accessor: StateAccessor,
    attacker: Actor,
    target: Actor,
    attack: Dict
) -> AttackResult:
    """
    Execute an attack against a target.

    1. Calculate damage (base - target.armor)
    2. Apply damage to target
    3. Apply condition if attack has applies_condition
    4. Check for special effects

    Returns AttackResult with damage dealt, conditions applied, effects.
    """

def calculate_damage(
    attack: Dict,
    attacker: Actor,
    target: Actor,
    context: Dict
) -> int:
    """
    Calculate final damage after armor and modifiers.

    Base: attack.damage
    Minus: target.armor
    Modifiers: web_bonus, cover_reduction, etc.
    Minimum: 0
    """

def get_attacks(actor: Actor) -> List[Dict]:
    """Get all attacks available to an actor."""
```

#### Attack Selection Logic

```python
def select_attack(attacker: Actor, target: Actor, context: Dict) -> Optional[Dict]:
    attacks = get_attacks(attacker)
    if not attacks:
        return None

    # Simple selection rules (behaviors can override)
    target_health_pct = target.properties.get("health", 100) / target.properties.get("max_health", 100)

    for attack in attacks:
        # Prefer knockdown/control effects when target is healthy
        if target_health_pct > 0.5 and attack.get("effect") == "knockdown":
            return attack
        # Prefer condition attacks if target doesn't have condition
        if "applies_condition" in attack:
            cond_name = attack["applies_condition"]["name"]
            if not has_condition(target, cond_name):
                return attack

    # Default: highest damage
    return max(attacks, key=lambda a: a.get("damage", 0))
```

#### Cover Mechanics

When target has cover (`posture: "cover"` and `focused_on` a cover object):

```python
def apply_cover_reduction(damage: int, target: Actor, accessor: StateAccessor) -> int:
    if target.properties.get("posture") != "cover":
        return damage

    cover_obj_id = target.properties.get("focused_on")
    if not cover_obj_id:
        return damage

    cover_obj = accessor.get_entity(cover_obj_id)
    if not cover_obj:
        return damage

    cover_value = cover_obj.properties.get("cover_value", 0)
    return int(damage * (1 - cover_value / 100))
```

#### Event Handlers

```python
def on_attack(entity, accessor, context) -> Optional[EventResult]:
    """
    Handle attack command.

    Context:
        - target_id: str
        - attack_name: Optional[str] - specific attack or auto-select
    """

def on_damage(entity, accessor, context) -> Optional[EventResult]:
    """
    Called when entity takes damage.

    Context:
        - damage: int
        - attacker_id: str
        - attack_type: Optional[str]

    Can trigger reactions: flee, retaliate, call for help.
    """

def on_death(entity, accessor, context) -> Optional[EventResult]:
    """
    Called when entity's health reaches 0.

    Hook: DEATH_CHECK

    Author implements: drop inventory, create corpse, etc.
    Engine does NOT automatically handle death.
    """
```

---

## Medium Priority Modules

### 7. Morale and Fleeing Module

**File**: `behaviors/library/actors/morale.py`

**Recommendation**: Include - Simple implementation, significant gameplay impact.

**Purpose**: Track morale and trigger fleeing when thresholds are crossed.

#### Property Schema

**Actor morale properties** (in `actor.properties`):
```json
{
  "ai": {
    "morale": 60,
    "flee_threshold": 20,
    "flee_destination": "loc_wolf_den"
  }
}
```

#### Public API

```python
def get_morale(actor: Actor) -> int:
    """Get current morale (default 100)."""

def set_morale(accessor: StateAccessor, actor: Actor, value: int) -> None:
    """Set morale value (clamped 0-100)."""

def reduce_morale(accessor: StateAccessor, actor: Actor, amount: int) -> MoraleResult:
    """
    Reduce morale and check flee threshold.

    Returns MoraleResult with new_morale and should_flee.
    """

def check_morale_from_health(actor: Actor) -> int:
    """
    Calculate morale based on health percentage.

    If health < 30% of max: morale drops to 0
    If health < 50% of max: morale reduced by 50%
    """

def should_flee(actor: Actor) -> bool:
    """Check if actor's morale is below flee threshold."""

def execute_flee(accessor: StateAccessor, actor: Actor) -> FleeResult:
    """
    Execute flee behavior.

    Moves actor toward flee_destination or off-map.
    """
```

#### Integration with on_damage

```python
def on_damage(entity, accessor, context) -> Optional[EventResult]:
    # ... apply damage ...

    # Check morale
    new_morale = check_morale_from_health(entity)
    if new_morale != get_morale(entity):
        set_morale(accessor, entity, new_morale)

    if should_flee(entity):
        flee_result = execute_flee(accessor, entity)
        return EventResult(allow=True, message=f"{entity.name} flees!")
```

---

### 8. Pack Coordination Module

**File**: `behaviors/library/actors/packs.py`

**Recommendation**: Include - Modest complexity, enables rich multi-actor scenarios.

**Purpose**: Coordinate pack member behavior based on alpha state.

#### Property Schema

**Actor pack properties** (in `actor.properties`):
```json
{
  "ai": {
    "pack_id": "winter_wolves",
    "pack_role": "follower",
    "follows_alpha": "npc_wolf_alpha"
  }
}
```

**Pack roles**:
| Role | Description |
|------|-------------|
| `"alpha"` | Pack leader, others follow their state |
| `"follower"` | Copies disposition from alpha |

#### Public API

```python
def get_pack_members(accessor: StateAccessor, pack_id: str) -> List[Actor]:
    """Get all actors in a pack."""

def get_alpha(accessor: StateAccessor, actor: Actor) -> Optional[Actor]:
    """Get the alpha for an actor's pack."""

def sync_pack_disposition(accessor: StateAccessor, pack_id: str) -> List[Actor]:
    """
    Sync all followers to their alpha's disposition.

    Called during NPC action phase, after sorting by role.
    Returns list of actors whose disposition changed.
    """

def is_alpha(actor: Actor) -> bool:
    """Check if actor is a pack alpha."""

def get_pack_id(actor: Actor) -> Optional[str]:
    """Get actor's pack ID."""
```

#### NPC Action Phase Integration

The NPC action phase must process actors in order:

```python
def npc_action_phase(accessor: StateAccessor, location_id: str):
    actors = accessor.get_actors_in_location(location_id)

    # Sort: alphas first, then followers
    def pack_sort_key(actor):
        role = actor.properties.get("ai", {}).get("pack_role", "")
        return 0 if role == "alpha" else 1

    actors.sort(key=pack_sort_key)

    for actor in actors:
        # Followers sync before acting
        if actor.properties.get("ai", {}).get("pack_role") == "follower":
            alpha = get_alpha(accessor, actor)
            if alpha:
                actor.properties["ai"]["disposition"] = alpha.properties["ai"]["disposition"]

        # Then take action
        invoke_npc_action(accessor, actor)
```

#### Alert Propagation

When alpha is alerted, pack follows:

```python
def alert_pack(accessor: StateAccessor, alpha: Actor):
    """
    Alert entire pack when alpha becomes hostile.

    Sets disposition="hostile" on alpha.
    Followers will sync during NPC action phase.
    """
    pack_id = get_pack_id(alpha)
    if not pack_id:
        return

    alpha.properties["ai"]["disposition"] = "hostile"
    # Followers sync automatically in npc_action_phase
```

---

## Design Clarifications

During library design, several ambiguities were identified and resolved. These resolutions have been incorporated into the [Conceptual Design v3](actor_interaction_conceptual_design_v3.md) document.

### Resolved in Conceptual Design v3

The following items are now documented as **Implementation Requirements** in the conceptual design:

1. **Property Location for Vitals** (Requirement 1): Vitals stored directly in `actor.properties`, not nested in stats dict.

2. **Turn Phase Hook System** (Requirement 2): Engine must implement hooks for NPC_ACTION, ENVIRONMENTAL_EFFECT, CONDITION_TICK, DEATH_CHECK.

3. **Part Access API** (Requirement 3): StateAccessor must provide `get_actor_part(actor)` for environmental effects.

4. **Effect String Registry** (Requirement 4): Effects registered via vocabulary, validated at load time, extensible by authors.

### Resolved via Design Updates

The following clarifications have been added to the conceptual design:

5. **Item Consumption**: Items with `consumable: true` are automatically consumed by treatment behaviors.

6. **Service Payment Matching**: Exact match required, overpayment accepted (no change), underpayment rejected.

7. **Condition Stacking**: Severities add when same condition applied multiple times (capped at 100).

8. **NPC Action Scope**: All NPCs everywhere processed, with documented early-out pattern for performance.

9. **Construct Health**: Use `health` uniformly for all actor types (interpret as "integrity" narratively for constructs).

### Unchanged (Current Design Adequate)

10. **Knowledge Grants**: Simple string array in `player.knows`. No registry needed—check membership directly.

---

## Implementation Dependencies

### Prerequisites (Must Exist First)

1. **Turn phase hook system**: Engine must fire hooks after each successful command (see Requirement 2 in conceptual design)
2. **Part access API**: `accessor.get_actor_part(actor)` or equivalent (see Requirement 3 in conceptual design)
3. **Effect registry**: Register effects via vocabulary (see Requirement 4 in conceptual design)
4. **Event registry updates**: Register new events/hooks per event_registration.md

### Implementation Order

1. **Condition System** - Foundation, no dependencies on other new modules
2. **Environmental Effects** - Depends on Condition System
3. **Cure/Treatment** - Depends on Condition System
4. **Relationship Tracking** - Independent
5. **NPC Services** - Depends on Relationship Tracking (for discounts)
6. **Attack Selection** - Depends on Condition System (for applies_condition)
7. **Morale/Fleeing** - Depends on Attack Selection (triggered by on_damage)
8. **Pack Coordination** - Depends on turn phase system (NPC ordering)

---

## Testing Strategy

Each module should have:

1. **Unit tests**: Pure functions with mock data
2. **Integration tests**: StateAccessor with test fixtures
3. **Scenario tests**: Multi-turn sequences matching simplified use cases

### Test Fixtures Needed

```json
{
  "actors": {
    "npc_poisoned_scholar": {
      "conditions": {"fungal_infection": {"severity": 80}}
    },
    "npc_wolf_alpha": {
      "ai": {"pack_role": "alpha", "morale": 60}
    },
    "npc_wolf_follower": {
      "ai": {"pack_role": "follower", "follows_alpha": "npc_wolf_alpha"}
    }
  },
  "items": {
    "item_antidote": {
      "cures": ["fungal_infection", "poison"],
      "cure_amount": 100
    }
  },
  "parts": {
    "part_spore_basement": {
      "spore_level": "high",
      "breathable": true
    }
  }
}
```

---

## Summary

This design provides eight behavior library modules that together implement the actor interaction system:

**Critical** (must have):
- Condition System: Foundation for all ailments and status effects
- Environmental Effects: Location hazards and breath tracking

**High Priority** (needed for rich gameplay):
- Cure/Treatment: Item-based healing
- NPC Services: Trade, teaching, healing services
- Relationship Tracking: Progressive bonds
- Attack Selection: Multi-attack combat

**Medium Priority** (included for value):
- Morale/Fleeing: Dynamic combat endings
- Pack Coordination: Group behavior

**Key Design Principles**:
- Property-driven: Behaviors read entity properties, don't require code
- Deterministic: No hidden dice rolls, predictable outcomes
- Modular: Each module independent, uses public APIs
- Author-friendly: Sensible defaults, minimal configuration

**Open Issues**:
- Turn phase system needs engine support
- Part access API may need addition
- Some property locations need standardization (stats vs properties)

All modules follow existing behavior patterns and integrate through the event/hook system.
