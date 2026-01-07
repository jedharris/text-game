# Reaction System Design: Property-Based Architecture with Unified Interpreter

**Status:** Complete Design Specification
**Date:** 2026-01-06
**Purpose:** Define comprehensive reaction system to replace mixed vocabulary/property approaches

---

## Table of Contents

1. [Architecture Decision](#architecture-decision)
2. [Unified Mini-Language](#unified-mini-language)
3. [Interpreter Implementation](#interpreter-implementation)
4. [Reaction Type Specifications](#reaction-type-specifications)
5. [Validation System](#validation-system)
6. [Discoverability Tooling](#discoverability-tooling)
7. [Migration Strategy](#migration-strategy)
8. [Testing Strategy](#testing-strategy)

---

# Part 1: Architecture Decision

## Core Principle

**Local dispatch via entity properties with unified interpreter execution**

Entity properties declare reactions → Infrastructure finds matching reaction → Unified interpreter executes configuration → Only relevant handler/config executes (O(1) dispatch).

## The Problem

Current game has two conflicting patterns:

**Approach A (Property-Based):** Entity properties in JSON point to handlers
- ✅ O(1) dispatch - only relevant entity checked
- ✅ Clear ownership - reaction belongs to entity
- ❌ Discoverability - need tooling to find what entities do
- ❌ Type safety - handler paths are strings, validated at runtime

**Approach B (Vocabulary Events):** Behavior modules declare events that broadcast
- ✅ Easy to find - grep for event name shows all handlers
- ✅ Type safety - Python imports catch missing modules
- ❌ O(n) dispatch - all handlers check if they apply
- ❌ Hook namespace pollution - limited hooks shared by many behaviors
- ❌ Fragile filtering - handlers use string matching like `if "wolf" in entity.id.lower()`

**Current State:** Mixed approach causes confusion and inconsistency.

## The Solution

**Property-based architecture (Approach A) + Unified interpreter + Comprehensive validation & tooling**

This combines the performance and ownership benefits of A with safety and discoverability through:
1. **Load-time validation** - All handler paths, schemas, cross-references checked at startup
2. **Unified interpreter** - Single execution model eliminates code duplication
3. **Discoverability tools** - entity_inspector, reaction_inventory, handler_usage
4. **Declarative mini-language** - Most reactions need no code, just JSON configuration

## Benefits vs. Current Approach

### Performance
- ✅ **O(1) dispatch** - Direct property lookup, no broadcasting
- ✅ **Handler caching** - First call imports, subsequent calls O(1) dict lookup
- ✅ **Scales to millions** - No O(n) iteration over entities

### Type Safety
- ✅ **Load-time handler validation** - All handler paths resolved at startup
- ✅ **Schema validation** - JSON configs validated against schemas
- ✅ **Cross-reference checks** - Verify referenced items/states/flags exist
- ✅ **Fail fast** - Invalid configs crash at load, not during gameplay

### Maintainability
- ✅ **Clear ownership** - Reaction belongs to entity in game_state.json
- ✅ **No string matching** - No `if "wolf" in entity_id.lower()` fragility
- ✅ **Single pattern** - All 12 reaction types use identical infrastructure
- ✅ **50% less code** - Unified interpreter eliminates duplication

### Discoverability
- ✅ **Entity inspector** - `entity_inspector.py alpha_wolf` shows all reactions
- ✅ **Reaction inventory** - `reaction_inventory.py --type gift` lists all entities with gift reactions
- ✅ **Handler usage** - `handler_usage.py path:function` shows which entities use handler
- ✅ **Validation tool** - `validate_game_state.py` checks entire game for issues

### Extensibility
- ✅ **Add entities without code** - Pure JSON configuration for simple cases
- ✅ **Composable effects** - Mix any effects/conditions without custom code
- ✅ **New effects benefit all** - Add effect handler once, all 12 reaction types gain it
- ✅ **Handler escape hatch** - Complex logic still possible with Python

---

# Part 2: Unified Mini-Language

## Overview

All 12 reaction types share a common declarative mini-language. Reactions are data transformations:

```
(GameState, Entity, Config) → (GameState', Feedback)
```

The mini-language has three sections:
1. **Matching** - What triggers this reaction (varies by type)
2. **Conditions** - When this reaction applies (universal)
3. **Effects** - What this reaction does (universal)

## Complete Grammar

```yaml
ReactionConfig:
  # ===== MATCHING (varies by reaction type) =====
  accepted_items?: string[]        # Items that trigger (gift, item_use, trade)
  keywords?: string[]              # Keywords that trigger (dialog)
  # Note: Some reactions have no matching (encounter, death, entry)

  # ===== CONDITIONS (universal - all must pass) =====
  # Property-based conditions (game-agnostic)
  require_property?: PropertyCondition | PropertyCondition[]

  # Convenience conditions (compile to require_property)
  requires_flags?: {flag: value}   # Convenience for extra.{key}
  requires_not_flags?: {flag: value}  # Negated flag check
  requires_state?: string[]        # Convenience for state_machine.current
  requires_trust?: int             # Convenience for trust_state.current >= value
  requires_items?: string[]        # Check player inventory

  # ===== EFFECTS (universal - applied in order) =====
  # Property manipulation (game-agnostic)
  modify_property?: PropertyMod | PropertyMod[]
  property_transitions?: PropertyTransitions

  # Collection operations (game-agnostic)
  add_to_collection?: CollectionOp | CollectionOp[]
  remove_from_collection?: CollectionOp | CollectionOp[]

  # System integration (game-specific)
  invoke_system?: SystemInvocation | SystemInvocation[]

  # Convenience effects (compile to modify_property or invoke_system)
  set_flags?: {flag: value}        # Convenience for extra.{key}
  unset_flags?: string[]           # Convenience for extra.{key}
  transition_to?: string           # Convenience for state_machine
  trust_delta?: int                # Convenience for trust_state.current
  trust_transitions?: {level: state}  # Convenience for property_transitions

  # Item/Player operations (common enough to keep)
  consume_item?: bool              # Remove item from player inventory
  grant_items?: string[]           # Add items to player inventory
  spawn_items?: string[]           # Create items in current location

  # Status conditions (game-specific but complex)
  apply_condition?: ConditionSpec  # Apply status effect to entity
  remove_condition?: string        # Remove status effect from entity

  # Deprecated convenience (compile to modify_property)
  apply_damage?: int               # DEPRECATED: use modify_property with delta: -N
  heal_amount?: int                # DEPRECATED: use modify_property with delta: N
  grant_knowledge?: string[]       # DEPRECATED: use modify_property with append
  create_commitment?: string       # DEPRECATED: use invoke_system
  fulfill_commitment?: string      # DEPRECATED: use invoke_system
  create_gossip?: GossipSpec       # DEPRECATED: use invoke_system
  track_in?: string                # DEPRECATED: use add_to_collection
  increment_counter?: string       # DEPRECATED: use modify_property

  # ===== FEEDBACK (varies by reaction type) =====
  message?: string                 # Generic message (all types)
  accept_message?: string          # Gift accepted (gift)
  reject_message?: string          # Gift rejected (gift)
  response?: string                # Response text (dialog, item_use)
  summary?: string                 # Dialog summary (dialog)
  encounter_message?: string       # First encounter (encounter)
  death_message?: string           # Death consequence (death)
  failure_message?: string         # Condition check failed (all types)

  # ===== ESCAPE HATCH =====
  handler?: string                 # "module.path:function_name"

# ===== CORE TYPE DEFINITIONS (game-agnostic) =====

PropertyCondition:
  path: string                     # Dot-notation property path
  min?: number                     # Value >= min
  max?: number                     # Value <= max
  equals?: any                     # Value == equals
  in?: any[]                       # Value in list
  not_equals?: any                 # Value != not_equals
  not_in?: any[]                   # Value not in list

PropertyMod:
  path: string                     # Dot-notation property path
  set?: any                        # Set to absolute value
  delta?: number                   # Add delta (numeric only)
  multiply?: number                # Multiply by factor
  append?: any | any[]             # Append to list/set
  remove?: any | any[]             # Remove from list/set
  merge?: dict                     # Merge dict (deep update)

PropertyTransitions:
  path: string                     # Property to monitor
  thresholds:
    {number}: string               # threshold: target_state

CollectionOp:
  path: string                     # Path to collection in game_state.extra
  value?: any                      # Explicit value to add/remove
  from_context?: string            # Context variable to add/remove

SystemInvocation:
  system: string                   # System name ("commitment", "gossip", etc.)
  action: string                   # Action to perform ("create", "fulfill", etc.)
  params: dict                     # System-specific parameters

# ===== GAME-SPECIFIC TYPE DEFINITIONS =====

ConditionSpec:
  type: string                     # "hypothermia", "spore_infection", etc.
  severity?: int                   # Condition intensity (1-10)
  duration?: int                   # Turns until expires (-1 = permanent)
```

## Design Philosophy: Game-Agnostic Core + Convenience Layer

The mini-language has three tiers:

### Tier 1: Universal Primitives (Game-Agnostic)
Core operations that work in ANY game:
- `modify_property` - Manipulate any numeric/list/dict property
- `require_property` - Check any property value/threshold
- `property_transitions` - Auto-transition based on any property
- `add_to_collection` / `remove_from_collection` - List/set operations
- `invoke_system` - Call game-specific subsystems

### Tier 2: Convenience Sugar (Compiles to Tier 1)
Common patterns given readable names:
- `requires_trust` → `require_property: {path: "trust_state.current", min: N}`
- `trust_delta` → `modify_property: {path: "trust_state.current", delta: N}`
- `trust_transitions` → `property_transitions: {path: "trust_state.current", ...}`
- `set_flags` → `modify_property: {path: "extra.{key}", set: value}`
- `transition_to` → `modify_property: {path: "state_machine.current", set: state}`

### Tier 3: Common Operations (Universal Enough to Keep)
Operations common across many game types:
- `grant_items` / `spawn_items` / `consume_item` - Inventory management
- `apply_condition` / `remove_condition` - Status effects (if game uses them)

**Migration Path:** Existing configs using Tier 2 sugar continue to work. The interpreter automatically expands them to Tier 1 primitives at load time. New games can use Tier 1 directly or define their own Tier 2 sugar.

## Effect Execution Order

Effects are applied in this deterministic order:

### Phase 1: Property Cleanup
1. `unset_flags` - Clear flags first
2. `remove_from_collection` - Remove from collections
3. `remove_condition` - Remove status effects

### Phase 2: Property Modification
4. `modify_property` - All property modifications (numeric, lists, dicts)
5. `set_flags` - Set new flags
6. `apply_condition` - Apply new status effects

### Phase 3: Transitions & State Changes
7. `property_transitions` - Auto-transitions based on thresholds
8. `transition_to` - Explicit state transitions

### Phase 4: Inventory & Items
9. `consume_item` - Remove items from player
10. `grant_items` - Add items to player
11. `spawn_items` - Create items in world

### Phase 5: System Integration
12. `add_to_collection` - Add to collections
13. `invoke_system` - Call game-specific systems

**Deprecated Effects (compile to above):**
- `apply_damage`, `heal_amount` → `modify_property` (Phase 2)
- `trust_delta`, `trust_transitions` → `modify_property`, `property_transitions` (Phase 2/3)
- `grant_knowledge` → `modify_property: append` (Phase 2)
- `create_commitment`, `fulfill_commitment` → `invoke_system` (Phase 5)
- `create_gossip` → `invoke_system` (Phase 5)
- `track_in` → `add_to_collection` (Phase 5)
- `increment_counter` → `modify_property: delta` (Phase 2)

This order ensures consistency (e.g., cleanup before modification, state changes after property updates, system calls last).

## Message Templates

All message fields support variable substitution:

```python
# Available context variables (varies by reaction type):
{item}          # Item ID being given/used
{actor}         # Actor performing action
{target}        # Target entity
{trust}         # Current trust level
{state}         # Current entity state
{count}         # For counters/tracking
{damage}        # For combat
{heal}          # For healing
{keyword}       # For dialog
{location}      # Current location
{custom.X}      # Custom context values

# Example:
"accept_message": "The {target} accepts your {item} gratefully (trust: {trust})"
```

## Handler Escape Hatch - When to Use

**Use data-driven config when:**
- Logic is pure data transformation (set flags, change trust, grant items)
- Behavior expressible with standard effects/conditions
- No complex branching or multi-step algorithms needed
- Example: Wolf feeding (trust +1, transition at threshold 5→allied)

**Use handler escape hatch when:**
- Logic requires complex calculations (dynamic pricing, damage formulas)
- Multiple entities interact (check both golems dead before unlocking passage)
- Conditional branching too complex for condition primitives
- Performance-critical code (combat damage calculations with modifiers)
- Example: Golem puzzle (track hits on both golems, unlock only when both dead)

**Anti-pattern: DON'T use handler for simple flag setting or trust changes**

---

# Part 3: Interpreter Implementation

## Three-Phase Execution Model

```python
def process_reaction(
    entity: Any,           # Target entity (NPC, item, location)
    config: dict,          # Single reaction configuration
    accessor: Any,         # StateAccessor instance
    context: dict,         # Event context
    spec: ReactionSpec     # Reaction type specification
) -> EventResult:
    """Universal reaction interpreter."""

    # Enrich context with reaction-specific values
    context = spec.context_enrichment(context, config)

    # PHASE 1: Evaluate all conditions
    for condition_key in CONDITION_REGISTRY.keys():
        if condition_key in config:
            if not CONDITION_REGISTRY[condition_key](config, state, entity, context):
                return EventResult(
                    allow=True,
                    feedback=config.get("failure_message")
                )

    # PHASE 2: Apply all effects (in deterministic order)
    for effect_key in EFFECT_ORDER:
        if effect_key in config:
            EFFECT_REGISTRY[effect_key](config, state, entity, context)

    # PHASE 3: Generate feedback
    message = _get_message(config, spec)
    if message:
        message = substitute_templates(message, context)

    return EventResult(allow=True, feedback=message)
```

## Architecture Components

### Directory Structure

```
behaviors/shared/infrastructure/
├── reaction_interpreter.py          # Core interpreter (process_reaction)
├── reaction_effects.py               # Effect handlers registry
├── reaction_conditions.py            # Condition checkers registry
├── reaction_specs.py                 # ReactionSpec definitions
├── match_strategies.py               # Item/keyword matching logic
├── message_templates.py              # Template substitution
├── dispatcher_utils.py               # Handler loading & caching

# Each reaction infrastructure module (30-50 lines each):
behaviors/shared/infrastructure/
├── gift_reactions.py                 # Wire hook, find match, call interpreter
├── dialog_reactions.py
├── item_use_reactions.py
├── encounter_reactions.py
├── death_reactions.py
├── combat_reactions.py
├── entry_reactions.py
├── turn_environmental.py
├── commitment_reactions.py
├── take_reactions.py
├── examine_reactions.py
└── trade_reactions.py
```

### Infrastructure Module Template

All 12 infrastructure modules follow this pattern:

```python
# infrastructure/<type>_reactions.py

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import <TYPE>_SPEC

vocabulary = {
    "hook_definitions": [{
        "hook_id": "entity_<event>",
        "invocation": "entity",
        "description": "Called when <event> occurs"
    }],
    "events": [{
        "event": "on_<event>",
        "hook": "entity_<event>",
        "description": "Handle <type> reactions"
    }]
}

def on_<event>(entity, accessor, context):
    """Infrastructure dispatcher for <type>_reactions."""
    # 1. Extract target from context
    target = context.get("target") or entity

    # 2. Get reactions config
    reactions = target.properties.get("<type>_reactions", {})
    if not reactions:
        return EventResult(allow=True, feedback=None)

    # 3. Check for top-level handler
    if "handler" in reactions:
        handler = load_handler(reactions["handler"])
        if handler:
            return handler(entity, accessor, context)

    # 4. Find matching reaction (if type uses matching)
    match = <TYPE>_SPEC.match_strategy.find_match(reactions, context)
    if not match:
        return EventResult(allow=True, feedback=reactions.get("reject_message"))

    reaction_name, reaction_config = match

    # 5. Delegate to unified interpreter
    return process_reaction(entity, reaction_config, accessor, context, <TYPE>_SPEC)
```

**Code reduction:** Each module 30-50 lines (vs 150-200 lines for separate processors).

### ReactionSpec Definition

```python
@dataclass
class ReactionSpec:
    """Parametrizes interpreter for a reaction type."""
    reaction_type: str              # "gift", "dialog", etc.
    message_key: str                # Primary message field
    fallback_message_key: str       # Secondary message field
    match_strategy: MatchStrategy   # How to find applicable reactions
    context_enrichment: Callable    # Add reaction-specific context vars
```

### Effect Registry (18 Effect Handlers)

```python
# reaction_effects.py

EFFECT_REGISTRY: dict[str, EffectHandler] = {
    "unset_flags": _unset_flags,
    "set_flags": _set_flags,
    "remove_condition": _remove_condition,
    "apply_condition": _apply_condition,
    "apply_damage": _apply_damage,
    "heal_amount": _heal_entity,
    "trust_delta": _apply_trust_delta,
    "trust_transitions": _apply_trust_transitions,
    "transition_to": _transition_state,
    "consume_item": _consume_item,
    "grant_items": _grant_items,
    "spawn_items": _spawn_items,
    "grant_knowledge": _grant_knowledge,
    "create_commitment": _create_commitment,
    "fulfill_commitment": _fulfill_commitment,
    "create_gossip": _create_gossip,
    "track_in": _track_in_list,
    "increment_counter": _increment_counter,
}

# Example effect handler:
def _set_flags(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Set game state flags."""
    flags = config.get("set_flags", {})
    for flag_name, flag_value in flags.items():
        state.extra[flag_name] = flag_value
```

### Condition Registry (5 Condition Checkers)

```python
# reaction_conditions.py

CONDITION_REGISTRY: dict[str, ConditionChecker] = {
    "requires_flags": _check_flags,
    "requires_not_flags": _check_not_flags,
    "requires_state": _check_state,
    "requires_trust": _check_trust,
    "requires_items": _check_items,
}

# Example condition checker:
def _check_flags(config: dict, state: Any, entity: Any, context: dict) -> bool:
    """Check if all required flags match."""
    required = config.get("requires_flags", {})
    return all(state.extra.get(k) == v for k, v in required.items())
```

---

# Part 4: Reaction Type Specifications

## Complete Infrastructure Module List

All 12 reaction types with specifications and examples:

### 1. gift_reactions ✅ EXISTS

**Trigger:** `give <item> to <npc>`

**Spec:**
```python
GIFT_SPEC = ReactionSpec(
    reaction_type="gift",
    message_key="accept_message",
    fallback_message_key="message",
    match_strategy=ItemMatchStrategy("accepted_items"),
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "item": ctx.get("item").id,
        "target": ctx.get("target_actor").id
    }
)
```

**Example Configuration:**
```json
{
  "gift_reactions": {
    "food": {
      "accepted_items": ["venison", "meat", "rabbit"],
      "requires_state": ["wary", "neutral", "friendly"],
      "trust_delta": 1,
      "trust_transitions": {"3": "friendly", "5": "allied"},
      "track_in": "items_given_to_wolf",
      "accept_message": "The wolf takes the {item} and devours it hungrily.",
      "set_flags": {"wolf_fed": true}
    },
    "flowers": {
      "accepted_items": ["moonpetal", "frost_lily", "water_bloom"],
      "requires_trust": 2,
      "trust_delta": 2,
      "grant_items": ["royal_honey"],
      "accept_message": "The Bee Queen examines the {item} with delight.",
      "set_flags": {"queen_pleased": true}
    },
    "reject_message": "The wolf ignores your offering."
  }
}
```

---

### 2. dialog_reactions ⚠️ NEEDS CREATION

**Trigger:** `talk to <npc>` OR `ask <npc> about <topic>`

**Spec:**
```python
DIALOG_SPEC = ReactionSpec(
    reaction_type="dialog",
    message_key="summary",
    fallback_message_key="response",
    match_strategy=KeywordMatchStrategy("keywords"),
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "keyword": ctx.get("keyword", ""),
        "state": ctx.get("entity").properties.get("state_machine", {}).get("current", "")
    }
)
```

**Example Configuration:**
```json
{
  "dialog_reactions": {
    "injury": {
      "keywords": ["injury", "hurt", "wound", "happened"],
      "requires_not_flags": {"sira_injury_discussed": true},
      "trust_delta": 1,
      "summary": "'Beast attack,' she manages through gritted teeth. 'Pack of wolves... or what used to be wolves.'",
      "grant_knowledge": ["sira_injury_info"],
      "set_flags": {"sira_injury_discussed": true}
    },
    "tracking": {
      "keywords": ["tracking", "hunt", "teach", "skills"],
      "requires_state": ["stabilized", "mobile"],
      "requires_trust": 3,
      "summary": "'I could teach you to read the forest,' Sira offers.",
      "grant_knowledge": ["tracking_basics"],
      "set_flags": {"tracking_training_available": true}
    },
    "vendetta": {
      "keywords": ["wolves", "beasts", "attack", "revenge"],
      "requires_flags": {"sira_injury_discussed": true},
      "requires_trust": 2,
      "summary": "'Those creatures need to be put down. If you help me, I'll make it worth your while.'",
      "create_commitment": "commit_beast_hunt"
    }
  }
}
```

---

### 3. item_use_reactions ✅ EXISTS

**Trigger:** `use <item> on <target>`

**Spec:**
```python
ITEM_USE_SPEC = ReactionSpec(
    reaction_type="item_use",
    message_key="response",
    fallback_message_key="message",
    match_strategy=ItemMatchStrategy("accepted_items"),
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "item": ctx.get("item", ctx.get("entity", "")).id if hasattr(ctx.get("item", ctx.get("entity", "")), "id") else "",
        "target": ctx.get("target").id if ctx.get("target") else ""
    }
)
```

**Example Configuration:**
```json
{
  "item_use_reactions": {
    "healing": {
      "accepted_items": ["silvermoss", "healing_herbs"],
      "requires_state": ["infected", "injured"],
      "transition_to": "stabilized",
      "heal_amount": 30,
      "remove_condition": "fungal_infection",
      "consume_item": true,
      "trust_delta": 3,
      "response": "The {item} takes effect. Aldric's breathing eases and the fungal growth recedes.",
      "set_flags": {"aldric_healed": true},
      "fulfill_commitment": "commit_aldric_rescue"
    },
    "telescope_repair": {
      "accepted_items": ["lava_core"],
      "requires_flags": {"telescope_examined": true},
      "consume_item": true,
      "transition_to": "functional",
      "spawn_items": ["ice_fragments"],
      "response": "The lava core melts through the ice. The telescope is free!",
      "set_flags": {"telescope_freed": true}
    }
  }
}
```

---

### 4. encounter_reactions ⚠️ NEEDS CREATION

**Trigger:** First time player enters location with NPC

**Spec:**
```python
ENCOUNTER_SPEC = ReactionSpec(
    reaction_type="encounter",
    message_key="encounter_message",
    fallback_message_key="message",
    match_strategy=NoMatchStrategy(),  # Single config, no matching
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "actor": ctx.get("actor_id", "player"),
        "location": ctx.get("location").id if ctx.get("location") else ""
    }
)
```

**Example Configuration:**
```json
{
  "encounter_reactions": {
    "requires_not_flags": {"dire_bear_encountered": true},
    "encounter_message": "A massive dire bear blocks your path, protective fury in her eyes. Behind her, two small cubs huddle together, their breathing labored. They are gravely ill.",
    "transition_to": "hostile",
    "create_commitment": "commit_bear_cubs",
    "set_flags": {"dire_bear_encountered": true, "cubs_visible": true}
  }
}
```

**Note:** Single config object (not dict of named reactions) - triggers once on first location entry.

---

### 5. death_reactions ⚠️ NEEDS CREATION

**Trigger:** Entity health reaches 0

**Spec:**
```python
DEATH_SPEC = ReactionSpec(
    reaction_type="death",
    message_key="death_message",
    fallback_message_key="message",
    match_strategy=NoMatchStrategy(),
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "entity": ctx.get("entity").id,
        "killer": ctx.get("killer", "unknown")
    }
)
```

**Example Configuration:**
```json
{
  "death_reactions": {
    "death_message": "The stone golem crumbles to dust, ancient magic finally exhausted.",
    "spawn_items": ["golem_core", "stone_fragments"],
    "set_flags": {"golem_1_dead": true},
    "create_gossip": {
      "topic": "golem_defeated",
      "spread_to": ["town_gate", "market_square"],
      "priority": 5
    },
    "handler": "behaviors.regions.frozen_reaches.golem_puzzle:check_both_golems_dead"
  }
}
```

**Handler Example (Complex Logic):**
```python
# golem_puzzle.py
def check_both_golems_dead(entity, accessor, context):
    """Unlock passage if both golems defeated."""
    state = accessor.game_state
    if state.extra.get("golem_1_dead") and state.extra.get("golem_2_dead"):
        unlock_exit(state, "frozen_chamber", "hidden_passage", "secret_vault")
        return EventResult(
            allow=True,
            feedback="With both guardians fallen, a hidden passage grinds open."
        )
    return EventResult(allow=True, feedback=None)
```

---

### 6. combat_reactions ⚠️ NEEDS CREATION

**Trigger:** `attack <target>` OR damage dealt/received

**Spec:**
```python
COMBAT_SPEC = ReactionSpec(
    reaction_type="combat",
    message_key="message",
    fallback_message_key="response",
    match_strategy=NoMatchStrategy(),
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "damage": ctx.get("damage", 0),
        "attacker": ctx.get("attacker", "unknown"),
        "weapon": ctx.get("weapon", "fists")
    }
)
```

**Example Configuration:**
```json
{
  "combat_reactions": {
    "on_damage_taken": {
      "requires_flags": {"puzzle_active": true},
      "increment_counter": "golem_1_hits",
      "message": "The golem shudders from the impact. (Hits: {count})",
      "handler": "behaviors.regions.frozen_reaches.golem_puzzle:track_simultaneous_damage"
    }
  }
}
```

**Note:** Combat reactions often use handlers due to complex damage calculations and puzzle state tracking.

---

### 7. entry_reactions ⚠️ NEEDS CREATION

**Trigger:** `go <direction>` → enter new location

**Spec:**
```python
ENTRY_SPEC = ReactionSpec(
    reaction_type="entry",
    message_key="message",
    fallback_message_key="entry_message",
    match_strategy=NoMatchStrategy(),
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "from_direction": ctx.get("from_direction", "unknown"),
        "actor": ctx.get("actor_id", "player")
    }
)
```

**Example Configuration (on Location):**
```json
{
  "entry_reactions": {
    "requires_not_flags": {"thermal_protection_worn": true},
    "apply_condition": {
      "type": "hypothermia",
      "severity": 1,
      "duration": -1
    },
    "message": "The brutal cold seeps into your bones. Without protection, you won't last long here.",
    "set_flags": {"entered_freezing_zone": true}
  }
}
```

---

### 8. turn_environmental ✅ EXISTS (PARTIAL)

**Trigger:** Per-turn phase for environmental effects

**Spec:**
```python
TURN_ENV_SPEC = ReactionSpec(
    reaction_type="turn_environmental",
    message_key="message",
    fallback_message_key="tick_message",
    match_strategy=NoMatchStrategy(),
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "turn": ctx.get("turn", 0),
        "location": ctx.get("location").id if ctx.get("location") else ""
    }
)
```

**Example Configuration (on Location):**
```json
{
  "turn_environmental": {
    "requires_flags": {"player_in_freezing_zone": true},
    "requires_not_flags": {"thermal_protection_worn": true},
    "apply_damage": 5,
    "increment_counter": "hypothermia_turns",
    "message": "The freezing cold drains your vitality. ({damage} damage)",
    "handler": "behaviors.regions.frozen_reaches.hypothermia:check_hypothermia_threshold"
  }
}
```

---

### 9. commitment_reactions ⚠️ NEEDS CREATION

**Trigger:** Commitment state changes (fulfilled/abandoned)

**Spec:**
```python
COMMITMENT_SPEC = ReactionSpec(
    reaction_type="commitment",
    message_key="message",
    fallback_message_key="consequence_message",
    match_strategy=StateChangeMatchStrategy("state_change"),  # Match "fulfilled" or "abandoned"
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "commitment_id": ctx.get("commitment_id", ""),
        "state_change": ctx.get("state_change", "")
    }
)
```

**Example Configuration:**
```json
{
  "commitment_reactions": {
    "fulfilled": {
      "requires_flags": {"cubs_healed": true},
      "transition_to": "grateful",
      "trust_delta": 5,
      "grant_items": ["bear_claw_charm"],
      "message": "The dire bear nuzzles her healthy cubs, then approaches you with reverence.",
      "set_flags": {"bear_alliance": true}
    },
    "abandoned": {
      "transition_to": "vengeful",
      "trust_delta": -10,
      "message": "The cubs' breathing stops. The dire bear's grief-stricken roar transforms into pure rage.",
      "set_flags": {"bear_hostile": true, "cubs_died": true},
      "handler": "behaviors.regions.beast_wilds.bear_cubs:on_cubs_died"
    }
  }
}
```

---

### 10. take_reactions ⚠️ NEEDS CREATION

**Trigger:** `take <item>` from location

**Spec:**
```python
TAKE_SPEC = ReactionSpec(
    reaction_type="take",
    message_key="message",
    fallback_message_key="response",
    match_strategy=NoMatchStrategy(),
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "item": ctx.get("item").id if ctx.get("item") else "",
        "location": ctx.get("location").id if ctx.get("location") else ""
    }
)
```

**Example Configuration (on Item):**
```json
{
  "take_reactions": {
    "requires_not_flags": {"queen_permission_granted": true},
    "message": "As you reach for the royal honey, furious buzzing fills the air. The bees attack!",
    "set_flags": {"honey_theft_detected": true, "bees_hostile": true},
    "apply_damage": 15,
    "handler": "behaviors.regions.beast_wilds.bee_queen:on_honey_theft"
  }
}
```

---

### 11. examine_reactions ⚠️ NEEDS CREATION (OPTIONAL)

**Trigger:** `examine <entity>`

**Spec:**
```python
EXAMINE_SPEC = ReactionSpec(
    reaction_type="examine",
    message_key="message",
    fallback_message_key="reveal_message",
    match_strategy=ProgressiveMatchStrategy("examine_count"),  # Index by count
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "entity": ctx.get("entity").id,
        "examine_count": ctx.get("examine_count", 0)
    }
)
```

**Example Configuration:**
```json
{
  "examine_reactions": {
    "progressive_reveals": [
      {
        "requires_not_flags": {"telescope_examined_once": true},
        "message": "The telescope is encased in thick magical ice. The ice seems to pulse with inner warmth.",
        "grant_knowledge": ["ice_puzzle_hint_1"],
        "set_flags": {"telescope_examined_once": true}
      },
      {
        "requires_flags": {"telescope_examined_once": true},
        "requires_not_flags": {"telescope_solution_known": true},
        "message": "Looking closer, you realize: this ice needs heat to melt it. A source of intense heat might work.",
        "grant_knowledge": ["ice_puzzle_solution"],
        "set_flags": {"telescope_solution_known": true}
      }
    ]
  }
}
```

---

### 12. trade_reactions ⚠️ NEEDS CREATION

**Trigger:** `buy <item>` OR `sell <item>`

**Spec:**
```python
TRADE_SPEC = ReactionSpec(
    reaction_type="trade",
    message_key="message",
    fallback_message_key="response",
    match_strategy=ItemMatchStrategy("item"),
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "item": ctx.get("item", ""),
        "vendor": ctx.get("vendor").id if ctx.get("vendor") else "",
        "transaction_type": ctx.get("transaction_type", "buy")
    }
)
```

**Example Configuration:**
```json
{
  "trade_reactions": {
    "inventory": [
      {
        "item": "healing_potion",
        "buy_price": 50,
        "sell_price": 20,
        "stock": 10,
        "message": "Herbalist Maren hands you a healing potion."
      },
      {
        "item": "rare_herb",
        "buy_price": 200,
        "sell_price": 80,
        "stock": 3,
        "requires_trust": 3,
        "message": "Maren pulls a rare herb from her private collection. 'Don't waste it.'"
      }
    ],
    "reputation_modifier": 0.9,
    "handler": "behaviors.regions.civilized_remnants.vendors:calculate_dynamic_prices"
  }
}
```

---

## Infrastructure Status Summary

| Module | Status | Entities | Priority | Effort |
|--------|--------|----------|----------|--------|
| gift_reactions | ✅ Exists | 5 | - | - |
| item_use_reactions | ✅ Exists | 10+ | - | - |
| turn_environmental | ✅ Exists | 3 | - | - |
| dialog_reactions | ⚠️ Partial | 13+ | HIGH | 1 day |
| encounter_reactions | ❌ Needs | 4 | HIGH | 1 day |
| death_reactions | ❌ Needs | 7 | HIGH | 1 day |
| combat_reactions | ❌ Needs | 3 | MEDIUM | 1 day |
| entry_reactions | ❌ Needs | 4 | MEDIUM | 0.5 day |
| commitment_reactions | ❌ Needs | 5 | MEDIUM | 1 day |
| take_reactions | ❌ Needs | 2 | LOW | 0.5 day |
| examine_reactions | ❌ Needs | 5+ | LOW | 0.5 day |
| trade_reactions | ❌ Needs | 4 | LOW | 1 day |

**Total:** 3/12 complete, 9 need creation/migration (~8-10 days effort)

---

# Part 5: Validation System

## Load-Time Validation (Comprehensive)

All reaction configurations validated when game loads. Invalid configs cause **immediate failure** - no silent errors.

### 1. Handler Path Validation

**What:** Verify all handler paths can be imported and have correct signatures.

```python
def validate_handler_path(entity_id: str, reaction_type: str, handler_path: str) -> None:
    """Validate handler can be loaded and has correct signature.

    Raises ValidationError if:
    - Module cannot be imported
    - Function doesn't exist
    - Signature doesn't match (entity, accessor, context)
    - Return type isn't EventResult
    """
    try:
        # Parse path
        if ":" not in handler_path:
            raise ValueError(f"Invalid handler path format (missing ':'): {handler_path}")

        module_path, func_name = handler_path.rsplit(":", 1)

        # Import module
        module = import_module(module_path)

        # Get function
        handler = getattr(module, func_name)

        # Check signature
        sig = inspect.signature(handler)
        params = list(sig.parameters.keys())
        if params != ["entity", "accessor", "context"]:
            raise TypeError(
                f"Handler {handler_path} has invalid signature. "
                f"Expected (entity, accessor, context), got ({', '.join(params)})"
            )

        # Check return type annotation
        hints = get_type_hints(handler)
        if hints.get("return").__name__ != "EventResult":
            raise TypeError(
                f"Handler {handler_path} must return EventResult, "
                f"got {hints.get('return', 'unknown')}"
            )

    except Exception as e:
        raise ValidationError(
            f"Entity '{entity_id}' {reaction_type} handler invalid: {handler_path}\n"
            f"  Error: {e}"
        )
```

**When:** Game load, before any gameplay.
**Result:** All handlers validated and cached in `_handler_cache`.

---

### 2. Schema Validation

**What:** Verify all reaction configs match expected structure.

```python
# Auto-generated from effect/condition registries
def generate_reaction_schema(spec: ReactionSpec) -> dict:
    """Generate JSON schema for a reaction type."""
    return {
        "type": "object",
        "properties": {
            # Handler escape hatch
            "handler": {
                "type": "string",
                "pattern": r"^[\w\.]+:\w+$"
            },

            # Conditions (from CONDITION_REGISTRY)
            **{key: {"type": get_type(key)} for key in CONDITION_REGISTRY.keys()},

            # Effects (from EFFECT_REGISTRY)
            **{key: {"type": get_type(key)} for key in EFFECT_REGISTRY.keys()},

            # Messages (from spec)
            spec.message_key: {"type": "string"},
            spec.fallback_message_key: {"type": "string"},
            "failure_message": {"type": "string"},
        },
        "additionalProperties": False  # Catch typos
    }

# Validate at load time
def validate_reaction_config(entity: Entity, reaction_type: str) -> None:
    """Validate reaction config against schema."""
    config = entity.properties.get(reaction_type)
    if not config:
        return

    spec = REACTION_SPECS[reaction_type]
    schema = generate_reaction_schema(spec)

    try:
        jsonschema.validate(config, schema)
    except jsonschema.ValidationError as e:
        raise ValidationError(
            f"Entity '{entity.id}' {reaction_type} config invalid:\n"
            f"  Path: {'.'.join(str(p) for p in e.path)}\n"
            f"  Error: {e.message}"
        )
```

**When:** Game load, after handler validation.
**Result:** All configs structurally valid, unknown fields caught.

---

### 3. Cross-Reference Validation

**What:** Verify referenced entities/items/states exist.

```python
def validate_cross_references(entity: Entity, game_state: GameState) -> None:
    """Validate all entity references in reaction configs."""

    # Check all reaction types
    for reaction_type in REACTION_TYPES:
        config = entity.properties.get(reaction_type)
        if not config:
            continue

        # Recursively check all configs
        for reaction_name, reaction_config in flatten_configs(config).items():
            # Validate accepted_items reference actual items
            if "accepted_items" in reaction_config:
                for item_id in reaction_config["accepted_items"]:
                    if not game_state.get_item(item_id):
                        warnings.warn(
                            f"Entity '{entity.id}' {reaction_type}.{reaction_name} "
                            f"accepts unknown item '{item_id}'"
                        )

            # Validate grant_items reference actual items
            if "grant_items" in reaction_config:
                for item_id in reaction_config["grant_items"]:
                    if not game_state.get_item(item_id):
                        raise ValidationError(
                            f"Entity '{entity.id}' {reaction_type}.{reaction_name} "
                            f"grants unknown item '{item_id}'"
                        )

            # Validate transition_to references valid states
            if "transition_to" in reaction_config:
                target_state = reaction_config["transition_to"]
                sm = entity.properties.get("state_machine", {})
                valid_states = sm.get("states", [])
                if target_state not in valid_states:
                    raise ValidationError(
                        f"Entity '{entity.id}' {reaction_type}.{reaction_name} "
                        f"transitions to unknown state '{target_state}'. "
                        f"Valid states: {valid_states}"
                    )

            # Validate trust_transitions reference valid states
            if "trust_transitions" in reaction_config:
                for threshold, target_state in reaction_config["trust_transitions"].items():
                    sm = entity.properties.get("state_machine", {})
                    valid_states = sm.get("states", [])
                    if target_state not in valid_states:
                        raise ValidationError(
                            f"Entity '{entity.id}' {reaction_type}.{reaction_name} "
                            f"trust_transitions[{threshold}] references unknown state '{target_state}'. "
                            f"Valid states: {valid_states}"
                        )

            # Validate create_commitment references valid commitment config
            if "create_commitment" in reaction_config:
                commitment_id = reaction_config["create_commitment"]
                if commitment_id not in game_state.extra.get("commitment_configs", {}):
                    raise ValidationError(
                        f"Entity '{entity.id}' {reaction_type}.{reaction_name} "
                        f"creates unknown commitment '{commitment_id}'"
                    )

            # Validate spawn_items reference actual item templates
            if "spawn_items" in reaction_config:
                for item_id in reaction_config["spawn_items"]:
                    if not game_state.get_item_template(item_id):
                        raise ValidationError(
                            f"Entity '{entity.id}' {reaction_type}.{reaction_name} "
                            f"spawns unknown item '{item_id}'"
                        )
```

**When:** Game load, after schema validation.
**Result:** All references validated, broken references caught.

---

### 4. Entity Capability Validation

**What:** Verify entity types only have appropriate reaction types.

```python
def validate_entity_capabilities(entity: Entity, game_state: GameState) -> None:
    """Ensure entity type supports its reaction types."""

    # Determine entity type
    if entity.id in game_state.actors:
        entity_type = "actor"
    elif any(entity.id == item.id for item in game_state.items):
        entity_type = "item"
    elif any(entity.id == loc.id for loc in game_state.locations):
        entity_type = "location"
    else:
        raise ValidationError(f"Entity '{entity.id}' not found in actors/items/locations")

    # Define valid reaction types per entity type
    VALID_REACTIONS = {
        "actor": [
            "gift_reactions",
            "encounter_reactions",
            "death_reactions",
            "dialog_reactions",
            "combat_reactions",
            "commitment_reactions"
        ],
        "item": [
            "item_use_reactions",
            "take_reactions",
            "examine_reactions"
        ],
        "location": [
            "entry_reactions",
            "turn_environmental"
        ]
    }

    # Check each reaction type on entity
    for property_key in entity.properties.keys():
        if property_key.endswith("_reactions"):
            if property_key not in VALID_REACTIONS[entity_type]:
                raise ValidationError(
                    f"{entity_type.title()} '{entity.id}' cannot have {property_key}. "
                    f"Valid reactions for {entity_type}s: {VALID_REACTIONS[entity_type]}"
                )
```

**When:** Game load, after cross-reference validation.
**Result:** No actors with entry_reactions, no items with gift_reactions, etc.

---

### 5. Effect/Condition Compatibility Validation

**What:** Verify effects/conditions make sense for entity.

```python
def validate_effect_compatibility(entity: Entity, reaction_type: str, config: dict) -> None:
    """Check if effects are compatible with entity properties."""

    # Trust effects require trust_state
    if "trust_delta" in config or "trust_transitions" in config:
        if "trust_state" not in entity.properties:
            raise ValidationError(
                f"Entity '{entity.id}' {reaction_type} uses trust effects "
                f"but has no trust_state property"
            )

    # State transitions require state_machine
    if "transition_to" in config or "trust_transitions" in config:
        if "state_machine" not in entity.properties:
            raise ValidationError(
                f"Entity '{entity.id}' {reaction_type} uses state transitions "
                f"but has no state_machine property"
            )

    # Damage/healing require health
    if "apply_damage" in config or "heal_amount" in config:
        if "health" not in entity.properties and "max_health" not in entity.properties:
            warnings.warn(
                f"Entity '{entity.id}' {reaction_type} uses damage/healing "
                f"but has no health/max_health property"
            )

    # Conditions require active_conditions tracking
    if "apply_condition" in config or "remove_condition" in config:
        # This is OK - active_conditions created on demand
        pass
```

**When:** Game load, during cross-reference validation.
**Result:** Effects match entity capabilities.

---

## Validation Tool: validate_game_state.py

**Usage:**
```bash
$ python tools/validate_game_state.py examples/big_game

Validating game state...

✓ All handler paths resolve (47/47)
✓ All reaction schemas valid (42/42)
✓ All cross-references valid (183/183)
✓ All entity capabilities valid (156/156)
✓ All effect compatibilities valid (42/42)

⚠ 3 warnings:
  - alpha_wolf (gift_reactions.food) accepts 'rabbit' but no item 'rabbit' exists
  - dire_bear (gift_reactions) missing reject_message
  - spider_matriarch (combat_reactions) uses damage but has no health property

Validation complete: 0 errors, 3 warnings
```

**Features:**
- Validates all 5 validation types
- Reports both errors (fatal) and warnings (suspicious)
- Shows line numbers for JSON errors
- Suggests fixes for common issues
- Exit code 1 if any errors found (for CI)

---

# Part 6: Discoverability Tooling

All tools work with the unified interpreter's declarative configs.

## Tool 1: entity_inspector.py

**Purpose:** Show complete behavior profile for a single entity.

**Usage:**
```bash
$ python tools/entity_inspector.py alpha_wolf
```

**Output:**
```
Entity: alpha_wolf (Actor)
Location: wolf_clearing
State: hostile (can transition to: wary, neutral, friendly, allied)
Trust: 0 (floor: -5, ceiling: 5)

Reactions:
  ✓ gift_reactions (3 reaction types)

    [food]
      Trigger: give [venison, meat, rabbit] to alpha_wolf
      Conditions: entity state in [wary, neutral, friendly]
      Effects:
        - trust +1
        - auto-transition at trust=3 → friendly, trust=5 → allied
        - track in 'items_given_to_wolf'
        - set flag: wolf_fed = true
      Message: "The wolf takes the {item} and devours it hungrily."

    [rejection]
      Message: "The wolf ignores your offering."

  ✓ dialog_reactions
    Handler: behaviors.regions.beast_wilds.wolf_pack:on_wolf_talk
    (see handler for details)

  ✓ combat_reactions
    Handler: behaviors.regions.beast_wilds.wolf_pack:on_wolf_combat
    (see handler for details)

Properties:
  - pack_behavior: {pack_id: "wolf_pack", role: "alpha", followers: [grey_wolf_1, grey_wolf_2]}
  - companion_config: {activation_state: "allied", skills: ["tracking", "hunting"]}
  - health: 150
  - max_health: 150

Linked Entities:
  - Followers: grey_wolf_1, grey_wolf_2
  - Location: wolf_clearing
  - Items accepted: venison, meat, rabbit
```

**Implementation:**
```python
def inspect_entity(entity_id: str, game_state: GameState) -> str:
    """Generate detailed entity report."""
    entity = find_entity(entity_id, game_state)

    report = []
    report.append(f"Entity: {entity.id} ({get_entity_type(entity)})")
    report.append(f"Location: {entity.location if hasattr(entity, 'location') else 'N/A'}")

    # Show state machine
    if "state_machine" in entity.properties:
        sm = entity.properties["state_machine"]
        current = sm.get("current", sm.get("initial"))
        report.append(f"State: {current} (can transition to: {', '.join(sm['states'])})")

    # Show trust
    if "trust_state" in entity.properties:
        trust = entity.properties["trust_state"]
        report.append(f"Trust: {trust['current']} (floor: {trust['floor']}, ceiling: {trust['ceiling']})")

    # Show all reactions
    report.append("\nReactions:")
    for reaction_type in REACTION_TYPES:
        if reaction_type not in entity.properties:
            continue

        config = entity.properties[reaction_type]
        report.append(f"  ✓ {reaction_type}")

        # If handler-only, show handler
        if "handler" in config and len(config) == 1:
            report.append(f"    Handler: {config['handler']}")
            report.append(f"    (see handler for details)")
            continue

        # Show each named reaction
        for name, reaction_config in config.items():
            if name in ("handler", "reject_message"):
                continue
            report.append(f"\n    [{name}]")

            # Show trigger
            if "accepted_items" in reaction_config:
                report.append(f"      Trigger: give {reaction_config['accepted_items']} to {entity.id}")
            if "keywords" in reaction_config:
                report.append(f"      Trigger: talk about {reaction_config['keywords']}")

            # Show conditions
            conditions = [k for k in CONDITION_REGISTRY.keys() if k in reaction_config]
            if conditions:
                report.append(f"      Conditions:")
                for cond in conditions:
                    report.append(f"        - {format_condition(cond, reaction_config[cond])}")

            # Show effects
            effects = [k for k in EFFECT_REGISTRY.keys() if k in reaction_config]
            if effects:
                report.append(f"      Effects:")
                for effect in effects:
                    report.append(f"        - {format_effect(effect, reaction_config[effect])}")

            # Show message
            message_key = get_message_key(reaction_type)
            if message_key in reaction_config:
                report.append(f'      Message: "{reaction_config[message_key]}"')

    return "\n".join(report)
```

---

## Tool 2: reaction_inventory.py

**Purpose:** List all entities with a specific reaction type.

**Usage:**
```bash
$ python tools/reaction_inventory.py --type gift_reactions
```

**Output:**
```
Gift Reactions (5 entities):

alpha_wolf (3 reaction types: food, flowers, rejection)
  [food] → venison, meat, rabbit (trust +1, transition at 3→friendly, 5→allied)
  Location: wolf_clearing

salamander (handler)
  Handler: behaviors.regions.frozen_reaches.salamanders:on_receive_item
  Location: hot_springs

bee_queen (2 reaction types: flowers, honey_offering)
  [flowers] → moonpetal, frost_lily, water_bloom (trust +2, grant royal_honey)
  [honey_offering] → requires trust=3, grants queen_blessing
  Location: hive_chamber

dire_bear (1 reaction type: healing_herbs)
  [healing_herbs] → healing_herbs (fulfill commitment, heal cubs)
  Handler: behaviors.regions.beast_wilds.bear_cubs:on_cubs_healed
  Location: predators_den

npc_spore_mother (handler)
  Handler: behaviors.regions.fungal_depths.spore_mother:on_receive_offering
  Location: spore_grotto
```

**Filters:**
```bash
$ python tools/reaction_inventory.py --type dialog_reactions --state friendly
$ python tools/reaction_inventory.py --type item_use_reactions --region frozen_reaches
$ python tools/reaction_inventory.py --handler-only
```

---

## Tool 3: handler_usage.py

**Purpose:** Show which entities use a specific handler.

**Usage:**
```bash
$ python tools/handler_usage.py behaviors.regions.beast_wilds.wolf_pack:on_receive_item
```

**Output:**
```
Handler: on_receive_item
Module: behaviors.regions.beast_wilds.wolf_pack
Location: wolf_pack.py:81-187

Signature: (entity, accessor, context) -> EventResult

Used by (3 entities):
  - alpha_wolf (gift_reactions.food)
      Accepts: venison, meat, rabbit
      Trust: +1 per feeding
      Transitions: hostile→wary(1)→neutral(2)→friendly(3)→allied(5)
      Location: wolf_clearing

  - grey_wolf_1 (gift_reactions.food)
      Accepts: venison, meat, rabbit
      Trust: mirrors alpha_wolf
      Location: wolf_clearing

  - grey_wolf_2 (gift_reactions.food)
      Accepts: venison, meat, rabbit
      Trust: mirrors alpha_wolf
      Location: wolf_clearing

Trigger: give <food> to <wolf>

Handler Effects (from code analysis):
  - Increases alpha_wolf trust (+1 per feeding)
  - Pack mirrors alpha trust/state via pack_behavior
  - Grants alpha_fang_fragment at allied state
  - Activates wolf as companion at allied state
```

**Features:**
- Shows all entities using the handler
- Displays their configurations
- Analyzes handler code for effects (AST parsing)
- Shows handler signature and location

---

## Tool 4: reaction_graph.py

**Purpose:** Visualize reaction dependencies and flows.

**Usage:**
```bash
$ python tools/reaction_graph.py --entity dire_bear --output graph.png
```

**Output:** PNG graph showing:
```
[Player] --give healing_herbs--> [Dire Bear]
           |
           v
    [encounter_reactions]
           |
           v
    create_commitment: commit_bear_cubs
           |
           v
    [gift_reactions.healing_herbs]
           |
           v
    - heal_amount: 30
    - remove_condition: sick
    - transition_to: grateful
    - set_flags: {cubs_healed: true}
    - fulfill_commitment: commit_bear_cubs
           |
           v
    [commitment_reactions.fulfilled]
           |
           v
    - trust_delta: +5
    - grant_items: [bear_claw_charm]
    - set_flags: {bear_alliance: true}
```

**Filters:**
```bash
$ python tools/reaction_graph.py --entity dire_bear --trace "give healing_herbs"
$ python tools/reaction_graph.py --region beast_wilds --show-all-flows
```

---

## Tool 5: mini_language_reference.py

**Purpose:** Generate complete mini-language documentation from registries.

**Usage:**
```bash
$ python tools/mini_language_reference.py --format markdown > mini_language.md
```

**Output:**
```markdown
# Reaction Mini-Language Reference

Auto-generated from effect/condition registries.

## Effects (18 total)

### set_flags
**Type:** `{string: any}`
**Description:** Set game state flags
**Example:**
```json
"set_flags": {"wolf_fed": true, "quest_started": "bear_cubs"}
```
**Used by:** All reaction types

### trust_delta
**Type:** `int`
**Description:** Modify entity trust by delta
**Example:**
```json
"trust_delta": 2
```
**Requirements:** Entity must have trust_state property
**Used by:** gift_reactions, dialog_reactions, item_use_reactions, encounter_reactions

[... continues for all 18 effects ...]

## Conditions (5 total)

### requires_flags
**Type:** `{string: any}`
**Description:** All flags must match for reaction to apply
**Example:**
```json
"requires_flags": {"quest_active": true, "player_level": 5}
```
**Used by:** All reaction types

[... continues for all 5 conditions ...]

## Reaction Type Specifications

### gift_reactions
**Trigger:** `give <item> to <npc>`
**Matching:** accepted_items list
**Message:** accept_message (primary), message (fallback)
**Context vars:** {item}, {target}, {trust}

[... continues for all 12 reaction types ...]
```

---

## Tool 6: config_validator.py (Interactive)

**Purpose:** Validate reaction configs interactively with helpful errors.

**Usage:**
```bash
$ python tools/config_validator.py
```

**Interactive Session:**
```
Reaction Config Validator
-------------------------
Paste your reaction config (JSON), then press Enter twice:

{
  "gift_reactions": {
    "food": {
      "accepted_items": ["venison"],
      "trust_delta": 1,
      "transition_too": "friendly"  <-- TYPO
    }
  }
}

❌ Validation failed:

Line 5: Unknown field 'transition_too'
  Did you mean: transition_to?

Line 5: Missing state_machine check
  Effect 'transition_to' requires entity to have 'state_machine' property.
  Add this to entity.properties:
    "state_machine": {
      "states": ["hostile", "friendly", "allied"],
      "initial": "hostile"
    }

✓ Schema: PASS
✓ Cross-references: PASS
❌ Effect compatibility: 1 warning

Fix these issues and try again.
```

---

# Part 7: Migration Strategy

## Four-Phase Migration Plan

### Phase 1: Build Core Infrastructure (2-3 days)

**Objective:** Create unified interpreter and registries.

**Tasks:**
1. Create `reaction_interpreter.py` with 3-phase execution model
2. Create `reaction_effects.py` with 18 effect handlers
3. Create `reaction_conditions.py` with 5 condition checkers
4. Create `reaction_specs.py` with all 12 ReactionSpec definitions
5. Create `match_strategies.py` with matching logic
6. Create `message_templates.py` with substitution engine
7. Write comprehensive tests for all components

**Deliverables:**
- Core interpreter fully functional
- All effect/condition handlers tested
- Template substitution working
- Unit test coverage >80%

**Success Criteria:**
- Can process any valid reaction config
- Effects compose correctly
- Conditions evaluate correctly
- Templates substitute all variables

---

### Phase 2: Create Infrastructure Dispatchers (2-3 days)

**Objective:** Build all 12 thin infrastructure modules.

**Tasks:**

**High Priority (required for existing content):**
1. Refactor `gift_reactions.py` to use interpreter (0.5 day)
2. Refactor `item_use_reactions.py` to use interpreter (0.5 day)
3. Create `encounter_reactions.py` (0.5 day)
4. Create `dialog_reactions.py` (0.5 day)
5. Create `death_reactions.py` (0.5 day)

**Medium Priority (needed for complete game):**
6. Create `combat_reactions.py` (0.5 day)
7. Create `entry_reactions.py` (0.5 day)
8. Refactor `turn_environmental.py` to use interpreter (0.5 day)
9. Create `commitment_reactions.py` (0.5 day)

**Low Priority (quality of life):**
10. Create `take_reactions.py` (0.5 day)
11. Create `examine_reactions.py` (0.5 day)
12. Create `trade_reactions.py` (0.5 day)

**Deliverables:**
- All 12 infrastructure modules follow template pattern
- Each module 30-50 lines
- All registered in appropriate hooks
- Integration tests for each module

**Success Criteria:**
- Each module delegates to interpreter correctly
- Matching strategies work for each type
- Context enrichment adds expected variables
- All hooks fire correctly

---

### Phase 3: Migrate Entity Configurations (2-3 days)

**Objective:** Update all game_state.json configs to new format.

**Tasks:**
1. Audit all existing handler-based reactions (grep for `vocabulary` in behavior modules)
2. For each entity with reactions:
   - Convert vocabulary event handlers to property configs
   - Add data-driven configs where possible
   - Use handler escape hatch for complex logic
   - Validate with `validate_game_state.py`
3. Update all handler paths to full module paths
4. Remove vocabulary declarations from behavior modules
5. Keep handler functions as pure functions (no vocabulary)

**Entity Migration Priority:**
1. **Frozen Reaches** (salamanders, golems, telescope) - 0.5 day
2. **Beast Wilds** (wolves, bear, bee queen, spider) - 1 day
3. **Fungal Depths** (spore mother, aldric, myconids) - 1 day
4. **Sunken District** (sailors, merchants, drowning) - 0.5 day
5. **Civilized Remnants** (vendors, guards, healer) - 0.5 day

**Deliverables:**
- All entities using property-based reactions
- No vocabulary events in behavior modules
- Handler functions callable directly (no infrastructure dependency)
- All configs pass validation

**Success Criteria:**
- `validate_game_state.py` shows 0 errors
- All existing walkthroughs pass
- Handler cache populated correctly
- Performance: game load < 2 seconds

---

### Phase 4: Build Validation & Tooling (1-2 days)

**Objective:** Create comprehensive validation and discoverability ecosystem.

**Tasks:**
1. Implement load-time validation (all 5 types)
2. Build `validate_game_state.py` tool
3. Build `entity_inspector.py` tool
4. Build `reaction_inventory.py` tool
5. Build `handler_usage.py` tool
6. Build `reaction_graph.py` tool (optional)
7. Build `mini_language_reference.py` tool
8. Build `config_validator.py` interactive tool (optional)
9. Generate JSON schemas from registries
10. Create authoring templates for common patterns

**Deliverables:**
- All validation runs at game load
- All 6+ tools functional
- Comprehensive error messages
- JSON schemas auto-generated
- Documentation auto-generated from configs

**Success Criteria:**
- Validation catches all error types
- Tools provide actionable information
- Schemas prevent typos
- Documentation stays in sync with code

---

## Migration Checklist

Before declaring migration complete:

- [ ] Core interpreter handles all 12 reaction types
- [ ] All 18 effect handlers implemented and tested
- [ ] All 5 condition checkers implemented and tested
- [ ] All 12 infrastructure modules created
- [ ] All entities migrated to property-based configs
- [ ] All handler paths use full module names
- [ ] No vocabulary events in behavior modules
- [ ] All 5 validation types running at load time
- [ ] All discoverability tools functional
- [ ] All existing walkthroughs pass
- [ ] Performance: game load < 2 seconds
- [ ] Performance: reaction dispatch < 1ms average
- [ ] Test coverage >80% for interpreter/effects/conditions
- [ ] Documentation auto-generated from registries
- [ ] Zero validation errors on full game state
- [ ] All handler paths resolve and cache correctly

---

## Estimated Total Effort

| Phase | Days | Tasks |
|-------|------|-------|
| 1. Core Infrastructure | 2-3 | Interpreter, registries, tests |
| 2. Infrastructure Dispatchers | 2-3 | All 12 modules |
| 3. Entity Migration | 2-3 | Update all game_state.json |
| 4. Validation & Tooling | 1-2 | 5 validations, 6+ tools |
| **Total** | **7-11 days** | **~40 tasks** |

Conservative estimate: **10 working days** for complete migration.

---

# Part 8: Testing Strategy

## Unit Tests

### Interpreter Core Tests

```python
class TestReactionInterpreter(unittest.TestCase):
    def test_three_phase_execution_order(self):
        """Interpreter executes phases in order: conditions → effects → feedback."""
        config = {
            "requires_flags": {"test": True},
            "set_flags": {"result": True},
            "message": "Success"
        }
        state = MockGameState(extra={"test": True})

        result = process_reaction(
            entity=MockEntity("test"),
            config=config,
            accessor=MockAccessor(state),
            context={},
            spec=GIFT_SPEC
        )

        self.assertTrue(result.allow)
        self.assertEqual(result.feedback, "Success")
        self.assertTrue(state.extra.get("result"))

    def test_condition_failure_skips_effects(self):
        """Failed condition prevents effect application."""
        config = {
            "requires_flags": {"prereq": True},
            "set_flags": {"should_not_set": True},
            "failure_message": "Missing prerequisite"
        }
        state = MockGameState(extra={"prereq": False})

        result = process_reaction(
            entity=MockEntity("test"),
            config=config,
            accessor=MockAccessor(state),
            context={},
            spec=GIFT_SPEC
        )

        self.assertFalse(state.extra.get("should_not_set"))
        self.assertEqual(result.feedback, "Missing prerequisite")
```

### Effect Handler Tests

```python
class TestEffectHandlers(unittest.TestCase):
    def test_set_flags(self):
        """set_flags adds flags to game state."""
        config = {"set_flags": {"flag1": True, "flag2": "value"}}
        state = MockGameState()

        _set_flags(config, state, None, {})

        self.assertTrue(state.extra.get("flag1"))
        self.assertEqual(state.extra.get("flag2"), "value")

    def test_trust_delta_with_transitions(self):
        """trust_delta applies and triggers state transition at threshold."""
        entity = MockEntity("wolf", {
            "trust_state": {"current": 2, "floor": -5, "ceiling": 5},
            "state_machine": {"current": "wary", "states": ["wary", "friendly", "allied"]}
        })
        config = {
            "trust_delta": 2,
            "trust_transitions": {"3": "friendly", "5": "allied"}
        }
        state = MockGameState()

        _apply_trust_delta(config, state, entity, {})
        _apply_trust_transitions(config, state, entity, {})

        self.assertEqual(entity.properties["trust_state"]["current"], 4)
        self.assertEqual(entity.properties["state_machine"]["current"], "friendly")

    def test_effect_execution_order(self):
        """Effects execute in deterministic order."""
        entity = MockEntity("test", {"health": 50, "max_health": 100})
        config = {
            "apply_damage": 20,    # Applied first
            "heal_amount": 10,     # Applied second
        }
        state = MockGameState()

        # Execute in order
        for effect_key in EFFECT_ORDER:
            if effect_key in config:
                EFFECT_REGISTRY[effect_key](config, state, entity, {})

        # Damage applied first (50 - 20 = 30), then heal (30 + 10 = 40)
        self.assertEqual(entity.properties["health"], 40)
```

### Condition Checker Tests

```python
class TestConditionCheckers(unittest.TestCase):
    def test_requires_flags_all_match(self):
        """requires_flags passes when all flags match."""
        config = {"requires_flags": {"flag1": True, "flag2": "value"}}
        state = MockGameState(extra={"flag1": True, "flag2": "value"})

        result = _check_flags(config, state, None, {})

        self.assertTrue(result)

    def test_requires_flags_partial_match(self):
        """requires_flags fails when any flag doesn't match."""
        config = {"requires_flags": {"flag1": True, "flag2": "value"}}
        state = MockGameState(extra={"flag1": True, "flag2": "wrong"})

        result = _check_flags(config, state, None, {})

        self.assertFalse(result)

    def test_requires_not_flags_negated(self):
        """requires_not_flags is inverse of requires_flags."""
        config = {"requires_not_flags": {"flag": True}}
        state_with_flag = MockGameState(extra={"flag": True})
        state_without_flag = MockGameState(extra={"flag": False})

        self.assertFalse(_check_not_flags(config, state_with_flag, None, {}))
        self.assertTrue(_check_not_flags(config, state_without_flag, None, {}))
```

---

## Integration Tests

```python
class TestGiftReactionsIntegration(unittest.TestCase):
    def test_wolf_feeding_full_flow(self):
        """Wolf feeding: match → conditions → trust → transition → message."""
        wolf = create_wolf_with_gift_reactions()
        venison = create_item("venison")
        context = {"target_actor": wolf, "item": venison}

        # Initial state
        self.assertEqual(wolf.properties["trust_state"]["current"], 0)
        self.assertEqual(wolf.properties["state_machine"]["current"], "hostile")

        # Give venison
        result = on_gift_given(venison, self.accessor, context)

        # Verify effects
        self.assertEqual(wolf.properties["trust_state"]["current"], 1)
        self.assertTrue(self.accessor.game_state.extra.get("wolf_fed"))
        self.assertIn("wolf takes the venison", result.feedback.lower())

    def test_reject_message_for_wrong_item(self):
        """Wrong item triggers reject_message."""
        wolf = create_wolf_with_gift_reactions()
        rock = create_item("rock")
        context = {"target_actor": wolf, "item": rock}

        result = on_gift_given(rock, self.accessor, context)

        self.assertIn("wolf ignores", result.feedback.lower())
        self.assertEqual(wolf.properties["trust_state"]["current"], 0)  # No trust change
```

---

## Validation Tests

```python
class TestLoadTimeValidation(unittest.TestCase):
    def test_invalid_handler_path_caught(self):
        """Invalid handler path raises ValidationError at load."""
        entity = MockEntity("test", {
            "gift_reactions": {
                "handler": "nonexistent.module:function"
            }
        })

        with self.assertRaises(ValidationError) as cm:
            validate_handler_path(entity.id, "gift_reactions", "nonexistent.module:function")

        self.assertIn("Failed to import", str(cm.exception))

    def test_schema_validation_catches_typo(self):
        """Schema validation catches typo in field name."""
        entity = MockEntity("test", {
            "gift_reactions": {
                "food": {
                    "accepted_items": ["venison"],
                    "trust_deltaa": 1  # Typo: 'deltaa' instead of 'delta'
                }
            }
        })

        with self.assertRaises(ValidationError) as cm:
            validate_reaction_config(entity, "gift_reactions")

        self.assertIn("trust_deltaa", str(cm.exception))
        self.assertIn("not allowed", str(cm.exception))

    def test_cross_reference_validation_catches_missing_item(self):
        """Cross-reference validation catches reference to non-existent item."""
        entity = MockEntity("test", {
            "gift_reactions": {
                "food": {
                    "accepted_items": ["nonexistent_item"],
                }
            }
        })
        game_state = MockGameState(items=[])

        with self.assertWarns(UserWarning) as cm:
            validate_cross_references(entity, game_state)

        self.assertIn("nonexistent_item", str(cm.warning))
```

---

## Performance Tests

```python
class TestPerformance(unittest.TestCase):
    def test_interpreter_overhead_under_1ms(self):
        """Interpreter processes reaction in under 1ms."""
        config = {
            "set_flags": {"test": True},
            "trust_delta": 1,
            "message": "Test"
        }
        entity = MockEntity("test", {"trust_state": {"current": 0}})

        start = time.perf_counter()
        for _ in range(1000):
            process_reaction(entity, config, self.accessor, {}, GIFT_SPEC)
        end = time.perf_counter()

        avg_time = (end - start) / 1000
        self.assertLess(avg_time, 0.001)  # < 1ms per reaction

    def test_handler_caching_performance(self):
        """Handler loading is O(1) after first call."""
        handler_path = "behaviors.regions.beast_wilds.wolf_pack:on_receive_item"

        # First call: import (slow)
        start = time.perf_counter()
        handler1 = load_handler(handler_path)
        first_call = time.perf_counter() - start

        # Second call: cache hit (fast)
        start = time.perf_counter()
        handler2 = load_handler(handler_path)
        cached_call = time.perf_counter() - start

        self.assertIs(handler1, handler2)  # Same object
        self.assertLess(cached_call, first_call / 10)  # >10x faster
```

---

## Walkthrough Tests

All existing walkthroughs must pass:

```bash
$ python tools/walkthrough.py examples/big_game --file walkthroughs/test_wolf_feeding.txt
✓ All commands succeeded
✓ All assertions passed

$ python tools/walkthrough.py examples/big_game --file walkthroughs/test_sira_rescue.txt
✓ All commands succeeded
✓ All assertions passed

$ python tools/walkthrough.py examples/big_game --file walkthroughs/test_bear_cubs.txt
✓ All commands succeeded
✓ All assertions passed
```

---

## Test Coverage Goals

| Component | Target Coverage | Critical Paths |
|-----------|----------------|----------------|
| Interpreter core | >90% | All 3 phases, error handling |
| Effect handlers | >85% | All 18 effects, edge cases |
| Condition checkers | >85% | All 5 conditions, combinations |
| Infrastructure modules | >80% | Matching, dispatch, integration |
| Validation system | >90% | All 5 validation types |
| Template engine | >85% | All variable types, escaping |

**Overall target: >80% coverage for reaction system**

---

## Validation Checklist

Before deployment:

- [ ] All effect handlers unit tested
- [ ] All condition checkers unit tested
- [ ] Interpreter phases tested in isolation
- [ ] Integration tests for all 12 reaction types
- [ ] Load-time validation tests for all 5 types
- [ ] Performance tests show <1ms average
- [ ] All existing walkthroughs pass
- [ ] New walkthroughs created for new reaction types
- [ ] Schema validation catches typos
- [ ] Cross-reference validation catches broken links
- [ ] Handler path validation catches import errors
- [ ] Template substitution handles all variable types
- [ ] Error messages are actionable and clear
- [ ] No silent failures - all errors loud and immediate

---

# Appendix: Complete Reference Tables

## Effect Primitives (18 Total)

| Effect | Type | Description | Requirements | Example |
|--------|------|-------------|--------------|---------|
| `unset_flags` | `string[]` | Remove game flags | None | `["old_flag", "temp"]` |
| `set_flags` | `{string: any}` | Set game flags | None | `{"quest": "active"}` |
| `remove_condition` | `string` | Remove status effect | None | `"hypothermia"` |
| `apply_condition` | `ConditionSpec` | Apply status effect | None | `{"type": "poison", "severity": 2}` |
| `apply_damage` | `int` | Deal damage | Entity has health | `15` |
| `heal_amount` | `int` | Restore health | Entity has health | `30` |
| `trust_delta` | `int` | Modify trust | Entity has trust_state | `2` |
| `trust_transitions` | `{string: string}` | Auto-transition at thresholds | Entity has trust_state + state_machine | `{"3": "friendly"}` |
| `transition_to` | `string` | Change state | Entity has state_machine | `"hostile"` |
| `consume_item` | `bool` | Remove item from player | None | `true` |
| `grant_items` | `string[]` | Give items to player | Items exist | `["potion", "gold"]` |
| `spawn_items` | `string[]` | Create items in location | Item templates exist | `["treasure"]` |
| `grant_knowledge` | `string[]` | Add knowledge flags | None | `["clue_1", "hint_2"]` |
| `create_commitment` | `string` | Start commitment | Commitment config exists | `"commit_rescue"` |
| `fulfill_commitment` | `string` | Complete commitment | Active commitment exists | `"commit_rescue"` |
| `create_gossip` | `GossipSpec` | Add gossip | None | `{"topic": "news", "spread_to": ["town"]}` |
| `track_in` | `string` | Append to list | None | `"items_given"` |
| `increment_counter` | `string` | Increment counter | None | `"visit_count"` |

## Condition Primitives (5 Total)

| Condition | Type | Description | Example |
|-----------|------|-------------|---------|
| `requires_flags` | `{string: any}` | All flags must match | `{"quest_active": true, "level": 5}` |
| `requires_not_flags` | `{string: any}` | Flags must NOT match | `{"quest_done": true}` |
| `requires_state` | `string[]` | Entity in one of states | `["friendly", "allied"]` |
| `requires_trust` | `int` | Trust >= threshold | `3` |
| `requires_items` | `string[]` | Player has items | `["key", "torch"]` |

## Message Fields by Reaction Type

| Reaction Type | Primary | Fallback | Template Vars |
|---------------|---------|----------|---------------|
| gift | `accept_message` | `message` | `{item}`, `{target}`, `{trust}` |
| dialog | `summary` | `response` | `{keyword}`, `{state}`, `{trust}` |
| item_use | `response` | `message` | `{item}`, `{target}` |
| encounter | `encounter_message` | `message` | `{actor}`, `{location}` |
| death | `death_message` | `message` | `{entity}`, `{killer}` |
| combat | `message` | `response` | `{damage}`, `{attacker}`, `{weapon}` |
| entry | `message` | `entry_message` | `{from_direction}`, `{actor}` |
| turn_environmental | `message` | `tick_message` | `{turn}`, `{damage}` |
| commitment | `message` | `consequence_message` | `{commitment_id}`, `{state_change}` |
| take | `message` | `response` | `{item}`, `{count}` |
| examine | `message` | `reveal_message` | `{entity}`, `{examine_count}` |
| trade | `message` | `response` | `{item}`, `{vendor}`, `{transaction_type}` |

---

**END OF DESIGN DOCUMENT**

Total length: ~15,000 words
Comprehensive coverage: Architecture, implementation, validation, tooling, migration, testing
