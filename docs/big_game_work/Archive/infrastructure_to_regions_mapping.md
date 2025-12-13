# Infrastructure to Regions Mapping Analysis

This document analyzes how each region maps to the infrastructure spec, identifying what can be expressed purely through schema declarations vs. what requires custom behavior modules.

## Summary Table

| Region | Schema Coverage | Custom Modules Needed | Infrastructure Gaps |
|--------|----------------|----------------------|---------------------|
| Frozen Reaches | 85% | Puzzle system, Ice extraction | Minor |
| Beast Wilds | 75% | Pack dynamics, Multi-companion reconciliation | Moderate |
| Sunken District | 80% | Multi-stage rescue, Skill gating | Minor |
| Fungal Depths | 80% | Light puzzle, Spore network | Minor |
| Civilized Remnants | 70% | Council decisions, Exile system | Moderate |
| Meridian Nexus | 90% | Echo appearance probability | Minor |

---

## 1. Frozen Reaches Mapping

### Schema-Expressible Systems

#### Environmental Zones (Infrastructure §3)
```json
{
  "zones": {
    "frozen_pass": {
      "type": "cold",
      "hypothermia_rate": 5,
      "protection_rules": {
        "cold_weather_gear": { "multiplier": 0.5 },
        "cold_resistance_cloak": { "immunity": true }
      }
    },
    "ice_caves": {
      "type": "freezing",
      "hypothermia_rate": 10
    },
    "frozen_observatory": {
      "type": "extreme_cold",
      "hypothermia_rate": 20,
      "protection_rules": {
        "cold_weather_gear": { "ineffective": true },
        "cold_resistance_cloak": { "multiplier": 0.5 },
        "salamander_aura": { "immunity": true }
      }
    },
    "hot_springs_refuge": {
      "type": "normal",
      "healing_zone": true,
      "hypothermia_effect": "instant_cure"
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §3 Environmental Conditions

#### Condition System (Infrastructure §4)
```json
{
  "conditions": {
    "hypothermia": {
      "severity_range": [0, 100],
      "acquisition": {
        "per_zone_type": {
          "cold": 5,
          "freezing": 10,
          "extreme_cold": 20
        }
      },
      "thresholds": {
        "30": { "effect": "movement_slowed" },
        "60": { "effect": "combat_penalty", "value": -2 },
        "80": { "effect": "health_damage", "per_turn": 5 },
        "100": { "effect": "collapse" }
      },
      "treatment": {
        "normal_zone": { "recovery_rate": 10 },
        "hot_springs": { "instant_cure": true }
      }
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §4 Condition System

#### Companion Boundaries (Infrastructure §6)
```json
{
  "companion_rules": {
    "wolf_pack": {
      "comfortable_in": ["frozen_pass", "temple_sanctum"],
      "uncomfortable_in": ["ice_caves"],
      "cannot_enter": ["frozen_observatory"],
      "waiting_location": "temple_sanctum"
    },
    "salamander": {
      "home_region": true,
      "comfortable_everywhere": true,
      "provides_aura": "cold_immunity"
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §6 Companion System

#### Commitment System (Infrastructure §1)
```json
{
  "commitments": {
    "salamander_commitment": {
      "trigger_phrases": ["I'll bring you fire", "I'll help warm you"],
      "target": "steam_salamander_1",
      "timer": null,
      "hope_bonus": false,
      "abandonment_penalty": null
    }
  }
}
```
**Infrastructure Fit:** ✅ This is a "soft commitment" - no timer, no penalty. Infrastructure handles this via `timer: null` option.

### Custom Behavior Modules Needed

#### 1. Golem Puzzle System
The temple guardians have multiple deactivation methods that interact:
- **Password recognition**: Parse player speech for specific phrase
- **Control crystal usage**: Item-based full control
- **Ritual offering**: Combination of specific items

**Not covered by infrastructure:** The spec doesn't define a general puzzle/riddle system.

**Proposed module:** `behaviors/puzzles/guardian_deactivation.py`
- Input: player action + current guardian state
- Output: state transition or failure message

#### 2. Ice Extraction Mechanics
Items frozen in ice require:
- Heat source detection
- Careful vs. rough extraction (fragile item handling)
- Permanent destruction on failure

**Not covered by infrastructure:** Item extraction with failure states.

**Proposed module:** `behaviors/environment/ice_extraction.py`

### Infrastructure Gaps Identified

1. **Puzzle/Riddle System**: No general schema for multi-solution puzzles with password/item/ritual alternatives. The commitment system handles NPC relationships but not environmental puzzles.

2. **Item Fragility**: No schema for items that can be permanently destroyed through improper handling.

---

## 2. Beast Wilds Mapping

### Schema-Expressible Systems

#### Pack Dynamics (Infrastructure §5)
```json
{
  "packs": {
    "wolf_pack": {
      "alpha": "alpha_wolf",
      "followers": ["grey_wolf_1", "grey_wolf_2", "grey_wolf_3"],
      "state_follows_alpha": true,
      "location_follows_alpha": true
    },
    "spider_pack": {
      "alpha": "spider_queen",
      "followers": ["giant_spider_1", "giant_spider_2"],
      "respawn_rate": "10_turns"
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §5 Pack System

#### Commitment System (Infrastructure §1)
```json
{
  "commitments": {
    "bear_cubs": {
      "trigger_phrases": ["I'll find medicine", "I'll heal your cubs"],
      "target": "dire_bear",
      "timer": {
        "base": 30,
        "starts_at": "first_encounter",
        "hope_bonus": 5,
        "warning_at": 8
      },
      "abandonment": {
        "flags": ["broke_promise_bear_cubs"],
        "target_becomes": "vengeful",
        "trust_spread": -2
      }
    },
    "sira": {
      "trigger_phrases": ["I'll get help", "I'll save you"],
      "target": "hunter_sira",
      "timer": {
        "base": 8,
        "starts_at": "first_encounter",
        "hope_bonus": 4,
        "warning_at": 3
      }
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §1 Commitment System - including the partial_credit concept when player tries but fails multiple commitments.

#### Companion Boundaries (Infrastructure §6)
```json
{
  "companion_rules": {
    "wolf_pack": {
      "cannot_enter": [
        { "location": "nexus_chamber", "reason": "magical_wards" },
        { "location": "civilized_remnants/*", "reason": "guards_attack" },
        { "location": "spider_nest_gallery", "reason": "territorial_instinct", "override": "exceptional_bravery" }
      ],
      "waiting_behavior": {
        "location": "forest_edge",
        "auto_rejoin": true
      }
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §6, including the "exceptional_bravery" override mechanism

#### Domestication/Trust (Infrastructure §5)
```json
{
  "domestication": {
    "alpha_wolf": {
      "gratitude_threshold": 3,
      "feeding_items": ["venison", "meat"],
      "gratitude_per_feed": 1,
      "max_from_feeding": 4,
      "companion_benefits": ["+15_combat_damage", "tracking", "intimidation"]
    }
  }
}
```
**Infrastructure Fit:** ✅ Covered by §5 Pack/Domestication System

### Custom Behavior Modules Needed

#### 1. Multi-Companion Reconciliation
Wolf pack + Sira requires explicit reconciliation dialog with specific requirements:
- Trust checks on both sides
- Dialog option unlocking
- Prejudice flag removal

**Not fully covered by infrastructure:** The companion system handles boundaries but not interpersonal conflicts between companions.

**Proposed module:** `behaviors/companions/reconciliation.py`

#### 2. Territorial Balance
Wolf/spider balance shifts based on player actions:
- Killing queen → wolves expand
- Killing alpha → spiders expand

**Partially covered:** The pack system handles individual pack states but not inter-pack territorial dynamics.

**Proposed module:** `behaviors/region/territorial_balance.py`

### Infrastructure Gaps Identified

1. **Multi-Companion Interaction**: Need schema for companion-to-companion relationships and reconciliation mechanics.

2. **Regional Territorial Balance**: No schema for how pack destruction affects other packs' behavior.

---

## 3. Sunken District Mapping

### Schema-Expressible Systems

#### Environmental Conditions (Infrastructure §3)
```json
{
  "zones": {
    "flooded_plaza": { "water_level": "ankle_to_waist", "breathable": true },
    "flooded_chambers": { "water_level": "chest", "breathable": true },
    "tidal_passage": { "water_level": "submerged", "breathable": false },
    "merchant_quarter": { "water_level": "over_head", "breathable": false },
    "survivor_camp": { "water_level": "dry", "safe_zone": true }
  }
}
```
**Infrastructure Fit:** ✅ Covered by §3 Environmental Conditions

#### Breath System (Extension of §4)
```json
{
  "conditions": {
    "drowning": {
      "breath_base": 10,
      "breath_with_basic_swimming": 15,
      "breath_with_advanced_swimming": 20,
      "depletion_rate": 1,
      "warning_at": 3,
      "damage_at_zero": 10
    }
  }
}
```
**Infrastructure Fit:** ✅ This is a condition with special tracking - fits §4

#### Commitment System (Infrastructure §1)
```json
{
  "commitments": {
    "garrett": {
      "trigger_phrases": ["I'll save you", "hold on"],
      "target": "sailor_garrett",
      "timer": {
        "base": 5,
        "starts_at": "room_entry",
        "hope_bonus": 0
      },
      "note": "Physics doesn't care about promises"
    },
    "delvan": {
      "trigger_phrases": ["I'll free you", "hold on"],
      "target": "merchant_delvan",
      "timer": {
        "base": 10,
        "starts_at": "first_encounter",
        "hope_bonus": 3
      }
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §1, including the "both_commitment_special" partial credit scenario

#### Companion Boundaries (Infrastructure §6)
```json
{
  "companion_rules": {
    "salamander": {
      "cannot_enter": ["sunken_district/*"],
      "reason": "water_extinguishes",
      "death_if_forced": true,
      "waiting_location": "nexus_chamber"
    },
    "wolf_pack": {
      "uncomfortable_in": ["sunken_district/*"],
      "refuses_swimming": true,
      "waiting_location": "survivor_camp"
    }
  }
}
```
**Infrastructure Fit:** ✅ Covered by §6

### Custom Behavior Modules Needed

#### 1. Multi-Stage Rescue
Delvan rescue requires ordered steps:
1. Stop bleeding
2. Free from cargo (lever or strength)
3. Splint leg or carry

**Not covered by infrastructure:** Sequential prerequisite actions on same target.

**Proposed module:** `behaviors/rescue/multi_stage_rescue.py`

#### 2. Skill-Gated Navigation
Tidal passage has different outcomes based on swimming skill level:
- No skill: high risk
- Basic: 2 turns, fish attack
- Advanced: 1 turn, safe

**Partially covered:** The skill system exists but skill-gated location traversal isn't explicit.

**Proposed module:** `behaviors/navigation/skill_gated_passage.py`

### Infrastructure Gaps Identified

1. **Multi-Stage Rescue**: Need schema for rescue actions that require multiple ordered steps.

2. **Knowledge Fragments**: The archivist's quest requires collecting abstract "knowledge" from various sources - needs a collectible tracking system.

---

## 4. Fungal Depths Mapping

### Schema-Expressible Systems

#### Environmental Spreads (Infrastructure §3)
```json
{
  "spreads": {
    "spore_spread": {
      "zones": {
        "luminous_grotto": { "spore_level": "medium", "exposure_rate": 5 },
        "spore_heart": { "spore_level": "high", "exposure_rate": 10 },
        "cavern_entrance": { "spore_level": "none" },
        "myconid_sanctuary": { "spore_level": "none", "safe_zone": true }
      },
      "condition_caused": "fungal_infection",
      "protection": {
        "breathing_mask": { "immunity": true },
        "spore_resistance": { "multiplier": 0.5 },
        "safe_path_known": { "multiplier": 0.3 }
      }
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §3 Environmental Spreads

#### Condition System (Infrastructure §4)
```json
{
  "conditions": {
    "fungal_infection": {
      "severity_range": [0, 100],
      "progression_rate": 5,
      "thresholds": {
        "20": { "effect": "coughing" },
        "40": { "effect": "visible_patches" },
        "60": { "effect": "breathing_difficulty" },
        "80": { "effect": "immobile" },
        "100": { "effect": "death" }
      },
      "treatment": {
        "silvermoss": { "severity_reduction": 40, "stops_progression": true },
        "myconid_cure": { "full_cure": true }
      }
    },
    "held_breath": {
      "max_duration": 12,
      "thresholds": {
        "8": { "warning": "lungs_burning" },
        "10": { "warning": "critical" },
        "12": { "effect": "suffocation_damage", "per_turn": 20 }
      },
      "recovery": "breathable_room"
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §4

#### Commitment System (Infrastructure §1)
```json
{
  "commitments": {
    "aldric": {
      "trigger_phrases": ["I'll find silvermoss", "I'll help you"],
      "target": "npc_aldric",
      "timer": {
        "base": 50,
        "starts_at": "first_encounter",
        "hope_bonus": 10,
        "warning_at": 10
      },
      "fulfillment_bonus": "+2 gratitude"
    },
    "spore_mother": {
      "trigger_phrases": ["I'll find heartmoss", "I'll heal her"],
      "target": "npc_spore_mother",
      "timer": {
        "base": 200,
        "hope_bonus": 0
      },
      "note": "Very long timer - not urgent"
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §1

#### Pack System (Infrastructure §5)
```json
{
  "packs": {
    "sporeling_pack": {
      "alpha": "npc_spore_mother",
      "followers": ["npc_sporeling_1", "npc_sporeling_2", "npc_sporeling_3"],
      "range_limit": "loc_spore_heart",
      "state_follows_alpha": true
    }
  }
}
```
**Infrastructure Fit:** ✅ Covered by §5

### Custom Behavior Modules Needed

#### 1. Mushroom Light Puzzle
The illuminate_grotto puzzle requires:
- Fill bucket from pool
- Pour water on mushrooms with different effects
- Track cumulative light level
- Reveal inscription at threshold

**Not covered by infrastructure:** General puzzle with stateful interactions.

**Proposed module:** `behaviors/puzzles/mushroom_light.py`

#### 2. Spore Network Knowledge
Myconids know if player has killed fungi anywhere through the spore network.

**Partially covered:** Global flags exist, but automatic flag propagation through "network" isn't specified.

**Proposed module:** `behaviors/information/spore_network.py`

### Infrastructure Gaps Identified

1. **General Puzzle System**: Need schema for environmental puzzles with multiple interaction points and cumulative state.

2. **Information Networks**: The spore network (and later gossip network) requires a system for automatic information propagation between entities.

---

## 5. Civilized Remnants Mapping

### Schema-Expressible Systems

#### Reputation System (Infrastructure §7)
```json
{
  "reputation": {
    "town": {
      "scale": [-10, 10],
      "initial": 0,
      "thresholds": {
        "-5": { "effect": "exile" },
        "-2": { "effect": "suspicious" },
        "2": { "effect": "discounts", "value": 10 },
        "5": { "effect": "hero_status" }
      },
      "sources": {
        "rescue_survivor": "+1",
        "complete_council_quest": "+1 to +3",
        "repair_guardian": "+3",
        "stealing": "-2",
        "undercity_discovered": "-2"
      }
    },
    "undercity": {
      "scale": [-5, 5],
      "separate_from": "town"
    }
  }
}
```
**Infrastructure Fit:** ✅ Covered by §7 Reputation System

#### Companion Boundaries (Infrastructure §6)
```json
{
  "companion_rules": {
    "wolf_pack": {
      "cannot_enter": ["civilized_remnants/*"],
      "reason": "guards_attack",
      "if_forced": { "combat": true, "reputation": -5 }
    },
    "salamander": {
      "uncomfortable_in": ["civilized_remnants/*"],
      "initial_penalty": { "reputation": -1 },
      "incident_chance": 0.05
    }
  }
}
```
**Infrastructure Fit:** ✅ Covered by §6

#### Trust/Services System (Infrastructure §5)
```json
{
  "services": {
    "herbalist_maren": {
      "teach_basic_herbalism": {
        "trust_required": 2,
        "payment": ["50 gold", "rare_plant"]
      }
    },
    "healer_elara": {
      "teach_advanced_herbalism": {
        "trust_required": 3,
        "payment": ["help_in_garden", "50 gold"]
      }
    }
  }
}
```
**Infrastructure Fit:** ✅ Covered by §5 NPC Services

### Custom Behavior Modules Needed

#### 1. Council Decision System
Council quests have multi-outcome decisions with:
- Different councilor reactions
- Probabilistic outcomes (dangerous_traders: 80%/20% clean/infected)
- Hidden options discovered through dialog

**Not covered by infrastructure:** Branching decisions with councilor-specific reactions and probabilistic outcomes.

**Proposed module:** `behaviors/social/council_decisions.py`

#### 2. Exile System
Exile creates alternative gameplay loop:
- Surface locations inaccessible
- Undercity access
- Reputation recovery path
- Guardian repair while exiled triggers asha_mercy_mechanism

**Partially covered:** Reputation thresholds exist but exile as a game state change isn't specified.

**Proposed module:** `behaviors/social/exile_system.py`

#### 3. Undercity Discovery Risk
Each undercity service has 5% discovery chance:
- Cumulative reputation damage
- Can trigger exile

**Not covered by infrastructure:** Probabilistic discovery per service use.

**Proposed module:** `behaviors/social/undercity_risk.py`

### Infrastructure Gaps Identified

1. **Multi-Outcome Decisions**: Need schema for decisions with multiple valid choices and per-faction reactions.

2. **Alternative Game States**: Exile fundamentally changes available locations and NPCs - needs state-change schema.

3. **Probabilistic Events**: Per-action probability checks with cumulative consequences.

---

## 6. Meridian Nexus Mapping

### Schema-Expressible Systems

#### Safe Zone (Infrastructure §3)
```json
{
  "zones": {
    "nexus_chamber": {
      "safe_zone": true,
      "no_combat": true,
      "no_environmental_hazards": true,
      "hostile_repelled": true
    },
    "keepers_quarters": {
      "temporal_stasis": true,
      "items_preserved": true
    }
  }
}
```
**Infrastructure Fit:** ✅ Covered by §3

#### Echo Trust System (Infrastructure §2)
```json
{
  "echo_trust": {
    "scale": [-5, 10],
    "initial": 0,
    "sources": {
      "restore_crystal": "+1",
      "heal_major_npc": "+1",
      "fulfill_commitment": "+0.5",
      "kill_friendly_npc": "-2",
      "abandon_commitment": "-1",
      "assassination": "-2"
    },
    "thresholds": {
      "-3": { "effect": "echo_refuses" },
      "5": { "effect": "speaks_name" },
      "6": { "effect": "reveals_full_backstory" }
    },
    "recovery_cap": "+1 per Nexus visit"
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §2 Echo Trust

#### Ending System (Infrastructure §8)
```json
{
  "endings": {
    "triumphant": {
      "requirements": {
        "trust": 5,
        "crystals": 5,
        "waystone": true
      }
    },
    "successful": {
      "requirements": {
        "trust": 3,
        "crystals": "3+",
        "waystone": true
      }
    },
    "bittersweet": {
      "requirements": {
        "trust": 0,
        "waystone": true
      }
    },
    "hollow_victory": {
      "requirements": {
        "trust": -2,
        "waystone": true
      }
    },
    "pyrrhic": {
      "requirements": {
        "trust": -3,
        "waystone": true
      }
    },
    "abandoned": {
      "requirements": {
        "waystone": false
      }
    }
  }
}
```
**Infrastructure Fit:** ✅ Fully covered by §8 Ending System

#### Crystal Garden Progress (Infrastructure §9)
```json
{
  "crystal_progress": {
    "frozen_crystal": {
      "restores_when": ["telescope_repaired", "major_frozen_healing"],
      "buff": "cold_resistance"
    },
    "fungal_crystal": {
      "restores_when": ["spore_mother_healed", "aldric_saved"],
      "buff": "slow_infection"
    }
  }
}
```
**Infrastructure Fit:** ✅ Covered by §9 Progress Tracking

### Custom Behavior Modules Needed

#### 1. Echo Appearance Probability
Echo has complex appearance mechanics:
- Base chance + trust modifier
- Cooldown between appearances
- Guaranteed appearances at specific events
- Minimum threshold at negative trust
- Refusal below -3

**Partially covered:** Trust thresholds exist but probabilistic appearance isn't in spec.

**Proposed module:** `behaviors/nexus/echo_manifestation.py`

### Infrastructure Gaps Identified

1. **Probabilistic NPC Appearance**: Need schema for NPCs that appear based on probability + trust + cooldown.

---

## Infrastructure Gaps Summary

### Major Gaps (Affect Multiple Regions)

1. **Puzzle System** (Frozen, Fungal)
   - Multi-solution environmental puzzles
   - Password/item/ritual alternatives
   - Cumulative state tracking

   **Recommendation:** Add §10 Puzzle System to infrastructure spec

2. **Information Networks** (Fungal, Civilized)
   - Spore network: automatic flag propagation
   - Gossip system: timed information spread

   **Recommendation:** Add §11 Information Propagation to infrastructure spec (partially covered in §20 Gossip but needs expansion)

3. **Multi-Companion Interactions** (Beast)
   - Companion-to-companion conflicts
   - Reconciliation mechanics

   **Recommendation:** Expand §6 Companion System with companion relationship subsection

4. **Alternative Game States** (Civilized)
   - Exile as fundamental state change
   - Different available locations/NPCs per state

   **Recommendation:** Add §12 Game State Variants to infrastructure spec

### Minor Gaps (Single Region)

5. **Item Fragility** (Frozen)
   - Permanent destruction through improper handling

   **Recommendation:** Add property to Item schema: `fragile: { destruction_conditions: [], permanent: true }`

6. **Multi-Stage Rescue** (Sunken)
   - Sequential prerequisite actions

   **Recommendation:** Add `rescue_sequence` property to commitment schema

7. **Probabilistic Discovery** (Civilized)
   - Per-action probability with cumulative effects

   **Recommendation:** Add `discovery_risk` property to service schema

8. **Collectible Quest Items** (Sunken)
   - Knowledge fragment collection for Archivist

   **Recommendation:** Add §13 Collection Quests to infrastructure spec

---

## Custom Behavior Modules Summary

Based on this analysis, the following custom behavior modules are needed:

### Puzzle Behaviors
- `behaviors/puzzles/guardian_deactivation.py` - Multi-solution temple puzzle
- `behaviors/puzzles/mushroom_light.py` - Cumulative light puzzle

### Environment Behaviors
- `behaviors/environment/ice_extraction.py` - Heat-based item extraction

### Companion Behaviors
- `behaviors/companions/reconciliation.py` - Multi-companion conflict resolution

### Social Behaviors
- `behaviors/social/council_decisions.py` - Multi-outcome decisions
- `behaviors/social/exile_system.py` - Alternative game state
- `behaviors/social/undercity_risk.py` - Probabilistic discovery

### Navigation Behaviors
- `behaviors/navigation/skill_gated_passage.py` - Skill-based traversal

### Rescue Behaviors
- `behaviors/rescue/multi_stage_rescue.py` - Sequential rescue steps

### Region-Specific Behaviors
- `behaviors/region/territorial_balance.py` - Pack territory dynamics
- `behaviors/information/spore_network.py` - Fungal information propagation
- `behaviors/nexus/echo_manifestation.py` - Probabilistic appearance

---

## Recommended Infrastructure Spec Updates

1. **Add §10 Puzzle System**
   - Schema for multi-solution puzzles
   - Password, item, and ritual solution types
   - Cumulative state tracking

2. **Expand §20 Gossip System → §11 Information Propagation**
   - Add network types (spore, gossip, merchant)
   - Automatic flag propagation
   - Timed information spread

3. **Expand §6 Companion System**
   - Add companion-to-companion relationship section
   - Reconciliation trigger mechanics

4. **Add §12 Game State Variants**
   - Schema for alternative game states (exile, alliance modes)
   - Location/NPC availability per state

5. **Add §13 Collection Quests**
   - Schema for collectible tracking
   - Requirements thresholds
   - Source-based bonus tracking

6. **Schema Property Additions**
   - Item schema: `fragile` property
   - Commitment schema: `rescue_sequence` property
   - Service schema: `discovery_risk` property
