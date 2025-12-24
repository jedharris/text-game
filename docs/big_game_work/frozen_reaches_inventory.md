# Frozen Reaches Implementation Inventory

**Created**: 2025-12-22
**Phase**: 4 of Big Game Content Audit (#251)
**Issue**: #265

This document compares the [Frozen Reaches Detailed Design](detailed_designs/frozen_reaches_detailed_design.md) against the current implementation in `game_state.json` and behavior modules.

---

## Summary

The Frozen Reaches region is **partially implemented**:
- ✅ Hypothermia system implemented (`hypothermia.py`)
- ✅ Golem puzzle handlers implemented (`golem_puzzle.py`)
- ✅ Salamander befriending handlers implemented (`salamanders.py`)
- ⚠️ **Locations**: 4 of 5 exist (missing `temple_sanctum` and `ice_caves`)
- ❌ **NPCs**: 1 of 5 exist (only 1 salamander, missing golems + 2 more salamanders)
- ❌ **Items**: 2 of 12 core items exist (telescope exists, but 10+ items missing)
- ❌ **Puzzles**: Handlers exist but entities are missing
- ❌ **Talk handlers**: Salamander needs non-verbal talk handler

---

## Locations

### Current Locations in game_state.json

| Location ID | Name | Design Match | Notes |
|-------------|------|--------------|-------|
| `frozen_pass` | Frozen Pass | ✅ Match | Entry point, exits to south/north/east |
| `hot_springs` | Hot Springs | ⚠️ Partial | Exists but needs properties review |
| `frozen_observatory` | Frozen Observatory | ✅ Match | Top of temple |
| `observatory_platform` | Observatory Platform | ⚠️ Extra | Not in design - may be duplicate/related |

### Missing Locations

| Location ID (proposed) | Name | Design Source | Priority |
|------------------------|------|---------------|----------|
| `ice_caves` | Ice Caves | Section 1.1 | **HIGH** - Contains 4 treasure items |
| `temple_sanctum` | Temple Sanctum | Section 1.1 | **HIGH** - Golem puzzle location |

**Notes**:
- `frozen_pass` should have 4 exits: south (nexus), north (temple), east (ice_caves), west (hot_springs)
- Current `frozen_pass` has: south, north, east (missing west)
- `observatory_platform` may be intended as temple sanctum entry, needs investigation
- `temple_sanctum` should have exits: south (frozen_pass), up (frozen_observatory)

---

## NPCs

### Current NPCs in game_state.json

| Actor ID | Name | Design Match | Implementation | Notes |
|----------|------|--------------|----------------|-------|
| `salamander` | Fire Salamander | ⚠️ Partial | Partial | Only lead salamander exists |

**Salamander Review**:
- ✅ Has `state_machine` with correct states
- ✅ Has `trust_state` (0-5 range)
- ✅ Has `gift_reactions` handler wired
- ❌ Missing `llm_context` for state-based descriptions
- ❌ Missing `talk_handler` for non-verbal communication
- ✅ Located at `hot_springs`

### Missing NPCs

| Actor ID (proposed) | Name | Design Source | Priority |
|---------------------|------|---------------|----------|
| `stone_golem_1` | Stone Guardian | Section 1.2 | **HIGH** - Core puzzle |
| `stone_golem_2` | Stone Guardian | Section 1.2 | **HIGH** - Linked to golem_1 |
| `steam_salamander_2` | Steam Salamander | Section 1.2 | **MEDIUM** - Follower, state mirrors lead |
| `steam_salamander_3` | Steam Salamander | Section 1.2 | **MEDIUM** - Follower, state mirrors lead |

**Notes**:
- Golem handlers in `golem_puzzle.py` reference `stone_golem_1` and `stone_golem_2`
- Golems need: `state_machine`, `dialog_reactions` (password), `item_use_reactions` (crystal/ritual), `death_reactions`
- Salamander followers need: pack mirroring config, same trust thresholds as lead

---

## Items

### Current Items in game_state.json

| Item ID | Name | Design Match | Location | Notes |
|---------|------|--------------|----------|-------|
| `frozen_telescope` | Frozen Telescope | ✅ Match | `frozen_observatory` | Exists but needs repair components |
| `frozen_crystal` | Frozen Crystal | ❓ Unknown | `crystal_garden` | Not in design - may be control_crystal? |

### Missing Items

#### Frozen Pass Camp Items (Section 1.3)
| Item ID (proposed) | Name | Purpose | Priority |
|--------------------|------|---------|----------|
| `cold_weather_gear` | Cold Weather Gear | Halves hypothermia rate | **HIGH** |
| `preserved_supplies` | Preserved Supplies | Contains torch, bandages, dried meat | **HIGH** |
| `partial_map` | Partial Map | Reveals hints, dangers | **MEDIUM** |

#### Ice Caves Items (Section 1.3)
| Item ID (proposed) | Name | Purpose | Priority |
|--------------------|------|---------|----------|
| `frost_lily` | Frost Lily | Trade item for Bee Queen | **HIGH** - Cross-region |
| `ice_shard` | Ice Shard | Waystone fragment | **CRITICAL** - Required for waystone |
| `crystal_lens` | Crystal Lens | Telescope component | **HIGH** - Puzzle item |
| `control_crystal` | Control Crystal | Golem control (best solution) | **HIGH** - Puzzle item |

**Note**: `ice_caves` location must be created first with sub-areas (main, deep, hidden side passage)

#### Temple Sanctum Items (Section 1.3)
| Item ID (proposed) | Name | Purpose | Priority |
|--------------------|------|---------|----------|
| `mounting_bracket` | Mounting Bracket | Telescope component | **HIGH** - Puzzle item |
| `cold_resistance_cloak` | Cold Resistance Cloak | Cold immunity / 50% freezing reduction | **HIGH** - Major reward |
| `fire_crystal` | Fire Crystal | Fire-aspected gift for salamanders | **HIGH** - Enables befriending |
| `lore_tablets` | Lore Tablets | Backstory, password, hints | **MEDIUM** - Puzzle help |

#### Service Items (Section 1.3)
| Item ID (proposed) | Name | Purpose | Priority |
|--------------------|------|---------|----------|
| `salamander_heated_stone` | Salamander-heated Stone | Portable warmth (~20 turns) | **MEDIUM** - Service reward |

#### Waystone Fragment (Phase 4 Requirement)
| Item ID (proposed) | Name | Purpose | Priority |
|--------------------|------|---------|----------|
| `ice_shard_fragment` | Ice Shard (Waystone Fragment) | Waystone repair | **CRITICAL** - Phase requirement |

**Notes**:
- `ice_shard` vs `ice_shard_fragment`: Design calls the item "ice_shard" and says it's a waystone fragment. May be same item.
- `frozen_crystal` in game_state may be intended as `control_crystal` - needs investigation
- `fire_crystal` is in temple side chamber, accessible without defeating golems (design Section 1.1)

---

## Handlers and Systems

### Implemented Behavior Modules

#### `hypothermia.py` ✅ COMPLETE
- ✅ `on_cold_zone_turn` - Turn phase hypothermia application
- ✅ `on_enter_hot_springs` - Instant cure on entry
- ✅ Temperature zones: warm, cold, freezing, extreme
- ✅ Gear effects: cold_weather_gear (50%), cloak (immune/50%), salamander (immune)
- **Status**: Fully implemented, ready for testing once locations have proper `temperature` properties

#### `golem_puzzle.py` ✅ HANDLERS COMPLETE
- ✅ `on_golem_password` - Password deactivation
- ✅ `on_golem_item_use` - Control crystal & ritual routing
- ✅ `on_golem_death` - Destruction consequences
- ✅ Helper: `_deactivate_golems` - Linked state transitions
- **Status**: Handlers ready, needs golem NPCs and items in game_state

#### `salamanders.py` ✅ HANDLERS COMPLETE
- ✅ `on_fire_gift` - Fire item gifting with trust increase
- ✅ `on_salamander_state_change` - State mirroring (currently no-op)
- ✅ Pack behavior: Followers mirror lead state
- **Status**: Handlers ready, needs follower salamanders and talk handler

### Missing Handlers

| Handler | Purpose | Module | Priority |
|---------|---------|--------|----------|
| `on_salamander_talk` | Non-verbal gesture communication | `salamanders.py` | **HIGH** |
| State mirroring activation | Wire `steam_salamander_2` and `steam_salamander_3` | `salamanders.py` | **MEDIUM** |

**Salamander Talk Handler Requirements** (Design Section 1.5):
- Gesture vocabulary: pointing at fire, shaking head at cold, warning gestures
- Flame behavior: brightens (happy), dims (frightened), flickers (excited)
- Posture: head tilt (curious), curls near (trusting), backs away (wary)
- Sounds: crackle (pleased), hissing (warning), rumble (content)
- Should return EventResult with gesture description based on state

---

## Puzzles and Systems

### Golem Deactivation Puzzle (Design Section 1.4)

**Four Solutions**:
1. ✅ Password - Handler exists (`on_golem_password`)
2. ✅ Control Crystal - Handler exists (`on_golem_item_use`)
3. ✅ Ritual Offering - Handler exists (`on_golem_item_use`)
4. ✅ Combat - Handler exists (`on_golem_death`)

**Missing**:
- ❌ Golem NPCs with proper configuration
- ❌ Control crystal item
- ❌ Lore tablets with password hints
- ❌ Dialog reactions wiring in golem NPCs

### Telescope Repair (Design Section 1.4)

**Three Components**:
1. ✅ `crystal_lens` - (missing item)
2. ✅ `mounting_bracket` - (missing item)
3. ✅ `cleaning_supplies` - Should exist in Meridian Nexus

**Missing**:
- ❌ Telescope item_use_reactions handler for component installation
- ❌ Component items
- ❌ Repaired telescope functionality (reveals NPC states, prevents cold spread)

### Ice Extraction (Design Section 1.4)

**Requirements**: Heat source + time

**Missing**:
- ❌ Items frozen in ice (crystal_lens, control_crystal, ice_shard)
- ❌ Ice extraction mechanic handler
- ❌ Heat source validation

---

## Infrastructure Integration

### Temperature Zones (Design Section 4.1)

Current location `temperature` property status:

| Location | Expected Zone | Current Status | Notes |
|----------|---------------|----------------|-------|
| `frozen_pass` | Cold (+5/turn) | ❓ Needs verification | Entry point |
| `hot_springs` | Warm (0, instant cure) | ❓ Needs verification | Sanctuary |
| `ice_caves` | Freezing (+10/turn) | ❌ Missing | Not created yet |
| `temple_sanctum` | Cold (+2.5/turn) | ❌ Missing | Not created yet |
| `frozen_observatory` | Extreme (+20/turn) | ❓ Needs verification | Top level |

### Hypothermia Condition

- ✅ Condition type defined in infrastructure
- ✅ Turn phase handler implemented
- ✅ Severity thresholds: 30 (mild), 60 (severe), 80 (critical)
- ❌ Location turn_phase_effects configuration needed

### State Machines

**Golems** (Design Appendix B.2):
```json
{
  "state_machine": {
    "states": ["guarding", "hostile", "passive", "serving", "destroyed"],
    "initial": "guarding"
  }
}
```

**Salamanders** (Current):
```json
{
  "state_machine": {
    "states": ["neutral", "friendly", "companion", "hostile", "dead"],
    "initial": "neutral"
  }
}
```
✅ Matches design

### Cross-Region Items

| Item | Destination | Status |
|------|-------------|--------|
| `ice_shard` | Meridian Nexus (waystone) | ❌ Missing |
| `frost_lily` | Beast Wilds (Bee Queen trade) | ❌ Missing |
| `ice_crystals` | Fungal Depths (Myconid payment) | ❓ Unknown |

**Note**: `ice_crystals` may be `frozen_crystal` or may need to be created

---

## Vocabulary

### Required Vocabulary Additions

The following words must be in vocabulary (either base vocab or behavior vocab):

**Nouns** (from item names):
- cold, weather, gear, supplies, map
- frost, lily, ice, shard, crystal, lens, control
- mounting, bracket, cloak, resistance
- fire, lore, tablets
- salamander, heated, stone
- golem, guardian, temple, sanctum

**Adjectives**:
- cold, frozen, frost, ice, fire, hot
- (Most should be auto-extracted or already exist)

**Verbs** (for puzzle interactions):
- melt, heat, warm, thaw (for ice extraction)
- speak, say (for password - likely already exist)
- install, repair, fix (for telescope - may need verification)

---

## Testing Requirements

### Unit Tests Needed

1. ✅ Hypothermia system tests - Likely already exist
2. ✅ Golem puzzle tests - Likely already exist
3. ✅ Salamander befriending tests - Likely already exist
4. ❌ Salamander talk handler tests - New
5. ❌ Ice extraction tests - New
6. ❌ Telescope repair tests - New

### Walkthrough Tests Needed

From `npc_authoring_implementation_plan.md` Phase 4:

1. ❌ `walkthroughs/test_frozen_reaches.txt` - Full region walkthrough
2. ❌ Salamander gesture communication test
3. ❌ Golem password path test
4. ❌ Golem control crystal path test
5. ❌ Telescope repair test
6. ❌ Hypothermia survival test

---

## Implementation Recommendations

### Sub-Phasing

Based on the inventory, I recommend the following sub-phases:

#### **Sub-Phase 4.1: Spatial Foundation** (2-3 hours)
**Priority**: CRITICAL - Enables all other work

**Work**:
1. Create missing locations (`ice_caves`, `temple_sanctum`)
2. Fix `frozen_pass` exit to hot springs (add west exit)
3. Add temperature properties to all locations
4. Add turn_phase_effects configuration for hypothermia
5. Create frozen pass camp items (gear, supplies, map)
6. Verify location connectivity

**Success**: Player can navigate all 5 locations, hypothermia system active

#### **Sub-Phase 4.2: Golem Puzzle** (3-4 hours)
**Priority**: HIGH - Core puzzle content

**Work**:
1. Create `stone_golem_1` and `stone_golem_2` actors
2. Wire golem handlers (dialog_reactions, item_use_reactions, death_reactions)
3. Create puzzle items (control_crystal, lore_tablets, fire_crystal, mounting_bracket, cold_resistance_cloak)
4. Test all 4 deactivation paths (password, crystal, ritual, combat)
5. Create walkthrough tests for each path

**Success**: All 4 golem solutions work, golems properly linked

#### **Sub-Phase 4.3: Salamander Non-Verbal Communication** (2-3 hours)
**Priority**: HIGH - Unique interaction pattern

**Work**:
1. Add `llm_context` to lead salamander with state descriptions
2. Implement `on_salamander_talk` handler with gesture vocabulary
3. Create `steam_salamander_2` and `steam_salamander_3` actors
4. Wire pack mirroring between salamanders
5. Test gesture communication and state transitions
6. Create walkthrough test for befriending

**Success**: Salamander talk returns gestures, followers mirror state, companion recruitment works

#### **Sub-Phase 4.4: Ice Caves and Telescope** (3-4 hours)
**Priority**: MEDIUM - Completion content

**Work**:
1. Add ice caves sub-areas (main, deep, hidden passage)
2. Create treasure items (frost_lily, ice_shard, crystal_lens)
3. Implement ice extraction mechanic
4. Create telescope repair handler
5. Test telescope reveal functionality
6. Create walkthrough test

**Success**: All treasures extractable, telescope repairable, reveals work

#### **Sub-Phase 4.5: Waystone Fragment** (1-2 hours)
**Priority**: CRITICAL - Phase requirement

**Work**:
1. Create `ice_shard_fragment` item (or verify `ice_shard` is the fragment)
2. Add reward handler for temple puzzle completion
3. Wire fragment to waystone's `item_use_reactions`
4. Test fragment placement at waystone

**Success**: Completing temple puzzle gives fragment, fragment placeable at waystone

#### **Sub-Phase 4.6: Verification and Polish** (2-3 hours)
**Priority**: HIGH - Ensures quality

**Work**:
1. Create complete `walkthroughs/test_frozen_reaches.txt`
2. Run all walkthrough tests
3. Fix any failures
4. Update `npc_interaction_inventory.md`
5. Verify cross-region items (frost_lily, ice_shard)

**Success**: Complete walkthrough passes, all content verified

---

## Estimated Total Effort

**Total**: 13-19 hours of Claude work

**Breakdown**:
- Spatial Foundation: 2-3 hours
- Golem Puzzle: 3-4 hours
- Salamander Communication: 2-3 hours
- Ice Caves & Telescope: 3-4 hours
- Waystone Fragment: 1-2 hours
- Verification: 2-3 hours

**Critical Path**: Spatial → Golems → Salamander → Verification

**Parallel Opportunities**:
- Ice Caves work can overlap with Salamander work
- Waystone fragment can be done anytime after Golem puzzle

---

## Open Questions

1. **`frozen_crystal` vs `control_crystal`**: Is the existing `frozen_crystal` item intended to be the control crystal? Location is `crystal_garden` (Nexus) not ice caves.

2. **`observatory_platform` vs `temple_sanctum`**: Is `observatory_platform` intended as the temple entry? Design shows temple_sanctum as separate location with golems.

3. **Ice extraction mechanic**: Should this be a new handler or an extension of existing item_use_reactions?

4. **Telescope repair**: Should this be dialog-based ("repair telescope with lens") or item-based ("use lens on telescope")?

5. **`ice_shard` naming**: Design Section 1.3 calls it "ice_shard" but it's a waystone fragment. Should we create `ice_shard` (treasure) and `ice_shard_fragment` (reward) as separate items?

6. **Salamander heated stone**: Design shows this as a service item. Should it be created on-demand when salamander is friendly, or pre-created?

---

## Next Steps

**Immediate**:
1. ✅ Review this inventory with user
2. Resolve open questions
3. Choose sub-phasing approach
4. Create GitHub sub-issues if using sub-phases
5. Begin Sub-Phase 4.1 (Spatial Foundation)

**After Approval**:
- Start implementation following TDD workflow
- Update this document as decisions are made
- Track progress in phase issue #265
