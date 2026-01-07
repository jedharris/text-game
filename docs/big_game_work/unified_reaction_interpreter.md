# Unified Reaction Interpreter Design

**Status:** Design Document
**Date:** 2026-01-06
**Purpose:** Define a single parametrized interpreter for all reaction mini-languages

---

## Executive Summary

Replace 12 separate reaction processors with one unified interpreter that executes a declarative mini-language. The interpreter processes reaction configurations through three phases:

1. **Condition Evaluation:** Check `requires_*` predicates
2. **Effect Application:** Execute `set_*`, `grant_*`, `apply_*` operations
3. **Feedback Generation:** Return templated messages

This eliminates ~50% code duplication and creates a consistent semantic model across all entity interactions.

---

## Architecture Overview

### Core Principle

**All reactions are data transformations:**
`(GameState, Entity, Config) → (GameState', Feedback)`

The interpreter is a pure evaluator of declarative configurations. Complex logic escapes to Python handlers via `"handler": "module:function"`.

### Three-Phase Execution Model

```python
def process_reaction(
    entity: Any,           # Target entity (NPC, item, location)
    config: dict,          # Reaction configuration from entity.properties
    accessor: Any,         # StateAccessor instance
    context: dict,         # Event context (item, actor, etc.)
    spec: ReactionSpec     # Reaction type specification
) -> EventResult:

    # Phase 1: Evaluate conditions
    if not _evaluate_conditions(config, accessor.game_state, entity, context):
        return EventResult(allow=True, feedback=config.get("failure_message"))

    # Phase 2: Apply effects
    _apply_effects(config, accessor.game_state, entity, context)

    # Phase 3: Generate feedback
    message = _generate_feedback(config, context, spec)

    return EventResult(allow=True, feedback=message)
```

---

## Unified Mini-Language Specification

### Grammar Overview

```yaml
ReactionConfig:
  # Matching (varies by reaction type)
  accepted_items?: string[]        # Items that trigger this reaction
  keywords?: string[]              # Dialog keywords that trigger

  # Conditions (universal)
  requires_flags?: {flag: value}   # Game state flags must match
  requires_state?: string[]        # Entity state must be in list
  requires_trust?: int             # Entity trust must be >= value
  requires_items?: string[]        # Player must have items
  requires_not_flags?: {flag: value}  # Negated flag checks

  # Effects (universal - applied in order listed)
  set_flags?: {flag: value}        # Set game state flags
  unset_flags?: string[]           # Remove game state flags
  trust_delta?: int                # Modify entity trust
  trust_transitions?: {level: state}  # Auto-transition at trust thresholds
  transition_to?: string           # Change entity state
  apply_damage?: int               # Deal damage to entity
  heal_amount?: int                # Heal entity
  apply_condition?: ConditionSpec  # Apply status effect
  remove_condition?: string        # Remove status effect
  create_commitment?: string       # Start commitment timer
  fulfill_commitment?: string      # Mark commitment complete
  spawn_items?: string[]           # Create items in location
  grant_items?: string[]           # Add items to player inventory
  consume_item?: bool              # Remove item from player
  grant_knowledge?: string[]       # Add knowledge flags
  create_gossip?: GossipSpec       # Add gossip to queue
  track_in?: string                # Append to list in game_state.extra
  increment_counter?: string       # game_state.extra[key] += 1

  # Feedback (varies by reaction type)
  message?: string                 # Generic message template
  accept_message?: string          # Gift/item accepted
  reject_message?: string          # Gift/item rejected
  response?: string                # Dialog/item use response
  summary?: string                 # Dialog topic summary
  encounter_message?: string       # First encounter
  death_message?: string           # Death consequence
  failure_message?: string         # Condition check failed

  # Escape hatch
  handler?: string                 # "module.path:function_name"

# Complex nested types
ConditionSpec:
  type: string                     # "hypothermia", "spore_infection", etc.
  severity?: int                   # Condition intensity
  duration?: int                   # Turns until expires

GossipSpec:
  topic: string                    # Gossip identifier
  spread_to?: string[]             # Location IDs to spread
  priority?: int                   # Queue priority
```

### Message Template Syntax

All message fields support substitution:

```python
# Context variables available:
{item}          # Item ID being given/used
{actor}         # Actor performing action
{target}        # Target entity
{trust}         # Current trust level
{state}         # Current entity state
{count}         # For counters/tracking
{damage}        # For combat
{custom.X}      # Custom context values

# Example:
"accept_message": "The {target} accepts your {item} gratefully (trust: {trust})"
```

---

## Reaction Type Specifications

Each reaction type provides a `ReactionSpec` that parametrizes the interpreter:

```python
@dataclass
class ReactionSpec:
    """Specification for a reaction type."""
    reaction_type: str              # "gift", "dialog", "item_use", etc.
    message_key: str                # Primary message field name
    fallback_message_key: str       # Secondary message field
    match_strategy: MatchStrategy   # How to find applicable reactions
    context_enrichment: Callable    # Add reaction-specific context
```

### 1. gift_reactions

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
    }
  }
}
```

---

### 2. dialog_reactions

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

### 3. item_use_reactions

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

### 4. encounter_reactions

```python
ENCOUNTER_SPEC = ReactionSpec(
    reaction_type="encounter",
    message_key="encounter_message",
    fallback_message_key="message",
    match_strategy=NoMatchStrategy(),  # Triggered on location entry
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

**Note:** encounter_reactions is a single config object, not a dict of named reactions, because encounters don't need matching - they trigger once on location entry.

---

### 5. death_reactions

```python
DEATH_SPEC = ReactionSpec(
    reaction_type="death",
    message_key="death_message",
    fallback_message_key="message",
    match_strategy=NoMatchStrategy(),  # Triggered when health reaches 0
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

**Special Case - Handler for Puzzle Logic:**
```python
# golem_puzzle.py
def check_both_golems_dead(entity, accessor, context):
    """Custom handler: unlock passage if both golems defeated."""
    state = accessor.game_state
    if state.extra.get("golem_1_dead") and state.extra.get("golem_2_dead"):
        # Unlock the hidden passage
        unlock_exit(state, "frozen_chamber", "hidden_passage", "secret_vault")
        return EventResult(
            allow=True,
            feedback="With both guardians fallen, a hidden passage grinds open in the wall."
        )
    return EventResult(allow=True, feedback=None)
```

---

### 6. combat_reactions

```python
COMBAT_SPEC = ReactionSpec(
    reaction_type="combat",
    message_key="message",
    fallback_message_key="response",
    match_strategy=NoMatchStrategy(),  # Triggered on damage dealt/taken
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
    },
    "resistances": {
      "fire_damage_multiplier": 0.5,
      "ice_damage_multiplier": 2.0,
      "physical_damage_multiplier": 1.0
    }
  }
}
```

**Note:** combat_reactions may need custom structure for damage modifiers - this is a candidate for handler-heavy implementation.

---

### 7. entry_reactions

```python
ENTRY_SPEC = ReactionSpec(
    reaction_type="entry",
    message_key="message",
    fallback_message_key="entry_message",
    match_strategy=NoMatchStrategy(),  # Triggered on location entry
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

### 8. turn_environmental

```python
TURN_ENV_SPEC = ReactionSpec(
    reaction_type="turn_environmental",
    message_key="message",
    fallback_message_key="tick_message",
    match_strategy=NoMatchStrategy(),  # Triggered each turn
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

### 9. commitment_reactions

```python
COMMITMENT_SPEC = ReactionSpec(
    reaction_type="commitment",
    message_key="message",
    fallback_message_key="consequence_message",
    match_strategy=NoMatchStrategy(),  # Triggered on commitment state change
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "commitment_id": ctx.get("commitment_id", ""),
        "state_change": ctx.get("state_change", "")  # "fulfilled" or "abandoned"
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

### 10. take_reactions

```python
TAKE_SPEC = ReactionSpec(
    reaction_type="take",
    message_key="message",
    fallback_message_key="response",
    match_strategy=NoMatchStrategy(),  # Triggered when item taken
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

**Depletion Tracking:**
```json
{
  "take_reactions": {
    "increment_counter": "ice_fragments_taken",
    "message": "You extract another ice fragment. ({count} taken)",
    "handler": "behaviors.regions.frozen_reaches.ice_extraction:check_depletion"
  }
}
```

---

### 11. examine_reactions

```python
EXAMINE_SPEC = ReactionSpec(
    reaction_type="examine",
    message_key="message",
    fallback_message_key="reveal_message",
    match_strategy=NoMatchStrategy(),  # Triggered on examine
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
        "message": "The telescope is encased in thick magical ice. The ice seems to pulse with inner warmth - paradoxically, it's warm to the touch.",
        "grant_knowledge": ["ice_puzzle_hint_1"],
        "set_flags": {"telescope_examined_once": true}
      },
      {
        "requires_flags": {"telescope_examined_once": true},
        "requires_not_flags": {"telescope_solution_known": true},
        "message": "Looking closer at the warm ice, you realize: this ice needs heat to melt it, not cold. A source of intense heat might work.",
        "grant_knowledge": ["ice_puzzle_solution"],
        "set_flags": {"telescope_solution_known": true}
      }
    ]
  }
}
```

---

### 12. trade_reactions

```python
TRADE_SPEC = ReactionSpec(
    reaction_type="trade",
    message_key="message",
    fallback_message_key="response",
    match_strategy=ItemMatchStrategy("item"),  # Match on item being bought/sold
    context_enrichment=lambda ctx, cfg: {
        **ctx,
        "item": ctx.get("item", ""),
        "vendor": ctx.get("vendor").id if ctx.get("vendor") else "",
        "transaction_type": ctx.get("transaction_type", "buy")  # "buy" or "sell"
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

## Implementation Architecture

### Directory Structure

```
behaviors/shared/infrastructure/
├── reaction_interpreter.py          # Core interpreter (Phase 1-3)
├── reaction_effects.py               # Effect handlers registry
├── reaction_conditions.py            # Condition checkers registry
├── reaction_specs.py                 # ReactionSpec definitions
├── match_strategies.py               # Item/keyword matching logic
└── message_templates.py              # Template substitution

# Each reaction infrastructure module becomes thin:
behaviors/shared/infrastructure/
├── gift_reactions.py                 # 30 lines (spec + dispatcher)
├── dialog_reactions.py               # 30 lines
├── item_use_reactions.py             # 30 lines
├── encounter_reactions.py            # 30 lines
├── death_reactions.py                # 30 lines
├── combat_reactions.py               # 40 lines (more complex matching)
├── entry_reactions.py                # 20 lines
├── turn_environmental.py             # 25 lines
├── commitment_reactions.py           # 35 lines
├── take_reactions.py                 # 25 lines
├── examine_reactions.py              # 30 lines
└── trade_reactions.py                # 45 lines (inventory management)
```

### Core Interpreter API

```python
# reaction_interpreter.py

def process_reaction(
    entity: Any,
    config: dict[str, Any],
    accessor: Any,
    context: dict[str, Any],
    spec: ReactionSpec,
) -> EventResult:
    """Universal reaction interpreter.

    Args:
        entity: Target entity (NPC, item, location)
        config: Single reaction configuration (NOT the full reactions dict)
        accessor: StateAccessor instance
        context: Event context from hook
        spec: ReactionSpec for this reaction type

    Returns:
        EventResult with feedback
    """
    state = accessor.game_state

    # Enrich context with reaction-specific values
    if spec.context_enrichment:
        context = spec.context_enrichment(context, config)

    # Phase 1: Evaluate all conditions
    for condition_key in CONDITION_REGISTRY.keys():
        if condition_key in config:
            if not CONDITION_REGISTRY[condition_key](config, state, entity, context):
                return EventResult(
                    allow=True,
                    feedback=config.get("failure_message")
                )

    # Phase 2: Apply all effects (order matters!)
    effect_order = [
        "unset_flags",          # Clear flags first
        "set_flags",            # Then set new flags
        "remove_condition",     # Remove conditions before applying
        "apply_condition",      # Apply new conditions
        "apply_damage",         # Damage before healing
        "heal_amount",          # Healing
        "trust_delta",          # Trust changes
        "trust_transitions",    # State transitions from trust
        "transition_to",        # Explicit state transitions
        "consume_item",         # Remove items
        "grant_items",          # Grant items
        "spawn_items",          # Create items in world
        "grant_knowledge",      # Grant knowledge
        "create_commitment",    # Start commitments
        "fulfill_commitment",   # Complete commitments
        "create_gossip",        # Add gossip
        "track_in",             # Track in lists
        "increment_counter",    # Increment counters
    ]

    for effect_key in effect_order:
        if effect_key in config:
            EFFECT_REGISTRY[effect_key](config, state, entity, context)

    # Phase 3: Generate feedback
    message = _get_message(config, spec)
    if message:
        message = substitute_templates(message, context)

    return EventResult(allow=True, feedback=message if message else None)


def find_matching_reaction(
    reactions_config: dict[str, Any],
    context: dict[str, Any],
    spec: ReactionSpec,
) -> tuple[str, dict[str, Any]] | None:
    """Find which reaction in config matches the context.

    Args:
        reactions_config: Full reactions dict from entity.properties
        context: Event context
        spec: ReactionSpec with match strategy

    Returns:
        (reaction_name, reaction_config) or None
    """
    return spec.match_strategy.find_match(reactions_config, context)
```

### Effect Registry

```python
# reaction_effects.py

from typing import Any, Callable

EffectHandler = Callable[[dict, Any, Any, dict], None]

EFFECT_REGISTRY: dict[str, EffectHandler] = {
    "set_flags": _set_flags,
    "unset_flags": _unset_flags,
    "trust_delta": _apply_trust_delta,
    "trust_transitions": _apply_trust_transitions,
    "transition_to": _transition_state,
    "apply_damage": _apply_damage,
    "heal_amount": _heal_entity,
    "apply_condition": _apply_condition,
    "remove_condition": _remove_condition,
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

def _set_flags(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Set game state flags."""
    flags = config.get("set_flags", {})
    for flag_name, flag_value in flags.items():
        state.extra[flag_name] = flag_value

def _unset_flags(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Remove game state flags."""
    flags = config.get("unset_flags", [])
    for flag_name in flags:
        state.extra.pop(flag_name, None)

def _apply_trust_delta(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Apply trust change to entity."""
    trust_delta = config.get("trust_delta", 0)
    if trust_delta and hasattr(entity, "properties"):
        # Initialize trust_state if missing
        if "trust_state" not in entity.properties:
            entity.properties["trust_state"] = {"current": 0, "floor": -5, "ceiling": 5}

        from src.infrastructure_utils import apply_trust_change
        apply_trust_change(
            entity=entity,
            delta=trust_delta,
            transitions={}  # Transitions handled separately
        )

def _apply_trust_transitions(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Check trust thresholds and auto-transition states."""
    transitions = config.get("trust_transitions", {})
    if not transitions or not hasattr(entity, "properties"):
        return

    trust = entity.properties.get("trust_state", {}).get("current", 0)
    sm = entity.properties.get("state_machine")

    if not sm:
        return

    # Check each threshold (sorted)
    for threshold_str, target_state in sorted(transitions.items(), key=lambda x: int(x[0])):
        threshold = int(threshold_str)
        if trust >= threshold:
            from src.infrastructure_utils import transition_state
            transition_state(sm, target_state)
            break  # Only transition to highest threshold met

def _transition_state(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Explicitly transition entity state."""
    new_state = config.get("transition_to")
    if new_state and hasattr(entity, "properties"):
        sm = entity.properties.get("state_machine")
        if sm:
            from src.infrastructure_utils import transition_state
            transition_state(sm, new_state)

def _apply_damage(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Deal damage to entity."""
    damage = config.get("apply_damage", 0)
    if damage and hasattr(entity, "properties"):
        health = entity.properties.get("health", 100)
        entity.properties["health"] = max(0, health - damage)
        context["damage"] = damage  # For message templates

def _heal_entity(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Heal entity."""
    heal = config.get("heal_amount", 0)
    if heal and hasattr(entity, "properties"):
        health = entity.properties.get("health", 100)
        max_health = entity.properties.get("max_health", 100)
        entity.properties["health"] = min(max_health, health + heal)
        context["heal"] = heal  # For message templates

def _apply_condition(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Apply status condition to entity."""
    condition_spec = config.get("apply_condition")
    if not condition_spec:
        return

    # Add to entity's active conditions
    if not hasattr(entity, "properties"):
        return

    conditions = entity.properties.setdefault("active_conditions", {})
    condition_type = condition_spec["type"]
    conditions[condition_type] = {
        "severity": condition_spec.get("severity", 1),
        "duration": condition_spec.get("duration", -1),  # -1 = permanent
        "applied_turn": state.extra.get("turn_number", 0)
    }

def _remove_condition(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Remove status condition from entity."""
    condition_type = config.get("remove_condition")
    if condition_type and hasattr(entity, "properties"):
        conditions = entity.properties.get("active_conditions", {})
        conditions.pop(condition_type, None)

def _consume_item(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Remove item from player inventory."""
    if not config.get("consume_item"):
        return

    item = context.get("item")
    if item and hasattr(state, "player"):
        # Remove from player inventory
        state.player.inventory = [i for i in state.player.inventory if i.id != item]

def _grant_items(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Add items to player inventory."""
    item_ids = config.get("grant_items", [])
    for item_id in item_ids:
        # Find item in game state
        item = next((i for i in state.items if i.id == item_id), None)
        if item and hasattr(state, "player"):
            state.player.inventory.append(item)

def _spawn_items(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Create items in location."""
    item_ids = config.get("spawn_items", [])
    location = context.get("location") or getattr(entity, "location", None)

    if not location:
        return

    for item_id in item_ids:
        # Create new item instance
        item = next((i for i in state.items if i.id == item_id), None)
        if item:
            # Clone item and place in location
            import copy
            new_item = copy.deepcopy(item)
            new_item.location = location if isinstance(location, str) else location.id
            state.items.append(new_item)

def _grant_knowledge(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Add knowledge flags to player."""
    knowledge_ids = config.get("grant_knowledge", [])
    knowledge_set = state.extra.setdefault("knowledge", set())
    if isinstance(knowledge_set, list):
        knowledge_set = set(knowledge_set)
        state.extra["knowledge"] = knowledge_set

    for k_id in knowledge_ids:
        knowledge_set.add(k_id)

def _create_commitment(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Start a commitment timer."""
    commitment_id = config.get("create_commitment")
    if commitment_id:
        from src.infrastructure_utils import create_commitment, get_current_turn
        current_turn = get_current_turn(state)
        create_commitment(state, commitment_id, current_turn)

def _fulfill_commitment(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Mark commitment as fulfilled."""
    commitment_id = config.get("fulfill_commitment")
    if commitment_id:
        # Find commitment in active_commitments
        for commitment in state.extra.get("active_commitments", []):
            if commitment.get("id") == commitment_id:
                commitment["state"] = "fulfilled"
                break

def _create_gossip(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Add gossip to propagation queue."""
    gossip_spec = config.get("create_gossip")
    if not gossip_spec:
        return

    gossip_queue = state.extra.setdefault("gossip_queue", [])
    gossip_queue.append({
        "topic": gossip_spec["topic"],
        "spread_to": gossip_spec.get("spread_to", []),
        "priority": gossip_spec.get("priority", 1),
        "created_turn": state.extra.get("turn_number", 0)
    })

def _track_in_list(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Append value to a list in game_state.extra."""
    list_key = config.get("track_in")
    if not list_key:
        return

    tracked_list = state.extra.setdefault(list_key, [])

    # Determine what to track (context-dependent)
    value = context.get("item") or context.get("keyword") or context.get("entity")
    if value and value not in tracked_list:
        tracked_list.append(value)

    context["count"] = len(tracked_list)  # For message templates

def _increment_counter(config: dict, state: Any, entity: Any, context: dict) -> None:
    """Increment a counter in game_state.extra."""
    counter_key = config.get("increment_counter")
    if counter_key:
        current = state.extra.get(counter_key, 0)
        state.extra[counter_key] = current + 1
        context["count"] = current + 1  # For message templates
```

### Condition Registry

```python
# reaction_conditions.py

from typing import Any, Callable

ConditionChecker = Callable[[dict, Any, Any, dict], bool]

CONDITION_REGISTRY: dict[str, ConditionChecker] = {
    "requires_flags": _check_flags,
    "requires_not_flags": _check_not_flags,
    "requires_state": _check_state,
    "requires_trust": _check_trust,
    "requires_items": _check_items,
}

def _check_flags(config: dict, state: Any, entity: Any, context: dict) -> bool:
    """Check if all required flags match."""
    required = config.get("requires_flags", {})
    return all(state.extra.get(k) == v for k, v in required.items())

def _check_not_flags(config: dict, state: Any, entity: Any, context: dict) -> bool:
    """Check if flags DO NOT match (negated check)."""
    forbidden = config.get("requires_not_flags", {})
    return all(state.extra.get(k) != v for k, v in forbidden.items())

def _check_state(config: dict, state: Any, entity: Any, context: dict) -> bool:
    """Check if entity is in one of required states."""
    required_states = config.get("requires_state", [])
    if not required_states or not hasattr(entity, "properties"):
        return True

    sm = entity.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", ""))
    return current_state in required_states

def _check_trust(config: dict, state: Any, entity: Any, context: dict) -> bool:
    """Check if entity trust meets minimum threshold."""
    required_trust = config.get("requires_trust")
    if required_trust is None or not hasattr(entity, "properties"):
        return True

    trust_state = entity.properties.get("trust_state", {})
    current_trust = trust_state.get("current", 0)
    return current_trust >= required_trust

def _check_items(config: dict, state: Any, entity: Any, context: dict) -> bool:
    """Check if player has required items."""
    required_items = config.get("requires_items", [])
    if not required_items or not hasattr(state, "player"):
        return True

    player_items = {item.id for item in state.player.inventory}
    return all(item_id in player_items for item_id in required_items)
```

---

## Migration Strategy

### Phase 1: Build Core Infrastructure (1-2 days)
1. Create `reaction_interpreter.py` with core 3-phase execution
2. Create `reaction_effects.py` with effect registry
3. Create `reaction_conditions.py` with condition registry
4. Create `reaction_specs.py` with all 12 ReactionSpec definitions
5. Create `match_strategies.py` with matching logic
6. Create `message_templates.py` with substitution

### Phase 2: Migrate Existing Reactions (2-3 days)
1. **gift_reactions.py** - Already exists, refactor to use interpreter
2. **item_use_reactions.py** - Already exists, refactor to use interpreter
3. **dialog_reactions.py** - Partially exists, complete and refactor
4. Update all entity configurations in game_state.json

### Phase 3: Create New Reaction Types (2-3 days)
5. **encounter_reactions.py** - New infrastructure
6. **death_reactions.py** - New infrastructure
7. **combat_reactions.py** - New infrastructure
8. **entry_reactions.py** - New infrastructure
9. **turn_environmental.py** - Refactor existing
10. **commitment_reactions.py** - New infrastructure
11. **take_reactions.py** - New infrastructure
12. **examine_reactions.py** - New infrastructure (optional)
13. **trade_reactions.py** - New infrastructure

### Phase 4: Testing & Validation (1-2 days)
1. Write comprehensive tests for interpreter
2. Write tests for each effect handler
3. Write tests for each condition checker
4. Run all existing walkthroughs
5. Create walkthroughs for new reaction types

**Total Estimated Effort: 6-10 days**

---

## Testing Strategy

### Unit Tests

```python
# tests/infrastructure/test_reaction_interpreter.py

class TestReactionInterpreter(unittest.TestCase):
    def test_set_flags_effect(self):
        """set_flags adds flags to game state."""
        config = {"set_flags": {"test_flag": True}}
        state = MockGameState()

        _set_flags(config, state, None, {})

        self.assertTrue(state.extra.get("test_flag"))

    def test_requires_flags_condition(self):
        """requires_flags checks game state flags."""
        config = {"requires_flags": {"prereq": True}}
        state = MockGameState(extra={"prereq": True})

        result = _check_flags(config, state, None, {})

        self.assertTrue(result)

    def test_trust_delta_with_transitions(self):
        """trust_delta applies and triggers state transition."""
        entity = MockEntity("wolf", {
            "trust_state": {"current": 2},
            "state_machine": {"current": "wary", "states": ["wary", "friendly"]}
        })
        config = {
            "trust_delta": 2,
            "trust_transitions": {"3": "friendly"}
        }
        state = MockGameState()

        _apply_trust_delta(config, state, entity, {})
        _apply_trust_transitions(config, state, entity, {})

        self.assertEqual(entity.properties["trust_state"]["current"], 4)
        self.assertEqual(entity.properties["state_machine"]["current"], "friendly")
```

### Integration Tests

```python
# tests/infrastructure/test_gift_reactions_integration.py

class TestGiftReactionsIntegration(unittest.TestCase):
    def test_wolf_feeding_full_flow(self):
        """Wolf feeding: item match → trust delta → state transition → message."""
        wolf = create_wolf_entity()
        venison = create_item("venison")
        config = wolf.properties["gift_reactions"]["food"]
        context = {"target_actor": wolf, "item": venison}

        result = process_reaction(
            entity=wolf,
            config=config,
            accessor=self.accessor,
            context=context,
            spec=GIFT_SPEC
        )

        # Verify trust increased
        self.assertEqual(wolf.properties["trust_state"]["current"], 1)

        # Verify message generated
        self.assertIn("wolf takes the venison", result.feedback.lower())

        # Verify flags set
        self.assertTrue(self.accessor.game_state.extra.get("wolf_fed"))
```

---

## Validation Checklist

Before deployment, validate:

- [ ] All 12 reaction specs defined
- [ ] All effect handlers implemented and tested
- [ ] All condition checkers implemented and tested
- [ ] Message template substitution works for all variables
- [ ] Handler escape hatch works for all reaction types
- [ ] Load-time validation catches invalid configs
- [ ] Existing walkthroughs pass with new interpreter
- [ ] New walkthroughs created for new reaction types
- [ ] Performance testing (interpreter overhead < 1ms per reaction)
- [ ] Documentation complete for all mini-language primitives

---

## Open Questions

1. **Combat damage modifiers:** Should `combat_reactions` use interpreter or custom handler?
   - **Recommendation:** Start with handler-only, migrate to interpreter later if pattern emerges

2. **Progressive examine reveals:** Should this be array-based or nested reactions?
   - **Recommendation:** Use array with indexed matching based on examine_count

3. **Trade inventory management:** Should stock tracking be automatic or explicit?
   - **Recommendation:** Automatic via interpreter effect handler

4. **Commitment lifecycle:** Should fulfilled/abandoned be separate configs or unified?
   - **Recommendation:** Unified dict with "fulfilled" and "abandoned" keys (like combat_reactions)

---

## Success Criteria

✅ Single `process_reaction()` function handles all 12 reaction types
✅ Effect handlers are composable and reusable
✅ Adding new effect types requires only registry update
✅ Entity configs are 100% declarative (no mixed Python/JSON)
✅ Handler escape hatch preserves full flexibility
✅ Code reduction: ~50% fewer lines vs. current implementation
✅ All existing behaviors work identically after migration
✅ New reaction types can be added in < 1 hour

---

## Appendix: Complete Effect/Condition Reference

### Effects (Applied in Order)

| Effect | Type | Description | Example |
|--------|------|-------------|---------|
| `unset_flags` | `string[]` | Remove game flags | `["old_flag"]` |
| `set_flags` | `{string: any}` | Set game flags | `{"flag": true}` |
| `remove_condition` | `string` | Remove status effect | `"hypothermia"` |
| `apply_condition` | `ConditionSpec` | Apply status effect | `{"type": "poisoned", "severity": 2}` |
| `apply_damage` | `int` | Deal damage | `15` |
| `heal_amount` | `int` | Restore health | `30` |
| `trust_delta` | `int` | Modify trust | `2` |
| `trust_transitions` | `{string: string}` | Auto-transition at thresholds | `{"3": "friendly"}` |
| `transition_to` | `string` | Change state | `"hostile"` |
| `consume_item` | `bool` | Remove item from player | `true` |
| `grant_items` | `string[]` | Give items to player | `["potion", "gold"]` |
| `spawn_items` | `string[]` | Create items in location | `["treasure"]` |
| `grant_knowledge` | `string[]` | Add knowledge flags | `["clue_1"]` |
| `create_commitment` | `string` | Start commitment | `"commit_rescue"` |
| `fulfill_commitment` | `string` | Complete commitment | `"commit_rescue"` |
| `create_gossip` | `GossipSpec` | Add gossip | `{"topic": "news"}` |
| `track_in` | `string` | Append to list | `"items_given"` |
| `increment_counter` | `string` | Increment counter | `"visit_count"` |

### Conditions (All Must Pass)

| Condition | Type | Description | Example |
|-----------|------|-------------|---------|
| `requires_flags` | `{string: any}` | Flags must match | `{"flag": true}` |
| `requires_not_flags` | `{string: any}` | Flags must NOT match | `{"flag": true}` |
| `requires_state` | `string[]` | Entity in state list | `["friendly", "allied"]` |
| `requires_trust` | `int` | Trust >= threshold | `3` |
| `requires_items` | `string[]` | Player has items | `["key", "torch"]` |

### Message Fields (By Reaction Type)

| Reaction Type | Primary Message | Fallback | Template Vars |
|---------------|----------------|----------|---------------|
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
