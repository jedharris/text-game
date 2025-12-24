# Beast Wilds Implementation Inventory

**Created**: 2025-12-22
**Purpose**: Comprehensive audit of Beast Wilds implementation vs. design
**Design Source**: `docs/big_game_work/detailed_designs/beast_wilds_detailed_design.md`

---

## Summary

| Category | Designed | Implemented | Missing |
|----------|----------|-------------|---------|
| Locations | 6 | 8 | 1 (predators_den) |
| NPCs/Actors | 12 | 6 | 5 (dire bear family, giant spiders) |
| Items | 8+ | 4 | 4+ (venison, alpha_fang, tracking_equipment, hunters_journal) |
| Behaviors | 5 files | 5 files | Talk handler for bee queen |

---

## Locations

### Implemented Locations

| Design ID | game_state.json ID | Name | Exits | Properties |
|-----------|-------------------|------|-------|------------|
| loc_forest_edge | forest_edge | Forest Edge | north: nexus_chamber, south: tangled_path, east: southern_trail | region: beast_wilds |
| loc_wolf_clearing | wolf_den | Wolf Den | (in frozen_reaches!) | wolf_territory: true |
| loc_beehive_grove | ancient_grove + bee_queen_clearing | Ancient Grove / Bee Queen's Clearing | ancient_grove->bee_queen_clearing | region: beast_wilds |
| loc_spider_nest_gallery | spider_thicket + spider_matriarch_lair | Spider Thicket / Spider Matriarch's Lair | spider_thicket->spider_matriarch_lair | web_hazard, difficult_terrain |
| loc_southern_trail | southern_trail | Southern Trail | west: forest_edge, south: town_gate, east: hunters_camp | region: beast_wilds |
| - | hunters_camp | Hunter's Camp | west: southern_trail | region: beast_wilds |
| - | tangled_path | Tangled Path | north: forest_edge, south: ancient_grove, west: spider_thicket | difficult_terrain |

### Missing Locations

| Design ID | Name | Purpose | Required Content |
|-----------|------|---------|------------------|
| loc_predators_den | Predator's Den | Dire bear and sick cubs, healing commitment | dire_bear, bear_cub_1, bear_cub_2 |

### Location Discrepancies

1. **Wolf Den Location**: Design specifies `loc_wolf_clearing` in Beast Wilds, but `wolf_den` is in Frozen Reaches region
   - **Impact**: Wolf pack encounter is geographically displaced
   - **Decision needed**: Move wolves to Beast Wilds or accept as is?

2. **Split Locations**: Design has single locations that are implemented as pairs:
   - `loc_beehive_grove` -> `ancient_grove` + `bee_queen_clearing`
   - `loc_spider_nest_gallery` -> `spider_thicket` + `spider_matriarch_lair`
   - **Impact**: Navigation differs from design but functionally equivalent

---

## Actors (NPCs/Creatures)

### Implemented Actors

| Design ID | game_state.json ID | Location | State Machine | Trust State | Key Properties |
|-----------|-------------------|----------|---------------|-------------|----------------|
| npc_alpha_wolf | alpha_wolf | wolf_den | hostile->wary->neutral->friendly->allied | current: -2, floor: -5, ceiling: 5 | pack_behavior, gift_reactions handler |
| npc_grey_wolf_1/2 | frost_wolf_1/2 | wolf_den | same as alpha (mirrored) | N/A | pack_role: follower |
| npc_bee_queen | bee_queen | bee_queen_clearing | defensive->neutral->trading->allied->hostile | current: 0, floor: -3, ceiling: 5 | trades_for, gift_reactions handler |
| npc_spider_queen | spider_matriarch | spider_matriarch_lair | hostile->wary->neutral->allied->dead | N/A | pack_role: alpha, death_reactions |
| npc_hunter_sira | hunter_sira | hunters_camp | injured->stabilized->mobile->dead | N/A | conditions, dialog_topics, item_use_reactions |

### Missing Actors

| Design ID | Name | Purpose | Design Reference |
|-----------|------|---------|------------------|
| npc_dire_bear | Dire Bear | Hostile guardian, ally if cubs healed | Section 1.2 |
| npc_bear_cub_1 | Bear Cub | Sick cub requiring healing | Section 1.2 |
| npc_bear_cub_2 | Bear Cub | Sick cub requiring healing | Section 1.2 |
| npc_giant_spider_1 | Giant Spider | Combat follower in spider pack | Section 1.2 |
| npc_giant_spider_2 | Giant Spider | Combat follower in spider pack | Section 1.2 |

### Actor Discrepancies

1. **Wolf names**: Design says "Grey Wolf" but implementation has "Frost Wolf"
   - **Impact**: Minor naming inconsistency

2. **Bee Swarm**: Design mentions `npc_bee_swarm` as combat entity
   - **Status**: Not implemented, may not be needed for Phase 3

---

## Items

### Implemented Items

| Design ID | game_state.json ID | Location | Properties |
|-----------|-------------------|----------|------------|
| item_spider_silk | spider_silk | spider_thicket | portable, trade_good |
| item_venom_sacs | venom_sac | spider_matriarch_lair | portable, dangerous, trade_good |
| item_healing_herbs | healing_herbs | healers_garden | portable, curative |
| - | bear_cub_medicine | null (crafted) | curative, crafted |
| - | moonpetal | healers_garden | rare_flower (for bee queen trade) |
| - | water_bloom | deep_archive | rare_flower (for bee queen trade) |

### Missing Items

| Design ID | Name | Purpose | Location per Design |
|-----------|------|---------|---------------------|
| item_venison | Venison | Wolf feeding | Forest Edge |
| item_tracking_equipment | Tracking Equipment | Tool (requires skill) | Forest Edge |
| item_hunters_journal | Hunter's Journal | Hint source | Forest Edge |
| item_alpha_fang | Alpha Fang | Waystone component | Alpha Wolf gift at trust 5+ |
| item_royal_honey | Royal Honey | Full heal + condition cure | Bee Queen trade |

### Item Notes

1. **alpha_fang_fragment**: Referenced in waystone_spirit.item_use_reactions but doesn't exist
   - **Impact**: Waystone repair path is broken for Beast Wilds

2. **Flowers**: moonpetal and frost_lily exist, but frost_lily is in Frozen Reaches (ice_caves)

---

## Behaviors

### Implemented Behavior Files

| File | Functions | Status |
|------|-----------|--------|
| wolf_pack.py | on_wolf_state_change, on_wolf_feed | Working |
| bee_queen.py | on_flower_offer, on_honey_theft | Working, missing talk handler |
| bear_cubs.py | on_bear_commitment, on_cubs_healed, on_cubs_died | References non-existent actors |
| sira_rescue.py | on_sira_encounter, on_sira_death, on_sira_healed | Working |
| spider_nest.py | on_spider_respawn_check, on_web_movement, on_spider_queen_death | Working |

### Missing Behavior Components

1. **Bee Queen Talk Handler**: Design Section 1.5 specifies antenna/wing communication
   - Similar pattern to spore_mother.py::on_spore_mother_talk
   - Should return non-verbal description based on state

2. **Wolf Talk Handler**: Wolves don't speak, but "talk to wolf" should return body language description
   - Design Section 1.5 has wolf communication vocabulary

---

## Handler Configurations in game_state.json

### Alpha Wolf

```json
"gift_reactions": {
  "food_offering": {
    "accepted_items": ["venison", "meat", "rabbit"],
    "handler": "examples.big_game.behaviors.regions.beast_wilds.wolf_pack:on_wolf_feed"
  }
}
```
**Issue**: venison item doesn't exist

### Hunter Sira

```json
"dialog_topics": {
  "injury": {...},
  "tracking": {...},
  "beasts": {...},
  "elara": {...}
}
"item_use_reactions": {
  "healing": {
    "accepted_items": ["bandages", "healing_herbs"],
    "handler": "examples.big_game.behaviors.regions.beast_wilds.sira_rescue:on_sira_healed"
  }
}
```
**Status**: Fully configured

### Bee Queen

```json
"gift_reactions": {
  "flower_offering": {
    "accepted_items": ["moonpetal", "frost_lily", "water_bloom"],
    "handler": "examples.big_game.behaviors.regions.beast_wilds.bee_queen:on_flower_offer"
  }
}
"take_reactions": {
  "honey_theft": {
    "handler": "examples.big_game.behaviors.regions.beast_wilds.bee_queen:on_honey_theft"
  }
}
```
**Issue**: No talk_handler configured, no dialog_topics

### Waystone Spirit (for reference)

```json
"item_use_reactions": {
  "fragment_placement": {
    "accepted_items": ["spore_heart_fragment", "alpha_fang_fragment", "ice_shard_fragment", "water_bloom_fragment", "echo_essence_fragment"],
    "handler": "examples.big_game.behaviors.regions.meridian_nexus.waystone:on_fragment_placement"
  }
}
```
**Issue**: alpha_fang_fragment doesn't exist in items array

---

## Critical Gaps for Phase 3

### Must Fix (Blocking)

1. **Missing predators_den location** - Bear healing commitment cannot work
2. **Missing dire_bear and bear_cub actors** - Bear mechanics non-functional
3. **Missing alpha_fang_fragment item** - Waystone repair blocked for this path
4. **Missing venison item** - Wolf feeding cannot work as designed

### Should Fix

1. **Bee Queen talk handler** - Player cannot communicate with queen
2. **Wolf location in wrong region** - Wolves in Frozen Reaches, not Beast Wilds
3. **Missing hint items** - tracking_equipment, hunters_journal

### Nice to Have

1. **Giant spider actors** - Only spider_matriarch exists
2. **Royal honey item** - Trade reward doesn't exist
3. **Wolf talk handler** - Non-verbal communication for body language

---

## Comparison with Design Walkthrough

Design walkthrough expectations vs. current capability:

| Action | Design Expectation | Current Status |
|--------|-------------------|----------------|
| Navigate to Hunter's Camp | Works | Works (forest_edge->southern_trail->hunters_camp) |
| Talk to Sira | Dialog with injury/tracking/beasts/elara topics | Works |
| Give bandages/healing_herbs to Sira | Heals conditions | Works |
| Navigate to Wolf Den | Find hostile pack | Broken - wolves in wrong region |
| Give venison to alpha (3x) | Trust increases to 3+ | Broken - no venison item |
| Ask alpha to follow | Companion recruitment | Untested |
| Navigate to Bee Queen's Clearing | Works | Works |
| Talk to queen | Antenna/wing expectation | Broken - no talk handler |
| Give wildflower to queen | Trade for royal honey | Partial - gift handler exists |
| Navigate to Predator's Den | Find dire bear and cubs | Broken - location doesn't exist |
| Heal cubs with healing_herbs | Bear becomes friendly | Broken - actors don't exist |
| Receive alpha_fang_fragment | Waystone component | Broken - item doesn't exist |

---

## Recommended Implementation Order

1. **Add missing items**: venison, alpha_fang_fragment, (royal_honey optional)
2. **Add missing location**: predators_den
3. **Add missing actors**: dire_bear, bear_cub_1, bear_cub_2
4. **Add bee queen talk handler**: Follow spore_mother pattern
5. **Verify wolf location**: Decide whether to move or accept
6. **Create walkthrough test**: walkthroughs/test_beast_wilds.txt
