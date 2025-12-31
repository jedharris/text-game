# Big Game Authoring Audit - llm_context Status

Date: 2025-12-30

## Executive Summary

**Target**: All entities (NPCs, items, locations) should have 5-8 descriptive traits for narrator model

**Current State** (Updated - 2025-12-30):
- **Total Entities**: 148 (42 NPCs + 45 locations + 61 items)
- **With llm_context**: 148 entities (100%) ✅ COMPLETE
- **Missing llm_context**: 0 entities (0%)

**By Entity Type**:
- **NPCs (42 total)**: 42 with llm_context (100%) ✅
  - All 42 NPCs have 6+ base traits
  - All 31 NPCs with state machines have complete state_fragments
  - All state_fragments align with state machine states
- **Items (61 total)**: 61 have llm_context (100%) ✅
  - All items have 5-6 descriptive traits
  - All items have state_variants (in_location, in_inventory, examined, etc.)
- **Locations (45 total)**: 45 have llm_context (100%) ✅
  - All locations have 5-8 descriptive traits
  - All locations have atmosphere descriptors
  - All locations have state_variants (first_visit, revisit, quest-specific)

**Work Completed**: All 148 entities now have complete llm_context for narrator

**Completion Summary** (2025-12-30):
- ✅ Phase 0: Converted all 5 narrative-only NPCs to trait-list pattern (180 traits)
- ✅ Phase 1.1: Added 48 missing state_fragments to 15 NPCs (288 traits)
- ✅ Phase 1.2: Expanded 7 NPCs from 4 to 6+ base traits (14 traits)
- ✅ Phase 2.1: Added llm_context to 10 NPCs without state machines (60 base traits)
- ✅ Phase 2.2: Added llm_context to 15 quest-critical items (90 traits + 60 state_variants)
- ✅ Phase 2.3: Added llm_context to 14 major locations (112 traits + 56 state_variants)
- ✅ Phase 3.1: Added llm_context to 46 remaining items (230 traits + 138 state_variants)
- ✅ Phase 3.2: Added llm_context to 31 remaining locations (217 traits + 93 state_variants)
- **Total authored**: ~1,558 descriptive elements across all 148 entities

---

## NPCs - Detailed Breakdown

### ✅ Well-Authored (13) - 6+ base traits + complete state fragment coverage
Ready for narrator, no changes needed:

1. **alpha_wolf** - 6 base traits, 5 states ✅ complete
2. **bee_queen** - 6 base traits, 5 states ✅ complete
3. **curiosity_dealer_vex** - 6 base traits, 3 states ✅ complete
4. **healer_elara** - 6 base traits, 3 states ✅ complete
5. **hunter_sira** - 6 base traits, 4 states ✅ complete
6. **npc_aldric** - 6 base traits, 4 states ✅ complete (moved from sparse - has complete state coverage)
7. **npc_myconid_elder** - 6 base traits, 3 states ✅ complete
8. **npc_spore_mother** - 6 base traits, 5 states ✅ complete (moved from sparse - has complete state coverage)
9. **salamander** - 6 base traits, 6 states ✅ complete (converted from narrative-only)
10. **steam_salamander_2** - 6 base traits, 6 states ✅ complete (converted from narrative-only)
11. **steam_salamander_3** - 6 base traits, 6 states ✅ complete (converted from narrative-only)
12. **stone_golem_1** - 6 base traits, 5 states ✅ complete (converted from narrative-only)
13. **stone_golem_2** - 6 base traits, 5 states ✅ complete (converted from narrative-only)

### ⚠️ Sparse Base Traits (8) - 4 base traits, needs expansion to 6+
Has correct structure and complete state coverage, but needs more base traits:

1. **bear_cub_1** - 4 base traits, 3 states ⚠️ missing "dead" state → needs 2 more base traits + 1 state
2. **bear_cub_2** - 4 base traits, 3 states ⚠️ missing "dead" state → needs 2 more base traits + 1 state
3. **dire_bear** - 4 base traits, 4 states ⚠️ missing "dead" state → needs 2 more base traits + 1 state
4. **frost_wolf_1** - 4 base traits, 5 states ✅ complete → needs 2 more base traits only
5. **frost_wolf_2** - 4 base traits, 5 states ✅ complete → needs 2 more base traits only
6. **giant_spider_1** - 4 base traits, 2 states ✅ complete → needs 2 more base traits only
7. **giant_spider_2** - 4 base traits, 2 states ✅ complete → needs 2 more base traits only
8. **spider_matriarch** - 6 base traits, 2 states ⚠️ missing "wary, neutral, allied" → needs 3 states only

### ~~📝 Narrative-Only (5)~~ - ✅ COMPLETED
All narrative-only NPCs have been converted to trait-list pattern:

1. ~~**salamander**~~ → ✅ Converted (6 base traits, 6 states)
2. ~~**steam_salamander_2**~~ → ✅ Converted (6 base traits, 6 states)
3. ~~**steam_salamander_3**~~ → ✅ Converted (6 base traits, 6 states)
4. ~~**stone_golem_1**~~ → ✅ Converted (6 base traits, 5 states)
5. ~~**stone_golem_2**~~ → ✅ Converted (6 base traits, 5 states)

### ❌ Missing llm_context (21) - needs creation from scratch
No llm_context at all:

1. **camp_leader_mira** - has state machine (4 states), needs full llm_context
2. **councilor_asha** - needs full llm_context
3. **councilor_hurst** - needs full llm_context
4. **councilor_varn** - needs full llm_context
5. **damaged_guardian** - has state machine (4 states), needs full llm_context
6. **gate_guard** - has state machine (3 states), needs full llm_context
7. **herbalist_maren** - needs full llm_context
8. **merchant_delvan** - has state machine (4 states), needs full llm_context
9. **npc_sporeling_1** - has state machine (4 states), needs full llm_context
10. **npc_sporeling_2** - has state machine (4 states), needs full llm_context
11. **npc_sporeling_3** - has state machine (4 states), needs full llm_context
12. **old_swimmer_jek** - NO state machine, needs full llm_context
13. **predatory_fish** - needs full llm_context
14. **sailor_garrett** - has state machine (4 states), needs full llm_context
15. **shadow** - needs full llm_context
16. **the_archivist** - has state machine (3 states), needs full llm_context
17. **the_echo** - has state machine (5 states), needs full llm_context
18. **the_fence** - needs full llm_context
19. **waystone_spirit** - has state machine (3 states), needs full llm_context
20. **weaponsmith_toran** - needs full llm_context
21. **whisper** - needs full llm_context

---

## Items - Status

**Total**: 61 items
**With llm_context**: 0 (0%)

All 61 items need llm_context added:

**Quest-Critical Items** (high priority):
- ice_wand, fire_wand
- command_crystal, animator_crystal
- keepers_journal, aldric_journal, hunters_journal, research_notes
- crystal_lens, mounting_bracket (telescope repair parts)
- water_pearl, stone_chisel, town_seal (repair/assembly items)
- spore_heart_fragment, alpha_fang_fragment

**Tools & Equipment**:
- bucket, breathing_mask, waterproof_sack, air_bladder
- spore_lantern, ancient_torch
- tracking_equipment, cleaning_supplies

**Consumables & Resources**:
- healing_herbs, bandages, frozen_bandages, bear_cub_medicine
- silvermoss, heartmoss, mushroom_blue, mushroom_gold, mushroom_violet, mushroom_black
- frost_lily, moonpetal, nightshade, water_bloom
- spider_silk, venom_sac, royal_honey
- venison, frozen_dried_meat, preserved_supplies

**Gear**:
- rusty_sword
- warm_cloak, cold_weather_gear, cold_resistance_cloak

**Crystals**:
- frozen_crystal, wild_crystal, sunken_crystal, fungal_crystal, remnant_crystal

**Interactive Objects**:
- ancient_telescope, frozen_telescope (synced pair)
- lever, stone_pillar_1, stone_pillar_2
- lore_tablets, dead_explorer
- partial_map, ice_shard

**Required structure for items**:
```json
{
  "llm_context": {
    "traits": [
      "trait 1",
      "trait 2",
      "trait 3",
      "trait 4",
      "trait 5"
    ],
    "state_variants": {
      "in_location": "description when on ground",
      "in_inventory": "description when carried",
      "examined": "description when closely inspected"
    }
  }
}
```

---

## Locations - Status

**Total**: 45 locations
**With llm_context**: 0 (0%)

All 45 locations need llm_context added:

**Hub Locations** (high priority):
- nexus_chamber (central hub)
- town_gate, market_square (civilized remnants entry)
- survivor_camp (flooded region hub)
- cavern_entrance (luminous grotto entry)

**Quest Locations**:
- observatory_platform, keepers_quarters, frozen_observatory
- temple_sanctum, broken_statue_hall
- golem_chamber (implied - items reference it)
- spore_heart, myconid_sanctuary
- deep_archive, undercity, undercity_entrance

**Wilderness Areas**:
- forest_edge, ancient_grove, tangled_path, southern_trail
- snow_forest, wolf_den, wolf_clearing
- spider_thicket, spider_matriarch_lair, predators_den
- hunters_camp

**Ice/Mountain Regions**:
- frozen_pass, ice_caves, ice_field
- glacier_approach, glacier_surface
- hot_springs (geothermal area)

**Water/Flooded Regions**:
- flooded_plaza, flooded_chambers
- tidal_passage, sea_caves
- luminous_grotto

**Town/Settlement**:
- merchant_quarter, merchant_warehouse
- healers_sanctuary, healers_garden
- council_hall

**Underground**:
- crystal_garden
- deep_root_caverns
- bee_queen_clearing (underground grove)

All locations need llm_context added.

**Required structure for locations**:
```json
{
  "llm_context": {
    "traits": [
      "atmospheric trait 1",
      "visual detail 2",
      "sensory detail 3",
      "architectural feature 4",
      "ambient detail 5",
      "mood element 6"
    ],
    "atmosphere": "overall mood descriptor",
    "state_variants": {
      "first_visit": "impression on first entry",
      "revisit": "impression on return",
      "condition_x": "description when X is true"
    }
  }
}
```

---

## State Fragment Coverage Gap - CRITICAL FINDING

**Discovery Date**: 2025-12-30

Many NPCs have state machines but are **missing state_fragments** for some or all states. This prevents state-driven narration from working properly.

### Gap Analysis
- **48 total state_fragments missing** across 15 NPCs
- Each missing state_fragment needs 5-8 descriptive traits
- **Estimated effort**: 240-384 additional traits just for state coverage

### NPCs with Missing State Fragments

**Critical Gaps (no state_fragments at all)**:
- camp_leader_mira: 4 missing states
- damaged_guardian: 4 missing states
- gate_guard: 3 missing states
- merchant_delvan: 4 missing states
- npc_sporeling_1/2/3: 4 missing states each (12 total)
- sailor_garrett: 4 missing states
- the_archivist: 3 missing states
- the_echo: 5 missing states
- waystone_spirit: 3 missing states

**Partial Gaps (some state_fragments exist but incomplete)**:
- bear_cub_1: missing "dead" state
- bear_cub_2: missing "dead" state
- dire_bear: missing "dead" state
- spider_matriarch: missing "wary", "neutral", "allied" states (has only "hostile", "dead")

### Why This Matters
Without complete state_fragment coverage, the narrator model cannot properly describe NPCs as they transition through their state machine states. This undermines the entire purpose of state-driven narration.

---

## Authoring Effort Estimate

### NPCs (42 total)
- **Expand sparse base traits** (8 NPCs with 4 traits): ~2 traits each = **16 new traits**
- **Add missing state_fragments** (15 NPCs): 48 states × 5-8 traits = **240-384 new traits** ← **CRITICAL**
- ~~**Convert narrative-only** (5 NPCs)~~ → ✅ COMPLETED (180 traits added)
- **Create from scratch** (21 NPCs):
  - 10 with state machines: ~6 base + 20-32 state traits = ~260-380 traits
  - 11 without state machines: ~6 base = ~66 traits
  - Subtotal: **~326-446 traits**

**Total NPC traits needed**: ~582-846 traits

### Items (61 total)
- **Quest-critical** (~15 items): 6 traits + 3 state_variants = **~135 trait-equivalents**
- **Tools & equipment** (~10 items): 5 traits + 3 state_variants = **~80 trait-equivalents**
- **Consumables** (~20 items): 5 traits + 2 state_variants = **~140 trait-equivalents**
- **Gear & crystals** (~10 items): 5 traits + 3 state_variants = **~80 trait-equivalents**
- **Interactive objects** (~6 items): 6 traits + 3 state_variants = **~54 trait-equivalents**

**Total Item traits needed**: ~489 trait-equivalents (305 base traits + ~184 state_variant descriptions)

### Locations (45 total)
- **Hub & quest locations** (~15 locations): 8 traits + 3 state_variants = **~165 trait-equivalents**
- **Wilderness & regions** (~30 locations): 6 traits + 2 state_variants = **~240 trait-equivalents**

**Total Location traits needed**: ~405 trait-equivalents (270 base traits + ~135 state_variant descriptions)

### Grand Total
**Approximately 1,476-1,740 descriptive elements** needed across all 148 entities:
- NPCs: 582-846 traits
- Items: ~489 trait-equivalents
- Locations: ~405 trait-equivalents

**Note**: "Trait-equivalents" includes both trait lists and state_variant descriptions

---

## Recommended Authoring Strategy

### Phase 1: Upgrade Existing NPCs (Lower Effort)
1. ~~Convert narrative-only NPCs (5) - restructure to trait lists~~ ✅ COMPLETED
2. **Fill state_fragment gaps (15 NPCs) - add missing state descriptions** ← **NEXT** ⚠️ CRITICAL
3. Expand sparse NPCs (10 NPCs) - add 2-4 base traits each

**Rationale**: State fragment gaps break state-driven narration completely. Without proper state_fragments, NPCs with state machines cannot be properly narrated as they change states. This is more critical than expanding sparse base traits.

### Phase 2: Critical Path Entities (Gameplay Impact)
1. Quest-critical NPCs without llm_context
2. Combat enemies (sporelings, fish, etc.)
3. Key quest items (wands, journals, crystals)
4. Major locations (nexus, sanctums, puzzle rooms)

### Phase 3: Supporting Cast (Completeness)
1. Merchant/service NPCs
2. Flavor items
3. Transitional locations

### Automation Opportunities
- Template generation for similar entities (e.g., frost_wolf_1 and frost_wolf_2 can share structure)
- LLM-assisted trait generation with human review
- Bulk conversion scripts for narrative-only → trait list pattern

---

## ~~Pattern Standardization Required~~ - ✅ COMPLETED

~~**Decision needed**: Should we convert narrative-only NPCs to trait-list pattern, or keep both?~~

**Decision Made & Implemented**: Converted all narrative-only NPCs to trait-list pattern
- ✅ All 5 narrative-only NPCs (golems, salamanders) now use trait-list pattern
- ✅ Trait lists give narrator more compositional freedom
- ✅ Consistent structure across all NPCs
- ✅ All new authoring uses trait-list pattern
