# The Shattered Meridian - Infrastructure Specification v2.0

This document defines the game-wide infrastructure systems that regions depend on. It specifies schemas that regions must provide and APIs/behaviors that the infrastructure implements.

**Design Goal**: Maximize what infrastructure handles automatically, minimizing per-region custom code. Regions should primarily provide *data declarations*, not *behavior implementations*.

**Version 2.0 Changes from v1.0**:
- Added §10 Puzzle System (new)
- Added §11 Information Network System (expanded from gossip)
- Added §12 Collection Quest System (new)
- Replaced §13 Game State Variants with §13 Branding System (simpler alternative to exile)
- Expanded §4 Companion System with multi-companion interactions
- Added item fragility, rescue sequences, discovery risk properties
- Reorganized section numbering

---

## Table of Contents

1. [Commitment System](#1-commitment-system)
2. [Echo Trust System](#2-echo-trust-system)
3. [Gossip Propagation System](#3-gossip-propagation-system)
4. [Companion System](#4-companion-system) *(expanded)*
5. [Environmental Systems](#5-environmental-systems)
6. [NPC State and Services](#6-npc-state-and-services)
7. [Dialog System Integration](#7-dialog-system-integration)
8. [Waystone and Ending System](#8-waystone-and-ending-system)
9. [Branding and Reputation System](#9-branding-and-reputation-system)
10. [Puzzle System](#10-puzzle-system) *(new)*
11. [Information Network System](#11-information-network-system) *(new)*
12. [Collection Quest System](#12-collection-quest-system) *(new)*
13. [Branding System](#13-branding-system) *(replaces exile)*
14. [Flag System](#14-flag-system)
15. [Turn and Timing System](#15-turn-and-timing-system)
16. [Item and Inventory System](#16-item-and-inventory-system) *(expanded)*
17. [Skill System](#17-skill-system)
18. [Narration Integration](#18-narration-integration)
19. [Consolidated Region Interface](#19-consolidated-region-interface)
20. [Validation and Testing](#20-validation-and-testing)

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

### 1.2 Rescue Sequence Extension (v2.0)

For commitments requiring multi-step rescue (e.g., Delvan):

```json
{
  "commitment_id": "save_delvan",
  "rescue_sequence": {
    "enabled": true,
    "steps": [
      {
        "step_id": "stop_bleeding",
        "description": "Stop the bleeding",
        "conditions": [
          {"type": "item_used", "item": "bandages", "on": "delvan"},
          {"type": "skill_used", "skill": "first_aid", "on": "delvan"}
        ],
        "any_condition_sufficient": true,
        "on_complete": {
          "stops_damage": "bleeding",
          "narration": "The bleeding slows. Delvan's breathing steadies slightly."
        }
      },
      {
        "step_id": "free_from_cargo",
        "description": "Free Delvan from the cargo",
        "conditions": [
          {"type": "item_used", "item": "lever", "on": "cargo"},
          {"type": "stat_check", "stat": "strength", "threshold": 15}
        ],
        "any_condition_sufficient": true,
        "on_complete": {
          "narration": "The cargo shifts. Delvan gasps as pressure releases from his leg."
        }
      },
      {
        "step_id": "mobilize",
        "description": "Help Delvan move",
        "conditions": [
          {"type": "item_used", "item": "splint", "on": "delvan"},
          {"type": "action", "action": "carry", "target": "delvan"}
        ],
        "any_condition_sufficient": true,
        "on_complete": {
          "commitment_fulfilled": true
        }
      }
    ],
    "partial_sequence_partial_credit": true
  }
}
```

### 1.3 Commitment API

```
commitment.register(commitment_id, player)
commitment.check_fulfillment(commitment_id)
commitment.get_active(player) -> List[Commitment]
commitment.get_status(commitment_id) -> CommitmentStatus
commitment.extend_hope(commitment_id, turns, reason)
commitment.complete_rescue_step(commitment_id, step_id)  // v2.0
commitment.get_rescue_progress(commitment_id) -> List[StepStatus]  // v2.0
```

### 1.4 Timer Tick Behavior

Infrastructure handles automatically each turn:
1. Decrement all active timers
2. Check warning thresholds, emit NPC warning dialog if configured
3. On timer expire:
   - Evaluate partial credit conditions (including rescue sequence progress)
   - Apply appropriate trust penalty
   - Set flags, trigger NPC death if configured
   - Schedule gossip events
   - Queue Echo commentary for next Nexus visit

---

## 2. Echo Trust System

Echo is the central moral tracking entity. Infrastructure manages all trust accounting.

### 2.1 Trust Event Schema

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
    "crystal_restored": {
      "trust_delta": 1.0,
      "echo_reaction": "joy"
    }
  }
}
```

### 2.2 Trust Mechanics

**Trust Range**: -6 to unbounded positive (5+ is "high")

**Recovery Cap**: Maximum +1.0 trust gain per Nexus visit

**Trust Floor Behavior** (trust <= -6):
- Echo refuses to manifest
- Commitment tracking continues internally but player loses UI
- Game remains completable (pyrrhic ending tier)

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

### 2.3 Echo Manifestation (v2.0)

Echo appearance is probabilistic based on trust and context:

```json
{
  "echo_manifestation": {
    "base_chance": 0.2,
    "trust_modifier": 0.1,
    "cooldown_turns": 5,
    "minimum_chance_at_negative": 0.05,
    "refuses_below_trust": -3,

    "guaranteed_appearances": [
      {"event": "first_keepers_quarters_entry"},
      {"event": "waystone_repair_complete"},
      {"event": "commitment_abandoned", "duration": "brief"}
    ]
  }
}
```

### 2.4 Echo API

```
echo.queue_commentary(type, context)
echo.get_pending_commentary() -> List[Commentary]
echo.manifest() -> bool
echo.get_appearance_chance() -> float  // v2.0
echo.force_appearance(event_type)  // v2.0
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
        "recovery_possible": true
      },
      "discovered_via_gossip": {
        "trust_delta": -3,
        "recovery_possible": false
      }
    }
  }
}
```

### 3.3 Relationship Foreshadowing

To help players understand that confession windows exist, NPCs establish relationships through early dialog that implies gossip consequences later.

**Design Pattern**: When an NPC might be affected by gossip about another NPC, establish the relationship explicitly during first conversation with either party. When the triggering event occurs, have Echo comment on the relationship.

**Example: Sira-Elara Connection**
```json
{
  "foreshadowing": {
    "relationship": "sira_elara",
    "established_by": {
      "npc": "sira",
      "dialog_topic": "elara_connection",
      "trigger": "first_conversation OR player_offers_help",
      "text": "If I don't make it... there's a healer in the town to the south. Elara. She's... we're close. Tell her what happened to me. She deserves to know.",
      "sets_flag": "knows_sira_elara_connection"
    },
    "reinforced_by": {
      "npc": "sira",
      "on_event": "player_withdraws_commitment",
      "text": "Elara - the healer I mentioned - she'd help. We've been through a lot together."
    },
    "echo_reminder": {
      "on_event": "sira_dies",
      "text": "The hunter is gone. And somewhere in the town, a healer will grieve when word reaches her.",
      "implies": "Gossip will reach Elara - confession is possible"
    }
  }
}
```

**Effect**: Player learns early that Sira and Elara are connected. When Sira dies, Echo's comment reminds the player of this connection and implies word will spread. The player can then infer that confessing to Elara before she hears through gossip might be worthwhile.

### 3.4 Gossip API

```
gossip.schedule(gossip_id, source_turn)
gossip.has_arrived(gossip_id, npc_id) -> bool
gossip.confess(gossip_id, to_npc)
gossip.get_available_confessions(player) -> List[ConfessionOpportunity]
```

---

## 4. Companion System (Expanded in v2.0)

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
    "combat_support": {"damage_bonus": 15},
    "tracking": true,
    "warmth_sharing": {"hypothermia_reduction": 0.2}
  },

  "region_restrictions": {
    "nexus": {
      "allowed": false,
      "reason": "wards_repel",
      "wait_behavior": "outside_nexus_entrance"
    },
    "civilized_remnants": {
      "surface": {"allowed": false, "reason": "guards_refuse"},
      "undercity": {"allowed": true}
    }
  },

  "death_conditions": {
    "sacrifice_for_player": {
      "trigger": "player_would_die_in_combat",
      "echo_reaction": "grief_heroic"
    }
  }
}
```

### 4.2 Multi-Companion Interactions (v2.0)

```json
{
  "multi_companion_interactions": {
    "wolf_pack": {
      "with_sira": {
        "initial_state": "hostile",
        "conflict_reason": "sira_partner_killed_by_wolves",
        "resolution": {
          "type": "reconciliation_dialog",
          "dialog_id": "wolf_sira_reconciliation",
          "requires": {
            "sira_trust": ">=2",
            "wolf_gratitude": ">=3",
            "player_initiates": true
          }
        },
        "unresolved_behavior": "one_must_wait",
        "resolved_effects": {
          "sira_flag_set": "accepts_wolves",
          "narration": "Sira's hand slowly moves away from her weapon. 'Fine. I'll try.'"
        }
      },
      "with_salamander": {
        "initial_state": "wary",
        "resolution": {
          "type": "automatic",
          "turns_together": 3
        }
      }
    }
  }
}
```

### 4.3 Companion Boundary Behavior

Infrastructure handles automatically:

1. **On Region Entry Attempt**:
   - Check companion restrictions for target region
   - If blocked: emit narration, move companion to wait location

2. **On Region Exit**:
   - Auto-rejoin companion from wait location

3. **Multi-Companion Conflict**:
   - Check `multi_companion_interactions`
   - If unresolved hostile: present choice to player
   - Track turns together for automatic resolution

### 4.4 Companion API

```
companion.acquire(companion_type, source_npc)
companion.can_enter(companion, region) -> (bool, reason)
companion.get_active(player) -> List[Companion]
companion.get_waiting() -> Dict[Companion, Location]
companion.check_interaction(companion_a, companion_b) -> InteractionState
companion.resolve_interaction(companion_a, companion_b, resolution_event)
companion.die(companion, cause)
companion.get_conflict_resolution_options() -> List[Resolution]  // v2.0
```

---

## 5. Environmental Systems

### 5.1 Environmental Condition Schema

```json
{
  "condition_type": "hypothermia",
  "category": "progressive",

  "acquisition": {
    "exposure_zones": ["cold", "freezing", "extreme_cold"],
    "rate_per_zone": {
      "cold": 5,
      "freezing": 10,
      "extreme_cold": 20
    }
  },

  "progression": {
    "stages": [
      {"severity": "0-30", "effects": ["movement_slowed"]},
      {"severity": "31-60", "effects": ["combat_penalty"], "combat_modifier": -2},
      {"severity": "61-90", "effects": ["health_damage"], "damage_per_turn": 5},
      {"severity": "91-100", "effects": ["collapse"]}
    ]
  },

  "protection": {
    "cold_weather_gear": {"multiplier": 0.5, "zones": ["cold", "freezing"]},
    "cold_resistance_cloak": {"immunity": ["cold"], "multiplier": 0.5, "zones": ["freezing", "extreme_cold"]},
    "salamander_aura": {"immunity": ["cold", "freezing", "extreme_cold"]}
  },

  "treatment": {
    "normal_zone": {"recovery_rate": 10},
    "hot_springs": {"instant_cure": true}
  }
}
```

### 5.2 Environmental Zone Schema

```json
{
  "zone_type": "extreme_cold",
  "applies_to_rooms": ["frozen_observatory"],

  "effects_per_turn": [
    {
      "condition": "hypothermia",
      "acquisition_rate": 20,
      "blocked_by": ["salamander_aura"]
    }
  ],

  "time_limit": {
    "without_protection": 5,
    "with_cloak": 15,
    "with_salamander": null
  }
}
```

### 5.3 Environmental Spread Schema

```json
{
  "spread_id": "cold_spread",
  "trigger": {
    "condition": "NOT telescope_repaired",
    "check_at_turn": 75
  },

  "stages": [
    {
      "turn": 75,
      "effects": [
        {"add_zone": "cold", "to_rooms": ["beast_wilds_high_ground"]}
      ]
    },
    {
      "turn": 125,
      "effects": [
        {"add_zone": "cold", "to_rooms": ["nexus_boundary_areas"]}
      ]
    }
  ],

  "halted_by": [
    {"flag": "telescope_repaired"},
    {"flag": "waystone_repaired"}
  ]
}
```

### 5.4 Environmental API

```
environment.apply_zone_effects(room, actors)
environment.check_spread_progression(turn)
environment.is_halted(spread_id) -> bool
environment.get_protection_status(actor, zone) -> ProtectionLevel
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

  "services": [
    {
      "service_id": "teach_advanced_herbalism",
      "available_when": {"trust": ">=5"},
      "cost": {"quest_completed": "elara_personal_quest"},
      "one_time": true,
      "grants_skill": "advanced_herbalism",
      "permanently_lost_if": "elara_dead",
      "discovery_risk": null
    }
  ],

  "reactions": {
    "on_flag": {
      "aldric_saved": {"trust_delta": 1},
      "sira_saved": {"trust_delta": 1},
      "elara_knows_sira_fate": {"dialog_unlock": "sira_grief"}
    }
  }
}
```

### 6.2 Service Discovery Risk (v2.0)

For services with risk of detection (undercity):

```json
{
  "service_id": "fence_stolen_goods",
  "npc_id": "the_fence",
  "discovery_risk": {
    "enabled": true,
    "chance_per_use": 0.05,
    "cumulative": false,
    "on_discovery": {
      "reputation_delta": {"town": -2},
      "flags_set": ["undercity_service_discovered"],
      "threshold_effect": {
        "discoveries_for_exile": 3
      }
    }
  }
}
```

### 6.3 NPC API

```
npc.get_services(npc_id, player) -> List[AvailableService]
npc.use_service(npc_id, service_id, player)
npc.get_trust(npc_id) -> float
npc.modify_trust(npc_id, delta, reason)
npc.check_discovery_roll(service_id) -> bool  // v2.0
npc.get_discovery_count(player, category) -> int  // v2.0
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
    "requires_not_flags": ["aldric_dead", "aldric_commitment_active"]
  },

  "content": {
    "opening": "The scholar's hands tremble...",
    "choices": [
      {
        "id": "promise_help",
        "text": "I'll find it for you.",
        "effects": {
          "create_commitment": "save_aldric",
          "trust_delta": 1
        }
      }
    ]
  }
}
```

### 7.2 Dialog Integration Points

Infrastructure connects dialogs to:
- `create_commitment`: Commitment system
- `schedule_gossip`: Gossip system
- `confess`: Confession evaluation
- `modify_trust`: NPC trust
- `set_flag`: Flag system
- `start_puzzle`: Puzzle system (v2.0)
- `update_collection`: Collection quest system (v2.0)

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
      }
    },
    "town_seal": {
      "source_region": "civilized_remnants",
      "acquisition": {
        "type": "multiple_paths",
        "paths": [
          {"flag": "hero_status", "from": "council"},
          {"flag": "guardian_repaired", "from": "council"},
          {"flag": "branded", "flag2": "guardian_repaired", "from": "asha", "via": "asha_mercy_mechanism"}
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
    "requires": {"all_fragments_placed": true},

    "tiers": [
      {"name": "triumphant", "trust_range": [5, null], "blocked_by_locks": ["triumphant_ending"]},
      {"name": "successful", "trust_range": [3, 4.99]},
      {"name": "bittersweet", "trust_range": [0, 2.99]},
      {"name": "hollow_victory", "trust_range": [-2, -0.01]},
      {"name": "pyrrhic", "trust_range": [-5, -2.01]},
      {"name": "pyrrhic_extreme", "trust_range": [null, -5.01]}
    ]
  }
}
```

### 8.3 Waystone API

```
waystone.place_fragment(fragment_id)
waystone.get_placed_fragments() -> List[FragmentId]
waystone.is_complete() -> bool
waystone.complete_ritual() -> Ending
```

---

## 9. Branding and Reputation System

### 9.1 Reputation Schema

```json
{
  "reputation_systems": {
    "town": {
      "initial": 0,
      "range": [-10, 10],
      "branding_threshold": -5,

      "on_branding": {
        "sets_flag": "branded",
        "triggers_event": "branding_ceremony",
        "effects": {
          "service_prices": 2.0,
          "teaching_unavailable": true,
          "council_quests_unavailable": true,
          "trust_caps": {"all_npcs": 2},
          "stealing_impossible": true,
          "hero_status_blocked": true
        }
      },

      "recovery": {
        "per_heroic_act": 1.0,
        "heroic_acts": {"guardian_repaired": 3, "major_npc_saved": 1},
        "un_branding_threshold": 3,
        "un_branding_requires": ["heroic_act_while_branded"]
      }
    },
    "undercity": {
      "initial": 0,
      "range": [-5, 5],
      "separate_from": "town"
    }
  }
}
```

### 9.2 Branding Ceremony Schema

```json
{
  "branding_ceremony": {
    "trigger": {"reputation": {"town": "<=-5"}},

    "event_sequence": [
      {"type": "narration", "text": "Guards seize you in the market square. A crowd gathers."},
      {"type": "narration", "text": "Councilor Hurst reads your crimes aloud. The crowd murmurs."},
      {"type": "narration", "text": "A brazier is brought forward. The iron glows red."},
      {"type": "narration", "text": "The brand sears into your hand. The pain is blinding. When it fades, the mark remains - a broken circle, the sign of the outcast."}
    ],

    "sets_flag": "branded",
    "brand_location": "hand",
    "brand_symbol": "broken_circle",
    "crime_specific": false,
    "permanent_mark": true,

    "npc_dialog_variants": {
      "branded_greeting": "All NPCs have alternate greetings acknowledging the brand",
      "example_maren": "'I see you bear the mark. I'll still trade with you - coin is coin - but don't expect favors.'",
      "example_elara": "'The brand... I've treated worse people. But I won't teach you. Not anymore.'"
    }
  }
}
```

### 9.3 Un-branding / Redemption Schema

```json
{
  "un_branding": {
    "requirements": {
      "reputation_threshold": 3,
      "heroic_act_while_branded": true
    },

    "ceremony": {
      "location": "council_hall",
      "initiated_by": "councilor_asha",
      "narration": [
        "Asha places her hand over the brand. Light flares from her palm.",
        "When she removes her hand, the scar remains - but transformed.",
        "The broken circle now appears almost like a badge. A mark of one who fell and rose again.",
        "'The mark cannot be erased,' Asha says quietly. 'But its meaning can change.'"
      ]
    },

    "effects": {
      "removes_flag": "branded",
      "sets_flag": "redeemed",
      "service_prices": "normal",
      "teaching_available": true,
      "trust_caps": "removed",
      "scar_remains": true
    },

    "ending_implications": {
      "branded_blocks": ["triumphant", "successful"],
      "branded_best_ending": "bittersweet",
      "redeemed_unlocks": ["triumphant", "successful"],
      "note": "Un-branding is required for good endings"
    },

    "permanent_consequences": {
      "assassination_discovered": "un_branding_unavailable"
    }
  }
}
```

### 9.4 Assassination Schema

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
        "locks": ["triumphant_ending"]
      }
    }
  }
}
```

---

## 10. Puzzle System (NEW in v2.0)

Puzzles are environmental challenges with multiple solution paths.

### 10.1 Puzzle Schema

```json
{
  "puzzle_id": "guardian_deactivation",
  "location": "temple_sanctum",
  "puzzle_type": "multi_solution",

  "initial_state": {
    "guardians_hostile": true,
    "password_known": false,
    "crystal_placed": false
  },

  "solutions": [
    {
      "solution_id": "password",
      "type": "verbal",
      "trigger": {
        "type": "speech",
        "pattern": "Fire-that-gives-life and water-that-cleanses, united in purpose",
        "partial_patterns": [
          {"pattern": "Fire-that-gives-life", "hint": "The guardians pause, waiting for more..."}
        ]
      },
      "discovery_sources": [
        {"item": "lore_tablets", "reveals": "full_password"},
        {"item": "keeper_journal", "reveals": "partial_password"},
        {"location": "temple_inscriptions", "reveals": "hint_about_elements"}
      ],
      "on_success": {
        "sets_state": {"guardians_hostile": false, "guardians_passive": true},
        "narration": "The guardians lower their arms. They will permit passage."
      }
    },
    {
      "solution_id": "control_crystal",
      "type": "item_use",
      "trigger": {
        "type": "item_used",
        "item": "control_crystal",
        "target": "guardian"
      },
      "item_source": {
        "location": "ice_caves_side_passage",
        "extraction_required": true
      },
      "on_success": {
        "sets_state": {"guardians_hostile": false, "guardians_serving": true},
        "narration": "The guardians bow. They await your commands."
      }
    },
    {
      "solution_id": "ritual_offering",
      "type": "item_combination",
      "trigger": {
        "type": "items_placed",
        "items": ["fire_aspected_item", "hot_springs_water"],
        "location": "altar"
      },
      "on_success": {
        "sets_state": {"guardians_hostile": false, "guardians_passive": true},
        "consumes_items": true
      }
    },
    {
      "solution_id": "combat",
      "type": "combat",
      "difficulty": "extreme",
      "design_note": "Deliberately punishing - puzzle solutions preferred",
      "on_success": {
        "sets_state": {"guardians_destroyed": true},
        "permanent_consequences": ["control_crystal_useless", "guardian_protection_lost"]
      }
    }
  ],

  "failure_handling": {
    "password_wrong": {
      "effect": "Guardians attack",
      "recovery": "Player can flee, try again with correct password"
    }
  }
}
```

### 10.2 Light/State Puzzle Schema

For puzzles with cumulative state changes:

```json
{
  "puzzle_id": "illuminate_grotto",
  "location": "luminous_grotto",
  "puzzle_type": "cumulative_state",

  "state_tracking": {
    "light_level": {
      "initial": 2,
      "target": 6,
      "on_target_reached": {
        "reveals": "ceiling_inscription",
        "sets_flag": "safe_path_known"
      }
    }
  },

  "interactions": {
    "fill_bucket": {
      "source": "pool",
      "target": "bucket",
      "effect": {"bucket_charges": 3}
    },
    "pour_on_mushroom": {
      "requires": {"bucket_charges": ">=1"},
      "consumes": {"bucket_charges": 1},
      "per_target_effects": {
        "blue_mushroom": {"light_level": "+1"},
        "gold_mushroom": {"light_level": "+2"},
        "violet_mushroom": {"light_level": 0, "applies_condition": "fungal_infection", "severity": 15},
        "black_mushroom": {"light_level": "-2"}
      }
    }
  },

  "hints": {
    "from_item": {
      "aldric_journal": "Blue and gold glow brighter. Violet releases spores. Black absorbs light."
    },
    "observable": {
      "blue_mushroom": {"trait": "steady pulse", "implies": "safe"},
      "gold_mushroom": {"trait": "irregular pulse", "implies": "powerful"},
      "violet_mushroom": {"trait": "rapid pulse", "implies": "dangerous"},
      "black_mushroom": {"trait": "no pulse", "implies": "absorbs"}
    }
  }
}
```

### 10.3 Puzzle API

```
puzzle.get_state(puzzle_id) -> PuzzleState
puzzle.attempt_solution(puzzle_id, solution_type, params) -> Result
puzzle.interact(puzzle_id, interaction_id, params) -> Result
puzzle.get_available_hints(puzzle_id) -> List[Hint]
puzzle.check_completion(puzzle_id) -> bool
```

---

## 11. Information Network System (NEW in v2.0)

Extends gossip to handle different types of information propagation.

### 11.1 Network Types

```json
{
  "information_networks": {
    "spore_network": {
      "type": "instant",
      "scope": "fungal_creatures",
      "events_tracked": ["fungal_creature_killed", "spore_mother_healed"],
      "propagation": "immediate_to_all_fungal",
      "effects": {
        "on_fungal_creature_killed": {
          "sets_global_flag": "has_killed_fungi",
          "myconid_trust_modifier": -3,
          "applies_on_first_interaction": true
        }
      }
    },
    "merchant_network": {
      "type": "delayed",
      "scope": "merchants",
      "delay_base": 5,
      "events_tracked": ["large_sale", "theft_from_merchant"]
    },
    "gossip_network": {
      "type": "delayed",
      "scope": "named_npcs",
      "delay_varies": true
    }
  }
}
```

### 11.2 Network Event Schema

```json
{
  "network_event": {
    "event_id": "player_killed_sporeling",
    "network": "spore_network",
    "trigger": {
      "type": "npc_death",
      "npc_property": {"fungal": true},
      "caused_by": "player"
    },
    "propagation": {
      "immediate_to": ["all_fungal_creatures"],
      "effect_on_recipients": {
        "trust_modifier": -1,
        "disposition_change": "more_hostile"
      }
    },
    "echo_notification": true
  }
}
```

### 11.3 Network API

```
network.broadcast(network_id, event_id, context)
network.has_received(npc_id, event_id) -> bool
network.get_npc_knowledge(npc_id) -> List[KnownEvent]
network.check_first_interaction_effects(npc_id) -> List[Effect]
```

---

## 12. Collection Quest System (NEW in v2.0)

For quests requiring collection of abstract items or information.

### 12.1 Collection Quest Schema

```json
{
  "collection_quest_id": "archivist_knowledge",
  "quest_giver": "the_archivist",
  "display_name": "The Lost Knowledge",

  "collectibles": {
    "type": "knowledge_fragments",
    "total_available": 5,
    "required_for_completion": 3,

    "fragments": [
      {
        "fragment_id": "merchant_ledger",
        "location": "merchant_warehouse",
        "acquisition": {"type": "search", "container": "delvan_desk"},
        "description": "Trade routes and contacts before the disaster"
      },
      {
        "fragment_id": "survivor_story",
        "location": "survivor_camp",
        "acquisition": {
          "type": "dialog",
          "npc": "old_swimmer_jek",
          "dialog_id": "jek_disaster_story",
          "requires": {"trust": ">=1"}
        },
        "description": "Firsthand account of the flooding"
      },
      {
        "fragment_id": "garrett_map",
        "location": "sea_caves",
        "acquisition": {
          "type": "npc_gift",
          "npc": "garrett",
          "requires_flag": "garrett_rescued"
        },
        "description": "Maps of underwater passages",
        "bonus": "Comes from rescued NPC"
      }
    ]
  },

  "rewards": {
    "at_minimum": {
      "unlocks": "water_pearl_available",
      "trust_delta": 2
    },
    "at_all_collected": {
      "bonus_item": "archivist_blessing",
      "trust_delta": 3
    }
  },

  "design_note": "Some fragments come from rescued NPCs, creating value in those relationships beyond immediate rewards."
}
```

### 12.2 Collection API

```
collection.start_quest(quest_id)
collection.add_fragment(quest_id, fragment_id)
collection.get_progress(quest_id) -> (collected, required, total)
collection.check_completion(quest_id) -> bool
collection.get_fragment_sources(quest_id) -> List[Source]
```

---

## 13. Branding System (Replaces Exile in v2.0)

Branding is a public punishment that marks the player as an outcast without changing location access. It provides dramatic consequence for severe reputation damage while being simpler to implement than exile state variants.

### 13.1 Design Rationale

**Why Branding Instead of Exile**:
- No location access changes needed (simpler implementation)
- Visible, permanent mark creates narrative weight
- Public ceremony provides dramatic moment
- All content remains accessible, but with consequences
- Un-branding ceremony provides redemption arc
- Saves ~6-8 days implementation time

### 13.2 Branding Effects Summary

| Effect | Implementation |
|--------|----------------|
| Service prices doubled | Price modifier flag check |
| Teaching services unavailable | Service gating flag check |
| Council quests unavailable | Quest gating flag check |
| NPC trust capped at 2 | Trust ceiling flag check |
| Stealing impossible | Action blocking flag check |
| Hero status blocked | Reputation cap flag check |
| Good endings blocked | Ending determination flag check |

### 13.3 Asha Mercy Mechanism

When a branded player repairs the guardian:

```json
{
  "asha_mercy_mechanism": {
    "trigger": {
      "flag_required": "branded",
      "flag_required_2": "guardian_repaired"
    },

    "scene": {
      "location": "broken_statue_hall",
      "npc": "councilor_asha",
      "narration": [
        "Asha watches as the guardian's eyes flicker to life.",
        "'You bear the mark of our judgment,' she says. 'And yet you restored what we could not.'",
        "'I don't understand you. I don't forgive you. But I cannot deny what you've done.'",
        "She produces the town seal. 'The council voted. Hurst said a tool is a tool. Varn called it good business.'",
        "'I abstained. Take it. Finish what you started.'"
      ]
    },

    "effects": {
      "grants_item": "town_seal",
      "sets_flag": "asha_acknowledged_guardian"
    },

    "design_note": "This allows branded players to complete the game while maintaining the weight of their choices. The scene is uncomfortable, not triumphant."
  }
}
```

### 13.4 Branding API

```
branding.check_threshold(reputation) -> bool
branding.trigger_ceremony()
branding.is_branded() -> bool
branding.get_effects() -> List[BrandingEffect]
branding.check_unbranding_eligible() -> bool
branding.trigger_unbranding_ceremony()
branding.is_redeemed() -> bool
```

---

## 14. Flag System

### 14.1 Flag Categories

```json
{
  "flag_categories": {
    "npc_state": ["aldric_saved", "aldric_dead", "sira_companion"],
    "quest_state": ["archivist_quest_complete", "telescope_repaired"],
    "knowledge": ["knows_elara_connection", "knows_temple_password"],
    "player_state": ["branded", "redeemed", "hero_status"],
    "locks": ["triumphant_ending_locked"],
    "network_flags": ["has_killed_fungi"]
  }
}
```

### 14.2 Flag API

```
flags.set(flag_name)
flags.unset(flag_name)
flags.is_set(flag_name) -> bool
flags.get_all_matching(pattern) -> List[str]
```

---

## 15. Turn and Timing System

### 15.1 Turn Tick Order

Each turn, infrastructure processes in this order:

1. **Environmental effects**: Apply zone effects to all actors
2. **Condition progression**: Advance progressive conditions
3. **Commitment timers**: Decrement, check warnings, handle expirations
4. **Information networks**: Process instant propagation
5. **Gossip propagation**: Advance delayed gossip
6. **Environmental spreads**: Check and advance if applicable
7. **NPC relocations**: Execute scheduled moves
8. **Companion interactions**: Advance automatic resolutions
9. **Puzzle state decay**: Handle temporary puzzle states
10. **Discovery risk accumulation**: Track service usage

### 15.2 Turn API

```
turn.get_current() -> int
turn.schedule(event, delay_turns)
turn.cancel_scheduled(event_id)
```

---

## 16. Item and Inventory System (Expanded in v2.0)

### 16.1 Item Schema

```json
{
  "item_id": "crystal_lens",
  "display_name": "Crystal Lens",
  "type": "component",

  "properties": {
    "portable": true,
    "fragile": {
      "enabled": true,
      "destruction_conditions": [
        {"action": "rough_extraction", "chance": 0.5},
        {"action": "drop_from_height", "chance": 0.8}
      ],
      "destroyed_permanently": true,
      "destruction_narration": "The lens cracks, then shatters into useless fragments."
    }
  },

  "extraction": {
    "required": true,
    "location": "ice_caves_deep",
    "frozen_in_ice": true,
    "extraction_methods": [
      {"method": "heat_source", "success": true, "safe": true},
      {"method": "chipping", "success": true, "safe": false, "fragile_risk": true}
    ]
  },

  "use_in": ["telescope_repair"]
}
```

### 16.2 Item API

```
item.acquire(item_id, method) -> Result
item.check_extraction_requirements(item_id) -> List[Requirement]
item.attempt_extraction(item_id, method) -> Result  // v2.0
item.is_destroyed(item_id) -> bool  // v2.0
```

---

## 17. Skill System

### 17.1 Skill Schema

```json
{
  "skill_id": "swimming_advanced",
  "display_name": "Advanced Swimming",

  "acquisition": {
    "taught_by": ["garrett"],
    "requires_flag": "garrett_rescued",
    "requires_recovery_turns": 5,
    "payment": "none"
  },

  "effects": {
    "breath_extension": 20,
    "navigation_bonus": ["currents_safe", "fish_avoidance"],
    "unlocks_locations": ["deep_archive"]
  },

  "skill_gated_navigation": {
    "tidal_passage": {
      "no_skill": {"risk": "high", "turns": 3, "fish_attack": true},
      "basic_swimming": {"risk": "medium", "turns": 2, "fish_attack": true},
      "advanced_swimming": {"risk": "low", "turns": 1, "fish_attack": false}
    }
  }
}
```

### 17.2 Skill API

```
skill.has(skill_id) -> bool
skill.get_navigation_modifier(skill_id, location) -> NavigationResult
skill.check_skill_gate(location) -> SkillRequirement
```

---

## 18. Narration Integration

### 18.1 Narration Event Schema

```json
{
  "narration_events": {
    "commitment_warning": {
      "context": {"npc": "aldric", "turns_remaining": 5},
      "tone": "urgency",
      "elements": ["npc_condition_worsening", "time_pressure"]
    },
    "puzzle_hint": {
      "context": {"puzzle": "guardian_deactivation", "hint_source": "inscription"},
      "tone": "discovery",
      "elements": ["cryptic_message", "player_deduction"]
    },
    "branding_ceremony": {
      "context": {"event": "branding"},
      "tone": "dramatic",
      "elements": ["guards_seizing", "crimes_announced", "hot_iron", "crowd_watching", "permanent_mark"]
    }
  }
}
```

---

## 19. Consolidated Region Interface

### 19.1 What Regions Must Provide

```json
{
  "region_id": "fungal_depths",
  "display_name": "The Fungal Depths",

  "rooms": [],
  "npcs": [],
  "items": [],
  "commitments": [],
  "gossip_events": [],
  "dialogs": [],
  "puzzles": [],
  "collection_quests": [],

  "companion_rules": {},
  "environmental_zones": [],
  "information_network_events": [],
  "waystone_fragment": {}
}
```

### 19.2 What Regions Do NOT Implement

Regions should NOT contain custom behavior code for:
- Timer countdown logic
- Trust modification
- Gossip/network propagation
- Companion boundary checking
- Environmental condition application
- Puzzle state management
- Collection tracking
- State variant handling

### 19.3 Extension Points

For truly unique regional mechanics:

```
hooks.on_room_enter(room_id, callback)
hooks.on_item_use(item_id, target, callback)
hooks.on_dialog_choice(dialog_id, choice_id, callback)
hooks.on_puzzle_interaction(puzzle_id, interaction_id, callback)
```

---

## 20. Validation and Testing

### 20.1 Schema Validation

Infrastructure validates on load:
- All referenced entities exist
- Puzzle solutions are achievable
- Collection quests have sufficient fragments
- State variants have recovery paths
- No orphaned content

### 20.2 Test Scenarios

```
test.simulate_commitment_cascade(commitments, actions) -> Timeline
test.simulate_puzzle_solutions(puzzle_id) -> List[SolutionPath]
test.simulate_state_variant(variant_id, actions) -> VariantState
test.evaluate_ending(trust, locks, fragments) -> Ending
```

---

## Appendix A: Implementation Work Estimates

| System | Complexity | Estimated Effort | Dependencies |
|--------|------------|------------------|--------------|
| Flag System | Low | 1 day | None |
| Turn/Timing | Low | 1 day | None |
| Echo Trust | Medium | 2 days | Flags |
| Commitment | High | 4 days | Flags, Timing, Trust |
| Gossip | Medium | 2 days | Flags, Timing |
| Information Networks | Medium | 2 days | Flags, Gossip |
| Environmental | Medium | 3 days | Conditions |
| Companion | High | 4 days | Flags, Regions |
| NPC/Services | Medium | 3 days | Trust, Flags |
| Puzzle System | High | 4 days | Items, Flags |
| Collection Quests | Medium | 2 days | Items, Flags |
| Branding System | Low | 1 day | Flags, Reputation |
| Waystone/Ending | Medium | 2 days | Trust, Flags |
| Item/Inventory | Medium | 2 days | None |
| Skill System | Low | 1 day | Items |
| Dialog Integration | Medium | 2 days | All above |
| Narration | Medium | 2 days | All above |
| Validation | Medium | 2 days | All above |

**Total Estimated Infrastructure: ~40 days**

---

## Appendix B: Hard-to-Implement/Understand Features

### B.1 Implementation Challenges

| Feature | Challenge | Mitigation |
|---------|-----------|------------|
| Multi-companion reconciliation | Complex state tracking with dialog triggers | Clear state machine, explicit triggers |
| Puzzle partial solutions | Password partial matching, hint revelation | Pattern matching library, hint queue |
| Information network instant propagation | Must process before player sees NPC | Hook into room entry, pre-compute |
| Branding ceremony triggering | Must interrupt gameplay for ceremony | Event queue, clear narration sequence |
| Rescue sequence partial credit | Multiple step tracking | Step completion events, progress UI |
| Item fragility | Permanent destruction feels bad | Clear warnings, multiple items available |

### B.2 Player Understanding Challenges

| Feature | Challenge | Mitigation |
|---------|-----------|------------|
| Hope bonus | Invisible timer extension | Narration hints ("They seem encouraged") |
| Partial credit | Unclear what counts | Echo explains on failure |
| Confession windows | Must confess before gossip | **Relationship foreshadowing** (see §3.3): NPCs establish connections early, Echo reminds of relationships when events occur |
| Discovery risk | Cumulative invisible risk | Occasional "close call" warnings |
| Branding consequences | Unclear why services change | Brand is visible, NPCs reference it in dialog |
| Information networks | Instant knowledge spread | NPC dialog references "the network told us" |

**Confession Window Mitigation Detail**: The original concern was that players wouldn't understand they could confess to an NPC before gossip arrived. The solution uses narrative foreshadowing:
1. NPCs mention their important relationships in early dialog (e.g., Sira mentions Elara when first met)
2. Echo comments on these relationships when triggering events occur ("And somewhere in the town, a healer will grieve...")
3. This gives players enough context to realize confession might help, without spelling it out mechanically

---

## Version History

- v1.0: Initial infrastructure specification
- v2.0: Added Puzzle System, Information Networks, Collection Quests, State Variants; expanded Companion and Item systems
