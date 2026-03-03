# NPC Authoring Plan: Complete Missing Configurations

## Overview

17 NPCs have state machines but lack reaction configurations. This document details what needs to be authored for each, including handler requirements and gameplay mechanics.

---

## Priority 1: Major NPCs with Existing Handlers

### The Echo (the_echo)

**Current State:**
- Location: keepers_quarters
- Trust: 0 (floor: -6, ceiling: 6)
- States: dormant → manifesting → communicating → fading → permanent
- Handlers exist: `echo.py:on_echo_dialog`, `echo.py:on_echo_gossip`

**Gameplay Role:**
- Spectral remnant of the Meridian Keeper
- Provides lore about the catastrophe
- Trust system gates information reveals
- Can become permanent companion at high trust

**Authoring Requirements:**

1. **dialog_reactions Configuration:**
```json
"dialog_reactions": {
  "handler": "examples.big_game.behaviors.regions.meridian_nexus.echo:on_echo_dialog"
}
```

2. **Handler Review (echo.py):**
- Check `on_echo_dialog` implements:
  - Keyword matching for lore topics (catastrophe, waystone, keeper, regions)
  - Trust-gated responses (higher trust → deeper lore)
  - State transitions based on dialog progress
  - Progressive revelation system
- Check `on_echo_gossip` implements:
  - Reactions to player accomplishments in other regions
  - Trust changes based on gossip content

3. **Missing Handler (if needed):**
- **Commitment system** for making Echo permanent
  - Trigger: High trust (5+) + specific dialog
  - Effect: State → permanent, add to companions
  - Handler: `on_echo_commitment` in echo.py

**Testing Requirements:**
- Walkthrough: Dialog progression from dormant → permanent
- Verify all lore topics accessible
- Test trust gates work correctly

---

## Priority 2: Town NPCs (Civilized Remnants)

All three NPCs share the services.py infrastructure.

### Healer Elara (healer_elara)

**Current State:**
- Location: town_square
- Trust: 0 (floor: -5, ceiling: 5)
- States: neutral → concerned → helping
- Handler exists: `services.py:on_service_request`

**Gameplay Role:**
- Heals player for gold
- Cures conditions (poison, infection, hypothermia)
- Trust affects prices and available services
- Receives gossip about NPC deaths/failures

**Authoring Requirements:**

1. **dialog_reactions Configuration:**
```json
"dialog_reactions": {
  "healing": {
    "keywords": ["heal", "help", "medicine", "cure", "injured"],
    "requires_property": {"path": "extra.gold", "min": 50},
    "modify_property": [
      {"path": "extra.gold", "delta": -50},
      {"path": "properties.health", "set": 100, "target": "player"}
    ],
    "remove_condition": "hypothermia",
    "transition_to": "helping",
    "summary": "Elara nods professionally. 'I can help with that.' She applies her healing arts."
  },
  "gossip": {
    "keywords": ["sira", "aldric", "garrett", "delvan"],
    "handler": "examples.big_game.behaviors.regions.civilized_remnants.services:on_gossip_received"
  },
  "default_response": "Elara looks at you expectantly. 'Do you need healing?'"
}
```

2. **Handler Enhancement (services.py):**
- Verify `on_service_request` handles:
  - Gold deduction
  - Health restoration
  - Condition removal
  - Trust changes based on repeat business
- Check `on_gossip_received` handles:
  - NPC death gossip (Sira, Aldric, Garrett, Delvan)
  - Trust penalties for failed commitments
  - Reputation changes

**Testing:**
- Heal when healthy (should it work?)
- Heal when injured + sufficient gold
- Heal when injured + insufficient gold
- Multiple healings (trust progression)
- Gossip about dead NPCs

### Gate Guard (gate_guard)

**Current State:**
- Location: town_gate
- States: suspicious → neutral → friendly

**Gameplay Role:**
- Controls access to dangerous regions (warning system)
- Provides hints about regional hazards
- Trust affects willingness to share information

**Authoring Requirements:**

1. **dialog_reactions Configuration:**
```json
"dialog_reactions": {
  "warnings": {
    "keywords": ["frozen", "beast", "fungal", "sunken", "danger", "warn"],
    "requires_state": ["neutral", "friendly"],
    "summary": "The guard shares warnings about the region you asked about...",
    "set_flags": {"guard_warned_{region}": true}
  },
  "suspicious_response": {
    "keywords": ["help", "information", "tell"],
    "requires_state": ["suspicious"],
    "summary": "The guard eyes you suspiciously. 'Move along.'"
  },
  "default_response": "The guard watches the horizon, alert."
}
```

2. **Handler Needs:**
- Likely can be fully data-driven (no handler needed)
- Use state machine transitions based on player reputation

**Testing:**
- Dialog in suspicious state (should be rebuffed)
- Dialog in neutral/friendly state (should get warnings)
- Verify region-specific warnings

### Herbalist Maren (herbalist_maren)

**Current State:**
- Location: herbalists_shop
- Trust: 0 (floor: -3, ceiling: 5)

**Gameplay Role:**
- Sells/trades herbs and alchemical items
- Teaches about ingredient uses
- Higher trust → better prices, rare items

**Authoring Requirements:**

1. **dialog_reactions Configuration:**
```json
"dialog_reactions": {
  "trade": {
    "keywords": ["buy", "sell", "trade", "herbs", "potion"],
    "handler": "examples.big_game.behaviors.regions.civilized_remnants.services:on_trade_request"
  },
  "teaching": {
    "keywords": ["silvermoss", "mushroom", "ingredient", "use"],
    "requires_trust": 2,
    "grant_knowledge": ["ingredient_lore"],
    "trust_delta": 1,
    "summary": "Maren explains the properties of {topic} in detail..."
  },
  "default_response": "Maren tends her herb garden. 'Looking for supplies?'"
}
```

2. **Handler Needs:**
- **New handler:** `on_trade_request` in services.py
  - Implement item-for-gold trades
  - Trust-based pricing (higher trust → discounts)
  - Inventory management
  - Available items: silvermoss, healing_potion, antidote, warm_clothes

**Testing:**
- Buy items with sufficient gold
- Buy items with insufficient gold
- Check trust affects prices
- Verify inventory updates

---

## Priority 3: Pack Followers

These NPCs should mirror their pack leaders and need minimal individual configuration.

### Grey Wolves (frost_wolf_1, frost_wolf_2)

**Current State:**
- Pack members of alpha_wolf
- States mirror alpha: hostile → wary → neutral → friendly → allied

**Authoring Requirements:**

1. **Verify pack_behavior Property:**
```json
"properties": {
  "pack_behavior": {
    "leader": "alpha_wolf",
    "mirrors_state": true,
    "follows_location": true
  },
  "state_machine": {
    "states": ["hostile", "wary", "neutral", "friendly", "allied"],
    "initial": "hostile"
  }
}
```

2. **No reactions needed** - mirroring handles behavior

3. **Handler Check:**
- Verify `wolf_pack.py:on_wolf_state_change` mirrors to pack members
- Ensure pack members listed in alpha_wolf's pack_behavior config

**Testing:**
- Feed alpha_wolf, verify pack members mirror state
- Attack alpha_wolf, verify pack responds
- Alpha dies, verify pack behavior

### Steam Salamanders (steam_salamander_2, steam_salamander_3)

**Current State:**
- Pack members of salamander (lead)
- States mirror: neutral → friendly → companion

**Authoring Requirements:**

1. **Verify pack_behavior Property:**
```json
"properties": {
  "pack_behavior": {
    "leader": "salamander",
    "mirrors_state": true,
    "follows_location": true
  },
  "state_machine": {
    "states": ["neutral", "friendly", "companion", "wild", "curious", "bonded"],
    "initial": "neutral"
  }
}
```

2. **Handler Check:**
- Verify `salamanders.py:_mirror_salamander_state` includes these IDs
- Check salamander leader has pack_behavior.followers list

**Testing:**
- Gift fire to lead salamander
- Verify pack members mirror state transition
- Verify companion activation includes pack

### Sporelings (npc_sporeling_1, npc_sporeling_2, npc_sporeling_3)

**Current State:**
- Pack members of npc_spore_mother
- States mirror: hostile → wary → allied → confused

**Authoring Requirements:**

1. **Verify pack_behavior Property:**
```json
"properties": {
  "pack_behavior": {
    "leader": "npc_spore_mother",
    "mirrors_state": true,
    "follows_location": true
  },
  "state_machine": {
    "states": ["hostile", "wary", "allied", "confused"],
    "initial": "hostile"
  }
}
```

2. **Handler Check:**
- Verify `spore_mother.py` has pack mirroring logic
- Check spore_mother has followers list

**Testing:**
- Peaceful presence near Spore Mother (should transition to wary)
- Heal Spore Mother (should transition to allied, pack follows)
- Kill Spore Mother (sporelings → confused)

### Giant Spiders (giant_spider_1, giant_spider_2)

**Current State:**
- Related to spider_matriarch
- States: hostile → dead

**Authoring Requirements:**

1. **Analysis Needed:**
- Are these pack members or independent encounters?
- Check `spider_nest.py` for respawn mechanics
- If independent: Add combat_reactions, death_reactions
- If pack: Add pack_behavior mirroring matriarch

2. **If Independent (most likely):**
```json
"combat_reactions": {
  "modify_property": {"path": "properties.health", "delta": -1},
  "message": "The spider hisses as your attack lands."
},
"death_reactions": {
  "set_flags": {"spider_{id}_dead": true},
  "message": "The spider collapses, legs curling inward."
}
```

**Testing:**
- Combat with spiders
- Verify death handling
- Check respawn mechanics if any

---

## Priority 4: Secondary Town NPCs

### Camp Leader Mira (camp_leader_mira)

**Current State:**
- Location: survivor_camp
- States: neutral → friendly → allied → disappointed

**Gameplay Role:**
- Leader of survivor camp
- Quests/commitments for helping survivors
- Trust affects camp access and services

**Authoring Requirements:**

1. **dialog_reactions Configuration:**
```json
"dialog_reactions": {
  "help_request": {
    "keywords": ["help", "survivors", "quest", "need"],
    "requires_state": ["neutral", "friendly"],
    "handler": "examples.big_game.behaviors.regions.civilized_remnants.mira:on_quest_offer"
  },
  "disappointed": {
    "keywords": ["talk", "speak"],
    "requires_state": ["disappointed"],
    "summary": "Mira turns away. 'You failed us when we needed you most.'"
  },
  "default_response": "Mira surveys the camp with weary determination."
}
```

2. **Handler Needs:**
- **New file:** `mira.py`
- **Handler:** `on_quest_offer`
  - Creates commitment for survivor rescue
  - Time-limited (20 turns)
  - Success: state → allied, trust +2, unlock camp services
  - Failure: state → disappointed, trust -3

**Testing:**
- Accept quest, complete in time
- Accept quest, fail timer
- Dialog in each state

### The Archivist (the_archivist)

**Current State:**
- Location: ancient_library
- States: guardian → helpful → allied

**Gameplay Role:**
- Protects ancient knowledge
- Trades lore for artifacts
- Can teach powerful insights

**Authoring Requirements:**

1. **dialog_reactions Configuration:**
```json
"dialog_reactions": {
  "lore_trade": {
    "keywords": ["trade", "knowledge", "artifact", "teach"],
    "requires_state": ["helpful", "allied"],
    "requires_items": ["ancient_artifact"],
    "consume_item": true,
    "grant_knowledge": ["ancient_lore"],
    "trust_delta": 1,
    "summary": "The Archivist accepts the artifact reverently and shares forbidden knowledge..."
  },
  "guardian_response": {
    "keywords": ["knowledge", "teach", "lore"],
    "requires_state": ["guardian"],
    "summary": "The Archivist regards you coldly. 'Knowledge is earned, not given.'"
  }
}
```

2. **State Transition:**
- guardian → helpful: Solve library puzzle or prove worth
- helpful → allied: Multiple successful trades

**Testing:**
- Dialog in guardian state (should be rebuffed)
- Trade artifact for knowledge
- Verify knowledge grants

### Curiosity Dealer Vex (curiosity_dealer_vex)

**Current State:**
- Location: dark_market
- Trust: 0 (floor: -3, ceiling: 5)
- States: guarded → interested → trusting

**Gameplay Role:**
- Deals in rare/strange items
- Information broker
- Morally ambiguous trades

**Authoring Requirements:**

1. **dialog_reactions + gift_reactions Configuration:**
```json
"dialog_reactions": {
  "trade_rare": {
    "keywords": ["trade", "buy", "sell", "rare"],
    "handler": "examples.big_game.behaviors.regions.civilized_remnants.vex:on_trade"
  },
  "information": {
    "keywords": ["information", "know", "tell", "secret"],
    "requires_trust": 2,
    "modify_property": {"path": "extra.gold", "delta": -100},
    "grant_knowledge": ["secret_paths"],
    "summary": "Vex leans in conspiratorially. 'For the right price...'"
  }
},
"gift_reactions": {
  "curiosities": {
    "accepted_items": ["strange_artifact", "mysterious_object", "unique_item"],
    "trust_delta": 1,
    "accept_message": "Vex's eyes light up. 'Now THIS is interesting...'"
  }
}
```

2. **Handler Needs:**
- **New file:** `vex.py`
- **Handler:** `on_trade`
  - Buys unusual items at high prices
  - Sells rare items (command_orb, special equipment)
  - Trust affects availability and prices

**Testing:**
- Trade common items (should reject)
- Trade rare items (should accept, good price)
- Gift curiosities (trust increase)
- Buy information at different trust levels

### Damaged Guardian (damaged_guardian)

**Current State:**
- Location: unknown (needs placement)
- States: non_functional → partially_awakened → functional → active

**Gameplay Role:**
- Ancient construct puzzle
- Repair sequence = multi-stage quest
- Rewards knowledge or guardian assistance

**Authoring Requirements:**

1. **item_use_reactions Configuration:**
```json
"item_use_reactions": {
  "power_core": {
    "accepted_items": ["power_core", "energy_crystal"],
    "transition_to": "partially_awakened",
    "consume_item": true,
    "response": "The guardian flickers to life, systems coming online slowly..."
  },
  "repair_kit": {
    "accepted_items": ["repair_kit", "ancient_tools"],
    "requires_state": ["partially_awakened"],
    "transition_to": "functional",
    "consume_item": true,
    "response": "You repair the damaged plating. The guardian's eyes glow steadier."
  },
  "activation_sequence": {
    "accepted_items": ["command_code", "activation_key"],
    "requires_state": ["functional"],
    "transition_to": "active",
    "consume_item": true,
    "response": "The guardian rises to full power! 'Primary functions restored.'"
  }
}
```

2. **dialog_reactions (active state):**
```json
"dialog_reactions": {
  "guardian_knowledge": {
    "keywords": ["catastrophe", "waystone", "ancients"],
    "requires_state": ["active"],
    "grant_knowledge": ["guardian_lore"],
    "summary": "The guardian shares ancient records from before the catastrophe..."
  }
}
```

**Testing:**
- Use items in wrong order (should reject)
- Use items in correct sequence
- Verify state transitions
- Dialog in each state

---

## Implementation Phases

### Phase 1: Critical Path (1-2 days)
1. The Echo - Complete dialog system
2. Town NPCs - Basic dialog/services
3. Verify pack behaviors working

### Phase 2: Gameplay Systems (1-2 days)
4. Mira commitment system
5. Vex trading system
6. Archivist lore trades
7. Damaged Guardian puzzle

### Phase 3: Polish & Testing (1 day)
8. Create walkthroughs for each NPC
9. Balance trust/gold/rewards
10. Test all state transitions

---

## New Handler Files Needed

1. **mira.py** (civilized_remnants)
   - on_quest_offer
   - on_quest_complete
   - on_quest_failed

2. **vex.py** (civilized_remnants)
   - on_trade (rare items)

3. **echo.py additions** (meridian_nexus)
   - on_echo_commitment (if needed)

4. **services.py additions**
   - on_trade_request (for Maren)

---

## Validation Checklist

After authoring each NPC:
- [ ] Run `python tools/validate_game_state.py examples/big_game`
- [ ] Verify 0 errors for that NPC
- [ ] Create walkthrough file
- [ ] Run walkthrough with `python tools/walkthrough.py`
- [ ] Document any handler-escape-hatch usage
- [ ] Update this plan with actual implementation notes

---

## Success Criteria

- All 17 NPCs have complete reaction configurations
- All NPCs validate without errors
- All NPCs have walkthrough coverage
- No empty state machines
- All trust systems functional
- All dialog systems responsive
