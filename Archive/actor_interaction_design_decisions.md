# Actor Interaction System - Design Decisions

This document records design decisions for the actor interaction system. Each decision includes rationale and implications for implementation.

---

## 1. Architecture: Actor Interaction Framework in Core

**Decision:** The actor interaction framework lives in `behaviors/core/actors.py` (or `interactions.py`), not in game-specific behaviors.

**Rationale:**
- Actor interactions (not just combat) are broadly useful across many game types
- Similar to how `manipulation.py` and `light_sources.py` provide universal mechanics
- The framework is general-purpose; specific interactions are customized via properties and behaviors
- Includes: condition management, health tracking, attack resolution, NPC action timing, environmental effects, morale, pack coordination, and services framework

**What's in Core:**
- Mechanisms and infrastructure (turn progression, condition lifecycle, damage application)
- Generic calculation frameworks (base damage formulas, environmental checks)
- Behavior orchestration (when to invoke behaviors, in what order)

**What's in Game Behaviors:**
- Strategy and policy (which attack to use, when to flee)
- Semantic meaning (what "entangled" does, what "agility_reduced" means)
- Specific implementations (boss phase transitions, unique enemy abilities)
- Service implementations (teaching, healing, trading)

**Implications:**
- Core behaviors provide universal actor interaction capabilities
- Authors customize via properties (attacks array, immunities, body characteristics)
- Authors extend via custom behaviors (on_damage, on_attack, custom AI)
- Maintains consistency with existing behavior architecture

---

## 2. Behavior Integration: First-Class Event System

**Decision:** Actor interaction events (`on_attack`, `on_damage`, `on_heal`, `on_condition_change`) are first-class events in the behavior system, not special-cased.

**Rationale:**
- Maintains architectural consistency with existing behavior patterns
- `accessor.update(entity, changes, verb="damage")` already supports arbitrary verbs
- Entity behaviors already fire on events (on_take, on_examine, on_open)
- Adding new event types doesn't require changing the behavior manager architecture
- Allows same behavior composition patterns (stacking, chaining, override)

**How It Works:**
```python
# In combat handler
result = accessor.update(
    target_actor,
    {"properties.health": new_health},
    verb="damage",
    actor_id=attacker_id,
    damage_amount=damage  # Additional context
)
# This automatically invokes target's on_damage behavior if present
```

**Implications:**
- Combat behaviors use same patterns as existing behaviors
- No parallel "combat behavior system" - everything unified
- Authors can stack behaviors (e.g., base on_damage + game-specific on_damage)
- Consistent behavior discovery and loading

---

## 3. NPC Action Timing: After Player Commands

**Decision:** NPCs act after successful player commands. All NPCs everywhere are given opportunity to act. Processing order is random by default, with deterministic mode available via config switch. NPCs should cheaply check if they need to act and return early if nothing to do.

**Rationale:**
- Maintains request-driven architecture (no background processing)
- All NPCs everywhere need to act (healing, recovery from conditions, alchemical work, etc.) - not just hostile combat NPCs
- "All NPCs everywhere" scope is necessary, but performance optimized via cheap early-return pattern
- Random order by default provides varied gameplay experience
- Deterministic mode available for debugging and testing
- Deterministic/random mode is part of saved game state
- "After successful commands" means failed actions don't trigger NPC responses

**Specific Rules:**
1. Player command executes completely
2. If command succeeds: trigger NPC action phase
3. Get all actors everywhere (not just in player's location)
4. Process NPCs in random order (or deterministic order if config switch enabled)
5. For each NPC:
   - Invoke `npc_take_action(npc, accessor)` behavior
   - **Best Practice:** Behavior should cheaply check conditions (e.g., "is player in same room?") and return early if nothing to do
   - Example: Hostile NPC checks if player in same room, returns immediately if not
   - Example: Healing NPC checks if anyone nearby needs healing, returns if not
6. After all NPCs act: apply environmental effects → progress conditions → check for death/incapacitation
7. Narrator combines all actions into smooth narration
8. Return combined result to player

**Best Practice Pattern:**
```python
def npc_take_action(entity, accessor, context):
    """Example NPC behavior with cheap early return."""
    # Cheap check: is player in same room?
    player_location = accessor.get_entity_location(accessor.get_player())
    npc_location = accessor.get_entity_location(entity)

    if player_location.id != npc_location.id:
        return  # Nothing to do - player not here

    # Only proceed with expensive logic if check passes
    # ... actual combat/interaction logic here
```

**Turn Progression Sequence:**
```
1. Player command executes
2. If successful:
   a. For each NPC (in random or deterministic order based on config):
      - Invoke NPC behaviors
      - Behaviors check conditions and return early if nothing to do
   b. For each actor everywhere:
      - Apply environmental effects
      - Progress conditions
   c. Check for death/incapacitation everywhere
3. Narrator combines all actions into smooth narration
4. Return combined result to player
```

**Save/Load Implications:**
- Save only happens between turns, never during turn processing
- Save captures current state only, not history or execution path
- Random/deterministic mode switch IS saved as part of game state
- Different execution orders can lead to different states, but save/load doesn't care about the path taken

**Implications:**
- Clear turn structure: player acts → NPCs act → environmental effects → conditions tick
- No async or background NPC activity
- All NPC behaviors can execute (hostile, healing, vendors, crafting, etc.)
- "Cheap test followed by quick return" pattern keeps performance good despite checking all NPCs
- Narrator has all actions available to create cohesive narration
- Predictable and testable turn sequence (especially in deterministic mode)

---

## 4. Turn Definition: Every Successful Player Command

**Decision:** Every successful player command constitutes a turn. Failed commands do not advance time. Conditions progress after each successful command.

**Rationale:**
- Simplest to implement - no command classification needed
- Consistent with Decision 3 - same rule for NPC actions and condition progression
- Command handler already knows if it succeeded - clear success/fail boundary
- Failed attempts don't waste time (merciful to player)
- Even "free" commands like `examine` can have side effects in game-specific handlers (guard notices you looking at them)
- Attempting to classify "free actions" vs "significant actions" creates murky edge cases and implementation complexity

**Turn Sequence:**
```
1. Player issues command
2. Handler executes command
3. If command succeeds:
   a. For each NPC (random or deterministic order):
      - Invoke NPC behaviors
   b. For each actor everywhere:
      - Apply environmental effects
      - Progress conditions (damage_per_turn, duration--)
   c. Check for death/incapacitation
   d. Narrator combines actions
4. Return result to player
```

**Why Not Classify Commands:**
- `look` might seem "free", but can trigger events (guard notices observation)
- `examine` might reveal secrets, alert NPCs, or trigger behaviors
- `inventory` is usually safe, but game-specific handlers could make it meaningful
- Classification adds complexity for unclear benefit
- Edge cases multiply (is examining during combat free? What about searching?)

**Implications:**
- Poison ticks while player examines things (creates time pressure)
- Drowning timer advances even during "look" commands (encourages urgency)
- Failed attempts (try to take nailed item) don't waste precious breath/poison duration
- Simple to implement - no special cases or command categorization
- Encourages focused gameplay (don't dawdle while poisoned)
- All commands can have meaningful side effects via game-specific behaviors

**Why This Works:**
- Command handlers decide what counts as "success"
- Failed command = error message, no state change, no time passage
- Successful command = state changed (even if just "you looked"), time advances
- Clear, deterministic, easy to reason about

---

## 5. Save/Load: Full Serialization of Temporal State

**Decision:** Serialize all time-dependent state (conditions, durations, morale, pack relationships, event ordering mode) in game_state.json. Save only happens between turns.

**Rationale:**
- Most faithful to game state - resume exactly where you left off
- Conditions mid-duration are preserved
- Combat in progress resumes correctly
- Simpler than trying to recalculate derived state on load
- Between-turn constraint ensures no partial/inconsistent states
- Event ordering mode must be preserved to maintain consistent behavior

**What Gets Serialized:**

*Actor State:*
- Actor health and max_health
- All active conditions with severity and duration
- Actor morale values (ai.morale)
- Hostility state (ai.hostile)
- Pack relationships (pack_id, follows_alpha) - static but included
- Any temporary effects (repellent duration, focused_on, posture, etc.)
- Vital stats (breath, power, etc.)

*Game Settings:*
- `deterministic_event_order` - boolean flag controlling event processing order
  - Named generically since events can be fired by any entity (NPCs, plants, fires, pendulums, etc.)
  - `true` = process events in deterministic order (ID sort)
  - `false` = process events in random order (default)
  - Must be saved because it affects gameplay outcomes

**What Doesn't Get Serialized:**
- Calculated values (can be recomputed from properties)
- Behavior code (loaded from modules)
- Turn history (only current state matters)
- Partial turn progress (save only between turns)

**Save Constraints (from Decision 3):**
- Save only happens between turns, never during turn processing
- No capturing partial turns or mid-execution state
- Game must be in "waiting for player command" state to save
- Ensures clean, consistent state snapshots

**Example Save State:**
```json
{
  "settings": {
    "deterministic_event_order": false
  },
  "entities": {
    "npc_wolf": {
      "properties": {
        "health": 35,
        "max_health": 60,
        "ai": {
          "hostile": true,
          "morale": 45
        },
        "conditions": {}
      }
    },
    "player": {
      "properties": {
        "health": 70,
        "max_health": 100,
        "breath": 45,
        "posture": "cover",
        "focused_on": "item_pillar_1",
        "conditions": {
          "bleeding": {
            "severity": 20,
            "duration": 3,
            "damage_per_turn": 2
          }
        }
      }
    }
  }
}
```

**Implications:**
- Game state JSON contains full snapshot of all temporal state
- Save/load is straightforward - no state reconstruction
- Combat in progress resumes exactly (hostile NPCs still hostile, wounds still bleeding)
- Event ordering mode preserved across save/load
- Schema changes may require migration (but we already handle this)
- Save files are self-contained and complete

**Backward Compatibility:**
- Actors without combat properties (old save files) treated as non-combatant
- Missing properties get sensible defaults (empty attacks array, no conditions)
- Missing `deterministic_event_order` defaults to false (random order)
- Graceful degradation rather than forced migration

---

## 6. Core/Game Boundary: Infrastructure vs Strategy

**Decision:** Core provides infrastructure and mechanisms. Game authors provide strategy, meaning, and policy.

**Core Provides (Infrastructure):**
1. **Condition Management**
   - Storage: `add_condition()`, `remove_condition()`, `get_conditions()`
   - Progression: `progress_conditions()` - auto-tick duration, apply damage_per_turn
   - Stacking: rules for when same condition applied multiple times
   - Treatment: framework for items/NPCs removing conditions

2. **Health and Damage**
   - `apply_damage(target, amount, source, damage_type)` - reduces health, invokes on_damage
   - `apply_healing(target, amount)` - restores health up to max
   - `check_incapacitation(actor)` - if health ≤ 0, invoke on_death/on_incapacitate

3. **Turn Progression**
   - `end_player_turn(state)` - orchestrates NPC actions, condition progression, environmental effects
   - `process_npc_actions(state, location)` - each hostile NPC acts in order
   - `apply_environmental_effects(actor, state)` - check current part for hazards

4. **Pack Coordination Helpers**
   - `get_pack_members(pack_id)` - find actors with same pack_id
   - `alert_pack(pack_id, property, value)` - broadcast state change (hostility, target)
   - `is_pack_alpha(actor)` - check pack_role

5. **Environmental Effect Checking**
   - `get_actor_location_part(actor, state)` - where is actor positioned?
   - `get_environmental_modifiers(part)` - parse part properties for bonuses/hazards
   - Standard application of breathable, hazard_condition, etc.

**Authors Provide (Strategy & Meaning):**
1. **Attack Selection** - custom behaviors choose which attack from attacks array
2. **Condition Effects** - behaviors interpret "entangled" → cannot move, "agility_reduced" → movement penalty
3. **AI Complexity** - simple range-based attack choice vs sophisticated tactics
4. **Service Implementations** - teaching, healing, trading all custom behaviors
5. **Damage Type Interactions** - what fire/ice/piercing mean is game-defined
6. **Death Consequences** - what happens to inventory, can corpse be examined/looted?
7. **Fleeing Destinations** - where NPCs go when morale drops
8. **Special Mechanics** - boss phases, unique abilities, activation triggers

**Hybrid (Core Hooks, Author Implements):**
1. **NPC Action Execution** - core calls behavior, author implements `npc_take_action()`
2. **Damage Calculation** - core provides `base_damage - armor`, behaviors can override
3. **Immunities** - core provides `check_immunity(actor, condition_type)` utility, behaviors use it
4. **Cover** - core provides `apply_cover_reduction(damage, cover_value)`, behaviors decide when

**Rationale for This Boundary:**
- Follows existing pattern: core handles "when/how", behaviors handle "what"
- Maximizes author flexibility (can customize everything)
- Minimizes core complexity (no hardcoded game rules)
- Enables diverse game types (puzzle games, combat games, social games all use same core)

**Evolution Strategy:**
- Start with minimal core infrastructure
- As common patterns emerge, migrate them to core (with author override option)
- Don't prematurely optimize - let usage inform what should be core vs custom
- Example: if all games use range-based attack selection, consider adding `select_attack_by_range()` utility to core

---

## 7. Default Behaviors: Start Minimal, Evolve Toward Convenience

**Decision:** Core provides **no automatic behavior**, only infrastructure and utilities. Authors implement all behavior. As common patterns emerge, consider adding **optional default behaviors** to core.

**Why Start Minimal:**
- We don't yet know what patterns authors will actually want
- Different games may have radically different needs
- Premature defaults could be wrong/limiting
- Easy to add defaults later, hard to remove bad defaults

**Current Approach:**
```python
# Core provides utilities
from behaviors.core.actors import apply_damage, check_immunity

def on_damage(entity, accessor, context):
    """Custom behavior - author implements"""
    damage = context['damage_amount']
    damage_type = context.get('damage_type', 'physical')

    # Author decides what to do
    if damage_type == 'fire' and entity.properties.get('body', {}).get('material') == 'ice':
        # Ice creatures take double fire damage
        damage *= 2

    # Use core utility to apply
    apply_damage(entity, damage, accessor)

    return EventResult(allow=True)
```

**Future Evolution (after seeing usage patterns):**
If most games use similar damage application:
```python
# Could add optional default behavior to core
from behaviors.core.actors import default_on_damage

# Game can use default
def on_damage(entity, accessor, context):
    return default_on_damage(entity, accessor, context)

# Or customize
def on_damage(entity, accessor, context):
    # Custom pre-processing
    context = apply_ice_fire_interaction(entity, context)
    # Use default for rest
    return default_on_damage(entity, accessor, context)
```

**Examples of Potential Future Defaults:**
- `default_attack_selection()` - simple range-based attack choice
- `default_on_damage()` - standard damage application with armor
- `default_condition_treatment()` - check item cures property
- `default_pack_coordination()` - followers copy alpha hostility

**NOT Providing Defaults For:**
- Boss mechanics (too game-specific)
- Unique enemy abilities
- Service implementations (teaching, trading, etc.)
- Complex AI strategies

**Implications:**
- Phase 1 implementation: all infrastructure, zero defaults
- Authors write more code initially, but have full control
- After 2-3 games built, review common patterns
- Add **optional** defaults that authors can use or override
- Defaults never required - always just convenience

---

## 8. Property Schemas: Conventions, Not Requirements

**Decision:** Actor property schemas (health, attacks, body, ai, conditions) are **documented conventions**, not enforced schemas. Core utilities check for properties, handle missing gracefully.

**Rationale:**
- Maintains flexibility - authors can add custom properties
- Different game types need different properties (constructs need power, living need breath)
- Gradual adoption - authors add properties as needed
- Graceful degradation - actors without combat properties just can't fight

**Documented Conventions:**
```python
# Recommended actor property structure (from use cases)
actor.properties = {
    # Core vitals
    "health": 100,
    "max_health": 100,

    # Optional vitals (add as needed)
    "breath": 60,  # For drowning mechanics
    "power": 50,   # For constructs

    # Body characteristics
    "body": {
        "form": "humanoid|quadruped|arachnid|construct|elemental",
        "material": "flesh|stone|metal|living_flame",
        "features": ["teeth", "claws"],  # List of features
        "size": "small|medium|large|huge"
    },

    # Combat capabilities
    "attacks": [
        {
            "name": "sword_slash",
            "damage": 15,
            "range": "melee",  # Optional
            "applies_condition": {...}  # Optional
        }
    ],
    "armor": 5,  # Flat damage reduction
    "immunities": ["poison", "disease"],  # Condition types

    # Active conditions
    "conditions": {
        "poison": {
            "severity": 40,
            "damage_per_turn": 2,
            "duration": 10,
            "effect": "weakened"  # Semantic, interpreted by behaviors
        }
    },

    # AI and behavior
    "ai": {
        "hostile": false,
        "morale": 70,
        "flee_threshold": 20,
        "pack_id": "wolf_pack",  # Optional
        "pack_role": "alpha|follower",  # Optional
        "follows_alpha": "npc_alpha_wolf"  # Optional
    },

    # Services (optional)
    "services": {
        "cure_poison": {
            "accepts": ["rare_herbs"],
            "amount_required": 1
        }
    },

    # Relationships (optional)
    "relationships": {
        "player": {
            "trust": 50,
            "gratitude": 0
        }
    }
}
```

**Core Utilities Handle Missing Properties:**
```python
def apply_damage(actor, amount, accessor):
    """Apply damage to actor. Handles missing health property gracefully."""
    health = actor.properties.get('health')
    if health is None:
        # Actor doesn't have health - can't be damaged
        return UpdateResult(success=False, message=f"{actor.name} cannot be damaged")

    max_health = actor.properties.get('max_health', 100)
    new_health = max(0, health - amount)

    accessor.update(actor, {'properties.health': new_health})

    if new_health <= 0:
        check_incapacitation(actor, accessor)

    return UpdateResult(success=True, message=f"{actor.name} takes {amount} damage")
```

**Implications:**
- Authors only add properties they need
- Puzzle game actors might just have "health" and nothing else
- Combat game actors have full suite of properties
- Core code defensively checks for properties before using
- Documentation clearly shows recommended structure

---

## 9. Randomness: Deterministic by Default

**Decision:** All outcomes are deterministic by default. No randomness in core mechanics. Authors can add randomness in custom behaviors if desired.

**Rationale:**
- Evaluation document recommends deterministic outcomes
- Simpler to implement (no RNG state to serialize)
- Easier to test (reproducible outcomes)
- Save/load works without RNG seed management
- Authors who want randomness can add it via behaviors

**What This Means:**
- Damage calculation: `damage = attack_damage - armor` (no variance)
- Attack success: attacks always hit (unless behavior prevents)
- Condition application: if attack has `applies_condition`, condition is applied (no resistance roll)
- Treatment: if item `cures` condition, condition is removed (no failure chance)
- Environmental hazards: damage applies every turn (no chance to avoid)

**How Authors Can Add Randomness:**
```python
import random

def on_damage(entity, accessor, context):
    """Custom behavior with randomness."""
    base_damage = context['damage_amount']

    # Add ±20% variance
    variance = random.uniform(0.8, 1.2)
    actual_damage = int(base_damage * variance)

    apply_damage(entity, actual_damage, accessor)
    return EventResult(allow=True)
```

**Future Consideration:**
- If multiple games want randomness, could add optional RNG utilities to core
- Would need to provide seeded RNG for save/load consistency
- For now: deterministic is simpler and sufficient

**Implications:**
- Predictable outcomes - player knows exactly what will happen
- Easier debugging and testing
- No "unfair" random deaths
- Strategy over luck

---

## 10. Condition Storage and Management

**Decision:** Conditions stored in `actor.properties.conditions` as a dict keyed by condition name. Engine provides infrastructure utilities, but does not automatically progress conditions.

**Storage Structure:**
```python
actor.properties.conditions = {
    "poison": {
        "severity": 40,           # Numeric severity level
        "damage_per_turn": 2,     # Optional: damage applied each turn
        "duration": 10,           # Turns remaining, None = permanent
        "source": "spider_bite",  # Optional: what caused it
        "effect": "weakened"      # Optional: semantic effect for behaviors
    },
    "bleeding": {
        "severity": 20,
        "damage_per_turn": 1,
        "duration": 5
    }
}
```

**Core Utilities Provided:**
```python
# Infrastructure - no automatic behavior
def add_condition(actor, condition_name, properties, accessor):
    """Add or update condition. Handles stacking per Decision 11."""

def remove_condition(actor, condition_name, accessor):
    """Remove condition entirely."""

def get_condition(actor, condition_name):
    """Retrieve condition properties if present."""

def progress_conditions(actor, accessor):
    """Reduce duration by 1, apply damage_per_turn if present.
    Called by turn progression (Decision 4), not automatic."""
```

**Rationale:**
- Simple dict structure - easy to serialize, inspect, modify
- Condition name as key enables fast lookup and uniqueness
- Properties dict allows flexible condition data
- Core provides storage/retrieval, behaviors interpret semantic meaning
- Explicit progression call maintains control

**Implications:**
- Conditions persist across save/load (Decision 5)
- Behaviors check conditions to interpret effects (e.g., "can't move while entangled")
- Authors define what conditions mean
- Turn progression explicitly calls `progress_conditions()`

---

## 11. Condition Stacking and Multiple Conditions

**Decision:** Same condition type replaces previous instance (no stacking). Different condition types coexist independently.

**Stacking Rules:**
1. **Same condition, new application**: Replace entirely with new values
2. **Different conditions**: Each condition is independent
3. **No severity accumulation**: New poison replaces old poison
4. **No instance counting**: One "poison" condition, not multiple poison instances

**Example Behavior:**
```python
# Player has poison: severity 40, duration 10
actor.properties.conditions = {"poison": {"severity": 40, "duration": 10, ...}}

# Spider bites again, applies poison: severity 30, duration 8
# Result: NEW poison replaces old
actor.properties.conditions = {"poison": {"severity": 30, "duration": 8, ...}}

# Player also gets bleeding
# Result: Both conditions coexist
actor.properties.conditions = {
    "poison": {"severity": 30, "duration": 8, ...},
    "bleeding": {"severity": 20, "duration": 5, ...}
}
```

**Rationale:**
- Simplest implementation - dict keys naturally enforce uniqueness
- Avoids complexity of tracking multiple poison instances
- Authors can implement severity increase via custom behaviors if desired
- Different conditions (poison, bleeding, burning) clearly stack - different effects
- Deterministic - no "which poison ticks first?" questions

**Alternative Pattern for Authors Who Want Accumulation:**
```python
def on_poison_applied(entity, accessor, context):
    """Custom behavior that increases severity instead of replacing."""
    existing = get_condition(entity, 'poison')
    new_severity = context['severity']

    if existing:
        # Increase severity, reset duration
        new_severity = min(100, existing['severity'] + new_severity)
        context['severity'] = new_severity

    add_condition(entity, 'poison', context, accessor)
```

**Implications:**
- Core code is simple - just dict assignment
- Getting same condition twice "refreshes" it with new values
- If authors want accumulation, they implement via behaviors
- Multiple different conditions can coexist without limit

---

## 12. Condition Treatment and Curing

**Decision:** Items/NPCs with `cures: ["condition_name"]` remove condition entirely when applied. No partial curing, no potency system.

**How It Works:**
```python
# Item definition
{
    "item_antidote": {
        "name": "antidote vial",
        "properties": {
            "cures": ["poison"]  # Removes poison completely
        }
    }
}

# In use_item behavior or NPC service
def on_use(entity, accessor, context):
    target = context['target_actor']
    cures = entity.properties.get('cures', [])

    for condition_name in cures:
        if get_condition(target, condition_name):
            remove_condition(target, condition_name, accessor)
            # Return success message
```

**Rationale:**
- Simplest model: condition present or not present
- Deterministic - using antidote always cures poison
- No partial states to track
- Authors know exactly what items do
- Follows evaluation recommendation for simplicity

**What About Partial Curing?**
If authors want partial healing of severe conditions:
```python
# Item has reduction instead of cure
{
    "item_weak_antidote": {
        "properties": {
            "reduces_conditions": {
                "poison": 30  # Reduces severity by 30
            }
        }
    }
}

# Custom behavior handles reduction
def on_use(entity, accessor, context):
    target = context['target_actor']
    reduces = entity.properties.get('reduces_conditions', {})

    for condition_name, reduction in reduces.items():
        condition = get_condition(target, condition_name)
        if condition:
            new_severity = max(0, condition['severity'] - reduction)
            if new_severity == 0:
                remove_condition(target, condition_name, accessor)
            else:
                condition['severity'] = new_severity
                add_condition(target, condition_name, condition, accessor)
```

**Multiple Treatments:**
- Using multiple antidotes on same poison: first use cures it, subsequent uses do nothing
- Using bandages on multiple wounds: each different condition can be cured
- Sequential treatment: use antidote (cures poison), then bandage (cures bleeding)

**Implications:**
- Simple items: `cures: ["poison"]` just works
- Advanced games can implement partial curing via custom properties
- Deterministic - no "50% chance to cure"
- Clear feedback - condition removed or not

---

## 13. Damage Calculation and Application

**Decision:** Damage formula is `final_damage = max(0, attack_damage - target_armor)`. Flat armor reduction, minimum damage is 0 (armor can completely block).

**Basic Formula:**
```python
def calculate_damage(attack_damage, target_armor):
    """Core damage calculation."""
    return max(0, attack_damage - target_armor)

# Example: attack 30 damage, target armor 20 = 10 damage
# Example: attack 15 damage, target armor 20 = 0 damage (blocked)
```

**Damage Types and Resistances:**
- Core does NOT interpret damage types
- Authors implement via custom behaviors
- Example pattern:
```python
def on_damage(entity, accessor, context):
    """Custom behavior handling fire damage."""
    damage = context['damage_amount']
    damage_type = context.get('damage_type', 'physical')

    # Check material weakness
    material = entity.properties.get('body', {}).get('material')
    if damage_type == 'fire' and material == 'ice':
        damage *= 2  # Ice creatures take double fire damage

    # Apply armor reduction
    armor = entity.properties.get('armor', 0)
    final_damage = max(0, damage - armor)

    # Reduce health
    apply_damage(entity, final_damage, accessor)
```

**Order of Operations:**
1. Attacker selects attack (behavior-defined)
2. Base damage from attack properties
3. Environmental bonuses applied (if any)
4. Target's on_damage behavior fires (can modify damage)
5. Armor reduction applied
6. Damage type interactions (if behavior implements)
7. Final damage applied to health
8. Check for incapacitation

**Rationale:**
- Simple, predictable formula
- Armor blocks fixed amount - easy to understand
- Armor can completely block weak attacks (realistic)
- Damage type interactions are opt-in via behaviors
- Deterministic (no random variance by default)

**Implications:**
- High armor makes character very resistant to weak attacks
- Strong attacks still get through armor
- Authors control damage type meanings
- Core just handles arithmetic

---

## 14. Armor Mechanics

**Decision:** Armor is flat damage reduction stored in `actor.properties.armor`. No armor types, no percentage reduction. All in core actor properties, not equipment system.

**Storage:**
```python
actor.properties.armor = 20  # Reduces all incoming damage by 20
```

**How It Works:**
- Single numeric value
- Reduces damage after all other modifiers
- Applied to all attacks equally (unless behavior customizes)
- Stored directly on actor (not from equipped items)

**Rationale:**
- Evaluation deferred equipment system
- Flat reduction is simplest model
- Single value easier to author and understand
- Can add armor types later if needed via behaviors

**What About Different Armor Types?**
If authors want physical vs elemental armor:
```python
actor.properties.armor = {
    "physical": 20,
    "fire": 5,
    "ice": 10
}

# Custom behavior checks type
def on_damage(entity, accessor, context):
    damage = context['damage_amount']
    damage_type = context.get('damage_type', 'physical')

    armor_values = entity.properties.get('armor', 0)
    if isinstance(armor_values, dict):
        armor = armor_values.get(damage_type, 0)
    else:
        armor = armor_values

    final_damage = max(0, damage - armor)
    apply_damage(entity, final_damage, accessor)
```

**Equipment Integration (Future):**
When equipment system exists, armor could come from:
- Base actor armor + worn armor
- Behaviors sum equipment bonuses
- Still single value (or dict) in calculations

**Implications:**
- Phase 1: simple flat armor value
- Authors can extend to armor types via behaviors
- No equipment slot management needed initially
- Clean migration path when equipment system added

---

## 15. Attack Target Selection (NPC AI)

**Decision:** Core provides infrastructure to invoke NPC behaviors. Authors implement target selection and attack choice in custom behaviors. No default AI.

**Core Infrastructure:**
```python
def process_npc_actions(state, location_id, accessor):
    """Called by turn progression. Invokes NPC behaviors."""
    # Get all actors in location with ai.hostile = true
    hostile_npcs = [
        actor for actor in get_actors_in_location(state, location_id)
        if actor.properties.get('ai', {}).get('hostile', False)
    ]

    # Process in deterministic order (ID sort)
    for npc in sorted(hostile_npcs, key=lambda a: a.id):
        # Invoke npc_take_action behavior if present
        behavior = get_behavior(npc, 'npc_take_action')
        if behavior:
            behavior(npc, accessor, {'location_id': location_id})
```

**Author Implements Strategy:**
```python
def npc_take_action(entity, accessor, context):
    """Game-specific NPC AI behavior."""
    # Find targets (e.g., player and allies)
    targets = get_potential_targets(entity, accessor)
    if not targets:
        return

    # Select target (author's strategy)
    target = select_target(entity, targets)  # Lowest health, closest, etc.

    # Select attack (author's strategy)
    attacks = entity.properties.get('attacks', [])
    if not attacks:
        return

    attack = select_attack(entity, attacks, target)  # Range-based, highest damage, etc.

    # Execute attack
    execute_attack(entity, target, attack, accessor)
```

**Example Simple AI:**
```python
def npc_take_action(entity, accessor, context):
    """Simple AI: attack player with first available attack."""
    player = accessor.get_player()
    attacks = entity.properties.get('attacks', [])

    if attacks:
        attack = attacks[0]  # Just use first attack
        execute_attack(entity, player, attack, accessor)
```

**Example Sophisticated AI:**
```python
def npc_take_action(entity, accessor, context):
    """Advanced AI: range-based attack selection, morale checks."""
    player = accessor.get_player()

    # Check morale
    ai = entity.properties.get('ai', {})
    if ai.get('morale', 100) < ai.get('flee_threshold', 20):
        attempt_flee(entity, accessor)
        return

    # Get player distance/position
    player_distance = calculate_distance(entity, player, accessor)

    # Select appropriate attack for range
    attacks = entity.properties.get('attacks', [])
    suitable_attacks = [
        atk for atk in attacks
        if is_in_range(player_distance, atk.get('range', 'melee'))
    ]

    if suitable_attacks:
        # Pick highest damage attack
        attack = max(suitable_attacks, key=lambda a: a.get('damage', 0))
        execute_attack(entity, player, attack, accessor)
```

**Rationale:**
- Maximum author flexibility
- Different games need different AI complexity
- Core just provides "when to act" infrastructure
- Authors control "what to do" completely
- Follows Decision 7: no defaults, authors implement

**Implications:**
- Phase 1: authors write all NPC AI
- Simple games: trivial AI (attack player with first attack)
- Complex games: sophisticated targeting, attack selection, tactics
- Future: common patterns might become optional utilities

---

## 16. Environmental Effects and Hazards

**Decision:** Environmental properties (breathable, hazard_condition, bonuses) are checked automatically by turn progression. Effects applied via standard condition system.

**Environmental Property Conventions:**
```python
# Part properties affecting actors
part.properties = {
    "breathable": False,           # If False, actors need breath
    "hazard_condition": {          # Automatic condition application
        "burning": {
            "severity": 30,
            "damage_per_turn": 3,
            "duration": None       # Permanent while in part
        }
    },
    "cover_value": 80,             # For cover mechanics
    "web_bonus_attacks": 20,       # Environmental bonus (game-specific)
    "sticky": True                 # Semantic flag for behaviors
}
```

**Core Infrastructure:**
```python
def apply_environmental_effects(actor, state, accessor):
    """Called by turn progression for each actor."""
    # Get actor's current part
    part = get_actor_location_part(actor, state)
    if not part:
        return

    # Check breathable
    if not part.properties.get('breathable', True):
        handle_breathable_check(actor, accessor)

    # Apply hazard conditions
    hazards = part.properties.get('hazard_condition', {})
    for condition_name, condition_props in hazards.items():
        # Check immunity
        if not check_immunity(actor, condition_name):
            add_condition(actor, condition_name, condition_props, accessor)

    # Authors can query environmental bonuses in behaviors
```

**When Effects Are Checked:**
1. Every turn (per Decision 4)
2. After NPCs act, before condition progression
3. Applied to all actors in hazardous parts
4. Deterministic and automatic

**Environmental Bonuses:**
- Core does NOT automatically apply bonuses
- Authors query in behaviors:
```python
def npc_take_action(entity, accessor, context):
    """Spider gets bonus in webbed areas."""
    part = get_actor_location_part(entity, accessor.state)
    web_bonus = part.properties.get('web_bonus_attacks', 0)

    attack = entity.properties['attacks'][0].copy()
    attack['damage'] += web_bonus  # Apply bonus

    execute_attack(entity, target, attack, accessor)
```

**Rationale:**
- Hazards are automatic - no custom behavior needed
- Bonuses require awareness - behaviors opt-in
- Uses standard condition system (no parallel mechanics)
- Semantic properties (sticky, slippery) interpreted by behaviors
- Follows core/game boundary: core applies hazards, behaviors interpret bonuses

**Implications:**
- Standing in lava automatically applies burning condition each turn
- Moving to safe area stops new condition applications
- Existing conditions persist (duration must tick down)
- Authors add environmental bonuses as needed
- Spatial system integration: parts are environmental effect carriers

---

## 17. Breath and Asphyxiation

**Decision:** Breath is optional property `actor.properties.breath`. Depletes in non-breathable areas, causes damage at 0, recovers in breathable areas.

**Storage:**
```python
actor.properties = {
    "breath": 60,      # Current breath (if actor needs air)
    "max_breath": 60,  # Full breath capacity
    # Omit both properties for actors that don't breathe
}
```

**Core Utilities:**
```python
def handle_breathable_check(actor, accessor):
    """Called by environmental effects if part is not breathable."""
    # If actor doesn't have breath property, they don't need air
    breath = actor.properties.get('breath')
    if breath is None:
        return  # Constructs, undead, etc. don't breathe

    max_breath = actor.properties.get('max_breath', 60)
    current_breath = max(0, breath - 10)  # Lose 10 per turn

    accessor.update(actor, {'properties.breath': current_breath})

    if current_breath == 0:
        # Take asphyxiation damage
        apply_damage(actor, 5, accessor)  # 5 damage per turn

def restore_breath(actor, accessor):
    """Called when actor returns to breathable area."""
    breath = actor.properties.get('breath')
    if breath is None:
        return

    max_breath = actor.properties.get('max_breath', 60)
    accessor.update(actor, {'properties.breath': max_breath})
```

**When It Happens:**
```python
def apply_environmental_effects(actor, state, accessor):
    """Integrated into turn progression."""
    part = get_actor_location_part(actor, state)

    if not part.properties.get('breathable', True):
        handle_breathable_check(actor, accessor)
    else:
        # In breathable area - restore breath
        restore_breath(actor, accessor)
```

**Rationale:**
- Simple depletion/recovery model
- Automatic - no behavior needed
- Optional - actors without breath property don't breathe
- Creates time pressure in underwater/airless areas
- Deterministic damage progression

**Implications:**
- Constructs/undead don't have breath property - immune
- Living creatures need breath property for underwater areas
- 6 turns before asphyxiation (60 breath, -10 per turn)
- Damage escalates if player stays too long
- Moving to breathable area instantly restores (simple model)

**Alternative for Authors Who Want Gradual Recovery:**
```python
def restore_breath(actor, accessor):
    """Gradual breath recovery."""
    breath = actor.properties.get('breath')
    if breath is None:
        return

    max_breath = actor.properties.get('max_breath', 60)
    new_breath = min(max_breath, breath + 20)  # Recover 20 per turn
    accessor.update(actor, {'properties.breath': new_breath})
```

---

## 18. Combat Commands and Player Actions

**Decision:** Core provides `attack <target>` command handler. Other combat-related commands (defend, flee, hide) are game-specific and author-implemented.

**Core Command Handler:**
```python
def handle_attack(command, state, accessor):
    """Core attack command handler."""
    # Parse target
    target = parse_target(command.target_description, state)
    if not target:
        return CommandResult(success=False, message="What do you want to attack?")

    # Check target is attackable
    if not target.properties.get('health'):
        return CommandResult(success=False, message=f"You cannot attack {target.name}.")

    # Get player attacks
    player = accessor.get_player()
    attacks = player.properties.get('attacks', [])
    if not attacks:
        return CommandResult(success=False, message="You have no way to attack.")

    # Use first attack (or let behavior choose)
    attack = attacks[0]

    # Execute attack
    result = execute_attack(player, target, attack, accessor)

    # Turn progression happens after successful command
    return result
```

**Attack Execution Utility:**
```python
def execute_attack(attacker, target, attack, accessor):
    """Utility for executing an attack. Used by both player and NPC."""
    damage = attack.get('damage', 0)

    # Fire target's on_damage behavior (handles armor, resistances, etc.)
    result = accessor.update(
        target,
        {},  # No direct changes - behavior handles it
        verb="damage",
        attacker_id=attacker.id,
        damage_amount=damage,
        damage_type=attack.get('damage_type', 'physical'),
        attack_name=attack.get('name', 'attack')
    )

    # Apply condition if attack specifies
    if 'applies_condition' in attack:
        condition = attack['applies_condition']
        add_condition(target, condition['name'], condition, accessor)

    return result
```

**Game-Specific Commands:**
Authors implement additional commands as needed:
```python
# In game behaviors
def handle_defend(command, state, accessor):
    """Increase armor for one turn."""
    player = accessor.get_player()
    current_armor = player.properties.get('armor', 0)
    accessor.update(player, {
        'properties.armor': current_armor + 10,
        'properties.defending': True
    })
    return CommandResult(success=True, message="You take a defensive stance.")

def handle_hide(command, state, accessor):
    """Take cover behind object."""
    # Game-specific cover mechanics
    ...
```

**Rationale:**
- Attack is universal - goes in core
- Defend, hide, flee vary by game - let authors implement
- Core provides attack execution utility for reuse
- Player attack command uses same infrastructure as NPC attacks
- Authors can customize attack selection if needed

**Implications:**
- Phase 1: just attack command in core
- Games can add defend, flee, etc. as custom commands
- All use same execute_attack utility
- Consistent damage application for player and NPCs

---

## 19. Death and Incapacitation

**Decision:** When health reaches 0, invoke `on_death` behavior if present. No automatic removal. Authors decide consequences.

**Core Infrastructure:**
```python
def check_incapacitation(actor, accessor):
    """Called after health reaches 0."""
    health = actor.properties.get('health', 0)
    if health > 0:
        return  # Still alive

    # Invoke on_death behavior if present
    behavior = get_behavior(actor, 'on_death')
    if behavior:
        behavior(actor, accessor, {})
    # If no behavior, nothing happens (actor remains at 0 health)
```

**Author Implementations:**
```python
# Example: NPC dies and drops items
def on_death(entity, accessor, context):
    """NPC death behavior."""
    # Drop inventory
    location = accessor.get_entity_location(entity)
    for item_id in entity.properties.get('inventory', []):
        accessor.move_entity(item_id, location.id)

    # Remove from world
    accessor.remove_entity(entity.id)

    return EventResult(allow=True, message=f"{entity.name} collapses and dies.")

# Example: Player death ends game
def on_death(entity, accessor, context):
    """Player death - game over."""
    accessor.set_game_over(True)
    return EventResult(allow=True, message="You have died. Game over.")

# Example: Boss phase transition at low health
def on_damage(entity, accessor, context):
    """Boss transitions to phase 2 at 50% health."""
    health = entity.properties.get('health', 0)
    max_health = entity.properties.get('max_health', 100)

    if health <= max_health * 0.5 and not entity.properties.get('enraged'):
        # Trigger phase 2
        accessor.update(entity, {'properties.enraged': True})
        # Modify attacks, add abilities, etc.
```

**Rationale:**
- Different games have different death mechanics
- Player death might be game over, or respawn, or continue as ghost
- NPC death might drop loot, leave corpse, trigger event
- Boss "death" might trigger phase transition
- Core just detects health <= 0, behaviors define meaning

**Implications:**
- Actors can reach 0 health and remain (unconscious state)
- Authors must implement on_death if they want removal
- Phase transitions handled via on_damage checks
- Clear separation: core detects, behaviors interpret

---

## 20. Immunities and Resistances

**Decision:** Immunities are binary - actor immune or not. Stored as `immunities: [condition_type]`. Core provides check utility, behaviors use it.

**Storage:**
```python
actor.properties.immunities = ["poison", "disease", "bleeding"]
```

**Core Utility:**
```python
def check_immunity(actor, condition_type):
    """Check if actor is immune to condition type."""
    immunities = actor.properties.get('immunities', [])
    return condition_type in immunities
```

**Usage in Behaviors:**
```python
def on_poison_attack(attacker, target, accessor):
    """Apply poison from venomous bite."""
    if check_immunity(target, 'poison'):
        return CommandResult(
            success=True,
            message=f"{target.name} is immune to poison!"
        )

    # Apply poison
    add_condition(target, 'poison', {
        'severity': 40,
        'damage_per_turn': 2,
        'duration': 10
    }, accessor)
```

**Resistances (Optional Author Extension):**
If authors want partial resistance:
```python
# Actor properties
actor.properties.resistances = {
    "fire": 0.5,  # Takes 50% fire damage
    "ice": 0.3    # Takes 30% ice damage
}

# In on_damage behavior
def on_damage(entity, accessor, context):
    damage = context['damage_amount']
    damage_type = context.get('damage_type', 'physical')

    # Check resistance
    resistances = entity.properties.get('resistances', {})
    resistance = resistances.get(damage_type, 1.0)

    final_damage = int(damage * resistance)
    apply_damage(entity, final_damage, accessor)
```

**Rationale:**
- Immunities are common (constructs immune to poison, etc.)
- Binary is simplest: immune or not
- Resistances add complexity - let authors opt-in
- Core provides immunity check, doesn't interpret resistances
- Clear semantic: immunity = 100% resistance

**Implications:**
- Core only handles immunity checking
- Authors implement resistance if needed
- Consistent with body characteristics (stone immune to poison)
- Deterministic - no resistance rolls

---

## 21. Damage Modification: Properties Only, Authors Control Formula

**Decision:** Core provides minimal damage application utility. Authors implement all damage modifications (types, resistances, weaknesses, environmental bonuses, cover) in behaviors.

**What Core Provides:**
- `apply_damage(actor, amount, accessor)` - reduces health, no formula beyond subtraction
- Reads `actor.properties.armor` for flat reduction
- Basic formula: `final_damage = max(0, amount - armor)`

**What Authors Implement in Behaviors:**
All damage modification happens in `on_damage` behaviors BEFORE calling core utility:
- Check `immunities` list (return EventResult(allow=False) if immune)
- Apply `weaknesses` multipliers (200 = 2.0x damage)
- Apply `resistances` reduction
- Calculate environmental bonuses
- Calculate cover reduction
- Then call `apply_damage()` with modified amount

**Example Pattern:**
```python
def on_damage(entity, accessor, context):
    """Author implements all damage logic."""
    damage = context['damage_amount']
    damage_type = context.get('damage_type', 'physical')

    # Check immunity
    if damage_type in entity.properties.get('immunities', []):
        return EventResult(allow=False, message=f"{entity.name} is immune!")

    # Apply weakness multiplier
    weaknesses = entity.properties.get('weaknesses', {})
    if damage_type in weaknesses:
        damage = int(damage * weaknesses[damage_type] / 100)

    # Apply resistance
    resistances = entity.properties.get('resistances', {})
    if damage_type in resistances:
        damage = int(damage * (1 - resistances[damage_type] / 100))

    # Core utility applies armor and reduces health
    final_damage = apply_damage(entity, damage, accessor)

    return EventResult(allow=True, message=f"Takes {final_damage} damage")
```

**Rationale:**
- Maximizes flexibility - different games have different damage models
- Core just handles universal arithmetic (damage - armor)
- No hardcoded damage type meanings
- Authors control entire damage pipeline
- Simple behaviors for simple games, complex behaviors for complex games

**Implications:**
- Authors implement immunity/resistance/weakness checks
- Damage types are purely semantic (author-defined meaning)
- Environmental bonuses applied in attacker's behavior before attack
- Cover applied in attack execution before firing damage event
- Core stays simple, behaviors have full control

---

## 22. Armor: Property Only, Author Sets Value

**Decision:** Armor is a property containing a single numeric value (or dict if author wants typed armor). Core reads it during damage application. No automatic armor from body material.

**What Core Does:**
- Reads `actor.properties.armor` (expects number or dict)
- If number: uses directly
- If dict: author's `on_damage` selects appropriate value
- Applies in `apply_damage()` formula

**Property Examples:**
```python
# Simple armor
{"armor": 20}

# Typed armor (author implements dict handling)
{"armor": {"physical": 20, "fire": 5, "ice": 10}}

# Body material is semantic only
{"body": {"material": "stone"}, "armor": 20}  # Author sets armor explicitly
```

**Body Material Does NOT Auto-Grant Armor:**
- `body.material` is purely semantic/descriptive
- Author decides what armor value makes sense
- Stone golem has `armor: 20` explicitly set by author
- No automatic derivation of armor from material

**Typed Armor Pattern (Optional):**
```python
def on_damage(entity, accessor, context):
    """Author handles typed armor."""
    damage = context['damage_amount']
    damage_type = context.get('damage_type', 'physical')

    armor_prop = entity.properties.get('armor', 0)
    if isinstance(armor_prop, dict):
        armor = armor_prop.get(damage_type, 0)
    else:
        armor = armor_prop

    final_damage = max(0, damage - armor)
    # Apply to health...
```

**Rationale:**
- Simple games: single armor number
- Complex games: dict with types, author implements selection
- Material is flavor text, not mechanical
- Author has full control over armor values
- No magic derivation - explicit is better

**Implications:**
- Phase 1: recommend single armor value
- Authors wanting typed armor can use dict pattern
- Body material doesn't affect mechanics unless author implements it
- Clear, predictable, no hidden mechanics

---

## 23. Morale: Properties Only, Authors Implement Logic

**Decision:** Morale is stored in properties only. No core utilities. Authors implement all morale logic in behaviors. Optional library helpers available for common patterns.

**What's in Properties:**
```python
"ai": {
    "morale": 70,           # Current morale value
    "flee_threshold": 30    # When morale drops below this, flee
}
```

**What's NOT in Core:**
- No morale utilities
- No automatic morale changes
- No flee behavior
- Authors implement everything in `npc_take_action`

**Author Implementation Pattern:**
```python
def npc_take_action(entity, accessor, context):
    """Author implements morale and flee logic."""
    ai = entity.properties.get('ai', {})
    morale = ai.get('morale', 100)
    flee_threshold = ai.get('flee_threshold', 20)

    # Check if should flee
    if morale < flee_threshold:
        # Author implements flee behavior
        flee_to_exit(entity, accessor)
        return

    # Normal combat behavior
    # ...

def on_damage(entity, accessor, context):
    """Author reduces morale when damaged."""
    damage = context['damage_amount']
    ai = entity.properties.get('ai', {})
    morale = ai.get('morale', 100)

    # Author's morale formula
    new_morale = max(0, morale - damage // 2)
    accessor.update(entity, {'properties.ai.morale': new_morale})

    # Apply damage normally
    # ...
```

**Optional Library Helpers:**
Authors can use optional utility library (not in core):
```python
# In behaviors/utils/morale_helpers.py
def reduce_morale(entity, amount, accessor):
    """Helper: reduce morale by amount."""
    ai = entity.properties.get('ai', {})
    morale = ai.get('morale', 100)
    new_morale = max(0, morale - amount)
    accessor.update(entity, {'properties.ai.morale': new_morale})
    return new_morale
```

**Rationale:**
- Morale is pure strategy, not infrastructure
- Different games have different morale models
- Simple to implement in behaviors
- Library can provide helpers without forcing core complexity
- Avoids core decisions that might conflict with game designs

**Implications:**
- Authors store morale in properties
- Authors implement morale changes in behaviors
- Authors implement flee logic in `npc_take_action`
- Library helpers reduce boilerplate without adding core complexity
- Each game can have custom morale mechanics

---

## 24. Pack Coordination: Properties Only, Authors Implement Logic

**Decision:** Pack coordination is stored in properties only. No core utilities. Authors implement all pack logic in behaviors. Optional library helpers available for common patterns.

**What's in Properties:**
```python
"ai": {
    "pack_id": "wolf_pack",              # Identifies the pack
    "pack_role": "alpha",                # "alpha" or "follower" (semantic)
    "follows_alpha": "npc_alpha_wolf"    # Entity ID of alpha to follow
}
```

**What's NOT in Core:**
- No `get_pack_members()` utility
- No `alert_pack()` broadcast
- No automatic coordination
- No special sequencing
- Authors implement everything

**Author Implementation Pattern:**
```python
def npc_take_action(entity, accessor, context):
    """Follower copies alpha's hostility."""
    ai = entity.properties.get('ai', {})
    follows_alpha = ai.get('follows_alpha')

    if follows_alpha:
        # Get alpha entity
        alpha = accessor.get_entity(follows_alpha)
        if alpha:
            # Copy alpha's hostile state
            alpha_hostile = alpha.properties.get('ai', {}).get('hostile', False)
            if alpha_hostile and not ai.get('hostile'):
                accessor.update(entity, {'properties.ai.hostile': True})

    # Continue with normal NPC behavior
    # ...
```

**Alpha Broadcasts to Pack (Author Pattern):**
```python
def on_detect_player(entity, accessor, context):
    """Alpha alerts pack when detecting player."""
    # Alpha becomes hostile
    accessor.update(entity, {'properties.ai.hostile': True})

    # Alert all pack members
    pack_id = entity.properties.get('ai', {}).get('pack_id')
    if pack_id:
        all_npcs = accessor.get_all_entities_by_type('actor')
        for npc in all_npcs:
            npc_pack = npc.properties.get('ai', {}).get('pack_id')
            if npc_pack == pack_id and npc.id != entity.id:
                accessor.update(npc, {'properties.ai.hostile': True})
```

**Optional Library Helpers:**
```python
# In behaviors/utils/pack_helpers.py
def get_pack_members(pack_id, accessor):
    """Helper: get all entities in pack."""
    all_npcs = accessor.get_all_entities_by_type('actor')
    return [npc for npc in all_npcs
            if npc.properties.get('ai', {}).get('pack_id') == pack_id]

def copy_alpha_property(follower, property_path, accessor):
    """Helper: copy alpha's property to follower."""
    follows = follower.properties.get('ai', {}).get('follows_alpha')
    if follows:
        alpha = accessor.get_entity(follows)
        if alpha:
            value = get_nested_property(alpha, property_path)
            accessor.update(follower, {property_path: value})
```

**Rationale:**
- Pack coordination is pure strategy
- Different packs coordinate differently (wolves vs guards vs spiders)
- Simple to implement with basic queries
- Library helpers reduce boilerplate
- Avoids premature core complexity

**Implications:**
- Pack members act in normal turn order (random/deterministic)
- No special pack sequencing
- Authors query entities by pack_id to find pack members
- Coordination happens via property copying in behaviors
- Maximum flexibility for different coordination styles

---

## 26. Environmental Effects: Configurable Constants in Metadata

**Decision:** Environmental effect constants (breath depletion rate, asphyxiation damage, etc.) are stored in game metadata, not hardcoded. Authors can tune these values based on gameplay testing.

**What's in Game Metadata:**
```python
# In game_state.json or game_config.json
"environmental_constants": {
    "breath_depletion_rate": 10,      # Breath lost per turn in non-breathable area
    "asphyxiation_damage": 5,         # Damage per turn when breath = 0
    "breath_recovery_mode": "instant" # "instant" or "gradual"
}
```

**Core Implementation:**
```python
def apply_environmental_effects(actor, state, accessor):
    """Apply environmental effects using configurable constants."""
    part = get_actor_location_part(actor, state)
    if not part:
        return

    # Get constants from game metadata
    constants = state.get('environmental_constants', {})
    breath_depletion = constants.get('breath_depletion_rate', 10)
    asphyx_damage = constants.get('asphyxiation_damage', 5)

    # Check breathable
    if not part.properties.get('breathable', True):
        handle_breath_depletion(actor, breath_depletion, asphyx_damage, accessor)
    else:
        restore_breath(actor, constants.get('breath_recovery_mode', 'instant'), accessor)

    # Apply hazard conditions
    hazard = part.properties.get('hazard_condition', {})
    for condition_name, condition_props in hazard.items():
        if not check_immunity(actor, condition_name):
            add_condition(actor, condition_name, condition_props, accessor)
```

**Rationale:**
- Constants vary by game design and need tuning
- Metadata is easier to adjust than code
- Can be saved in game state for consistency
- Authors can experiment without changing code
- Different games have different pacing needs

**Implications:**
- Phase 1 provides sensible defaults
- Authors override via metadata
- Constants saved with game state
- Easy to tune during playtesting

---

## 27. Environmental Bonuses: Documentation Conventions

**Decision:** Environmental bonuses are properties that behaviors query. Recommend flat bonuses for simplicity. Document semantic meaning, but authors control interpretation.

**Recommended Conventions:**
```python
# Flat bonus (recommended)
"web_bonus_attacks": 20  # Add 20 to attack damage

# Percentage bonus (if author prefers)
"web_bonus_attacks_percent": 20  # Add 20% to attack damage

# Multiple bonuses
"web_bonus_attacks": 20,
"web_bonus_defense": 10,
"web_movement_penalty": -5  # Negative = penalty
```

**Usage Pattern:**
```python
def npc_take_action(entity, accessor, context):
    """Query and apply environmental bonuses."""
    part = get_actor_location_part(entity, accessor.state)

    # Query bonus
    attack_bonus = part.properties.get('web_bonus_attacks', 0) if part else 0

    # Apply to damage
    base_damage = 8
    final_damage = base_damage + attack_bonus
    execute_attack(entity, target, final_damage, accessor)
```

**Documentation:**
- Recommend flat bonuses for simplicity (easier to reason about)
- Authors can use percentage if preferred (just document it)
- Multiple bonuses work fine - just different property names
- Negative values for penalties work naturally

**Rationale:**
- Flat bonuses are simpler to understand
- Authors have full control over interpretation
- No core validation - maximum flexibility
- Documentation guides without restricting

---

## 28. Cover Mechanics: Author-Implemented Conventions

**Decision:** Cover is entirely author-implemented via `posture` and `focused_on` properties. Recommend percentage-based cover_value for consistency. Pillar damage is optional pattern.

**Recommended Pattern:**
```python
# Cover value as percentage reduction
"cover_value": 80  # Reduces damage by 80%

# Pillar can optionally have health
"health": 100,
"max_health": 100
```

**Basic Cover Implementation:**
```python
def execute_attack(attacker, target, base_damage, accessor):
    """Handle cover before applying damage."""
    # Check cover
    if target.properties.get('posture') == 'cover':
        cover_id = target.properties.get('focused_on')
        if cover_id:
            cover_obj = accessor.get_entity(cover_id)
            if cover_obj:
                cover_value = cover_obj.properties.get('cover_value', 0)
                base_damage = int(base_damage * (100 - cover_value) / 100)

    # Fire damage event
    accessor.update(target, {}, verb="damage", damage_amount=base_damage, ...)
```

**Optional: Pillar Damage Pattern:**
```python
def execute_attack(attacker, target, base_damage, accessor):
    """Cover with pillar damage."""
    if target.properties.get('posture') == 'cover':
        cover_obj = accessor.get_entity(target.properties.get('focused_on'))
        if cover_obj:
            cover_value = cover_obj.properties.get('cover_value', 0)
            reduced_damage = int(base_damage * (100 - cover_value) / 100)

            # Optional: damage the pillar
            if cover_obj.properties.get('health') is not None:
                pillar_damage = base_damage - reduced_damage
                apply_damage(cover_obj, pillar_damage, accessor)

                # Check if pillar destroyed
                if cover_obj.properties.get('health', 0) <= 0:
                    # Clear cover
                    accessor.update(target, {
                        'properties.posture': None,
                        'properties.focused_on': None
                    })
                    # Optionally remove pillar from game
                    accessor.remove_entity(cover_obj.id)

            base_damage = reduced_damage

    # Apply damage to target
    accessor.update(target, {}, verb="damage", damage_amount=base_damage, ...)
```

**Cover Commands (Game-Specific):**
Authors implement via custom command handlers:
```python
# hide behind <object>
# take cover at <object>
# leave cover
```

**Rationale:**
- Cover is game-specific behavior
- Percentage reduction is intuitive (80% = blocks most damage)
- Pillar damage is optional complexity
- Commands are entirely game-defined
- Core stays simple, authors have full control

---

## 29. Core Actor Interaction Commands: Minimal Set for Author Convenience

**Decision:** Core provides minimal commands for basic actor interactions without requiring custom handlers: `attack`, `defend`, `guide`, and `activate`. Authors can create working combat and interaction scenarios by defining properties only.

**What Core Provides:**

1. **`attack <target>`** - Basic combat command
   - Uses first attack in actor's `attacks` array
   - Applies damage using core `apply_damage()` utility
   - Validates target is an actor with health
   - Fires damage events for behaviors to customize

2. **`defend`** - Basic defensive stance
   - Sets `posture: "defending"` property
   - Behaviors can query this to reduce damage
   - Simple binary state (defending or not)

3. **`guide <actor>`** - Escort/follow command
   - Enables escort missions without custom code
   - Guided actor follows player's movement
   - Uses `ai.following` property to track state

4. **`activate <object>`** - General activation command
   - Activates constructs, mechanisms, runes, etc.
   - Fires `on_activate` behavior event
   - Authors implement activation logic in behaviors

**What Authors Still Need to Implement:**

Specialized commands remain game-specific:
- `hide behind <object>` - tactical cover (game-specific)
- `intimidate <actor>` - morale manipulation (game-specific)
- `tie <rope> to <actor>`, `pull <actor>` - rescue mechanics (specialized)
- `break free` - escape mechanics (can be automatic on move attempt)
- `command <actor> to <action>` - complex AI orders (advanced)

**Attack Selection:**

When player has multiple attacks:
- **Phase 1**: Always use first attack in `attacks` array
- Simple, predictable, no parsing complexity
- Authors wanting choice add custom attack command later

**Rationale:**

- Matches existing core philosophy: provide basic commands to enable quick authoring
- Authors can create combat scenarios with just property definitions
- `examine`, `take`, `move` already in core - adding `attack`, `defend`, `guide`, `activate` completes basic gameplay loop
- Specialized commands remain game-specific, avoiding core bloat
- Authors extend when needed via custom handlers

**Quick Start Example:**

Author defines:
```json
{
  "id": "npc_goblin",
  "properties": {
    "health": 30,
    "max_health": 30,
    "armor": 5,
    "attacks": [
      {"name": "club_swing", "damage": 10}
    ]
  }
}
```

Player can immediately:
- `attack goblin` - works out of the box
- `defend` - reduces damage from goblin's counter-attack
- Combat functional without writing any code

**Implications:**

- Lower barrier to entry for authors
- Consistent with design principle: maximize author capability with minimal effort
- Core commands enable ~80% of basic interactions
- Authors customize the remaining 20% for their specific game
- Phase 1 MVP should include these four core commands

---

---

## Summary of Decisions

| # | Decision | Type |
|---|----------|------|
| 1 | Actor interaction framework in core | Architecture |
| 2 | First-class event integration | Architecture |
| 3 | NPCs act after player commands | Timing |
| 4 | Every command is a turn | Timing |
| 5 | Full serialization of temporal state | Save/Load |
| 6 | Core provides infrastructure, authors provide strategy | Boundary |
| 7 | Start with no defaults, evolve toward convenience | Scope |
| 8 | Property schemas are conventions, not requirements | Flexibility |
| 9 | Deterministic outcomes by default | Game Mechanics |
| 10 | Conditions stored as dict, explicit progression | Core Systems |
| 11 | Same condition replaces, different conditions coexist | Core Systems |
| 12 | Cures remove condition entirely | Core Systems |
| 13 | Damage = attack - armor, minimum 0 | Core Systems |
| 14 | Armor is flat damage reduction | Core Systems |
| 15 | Authors implement NPC AI via behaviors | Core Systems |
| 16 | Environmental hazards automatic, bonuses opt-in | Environment |
| 17 | Breath optional property, automatic depletion | Environment |
| 18 | Core provides attack command, authors add others | Commands |
| 19 | on_death behavior determines consequences | Game Mechanics |
| 20 | Immunities binary, resistances author-optional | Game Mechanics |
| 21 | Damage modification in behaviors, core provides utility | Core Systems |
| 22 | Armor property only, author sets value | Core Systems |
| 23 | Morale properties only, authors implement logic | AI/Strategy |
| 24 | Pack properties only, authors implement logic | AI/Strategy |
| 25 | Event types dynamically discovered via registry | Architecture |
| 26 | Environmental constants in metadata, not hardcoded | Environment |
| 27 | Environmental bonuses are conventions, not enforced | Environment |
| 28 | Cover mechanics author-implemented via properties | Environment |
| 29 | Core provides attack, defend, guide, activate commands | Commands |

---

## 25. Event Type Registry: Dynamic Discovery Like Vocabulary

**STATUS: Being implemented separately prior to actor interaction system implementation.**

**Decision:** Event types should be discovered dynamically from behavior modules via a registry, not hardcoded. Just like vocabulary is built from modules, available events should be discoverable.

**Current State:**
The behavior system already dynamically registers verb→event mappings from module vocabulary:
```python
# In module vocabulary
vocabulary = {
    "verbs": [
        {"word": "take", "event": "on_take", "synonyms": ["get", "grab"]},
        {"word": "damage", "event": "on_damage"}
    ]
}
```

This is good - no hardcoded verb→event mappings. However, there's no **event registry** showing what events exist in the system.

**Architectural Issue:**
Currently, knowledge of what events exist is **implicit**:
- Defined in vocabulary entries: `"event": "on_damage"`
- Defined as behavior functions: `def on_damage(entity, accessor, context)`
- No central registry of available events
- No way to query "what events can entities respond to?"
- No validation that behavior functions match registered events

**Improved Architecture:**
```python
class BehaviorManager:
    def __init__(self):
        self._event_registry: Dict[str, EventInfo] = {}  # event_name -> metadata
        self._verb_event_map: Dict[str, List[tuple]] = {}  # verb -> [(tier, event)]
        # ... existing fields

@dataclass
class EventInfo:
    """Metadata about a registered event type."""
    event_name: str  # e.g., "on_damage"
    registered_by: List[str]  # Module names that register this event
    description: Optional[str] = None  # Optional documentation
```

**Dynamic Event Registration:**
```python
def _register_vocabulary(self, vocabulary: dict, module_name: str, tier: int):
    """Register vocabulary and discover event types."""
    if "verbs" not in vocabulary:
        return

    for verb_spec in vocabulary["verbs"]:
        event = verb_spec.get("event")
        if event:
            # Register verb→event mapping (already done)
            self._register_verb_mapping(verb_spec["word"], event, module_name, tier)

            # NEW: Register event type in registry
            if event not in self._event_registry:
                self._event_registry[event] = EventInfo(
                    event_name=event,
                    registered_by=[module_name],
                    description=verb_spec.get("event_description")
                )
            else:
                # Event already registered by another module - track it
                if module_name not in self._event_registry[event].registered_by:
                    self._event_registry[event].registered_by.append(module_name)
```

**Benefits:**
1. **Discoverability**: Can query `behavior_manager.get_registered_events()` to see all events
2. **Validation**: Can validate entity behaviors reference real events
3. **Documentation**: Event registry can include descriptions for authors
4. **Extensibility**: New modules can add new event types without core changes
5. **Debugging**: Can see which modules contribute which events

**Usage Examples:**
```python
# Query available events
events = behavior_manager.get_registered_events()
# Returns: ["on_take", "on_damage", "on_heal", "on_attack", ...]

# Validate entity behavior
def validate_entity_behaviors(entity, behavior_manager):
    """Check that entity behaviors reference valid modules."""
    for behavior_module in entity.behaviors:
        if behavior_module not in behavior_manager.get_loaded_modules():
            raise ValueError(f"Entity {entity.id} references unknown behavior: {behavior_module}")

# Check if event is registered
if behavior_manager.has_event("on_damage"):
    # Event exists in system
```

**What This Means for Actor Interactions:**
- Core modules register events: `on_damage`, `on_heal`, `on_attack`, `on_death`, `on_condition_change`
- Game modules can register custom events: `on_examine_mushroom`, `on_phase_transition`
- No need to modify core to add new interaction types
- Event registry provides single source of truth

**Implementation Notes:**
- This is a **pure addition** - doesn't break existing code
- Event registry built during module loading (no separate registration step)
- Backward compatible - existing modules work without changes
- Can add optional event descriptions in vocabulary for documentation

**Rationale:**
- Follows same pattern as vocabulary: dynamic discovery from modules
- Maximizes extensibility - new event types via modules, not core changes
- Improves author experience - can see what events are available
- Enables better validation and error messages
- Consistent with architecture principle: no hardcoded knowledge in core

**Implications:**
- Phase 1 implementation can add event registry alongside core actor interactions
- Better developer experience when authoring behaviors
- Foundation for future tooling (behavior documentation, validation)
- Makes event system truly first-class and discoverable

---

## 30. Range Modeling: Properties Only, Authors Implement Selection

**Decision:** Range is an attack property that behaviors interpret. Core provides no range validation or enforcement. Authors implement range-based attack selection in their NPC behaviors.

**Range Property Convention:**
```python
"attacks": [
    {"name": "slam", "damage": 50, "range": "melee"},
    {"name": "charge", "damage": 30, "range": "near"},
    {"name": "flame_breath", "damage": 25, "range": "area"}
]
```

**Recommended Range Values:**
- `"melee"` / `"touch"` - Requires attacker and target to be `focused_on` same entity, or in same location part
- `"near"` - Same location (any part within location)
- `"area"` - Affects multiple targets (author defines scope)

**What Core Does NOT Do:**
- No automatic range validation
- No prevention of "out of range" attacks
- No spatial distance calculations for range

**What Authors Implement in Behaviors:**
```python
def npc_take_action(entity, accessor, context):
    """Author implements range-based attack selection."""
    target = get_target(entity, accessor)
    attacks = entity.properties.get('attacks', [])

    # Determine effective range to target
    same_part = is_same_part(entity, target, accessor)
    same_location = is_same_location(entity, target, accessor)

    # Filter attacks by range
    available_attacks = []
    for attack in attacks:
        range_type = attack.get('range', 'melee')
        if range_type in ['melee', 'touch'] and same_part:
            available_attacks.append(attack)
        elif range_type == 'near' and same_location:
            available_attacks.append(attack)
        elif range_type == 'area':
            available_attacks.append(attack)  # Always available

    if available_attacks:
        # Select best attack (author's strategy)
        attack = max(available_attacks, key=lambda a: a.get('damage', 0))
        execute_attack(entity, target, attack, accessor)
```

**Rationale:**
- Follows core/game boundary: core provides properties, authors provide strategy
- Different games may have different range semantics
- Spatial integration already exists - behaviors can query part positions
- Maximum flexibility for authors
- No hardcoded range rules to work around

**Implications:**
- Core attack command uses first attack (no range check) - author can customize
- NPC behaviors should implement range-aware attack selection
- Authors define what "melee" vs "near" means for their game
- Spatial utilities (`is_same_part`, `get_actor_location_part`) support range queries
- Phase 1: document conventions, provide example behaviors

---

## 31. Area Attacks: Entirely Author-Implemented

**Decision:** Area attacks have no special core handling. Authors implement target selection, friendly fire rules, cover interaction, and damage distribution in behaviors.

**Area Attack Property:**
```python
{
    "name": "flame_breath",
    "damage": 25,
    "range": "area",
    "area_scope": "location"  # Optional hint for behaviors
}
```

**What Core Does NOT Provide:**
- No automatic multi-target damage
- No friendly fire rules
- No area-of-effect calculations
- No cover interaction for area attacks

**Author Implementation Patterns:**

*Basic Area Attack (all targets in location):*
```python
def execute_area_attack(attacker, attack, accessor):
    """Hit all actors in same location."""
    location = accessor.get_entity_location(attacker)
    all_actors = get_actors_in_location(location.id, accessor)

    for target in all_actors:
        if target.id == attacker.id:
            continue  # Don't hit self
        execute_attack(attacker, target, attack, accessor)
```

*Area Attack with Friendly Fire Protection:*
```python
def execute_area_attack(attacker, attack, accessor):
    """Hit all non-allies in location."""
    location = accessor.get_entity_location(attacker)
    all_actors = get_actors_in_location(location.id, accessor)
    attacker_pack = attacker.properties.get('ai', {}).get('pack_id')

    for target in all_actors:
        if target.id == attacker.id:
            continue
        # Skip pack members (no friendly fire)
        target_pack = target.properties.get('ai', {}).get('pack_id')
        if attacker_pack and target_pack == attacker_pack:
            continue
        execute_attack(attacker, target, attack, accessor)
```

*Area Attack Respecting Cover:*
```python
def execute_area_attack(attacker, attack, accessor):
    """Area attack with cover reducing damage."""
    # ... target selection ...
    for target in targets:
        damage = attack.get('damage', 0)

        # Check if target has cover
        if target.properties.get('posture') == 'cover':
            cover_obj = accessor.get_entity(target.properties.get('focused_on'))
            if cover_obj:
                cover_value = cover_obj.properties.get('cover_value', 0)
                # Author decides: full cover protection, partial, or none
                damage = int(damage * (100 - cover_value) / 100)

        apply_damage(target, damage, accessor)
```

**Recommended Conventions:**
- Same damage to all targets (simplest)
- Friendly fire off by default (check pack_id)
- Cover optionally protects from area attacks (author's choice)
- `area_scope` property can hint at targeting (location, part, radius)

**Rationale:**
- Area attacks vary widely between games (breath weapons, explosions, auras)
- No single "correct" implementation
- Authors have full control over semantics
- Core stays simple - just single-target damage utility
- Follows established pattern from Decisions 15, 21, 28

**Implications:**
- Authors write area attack logic in behaviors
- Core `execute_attack()` handles single target - loop for multi-target
- Optional library helpers could provide common patterns
- Phase 1: document patterns, no core area attack handling

---

## 32. Immunities: Condition Immunity Only, Resistances Affect Damage Only

**Decision (Clarification of Decision 20):** Immunities block conditions entirely. Resistances reduce damage only, not condition severity. Authors implement both in behaviors.

**Immunity Behavior:**
```python
# Spider tries to poison stone golem
# Golem has: immunities: ["poison", "disease"]

def apply_condition_with_immunity_check(target, condition_name, condition_props, accessor):
    """Check immunity before applying condition."""
    immunities = target.properties.get('immunities', [])
    if condition_name in immunities:
        return False  # Condition blocked entirely

    add_condition(target, condition_name, condition_props, accessor)
    return True
```

**Resistance Behavior (Damage Only):**
```python
def on_damage(entity, accessor, context):
    """Resistances reduce damage, not condition severity."""
    damage = context['damage_amount']
    damage_type = context.get('damage_type', 'physical')

    # Apply resistance to DAMAGE
    resistances = entity.properties.get('resistances', {})
    if damage_type in resistances:
        resistance_percent = resistances[damage_type]
        damage = int(damage * (100 - resistance_percent) / 100)

    # Condition severity is NOT affected by resistances
    # If attack applies condition, it applies at full severity

    apply_damage(entity, damage, accessor)
```

**Why Resistances Don't Affect Condition Severity:**
- Simpler mental model: resistances = damage reduction
- Conditions already have their own severity property
- If author wants reduced severity, they implement in `on_condition_applied` behavior
- Keeps damage and condition systems independent

**Author Pattern for Severity Reduction (Optional):**
```python
def on_condition_applied(entity, accessor, context):
    """Custom: reduce condition severity based on resistances."""
    condition_name = context['condition_name']
    condition_props = context['condition_props']

    # Check if entity has resistance to this condition type
    resistances = entity.properties.get('resistances', {})
    if condition_name in resistances:
        reduction = resistances[condition_name] / 100
        condition_props['severity'] = int(condition_props['severity'] * (1 - reduction))

    # Continue with modified severity
    return EventResult(allow=True)
```

**Rationale:**
- Clear separation: immunities block, resistances reduce damage
- Simpler for authors to reason about
- Conditions and damage are independent systems
- Authors can add severity reduction if needed

**Implications:**
- Core immunity check only handles condition blocking
- Resistance calculations happen in behaviors before `apply_damage()`
- Phase 1: immunity check utility, resistance pattern documented
- Authors wanting severity reduction implement custom behavior

---

## 33. Weaknesses: Damage Multipliers, Author-Implemented

**Decision:** Weaknesses are properties that behaviors interpret as damage multipliers. Core does NOT interpret weaknesses. Authors implement weakness checking in `on_damage` behaviors.

**Weakness Property Convention:**
```python
# Boss weak to ice
"weaknesses": {
    "ice": 200,    # 200% = 2x damage
    "fire": 150    # 150% = 1.5x damage
}
```

**What Core Does NOT Do:**
- No automatic weakness application
- No damage type interpretation
- No condition severity modification from weaknesses

**Author Implementation:**
```python
def on_damage(entity, accessor, context):
    """Apply weakness multipliers to damage."""
    damage = context['damage_amount']
    damage_type = context.get('damage_type', 'physical')

    # Check weakness
    weaknesses = entity.properties.get('weaknesses', {})
    if damage_type in weaknesses:
        multiplier = weaknesses[damage_type] / 100  # 200 → 2.0
        damage = int(damage * multiplier)

    # Check resistance (applied after weakness)
    resistances = entity.properties.get('resistances', {})
    if damage_type in resistances:
        reduction = resistances[damage_type] / 100
        damage = int(damage * (1 - reduction))

    # Apply armor (flat reduction last)
    armor = entity.properties.get('armor', 0)
    final_damage = max(0, damage - armor)

    apply_damage(entity, final_damage, accessor)
```

**Damage Type Convention:**
```python
# Attack specifies damage type
{
    "name": "ice_blast",
    "damage": 20,
    "damage_type": "ice"
}

# Default is "physical" if not specified
```

**Recommended Order of Operations:**
1. Base damage from attack
2. Apply environmental bonuses (if any)
3. Apply weakness multiplier (increases damage)
4. Apply resistance reduction (decreases damage)
5. Apply armor (flat subtraction)
6. Final damage applied to health

**Weaknesses Affect Damage Only (Recommended):**
- Weakness multiplies damage, not condition severity
- Keeps systems simple and independent
- If author wants condition enhancement, they implement separately

**Rationale:**
- Follows established pattern: properties only, authors implement
- Different games may calculate weaknesses differently
- Percentage multiplier is intuitive (200 = double)
- Clear order of operations prevents confusion
- Damage types are semantic, not enforced by core

**Implications:**
- Authors must implement weakness checks in behaviors
- Core `apply_damage()` just subtracts from health (after armor)
- Phase 1: document conventions, provide example `on_damage` behavior
- Damage types are strings - authors define their own
- Standard types: "physical", "fire", "ice", "poison", "lightning" (conventions, not enforced)

---

## Summary of Decisions

| # | Decision | Type |
|---|----------|------|
| 1 | Actor interaction framework in core | Architecture |
| 2 | First-class event integration | Architecture |
| 3 | NPCs act after player commands | Timing |
| 4 | Every command is a turn | Timing |
| 5 | Full serialization of temporal state | Save/Load |
| 6 | Core provides infrastructure, authors provide strategy | Boundary |
| 7 | Start with no defaults, evolve toward convenience | Scope |
| 8 | Property schemas are conventions, not requirements | Flexibility |
| 9 | Deterministic outcomes by default | Game Mechanics |
| 10 | Conditions stored as dict, explicit progression | Core Systems |
| 11 | Same condition replaces, different conditions coexist | Core Systems |
| 12 | Cures remove condition entirely | Core Systems |
| 13 | Damage = attack - armor, minimum 0 | Core Systems |
| 14 | Armor is flat damage reduction | Core Systems |
| 15 | Authors implement NPC AI via behaviors | Core Systems |
| 16 | Environmental hazards automatic, bonuses opt-in | Environment |
| 17 | Breath optional property, automatic depletion | Environment |
| 18 | Core provides attack command, authors add others | Commands |
| 19 | on_death behavior determines consequences | Game Mechanics |
| 20 | Immunities binary, resistances author-optional | Game Mechanics |
| 21 | Damage modification in behaviors, core provides utility | Core Systems |
| 22 | Armor property only, author sets value | Core Systems |
| 23 | Morale properties only, authors implement logic | AI/Strategy |
| 24 | Pack properties only, authors implement logic | AI/Strategy |
| 25 | Event types dynamically discovered via registry | Architecture |
| 26 | Environmental constants in metadata, not hardcoded | Environment |
| 27 | Environmental bonuses are conventions, not enforced | Environment |
| 28 | Cover mechanics author-implemented via properties | Environment |
| 29 | Core provides attack, defend, guide, activate commands | Commands |
| 30 | Range is property only, authors implement selection | Combat |
| 31 | Area attacks entirely author-implemented | Combat |
| 32 | Immunities block conditions, resistances reduce damage only | Combat |
| 33 | Weaknesses are damage multipliers, author-implemented | Combat |
| 34 | NPC movement is author-implemented in behaviors | AI/Movement |
| 35 | Activation triggers via observer or event patterns | AI/Triggers |
| 36 | Fleeing is author-implemented movement | AI/Movement |
| 37 | Pack coordination scales via cheap checks | AI/Performance |
| 38 | Behaviors can fire events without commands | Architecture |

---

## 34. NPC Movement: Author-Implemented in Behaviors

**Decision (Clarification of Decision 3):** NPCs can move between locations. Movement is author-implemented in `npc_take_action` behaviors using standard accessor methods. Core provides no automatic NPC movement.

**How NPC Movement Works:**
- NPCs are entities like any other - they have locations
- Authors move NPCs using `accessor.move_entity()` or equivalent
- Movement logic (patrol, pursue, flee, wander) is behavior code
- Core turn progression just invokes `npc_take_action` - what happens is up to author

**Example Patterns:**

*Patrol Behavior:*
```python
def npc_take_action(entity, accessor, context):
    """Guard patrols between waypoints."""
    ai = entity.properties.get('ai', {})
    waypoints = ai.get('patrol_waypoints', [])
    current_index = ai.get('patrol_index', 0)

    if waypoints and not ai.get('hostile'):
        next_location = waypoints[current_index]
        accessor.move_entity(entity.id, next_location)
        new_index = (current_index + 1) % len(waypoints)
        accessor.update(entity, {'properties.ai.patrol_index': new_index})
```

*Pursue Player:*
```python
def npc_take_action(entity, accessor, context):
    """Hostile NPC pursues player."""
    if not entity.properties.get('ai', {}).get('hostile'):
        return

    player = accessor.get_player()
    player_loc = accessor.get_entity_location(player)
    my_loc = accessor.get_entity_location(entity)

    if player_loc.id != my_loc.id:
        # Move toward player (author implements pathfinding if needed)
        path = find_path_to(my_loc.id, player_loc.id, accessor)
        if path:
            accessor.move_entity(entity.id, path[0])
    else:
        # Same location - attack instead
        execute_attack(entity, player, ...)
```

**Rationale:**
- NPCs are first-class entities - should be able to do anything player can
- Different games need different movement patterns
- No automatic movement avoids unwanted NPC behavior
- Authors have full control over when/where NPCs move

**Implications:**
- Authors implement patrol, pursuit, fleeing, wandering as needed
- Pathfinding (if needed) is author responsibility
- NPC movement triggers same location events as player movement
- Phase 1: document patterns, provide no automatic NPC movement

---

## 35. Activation Triggers: Observer or Event Patterns, Author-Implemented

**Decision:** Activation triggers (golem activates when player enters, guard alerts when seeing theft) have no core system. Authors implement via observer pattern (NPC checks each turn) or event pattern (location/behavior fires event).

**No Core Trigger System:**
- Core does NOT check activation conditions
- Core does NOT maintain trigger state
- All activation logic is in behaviors

**Observer Pattern (NPC Checks Each Turn):**
```python
def npc_take_action(entity, accessor, context):
    """Golem checks activation condition each turn."""
    ai = entity.properties.get('ai', {})

    # Already active - do normal behavior
    if ai.get('hostile'):
        # ... attack logic ...
        return

    # Check activation trigger
    trigger = ai.get('activation_trigger')
    if trigger == 'player_enters_center':
        player = accessor.get_player()
        player_part = get_actor_location_part(player, accessor)
        if player_part and player_part.id == 'part_hall_center':
            accessor.update(entity, {'properties.ai.hostile': True})
            # Optionally fire activation event for narration
            accessor.fire_event(entity, 'on_activate', {})
```

**Event Pattern (Location Fires Event):**
```python
# Behavior on part_hall_center
def on_enter(entity, accessor, context):
    """When player enters center, activate all golems."""
    entering_entity = context.get('entity')
    if entering_entity.id != accessor.get_player().id:
        return  # Only trigger for player

    # Find all entities with matching activation trigger
    all_actors = accessor.get_all_entities_by_type('actor')
    for actor in all_actors:
        trigger = actor.properties.get('ai', {}).get('activation_trigger')
        if trigger == 'player_enters_center':
            accessor.update(actor, {'properties.ai.hostile': True})
            accessor.fire_event(actor, 'on_activate', {})
```

**Deactivation:**
Same patterns work for deactivation:
- Observer: NPC checks if deactivation condition met
- Event: Rune's `on_activate` behavior sets golems to non-hostile

**Rationale:**
- Trigger conditions vary wildly (proximity, sight, time, event)
- No single trigger system could cover all cases
- Observer pattern is simple and flexible
- Event pattern integrates with existing behavior system
- Authors choose pattern that fits their needs

**Implications:**
- Authors define `activation_trigger` property as semantic hint
- Actual trigger logic is in behaviors
- Can combine patterns (location event sets flag, NPC checks flag)
- Phase 1: document both patterns with examples

---

## 36. Fleeing: Author-Implemented Movement

**Decision:** Fleeing is just NPC movement with different motivation. No special flee system. Authors implement flee logic in `npc_take_action` behaviors.

**Fleeing is Movement:**
- When morale < threshold, NPC decides to flee
- "Flee" means move away from threat
- Uses same movement mechanisms as patrol/pursuit
- NPC stays in game unless author explicitly removes

**Flee Destination Options (All Author-Implemented):**

*Specific Destination:*
```python
def npc_take_action(entity, accessor, context):
    """Flee to designated safe location."""
    ai = entity.properties.get('ai', {})

    if ai.get('morale', 100) < ai.get('flee_threshold', 20):
        flee_dest = ai.get('flee_destination')
        if flee_dest:
            current_loc = accessor.get_entity_location(entity)
            if current_loc.id != flee_dest:
                move_toward(entity, flee_dest, accessor)
            return  # Fleeing consumes action

    # Normal combat if not fleeing
    # ...
```

*Nearest Exit:*
```python
def npc_take_action(entity, accessor, context):
    """Flee via nearest exit."""
    ai = entity.properties.get('ai', {})

    if ai.get('morale', 100) < ai.get('flee_threshold', 20):
        current_loc = accessor.get_entity_location(entity)
        exits = get_exits_from_location(current_loc, accessor)
        if exits:
            # Pick exit furthest from player
            player_loc = accessor.get_entity_location(accessor.get_player())
            best_exit = select_exit_away_from(exits, player_loc, accessor)
            use_exit(entity, best_exit, accessor)
        return
```

*Cower in Place:*
```python
def npc_take_action(entity, accessor, context):
    """No flee destination - cower instead."""
    ai = entity.properties.get('ai', {})

    if ai.get('morale', 100) < ai.get('flee_threshold', 20):
        if not ai.get('flee_destination'):
            # No destination - just stop fighting
            accessor.update(entity, {'properties.ai.hostile': False})
            accessor.update(entity, {'properties.posture': 'cowering'})
        return
```

**What Happens at Destination:**
Author decides:
- NPC stays and recovers morale over time
- NPC despawns (removed from game)
- NPC becomes non-hostile but remains
- NPC alerts other NPCs at destination

**Rationale:**
- Fleeing is conceptually simple - just movement
- Different games handle flee differently
- Some want pursuable NPCs, others want despawn
- No artificial complexity needed

**Implications:**
- Authors store `flee_destination` or `flee_via` as properties
- Flee logic in `npc_take_action` checks morale threshold
- NPC remains in game world unless author removes
- Morale recovery (if any) is author-implemented

---

## 37. Pack Coordination Scaling: Cheap Checks Pattern

**Decision (Clarification of Decision 24):** Multiple packs are supported. Pack coordination scales well via cheap early-return checks. Range limits for coordination are optional and author-controlled.

**Multiple Packs:**
- `pack_id` is just a string - unlimited distinct packs
- Each pack operates independently
- No global pack registry needed

**Scaling via Cheap Checks:**
```python
def npc_take_action(entity, accessor, context):
    """Pack member with cheap early checks."""
    # CHEAP CHECK 1: Is player in my location?
    player = accessor.get_player()
    player_loc = accessor.get_entity_location(player)
    my_loc = accessor.get_entity_location(entity)

    if player_loc.id != my_loc.id:
        return  # Nothing to do - player not here

    # CHEAP CHECK 2: Am I a follower?
    ai = entity.properties.get('ai', {})
    follows = ai.get('follows_alpha')

    if follows:
        # Only now do more expensive alpha lookup
        alpha = accessor.get_entity(follows)
        if alpha and alpha.properties.get('ai', {}).get('hostile'):
            if not ai.get('hostile'):
                accessor.update(entity, {'properties.ai.hostile': True})

    # Normal behavior continues...
```

**Range-Limited Coordination (Optional):**
```python
def npc_take_action(entity, accessor, context):
    """Pack follower only coordinates with nearby alpha."""
    ai = entity.properties.get('ai', {})
    follows = ai.get('follows_alpha')

    if follows:
        alpha = accessor.get_entity(follows)
        if alpha:
            # Range check: only coordinate if alpha in same location
            alpha_loc = accessor.get_entity_location(alpha)
            my_loc = accessor.get_entity_location(entity)

            if alpha_loc.id == my_loc.id:
                # Coordinate with alpha
                if alpha.properties.get('ai', {}).get('hostile'):
                    accessor.update(entity, {'properties.ai.hostile': True})
            # If alpha far away, act independently
```

**Performance Characteristics:**
- 20 wolves × cheap location check = negligible overhead
- Expensive operations (entity queries) only when checks pass
- "All NPCs everywhere" pattern works fine at reasonable scale
- For truly massive scale (hundreds of NPCs), authors can implement location-based NPC lists

**No Artificial Limits:**
- No maximum pack size
- No maximum number of packs
- No forced range restrictions
- Authors optimize if needed for their specific game

**Rationale:**
- Simple pack behavior needs no optimization
- Cheap checks pattern already established (Decision 3)
- Range limits are game design choice, not technical requirement
- Maximum flexibility for authors

**Implications:**
- Authors define pack_id as needed
- Pack coordination patterns documented with examples
- Range-limited coordination is optional pattern
- Phase 1: document patterns, no pack-specific infrastructure

---

## 38. Behaviors Can Fire Events Without Commands

**Decision:** Behavior modules can fire events into the event system for dispatch without requiring a player command. This enables NPC-initiated interactions, environmental triggers, and internal game events.

**Event Firing Mechanisms:**

*Via Accessor:*
```python
def npc_take_action(entity, accessor, context):
    """NPC behavior fires events."""
    # NPC attacks player - fire damage event
    accessor.fire_event(
        target=player,
        event_type='on_damage',
        context={
            'attacker_id': entity.id,
            'damage_amount': 15,
            'damage_type': 'physical'
        }
    )

    # NPC activates - fire activation event for narration
    accessor.fire_event(
        target=entity,
        event_type='on_activate',
        context={'trigger': 'player_proximity'}
    )
```

*Via State Changes with Verb:*
```python
def environmental_effect(part, accessor, context):
    """Environmental hazard applies condition."""
    for actor in get_actors_in_part(part, accessor):
        # This fires on_condition_applied event
        accessor.update(
            actor,
            {'properties.conditions.burning': {...}},
            verb='condition_applied',
            condition_name='burning'
        )
```

**Use Cases for Behavior-Initiated Events:**
1. **NPC attacks** - fires `on_damage` on target
2. **NPC heals ally** - fires `on_heal` on ally
3. **Trap triggers** - fires `on_damage` when player steps on trap
4. **Environmental hazard** - fires `on_condition_applied` from location behavior
5. **Golem activates** - fires `on_activate` for narration hooks
6. **Pack alert** - alpha fires `on_pack_alert` that followers respond to

**Event Flow:**
```
Player command
  → Handler executes
  → Turn progression begins
  → NPC behaviors fire (may fire events)
  → Environmental behaviors fire (may fire events)
  → Condition progression (may fire events)
  → All events dispatched to appropriate handlers
  → Results collected for narration
```

**No Command Required:**
- Events can originate from any behavior, not just command handlers
- `accessor.fire_event()` is available to all behaviors
- Event registry (Decision 25) tracks all event types regardless of source
- Enables rich NPC-to-NPC and environment-to-actor interactions

**Rationale:**
- Commands are player-initiated, but game world has autonomous actors
- NPCs attacking player must fire damage events
- Environmental hazards must apply conditions
- Pack coordination may use events for communication
- Consistent event flow regardless of initiator

**Implications:**
- `accessor.fire_event()` available in all behavior contexts
- Events from behaviors use same dispatch as command-initiated events
- Narrator receives events from all sources
- Phase 1: ensure event firing works from behavior context

---

## Summary of Decisions

| # | Decision | Type |
|---|----------|------|
| 1 | Actor interaction framework in core | Architecture |
| 2 | First-class event integration | Architecture |
| 3 | NPCs act after player commands | Timing |
| 4 | Every command is a turn | Timing |
| 5 | Full serialization of temporal state | Save/Load |
| 6 | Core provides infrastructure, authors provide strategy | Boundary |
| 7 | Start with no defaults, evolve toward convenience | Scope |
| 8 | Property schemas are conventions, not requirements | Flexibility |
| 9 | Deterministic outcomes by default | Game Mechanics |
| 10 | Conditions stored as dict, explicit progression | Core Systems |
| 11 | Same condition replaces, different conditions coexist | Core Systems |
| 12 | Cures remove condition entirely | Core Systems |
| 13 | Damage = attack - armor, minimum 0 | Core Systems |
| 14 | Armor is flat damage reduction | Core Systems |
| 15 | Authors implement NPC AI via behaviors | Core Systems |
| 16 | Environmental hazards automatic, bonuses opt-in | Environment |
| 17 | Breath optional property, automatic depletion | Environment |
| 18 | Core provides attack command, authors add others | Commands |
| 19 | on_death behavior determines consequences | Game Mechanics |
| 20 | Immunities binary, resistances author-optional | Game Mechanics |
| 21 | Damage modification in behaviors, core provides utility | Core Systems |
| 22 | Armor property only, author sets value | Core Systems |
| 23 | Morale properties only, authors implement logic | AI/Strategy |
| 24 | Pack properties only, authors implement logic | AI/Strategy |
| 25 | Event types dynamically discovered via registry | Architecture |
| 26 | Environmental constants in metadata, not hardcoded | Environment |
| 27 | Environmental bonuses are conventions, not enforced | Environment |
| 28 | Cover mechanics author-implemented via properties | Environment |
| 29 | Core provides attack, defend, guide, activate commands | Commands |
| 30 | Range is property only, authors implement selection | Combat |
| 31 | Area attacks entirely author-implemented | Combat |
| 32 | Immunities block conditions, resistances reduce damage only | Combat |
| 33 | Weaknesses are damage multipliers, author-implemented | Combat |
| 34 | NPC movement is author-implemented in behaviors | AI/Movement |
| 35 | Activation triggers via observer or event patterns | AI/Triggers |
| 36 | Fleeing is author-implemented movement | AI/Movement |
| 37 | Pack coordination scales via cheap checks | AI/Performance |
| 38 | Behaviors can fire events without commands | Architecture |
| 39 | Services triggered via give, resolved in on_receive | Services |
| 40 | Binary knowledge array, no skill levels | Knowledge |
| 41 | Relationships stored on actor, threshold-based effects | Social |

---

## 39. NPC Services: Triggered via Give, Resolved in on_receive

**Decision:** NPC services are triggered when player gives an item. The NPC's `on_receive` behavior checks if the item matches a service requirement and executes the service. No automatic service system in core.

**Service Property Convention:**
```python
"services": {
    "cure_poison": {
        "accepts": ["rare_herbs", "gold"],
        "amount_required": 1,
        "gold_cost": 50,
        "effect": "remove_condition",
        "condition": "poison"
    },
    "teach_herbalism": {
        "accepts": ["gold"],
        "gold_cost": 100,
        "effect": "grant_knowledge",
        "grants": "herbalism"
    },
    "heal_wounds": {
        "accepts": ["gold"],
        "gold_cost": 25,
        "effect": "restore_health",
        "amount": 30
    }
}
```

**Service Resolution in on_receive:**
```python
def on_receive(entity, accessor, context):
    """NPC receives item, checks if it fulfills a service."""
    item = context.get('item')
    giver = context.get('giver')
    services = entity.properties.get('services', {})

    for service_name, service_def in services.items():
        accepts = service_def.get('accepts', [])
        # Check if item type matches (by id or by tag)
        if item.id in accepts or item.properties.get('type') in accepts:
            # Execute the service
            execute_service(entity, giver, service_name, service_def, accessor)
            return EventResult(allow=True, message=f"{entity.name} accepts your offering.")

    # Item doesn't match any service
    return EventResult(allow=False, message=f"{entity.name} has no use for that.")
```

**Service Effect Patterns:**
```python
def execute_service(npc, recipient, service_name, service_def, accessor):
    """Execute service effect based on effect type."""
    effect = service_def.get('effect')

    if effect == 'remove_condition':
        condition = service_def.get('condition')
        remove_condition(recipient, condition, accessor)

    elif effect == 'grant_knowledge':
        knowledge = service_def.get('grants')
        knows = recipient.properties.get('knows', [])
        if knowledge not in knows:
            knows.append(knowledge)
            accessor.update(recipient, {'properties.knows': knows})

    elif effect == 'restore_health':
        amount = service_def.get('amount', 20)
        current = recipient.properties.get('health', 0)
        max_health = recipient.properties.get('max_health', 100)
        new_health = min(max_health, current + amount)
        accessor.update(recipient, {'properties.health': new_health})

    # Fire event for narration
    accessor.fire_event(npc, 'on_service_provided', {
        'service': service_name,
        'recipient': recipient.id
    })
```

**Inquiry via Ask Command:**
```python
def on_ask(entity, accessor, context):
    """Player asks about available services."""
    topic = context.get('topic')
    services = entity.properties.get('services', {})

    if topic in services:
        service = services[topic]
        accepts = service.get('accepts', [])
        return EventResult(
            allow=True,
            message=f"I can help with {topic}. Bring me {' or '.join(accepts)}."
        )

    return EventResult(allow=True, message="I cannot help with that.")
```

**Gold Handling:**
- Gold is just an item with `type: "currency"` or specific id
- `gold_cost` in service checked against item's `amount` property
- Or use separate gold tracking in player properties

**Rationale:**
- Uses existing `give` command infrastructure
- `on_receive` is natural behavior hook
- Services are fully data-driven via properties
- Authors implement service effects in behaviors
- No special service command needed

**Implications:**
- Authors define services in NPC properties
- `on_receive` behavior checks services and executes
- Standard effects (heal, cure, teach) can be library helpers
- Custom effects implemented in game-specific behaviors
- Phase 1: document patterns, no core service system

---

## 40. Knowledge: Binary Array, No Skill Levels

**Decision:** Knowledge is modeled as a binary array of known topics/skills. No skill levels. Behaviors gate actions by checking if knowledge is present.

**Knowledge Property:**
```python
# Actor knows these things
"knows": ["herbalism", "lockpicking", "ancient_languages", "swimming"]
```

**Knowledge Check Pattern:**
```python
def on_examine(entity, accessor, context):
    """Examining requires relevant knowledge."""
    examiner = context.get('examiner')
    knows = examiner.properties.get('knows', [])

    # Plant examination requires herbalism
    if entity.properties.get('type') == 'plant':
        if 'herbalism' in knows:
            return EventResult(
                allow=True,
                message=f"You recognize this as {entity.properties.get('true_name')}. {entity.properties.get('expert_description')}"
            )
        else:
            return EventResult(
                allow=True,
                message=entity.properties.get('naive_description', 'A plant.')
            )
```

**Teaching Adds Knowledge:**
```python
def grant_knowledge(learner, knowledge_name, accessor):
    """Add knowledge to actor's knows array."""
    knows = learner.properties.get('knows', [])
    if knowledge_name not in knows:
        knows.append(knowledge_name)
        accessor.update(learner, {'properties.knows': knows})
        return True
    return False  # Already knew it
```

**Knowledge Gates Actions:**
```python
def handle_pick_lock(command, state, accessor):
    """Lockpicking requires knowledge."""
    player = accessor.get_player()
    knows = player.properties.get('knows', [])

    if 'lockpicking' not in knows:
        return CommandResult(
            success=False,
            message="You don't know how to pick locks."
        )

    # Proceed with lockpicking
    # ...
```

**Why No Skill Levels:**
- Evaluation recommends deferring detailed skill system
- Levels require balancing and difficulty tuning
- Binary is simpler: you can or you can't
- Deterministic outcomes (Decision 9) - no skill checks
- If author needs levels, they extend with dict

**Optional Level Extension (Author Pattern):**
```python
# If author wants skill levels
"knowledge": {
    "herbalism": "expert",    # novice, journeyman, expert, master
    "lockpicking": "novice"
}

# Check in behavior
def can_pick_complex_lock(actor):
    knowledge = actor.properties.get('knowledge', {})
    level = knowledge.get('lockpicking', None)
    return level in ['expert', 'master']
```

**Rationale:**
- Simplest model that enables knowledge-gated content
- No skill check mechanics to implement
- Authors define what knowledge enables
- Extension to levels is straightforward if needed

**Implications:**
- `knows` array on actors who can learn
- Behaviors check for specific knowledge strings
- Teaching services add to knows array
- No core skill check system
- Phase 1: document pattern, provide no skill infrastructure

---

## 41. Relationships: Stored on Actor, Threshold-Based Effects

**Decision:** Relationships are stored in actor properties. Authors modify relationship values in behaviors. Effects use simple thresholds rather than complex calculations.

**Relationship Property:**
```python
"relationships": {
    "player": {
        "trust": 50,      # How much NPC trusts player
        "gratitude": 0,   # Favors owed / appreciation
        "fear": 0         # Intimidation level
    },
    "npc_rival": {
        "hostility": 80
    }
}
```

**Lazy Initialization:**
```python
def get_relationship(actor, target_id, accessor):
    """Get or initialize relationship with target."""
    relationships = actor.properties.get('relationships', {})
    if target_id not in relationships:
        relationships[target_id] = {'trust': 0, 'gratitude': 0, 'fear': 0}
        accessor.update(actor, {'properties.relationships': relationships})
    return relationships[target_id]
```

**Modifying Relationships:**
```python
def on_receive(entity, accessor, context):
    """Giving gifts increases gratitude."""
    giver = context.get('giver')
    item = context.get('item')

    rel = get_relationship(entity, giver.id, accessor)

    # Gift increases gratitude
    if item.properties.get('gift_value'):
        rel['gratitude'] = rel.get('gratitude', 0) + item.properties['gift_value']
    else:
        rel['gratitude'] = rel.get('gratitude', 0) + 1

    # Update relationship
    relationships = entity.properties.get('relationships', {})
    relationships[giver.id] = rel
    accessor.update(entity, {'properties.relationships': relationships})
```

**Threshold-Based Effects:**
```python
def get_disposition(npc, toward_actor, accessor):
    """Determine NPC disposition based on relationship thresholds."""
    rel = get_relationship(npc, toward_actor.id, accessor)

    gratitude = rel.get('gratitude', 0)
    trust = rel.get('trust', 0)
    fear = rel.get('fear', 0)

    # Simple thresholds
    if gratitude >= 5:
        return 'loyal'      # Will follow, defend, give discounts
    elif trust >= 50:
        return 'friendly'   # Helpful, discounts
    elif trust >= 20:
        return 'neutral'    # Normal interactions
    elif fear >= 50:
        return 'intimidated'  # Complies but resentful
    else:
        return 'wary'       # Limited interactions
```

**Effects in Behaviors:**
```python
def get_service_cost(npc, customer, service_def, accessor):
    """Relationship affects pricing."""
    base_cost = service_def.get('gold_cost', 0)
    disposition = get_disposition(npc, customer, accessor)

    if disposition == 'loyal':
        return 0  # Free for loyal friends
    elif disposition == 'friendly':
        return int(base_cost * 0.8)  # 20% discount
    elif disposition == 'intimidated':
        return int(base_cost * 0.5)  # Fear discount
    else:
        return base_cost

def will_follow(npc, leader, accessor):
    """Check if NPC will follow based on relationship."""
    disposition = get_disposition(npc, leader, accessor)
    return disposition in ['loyal', 'intimidated']
```

**Relationship Changes from Actions:**
- Giving gifts: +gratitude
- Completing quests for NPC: +trust, +gratitude
- Combat assistance: +trust
- Threatening: +fear, -trust
- Stealing (witnessed): -trust
- Repeated positive interactions: cumulative effects

**Why Thresholds Over Formulas:**
- Simple to understand and author
- Clear breakpoints for behavior changes
- No complex reputation math
- Easy to tune by adjusting threshold values
- Authors can use continuous effects if preferred

**Rationale:**
- Relationships are just properties - saved automatically
- Lazy init avoids cluttering definitions
- Thresholds provide clear behavioral changes
- Authors control all relationship mechanics

**Implications:**
- Authors define relationship properties as needed
- Behaviors modify relationships on relevant events
- Threshold checks determine NPC responses
- No core relationship system - pure patterns
- Phase 1: document patterns and examples

---

## Summary of Decisions

| # | Decision | Type |
|---|----------|------|
| 1 | Actor interaction framework in core | Architecture |
| 2 | First-class event integration | Architecture |
| 3 | NPCs act after player commands | Timing |
| 4 | Every command is a turn | Timing |
| 5 | Full serialization of temporal state | Save/Load |
| 6 | Core provides infrastructure, authors provide strategy | Boundary |
| 7 | Start with no defaults, evolve toward convenience | Scope |
| 8 | Property schemas are conventions, not requirements | Flexibility |
| 9 | Deterministic outcomes by default | Game Mechanics |
| 10 | Conditions stored as dict, explicit progression | Core Systems |
| 11 | Same condition replaces, different conditions coexist | Core Systems |
| 12 | Cures remove condition entirely | Core Systems |
| 13 | Damage = attack - armor, minimum 0 | Core Systems |
| 14 | Armor is flat damage reduction | Core Systems |
| 15 | Authors implement NPC AI via behaviors | Core Systems |
| 16 | Environmental hazards automatic, bonuses opt-in | Environment |
| 17 | Breath optional property, automatic depletion | Environment |
| 18 | Core provides attack command, authors add others | Commands |
| 19 | on_death behavior determines consequences | Game Mechanics |
| 20 | Immunities binary, resistances author-optional | Game Mechanics |
| 21 | Damage modification in behaviors, core provides utility | Core Systems |
| 22 | Armor property only, author sets value | Core Systems |
| 23 | Morale properties only, authors implement logic | AI/Strategy |
| 24 | Pack properties only, authors implement logic | AI/Strategy |
| 25 | Event types dynamically discovered via registry | Architecture |
| 26 | Environmental constants in metadata, not hardcoded | Environment |
| 27 | Environmental bonuses are conventions, not enforced | Environment |
| 28 | Cover mechanics author-implemented via properties | Environment |
| 29 | Core provides attack, defend, guide, activate commands | Commands |
| 30 | Range is property only, authors implement selection | Combat |
| 31 | Area attacks entirely author-implemented | Combat |
| 32 | Immunities block conditions, resistances reduce damage only | Combat |
| 33 | Weaknesses are damage multipliers, author-implemented | Combat |
| 34 | NPC movement is author-implemented in behaviors | AI/Movement |
| 35 | Activation triggers via observer or event patterns | AI/Triggers |
| 36 | Fleeing is author-implemented movement | AI/Movement |
| 37 | Pack coordination scales via cheap checks | AI/Performance |
| 38 | Behaviors can fire events without commands | Architecture |
| 39 | Services triggered via give, resolved in on_receive | Services |
| 40 | Binary knowledge array, no skill levels | Knowledge |
| 41 | Relationships stored on actor, threshold-based effects | Social |
| 42 | Deterministic mechanics, random event ordering | Randomness |
| 43 | Condition duration managed by progress_conditions() | Core Systems |
| 44 | Death check after all turn effects resolve | Timing |
| 45 | TDD with unit, integration, and scenario tests | Testing |

---

## 42. Randomness: Deterministic Mechanics, Random Event Ordering

**Decision (Clarification of Decision 9):** Game mechanics (damage, conditions, immunities) are deterministic. Event ordering (NPC action sequence) is random by default. This provides variety without unpredictable outcomes.

**What Is Deterministic:**
- Damage calculation: `damage = attack - armor` (no variance)
- Condition application: if attack has condition, it applies (no resist roll)
- Immunity checks: immune or not (no partial immunity)
- Treatment: cure removes condition (no failure chance)
- Environmental effects: hazards apply predictably

**What Is Random:**
- NPC action order within a turn (per Decision 3)
- Can be switched to deterministic via config for testing/debugging

**Why This Balance Works:**
- Players can plan tactics knowing damage amounts
- Variety comes from which NPC acts first, not whether attacks hit
- Different turn orderings create different narratives
- Deterministic mode available for reproducible testing

**Event Ordering Randomness:**
```python
def process_npc_actions(state, accessor):
    """Process NPC actions in random or deterministic order."""
    npcs = get_all_npcs(state)

    if state.settings.get('deterministic_event_order', False):
        # Deterministic: sort by ID
        npcs = sorted(npcs, key=lambda n: n.id)
    else:
        # Random: shuffle
        random.shuffle(npcs)

    for npc in npcs:
        invoke_npc_behavior(npc, accessor)
```

**No RNG Seeding Required:**
- Random ordering doesn't affect save/load (save happens between turns)
- Each turn's random order is independent
- No need to serialize RNG state

**Author-Added Randomness:**
If authors want random damage variance or hit chances:
```python
import random

def on_damage(entity, accessor, context):
    """Custom behavior with author-added randomness."""
    base_damage = context['damage_amount']
    # Author adds ±20% variance
    variance = random.uniform(0.8, 1.2)
    actual_damage = int(base_damage * variance)
    apply_damage(entity, actual_damage, accessor)
```

**Rationale:**
- Deterministic mechanics = predictable, testable, fair
- Random ordering = variety, replayability, emergent narratives
- Authors can add randomness if desired
- Best of both worlds

**Implications:**
- Core damage/condition systems have no randomness
- Turn processing randomizes NPC order by default
- `deterministic_event_order` config switch for testing
- Authors implement any additional randomness in behaviors

---

## 43. Condition Duration: Managed by progress_conditions()

**Decision (Clarification of Decision 10):** The core `progress_conditions()` utility handles duration tracking. It decrements duration each turn, applies per-turn damage, and removes expired conditions. No global turn counter needed.

**Duration Semantics:**
- `duration: 10` - condition lasts 10 more turns
- `duration: None` - permanent until explicitly removed
- `duration: 0` - expired, will be removed this turn

**progress_conditions() Implementation:**
```python
def progress_conditions(actor, accessor):
    """Called during turn progression phase for each actor."""
    conditions = actor.properties.get('conditions', {})
    if not conditions:
        return

    expired = []
    total_damage = 0

    for name, props in conditions.items():
        # Apply per-turn damage
        damage = props.get('damage_per_turn', 0)
        if damage > 0:
            total_damage += damage

        # Decrement duration (if not permanent)
        duration = props.get('duration')
        if duration is not None:
            props['duration'] = duration - 1
            if props['duration'] <= 0:
                expired.append(name)
                # Fire expiration event for narration
                accessor.fire_event(actor, 'on_condition_expired', {
                    'condition': name
                })

    # Apply accumulated damage once
    if total_damage > 0:
        apply_damage(actor, total_damage, accessor)

    # Remove expired conditions
    for name in expired:
        del conditions[name]

    # Update actor
    accessor.update(actor, {'properties.conditions': conditions})
```

**No Global Turn Counter:**
- Conditions track their own remaining duration
- No need for `game_state.turn_number`
- If author needs global turn count for other purposes, they add it themselves

**Turn Progression Calls progress_conditions():**
```python
def end_turn(state, accessor):
    """Called after player command succeeds."""
    # 1. NPC actions
    process_npc_actions(state, accessor)

    # 2. Environmental effects
    for actor in get_all_actors(state):
        apply_environmental_effects(actor, state, accessor)

    # 3. Condition progression
    for actor in get_all_actors(state):
        progress_conditions(actor, accessor)

    # 4. Death/incapacitation check
    for actor in get_all_actors(state):
        check_incapacitation(actor, accessor)
```

**Rationale:**
- Self-contained duration tracking is simpler
- No global state to maintain
- Each condition knows when it expires
- Progression is explicit, not automatic

**Implications:**
- Core provides `progress_conditions()` utility
- Called during turn progression (after NPCs, after environment)
- Authors don't manually decrement durations
- Expired conditions fire `on_condition_expired` event

---

## 44. Death Check: After All Turn Effects Resolve

**Decision (Clarification of Decision 3):** Death/incapacitation checks happen AFTER all turn effects (NPC actions, environmental effects, condition progression). This ensures all actions resolve before state cleanup.

**Complete Turn Sequence:**
```
1. Player command executes
2. If successful:
   a. NPC actions phase
      - Each NPC takes action (random/deterministic order)
      - NPCs can attack, move, use abilities
      - Damage applied but no death removal yet
   b. Environmental effects phase
      - Check breathable, apply hazard conditions
      - Breath depletion, hazard damage applied
   c. Condition progression phase
      - progress_conditions() for each actor
      - Per-turn damage applied, durations decremented
      - Expired conditions removed
   d. Death/incapacitation phase
      - Check all actors for health <= 0
      - Invoke on_death behaviors
      - Remove dead actors (if behavior does so)
   e. Narration phase
      - Collect all events from phases a-d
      - Generate cohesive narrative
3. Return result to player
```

**Why Death Check Is Last:**

*Simpler Implementation:*
- No mid-turn actor removal
- All effects can reference all actors
- No "is this actor still alive?" checks during turn

*Fairer Gameplay:*
- Mutual kills are possible (both combatants die)
- Poison finishing off NPC still lets NPC attack first
- No ordering advantage for death

*Better Narration:*
- "The wolf bites you as the poison takes its toll, and you both collapse."
- All events available for narrative synthesis

**Death Check Implementation:**
```python
def check_incapacitation(actor, accessor):
    """Check if actor should die/be incapacitated."""
    health = actor.properties.get('health')
    if health is None or health > 0:
        return  # No health property or still alive

    # Health <= 0: invoke on_death behavior
    behavior = get_behavior(actor, 'on_death')
    if behavior:
        behavior(actor, accessor, {})
    # If no on_death behavior, actor remains at 0 health (incapacitated)
```

**Mutual Kill Example:**
```
Turn sequence:
1. Player attacks wolf, wolf health → 0 (not removed yet)
2. Wolf attacks player (still in NPC list), player health → 0
3. Poison on both ticks (no additional damage needed)
4. Death check: both have health <= 0
5. Both on_death behaviors fire
6. Narration: "You strike the wolf down, but its final bite proves fatal..."
```

**Rationale:**
- Clean separation of effect resolution and state cleanup
- All actors get their full turn
- Enables dramatic mutual destruction scenarios
- Simpler code - no mid-turn removal handling

**Implications:**
- on_death behaviors may fire for multiple actors in same turn
- Dead actors can deal damage on their final turn
- Removal happens at end of turn, not immediately on 0 health
- Narration has complete picture of turn events

---

## 45. Testing: TDD with Unit, Integration, and Scenario Tests

**Decision:** Actor interaction systems are developed using TDD. Tests use unittest (per project conventions). Testing is organized into unit tests (utilities), integration tests (turn flow), and scenario tests (use case verification).

**Test Organization:**
```
tests/
  test_conditions.py       # Unit: condition utilities
  test_damage.py           # Unit: damage calculation
  test_turn_progression.py # Integration: full turn flow
  test_combat_scenarios.py # Integration: combat use cases
  test_service_scenarios.py # Integration: service use cases
  fixtures/
    test_actors.py         # Reusable actor definitions
    test_items.py          # Reusable item definitions
    test_locations.py      # Reusable location/part definitions
```

**Unit Test Examples:**
```python
class TestConditionManagement(unittest.TestCase):
    """Unit tests for condition utilities."""

    def test_add_condition_creates_entry(self):
        """Adding condition creates entry in conditions dict."""
        actor = create_test_actor()
        add_condition(actor, 'poison', {'severity': 40, 'duration': 10}, accessor)
        self.assertIn('poison', actor.properties['conditions'])

    def test_same_condition_replaces(self):
        """Adding same condition type replaces previous instance."""
        actor = create_test_actor(conditions={'poison': {'severity': 40}})
        add_condition(actor, 'poison', {'severity': 20}, accessor)
        self.assertEqual(actor.properties['conditions']['poison']['severity'], 20)

    def test_progress_decrements_duration(self):
        """progress_conditions reduces duration by 1."""
        actor = create_test_actor(conditions={'poison': {'duration': 10}})
        progress_conditions(actor, accessor)
        self.assertEqual(actor.properties['conditions']['poison']['duration'], 9)

    def test_expired_condition_removed(self):
        """Condition with duration 1 is removed after progression."""
        actor = create_test_actor(conditions={'poison': {'duration': 1}})
        progress_conditions(actor, accessor)
        self.assertNotIn('poison', actor.properties['conditions'])


class TestDamageCalculation(unittest.TestCase):
    """Unit tests for damage utilities."""

    def test_damage_minus_armor(self):
        """Damage reduced by armor value."""
        actor = create_test_actor(health=100, armor=20)
        apply_damage(actor, 30, accessor)
        self.assertEqual(actor.properties['health'], 90)  # 30 - 20 = 10 damage

    def test_armor_blocks_weak_attack(self):
        """Armor can completely block weak attacks."""
        actor = create_test_actor(health=100, armor=20)
        apply_damage(actor, 15, accessor)
        self.assertEqual(actor.properties['health'], 100)  # 15 - 20 = 0 damage

    def test_immunity_blocks_condition(self):
        """Immune actor doesn't receive condition."""
        actor = create_test_actor(immunities=['poison'])
        result = apply_condition_with_immunity_check(actor, 'poison', {}, accessor)
        self.assertFalse(result)
        self.assertNotIn('poison', actor.properties.get('conditions', {}))
```

**Integration Test Examples:**
```python
class TestTurnProgression(unittest.TestCase):
    """Integration tests for turn flow."""

    def test_npc_acts_after_player_command(self):
        """NPC takes action after successful player command."""
        state = create_test_state_with_hostile_npc()
        player_health_before = state.player.properties['health']

        execute_command('wait', state)  # Successful command

        # NPC should have attacked
        self.assertLess(state.player.properties['health'], player_health_before)

    def test_conditions_progress_after_npc_actions(self):
        """Condition duration decrements after turn."""
        state = create_test_state()
        add_condition(state.player, 'poison', {'duration': 5}, accessor)

        execute_command('wait', state)

        self.assertEqual(
            state.player.properties['conditions']['poison']['duration'],
            4
        )

    def test_death_check_after_all_effects(self):
        """Death check happens after all effects resolve."""
        # Setup: NPC at 1 health, player poisoned
        state = create_test_state()
        state.npc.properties['health'] = 1
        add_condition(state.player, 'poison', {'damage_per_turn': 100}, accessor)

        # Player kills NPC, but poison will kill player
        execute_command('attack npc', state)

        # Both should be dead (mutual kill)
        self.assertLessEqual(state.npc.properties['health'], 0)
        self.assertLessEqual(state.player.properties['health'], 0)
```

**Scenario Test Examples:**
```python
class TestPoisonScenario(unittest.TestCase):
    """Scenario: Use Case 1 - Infected Scholar."""

    def test_antidote_cures_poison(self):
        """Giving antidote to poisoned NPC cures them."""
        state = create_infected_scholar_scenario()
        scholar = state.get_entity('npc_scholar')
        self.assertIn('fungal_infection', scholar.properties['conditions'])

        execute_command('give silvermoss to scholar', state)

        self.assertNotIn('fungal_infection', scholar.properties['conditions'])

    def test_poison_damages_over_time(self):
        """Poison deals damage each turn."""
        state = create_infected_scholar_scenario()
        scholar = state.get_entity('npc_scholar')
        health_before = scholar.properties['health']

        execute_command('wait', state)  # One turn passes

        expected_damage = scholar.properties['conditions']['fungal_infection']['damage_per_turn']
        self.assertEqual(
            scholar.properties['health'],
            health_before - expected_damage
        )
```

**Test Fixtures:**
```python
# fixtures/test_actors.py
def create_test_actor(**overrides):
    """Create actor with sensible defaults, overridable."""
    defaults = {
        'id': 'test_actor',
        'name': 'Test Actor',
        'properties': {
            'health': 100,
            'max_health': 100,
            'armor': 0,
            'conditions': {},
            'immunities': [],
            'attacks': [{'name': 'punch', 'damage': 10}]
        }
    }
    # Apply overrides
    for key, value in overrides.items():
        if key in defaults['properties']:
            defaults['properties'][key] = value
        else:
            defaults[key] = value
    return Entity(**defaults)
```

**Rationale:**
- TDD ensures testable, modular design
- Unit tests verify utilities in isolation
- Integration tests verify systems work together
- Scenario tests verify use cases are achievable
- Fixtures reduce boilerplate and ensure consistency

**Implications:**
- Write tests before implementing each utility
- Run tests after each change
- Aim for 80% coverage on new code
- Use deterministic mode for reproducible integration tests

---

## Summary of Decisions

| # | Decision | Type |
|---|----------|------|
| 1 | Actor interaction framework in core | Architecture |
| 2 | First-class event integration | Architecture |
| 3 | NPCs act after player commands | Timing |
| 4 | Every command is a turn | Timing |
| 5 | Full serialization of temporal state | Save/Load |
| 6 | Core provides infrastructure, authors provide strategy | Boundary |
| 7 | Start with no defaults, evolve toward convenience | Scope |
| 8 | Property schemas are conventions, not requirements | Flexibility |
| 9 | Deterministic outcomes by default | Game Mechanics |
| 10 | Conditions stored as dict, explicit progression | Core Systems |
| 11 | Same condition replaces, different conditions coexist | Core Systems |
| 12 | Cures remove condition entirely | Core Systems |
| 13 | Damage = attack - armor, minimum 0 | Core Systems |
| 14 | Armor is flat damage reduction | Core Systems |
| 15 | Authors implement NPC AI via behaviors | Core Systems |
| 16 | Environmental hazards automatic, bonuses opt-in | Environment |
| 17 | Breath optional property, automatic depletion | Environment |
| 18 | Core provides attack command, authors add others | Commands |
| 19 | on_death behavior determines consequences | Game Mechanics |
| 20 | Immunities binary, resistances author-optional | Game Mechanics |
| 21 | Damage modification in behaviors, core provides utility | Core Systems |
| 22 | Armor property only, author sets value | Core Systems |
| 23 | Morale properties only, authors implement logic | AI/Strategy |
| 24 | Pack properties only, authors implement logic | AI/Strategy |
| 25 | Event types dynamically discovered via registry | Architecture |
| 26 | Environmental constants in metadata, not hardcoded | Environment |
| 27 | Environmental bonuses are conventions, not enforced | Environment |
| 28 | Cover mechanics author-implemented via properties | Environment |
| 29 | Core provides attack, defend, guide, activate commands | Commands |
| 30 | Range is property only, authors implement selection | Combat |
| 31 | Area attacks entirely author-implemented | Combat |
| 32 | Immunities block conditions, resistances reduce damage only | Combat |
| 33 | Weaknesses are damage multipliers, author-implemented | Combat |
| 34 | NPC movement is author-implemented in behaviors | AI/Movement |
| 35 | Activation triggers via observer or event patterns | AI/Triggers |
| 36 | Fleeing is author-implemented movement | AI/Movement |
| 37 | Pack coordination scales via cheap checks | AI/Performance |
| 38 | Behaviors can fire events without commands | Architecture |
| 39 | Services triggered via give, resolved in on_receive | Services |
| 40 | Binary knowledge array, no skill levels | Knowledge |
| 41 | Relationships stored on actor, threshold-based effects | Social |
| 42 | Deterministic mechanics, random event ordering | Randomness |
| 43 | Condition duration managed by progress_conditions() | Core Systems |
| 44 | Death check after all turn effects resolve | Timing |
| 45 | TDD with unit, integration, and scenario tests | Testing |
| 46 | Phase 1 MVP: utilities, turn progression, environment, commands | Scope |
| 47 | Implementation phasing in separate design document | Scope |
| 48 | Graceful degradation for actors without combat properties | Compatibility |

---

## 46. Phase 1 MVP: Core Utilities, Turn Progression, Environment, Commands

**Decision:** Phase 1 implements the minimal viable combat system. This includes core utilities, turn progression, environmental effects, and core commands. Morale, pack coordination, services, relationships, and knowledge are patterns only (no core utilities).

**Phase 1 Includes (Core Infrastructure):**

*Core Utilities:*
- `apply_damage(actor, amount, accessor)` - reduces health by damage minus armor
- `add_condition(actor, name, props, accessor)` - adds/replaces condition
- `remove_condition(actor, name, accessor)` - removes condition
- `progress_conditions(actor, accessor)` - tick durations, apply per-turn damage
- `check_immunity(actor, condition_type)` - returns bool
- `check_incapacitation(actor, accessor)` - invokes on_death if health <= 0

*Turn Progression:*
- `end_turn(state, accessor)` - orchestrates post-command processing
- `process_npc_actions(state, accessor)` - invokes NPC behaviors (random order)
- Integration with command handlers

*Environmental Effects:*
- `apply_environmental_effects(actor, state, accessor)` - hazards, breath
- Breath depletion in non-breathable locations
- Hazard condition application from location properties

*Core Commands:*
- `attack <target>` - basic combat command
- `defend` - defensive posture
- `guide <actor>` - escort NPC
- `activate <object>` - trigger mechanisms

*Event Infrastructure:*
- `accessor.fire_event()` available from behavior context
- Event registry for dynamic event type discovery

**Phase 1 Excludes (Patterns Only, No Core Code):**

| Feature | Why Excluded | How It Works |
|---------|--------------|--------------|
| Morale | Decision 23: properties only | Authors check `ai.morale` in behaviors |
| Pack coordination | Decision 24: properties only | Authors check `pack_id`, `follows_alpha` |
| Services | Decision 39: pattern only | Authors implement in `on_receive` |
| Relationships | Decision 41: pattern only | Authors store in `relationships` property |
| Knowledge | Decision 40: pattern only | Authors check `knows` array |
| Resistances | Decision 20: author-optional | Authors implement in `on_damage` |
| Weaknesses | Decision 33: author-implemented | Authors implement in `on_damage` |
| Area attacks | Decision 31: author-implemented | Authors loop over targets |

**Why This Scope:**
- Core utilities enable all use cases
- Excluded features work via properties + behaviors
- No core code needed for excluded features
- Authors can implement any excluded feature immediately using patterns
- Keeps Phase 1 focused and testable

**Rationale:**
- Minimum infrastructure that enables maximum gameplay
- Property-based features don't need core utilities
- Authors have full capability from day one
- Clean separation: core provides mechanics, authors provide strategy

**Implications:**
- Phase 1 is self-contained and useful
- All 8 use cases are achievable with Phase 1 + author behaviors
- Future phases add convenience, not capability
- Documentation for excluded patterns ships with Phase 1

---

## 47. Implementation Phasing: Separate Design Document

**Decision:** Detailed implementation phasing (sub-phases, ordering, dependencies) will be specified in a separate implementation design document, not in this conceptual design decisions document.

**What This Document Contains:**
- Architectural decisions (what to build)
- Property conventions (how to structure data)
- Behavior patterns (how authors implement features)
- Core/author boundary (what core provides vs. what authors implement)

**What Implementation Document Will Contain:**
- Sub-phase breakdown (1a, 1b, 1c, etc.)
- Implementation order and dependencies
- Specific file/module organization
- Test file structure
- API signatures
- Migration considerations

**Why Separate:**
- This document captures design decisions that are stable
- Implementation details may change during development
- Keeps this document focused on "what" not "how"
- Implementation document can be revised without changing design decisions

**Rationale:**
- Separation of concerns between design and implementation
- Design decisions are reviewed and approved before implementation planning
- Implementation planning can reference stable design decisions
- Easier to maintain both documents

**Implications:**
- Create implementation design document before starting Phase 1 coding
- Implementation document references decisions by number
- Changes to implementation don't require design document updates
- Design document serves as stable reference during implementation

---

## 48. Backward Compatibility: Graceful Degradation

**Decision:** Actors without combat properties are non-combatants. Utilities handle missing properties gracefully. No forced migration of existing game data.

**Graceful Degradation Rules:**

| Property | If Missing | Behavior |
|----------|------------|----------|
| `health` | None | Actor cannot be damaged or killed |
| `max_health` | None | No health cap enforced |
| `attacks` | [] or None | Actor cannot attack |
| `armor` | 0 | No damage reduction |
| `conditions` | {} | No active conditions (can receive them) |
| `immunities` | [] | No immunities |
| `resistances` | {} | No resistances |
| `breath` | None | Actor doesn't need air |
| `max_breath` | None | No breath cap |
| `ai` | {} | Actor has no AI behaviors |
| `ai.hostile` | False | Actor doesn't initiate attacks |

**Utility Implementation Pattern:**
```python
def apply_damage(actor, amount, accessor):
    """Gracefully handle actors without health."""
    health = actor.properties.get('health')
    if health is None:
        # Actor has no health property - damage has no effect
        # Could fire event for narration: "The attack has no effect on {actor.name}"
        return DamageResult(applied=False, reason='no_health_property')

    armor = actor.properties.get('armor', 0)
    actual_damage = max(0, amount - armor)
    new_health = health - actual_damage
    accessor.update(actor, {'properties.health': new_health})
    return DamageResult(applied=True, damage=actual_damage)
```

**No Forced Migration:**
- Existing actors continue working
- Authors add combat properties only where needed
- Save files from before actor interaction still load
- Non-combat NPCs (shopkeepers, quest givers) don't need health

**Save Format Changes:**
Per project CLAUDE.md: If save format changes incompatibly, create separate migration tool rather than backward compatibility code in engine.

**Non-Combatant Examples:**
- Shopkeeper NPC: has `services` but no `health` or `attacks`
- Quest giver: has `relationships` but no combat properties
- Furniture: no actor properties at all
- Environmental hazard: has `applies_condition` but isn't an actor

**Rationale:**
- Existing games continue working without modification
- Combat is opt-in per actor
- Cleaner design - actors are combatants only if they have combat properties
- No bloat from default values on non-combat entities

**Implications:**
- Utilities check for property existence before use
- Missing property = feature not applicable to this actor
- Authors decide which actors participate in combat
- Documentation clarifies which properties enable which features

---

## Summary of Decisions

| # | Decision | Type |
|---|----------|------|
| 1 | Actor interaction framework in core | Architecture |
| 2 | First-class event integration | Architecture |
| 3 | NPCs act after player commands | Timing |
| 4 | Every command is a turn | Timing |
| 5 | Full serialization of temporal state | Save/Load |
| 6 | Core provides infrastructure, authors provide strategy | Boundary |
| 7 | Start with no defaults, evolve toward convenience | Scope |
| 8 | Property schemas are conventions, not requirements | Flexibility |
| 9 | Deterministic outcomes by default | Game Mechanics |
| 10 | Conditions stored as dict, explicit progression | Core Systems |
| 11 | Same condition replaces, different conditions coexist | Core Systems |
| 12 | Cures remove condition entirely | Core Systems |
| 13 | Damage = attack - armor, minimum 0 | Core Systems |
| 14 | Armor is flat damage reduction | Core Systems |
| 15 | Authors implement NPC AI via behaviors | Core Systems |
| 16 | Environmental hazards automatic, bonuses opt-in | Environment |
| 17 | Breath optional property, automatic depletion | Environment |
| 18 | Core provides attack command, authors add others | Commands |
| 19 | on_death behavior determines consequences | Game Mechanics |
| 20 | Immunities binary, resistances author-optional | Game Mechanics |
| 21 | Damage modification in behaviors, core provides utility | Core Systems |
| 22 | Armor property only, author sets value | Core Systems |
| 23 | Morale properties only, authors implement logic | AI/Strategy |
| 24 | Pack properties only, authors implement logic | AI/Strategy |
| 25 | Event types dynamically discovered via registry | Architecture |
| 26 | Environmental constants in metadata, not hardcoded | Environment |
| 27 | Environmental bonuses are conventions, not enforced | Environment |
| 28 | Cover mechanics author-implemented via properties | Environment |
| 29 | Core provides attack, defend, guide, activate commands | Commands |
| 30 | Range is property only, authors implement selection | Combat |
| 31 | Area attacks entirely author-implemented | Combat |
| 32 | Immunities block conditions, resistances reduce damage only | Combat |
| 33 | Weaknesses are damage multipliers, author-implemented | Combat |
| 34 | NPC movement is author-implemented in behaviors | AI/Movement |
| 35 | Activation triggers via observer or event patterns | AI/Triggers |
| 36 | Fleeing is author-implemented movement | AI/Movement |
| 37 | Pack coordination scales via cheap checks | AI/Performance |
| 38 | Behaviors can fire events without commands | Architecture |
| 39 | Services triggered via give, resolved in on_receive | Services |
| 40 | Binary knowledge array, no skill levels | Knowledge |
| 41 | Relationships stored on actor, threshold-based effects | Social |
| 42 | Deterministic mechanics, random event ordering | Randomness |
| 43 | Condition duration managed by progress_conditions() | Core Systems |
| 44 | Death check after all turn effects resolve | Timing |
| 45 | TDD with unit, integration, and scenario tests | Testing |
| 46 | Phase 1 MVP: utilities, turn progression, environment, commands | Scope |
| 47 | Implementation phasing in separate design document | Scope |
| 48 | Graceful degradation for actors without combat properties | Compatibility |

---

## Next Steps

With all design questions resolved, we can now:
1. Create implementation design document with detailed phasing
2. Finalize property schema documentation
3. Begin Phase 1 implementation using TDD
