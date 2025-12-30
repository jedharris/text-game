# Big Game Authoring Audit - llm_context Status

Date: 2025-12-30

## Executive Summary

**Target**: All entities (NPCs, items, locations) should have 5-8 descriptive traits for narrator model

**Current State**:
- **NPCs (42 total)**: 13 well-authored (31%), 10 sparse (24%), ~~5 narrative-only~~ **0 narrative-only** (converted), 19 missing (45%)
- **Items (61 total)**: 0 have llm_context (0%)
- **Locations (45 total)**: 0 have llm_context (0%)

**Work Required**: Significant authoring effort needed across all entity types

**Recent Progress**:
- ✅ Converted all 5 narrative-only NPCs to trait-list pattern (golems, salamanders)

---

## NPCs - Detailed Breakdown

### ✅ Well-Authored (13) - 6+ base traits + state fragments
Ready for narrator, no changes needed:

1. **alpha_wolf** - 6 base traits, 5 states
2. **bee_queen** - 6 base traits, 5 states
3. **curiosity_dealer_vex** - 6 base traits, 3 states
4. **dire_bear** - 6 base traits, 5 states
5. **healer_elara** - 6 base traits, 3 states
6. **hunter_sira** - 6 base traits, 4 states
7. **npc_myconid_elder** - 6 base traits, 3 states
8. **spider_matriarch** - 6 base traits, 2 states
9. **salamander** - 6 base traits, 6 states (converted from narrative-only)
10. **steam_salamander_2** - 6 base traits, 6 states (converted from narrative-only)
11. **steam_salamander_3** - 6 base traits, 6 states (converted from narrative-only)
12. **stone_golem_1** - 6 base traits, 5 states (converted from narrative-only)
13. **stone_golem_2** - 6 base traits, 5 states (converted from narrative-only)

### ⚠️ Sparse (10) - 4 base traits, needs expansion
Has correct structure but needs more detail:

1. **bear_cub_1** - 4 base traits, 3 states → needs 2-4 more base traits
2. **bear_cub_2** - 4 base traits, 3 states → needs 2-4 more base traits
3. **frost_wolf_1** - 4 base traits, 5 states → needs 2-4 more base traits
4. **frost_wolf_2** - 4 base traits, 5 states → needs 2-4 more base traits
5. **giant_spider_1** - 4 base traits, 2 states → needs 2-4 more base traits
6. **giant_spider_2** - 4 base traits, 2 states → needs 2-4 more base traits
7. **npc_aldric** - 4 base traits, 4 states → needs 2-4 more base traits
8. **npc_spore_mother** - 4 base traits, 5 states → needs 2-4 more base traits, also has pack_fragments

### ~~📝 Narrative-Only (5)~~ - ✅ COMPLETED
All narrative-only NPCs have been converted to trait-list pattern:

1. ~~**salamander**~~ → ✅ Converted (6 base traits, 6 states)
2. ~~**steam_salamander_2**~~ → ✅ Converted (6 base traits, 6 states)
3. ~~**steam_salamander_3**~~ → ✅ Converted (6 base traits, 6 states)
4. ~~**stone_golem_1**~~ → ✅ Converted (6 base traits, 5 states)
5. ~~**stone_golem_2**~~ → ✅ Converted (6 base traits, 5 states)

### ❌ Missing llm_context (19) - needs creation from scratch
No llm_context at all:

1. **camp_leader_mira**
2. **councilor_asha**
3. **councilor_hurst**
4. **councilor_varn**
5. **damaged_guardian**
6. **gate_guard**
7. **herbalist_maren**
8. **merchant_delvan**
9. **npc_sporeling_1**
10. **npc_sporeling_2**
11. **npc_sporeling_3**
12. **old_swimmer_jek**
13. **predatory_fish**
14. **sailor_garrett**
15. **shadow**
16. **the_archivist**
17. **the_echo**
18. **the_fence**
19. **waystone_spirit**
20. **weaponsmith_toran**
21. **whisper**

---

## Items - Status

**Total**: 61 items
**With llm_context**: 0 (0%)

All items need llm_context added. Key items include:
- Wands (ice_wand, fire_wand)
- Quest items (command_crystal, keepers_journal, aldric_journal, etc.)
- Tools and equipment (bucket, silvermoss, etc.)
- Interactive objects (mushrooms, containers, etc.)

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

## Authoring Effort Estimate

### NPCs
- **Expand sparse** (10 NPCs): ~2-3 traits each = 20-30 new traits
- ~~**Convert narrative-only** (5 NPCs)~~ → ✅ COMPLETED (180 traits added)
- **Create from scratch** (19 NPCs): ~6 base + 18-30 state traits each = ~456-684 traits total

**Total NPC traits needed**: ~476-714 traits (was ~656-894, reduced by 180 completed)

### Items
- **61 items** × 5-6 traits each = ~305-366 traits
- Plus state_variants for each

### Locations
- **45 locations** × 6-8 traits each = ~270-360 traits
- Plus state_variants for each

**Grand Total**: Approximately **1,050-1,440 descriptive traits** needed across all entities (was 1,230-1,620, reduced by 180 completed)

---

## Recommended Authoring Strategy

### Phase 1: Upgrade Existing NPCs (Lower Effort)
1. ~~Convert narrative-only NPCs (5) - restructure to trait lists~~ ✅ COMPLETED
2. Expand sparse NPCs (10) - add 2-4 traits each ← **NEXT**

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
