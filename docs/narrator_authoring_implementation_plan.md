# Narrator Authoring Implementation Plan

**Created**: 2025-12-30
**Status**: In Progress
**Goal**: Comprehensive llm_context authoring for all 148 entities in big_game to maximize narrator model quality

---

## Executive Summary

**Current State**:
- 148 total entities (42 NPCs, 45 locations, 61 items)
- Only 21 entities (14%) have llm_context
- 127 entities (86%) missing llm_context entirely

**Target State**:
- 100% llm_context coverage across all entities
- All NPCs with state machines have complete state_fragments
- All locations have appropriate state_variants for dynamic narration
- All items have descriptive traits and state_variants

**Estimated Effort**: ~1,476-1,740 descriptive elements to author

---

## Phase 0: Foundation & Analysis ✅ COMPLETED

**Goal**: Understand current state and establish authoring patterns

### Completed Work

1. ✅ **Pattern Standardization** (Issue #345)
   - Converted 5 narrative-only NPCs to trait-list pattern
   - 180 traits authored for golems and salamanders
   - Established trait-list as standard pattern

2. ✅ **Comprehensive Audit** (documented in authoring_audit_big_game.md)
   - Inventoried all 148 entities
   - Identified 48 missing state_fragments across 15 NPCs
   - Categorized entities by priority and authoring needs
   - Created audit scripts for ongoing verification

3. ✅ **Architecture Verification**
   - Confirmed llm_context support for NPCs, items, locations
   - Verified state_variants work for locations
   - Documented patterns from simple_game

### Issues Created
- Issue #344: Parent tracking issue for narrator authoring project
- Issue #345: Narrative-only NPC conversion (CLOSED - completed)

---

## Phase 1: Fix Critical State Gaps ⚠️ NEXT

**Goal**: Ensure all NPCs with state machines can be properly narrated through state transitions

**Priority**: CRITICAL - state fragment gaps break state-driven narration entirely

### 1.1: Fill Missing State Fragments (15 NPCs, 48 states)

**Effort**: 240-384 traits (48 states × 5-8 traits each)

#### Complete Gaps (11 NPCs with NO state_fragments)
These NPCs have state machines but zero state_fragments:

1. **camp_leader_mira** (4 states: neutral, friendly, allied, disappointed)
2. **damaged_guardian** (4 states: non_functional, partially_awakened, functional, active)
3. **gate_guard** (3 states: suspicious, neutral, friendly)
4. **merchant_delvan** (4 states: trapped, freed, mobile, dead)
5. **npc_sporeling_1** (4 states: hostile, wary, allied, confused)
6. **npc_sporeling_2** (4 states: hostile, wary, allied, confused)
7. **npc_sporeling_3** (4 states: hostile, wary, allied, confused)
8. **sailor_garrett** (4 states: drowning, stabilized, rescued, dead)
9. **the_archivist** (3 states: guardian, helpful, allied)
10. **the_echo** (5 states: dormant, manifesting, communicating, fading, permanent)
11. **waystone_spirit** (3 states: damaged, partial, repaired)

**Template for state_fragments**:
```json
"state_fragments": {
  "state_name": [
    "physical appearance in this state",
    "behavioral characteristic",
    "emotional quality",
    "interaction pattern",
    "environmental effect",
    "sensory detail"
  ]
}
```

#### Partial Gaps (4 NPCs with incomplete state_fragments)
These NPCs have some state_fragments but are missing others:

1. **bear_cub_1** - missing "dead" state
2. **bear_cub_2** - missing "dead" state
3. **dire_bear** - missing "dead" state
4. **spider_matriarch** - missing "wary", "neutral", "allied" states (has only "hostile", "dead")

**Deliverables**:
- [ ] Author all 48 missing state_fragments
- [ ] Verify alignment with state machines using `/tmp/check_npc_states.sh`
- [ ] Test narration with NPCs transitioning through states
- [ ] Update authoring audit document with progress

### 1.2: Expand Sparse Base Traits (8 NPCs)

**Effort**: 16 traits (8 NPCs × 2 traits each)

These NPCs have only 4 base traits and need expansion to 6+:

1. **bear_cub_1**
2. **bear_cub_2**
3. **dire_bear**
4. **frost_wolf_1**
5. **frost_wolf_2**
6. **giant_spider_1**
7. **giant_spider_2**
8. **spider_matriarch** (already has 6 base traits, just needs state_fragments)

**Deliverables**:
- [ ] Add 2 base traits to each sparse NPC
- [ ] Verify all NPCs have 6+ base traits
- [ ] Update audit document

---

## Phase 2: Critical Path Entities (Gameplay Impact)

**Goal**: Author llm_context for entities that directly impact gameplay and player experience

### 2.1: Quest-Critical NPCs (21 NPCs)

**Effort**: ~326-446 traits

These NPCs have no llm_context but are essential to gameplay:

#### With State Machines (10 NPCs)
Need base traits + state_fragments:

1. **camp_leader_mira** (also in Phase 1.1)
2. **damaged_guardian** (also in Phase 1.1)
3. **gate_guard** (also in Phase 1.1)
4. **merchant_delvan** (also in Phase 1.1)
5. **npc_sporeling_1** (also in Phase 1.1)
6. **npc_sporeling_2** (also in Phase 1.1)
7. **npc_sporeling_3** (also in Phase 1.1)
8. **sailor_garrett** (also in Phase 1.1)
9. **the_archivist** (also in Phase 1.1)
10. **waystone_spirit** (also in Phase 1.1)

#### Without State Machines (11 NPCs)
Need base traits only (~6 each):

11. **councilor_asha**
12. **councilor_hurst**
13. **councilor_varn**
14. **herbalist_maren**
15. **old_swimmer_jek**
16. **predatory_fish**
17. **shadow**
18. **the_echo** (has state machine - see above)
19. **the_fence**
20. **weaponsmith_toran**
21. **whisper**

**Deliverables**:
- [ ] Author base traits for all 21 NPCs
- [ ] Author state_fragments for 10 NPCs with state machines (overlaps with Phase 1.1)
- [ ] Test narration with quest-critical NPCs

### 2.2: Quest-Critical Items (15 items)

**Effort**: ~135 trait-equivalents

Essential items for quest progression:

1. **ice_wand** - elemental weapon
2. **fire_wand** - elemental weapon
3. **command_crystal** - golem control
4. **animator_crystal** - golem animation
5. **keepers_journal** - lore/clues
6. **aldric_journal** - character backstory
7. **hunters_journal** - tracking info
8. **research_notes** - explorer's findings
9. **crystal_lens** - telescope repair part
10. **mounting_bracket** - telescope repair part
11. **water_pearl** - repair/assembly item
12. **stone_chisel** - guardian repair
13. **town_seal** - authority/access
14. **spore_heart_fragment** - myconid healing
15. **alpha_fang_fragment** - wolf quest item

**Structure for quest items**:
```json
"llm_context": {
  "traits": [
    "physical appearance trait",
    "material/craftsmanship",
    "magical/special quality",
    "historical significance",
    "functional detail",
    "aesthetic element"
  ],
  "state_variants": {
    "in_location": "description when on ground/pedestal",
    "in_inventory": "description when carried",
    "examined": "close inspection reveals...",
    "in_use": "when actively being used (optional)"
  }
}
```

**Deliverables**:
- [ ] Author traits and state_variants for all 15 quest items
- [ ] Test narration with item pickup, examination, and use

### 2.3: Major Locations (15 locations)

**Effort**: ~165 trait-equivalents

Hub and quest-critical locations:

#### Hub Locations (4)
1. **nexus_chamber** - central hub
2. **town_gate** - civilized remnants entry
3. **market_square** - town center
4. **survivor_camp** - flooded region hub

#### Quest Locations (11)
5. **observatory_platform** - telescope puzzle
6. **keepers_quarters** - keeper's residence
7. **frozen_observatory** - frozen telescope
8. **temple_sanctum** - frost region temple
9. **broken_statue_hall** - damaged guardian location
10. **spore_heart** - myconid quest climax
11. **myconid_sanctuary** - myconid village
12. **deep_archive** - underwater knowledge
13. **undercity** - shadow faction base
14. **undercity_entrance** - secret access
15. **cavern_entrance** - grotto access

**Structure for locations**:
```json
"llm_context": {
  "traits": [
    "architectural feature",
    "lighting/atmosphere",
    "sensory detail (sound)",
    "sensory detail (smell/temperature)",
    "visual focal point",
    "ambient detail",
    "scale/spatial sense",
    "material/texture"
  ],
  "atmosphere": "concise mood/tone descriptor",
  "state_variants": {
    "first_visit": "initial discovery impression",
    "revisit": "familiar return",
    "quest_active": "during related quest (optional)",
    "quest_complete": "after resolution (optional)",
    "condition_specific": "when flag/state is true"
  }
}
```

**Deliverables**:
- [ ] Author traits, atmosphere, and state_variants for 15 major locations
- [ ] Test narration with location entry/exit

---

## Phase 3: Supporting Cast (Completeness)

**Goal**: Achieve 100% llm_context coverage

### 3.1: Remaining Items (46 items)

**Effort**: ~354 trait-equivalents

#### Tools & Equipment (10 items)
- bucket, breathing_mask, waterproof_sack, air_bladder
- spore_lantern, ancient_torch
- tracking_equipment, cleaning_supplies

#### Consumables & Resources (20 items)
- healing_herbs, bandages, frozen_bandages, bear_cub_medicine
- silvermoss, heartmoss, mushrooms (blue, gold, violet, black)
- frost_lily, moonpetal, nightshade, water_bloom
- spider_silk, venom_sac, royal_honey
- venison, frozen_dried_meat, preserved_supplies

#### Gear (3 items)
- rusty_sword
- warm_cloak, cold_weather_gear, cold_resistance_cloak

#### Crystals (5 items)
- frozen_crystal, wild_crystal, sunken_crystal, fungal_crystal, remnant_crystal

#### Interactive Objects (8 items)
- ancient_telescope, frozen_telescope (synced pair)
- lever, stone_pillar_1, stone_pillar_2
- lore_tablets, dead_explorer
- partial_map, ice_shard

**Deliverables**:
- [ ] Author traits and state_variants for all 46 remaining items
- [ ] Verify 100% item coverage

### 3.2: Remaining Locations (30 locations)

**Effort**: ~240 trait-equivalents

#### Wilderness Areas (9)
- forest_edge, ancient_grove, tangled_path, southern_trail
- snow_forest, wolf_den, wolf_clearing
- spider_thicket, spider_matriarch_lair
- predators_den, hunters_camp

#### Ice/Mountain Regions (6)
- frozen_pass, ice_caves, ice_field
- glacier_approach, glacier_surface
- hot_springs

#### Water/Flooded Regions (5)
- flooded_plaza, flooded_chambers
- tidal_passage, sea_caves
- luminous_grotto

#### Town/Settlement (4)
- merchant_quarter, merchant_warehouse
- healers_sanctuary, healers_garden
- council_hall

#### Underground (3)
- crystal_garden
- deep_root_caverns
- bee_queen_clearing

**Deliverables**:
- [ ] Author traits, atmosphere, and state_variants for 30 remaining locations
- [ ] Verify 100% location coverage

---

## Phase 4: Location State Narration Enhancement

**Goal**: Enable dynamic location narration based on quest progress and world state

**Dependencies**: Requires understanding of quest flag system and world state management

### 4.1: Analysis - Quest Flags and Location States

**Research needed**:
- [ ] Identify all quest flags in game
- [ ] Map which flags affect which locations
- [ ] Document flag naming conventions
- [ ] Determine how narrator accesses world state

**Key Questions**:
1. How does the narrator access quest flags / world state?
2. How does it select appropriate state_variant based on flags?
3. Do we need new narrator logic, or does existing system support this?

### 4.2: Design - State Variant Selection Logic

**Goal**: Design how narrator chooses location state_variants based on world state

**Considerations**:
- Priority order when multiple variants could apply
- Fallback to base traits when no variant matches
- Performance implications of state checking

**Deliverables**:
- [ ] Design document for state variant selection
- [ ] API for narrator to query world state
- [ ] Unit tests for state variant selection logic

### 4.3: Implementation - Narrator State Variant Support

**Code Changes Required**:

1. **Location Serializer Enhancement** (`utilities/location_serializer.py`)
   - Pass world state / quest flags to serializer
   - Select appropriate state_variant based on flags
   - Include selected variant in serialized output

2. **Narrator Prompt Enhancement**
   - Include state_variant alongside base traits
   - Ensure narrator understands variant context
   - Test that variants influence description

3. **State Variant Authoring**
   - Add state_variants to high-impact locations identified in Phase 4.4
   - Test narration changes when flags change

**Deliverables**:
- [ ] Updated location serializer with state variant selection
- [ ] Updated narrator prompts
- [ ] Unit tests for variant selection
- [ ] Integration tests with changing world state

### 4.4: Authoring - Location-Specific State Variants

**High-Impact Locations for State Variants**:

#### Repair/Restoration Locations
1. **broken_statue_hall**
   - States: `guardian_broken`, `guardian_repaired`, `guardian_active`

2. **crystal_garden**
   - States: `crystals_shattered`, `crystals_repaired`

3. **observatory_platform** / **frozen_observatory**
   - States: `telescope_broken`, `telescope_repaired`, `telescope_active`

#### Environmental State Locations
4. **flooded_chambers**, **flooded_plaza**, **merchant_warehouse**
   - States: `flooded`, `water_drained` (if drainage quest exists)

5. **deep_root_caverns**
   - States: `toxic`, `breathable_with_mask`, `air_cleared`

6. **hot_springs**
   - States: `first_visit`, `salamanders_present`, `salamanders_befriended`

#### Discovery/Exploration Locations
7. **nexus_chamber**
   - States: `first_arrival`, `familiar`, `all_regions_opened`

8. **luminous_grotto**
   - States: `first_visit`, `mushrooms_harvested`, `explorer_found`

9. **undercity** / **undercity_entrance**
   - States: `first_discovery`, `known_to_fence`, `regular_visitor`

#### Quest Resolution Locations
10. **spore_heart**
    - States: `infected`, `healing`, `healed`

11. **survivor_camp**
    - States: `desperate`, `hopeful`, `thriving`

**Deliverables**:
- [ ] Author state_variants for all high-impact locations
- [ ] Map state_variants to quest flags
- [ ] Test narration changes through quest progression
- [ ] Document state_variant → flag mappings

### 4.5: Testing - Dynamic Location Narration

**Test Scenarios**:

1. **Repair Quest Arc**
   - Visit broken_statue_hall with guardian broken
   - Repair guardian (use stone_chisel)
   - Revisit broken_statue_hall - verify changed narration
   - Activate guardian (use command_crystal)
   - Revisit again - verify active state narration

2. **Environmental Change**
   - Enter deep_root_caverns without breathing_mask
   - Equip breathing_mask
   - Re-enter - verify changed atmosphere narration

3. **Discovery Progression**
   - First visit to nexus_chamber
   - Open 1-2 regions
   - Return - verify "familiar" narration
   - Open all 5 regions
   - Return - verify "complete" narration

4. **Quest Resolution**
   - Visit survivor_camp at start (desperate)
   - Complete some rescue/aid quests
   - Return - verify "hopeful" narration
   - Complete all survivor quests
   - Return - verify "thriving" narration

**Deliverables**:
- [ ] Walkthrough tests for all scenarios
- [ ] Verification of narration changes
- [ ] Bug fixes for any broken variants

---

## Phase 5: Polish & Consistency

**Goal**: Ensure quality and consistency across all authored content

### 5.1: Review Pass - Trait Quality

**Process**:
- [ ] Review all NPC base traits for consistency and vividness
- [ ] Review all state_fragment traits for state-appropriate detail
- [ ] Review all item traits for appropriate detail level
- [ ] Review all location traits for atmospheric impact

**Quality Criteria**:
- Traits are specific and evocative (not generic)
- Traits use sensory details (sight, sound, smell, touch, temperature)
- Traits support narrator variety (not prescriptive sentences)
- Traits align with entity's role and theme

### 5.2: Review Pass - State Variant Appropriateness

**Process**:
- [ ] Verify state_variants actually differ meaningfully
- [ ] Ensure variants don't contradict base traits
- [ ] Check that variants enhance rather than replace base description
- [ ] Confirm variant triggers are achievable in gameplay

### 5.3: Template Generation for Similar Entities

**Automation Opportunities**:

1. **Duplicate NPCs**
   - frost_wolf_1 and frost_wolf_2 can share structure
   - giant_spider_1 and giant_spider_2 can share structure
   - steam_salamander_2 and steam_salamander_3 already complete
   - sporelings 1/2/3 can share base structure with variations

2. **Item Categories**
   - All mushrooms share similar structure
   - All crystals share similar structure
   - All journals share similar structure

**Deliverables**:
- [ ] Create templates for common entity types
- [ ] Script to apply templates with variations
- [ ] Documentation on template usage

### 5.4: Playtest with Full Narration

**Goal**: Experience the game with complete narrator coverage

**Process**:
1. Play through major quest arcs
2. Note narration quality, variety, and appropriateness
3. Identify any missing or weak narration
4. Refine traits and variants based on play experience

**Deliverables**:
- [ ] Playtest notes documenting narration quality
- [ ] Refinements to weak or repetitive narration
- [ ] Final verification of 100% coverage

---

## Success Metrics

### Quantitative Metrics
- ✅ 100% of NPCs (42/42) have llm_context
- ✅ 100% of NPCs with state machines (31/31) have complete state_fragments
- ✅ 100% of items (61/61) have llm_context
- ✅ 100% of locations (45/45) have llm_context
- ✅ High-impact locations (11+) have quest-aware state_variants
- ✅ ~1,476-1,740 descriptive elements authored

### Qualitative Metrics
- Narrator descriptions are vivid and specific (not generic)
- State transitions are clearly narrated through traits
- Location atmosphere changes noticeably with quest progress
- Player feels immersed through rich environmental detail
- Narration variety prevents repetition

---

## Risk Mitigation

### Risk: Authoring Fatigue / Inconsistency
**Mitigation**:
- Pace work across sessions
- Use templates for similar entities
- Review passes to catch inconsistencies
- Focus on high-impact entities first

### Risk: State Variant System Too Complex
**Mitigation**:
- Start with simple flag-based variants
- Test with small set of locations first
- Document clearly which flags trigger which variants
- Fallback to base traits if variant system fails

### Risk: Narrator Doesn't Use Traits Effectively
**Mitigation**:
- Test narration frequently during authoring
- Adjust trait style based on narrator output
- May need narrator prompt tuning
- Document trait-writing best practices

---

## Open Questions

1. **Quest Flag System**: How are quest flags currently implemented? Need reference to design state_variant triggers.

2. **World State Access**: How does narrator access world state to select state_variants?

3. **State Variant Priority**: If multiple variants could apply, which takes precedence?

4. **Performance**: Does checking world state for every location impact performance?

5. **Backward Compatibility**: Do we need to support old save files during authoring? (Likely not per CLAUDE.md)

---

## Progress Tracking

### Phase 0: Foundation ✅ 100%
- [x] Pattern standardization
- [x] Comprehensive audit
- [x] Architecture verification

### Phase 1: Critical State Gaps ⚠️ 0%
- [ ] 1.1: Fill missing state_fragments (0/48 states)
- [ ] 1.2: Expand sparse base traits (0/8 NPCs)

### Phase 2: Critical Path Entities ⚠️ 0%
- [ ] 2.1: Quest-critical NPCs (0/21)
- [ ] 2.2: Quest-critical items (0/15)
- [ ] 2.3: Major locations (0/15)

### Phase 3: Supporting Cast ⚠️ 0%
- [ ] 3.1: Remaining items (0/46)
- [ ] 3.2: Remaining locations (0/30)

### Phase 4: Location State Narration ⚠️ 0%
- [ ] 4.1: Analysis
- [ ] 4.2: Design
- [ ] 4.3: Implementation
- [ ] 4.4: Authoring
- [ ] 4.5: Testing

### Phase 5: Polish ⚠️ 0%
- [ ] 5.1: Trait quality review
- [ ] 5.2: State variant review
- [ ] 5.3: Template generation
- [ ] 5.4: Playtest

**Overall Completion**: ~12% (Phase 0 only)
