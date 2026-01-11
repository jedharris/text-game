# NPC Implementation Inventory

**Purpose:** Systematic review of ALL NPCs comparing sketch designs against actual game_state.json implementations to identify gaps, misplacements, and incomplete mechanics.

**Context:** Issue #424 - Created after discovering merchant_delvan placed in correct location but missing dialog and commitment reactions specified in sketch design.

**Generated:** 2026-01-08

---

## Summary Statistics

| Category | Count | Description |
|----------|-------|-------------|
| **Critical** | 0 | Wrong location, missing core quest mechanics |
| **Significant** | 1 | Missing dialog/major reactions (Delvan) |
| **Minor** | 0 | Has basics but missing enrichment |
| **Placeholder** | 14 | No behaviors or reactions implemented |
| **Complete** | 21 | Appears fully implemented |
| **Not Implemented** | 9 | Defined in sketches but not in game |
| **Total Analyzed** | 36 | NPCs in both sketch and game |

---

## Significant Gaps (Require Implementation)

### merchant_delvan
**Region:** sunken_district
**Location:** merchant_warehouse (CORRECT)
**Sketch:** sunken_district_sketch.json

**Current Implementation:**
- ✓ State machine: `trapped -> freed -> mobile -> dead`
- ✓ encounter_reactions (dual_rescue handler)
- ✓ death_reactions (dual_rescue handler)
- ✓ condition_reactions (bleeding_stopped trigger)
- ✓ Properties: conditions (bleeding, broken_leg), commitment_target: true

**Missing from Sketch:**
- ❌ **dialog_reactions** - Sketch defines 2 dialog topics:
  - `trapped`: keywords=[help, trapped, cargo]
    *"My leg... the cargo shifted when the barge tipped. I can't feel my foot. Please, there's a lever in the hold, you could..."*
  - `reward`: keywords=[reward, pay, thanks]
    *"Save me and I'll make it worth your while. My contacts, my goods, my connections - they'll all serve you."*

- ❌ **commitment_reactions** - Needed for quest tracking/rewards:
  - Sketch specifies 3-step rescue: stop bleeding, free from cargo, splint/carry
  - Sketch specifies rewards on rescue success:
    - 50 gold + rare items from cargo
    - 25% permanent discount on merchant services
    - Connection to black market contacts in Civilized Remnants
  - Currently has `commitment_target: true` but no commitment_reactions config

**Impact:** Player can interact with Delvan's encounter/death/condition mechanics but cannot talk to him or receive quest rewards. Rescue has no mechanical payoff.

**Priority:** HIGH - Core NPC with designed quest mechanics 70% implemented

---

## Placeholder NPCs (Zero Implementation)

These NPCs exist in game_state.json but have **no behaviors and no reactions**.

**UPDATE:** Full documentation found in `docs/big_game_work/detailed_designs/`. All NPCs below have complete specifications.

### Civilized Remnants Placeholders

1. **councilor_asha** (council_hall)
   - **Design:** civilized_remnants_detailed_design.md
   - Role: Idealist politician (ethics over efficiency)
   - Quest preferences: Ethical choices, protecting vulnerable, mercy
   - Special: Initiates un-branding ceremony for redeemed players

2. **councilor_hurst** (council_hall)
   - **Design:** civilized_remnants_detailed_design.md
   - Role: Pragmatist politician (results over methods)
   - Backstory: Family killed by beasts - explains harshness
   - Quest preferences: Efficient solutions, harsh but effective choices, security

3. **councilor_varn** (council_hall)
   - **Design:** civilized_remnants_detailed_design.md
   - Role: Commerce politician (prosperity through commerce)
   - Secret: Undercity connections, profits from condemned trades
   - Quest preferences: Choices increasing trade, wealth, connections

4. **shadow** (undercity)
   - **Design:** civilized_remnants_detailed_design.md
   - Role: Assassin
   - Services: Assassination contracts (100-500g, 3-turn delay, 20% discovery)
   - Consequences: Public branding if discovered, Echo trust penalty, un-branding blocked

5. **the_fence** (undercity)
   - **Design:** civilized_remnants_detailed_design.md
   - Role: Criminal vendor
   - Services: Buy stolen items (50% value), sell contraband (lockpicks 30g, poison 50g, disguise 40g)

6. **whisper** (undercity)
   - **Design:** civilized_remnants_detailed_design.md
   - Role: Information seller
   - Services: Sell NPC secrets (20g), location secrets (30g), valuable secrets (40-100g)

7. **weaponsmith_toran** (market_square)
   - **Design:** civilized_remnants_detailed_design.md
   - Role: Vendor (weapons, armor, repair)
   - Services: Sell weapons (sword 40g, silver_sword 100g, dagger 20g, crossbow 60g)
   - Services: Sell armor (leather 30g, chain_shirt 80g), repair (10-30g)
   - Reputation gate: Bad reputation (-3) = refuses service entirely

### Sunken District Placeholders

8. **old_swimmer_jek** (survivor_camp)
   - **Design:** sunken_district_detailed_design.md
   - Role: Swimming teacher (basic only; Garrett teaches advanced)
   - Services: Basic swimming (5g OR food item, 1 turn, breath +15)
   - Dialog: 3 topics (swimming, price, favor - find Garrett)
   - **CRITICAL:** Required for tidal_passage skill gate (blocks Garrett rescue)

9. **predatory_fish** (flooded_chambers)
   - **Design:** sunken_district_detailed_design.md
   - Type: Environmental hazard (NOT combat encounter)
   - Behavior: Watch in shallows, attack once in deep water (8HP + bleeding condition)
   - Properties: hazard_type="environmental", not_combat_encounter=true, no_xp_or_loot=true

### Beast Wilds Placeholders

10. **giant_spider_1** (spider_thicket)
    - Sketch has encounter reactions (territorial attack)

11. **giant_spider_2** (spider_thicket)
    - Sketch has encounter reactions (pack behavior)

### Fungal Depths Placeholders

12. **npc_sporeling_1** (spore_heart)
    - Sketch has item_use reactions (feeding triggers growth)

13. **npc_sporeling_2** (spore_heart)
    - Sketch has item_use reactions (feeding triggers growth)

14. **npc_sporeling_3** (spore_heart)
    - Sketch has item_use reactions (feeding triggers growth)

**Impact:** These NPCs appear in game but are completely non-interactive. Players can see them via `look` but cannot interact.

**Priority:** MEDIUM - Enrichment NPCs, not blocking core gameplay (except old_swimmer_jek)

---

## Complete/Adequate Implementations (21 NPCs)

These NPCs appear to have adequate implementations matching their sketch designs:

- **alpha_wolf** - gift_reactions ✓
- **bear_cub_1, bear_cub_2** - item_use_reactions ✓
- **bee_queen** - dialog + gift + take reactions ✓ (tested in #419)
- **camp_leader_mira** - dialog + commitment reactions ✓ (tested in #420)
- **curiosity_dealer_vex** - dialog + gift reactions ✓
- **damaged_guardian** - item_use + dialog reactions ✓
- **dire_bear** - encounter + gift reactions ✓
- **healer_elara** - dialog + gossip reactions ✓ (tested in #422)
- **herbalist_maren** - dialog reactions ✓
- **hunter_sira** - encounter + death + item_use + dialog ✓ (tested in #418)
- **npc_aldric** - item_use + dialog reactions ✓
- **npc_myconid_elder** - encounter + dialog reactions ✓
- **npc_spore_mother** - item_use + death + dialog reactions ✓
- **sailor_garrett** - death + condition reactions ✓
- **stone_golem_1, stone_golem_2** - item_use + death + dialog ✓
- **steam_salamander_2, steam_salamander_3** - dialog reactions ✓
- **the_archivist** - dialog + gift reactions ✓
- **the_echo** - dialog + gossip reactions ✓

Note: "Complete" means has some reactions/behaviors. May still have gaps vs sketch not yet analyzed.

---

## NPCs Not Implemented (In Sketches Only)

These NPCs are defined in sketch files but do NOT exist in game_state.json:

1. **bee_swarm** (beast_wilds)
   - Type: hostile_creature
   - Encounter reactions for bee queen protection

2. **child_survivor** (sunken_district)
   - Type: human_npc
   - Dialog about parents, fear of water

3. **gate_guard_1, gate_guard_2** (civilized_remnants)
   - Type: human_npc
   - Dialog about entry requirements, faction reputation

4. **grey_wolf_1, grey_wolf_2, grey_wolf_3** (beast_wilds)
   - Type: hostile_creature
   - Pack encounter mechanics

5. **spider_queen** (beast_wilds)
   - Type: boss_creature
   - Complex encounter + death reactions

6. **steam_salamander_1** (frozen_reaches)
   - Type: neutral_creature
   - Gift/dialog reactions

**Impact:** Missing creatures reduce world richness, encounter variety. Not blocking core gameplay.

**Priority:** LOW - Expansion content

---

## NPCs Created Ad-Hoc (Not in Sketches)

These NPCs exist in game_state.json but are NOT in any sketch file:

- **frost_wolf_1, frost_wolf_2** (wolf_clearing)
- **gate_guard** (town_gate) - Note: sketches have gate_guard_1/gate_guard_2, this is different
- **salamander** (hot_springs) - Distinct from steam_salamander_1/2/3
- **spider_matriarch** (spider_matriarch_lair) - Distinct from spider_queen
- **waystone_spirit** (nexus_chamber)

**Status:** These may be intentional additions or refactorings of sketch NPCs. Requires design review.

---

## Deep Dive: old_swimmer_jek (CRITICAL PLACEHOLDER)

**Why Critical:** Jek teaches swimming skill, which is REQUIRED to traverse tidal_passage to reach sailor_garrett.

**Sketch Design (sunken_district_sketch.json):**

```json
"old_swimmer_jek": {
  "name": "Old Swimmer Jek",
  "type": "human_npc",
  "description": "A leathery old man with ropey swimmer's muscles.",
  "dialog_topics": {
    "swimming": {
      "keywords": ["swim", "swimming", "teach", "learn"],
      "summary": "'In my day, every child knew how to swim before they could read...'"
    },
    "price": {
      "keywords": ["cost", "pay", "price"],
      "summary": "'Three silver for basic strokes. Ten silver for deep water technique.'"
    },
    "favor": {
      "keywords": ["favor", "free", "help"],
      "summary": "'Bring me Mira's blessing and I'll teach you for free.'"
    }
  },
  "teaching": {
    "skill": "swimming",
    "levels": ["basic", "advanced"],
    "cost": {
      "basic": 3,
      "advanced": 10
    },
    "free_with_commitment": "mira_favor"
  }
}
```

**Current Game State:**
```json
"old_swimmer_jek": {
  "id": "old_swimmer_jek",
  "name": "Old Swimmer Jek",
  "description": "A leathery old man with ropey swimmer's muscles, drying salvaged rope.",
  "location": "survivor_camp",
  "inventory": [],
  "properties": {},
  "behaviors": []
}
```

**Gap:** Complete placeholder. Zero implementation of:
- dialog_reactions for 3 dialog topics
- teaching mechanics (skill acquisition system)
- commitment integration (free teaching with Mira's favor)

**Blocker Impact:** Without swimming skill, player cannot reach sailor_garrett. Entire dual rescue quest unplayable.

**Priority:** CRITICAL - Required for core quest path

---

## Recommendations

**UPDATED:** All placeholders except sporelings/spiders have full design specs in detailed_designs/.

### Immediate Priorities (Can Implement Now)

1. **old_swimmer_jek** - CRITICAL (blocks dual rescue quest)
   - Full spec in sunken_district_detailed_design.md
   - Requires: teaching system + dialog + service integration

2. **merchant_delvan** - HIGH (70% done, needs completion)
   - Full spec in sunken_district_detailed_design.md
   - Requires: 2 dialog topics + commitment_reactions config

### Short-Term Priorities (Well-Documented)

3. **Undercity NPCs** (shadow, the_fence, whisper)
   - Full specs in civilized_remnants_detailed_design.md
   - Requires: Service systems (assassination, trading, information)
   - Systems: May need trading/contract infrastructure

4. **Council NPCs** (asha, hurst, varn)
   - Full specs in civilized_remnants_detailed_design.md
   - Requires: Quest preference system, un-branding ceremony
   - Systems: Faction/politics integration with quests

5. **weaponsmith_toran**
   - Full spec in civilized_remnants_detailed_design.md
   - Requires: Service dialog + reputation gates

6. **predatory_fish**
   - Full spec in sunken_district_detailed_design.md
   - Requires: Environmental hazard reactions (not combat)

### Long-Term Enrichment (Minimal Documentation)

7. Remaining placeholders (sporelings, giant spiders) - Only basic descriptions
8. Not-implemented NPCs from sketches (bee_swarm, child_survivor, etc.)
9. Deep review of "complete" NPCs for subtle gaps (dialog topics, state transitions, etc.)

---

## Next Steps

1. **User Decision:** Prioritize which NPCs to implement next
2. **For Each Selected NPC:**
   - Create focused issue using Workflow A
   - Design reactions based on sketch + infrastructure patterns
   - Implement using TDD
   - Create walkthrough test
   - Verify 100% walkthrough success
   - Document any test difficulties in issue #423

3. **Consider System Enhancements:**
   - Teaching/skill acquisition system (for old_swimmer_jek, others)
   - Reward delivery mechanism (for commitment quest completion)
   - Black market/trading system (for undercity NPCs)

---

## Related Issues

- #408 - Phase 6-7: Reaction system testing (revealed these gaps)
- #423 - Omitted test cases (tracks difficult-to-test mechanics)
- #424 - THIS ISSUE - NPC implementation gaps inventory
- #417 - Default reactions design (deferred work on pervasive reactions)
