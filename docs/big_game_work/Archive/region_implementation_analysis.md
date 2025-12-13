# Region Implementation Analysis

This document maps each region to the infrastructure spec v2.0 and analyzes implementation requirements.

## Table of Contents

1. [Implementation Summary](#implementation-summary)
2. [Frozen Reaches](#1-frozen-reaches)
3. [Beast Wilds](#2-beast-wilds)
4. [Sunken District](#3-sunken-district)
5. [Fungal Depths](#4-fungal-depths)
6. [Civilized Remnants](#5-civilized-remnants)
7. [Meridian Nexus](#6-meridian-nexus)
8. [Total Implementation Estimate](#total-implementation-estimate)

---

## Implementation Summary

| Region | Schema Coverage | Custom Modules | Data Authoring | Total Effort |
|--------|----------------|----------------|----------------|--------------|
| Frozen Reaches | 90% | 2 (puzzle, extraction) | 3-4 days | 6-8 days |
| Beast Wilds | 85% | 3 (pack dynamics, reconciliation, territorial) | 4-5 days | 9-11 days |
| Sunken District | 90% | 2 (rescue sequence, skill gate) | 4-5 days | 7-9 days |
| Fungal Depths | 88% | 2 (light puzzle, spore network) | 4-5 days | 8-10 days |
| Civilized Remnants | 85% | 3 (council, branding, discovery) | 5-6 days | 10-12 days |
| Meridian Nexus | 95% | 1 (echo manifestation) | 2-3 days | 4-5 days |

**Total Region Implementation: 44-54 days** (after infrastructure complete)

---

## 1. Frozen Reaches

**Theme**: Endurance, puzzles, patience over urgency

### Infrastructure Mapping

#### Fully Covered by Schema

| Feature | Infrastructure Section | Schema Type |
|---------|----------------------|-------------|
| Temperature zones | §5 Environmental Systems | zone_type with hypothermia rates |
| Hypothermia condition | §5.1 Condition Schema | progressive condition |
| Cold protection items | §5.1 protection rules | multipliers and immunity |
| Salamander befriending | §6.1 NPC Schema | gratitude/trust with threshold |
| Companion boundaries | §4 Companion System | region_restrictions |
| Soft commitment (salamander) | §1 Commitment System | timer: null |
| Telescope repair quest | §12 Collection Quest | multi-component assembly |
| Cold spread prevention | §5.3 Environmental Spread | halted_by flag |

#### Schema Declarations

```json
{
  "region_id": "frozen_reaches",

  "environmental_zones": [
    {
      "zone_id": "frozen_pass",
      "type": "cold",
      "hypothermia_rate": 5,
      "protection_rules": {
        "cold_weather_gear": {"multiplier": 0.5},
        "cold_resistance_cloak": {"immunity": true}
      }
    },
    {
      "zone_id": "frozen_observatory",
      "type": "extreme_cold",
      "hypothermia_rate": 20,
      "time_limit": {
        "without_protection": 5,
        "with_cloak": 15,
        "with_salamander": null
      }
    }
  ],

  "conditions": [
    {
      "condition_id": "hypothermia",
      "category": "progressive",
      "thresholds": [
        {"severity": 30, "effect": "movement_slowed"},
        {"severity": 60, "effect": "combat_penalty", "value": -2},
        {"severity": 80, "effect": "health_damage", "per_turn": 5},
        {"severity": 100, "effect": "collapse"}
      ],
      "treatment": {
        "hot_springs": {"instant_cure": true},
        "normal_zone": {"recovery_rate": 10}
      }
    }
  ],

  "commitments": [
    {
      "commitment_id": "salamander_befriend",
      "npc_id": "steam_salamander_1",
      "timer": null,
      "hope_bonus": null,
      "abandonment_penalty": null
    }
  ],

  "collection_quests": [
    {
      "quest_id": "telescope_repair",
      "components": ["crystal_lens", "mounting_bracket", "cleaning_supplies"],
      "rewards": {
        "reveals": ["npc_states_all_regions", "spore_mother_health", "waystone_requirements"],
        "global_effect": "cold_spread_prevented",
        "crystal_garden": "+1"
      }
    }
  ]
}
```

#### Requires Custom Modules

1. **Guardian Deactivation Puzzle** (§10 Puzzle System)
   - Multi-solution: password, control crystal, ritual offering, combat
   - Password partial matching
   - **Effort**: 2 days

2. **Ice Extraction Mechanics** (§16 Item Fragility)
   - Heat source detection
   - Fragile item handling (crystal lens)
   - **Effort**: 1 day

### Data Authoring Requirements

| Content Type | Count | Effort per Item | Total |
|--------------|-------|-----------------|-------|
| Locations | 5 | 0.5 days | 2.5 days |
| NPCs | 5 (3 salamanders, 2 golems) | 0.3 days | 1.5 days |
| Items | 12 | 0.1 days | 1.2 days |
| Dialog trees | 3 | 0.3 days | 0.9 days |

**Data authoring total**: ~6 days

### Implementation Complexity Notes

**Easy to Implement**:
- Environmental zones (straightforward schema)
- Hypothermia condition (standard progressive condition)
- Salamander gratitude tracking (standard trust system)

**Moderate Complexity**:
- Telescope repair quest (collection quest schema)
- Guardian state machine (standard NPC state)

**Complex**:
- Guardian multi-solution puzzle (needs puzzle system implementation)
- Crystal lens extraction with fragility (item fragility extension)

### Player Understanding Concerns

| Feature | Concern | Mitigation |
|---------|---------|------------|
| Observatory time limit | Sudden hypothermia dangerous | Clear warning on entry, visual countdown |
| Guardian password | Obtuse if hints missed | Multiple hint sources, partial matches help |
| Ice extraction | Fragile item loss frustrating | Warning narration, retry available with different items |

**Total Frozen Reaches: 9-11 days**

---

## 2. Beast Wilds

**Theme**: Territory, trust, moral complexity

### Infrastructure Mapping

#### Fully Covered by Schema

| Feature | Infrastructure Section | Schema Type |
|---------|----------------------|-------------|
| Wolf pack dynamics | §4 Companion System | pack with alpha/followers |
| Spider pack | §4 Companion System | pack with respawn |
| Wolf domestication | §6.1 NPC Schema | gratitude threshold for companion |
| Sira rescue timer | §1 Commitment System | commitment with timer, hope bonus |
| Bear cubs timer | §1 Commitment System | commitment requiring cross-region item |
| Gossip to Elara | §3 Gossip System | sira_death propagation |
| Companion boundaries | §4.1 region_restrictions | wolves can't enter Nexus/town |

#### Schema Declarations

```json
{
  "region_id": "beast_wilds",

  "packs": [
    {
      "pack_id": "wolf_pack",
      "alpha": "alpha_wolf",
      "followers": ["grey_wolf_1", "grey_wolf_2", "grey_wolf_3"],
      "state_follows_alpha": true
    },
    {
      "pack_id": "spider_pack",
      "alpha": "spider_queen",
      "followers": ["giant_spider_1", "giant_spider_2"],
      "respawn_rate": 10
    }
  ],

  "commitments": [
    {
      "commitment_id": "save_sira",
      "npc_id": "hunter_sira",
      "timer": {
        "base_turns": 8,
        "hope_bonus": {"enabled": true, "max_extension": 4},
        "timer_starts": "first_encounter"
      },
      "fulfillment": {
        "conditions": [{"type": "medical_aid_given"}],
        "effects": {"echo_trust": 0.5, "companion_available": true}
      },
      "abandonment": {
        "on_timer_expire": {"npc_death": true, "echo_trust": -1},
        "gossip_schedule": {"gossip_id": "sira_death", "delay": 12, "to": "elara"}
      }
    },
    {
      "commitment_id": "save_bear_cubs",
      "npc_id": "dire_bear",
      "timer": {
        "base_turns": 30,
        "hope_bonus": {"enabled": false},
        "timer_starts": "first_encounter"
      },
      "fulfillment": {
        "conditions": [{"type": "item_given", "item": "healing_herbs", "from": "civilized_remnants"}]
      }
    }
  ],

  "multi_companion_interactions": {
    "wolf_pack": {
      "with_sira": {
        "initial_state": "hostile",
        "conflict_reason": "sira_partner_killed_by_wolves",
        "resolution": {
          "type": "reconciliation_dialog",
          "requires": {"sira_trust": ">=2", "wolf_gratitude": ">=3"}
        }
      }
    }
  }
}
```

#### Requires Custom Modules

1. **Multi-Companion Reconciliation** (§4.2)
   - Wolf-Sira conflict tracking
   - Dialog trigger for resolution
   - **Effort**: 2 days

2. **Territorial Balance** (new)
   - Wolf/spider territory shifts based on kills
   - **Effort**: 1 day

3. **Pack Following Behavior** (§4 extension)
   - Alpha leads, followers follow
   - **Effort**: 1 day

### Data Authoring Requirements

| Content Type | Count | Effort per Item | Total |
|--------------|-------|-----------------|-------|
| Locations | 8 | 0.5 days | 4 days |
| NPCs | 12 (wolves, spiders, bear, sira, bee queen) | 0.3 days | 3.6 days |
| Items | 8 | 0.1 days | 0.8 days |
| Dialog trees | 6 | 0.3 days | 1.8 days |

**Data authoring total**: ~10 days

### Implementation Complexity Notes

**Easy to Implement**:
- Pack alpha/follower structure
- Commitment timers for Sira and cubs
- Basic companion acquisition

**Moderate Complexity**:
- Gossip propagation to Elara
- Wolf domestication with gratitude tracking

**Complex**:
- Wolf-Sira reconciliation (multi-companion interaction)
- Territorial balance (new system)

### Player Understanding Concerns

| Feature | Concern | Mitigation |
|---------|---------|------------|
| Sira timer | 8 turns very short | Clear visual urgency, warning narration |
| Wolf-Sira conflict | Unexpected companion issue | Sira explicitly states her history |
| Cubs needing herbs | Cross-region dependency unclear | Aldric or NPCs mention Civilized Remnants has healers |

**Total Beast Wilds: 14-16 days**

---

## 3. Sunken District

**Theme**: Drowning, dual rescue, water survival

### Infrastructure Mapping

#### Fully Covered by Schema

| Feature | Infrastructure Section | Schema Type |
|---------|----------------------|-------------|
| Water depth zones | §5 Environmental Systems | water_level property |
| Drowning condition | §5.1 Condition Schema | breath tracking |
| Swimming skill effects | §17 Skill System | skill_gated_navigation |
| Garrett timer (physics) | §1 Commitment System | hope_bonus: false |
| Delvan timer (hope works) | §1 Commitment System | hope_bonus: true |
| Companion water restrictions | §4 Companion System | salamander cannot_enter |
| Knowledge fragment quest | §12 Collection Quest | 3 of 5 required |

#### Schema Declarations

```json
{
  "region_id": "sunken_district",

  "environmental_zones": [
    {"zone_id": "flooded_plaza", "water_level": "ankle_to_waist", "breathable": true},
    {"zone_id": "tidal_passage", "water_level": "submerged", "breathable": false},
    {"zone_id": "survivor_camp", "water_level": "dry", "safe_zone": true}
  ],

  "conditions": [
    {
      "condition_id": "drowning",
      "breath_base": 10,
      "skill_modifiers": {
        "basic_swimming": {"breath": 15},
        "advanced_swimming": {"breath": 20}
      },
      "depletion_rate": 1,
      "warning_at": 3,
      "damage_at_zero": 10
    }
  ],

  "commitments": [
    {
      "commitment_id": "save_garrett",
      "npc_id": "sailor_garrett",
      "timer": {
        "base_turns": 5,
        "timer_starts": "room_entry",
        "hope_bonus": {"enabled": false}
      },
      "note": "Physics doesn't care about promises"
    },
    {
      "commitment_id": "save_delvan",
      "npc_id": "merchant_delvan",
      "timer": {
        "base_turns": 10,
        "timer_starts": "first_encounter",
        "hope_bonus": {"enabled": true, "max_extension": 3}
      },
      "rescue_sequence": {
        "steps": [
          {"step_id": "stop_bleeding", "conditions": [{"type": "item_used", "item": "bandages"}]},
          {"step_id": "free_from_cargo", "conditions": [{"type": "item_used", "item": "lever"}]},
          {"step_id": "mobilize", "conditions": [{"type": "item_used", "item": "splint"}]}
        ]
      }
    }
  ],

  "collection_quests": [
    {
      "quest_id": "archivist_knowledge",
      "total_fragments": 5,
      "required": 3,
      "fragments": [
        {"id": "merchant_ledger", "location": "merchant_warehouse"},
        {"id": "survivor_story", "source_npc": "old_swimmer_jek"},
        {"id": "garrett_map", "requires_flag": "garrett_rescued"}
      ]
    }
  ],

  "skills": [
    {
      "skill_id": "swimming_advanced",
      "taught_by": "garrett",
      "requires_flag": "garrett_rescued",
      "requires_recovery_turns": 5,
      "skill_gated_navigation": {
        "tidal_passage": {
          "no_skill": {"risk": "high", "turns": 3},
          "basic_swimming": {"risk": "medium", "turns": 2},
          "advanced_swimming": {"risk": "low", "turns": 1}
        }
      }
    }
  ]
}
```

#### Requires Custom Modules

1. **Multi-Stage Rescue** (§1.2)
   - Sequential step tracking
   - Partial completion credit
   - **Effort**: 2 days

2. **Skill-Gated Navigation** (§17 extension)
   - Different outcomes per skill level
   - **Effort**: 1 day

### Data Authoring Requirements

| Content Type | Count | Effort per Item | Total |
|--------------|-------|-----------------|-------|
| Locations | 8 (including sub-locations) | 0.5 days | 4 days |
| NPCs | 8 | 0.3 days | 2.4 days |
| Items | 10 | 0.1 days | 1 day |
| Dialog trees | 5 | 0.3 days | 1.5 days |

**Data authoring total**: ~9 days

### Implementation Complexity Notes

**Easy to Implement**:
- Water level zones
- Breath tracking (variation of progressive condition)
- Basic swimming skill

**Moderate Complexity**:
- Dual rescue timing (two commitments with different properties)
- Knowledge fragment collection

**Complex**:
- Multi-stage rescue sequence (new schema)
- Skill-gated navigation (new schema)

### Player Understanding Concerns

| Feature | Concern | Mitigation |
|---------|---------|------------|
| Dual rescue timing | Both NPCs dying at once overwhelming | Discovery order matters - can't see both immediately |
| Garrett's short timer | 5 turns feels unfair | Timer starts on room entry, not commitment |
| Delvan rescue steps | Multi-step not obvious | Delvan narrates his needs explicitly |

**Total Sunken District: 12-14 days**

---

## 4. Fungal Depths

**Theme**: Infection, symbiosis, communication

### Infrastructure Mapping

#### Fully Covered by Schema

| Feature | Infrastructure Section | Schema Type |
|---------|----------------------|-------------|
| Spore zones | §5.2 Environmental Zone | spore_level with severity rates |
| Fungal infection | §5.1 Condition Schema | progressive condition |
| Aldric commitment | §1 Commitment System | 50 turn timer with hope |
| Spore Mother commitment | §1 Commitment System | 200 turn timer (not urgent) |
| Myconid trust | §6 NPC System | trust with service gating |
| Sporeling pack | §4 Pack System | alpha (Mother), followers bound |
| Breath holding | §5.1 Condition Schema | held_breath counter |

#### Schema Declarations

```json
{
  "region_id": "fungal_depths",

  "environmental_zones": [
    {"zone_id": "cavern_entrance", "spore_level": "none", "breathable": true},
    {"zone_id": "luminous_grotto", "spore_level": "medium", "infection_rate": 5},
    {"zone_id": "spore_heart", "spore_level": "high", "infection_rate": 10},
    {"zone_id": "deep_root_caverns", "breathable": false, "requires_light": true}
  ],

  "conditions": [
    {
      "condition_id": "fungal_infection",
      "category": "progressive",
      "acquisition_zones": ["medium_spore", "high_spore"],
      "thresholds": [
        {"severity": 20, "effect": "coughing"},
        {"severity": 40, "effect": "visible_patches"},
        {"severity": 60, "effect": "breathing_difficulty"},
        {"severity": 80, "effect": "immobile"},
        {"severity": 100, "effect": "death"}
      ],
      "treatment": {"silvermoss": {"reduction": 40}, "myconid_cure": {"full_cure": true}}
    },
    {
      "condition_id": "held_breath",
      "max_duration": 12,
      "thresholds": [
        {"turns": 8, "warning": "lungs_burning"},
        {"turns": 10, "warning": "critical"},
        {"turns": 12, "effect": "suffocation_damage", "per_turn": 20}
      ]
    }
  ],

  "commitments": [
    {
      "commitment_id": "save_aldric",
      "npc_id": "aldric",
      "timer": {"base_turns": 50, "hope_bonus": {"max_extension": 10}},
      "fulfillment": {"conditions": [{"type": "item_given", "item": "silvermoss"}]}
    }
  ],

  "information_networks": [
    {
      "network_id": "spore_network",
      "type": "instant",
      "scope": "fungal_creatures",
      "events_tracked": ["fungal_creature_killed"],
      "effects": {"myconid_trust_modifier": -3}
    }
  ]
}
```

#### Requires Custom Modules

1. **Mushroom Light Puzzle** (§10)
   - Cumulative light level tracking
   - Per-mushroom water effects
   - **Effort**: 2 days

2. **Spore Network Propagation** (§11)
   - Instant knowledge spread to all fungi
   - First-interaction effect application
   - **Effort**: 1 day

### Data Authoring Requirements

| Content Type | Count | Effort per Item | Total |
|--------------|-------|-----------------|-------|
| Locations | 5 | 0.5 days | 2.5 days |
| NPCs | 6 (Aldric, Mother, 3 sporelings, Elder) | 0.4 days | 2.4 days |
| Items | 15 (mushrooms, moss, equipment) | 0.1 days | 1.5 days |
| Dialog trees | 5 | 0.3 days | 1.5 days |

**Data authoring total**: ~8 days

### Implementation Complexity Notes

**Easy to Implement**:
- Spore zones (environmental schema)
- Fungal infection (progressive condition)
- Breath holding (simple counter)

**Moderate Complexity**:
- Myconid service gating (trust + offering)
- Sporeling pack bound to Mother

**Complex**:
- Mushroom light puzzle (new puzzle type)
- Spore network instant propagation (new network type)

### Player Understanding Concerns

| Feature | Concern | Mitigation |
|---------|---------|------------|
| Spore network | Player may not realize kills are tracked | Myconid dialog explicitly mentions "network remembers" |
| Aldric's immobility | Why can't he get silvermoss himself? | Clear dialog explaining his severity 80 infection |
| Mushroom puzzle | Which mushrooms are safe? | Pulse pattern observable, journal has hints |

**Total Fungal Depths: 11-13 days**

---

## 5. Civilized Remnants

**Theme**: Society, ethics, moral complexity

### Infrastructure Mapping

#### Fully Covered by Schema

| Feature | Infrastructure Section | Schema Type |
|---------|----------------------|-------------|
| Town reputation | §9 Reputation System | reputation with thresholds |
| Undercity reputation | §9 Reputation System | separate reputation |
| Branding trigger | §9.1 on_branding | reputation threshold |
| Branding effects | §13 Branding System | flag-based service/price modifiers |
| Un-branding ceremony | §9.3 Un-branding | redemption path |
| Herbalism skill tiers | §17 Skill System | basic from Maren, advanced from Elara |
| NPC services | §6 NPC Services | trust-gated with costs |
| Elara-Sira connection | §3 Gossip System | cross-region relationship |
| Guardian repair | §12 Collection Quest | multi-component assembly |

#### Schema Declarations

```json
{
  "region_id": "civilized_remnants",

  "reputation_systems": [
    {
      "reputation_id": "town",
      "initial": 0,
      "range": [-10, 10],
      "branding_threshold": -5,
      "on_branding": {
        "sets_flag": "branded",
        "triggers_event": "branding_ceremony",
        "effects": {
          "service_prices": 2.0,
          "teaching_unavailable": true,
          "trust_caps": {"all_npcs": 2},
          "hero_status_blocked": true,
          "good_endings_blocked": true
        }
      },
      "recovery": {
        "per_heroic_act": 1.0,
        "un_branding_threshold": 3
      }
    },
    {
      "reputation_id": "undercity",
      "initial": 0,
      "range": [-5, 5],
      "unlocked_by": ["delvan_rescued", "payment_to_broker"]
    }
  ],

  "npcs": [
    {
      "npc_id": "herbalist_maren",
      "services": [
        {"service_id": "teach_basic_herbalism", "trust_required": 2, "payment": "50 gold"}
      ]
    },
    {
      "npc_id": "healer_elara",
      "services": [
        {"service_id": "teach_advanced_herbalism", "trust_required": 3, "payment": "garden_help"}
      ],
      "trust_sources": {
        "sira_saved": "+2"
      }
    },
    {
      "npc_id": "shadow",
      "services": [
        {
          "service_id": "assassination",
          "discovery_risk": {"chance": 0.2, "on_discovery": {"branding": true}},
          "effects": {"echo_trust": -2, "locks": ["triumphant_ending"], "blocks_un_branding": true}
        }
      ]
    }
  ],

  "branding": {
    "ceremony_location": "market_square",
    "brand_location": "hand",
    "brand_symbol": "broken_circle",
    "un_branding_ceremony": {
      "location": "council_hall",
      "initiated_by": "councilor_asha",
      "requires": {"reputation": ">=3", "heroic_act_while_branded": true}
    }
  },

  "asha_mercy_mechanism": {
    "trigger": {"branded": true, "guardian_repaired": true},
    "grants": "town_seal",
    "narration": "Asha's conflicted acknowledgment of the branded player's heroic act"
  }
}
```

#### Requires Custom Modules

1. **Council Decision System** (new)
   - Multi-outcome choices with councilor reactions
   - Probabilistic outcomes (80/20 trader infection)
   - **Effort**: 3 days

2. **Branding Ceremony** (§13)
   - Public event with narration sequence
   - Flag-based effect application
   - **Effort**: 1 day

3. **Discovery Risk per Service** (§6.2)
   - Per-use probability tracking
   - Cumulative discovery effects
   - **Effort**: 1 day

### Data Authoring Requirements

| Content Type | Count | Effort per Item | Total |
|--------------|-------|-----------------|-------|
| Locations | 8 | 0.5 days | 4 days |
| NPCs | 12 | 0.4 days | 4.8 days |
| Items | 6 | 0.1 days | 0.6 days |
| Dialog trees | 10 | 0.3 days | 3 days |
| Council quests | 3 | 0.5 days | 1.5 days |

**Data authoring total**: ~14 days

### Implementation Complexity Notes

**Easy to Implement**:
- Basic reputation tracking
- Service gating by trust
- Skill teaching

**Moderate Complexity**:
- Two-tier herbalism (Maren basic, Elara advanced)
- Undercity discovery risk
- Sira-Elara gossip connection

**Complex**:
- Council decision multi-outcomes

**Simplified from original design**:
- Branding replaces exile (no location access changes needed)
- Asha mercy mechanism is now straightforward flag check

### Player Understanding Concerns

| Feature | Concern | Mitigation |
|---------|---------|------------|
| Dual reputation | Town vs undercity confusing | Clear UI separation, different NPCs react to each |
| Council decisions | No "right" answer feels arbitrary | Each councilor explicitly states their preference |
| Branding consequences | Why are services different? | Brand is visible on hand, NPCs reference it in dialog |
| Discovery risk | Invisible cumulative risk | Occasional "close call" warnings |
| Un-branding path | How to recover? | Echo and NPCs hint at heroic acts as path to redemption |

**Total Civilized Remnants: 15-18 days**

---

## 6. Meridian Nexus

**Theme**: Safety, guidance, progress tracking

### Infrastructure Mapping

#### Fully Covered by Schema

| Feature | Infrastructure Section | Schema Type |
|---------|----------------------|-------------|
| Absolute safety | §5 Environmental Systems | safe_zone, no_combat |
| Echo trust | §2 Echo Trust System | trust range, sources, effects |
| Crystal restoration | §9 Progress Tracking | per-region crystal buffs |
| Waystone repair | §8 Waystone System | fragment collection |
| Ending determination | §8.2 Ending System | trust tiers |
| Commitment awareness | §1 Commitment System | Echo sees all |
| Item storage | §5 Environmental Systems | temporal_stasis |

#### Schema Declarations

```json
{
  "region_id": "meridian_nexus",

  "environmental_rules": {
    "absolute_safety": true,
    "no_combat": true,
    "temporal_stasis_location": "keepers_quarters"
  },

  "echo_trust": {
    "scale": [-6, 10],
    "initial": 0,
    "sources": {
      "restore_crystal": 1.0,
      "heal_major_npc": 1.0,
      "fulfill_commitment": 0.5,
      "abandon_commitment": -1.0,
      "assassination": -2.0
    },
    "thresholds": {
      "-3": {"effect": "refuses_to_manifest"},
      "5": {"effect": "speaks_name"},
      "6": {"effect": "reveals_backstory"}
    },
    "recovery_cap": "+1 per Nexus visit"
  },

  "waystone_fragments": [
    {"id": "spore_heart", "source_region": "fungal_depths"},
    {"id": "beast_fang", "source_region": "beast_wilds"},
    {"id": "water_pearl", "source_region": "sunken_district"},
    {"id": "ice_shard", "source_region": "frozen_reaches"},
    {"id": "town_seal", "source_region": "civilized_remnants"}
  ],

  "ending_determination": {
    "tiers": [
      {"name": "triumphant", "trust_range": [5, null], "blocked_by": ["assassination"]},
      {"name": "successful", "trust_range": [3, 4.99]},
      {"name": "bittersweet", "trust_range": [0, 2.99]},
      {"name": "hollow_victory", "trust_range": [-2, -0.01]},
      {"name": "pyrrhic", "trust_range": [-5, -2.01]},
      {"name": "pyrrhic_extreme", "trust_range": [null, -5.01]}
    ]
  }
}
```

#### Requires Custom Modules

1. **Echo Manifestation Probability** (§2.3)
   - Base chance + trust modifier
   - Cooldown tracking
   - Guaranteed appearances
   - **Effort**: 2 days

### Data Authoring Requirements

| Content Type | Count | Effort per Item | Total |
|--------------|-------|-----------------|-------|
| Locations | 4 | 0.4 days | 1.6 days |
| NPCs | 1 (Echo) | 1 day | 1 day |
| Items | 6 | 0.1 days | 0.6 days |
| Dialog trees | 3 | 0.3 days | 0.9 days |
| Ending narrations | 7 | 0.3 days | 2.1 days |

**Data authoring total**: ~6 days

### Implementation Complexity Notes

**Easy to Implement**:
- Safe zone rules
- Crystal restoration tracking
- Trust accounting

**Moderate Complexity**:
- Ending determination
- Commitment awareness display
- Telescope region status

**Complex**:
- Echo manifestation probability (new)

### Player Understanding Concerns

| Feature | Concern | Mitigation |
|---------|---------|------------|
| Echo availability | Why won't Echo appear? | Trust meter visible, Echo explains when refusing |
| Recovery cap | Can't grind trust back | Echo hints at "one step at a time" |
| Ending tiers | What determines ending? | Echo commentary throughout game hints at trust state |

**Total Meridian Nexus: 8-10 days**

---

## Total Implementation Estimate

### Infrastructure (from spec v2.0 Appendix A)

| System | Effort |
|--------|--------|
| Flag System | 1 day |
| Turn/Timing | 1 day |
| Echo Trust | 2 days |
| Commitment System | 4 days |
| Gossip System | 2 days |
| Information Networks | 2 days |
| Environmental Systems | 3 days |
| Companion System | 4 days |
| NPC/Services | 3 days |
| Puzzle System | 4 days |
| Collection Quests | 2 days |
| Branding System | 1 day |
| Waystone/Ending | 2 days |
| Item/Inventory | 2 days |
| Skill System | 1 day |
| Dialog Integration | 2 days |
| Narration Integration | 2 days |
| Validation/Testing | 2 days |

**Infrastructure Total: ~40 days**

### Region Implementation

| Region | Effort |
|--------|--------|
| Frozen Reaches | 9-11 days |
| Beast Wilds | 14-16 days |
| Sunken District | 12-14 days |
| Fungal Depths | 11-13 days |
| Civilized Remnants | 15-18 days |
| Meridian Nexus | 8-10 days |

**Regions Total: 69-82 days**

### Grand Total

**Infrastructure + Regions: 109-122 days**

### Recommended Implementation Order

1. **Infrastructure Phase 1** (10 days): Flag, Turn, Echo Trust, Commitment
2. **Meridian Nexus** (8 days): Simplest region, tests core systems
3. **Infrastructure Phase 2** (10 days): Environmental, Companion, NPC
4. **Frozen Reaches** (10 days): Tests environmental, simple commitments
5. **Fungal Depths** (12 days): Tests progressive conditions, networks
6. **Infrastructure Phase 3** (10 days): Puzzle, Collection, Gossip
7. **Sunken District** (13 days): Tests multi-commitment, rescue sequences
8. **Beast Wilds** (15 days): Tests pack dynamics, companion conflicts
9. **Infrastructure Phase 4** (10 days): Branding, Reputation, remaining
10. **Civilized Remnants** (17 days): Most complex region, tests everything

### Hardest-to-Implement Features

| Feature | Region | Difficulty | Why |
|---------|--------|------------|-----|
| Council decisions | Civilized | High | Multi-outcome with councilor tracking |
| Wolf-Sira reconciliation | Beast | High | Multi-companion interaction |
| Guardian puzzle | Frozen | High | Multi-solution with state tracking |
| Spore network | Fungal | Medium-High | Instant propagation, first-interaction |
| Branding ceremony | Civilized | Low | Simple flag + narration event |

### Hardest-to-Understand Features (Player)

| Feature | Region | Risk | Mitigation Strategy |
|---------|--------|------|---------------------|
| Hope bonus | All | Medium | Narration hints ("They seem encouraged") |
| Discovery risk | Civilized | Medium | Occasional "close call" warnings |
| Confession windows | Beast→Civilized | Medium | **Relationship foreshadowing**: Sira mentions Elara when first met; Echo reminds player of connection when Sira dies (see §3.3 of infrastructure spec) |
| Branding effects | Civilized | Low | Brand visible, NPCs reference it explicitly |
| Un-branding path | Civilized | Medium | Echo and NPCs hint at heroic redemption |
| Multi-companion conflict | Beast | Medium | Sira explicitly states history |

**Confession Window Risk Reduction**: Originally marked as High risk because players wouldn't understand they could confess before gossip arrived. The risk has been reduced to Medium through narrative foreshadowing:
- Sira mentions Elara during first encounter: "If I don't make it... find Elara in the town. She's... we're close."
- When Sira dies, Echo reminds player: "The hunter is gone. And somewhere in the town, a healer will grieve when word reaches her."
- This gives players enough context to infer that confessing to Elara might help, without mechanical exposition.
