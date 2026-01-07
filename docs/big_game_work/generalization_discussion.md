# Reaction System Generalization - Design Discussion Summary

**Date:** 2026-01-06
**Status:** Design Complete, Implementation Pending
**Related:** [reaction_system_design.md](reaction_system_design.md)

---

## Context

During the design phase for the unified reaction system, we identified that the initial mini-language specification contained game-specific primitives that would limit reusability. This document captures the discussion and decisions that led to the generalized property-based architecture.

---

## The Problem

The initial unified interpreter design (in `unified_reaction_interpreter.md`, now merged into `reaction_system_design.md`) included effect primitives that were too specific to Big Game mechanics:

**Game-Specific Primitives:**
- `requires_trust?: int` - Check trust threshold
- `trust_delta?: int` - Modify trust value
- `trust_transitions?: {level: state}` - Trust-based state transitions
- `heal_amount?: int` - Restore health
- `apply_damage?: int` - Deal damage
- `grant_knowledge?: string[]` - Add knowledge items
- `create_commitment?: string` - Create commitment
- `fulfill_commitment?: string` - Complete commitment
- `create_gossip?: GossipSpec` - Propagate gossip

**Why This Was Problematic:**
1. Encoded Big Game domain concepts (trust, gossip, commitments) as language primitives
2. Required new primitives for each new game mechanic
3. Couldn't support other games with different mechanics (reputation, sanity, fame, etc.)
4. Missing general mechanism for similar features (e.g., health wasn't included)
5. No way to extend without modifying the core interpreter

---

## The Generalization Request

**User's Analysis:**
> "Most of grammar items are fine, but some I hope we can generalize. The ones I want to consider now refer to specific design features of big_game that might not be relevant to other games. Conversely there's no general mechanism to include similar features that might appear in other games."

**Key Insight:**
> "We still need to provide all these functions, but I hope the specific operations can be generalized to be basically 'modify <property> by <amount>', 'require <property> at least <amount>' and other checks like that."

**Goal:** Create a game-agnostic core that can support ANY game's mechanics through property manipulation, while preserving authoring ergonomics for Big Game.

---

## The Solution: Three-Tier Architecture

### Tier 1: Universal Primitives (Game-Agnostic Core)

These primitives work for ANY game with numeric properties, collections, or state:

#### Property Conditions
```yaml
require_property?: PropertyCondition | PropertyCondition[]

PropertyCondition:
  path: string           # Dot-notation: "trust_state.current", "health", "sanity"
  min?: number          # Value >= min
  max?: number          # Value <= max
  equals?: any          # Exact match
  in?: any[]            # Value in list
  not_equals?: any      # Not equal
  not_in?: any[]        # Not in list
```

**Examples:**
```yaml
# Check trust (Big Game)
require_property:
  path: "trust_state.current"
  min: 3

# Check sanity (Horror Game)
require_property:
  path: "sanity"
  min: 50

# Check reputation (RPG)
require_property:
  path: "faction_reputation.thieves_guild"
  min: 100
```

#### Property Modification
```yaml
modify_property?: PropertyMod | PropertyMod[]

PropertyMod:
  path: string          # Dot-notation property path
  set?: any            # Set to absolute value
  delta?: number       # Add/subtract (numeric)
  multiply?: number    # Multiply by factor
  append?: any[]       # Append to list/set
  remove?: any[]       # Remove from list/set
  merge?: dict         # Deep merge dictionary
```

**Examples:**
```yaml
# Increase trust by 2 (Big Game)
modify_property:
  path: "trust_state.current"
  delta: 2

# Restore 20 health (any game)
modify_property:
  path: "health"
  delta: 20

# Add knowledge item (Big Game)
modify_property:
  path: "knowledge"
  append: "bear_behavior"

# Decrease sanity by 10 (Horror Game)
modify_property:
  path: "sanity"
  delta: -10
```

#### Property Transitions
```yaml
property_transitions?: PropertyTransitions

PropertyTransitions:
  path: string          # Property to monitor
  thresholds:
    {number}: string    # threshold: target_state
```

**Examples:**
```yaml
# Trust-based state transitions (Big Game)
property_transitions:
  path: "trust_state.current"
  thresholds:
    1: "wary"
    3: "friendly"
    5: "allied"

# Sanity-based state transitions (Horror Game)
property_transitions:
  path: "sanity"
  thresholds:
    25: "paranoid"
    10: "delusional"
    0: "insane"
```

#### Collection Operations
```yaml
add_to_collection?: CollectionOp | CollectionOp[]
remove_from_collection?: CollectionOp | CollectionOp[]

CollectionOp:
  path: string              # Path in game_state.extra
  value?: any              # Explicit value
  from_context?: string    # Get from context
```

**Examples:**
```yaml
# Track defeated bosses
add_to_collection:
  path: "defeated_bosses"
  value: "dragon_king"

# Track visited locations
add_to_collection:
  path: "visited_locations"
  from_context: "current_location"
```

#### System Integration
```yaml
invoke_system?: SystemInvocation | SystemInvocation[]

SystemInvocation:
  system: string        # "commitment", "gossip", "quest", etc.
  action: string        # "create", "fulfill", "abandon", etc.
  params: dict          # System-specific parameters
```

**Examples:**
```yaml
# Create commitment (Big Game)
invoke_system:
  system: "commitment"
  action: "create"
  params:
    commitment_id: "rescue_sira"
    deadline_turns: 20

# Create quest (RPG)
invoke_system:
  system: "quest"
  action: "start"
  params:
    quest_id: "dragon_slayer"

# Propagate gossip (Big Game)
invoke_system:
  system: "gossip"
  action: "create"
  params:
    gossip_type: "sira_rescue"
    source: "hunter_sira"
    targets: ["elara"]
```

### Tier 2: Convenience Sugar (Compiles to Tier 1)

Common patterns given readable names that compile to Tier 1 at load time:

```yaml
# Convenience conditions
requires_trust?: int          → require_property: {path: "trust_state.current", min: N}
requires_flags?: {flag: val}  → require_property: {path: "extra.{flag}", equals: val}
requires_state?: string[]     → require_property: {path: "state_machine.current", in: states}
requires_items?: string[]     → Check player inventory

# Convenience effects
trust_delta?: int             → modify_property: {path: "trust_state.current", delta: N}
trust_transitions?: {N: S}    → property_transitions: {path: "trust_state.current", ...}
set_flags?: {flag: value}     → modify_property: {path: "extra.{flag}", set: value}
transition_to?: string        → modify_property: {path: "state_machine.current", set: state}
```

**Authoring Benefit:** Big Game authors can write concise, readable configs:

```yaml
# Concise (Tier 2):
gift_reactions:
  food:
    accepted_items: ["venison", "meat"]
    requires_trust: 2
    trust_delta: 1
    trust_transitions:
      3: "friendly"
      5: "allied"

# Equivalent verbose (Tier 1):
gift_reactions:
  food:
    accepted_items: ["venison", "meat"]
    require_property:
      path: "trust_state.current"
      min: 2
    modify_property:
      path: "trust_state.current"
      delta: 1
    property_transitions:
      path: "trust_state.current"
      thresholds:
        3: "friendly"
        5: "allied"
```

### Tier 3: Common Operations (Universal Enough to Keep)

Operations common across many game types, kept as top-level primitives:

```yaml
# Inventory management (universal)
grant_items?: string[]        # Add items to player
spawn_items?: string[]        # Create items in world
consume_item?: bool          # Remove item from player

# Status effects (if game uses them)
apply_condition?: ConditionSpec
remove_condition?: string
```

---

## Migration Examples

### Example 1: Trust-Based Feeding (Alpha Wolf)

**OLD (game-specific primitives):**
```json
{
  "gift_reactions": {
    "food": {
      "accepted_items": ["venison", "meat"],
      "requires_trust": 0,
      "trust_delta": 1,
      "trust_transitions": {
        "1": "wary",
        "3": "friendly",
        "5": "allied"
      },
      "grant_items_at": {
        "allied": ["alpha_fang_fragment"]
      }
    }
  }
}
```

**NEW (generalized, using Tier 2 sugar):**
```json
{
  "gift_reactions": {
    "food": {
      "accepted_items": ["venison", "meat"],
      "requires_trust": 0,
      "trust_delta": 1,
      "trust_transitions": {
        "1": "wary",
        "3": "friendly",
        "5": "allied"
      },
      "grant_items": ["alpha_fang_fragment"],
      "requires_state": ["allied"]
    }
  }
}
```

**NEW (generalized, pure Tier 1):**
```json
{
  "gift_reactions": {
    "food": {
      "accepted_items": ["venison", "meat"],
      "require_property": {
        "path": "trust_state.current",
        "min": 0
      },
      "modify_property": {
        "path": "trust_state.current",
        "delta": 1
      },
      "property_transitions": {
        "path": "trust_state.current",
        "thresholds": {
          "1": "wary",
          "3": "friendly",
          "5": "allied"
        }
      },
      "grant_items": ["alpha_fang_fragment"],
      "require_property": {
        "path": "state_machine.current",
        "equals": "allied"
      }
    }
  }
}
```

### Example 2: Health/Damage System

**OLD (missing from initial design):**
```yaml
# No way to represent generic health without creating new primitives
```

**NEW (universal property manipulation):**
```yaml
# Deal 10 damage
modify_property:
  path: "health"
  delta: -10

# Heal 20 health
modify_property:
  path: "health"
  delta: 20

# Death transition at 0 health
property_transitions:
  path: "health"
  thresholds:
    0: "dead"
```

### Example 3: Commitment System

**OLD (game-specific primitive):**
```yaml
create_commitment?: string
fulfill_commitment?: string
```

**NEW (generic system invocation):**
```yaml
# Create commitment
invoke_system:
  system: "commitment"
  action: "create"
  params:
    commitment_id: "rescue_sira"
    deadline_turns: 20

# Fulfill commitment
invoke_system:
  system: "commitment"
  action: "fulfill"
  params:
    commitment_id: "rescue_sira"
```

### Example 4: Knowledge/Learning System

**OLD (game-specific primitive):**
```yaml
grant_knowledge?: string[]
```

**NEW (property modification):**
```yaml
# Add to knowledge list
modify_property:
  path: "knowledge"
  append: ["bear_behavior", "wolf_tactics"]

# Or using convenience sugar:
grant_knowledge: ["bear_behavior", "wolf_tactics"]
# (compiles to modify_property at load time)
```

---

## Benefits of Generalization

### 1. Game-Agnostic Engine
Any game can use the core interpreter:
- **Big Game:** Trust, gossip, commitments, knowledge
- **Horror Game:** Sanity, fear, hallucinations, trauma
- **RPG:** Reputation, fame, faction standing, quest states
- **Survival Game:** Hunger, thirst, temperature, exhaustion

### 2. No Engine Modifications Required
Adding new game mechanics doesn't require:
- New interpreter primitives
- Core engine changes
- Recompiling infrastructure modules

Just define properties and use `modify_property`/`require_property`.

### 3. Preserved Authoring Ergonomics
Tier 2 convenience sugar means Big Game authors can continue using readable names like `trust_delta` instead of verbose property paths.

### 4. Extensible Without Bloat
Games can define their own Tier 2 sugar that compiles to Tier 1:

```python
# Custom sugar for horror game
HORROR_SUGAR = {
    "sanity_delta": lambda v: {"modify_property": {"path": "sanity", "delta": v}},
    "requires_sanity": lambda v: {"require_property": {"path": "sanity", "min": v}},
    "fear_delta": lambda v: {"modify_property": {"path": "fear", "delta": v}}
}
```

### 5. Clear Migration Path
Existing Big Game configs using Tier 2 sugar continue to work unchanged. The interpreter expands sugar to Tier 1 at load time, so internal execution is always consistent.

---

## Implementation Notes

### Load-Time Compilation
The interpreter processes configs at game load:

```python
def compile_sugar_to_primitives(config: dict) -> dict:
    """Expand Tier 2 convenience sugar to Tier 1 primitives."""
    compiled = {}

    # Expand trust_delta
    if "trust_delta" in config:
        compiled["modify_property"] = compiled.get("modify_property", [])
        compiled["modify_property"].append({
            "path": "trust_state.current",
            "delta": config["trust_delta"]
        })

    # Expand requires_trust
    if "requires_trust" in config:
        compiled["require_property"] = compiled.get("require_property", [])
        compiled["require_property"].append({
            "path": "trust_state.current",
            "min": config["requires_trust"]
        })

    # ... expand other sugar ...

    return {**config, **compiled}
```

### Validation
All property paths validated at load time:

```python
def validate_property_path(entity: Entity, path: str):
    """Ensure property path exists and is accessible."""
    parts = path.split(".")
    current = entity.properties

    for part in parts:
        if not isinstance(current, dict):
            raise ValidationError(f"Invalid path '{path}': {part} not accessible")
        if part not in current:
            warnings.warn(f"Property path '{path}' does not exist on entity")
        current = current.get(part)
```

### Documentation Generation
Property usage can be automatically documented:

```bash
$ python tools/property_usage.py trust_state.current

Property: trust_state.current
Type: numeric (floor: -5, ceiling: 5)

Used by (8 entities):
  - alpha_wolf: gift_reactions (delta: +1), transitions at 1/3/5
  - dire_bear: item_use_reactions (delta: +3), floor set on failure
  - salamander: gift_reactions (delta: +2), transitions at 2/4
  - bee_queen: gift_reactions (delta: +1), transitions at 3/5
  - hunter_sira: dialog_reactions (checked >= 2)
  ...

Common patterns:
  - Gift acceptance increases by 1-3
  - State transitions at thresholds: 1 (wary), 3 (friendly), 5 (allied)
  - Floor typically -5, ceiling 5
```

---

## Design Philosophy

**Core Abstraction:**
> Game mechanics are fundamentally about manipulating properties based on conditions. Whether it's trust, sanity, health, or reputation - all are just numeric or list-valued properties that change in response to player actions.

**Key Principles:**

1. **Universal Core:** The interpreter knows nothing about trust, gossip, or commitments. It only knows how to read/write properties and call systems.

2. **Convenience Layer:** Authors shouldn't write verbose property paths for every common operation. Sugar provides ergonomics without limiting power.

3. **Escape Hatch Preserved:** When mini-language isn't sufficient, handlers provide full programmatic control.

4. **Fail Loud:** Invalid property paths, missing systems, bad configurations - all detected at load time, not during gameplay.

5. **Composability:** Effects combine naturally. `modify_property` + `property_transitions` + `invoke_system` can handle arbitrarily complex reactions.

---

## Status: Design Complete

**Approval:** "Excellent generalization. Make these changes to the design document"

**Next Steps:**
1. Inventory existing handlers across all regions
2. Map handlers to 12 reaction types
3. Plan implementation phases
4. Build infrastructure modules using generalized design
5. Migrate existing handlers

**Related Documents:**
- [reaction_system_design.md](reaction_system_design.md) - Complete unified design
- [reaction_system_architecture.md](reaction_system_architecture.md) - Original architecture (superseded, can be deleted)
- [unified_reaction_interpreter.md](unified_reaction_interpreter.md) - Original interpreter design (superseded, can be deleted)
