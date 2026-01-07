# Reaction System Architecture - Property-Based Approach

**Status:** Design Sketch
**Date:** 2026-01-06
**Purpose:** Define unified reaction system to replace mixed vocabulary/property approaches

---

## Architecture Overview

### Core Principle
**Local dispatch via entity properties with comprehensive load-time validation**

Entity properties declare reaction handlers → Infrastructure reads properties and calls handlers directly → Only relevant handler executes (O(1) dispatch).

---

## Infrastructure Modules Required

Each reaction pattern requires dedicated infrastructure module following this template:

```python
# infrastructure/<reaction_type>_reactions.py

vocabulary = {
    "hook_definitions": [{
        "hook_id": "entity_<action>_<event>",
        "invocation": "entity",
        "description": "Called when <event> happens to entity"
    }],
    "events": [{
        "event": "on_<event>",
        "hook": "entity_<action>_<event>",
        "description": "Handle entity reactions to <event>"
    }]
}

def on_<event>(entity, accessor, context):
    """Infrastructure dispatcher for <reaction_type>."""
    # 1. Extract target entity from context
    target = context.get("target") or entity

    # 2. Check for reaction configuration
    reaction_config = target.properties.get("<reaction_type>_reactions")
    if not reaction_config:
        return EventResult(allow=True, feedback=None)

    # 3. Check for handler escape hatch
    handler_path = reaction_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)  # Validated at load time
        return handler(entity, accessor, context)

    # 4. OR process data-driven config
    return _process_data_driven_config(target, reaction_config, context)
```

---

## Complete Infrastructure Module List

Based on full game interaction inventory:

### 1. gift_reactions.py ✅ EXISTS
- **Trigger:** `give <item> to <npc>`
- **Entities:** alpha_wolf, salamander, bee_queen, dire_bear, spore_mother
- **Data-driven:** accepted_items, trust_delta, state_transitions, set_flags
- **Handler option:** Custom logic for complex gift responses

### 2. encounter_reactions.py ⚠️ NEEDS CREATION
- **Trigger:** First time player enters location with NPC OR first examine/interact
- **Entities:** hunter_sira, dire_bear, merchant_delvan, npc_myconid_elder
- **Data-driven:** encounter_message, set_flags, create_commitment
- **Handler option:** Complex encounter logic (commitment creation, state changes)

### 3. death_reactions.py ⚠️ NEEDS CREATION
- **Trigger:** Entity health reaches 0 OR special death conditions
- **Entities:** stone_golem_1/2, hunter_sira, spider_matriarch, sailor_garrett, merchant_delvan, npc_spore_mother
- **Data-driven:** death_message, create_gossip, set_flags, unlock_passage
- **Handler option:** Complex death consequences (simultaneous golem check, gossip creation)

### 4. item_use_reactions.py ⚠️ NEEDS CREATION
- **Trigger:** `use <item> on <target>`
- **Entities:** telescope, ice_wall, mushroom_patch, npc_aldric, dire_bear/cubs
- **Data-driven:** accepted_items, consume_item, state_change, set_flags, grant_items
- **Handler option:** Multi-step puzzles, condition curing, complex transformations

### 5. dialog_reactions.py ⚠️ NEEDS CREATION
- **Trigger:** `talk to <npc>` OR `ask <npc> about <topic>`
- **Entities:** the_echo, salamander, stone_golem, hunter_sira, bee_queen, npc_aldric, npc_spore_mother, npc_myconid_elder, vendors
- **Data-driven:** dialog_topics with responses, trust_changes, knowledge_grants
- **Handler option:** Complex dialog trees, trust-gated responses, multi-step conversations

### 6. combat_reactions.py ⚠️ NEEDS CREATION
- **Trigger:** `attack <target>` OR damage dealt/received
- **Entities:** stone_golem_1/2 (puzzle), spider_nest (spawn tracking), thermal_shock (environmental)
- **Data-driven:** damage_modifiers, counter_attack, death_threshold
- **Handler option:** Puzzle tracking (simultaneous golem damage), environmental effects

### 7. entry_reactions.py ⚠️ NEEDS CREATION
- **Trigger:** `go <direction>` → enter new location
- **Entities:** Locations with temperature_zone, spore_density, water_level, web_effects
- **Data-driven:** apply_condition, environmental_message, movement_penalty
- **Handler option:** Complex entry consequences (commitment triggers, environmental checks)

### 8. turn_environmental.py ✅ EXISTS (partial)
- **Trigger:** Per-turn phase for environmental effects
- **Entities:** Locations with cold, spore, water effects
- **Data-driven:** condition_tick, damage_per_turn, condition_threshold
- **Handler option:** Complex environmental progression

### 9. commitment_reactions.py ⚠️ NEEDS CREATION
- **Trigger:** Commitment state changes (created, fulfilled, abandoned)
- **Entities:** npc_aldric, hunter_sira, dire_bear, sailor_garrett, merchant_delvan
- **Data-driven:** commitment_config reference, fulfillment_flags, failure_consequences
- **Handler option:** Complex commitment logic (dual rescue choice, cascading failures)

### 10. take_reactions.py ⚠️ NEEDS CREATION
- **Trigger:** `take <item>` from location
- **Entities:** ice_fragment (resource tracking), royal_honey (theft detection)
- **Data-driven:** extraction_count, permission_check, consequences
- **Handler option:** Complex take logic (resource depletion, theft consequences)

### 11. examine_reactions.py ⚠️ NEEDS CREATION (optional)
- **Trigger:** `examine <entity>` OR `observe <entity>`
- **Entities:** telescope, cave_ceiling, various puzzle elements
- **Data-driven:** reveal_message, grant_knowledge, update_description
- **Handler option:** Progressive revelation, puzzle clues

### 12. trade_reactions.py ⚠️ NEEDS CREATION
- **Trigger:** `buy <item> from <vendor>` OR `sell <item> to <vendor>`
- **Entities:** herbalist_maren, weaponsmith_toran, curiosity_dealer_vex
- **Data-driven:** inventory, prices, reputation_modifiers
- **Handler option:** Dynamic pricing, reputation checks, special transactions

---

## Load-Time Validation System

All reaction configurations validated at game load using these checks:

### Handler Path Validation
```python
def validate_handler_path(entity_id, reaction_type, handler_path):
    """Validate handler can be loaded and has correct signature."""
    try:
        module_path, func_name = handler_path.split(':')
        module = import_module(module_path)
        handler = getattr(module, func_name)

        # Check signature
        sig = inspect.signature(handler)
        params = list(sig.parameters.keys())
        if params != ["entity", "accessor", "context"]:
            raise TypeError(f"Handler {handler_path} has invalid signature")

        # Check return type annotation
        hints = get_type_hints(handler)
        if hints.get("return").__name__ != "EventResult":
            raise TypeError(f"Handler {handler_path} must return EventResult")

    except Exception as e:
        raise ValidationError(
            f"Entity '{entity_id}' {reaction_type} handler invalid: {e}"
        )
```

### Schema Validation
```python
# JSON schemas for each reaction type
GIFT_REACTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "handler": {"type": "string", "pattern": r"^[\w\.]+:\w+$"},
        "reject_message": {"type": "string"}
    },
    "patternProperties": {
        "^[a-z_]+$": {
            "type": "object",
            "properties": {
                "accepted_items": {"type": "array", "items": {"type": "string"}},
                "trust_delta": {"type": "integer"},
                "trust_transitions": {"type": "object"},
                "set_flags": {"type": "object"}
            },
            "additionalProperties": False,
            "required": ["accepted_items"]
        }
    }
}

# Validate at load time
jsonschema.validate(entity.properties["gift_reactions"], GIFT_REACTIONS_SCHEMA)
```

### Cross-Reference Validation
```python
def validate_cross_references(entity, game_state):
    """Validate referenced entities exist."""
    if "gift_reactions" in entity.properties:
        for reaction in entity.properties["gift_reactions"].values():
            if "accepted_items" in reaction:
                for item_id in reaction["accepted_items"]:
                    if not game_state.get_item(item_id):
                        warnings.warn(
                            f"Entity {entity.id} accepts unknown item '{item_id}'"
                        )

    if "state_machine" in entity.properties:
        for reaction_type in ["gift_reactions", "encounter_reactions"]:
            if reaction_type in entity.properties:
                reaction = entity.properties[reaction_type]
                if "trust_transitions" in reaction:
                    for trust_level, state_name in reaction["trust_transitions"].items():
                        valid_states = entity.properties["state_machine"]["states"]
                        if state_name not in valid_states:
                            raise ValidationError(
                                f"Entity {entity.id} {reaction_type} references "
                                f"non-existent state '{state_name}'"
                            )
```

### Entity Capability Validation
```python
def validate_entity_capabilities(entity):
    """Ensure entity type supports reaction types."""
    entity_type = "actor" if entity.id in game_state.actors else \
                  "item" if entity in game_state.items else "location"

    # Define valid reaction types per entity type
    VALID_REACTIONS = {
        "actor": ["gift_reactions", "encounter_reactions", "death_reactions",
                 "dialog_reactions", "combat_reactions"],
        "item": ["item_use_reactions", "take_reactions", "examine_reactions"],
        "location": ["entry_reactions", "turn_environmental"]
    }

    for reaction_type in entity.properties.keys():
        if reaction_type.endswith("_reactions"):
            if reaction_type not in VALID_REACTIONS[entity_type]:
                raise ValidationError(
                    f"{entity_type.title()} '{entity.id}' cannot have {reaction_type}. "
                    f"Valid: {VALID_REACTIONS[entity_type]}"
                )
```

---

## Discoverability Tooling

### entity_inspector.py
```bash
$ python tools/entity_inspector.py alpha_wolf

Entity: alpha_wolf (Actor)
Location: wolf_clearing

Reactions:
  ✓ gift_reactions (food) → beast_wilds.wolf_pack:on_receive_item
    Accepts: venison, meat, rabbit
    Effects: trust +1, transitions at trust=3→friendly, 5→allied
    Grants: alpha_fang_fragment at allied

  ✓ state_machine
    States: hostile → wary → neutral → friendly → allied
    Current: hostile

Properties:
  - trust_state: {current: 0, floor: -5, ceiling: 5}
  - pack_behavior: {followers: [grey_wolf_1, grey_wolf_2]}
```

### reaction_inventory.py
```bash
$ python tools/reaction_inventory.py --type gift_reactions

Gift Reactions (5 entities):

alpha_wolf (beast_wilds.wolf_pack:on_receive_item)
  Accepts: venison, meat, rabbit

salamander (frozen_reaches.salamanders:on_receive_item)
  Accepts: lava_fruit, volcanic_seed

bee_queen (beast_wilds.bee_queen:on_receive_item)
  Accepts: moonpetal, frost_lily, water_bloom

dire_bear (data-driven config)
  healing_herbs → cure cubs, fulfill commitment

npc_spore_mother (fungal_depths.spore_mother:on_receive_offering)
  Accepts: mushroom_samples, light_sources
```

### handler_usage.py
```bash
$ python tools/handler_usage.py beast_wilds.wolf_pack:on_receive_item

Handler: on_receive_item
Module: behaviors.regions.beast_wilds.wolf_pack
Line: 81-187

Used by (3 entities):
  - alpha_wolf (gift_reactions.food)
  - grey_wolf_1 (gift_reactions.food)
  - grey_wolf_2 (gift_reactions.food)

Trigger: give <food> to <wolf>

Effects:
  - Increases alpha_wolf trust (+1 per feeding)
  - State transitions: hostile→wary(1)→neutral(2)→friendly(3)→allied(5)
  - Grants alpha_fang_fragment at allied
  - Activates wolf as companion at allied
```

### validate_game_state.py
```bash
$ python tools/validate_game_state.py

Validating game state...

✓ All handler paths resolve (40/40)
✓ All reaction schemas valid (35/35)
✓ All cross-references valid (127/127)
✓ All entity capabilities valid (156/156)

⚠ 3 warnings:
  - alpha_wolf accepts 'rabbit' but no item 'rabbit' exists
  - dire_bear gift_reactions missing reject_message
  - spider_matriarch has combat_reactions but is not in combat system

Validation complete: 0 errors, 3 warnings
```

---

## Migration Strategy

### Phase 1: Build Core Infrastructure (Priority Order)
1. `encounter_reactions.py` - Needed for sira, bear cubs, dual rescue
2. `item_use_reactions.py` - Needed for bear healing, aldric healing, puzzles
3. `death_reactions.py` - Needed for sira, golems, spider queen
4. `dialog_reactions.py` - Needed for vendors, extensive NPC interactions

### Phase 2: Migrate Existing Vocabulary Events
- Convert vocabulary event handlers to property-based configs
- Update entity properties in game_state.json
- Remove vocabulary events from behavior modules
- Keep handlers as pure functions

### Phase 3: Complete Remaining Infrastructure
5. `combat_reactions.py` - For golem puzzle, spider tracking
6. `entry_reactions.py` - For environmental effects on entry
7. `take_reactions.py` - For resource tracking, theft detection
8. `commitment_reactions.py` - For commitment lifecycle events
9. `trade_reactions.py` - For vendor interactions
10. `examine_reactions.py` - For puzzle revelations

### Phase 4: Validation & Tooling
- Implement load-time validation system
- Build discoverability tools (inspector, inventory, usage)
- Generate documentation from configs
- Create authoring templates

---

## Benefits Summary

### vs. Current Vocabulary Events (Approach B)
- ✅ **Performance:** O(1) dispatch vs O(n) broadcast
- ✅ **Type Safety:** Load-time validation vs runtime string matching
- ✅ **Maintainability:** Clear entity ownership vs scattered handlers
- ✅ **Testability:** Direct handler calls vs infrastructure coupling
- ✅ **Discoverability:** With tooling, superior to code reading

### vs. Current Mixed Approach
- ✅ **Consistency:** Single pattern for all reactions
- ✅ **Predictability:** Same infrastructure for similar interactions
- ✅ **Debuggability:** Clear dispatch path, verbose logging available
- ✅ **Extensibility:** Add entities without new infrastructure

---

## Current Status: Infrastructure Modules

| Module | Status | Entities Using | Priority |
|--------|--------|----------------|----------|
| gift_reactions | ✅ Exists | 5 | - |
| turn_environmental | ✅ Exists | 3 | - |
| encounter_reactions | ❌ Needs Creation | 4 | HIGH |
| item_use_reactions | ❌ Needs Creation | 10+ | HIGH |
| death_reactions | ❌ Needs Creation | 7 | HIGH |
| dialog_reactions | ❌ Needs Creation | 13+ | HIGH |
| combat_reactions | ❌ Needs Creation | 3 | MEDIUM |
| entry_reactions | ❌ Needs Creation | 4 | MEDIUM |
| take_reactions | ❌ Needs Creation | 2 | LOW |
| commitment_reactions | ❌ Needs Creation | 5 | MEDIUM |
| trade_reactions | ❌ Needs Creation | 4 | LOW |
| examine_reactions | ❌ Needs Creation | 5+ | LOW |

**Total:** 2/12 infrastructure modules complete (17%)
