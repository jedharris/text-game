# Big Game Content Audit and Implementation Plan

**Issue**: #251
**Version**: 2.0
**Last Updated**: 2025-12-22
**Status**: Implementation Plan

---

## Overview

This plan addresses the implementation of all designed but unimplemented content in the Big Game, organized by region. Based on experience with Myconid Elder and Luminous Grotto, implementation must include:

1. **Spatial authoring** - Adding missing locations, items, and actors to game_state.json
2. **Vocabulary additions** - Ensuring all entities and verbs are parseable
3. **Behavior handlers** - Implementing custom handlers for non-standard interactions
4. **State updates** - Configuring state machines, dialog_topics, conditions, llm_context
5. **Walkthrough testing** - Verifying each piece works via command sequences

Each phase ends with a walkthrough test that exercises all new content.

---

## Related Documents

- [NPC Interaction Inventory](npc_interaction_inventory.md) - current status of all NPCs
- [Narrator JSON Simplification Design](../narrator_json_simplification_design.md) - API design
- Detailed design docs for each region in `detailed_designs/`
- Walkthrough guide in `sketches_and_walkthroughs/walkthrough_guide.md`

---

## Implementation Approach

### Per-Entity Workflow

For each entity (NPC, item, location, puzzle):

1. **Read design** - Check detailed design document for specification
2. **Add to game_state.json** - Create or update entity with all required properties
3. **Add vocabulary** - Ensure nouns/adjectives are in merged vocabulary
4. **Implement handlers** - Create behavior handlers if needed
5. **Write walkthrough commands** - Create test sequence in walkthrough file
6. **Run walkthrough** - Execute `tools/walkthrough.py` to verify
7. **Debug and fix** - Address any failures, update vocabulary/handlers as needed
8. **Document** - Update npc_interaction_inventory.md with completion status

### Walkthrough Testing Protocol

```bash
# Run a single test sequence
python tools/walkthrough.py examples/big_game "look" "talk to aldric" "ask aldric about infection" --verbose

# Run from file
python tools/walkthrough.py examples/big_game --file walkthroughs/test_fungal_depths.txt
```

Each walkthrough test file should contain:
- Comments documenting expected behavior (`# Expected: learns about silvermoss`)
- All commands needed to reach and test the content
- Final state verification commands (`look`, `inventory`)

---

## Phase 1: Fungal Depths Completion

**Design source**: `docs/big_game_work/detailed_designs/fungal_depths_detailed_design.md`
**Prior work**: Phase 1 NPC authoring complete (Aldric dialog_topics, Myconid Elder dialog_topics + llm_context)

### 1.1 Light Puzzle Completion ✅ COMPLETE

The light puzzle is fully implemented with:
- Bucket with water_capacity
- `light_puzzle.py` behavior handling watering effects
- Location light_level tracking
- 4 mushroom items (blue, gold, violet, black)
- Pool as water source
- Fill and pour verbs working

### 1.2 Spore Mother Non-Verbal Handler

**Current state**: Has `llm_context` and `item_use_reactions.healing`, but NO talk handler

**Design reference**: Section 1.5 - Empathic Spore Communication
- Communication vocabulary: pain spike, waves of need, gentle probing, warmth flood, pressure surge
- Does NOT use standard dialog_topics
- `talk to spore mother` should return empathic description, delay combat 1 turn

**Implementation**:
1. Create `behaviors/regions/fungal_depths/spore_mother.py::on_spore_mother_talk`
2. Handler returns empathic description based on Spore Mother state
3. Add handler reference to game_state.json: `"talk_handler": "behaviors.regions.fungal_depths.spore_mother:on_spore_mother_talk"`
4. Update `item_use_reactions` if needed for heartmoss region-wide effect

**Walkthrough test**:
```
# Navigate to Spore Heart (requires safe_path_known)
go west
go down
go down

# Test talk interaction
talk to spore mother
# Expected: empathic description, no combat trigger

look
# Expected: still alive, not attacked by sporelings

# Give heartmoss (if have it)
give heartmoss to spore mother
# Expected: healing event, region-wide spore_level change to "none"
```

### 1.3 Missing Spatial Content

**Dead Explorer** (design reference: Section 1.1, luminous_grotto):
- Location: luminous_grotto
- Carries: research_notes (gift item for Aldric)

**Items to add to game_state.json**:
```json
{
  "id": "dead_explorer",
  "name": "dead explorer",
  "location": "luminous_grotto",
  "description": "A dead explorer lies slumped against the far wall. Their clothing is covered in fungal growth, but they still clutch a worn notebook.",
  "portable": false,
  "searchable": true,
  "contains": ["research_notes"]
}
```

```json
{
  "id": "research_notes",
  "name": "research notes",
  "location": "dead_explorer",
  "description": "Detailed notes on fungal biology and cave exploration. A scholar would find these valuable.",
  "portable": true,
  "gift_value": {"npc_aldric": 1}
}
```

**Walkthrough test**:
```
go west
go down
look
# Expected: See dead explorer

examine dead explorer
search dead explorer
take research notes
go up

give research notes to aldric
# Expected: Aldric accepts, teaching unlocked
```

### 1.4 Myconid Elder Verification

**Current state**: Has 5 dialog_topics (greeting, cure, resistance, spore_mother, cold) + llm_context

**Walkthrough test**:
```
go west
go down
go east

talk to myconid elder
ask elder about cure
ask elder about resistance
ask elder about spore mother
ask elder about cold
take spore lantern
take breathing mask
# Expected: Both items taken (trust >= 0)
```

### Phase 1 Complete Walkthrough

Create `walkthroughs/test_fungal_depths.txt`:
```
# Phase 1: Fungal Depths Complete Test
# Prerequisites: None (fresh game)

# Entry and Aldric dialog
go west
look
talk to aldric
ask aldric about infection
ask aldric about research
ask aldric about myconids

# Get silvermoss
go down
look
take silvermoss

# Light puzzle
take bucket
fill bucket
pour water on gold mushroom
fill bucket
pour water on blue mushroom
fill bucket
pour water on gold mushroom
# Expected: light_level 6, safe_path_known flag

# Get research notes
examine dead explorer
search dead explorer
take research notes

# Return and cure Aldric
go up
give silvermoss to aldric
# Expected: Aldric stabilized

give research notes to aldric
# Expected: Aldric offers teaching

# Visit Myconid Sanctuary
go down
go east
look
talk to myconid elder
ask elder about cure
ask elder about resistance
take spore lantern
take breathing mask
# Expected: Both items taken (trust >= 0)

# Access Deep Root Caverns
go west
go down
wear mask
go down
look
# Expected: See heartmoss with lantern
take heartmoss

# Heal Spore Mother
go up
talk to spore mother
# Expected: Empathic communication
give heartmoss to spore mother
# Expected: Healing, region-wide change

# Verify region state
look
# Expected: Clean air, friendly Spore Mother
```

---

## Phase 2: Meridian Nexus Verification

**Design source**: `docs/big_game_work/detailed_designs/meridian_nexus_detailed_design.md`
**Prior work**: The Echo has custom handler

### 2.1 The Echo Verification

The Echo has:
- Custom dialog handler in `behaviors/regions/meridian_nexus/echo.py`
- dialog_topics with handler paths
- gossip_reactions handler
- Trust tracking and gated content

**Walkthrough test**:
```
# Start at Nexus Chamber
look
examine waystone

# Find Echo in Keeper's Quarters
go north
look
talk to echo
ask echo about disaster
ask echo about restoration
ask echo about waystone
ask echo about my promises
# Expected: Lists all commitments (empty initially)
```

### 2.2 Waystone Fragment Verification

**Walkthrough test**:
```
# With a fragment
place fragment on waystone
# or: give fragment to waystone
# Expected: Fragment accepted, count incremented
```

---

## Phase 3: Beast Wilds Completion

**Design source**: `docs/big_game_work/detailed_designs/beast_wilds_detailed_design.md`
**Prior work**: Hunter Sira dialog_topics + llm_context, Wolf Pack llm_context

### 3.1 Hunter Sira Verification

**Walkthrough test**:
```
# Navigate to Hunter's Camp
go east
# (additional navigation as needed)
look

talk to sira
ask sira about injury
ask sira about beasts
ask sira about elara
# Expected: Learn about Elara connection, potential commitment
```

### 3.2 Bee Queen Non-Verbal Handler

**Current state**: Has state_machine, trust_state, trades_for, gift_reactions - NO talk handler

**Design reference**: Section 1.5 - Antenna/wing communication
- "Antennae wave. She doesn't speak, but there's... expectation?"
- Trade is item-based, not dialog-based

**Implementation**:
1. Create `behaviors/regions/beast_wilds/bee_queen.py::on_bee_queen_talk`
2. Return description of antenna/wing signals indicating expectation
3. Add to game_state.json

**Walkthrough test**:
```
# Navigate to Bee Queen's Clearing
go [path]
look

talk to queen
# Expected: Antenna description, expectation sense

give wildflower to queen
# Expected: Trade for royal honey
```

### 3.3 Wolf Pack Verification

**Current state**: Has llm_context with 5 states

**Walkthrough test**:
```
# Navigate to Wolf Den
go [path]
look
# Expected: Hostile pack

give venison to alpha
give venison to alpha
give venison to alpha
# Expected: Trust rising

# Attempt companion (at trust 3+)
ask alpha to follow
# Expected: Success
```

### 3.4 Missing Entities: Dire Bear, Bear Cubs, Predator's Den

**Design reference**: Section 1.2 (dire_bear), Section 1.1 (predators_den)

**Location to add** (predators_den):
```json
{
  "id": "predators_den",
  "name": "Predator's Den",
  "description": "A dark cave mouth opens in the hillside. Deep growling echoes from within. Small shapes move near the back - bear cubs.",
  "exits": {
    "out": "appropriate_location"
  }
}
```

**Actors to add**:
```json
{
  "id": "dire_bear",
  "name": "Dire Bear",
  "description": "A massive bear, larger than any natural beast. Her eyes are intelligent, wary. She guards her cubs.",
  "location": "predators_den",
  "state_machine": {
    "states": ["hostile", "wary", "tolerant", "friendly"],
    "initial": "hostile"
  },
  "has_cubs": true
}
```

```json
{
  "id": "bear_cub_1",
  "name": "Bear Cub",
  "description": "A small bear cub, malnourished and weak.",
  "location": "predators_den",
  "conditions": ["starving"]
}
```

**Walkthrough test**:
```
# Navigate to Predator's Den
go [path]
look
# Expected: See dire bear (hostile), cubs

# Gift-based approach
give fresh meat to dire bear
# Expected: Trust increase, less hostile

# Heal cubs
use healing herbs on cub
use healing herbs on other cub
# Expected: Bear becomes tolerant/friendly
```

### Phase 3 Complete Walkthrough

Create `walkthroughs/test_beast_wilds.txt`:
```
# Phase 3: Beast Wilds Complete Test

# Entry
go east
look

# Sira interaction
go [to hunter's camp]
talk to sira
ask sira about injury
use bandages on sira
# Expected: Bleeding stabilized

# Wolf pack
go [to wolf den]
give venison to alpha
give venison to alpha
give venison to alpha
# Expected: Trust 3, companion available

# Bee Queen
go [to clearing]
talk to queen
# Expected: Antenna expectation
give wildflower to queen
# Expected: Royal honey received

# Dire Bear (if added)
go [to predator's den]
use healing herbs on cub
use healing herbs on cub
# Expected: Bear friendly
```

---

## Phase 4: Frozen Reaches Completion

**Design source**: `docs/big_game_work/detailed_designs/frozen_reaches_detailed_design.md`

### 4.1 Fire Salamander Gesture Handler

**Current state**: Has state_machine, trust_state, fire_creature, gift_reactions - NO talk handler

**Design reference**: Section 1.5 - Gesture vocabulary
- Points at torch → wants fire
- Two fists apart → warning about golems
- Flame behavior indicates emotional state

**Implementation**:
1. Create `behaviors/regions/frozen_reaches/salamander.py::on_salamander_talk`
2. Return gesture description based on salamander state and context
3. Handle follow-up "ask about X" as gesture responses

**Walkthrough test**:
```
# Navigate to Hot Springs
go [path]
look

talk to salamander
# Expected: Gesture toward torch

ask salamander about temple
# Expected: Two fists, warding gesture

give torch to salamander
# Expected: Trust +1, happy flame

give fire crystal to salamander
# Expected: Major trust, companion-ready
```

### 4.2 Missing Entities: Stone Guardians, Temple Sanctum

**Design reference**: Section 1.1 (temple_sanctum), Section 1.2 (stone_guardian)

**Location to add**:
```json
{
  "id": "temple_sanctum",
  "name": "Temple Sanctum",
  "description": "A vast chamber lined with frost-covered pillars. Two massive stone guardians stand at the far end.",
  "exits": {"out": "temple_entrance"}
}
```

**Actors to add**:
```json
{
  "id": "stone_guardian_1",
  "name": "Stone Guardian",
  "description": "A massive construct of ancient stone, runes covering its body.",
  "location": "temple_sanctum",
  "is_construct": true,
  "state_machine": {
    "states": ["dormant", "hostile", "passive", "serving"],
    "initial": "dormant"
  },
  "password_phrase": "fire-that-gives-life and water-that-cleanses, united in purpose"
}
```

**Walkthrough tests**:

Password path:
```
go [to temple sanctum]
look
# Guardians activate on approach

say "fire-that-gives-life and water-that-cleanses, united in purpose"
# Expected: Guardians become passive
```

Control crystal path:
```
use control crystal on guardian
# Expected: Guardian becomes serving
```

### Phase 4 Complete Walkthrough

Create `walkthroughs/test_frozen_reaches.txt`:
```
# Phase 4: Frozen Reaches Complete Test

# Entry
go [path from Nexus]
look
# Expected: Cold environment

# Find Hot Springs
go [path]
look
# Expected: Warm zone, salamander

# Befriend salamander
talk to salamander
give torch to salamander
give fire crystal to salamander
# Expected: Companion-ready

# Temple Sanctum - password path
go [to sanctum]
say "fire-that-gives-life and water-that-cleanses, united in purpose"
# Expected: Guardians passive
```

---

## Phase 5: Sunken District Completion

**Design source**: `docs/big_game_work/detailed_designs/sunken_district_detailed_design.md`

### 5.1 Missing Dialog Topics

**Camp Leader Mira** - needs dialog_topics:
- camp, help, garrett, delvan

**Old Swimmer Jek** - needs dialog_topics:
- swimming, price, favor

**The Archivist** - needs dialog_topics:
- identity, disaster, water_pearl, knowledge_quest

**Implementation per NPC**:
1. Add dialog_topics to game_state.json from design Section 1.2
2. Add llm_context if not present
3. Test with walkthrough

### 5.2 Swimming Skill System

**Walkthrough test**:
```
go [to survivor camp]
talk to jek
ask jek about swimming
# Expected: Offers to teach for 5 gold

give gold to jek
# Expected: Learn basic_swimming skill

# Test swimming
go [to flooded area]
swim
# Expected: Success (with skill)
```

### 5.3 Rescue Scenarios

**Walkthrough test - Garrett rescue**:
```
ask mira about garrett
# Expected: Location and urgency

go [to sea caves]
# Expected: See Garrett struggling

help garrett
# Expected: Rescue success if in time
```

### Phase 5 Complete Walkthrough

Create `walkthroughs/test_sunken_district.txt`:
```
# Phase 5: Sunken District Complete Test

# Entry
go [path from Nexus]
look

# Survivor Camp
go [to camp]
talk to mira
ask mira about camp
ask mira about garrett
ask mira about delvan
# Expected: Learn about rescues

# Learn swimming
talk to jek
ask jek about swimming
give gold to jek
# Expected: Learn basic_swimming

# Garrett rescue
go [to sea caves]
help garrett
# Expected: Rescue

# Archivist
go [to deep archive]
talk to archivist
ask about water pearl
# Expected: Quest info
```

---

## Phase 6: Civilized Remnants Completion

**Design source**: `docs/big_game_work/detailed_designs/civilized_remnants_detailed_design.md`
**Prior work**: Healer Elara dialog_topics + llm_context, Curiosity Dealer Vex dialog_topics + llm_context

### 6.1 NPCs Already Complete

- **Healer Elara** - 4 dialog_topics + llm_context
- **Curiosity Dealer Vex** - 4 dialog_topics + llm_context

### 6.2 NPCs Needing Dialog Topics

**Gate Guard**:
- Topics: business, inspection, companions, infection

**Herbalist Maren**:
- Topics: wares, herbalism, trust, garden
- Services: basic herbalism teaching

**Weaponsmith Toran**:
- Topics: weapons, armor, repair, prices
- Services: sell_weapons, sell_armor, repair_weapons

**Council members** (3 NPCs):
- Topics: council, problems, refugees, traders, punishment
- Complex dilemma system

**Undercity NPCs** (3 NPCs):
- the_fence: buying, selling, rumors
- whisper: information, prices, council_secrets
- shadow: services, targets, consequences

### 6.3 Council Dilemma System

**Design reference**: Section 2.3 (Dilemmas), Appendix B

**Walkthrough test**:
```
go [to council hall]
talk to council
ask about problems
# Expected: Three dilemmas listed

ask about infected refugees
# Expected: Dilemma details

ask hurst about refugees
ask asha about refugees
ask varn about refugees
# Expected: Different perspectives

propose quarantine with medical care
# Expected: Councilor reactions
```

### 6.4 Undercity Access

**Walkthrough test**:
```
# Build trust with Vex
talk to vex
sell ice crystals to vex
sell spider silk to vex
# Expected: Trust 2+

ask vex about private
ask vex about undercity
# Expected: Trapdoor location revealed

go [to trapdoor]
go down
look
# Expected: Undercity access
```

### 6.5 Guardian Repair

**Walkthrough test**:
```
go [to broken statue hall]
examine guardian
# Expected: Dormant, damaged

use stone chisel on guardian
use animator crystal on guardian
# Expected: Guardian repaired

designate purpose: protect the town
# Expected: Guardian active
```

### Phase 6 Complete Walkthrough

Create `walkthroughs/test_civilized_remnants.txt`:
```
# Phase 6: Civilized Remnants Complete Test

# Entry and inspection
go [to town gate]
talk to guard
submit to inspection
# Expected: Pass (if clean)

# Market Square
go [to market]
talk to maren
buy healing potion
ask about herbalism

talk to toran
ask about weapons

# Elara connection (from Beast Wilds)
go [to healer's sanctuary]
ask elara about sira
# Expected: Connection dialog

# Vex and undercity
talk to vex
sell ice crystals to vex
ask vex about private
go [to undercity]
talk to fence
talk to whisper

# Council
go [to council hall]
talk to council
ask about problems

# Guardian repair
go [to broken statue hall]
use repair materials
designate purpose: protect the town
# Expected: Guardian active
```

---

## Cross-Region Integration Tests

After all phases complete, run cross-region walkthroughs:

### Test A: Commitment Cascade
From `cross_region_walkthrough_A_commitment_cascade.md`

### Test B: Companion Journey
From `cross_region_walkthrough_B_companion_journey.md`

### Test C: Dark Path
From `cross_region_walkthrough_C_dark_path.md`

---

## Phasing Summary

| Phase | Region | Key Work | Priority |
|-------|--------|----------|----------|
| 1 | Fungal Depths | Light puzzle, Spore Mother handler, spatial items | HIGH |
| 2 | Meridian Nexus | Verification only | LOW |
| 3 | Beast Wilds | Bee Queen handler, Dire Bear + cubs, verify wolves | HIGH |
| 4 | Frozen Reaches | Salamander handler, Stone Guardians + Temple | MEDIUM |
| 5 | Sunken District | 3 NPC dialog_topics, swimming, rescues | MEDIUM |
| 6 | Civilized Remnants | 9+ NPC dialog_topics, dilemmas, undercity, guardian | HIGH |

---

## Progress Tracking

### Phase 1 NPC Authoring ✅ COMPLETE (2025-12-21)
- [x] Alpha Wolf llm_context
- [x] Frost wolves llm_context
- [x] Wolf pack handler update
- [x] Hunter Sira dialog_topics + llm_context
- [x] Healer Elara dialog_topics + llm_context
- [x] Myconid Elder dialog_topics + llm_context
- [x] Curiosity Dealer Vex dialog_topics + llm_context

### Phase 1 Spatial/Puzzle Work ✅ COMPLETE (2025-12-22)
- [x] Light puzzle mushroom items
- [x] Fill verb for bucket
- [x] Pour verb routing
- [x] Dead explorer + worn notebook (research notes)
- [x] Spore Mother empathic talk handler
- [x] Complete walkthrough test passes (36/36 commands)

### Phase 2 ✅ COMPLETE (2025-12-22)
- [x] Echo verification walkthrough (15/15 commands pass)
- [x] Waystone fragment configuration (item_use_reactions added)
- [x] Spore heart fragment item created and tested

### Waystone Fragment Requirements

Each region must provide a waystone fragment when the player completes its main quest. Fragment implementation requirements:

1. **Create fragment item in game_state.json** with:
   - `id`: `{region_id}_fragment` (e.g., `spore_heart_fragment`)
   - `location`: `null` (given as reward, not found in world)
   - `properties`: `{ "portable": true, "waystone_fragment": true, "quest_item": true, "synonyms": [...] }`

2. **Update reward handler** to give fragment to player:
   - Set `fragment.location = "player"`
   - Add fragment ID to `player.inventory`

3. **Add fragment ID to waystone's accepted_items** in `item_use_reactions.fragment_placement`

**Fragments by Region**:
| Region | Fragment ID | Source | Status |
|--------|-------------|--------|--------|
| Fungal Depths | `spore_heart_fragment` | Heal Spore Mother with heartmoss | ✅ Complete |
| Beast Wilds | `alpha_fang_fragment` | Befriend or defeat Alpha Wolf | Pending |
| Frozen Reaches | `ice_shard_fragment` | Complete temple challenge | Pending |
| Sunken District | `water_bloom_fragment` | Rescue drowned spirit / Archivist quest | Pending |
| Civilized Remnants | `echo_essence_fragment` | Guardian repair / Council dilemma | Pending |

### Phase 3
- [ ] Bee Queen talk handler
- [ ] Dire Bear + cubs + Predator's Den
- [ ] Wolf pack walkthrough verification
- [ ] Sira walkthrough verification
- [ ] Create `alpha_fang_fragment` item and reward handler

### Phase 4
- [ ] Salamander gesture handler
- [ ] Stone Guardians + Temple Sanctum
- [ ] Telescope verification
- [ ] Create `ice_shard_fragment` item and reward handler

### Phase 5
- [ ] Mira dialog_topics
- [ ] Jek dialog_topics
- [ ] Archivist dialog_topics
- [ ] Swimming skill system
- [ ] Rescue scenario verification
- [ ] Create `water_bloom_fragment` item and reward handler

### Phase 6
- [ ] Gate Guard dialog_topics
- [ ] Herbalist Maren dialog_topics
- [ ] Weaponsmith Toran dialog_topics
- [ ] Council (3) dialog_topics + dilemma system
- [ ] Undercity (3) dialog_topics
- [ ] Guardian repair verification
- [ ] Create `echo_essence_fragment` item and reward handler

### Cross-Region Tests
- [ ] Commitment Cascade walkthrough
- [ ] Companion Journey walkthrough
- [ ] Dark Path walkthrough

---

## Success Criteria

Each phase is complete when:

1. All entities from design exist in game_state.json
2. All custom handlers implemented and registered
3. All vocabulary additions made (entities parseable)
4. Walkthrough test file runs without parse errors
5. All expected outcomes occur (verified in walkthrough output)
6. npc_interaction_inventory.md updated with completion status
7. Phase issue closed with summary comment

Final success: All cross-region walkthroughs complete without errors.
