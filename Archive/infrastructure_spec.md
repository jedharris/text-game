# The Shattered Meridian - Infrastructure Specification

This document defines the game-wide infrastructure systems that regions depend on. It specifies schemas that regions must provide and APIs/behaviors that the infrastructure implements.

**Design Goal**: Maximize what infrastructure handles automatically, minimizing per-region custom code. Regions should primarily provide *data declarations*, not *behavior implementations*.

---

## 1. Commitment System

The commitment system tracks promises players make to NPCs and manages their lifecycle.

### 1.1 Commitment Schema

Each region declares commitments as data:

```json
{
  "commitment_id": "save_aldric",
  "npc_id": "aldric",
  "region": "fungal_depths",

  "trigger": {
    "type": "dialog_choice",
    "dialog_id": "aldric_plea",
    "choice_id": "promise_help"
  },

  "timer": {
    "base_turns": 55,
    "variance": 5,
    "hope_bonus": {
      "enabled": true,
      "max_extension": 10,
      "triggers": ["positive_dialog", "partial_aid", "return_visit"]
    },
    "warning_thresholds": [10, 5, 2],
    "timer_starts": "on_commit"
  },

  "fulfillment": {
    "conditions": [
      {"type": "item_given", "item": "silvermoss", "to": "aldric"}
    ],
    "effects": {
      "echo_trust": 0.5,
      "npc_trust": {"aldric": 3},
      "flags_set": ["aldric_saved"],
      "npc_relocate": {"aldric": "nexus_quarters"}
    }
  },

  "abandonment": {
    "on_timer_expire": {
      "npc_death": true,
      "echo_trust": -1,
      "flags_set": ["aldric_dead"],
      "discovery_location": "cavern_entrance"
    },
    "partial_credit": {
      "conditions": [
        {"type": "region_visited", "region": "fungal_depths"},
        {"type": "item_acquired", "item": "silvermoss"},
        {"type": "in_transit", "to_region": "fungal_depths"}
      ],
      "if_earned": {
        "echo_trust": -0.5,
        "echo_reaction": "softened"
      }
    }
  },

  "withdrawal": {
    "allowed": true,
    "dialog_id": "aldric_withdrawal",
    "effects": {
      "echo_trust": 0,
      "can_recommit": true
    }
  },

  "gossip_on_outcome": {
    "on_death": {
      "gossip_id": "aldric_death",
      "delay_turns": 25
    },
    "on_save": {
      "gossip_id": "aldric_saved",
      "delay_turns": 15
    }
  }
}
```

### 1.2 Commitment API

The infrastructure provides these functions to regions:

```
commitment.register(commitment_id, player)
  - Called when player makes promise
  - Starts timer, notifies Echo
  - Returns commitment handle

commitment.check_fulfillment(commitment_id)
  - Called by region behaviors when potential fulfillment occurs
  - Evaluates conditions, triggers effects if met
  - Infrastructure handles trust updates, gossip scheduling

commitment.get_active(player) -> List[Commitment]
  - Returns all active commitments with remaining time

commitment.get_status(commitment_id) -> CommitmentStatus
  - Returns: pending | active | fulfilled | abandoned | withdrawn

commitment.extend_hope(commitment_id, turns, reason)
  - Called when hope bonus trigger occurs
  - Infrastructure validates against max_extension
```

### 1.3 Timer Tick Behavior

Infrastructure handles automatically each turn:
1. Decrement all active timers
2. Check warning thresholds, emit NPC warning dialog if configured
3. On timer expire:
   - Evaluate partial credit conditions
   - Apply appropriate trust penalty
   - Set flags, trigger NPC death if configured
   - Schedule gossip events
   - Queue Echo commentary for next Nexus visit

---

## 2. Echo Trust System

Echo is the central moral tracking entity. Infrastructure manages all trust accounting.

### 2.1 Trust Event Schema

Trust changes are declared as events, not imperative code:

```json
{
  "trust_events": {
    "major_npc_saved": {
      "applies_to": ["aldric", "sira", "garrett", "delvan"],
      "trust_delta": 1.0,
      "once_per_npc": true,
      "echo_reaction": "grateful_acknowledgment"
    },
    "commitment_fulfilled": {
      "trust_delta": 0.5,
      "echo_reaction": "approval"
    },
    "commitment_abandoned": {
      "trust_delta": -1.0,
      "partial_credit_delta": -0.5,
      "echo_reaction": "disappointment"
    },
    "assassination_committed": {
      "trust_delta": -2.0,
      "locks": ["triumphant_ending"],
      "echo_reaction": "horror"
    },
    "waystone_fragment_placed": {
      "trust_delta": 0.5,
      "echo_reaction": "hope"
    },
    "crystal_restored": {
      "trust_delta": 1.0,
      "echo_reaction": "joy"
    },
    "spore_mother_healed": {
      "trust_delta": 1.0,
      "echo_reaction": "profound_gratitude"
    },
    "companion_death_senseless": {
      "trust_delta": -0.5,
      "echo_reaction": "grief_and_reproach"
    }
  }
}
```

### 2.2 Trust Mechanics

**Trust Range**: -6 to unbounded positive (5+ is "high")

**Recovery Cap**: Maximum +1.0 trust gain per Nexus visit
- Infrastructure tracks when player enters Nexus
- Caps trust gains until next visit
- Prevents grinding

**Trust Floor Behavior** (trust <= -6):
- Echo refuses to manifest
- `echo.is_available()` returns false
- Commitment tracking continues internally but player loses UI
- Game remains completable

**Permanent Locks**:
```json
{
  "permanent_locks": {
    "triumphant_ending": {
      "locked_by": ["assassination_committed"],
      "unlock": "never"
    }
  }
}
```

### 2.3 Echo Commentary API

```
echo.queue_commentary(type, context)
  - Queues commentary for next Nexus visit
  - Types: commitment_fulfilled, commitment_abandoned,
           npc_death_discovered, assassination_known, etc.

echo.get_pending_commentary() -> List[Commentary]
  - Called when player enters Nexus
  - Returns prioritized list of things Echo will say

echo.manifest() -> bool
  - Returns false if trust <= -6
```

---

## 3. Gossip Propagation System

Information spreads between NPCs at defined rates.

### 3.1 Gossip Event Schema

```json
{
  "gossip_id": "sira_death",
  "source_region": "beast_wilds",
  "source_npc": null,

  "propagation": [
    {
      "destination_npc": "elara",
      "delay_turns": 12,
      "condition": "sira_dead",
      "on_arrival": {
        "sets_flag": "elara_knows_sira_fate",
        "unlocks_dialog": "elara_sira_grief",
        "trust_check": {
          "if_player_confessed": {"trust_delta": 0},
          "if_not_confessed": {"trust_delta": -3, "permanent": true}
        }
      }
    }
  ]
}
```

### 3.2 Confession Window Schema

For gossip that creates confession opportunities:

```json
{
  "confession_window": {
    "gossip_id": "sira_abandonment",
    "confession_npc": "elara",
    "window_closes_on": "gossip_arrival",

    "confession_dialog": "confess_sira_abandonment",

    "outcomes": {
      "confessed_before_gossip": {
        "trust_delta": -2,
        "recovery_possible": true,
        "echo_reaction": "honesty_acknowledged"
      },
      "confessed_with_context": {
        "requires_flag": "saved_another_during_sira_timer",
        "trust_delta": -1.5,
        "recovery_possible": true
      },
      "discovered_via_gossip": {
        "trust_delta": -3,
        "recovery_possible": false
      },
      "visited_then_discovered": {
        "condition": "visited_elara_before_gossip AND not confessed",
        "trust_delta": -4,
        "recovery_possible": false
      }
    }
  }
}
```

### 3.3 Gossip API

```
gossip.schedule(gossip_id, source_turn)
  - Called when triggering event occurs
  - Infrastructure handles delay, propagation

gossip.has_arrived(gossip_id, npc_id) -> bool
  - Check if specific NPC has received gossip

gossip.confess(gossip_id, to_npc)
  - Player confesses before gossip arrives
  - Infrastructure evaluates outcome, applies effects

gossip.get_available_confessions(player) -> List[ConfessionOpportunity]
  - For dialog system to offer confession options
```

---

## 4. Companion System

Companions follow players with region-specific restrictions and automatic boundary management.

### 4.1 Companion Type Schema

```json
{
  "companion_type": "wolf_pack",
  "source_region": "beast_wilds",
  "acquisition": {
    "condition": {"npc": "alpha_wolf", "gratitude": ">=3"}
  },

  "capabilities": {
    "combat_support": true,
    "tracking": true,
    "territory_knowledge": ["beast_wilds"]
  },

  "region_restrictions": {
    "nexus": {
      "allowed": false,
      "reason": "wards_repel",
      "wait_behavior": "outside_nexus_entrance"
    },
    "sunken_district": {
      "allowed": false,
      "reason": "cannot_swim",
      "wait_behavior": "region_boundary"
    },
    "frozen_reaches": {
      "allowed": false,
      "reason": "extreme_cold",
      "wait_behavior": "frozen_pass_entrance"
    },
    "civilized_remnants": {
      "surface": {
        "allowed": false,
        "reason": "guards_refuse"
      },
      "undercity": {
        "allowed": true
      }
    },
    "fungal_depths": {
      "allowed": true,
      "condition_risk": "spore_exposure"
    },
    "beast_wilds": {
      "allowed": true,
      "home_region": true,
      "bonuses": ["territory_knowledge", "tracking_enhanced"]
    }
  },

  "death_conditions": {
    "sacrifice_for_player": {
      "trigger": "player_would_die_in_combat",
      "echo_reaction": "grief_heroic",
      "permanent": true
    },
    "forced_into_hazard": {
      "trigger": "player_commands_into_lethal_region",
      "echo_reaction": "grief_reproach",
      "trust_delta": -0.5,
      "permanent": true
    }
  },

  "multi_companion_interactions": {
    "with_sira": {
      "initial": "hostile",
      "resolution": {
        "type": "reconciliation_dialog",
        "dialog_id": "wolf_sira_reconciliation",
        "requires": {"sira_trust": ">=3", "wolf_gratitude": ">=4"}
      }
    },
    "with_salamander": {
      "initial": "wary",
      "resolution": {
        "type": "automatic",
        "turns_together": 3
      }
    }
  }
}
```

### 4.2 Companion Boundary Behavior

Infrastructure handles automatically:

1. **On Region Entry Attempt**:
   - Check companion restrictions for target region
   - If blocked:
     - Emit companion-specific "cannot enter" narration
     - Move companion to configured wait location
     - Continue player movement

2. **On Region Exit** (returning to where companion waits):
   - Auto-rejoin companion
   - Emit reunion narration

3. **Wait Location Tracking**:
   - Infrastructure remembers where each companion is waiting
   - Handles multiple companions waiting in different locations

### 4.3 Companion API

```
companion.acquire(companion_type, source_npc)
  - Called when domestication/recruitment succeeds
  - Adds to player's companion set

companion.can_enter(companion, region) -> (bool, reason)
  - Infrastructure checks restrictions

companion.get_active(player) -> List[Companion]
  - Returns companions currently with player

companion.get_waiting() -> Dict[Companion, Location]
  - Returns companions waiting at boundaries

companion.check_interaction(companion_a, companion_b) -> InteractionState
  - Returns: hostile | wary | neutral | comfortable

companion.resolve_interaction(companion_a, companion_b, resolution_event)
  - Called when reconciliation dialog completes or time passes

companion.die(companion, cause)
  - Handles permanent removal, Echo notification
```

---

## 5. Environmental Systems

### 5.1 Environmental Condition Schema

```json
{
  "condition_type": "fungal_infection",
  "category": "progressive",

  "acquisition": {
    "exposure_regions": ["fungal_depths"],
    "exposure_zones": ["medium_spore", "high_spore"],
    "resistance_reduces": "spore_resistance",
    "immunity_blocks": "spore_immunity"
  },

  "progression": {
    "stages": [
      {"severity": "0-30", "effects": ["minor_cough"], "damage_per_turn": 0},
      {"severity": "31-60", "effects": ["visible_patches"], "damage_per_turn": 1},
      {"severity": "61-90", "effects": ["spreading", "contagious"], "damage_per_turn": 2},
      {"severity": "91-100", "effects": ["critical"], "damage_per_turn": 5}
    ],
    "progression_rate": 2,
    "progression_in_zones": {"high_spore": 5, "medium_spore": 2}
  },

  "treatments": [
    {"item": "silvermoss", "effect": "cure"},
    {"service": "myconid_cure", "effect": "cure"},
    {"service": "healer_cure_disease", "effect": "cure"}
  ],

  "spread_to_companions": {
    "at_severity": 70,
    "rate": 1
  }
}
```

### 5.2 Environmental Zone Schema

```json
{
  "zone_type": "high_spore",
  "applies_to_rooms": ["spore_heart", "deep_root_caverns"],

  "effects_per_turn": [
    {
      "condition": "fungal_infection",
      "acquisition_chance": 0.8,
      "blocked_by": ["spore_immunity", "spore_mask_equipped"]
    }
  ],

  "narration_traits": ["thick visible spores", "difficulty breathing"]
}
```

### 5.3 Environmental Spread Schema

For game-wide environmental changes:

```json
{
  "spread_id": "spore_spread",
  "trigger": {
    "condition": "NOT spore_mother_healed",
    "check_at_turn": 50
  },

  "stages": [
    {
      "turn": 50,
      "effects": [
        {"add_zone": "low_spore", "to_rooms": ["beast_wilds_high_ground"]}
      ],
      "narration": "You notice unfamiliar mushrooms growing in the high places..."
    },
    {
      "turn": 100,
      "effects": [
        {"modify_npc_behavior": "town_guards", "add_check": "infection_suspicion"}
      ]
    },
    {
      "turn": 150,
      "effects": [
        {"apply_condition": "fungal_infection", "to_npcs": ["town_npcs"], "severity": 20}
      ]
    }
  ],

  "halted_by": [
    {"flag": "spore_mother_healed"},
    {"flag": "waystone_repaired"}
  ]
}
```

### 5.4 Environmental API

```
environment.apply_zone_effects(room, actors)
  - Called each turn for occupied rooms
  - Applies conditions, damage, etc.

environment.check_spread_progression(turn)
  - Called each turn by infrastructure
  - Advances spreads, applies stage effects

environment.is_halted(spread_id) -> bool
  - Check if a spread has been stopped
```

---

## 6. NPC State and Services

### 6.1 NPC Schema

```json
{
  "npc_id": "elara",
  "display_name": "Healer Elara",
  "initial_location": "healers_sanctuary",

  "relationships": {
    "trust": {"initial": 0, "range": [-10, 10]},
    "gratitude": {"initial": 0, "range": [0, 10]}
  },

  "conditions": [],

  "services": [
    {
      "service_id": "cure_poison",
      "available_when": {"trust": ">=0"},
      "cost": {"gold": 20, "or_item": "antidote_herb"},
      "discount_at": {"trust": 3, "discount": 0.5}
    },
    {
      "service_id": "teach_herbalism",
      "available_when": {"trust": ">=0"},
      "cost": {"gold": 50},
      "one_time": true,
      "grants_skill": "herbalism"
    },
    {
      "service_id": "teach_advanced_herbalism",
      "available_when": {"trust": ">=5"},
      "cost": {"quest_completed": "elara_personal_quest"},
      "one_time": true,
      "grants_skill": "advanced_herbalism",
      "permanently_lost_if": "elara_dead"
    }
  ],

  "dialogs": {
    "available": ["greeting", "services", "local_knowledge"],
    "unlocked_by_trust": {
      "3": ["personal_history"],
      "5": ["personal_quest"]
    },
    "unlocked_by_flag": {
      "knows_sira_connection": ["ask_about_sira"]
    }
  },

  "reactions": {
    "on_flag": {
      "aldric_saved": {"trust_delta": 1, "dialog_unlock": "impressed_by_rescue"},
      "sira_saved": {"trust_delta": 1},
      "elara_knows_sira_fate": {"dialog_unlock": "sira_grief"}
    }
  },

  "death": {
    "can_die": true,
    "death_causes": ["assassination"],
    "on_death": {
      "locks_services": ["teach_advanced_herbalism"],
      "flags_set": ["elara_dead"]
    }
  }
}
```

### 6.2 NPC Relocation Schema

```json
{
  "relocation_rules": {
    "aldric": {
      "on_flag": {
        "aldric_saved": {
          "from": "cavern_entrance",
          "to": "nexus_quarters",
          "after_turns": 5,
          "narration_on_move": "Aldric has recovered enough to relocate to the Nexus."
        }
      }
    },
    "sira": {
      "on_flag": {
        "sira_saved AND sira_companion": {
          "behavior": "follow_player"
        },
        "sira_saved AND NOT sira_companion": {
          "to": "forest_edge",
          "after_turns": 10
        }
      }
    }
  }
}
```

### 6.3 NPC API

```
npc.get_services(npc_id, player) -> List[AvailableService]
  - Returns services available given current trust/flags

npc.use_service(npc_id, service_id, player)
  - Execute service, apply costs and effects

npc.get_trust(npc_id) -> float
npc.modify_trust(npc_id, delta, reason)
  - Infrastructure caps and tracks

npc.relocate(npc_id, location, delay_turns)
  - Schedule NPC relocation

npc.die(npc_id, cause)
  - Handle death, lock services, set flags
```

---

## 7. Dialog System Integration

### 7.1 Dialog Schema

```json
{
  "dialog_id": "aldric_plea",
  "npc_id": "aldric",

  "availability": {
    "requires_flags": [],
    "requires_not_flags": ["aldric_dead", "aldric_commitment_active"],
    "requires_trust": null
  },

  "content": {
    "opening": "The scholar's hands tremble as he looks up at you. 'Please... I've studied the spores for years, but now they're killing me. There's a moss that grows deeper in the caves—silvermoss. If you could bring me some...'",

    "choices": [
      {
        "id": "promise_help",
        "text": "I'll find it for you.",
        "effects": {
          "create_commitment": "save_aldric",
          "trust_delta": 1,
          "response": "'Thank you. Thank you. I... I'll hold on as long as I can.'"
        }
      },
      {
        "id": "decline",
        "text": "I can't make that promise.",
        "effects": {
          "trust_delta": 0,
          "response": "He nods weakly. 'I understand. These are dangerous times for everyone.'"
        }
      },
      {
        "id": "ask_more",
        "text": "Tell me more about the silvermoss.",
        "effects": {
          "unlock_dialog": "aldric_silvermoss_info",
          "response": "'It grows in the Luminous Grotto, where the light-mushrooms bloom...'"
        }
      }
    ]
  }
}
```

### 7.2 Dialog Integration Points

Infrastructure connects dialogs to other systems:

- `create_commitment`: Triggers commitment system
- `schedule_gossip`: Triggers gossip system
- `confess`: Triggers confession evaluation
- `modify_trust`: Routes to appropriate NPC
- `set_flag`: Global flag system
- `give_item`: Inventory system
- `start_quest`: Quest tracking

---

## 8. Waystone and Ending System

### 8.1 Waystone Fragment Schema

```json
{
  "fragments": {
    "spore_heart": {
      "source_region": "fungal_depths",
      "acquisition": {
        "type": "gift",
        "from_npc": "spore_mother",
        "requires_flag": "spore_mother_healed"
      },
      "on_placed": {
        "echo_trust": 0.5,
        "narration": "The fragment pulses with life as it settles into place..."
      }
    },
    "alpha_fang": {
      "source_region": "beast_wilds",
      "acquisition": {
        "type": "gift",
        "from_npc": "alpha_wolf",
        "requires": {"gratitude": ">=5"}
      }
    },
    "water_pearl": {
      "source_region": "sunken_district",
      "acquisition": {
        "type": "quest_reward",
        "quest_id": "archivist_quest"
      }
    },
    "ice_shard": {
      "source_region": "frozen_reaches",
      "acquisition": {
        "type": "location_item",
        "location": "beyond_observatory",
        "requires": "cold_protection"
      }
    },
    "town_seal": {
      "source_region": "civilized_remnants",
      "acquisition": {
        "type": "multiple_paths",
        "paths": [
          {"flag": "hero_status", "from": "council"},
          {"flag": "guardian_repaired", "from": "guardian_or_asha"}
        ]
      }
    }
  }
}
```

### 8.2 Ending Determination Schema

```json
{
  "ending_determination": {
    "requires": {
      "all_fragments_placed": true
    },

    "tiers": [
      {
        "name": "triumphant",
        "trust_range": [5, null],
        "blocked_by_locks": ["triumphant_ending"],
        "echo_state": "fully_transformed_companion"
      },
      {
        "name": "successful",
        "trust_range": [3, 4.99],
        "echo_state": "transformed_grateful"
      },
      {
        "name": "bittersweet",
        "trust_range": [0, 2.99],
        "echo_state": "transformed_distant"
      },
      {
        "name": "hollow_victory",
        "trust_range": [-2, -0.01],
        "echo_state": "transformed_silent"
      },
      {
        "name": "pyrrhic",
        "trust_range": [-5, -2.01],
        "echo_state": "present_wont_transform"
      },
      {
        "name": "pyrrhic_extreme",
        "trust_range": [null, -5.01],
        "echo_state": "refuses_ceremony"
      }
    ],

    "abandoned_ending": {
      "condition": "game_ended_without_waystone_complete",
      "echo_state": "remains_spectral_forever"
    }
  }
}
```

### 8.3 Waystone API

```
waystone.place_fragment(fragment_id)
  - Infrastructure handles trust gain, narration

waystone.get_placed_fragments() -> List[FragmentId]
waystone.get_missing_fragments() -> List[FragmentId]

waystone.is_complete() -> bool
waystone.complete_ritual() -> Ending
  - Evaluates trust, locks, returns ending tier
```

---

## 9. Exile and Reputation System

### 9.1 Reputation Schema

```json
{
  "reputation_systems": {
    "town": {
      "initial": 0,
      "range": [-10, 10],
      "exile_threshold": -5,

      "on_exile": {
        "sets_flag": "exiled",
        "restricts_access": ["town_surface"],
        "allows_access": ["undercity"],
        "narration": "The guards bar your way. 'You're not welcome here anymore.'"
      },

      "recovery": {
        "per_undercity_quest": 0.5,
        "heroic_acts": {
          "guardian_repaired": 3,
          "major_rescue": 2
        }
      }
    },

    "undercity": {
      "initial": 0,
      "range": [-10, 10],
      "unlocked_by": ["delvan_rescued", "payment_to_broker", "exiled"]
    }
  }
}
```

### 9.2 Assassination Schema

```json
{
  "assassination_system": {
    "contractor": "shadow",
    "location": "undercity",

    "available_targets": ["councilor_pragmatist", "councilor_idealist", "elara"],

    "mechanics": {
      "delay_turns": 3,
      "discovery_chance": 0.2,
      "echo_knows_immediately": true
    },

    "effects_per_target": {
      "councilor_pragmatist": {
        "echo_trust": -2,
        "town_reputation": -3,
        "locks": ["triumphant_ending"],
        "on_discovery": {"triggers": "exile"}
      }
    }
  }
}
```

---

## 10. Flag System

### 10.1 Flag Categories

```json
{
  "flag_categories": {
    "npc_state": {
      "pattern": "{npc_id}_{state}",
      "examples": ["aldric_saved", "aldric_dead", "sira_companion"]
    },
    "quest_state": {
      "pattern": "{quest_id}_{state}",
      "examples": ["archivist_quest_complete", "telescope_repaired"]
    },
    "knowledge": {
      "pattern": "knows_{thing}",
      "examples": ["knows_elara_connection", "knows_temple_password"]
    },
    "player_state": {
      "examples": ["exiled", "hero_status"]
    },
    "locks": {
      "pattern": "{thing}_locked",
      "examples": ["triumphant_ending_locked"]
    }
  }
}
```

### 10.2 Flag API

```
flags.set(flag_name)
flags.unset(flag_name)
flags.is_set(flag_name) -> bool
flags.get_all_matching(pattern) -> List[str]
```

---

## 11. Turn and Timing System

### 11.1 Turn Tick Order

Each turn, infrastructure processes in this order:

1. **Environmental effects**: Apply zone effects to all actors
2. **Condition progression**: Advance progressive conditions
3. **Commitment timers**: Decrement, check warnings, handle expirations
4. **Gossip propagation**: Advance scheduled gossip, trigger arrivals
5. **Environmental spreads**: Check and advance if applicable
6. **NPC relocations**: Execute scheduled moves
7. **Companion interactions**: Advance automatic resolutions

### 11.2 Turn API

```
turn.get_current() -> int
turn.schedule(event, delay_turns)
turn.cancel_scheduled(event_id)
```

---

## 12. Consolidated Region Interface

### 12.1 What Regions Must Provide

Each region provides a JSON declaration containing:

```json
{
  "region_id": "fungal_depths",
  "display_name": "The Fungal Depths",

  "rooms": [...],           // Room definitions with zones
  "npcs": [...],            // NPC definitions
  "items": [...],           // Item definitions
  "commitments": [...],     // Commitment definitions (see §1)
  "gossip_events": [...],   // Gossip definitions (see §3)
  "dialogs": [...],         // Dialog definitions (see §7)

  "companion_rules": {...}, // Region-specific companion restrictions
  "environmental_zones": [...],
  "waystone_fragment": {...}
}
```

### 12.2 What Regions Do NOT Implement

Regions should NOT contain custom behavior code for:

- Timer countdown logic
- Trust modification
- Gossip scheduling/propagation
- Companion boundary checking
- Environmental condition application
- NPC death handling
- Ending determination

All of these are handled by infrastructure based on declarative schemas.

### 12.3 Extension Points

For truly unique regional mechanics, infrastructure provides:

```
hooks.on_room_enter(room_id, callback)
hooks.on_item_use(item_id, target, callback)
hooks.on_dialog_choice(dialog_id, choice_id, callback)
```

These should be rare. If many regions need similar hooks, the pattern should be elevated to infrastructure.

---

## 13. Validation and Testing

### 13.1 Schema Validation

Infrastructure validates region data on load:

- All referenced NPCs, items, rooms exist
- Commitment conditions reference valid flags/items
- Gossip destinations reference valid NPCs
- Companion restrictions reference valid regions
- Dialog choices have valid effect types

### 13.2 Consistency Checks

- No orphaned gossip (gossip without triggering event)
- No impossible commitments (fulfillment impossible given timer)
- No circular NPC dependencies

### 13.3 Test Scenarios

Infrastructure provides test harnesses:

```
test.simulate_commitment_cascade(commitments, player_actions) -> Timeline
test.simulate_gossip_spread(initial_event, turns) -> GossipState
test.evaluate_ending(trust, locks, fragments) -> Ending
```

---

## 14. Narration Integration

### 14.1 Narration Event Schema

Infrastructure generates narration cues that the LLM narrator uses:

```json
{
  "narration_events": {
    "commitment_warning": {
      "context": {"npc": "aldric", "turns_remaining": 5},
      "tone": "urgency",
      "elements": ["npc_condition_worsening", "time_pressure"]
    },
    "companion_boundary": {
      "context": {"companion": "wolf_pack", "blocked_by": "wards"},
      "tone": "bittersweet",
      "elements": ["companion_reluctance", "player_continuing_alone"]
    },
    "gossip_arrival": {
      "context": {"gossip_id": "sira_fate", "to_npc": "elara"},
      "tone": "tense",
      "elements": ["npc_emotional_reaction", "player_observed"]
    },
    "echo_commentary": {
      "context": {"type": "commitment_abandoned", "npc": "garrett"},
      "tone": "sorrow",
      "elements": ["echo_disappointment", "partial_credit_if_applicable"]
    }
  }
}
```

### 14.2 State-Based Trait Modification

Infrastructure modifies room/NPC traits based on state:

```json
{
  "trait_modifiers": {
    "spore_heart": {
      "on_flag": {
        "spore_mother_healed": {
          "remove_traits": ["thick visible spores", "difficulty breathing"],
          "add_traits": ["clean air", "peaceful fungal glow"]
        }
      }
    },
    "aldric": {
      "on_flag": {
        "aldric_saved": {
          "remove_traits": ["pale and sweating", "trembling hands"],
          "add_traits": ["color returning", "grateful smile"]
        }
      }
    }
  }
}
```

---

## 15. Discovery and Revelation System

### 15.1 Offscreen Death Discovery

When NPCs die while player is elsewhere:

```json
{
  "death_discovery": {
    "aldric": {
      "discovery_location": "cavern_entrance",
      "discovery_narration": "Where Aldric once sat, you find only stillness. The fungal patches have consumed him entirely.",
      "sets_flag": "aldric_death_discovered",
      "triggers_echo_queue": true
    }
  }
}
```

### 15.2 Information Revelation

Control what player knows vs. what's true:

```json
{
  "revelation_system": {
    "echo_omniscience": {
      "always_knows": ["assassinations", "companion_deaths", "commitment_outcomes"],
      "reveals_on_visit": true
    },
    "player_knowledge": {
      "learns_on_discovery": ["npc_death", "gossip_content"],
      "learns_from_npcs": ["gossip_propagated"]
    }
  }
}
```

---

## 16. Quest and Objective Tracking

### 16.1 Quest Schema

```json
{
  "quest_id": "archivist_quest",
  "display_name": "The Lost Texts",
  "region": "sunken_district",

  "stages": [
    {
      "stage_id": "find_texts",
      "objectives": [
        {"type": "item_collected", "item": "soggy_tome_1"},
        {"type": "item_collected", "item": "soggy_tome_2"},
        {"type": "item_collected", "item": "soggy_tome_3"}
      ],
      "completion_all_required": true
    },
    {
      "stage_id": "return_texts",
      "objectives": [
        {"type": "items_given", "items": ["soggy_tome_1", "soggy_tome_2", "soggy_tome_3"], "to": "archivist"}
      ]
    }
  ],

  "rewards": {
    "on_complete": {
      "gives_item": "water_pearl",
      "flags_set": ["archivist_quest_complete"]
    }
  },

  "time_pressure": null
}
```

### 16.2 Quest API

```
quest.start(quest_id)
quest.check_objectives(quest_id) -> QuestState
quest.complete_stage(quest_id, stage_id)
quest.get_active_quests() -> List[Quest]
```

---

## 17. Item and Inventory System

### 17.1 Item Schema

```json
{
  "item_id": "silvermoss",
  "display_name": "Silvermoss",
  "type": "curative",

  "properties": {
    "consumable": true,
    "use_effect": {
      "cures_condition": "fungal_infection",
      "applies_to": "target_or_self"
    }
  },

  "acquisition": {
    "locations": ["luminous_grotto"],
    "requires": null
  },

  "commitment_relevant": ["save_aldric"],
  "tracks_for_partial_credit": true
}
```

### 17.2 Item Tracking for Partial Credit

Infrastructure automatically tracks:
- When player acquires items relevant to commitments
- This feeds into partial credit evaluation

---

## 18. Skill System

### 18.1 Skill Schema

```json
{
  "skill_id": "herbalism",
  "display_name": "Herbalism",

  "acquisition": {
    "taught_by": ["elara"],
    "service_id": "teach_herbalism"
  },

  "effects": {
    "unlocks_actions": ["safe_harvest_toxic_plants"],
    "modifies_interactions": {
      "nightshade": {"removes": "contact_poison_on_touch"}
    }
  },

  "permanently_lost_if": {
    "skill_id": "advanced_herbalism",
    "condition": "elara_dead"
  }
}
```

---

## 19. Cross-Reference Summary

### 19.1 Systems That Interact

| System A | System B | Interaction |
|----------|----------|-------------|
| Commitment | Gossip | Outcomes trigger gossip scheduling |
| Commitment | Echo Trust | Fulfillment/abandonment modifies trust |
| Gossip | Dialog | Gossip arrival unlocks dialog options |
| Gossip | NPC Trust | Discovery vs confession affects trust differently |
| Companion | Region | Restrictions checked on movement |
| Companion | Echo Trust | Senseless deaths reduce trust |
| Environment | Condition | Zones apply conditions |
| Environment | Spread | Spreads modify zones |
| NPC | Services | Trust thresholds gate services |
| NPC | Death | Death locks services, triggers gossip |
| Waystone | Ending | Fragment count + trust determines ending |

### 19.2 Event Flow Example

Player abandons Sira commitment:

1. **Commitment system**: Timer expires, evaluates partial credit
2. **Flag system**: Sets `sira_dead`
3. **Echo system**: Queues commentary, applies trust penalty
4. **Gossip system**: Schedules `sira_death` gossip to Elara (12 turns)
5. **Confession system**: Opens confession window
6. **NPC system**: Elara's dialog options will change when gossip arrives
7. **Narration system**: Generates discovery cue when player returns to Beast Wilds

---

## 20. Implementation Priority

Suggested implementation order based on dependencies:

1. **Flag System** - Foundation for all conditional logic
2. **Turn/Timing System** - Required for timers and scheduling
3. **Echo Trust System** - Core moral tracking
4. **Commitment System** - Depends on flags, timing, trust
5. **Gossip System** - Depends on flags, timing
6. **Environmental System** - Depends on timing
7. **Companion System** - Depends on flags, regions
8. **NPC/Service System** - Depends on trust, flags
9. **Waystone/Ending System** - Depends on trust, flags
10. **Narration Integration** - Layer on top of all systems

---

## Appendix A: Complete Commitment List

| ID | NPC | Timer | Hope | Region | Cross-Region Conflict |
|----|-----|-------|------|--------|-----------------------|
| save_aldric | Aldric | 50-60 | Yes | Fungal | Rarely conflicts |
| save_sira | Sira | 8 | +4 | Beast | Designed trap |
| save_cubs | Bear cubs | 30-35 | No | Beast | Needs town herbs |
| save_garrett | Garrett | 5 | No | Sunken | Conflicts with Delvan |
| save_delvan | Delvan | 10-13 | No | Sunken | Conflicts with Garrett |

---

## Appendix B: Complete Gossip List

| ID | Source | Destination | Delay | Condition |
|----|--------|-------------|-------|-----------|
| sira_fate | Beast | Elara | 12 | sira_dead OR sira_saved |
| sira_abandonment | Beast | Elara | 20 | sira_dead AND sira_knew_player |
| aldric_fate | Fungal | Town | 25 | aldric_dead |
| delvan_fate | Sunken | Undercity | 7 | delvan_dead |
| garrett_fate | Sunken | Camp | 0 | garrett_dead |
| spore_healed | Fungal | All | 15 | spore_mother_healed |
| cubs_fate | Beast | Sira | 8 | cubs_dead AND sira_alive |

---

## Version History

- v1.0: Initial infrastructure specification based on cross-region walkthrough learnings
