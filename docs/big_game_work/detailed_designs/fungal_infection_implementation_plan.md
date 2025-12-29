# Fungal Infection System - Implementation Plan

**Parent Issue**: #326
**Status**: COMPLETE (All 6 Phases Finished)
**Last Updated**: 2025-12-29

---

## Implementation Strategy

### Phasing Approach

Break fungal infection implementation into independent, testable phases:
- Each phase has a focused scope with clear deliverables
- Each phase includes comprehensive walkthrough testing
- Phases can be implemented incrementally without blocking each other
- Deferred work is tracked and merged into later phases

### Testing Strategy: Fix Local, Defer Systemic

**Fix Immediately** (during current phase):
- Blocking issues that prevent testing
- Localized bugs within the current phase scope
- Simple missing data (items, properties) needed for walkthrough
- Code duplication/redundancy within current phase modules

**Defer to Separate Phase** (track in this document):
- Systemic issues affecting multiple regions/modules
- Architectural changes requiring design decisions
- Infrastructure work (new hooks, core systems)
- Cross-region dependencies
- Features requiring extensive testing beyond current scope

---

## Completed Phases

### Phase 1: Player Fungal Infection Damage ✅
**Issue**: #327 (Closed)
**Scope**: Environmental spore exposure causes severity-tiered damage to player

**Deliverables**:
- Damage tier calculation in `conditions.py` (0/2/4/7/10 at severity 20/40/60/80)
- Hook ordering fix: spore_infection runs BEFORE condition_tick
- Walkthrough: `walkthroughs/phase1_fungal_damage.txt` (26 turns, all assertions pass)

**Work Done**:
- Added fungal_infection damage tier calculation to `tick_conditions()`
- Fixed spore_zones hook from `after: condition_tick` → `before: condition_tick`
- Removed redundant damage calculation from spore_zones.py

**Key Decisions**:
- Damage tier logic lives in conditions.py (generic condition processor)
- Spore zones only modify severity; tick_conditions handles damage calculation
- This ensures all actors (NPCs, player, future entities) get correct damage scaling

---

### Phase 2: NPC Damage via Progression ✅
**Issue**: #328 (Closed)
**Scope**: NPCs with progression_rate correctly update damage_per_turn as severity increases

**Deliverables**:
- Validated tick_conditions() handles NPC infections with progression_rate
- Walkthrough: `walkthroughs/phase2_aldric_infection.txt` (20 assertions pass)

**Work Done**:
- Fixed Aldric's initial damage_per_turn (7 → 10 to match severity 80)
- Confirmed damage tier calculation works for all actors, not just player

**Key Findings**:
- No new code needed - Phase 1 implementation already handles NPCs
- Progression_rate causes severity increase, which triggers damage recalculation
- Net damage correctly calculated: damage_per_turn - regeneration

---

### Phase 3: Treatment and Cure System ✅
**Issue**: #329 (Closed)
**Scope**: Silvermoss treatment reduces infection severity and enables cure path

**Deliverables**:
- Two-stage cure: stabilize (first silvermoss) → recover (second silvermoss)
- Walkthrough: `walkthroughs/phase3_treatment_cure.txt` (21 assertions pass)

**Work Done**:
- Removed hardcoded damage_per_turn from aldric_rescue.py treatment handler
- Added silvermoss_2 item to game_state.json for complete cure testing
- Validated treatment reduces severity, stops progression, allows healing

**Local Fixes Applied**:
- Added second silvermoss item (blocked complete cure testing)
- Fixed hardcoded damage value (contradicted automatic calculation)

**Key Findings**:
- First silvermoss: severity 80→40, progression stops, damage 10→4, net +1 HP/turn
- Second silvermoss: infection removed completely, full +5 HP/turn regen
- Treatment modifies severity; tick_conditions automatically updates damage tier

---

### Phase 4: Equipment Protection - Breathing Mask ✅
**Issue**: #330 (Closed)
**Scope**: Validate breathing mask prevents spore zone infection

**Deliverables**:
- Breathing mask blocks all environmental spore exposure
- Walkthrough: `walkthroughs/phase4_breathing_mask.txt` (31 commands, 13 assertions pass)

**Work Done**:
- No code changes needed - functionality already exists in spore_zones.py
- Fixed command syntax: `get breathing mask` → `take mask`

**Key Findings**:
- `_has_breathing_mask()` checks equipment and inventory correctly
- Mask provides absolute protection in both medium and high spore zones
- Existing infections persist but don't worsen (mask prevents new exposure only)

**Deferred Work Identified**:
- Trust-gated equipment access (see Deferred Work section below)

---

### Phase 5: Environmental Hazards - Safe Path & Zone Warnings ✅
**Issue**: #331 (Closed)
**Scope**: Light puzzle + safe path knowledge + zone entry warnings

**Deliverables**:
- Light puzzle solution sets `safe_path_known` flag
- High spore zone infection: 10 → 3 with flag (safe path reduces exposure)
- Zone entry warnings validated for all spore levels
- Walkthrough: `walkthroughs/phase5_environmental_hazards.txt` (28 commands, all assertions pass)

**Work Done**:
- Fixed bucket charge double-decrement bug in light_puzzle.py
- Fixed _apply_infection to use conditions library instead of obsolete list format
- Tested all mushroom types: blue (+1 safe), gold (+2 safe), violet (+15 infection dangerous), black (-2 dangerous)
- Validated light puzzle mechanic: water mushrooms to reach light level 6, read ceiling for safe path knowledge
- Confirmed safe path knowledge reduces high spore infection rate: 10 → 3 severity/turn

**Key Findings**:
- Light puzzle fully implemented and functional (just had 2 bugs)
- Water bucket system works correctly (managed by liquid_lib)
- Safe path knowledge significantly reduces high spore exposure
- Zone warnings provide appropriate feedback for spore levels

---

### Phase 6: Death from Infection ✅
**Issue**: #332 (Closed)
**Scope**: Player and NPC death from infection

**Deliverables**:
- Extended `walkthroughs/phase2_aldric_infection.txt` to validate Aldric's death
- Created `walkthroughs/phase6_player_death.txt` for player death validation
- Both walkthroughs pass with death messages confirmed

**Work Done**:
- Extended Phase 2 walkthrough with 2 additional turns to trigger Aldric's death
- Created comprehensive player death test (32 turns in high spore zone)
- Validated death messages: "Scholar Aldric has been slain!", "Wanderer has been slain!"
- Confirmed dead actors removed from state.actors dict

**Key Findings**:
- Death detection works via `turn_death_check` hook in combat.py
- Death occurs when health <= 0
- Both NPCs and player use same death handler (`on_death`)
- No code changes needed - death system already fully functional

---

## Fungal Infection Testing - COMPLETE

All 6 phases of fungal infection mechanics validation completed. See issue #326 for completion summary and deferred work.

---

### Phase 7: Aldric Commitment Timer (if time permits)
**Scope**: 50-turn commitment timer system

**Tentative Deliverables**:
- Commitment creation → timer starts
- Timer tick and warning messages
- Timer expiration → Aldric death
- Hope bonus (+10 turns)

**Dependencies**:
- Commitment system implementation status
- Turn tracking integration

**Estimated Effort**: Medium (timer mechanics + 50+ turn walkthrough)

**NOTE**: May defer if commitment system not ready

---

### Phase 8+: Advanced Features (Future Work)
**Scope**: Cross-region dependencies, services, complex interactions

**Tentative Areas**:
- Myconid Elder services (cure, teaching) - requires Frozen Reaches
- Deep Root Caverns (toxic air, breath holding, heartmoss)
- Spore Mother healing mechanics
- Trust-gated equipment (infrastructure change)

**Why Deferred**:
- Cross-region dependencies
- Infrastructure changes required
- Not blocking core infection mechanics

**Approach**:
- Address after core infection system complete
- Likely separate issue/effort from #326
- May belong to broader region implementation work

---

## Deferred Work

### Infrastructure Issues

#### 1. Trust-Gated Item Taking (Phase 4 Deferred)
**Status**: Not Implemented
**Scope**: Systemic infrastructure change

**Current State**:
- Breathing mask has `requires_trust: 0` property in game_state.json
- Property is not enforced - player can take mask regardless of trust
- Trust system exists for NPCs but not item access

**What's Needed**:
- Modify core item manipulation (take/get handler) to check `requires_trust`
- Compare against NPC trust level (Myconid Elder trust in this case)
- Block take action if trust < threshold
- Provide appropriate feedback ("The Myconids won't let you take that")

**Why Deferred**:
- Affects core manipulation.py (not localized to fungal infection)
- Requires design: which NPC's trust? Location-based? Item property points to NPC?
- Impacts all regions that might use trust-gated items
- Testing requires trust manipulation mechanics

**Recommended Approach**:
- Separate phase or separate issue (not fungal infection specific)
- Design trust-gating mechanism first (property schema, NPC association)
- Implement in manipulation.py with proper handler integration
- Test across multiple contexts (not just breathing mask)

**Tracking**: To be added to umbrella issue #326 deferred work list

---

#### 2. Myconid Elder Services (Future Phase)
**Status**: Designed, Not Implemented
**Scope**: Cross-region service system

**Current State**:
- Myconid Elder NPC exists with `services` property: ["cure_infection", "teach_spore_resistance"]
- `accepts_payment` property: ["ice_wand", "rare_mineral", "gold"]
- No behavior handlers implement these services
- Trading system exists (trading.py) but not connected to Elder

**What's Needed**:
- Service handlers for cure_infection and teach_spore_resistance
- Payment acceptance logic (check for payment items, consume them)
- Trust requirements for services (Elder requires trust >= 2 for teaching)
- Cross-region item dependencies (ice crystals from Frozen Reaches)

**Why Not Yet Implemented**:
- Requires cross-region coordination (Frozen Reaches for ice crystals)
- Service system pattern needs design (similar to civilized_remnants/services.py?)
- Teaching system (grant spore_resistance skill) needs skill effect implementation

**Recommended Phases**:
- Phase 7: Myconid Cure Service (ice crystal payment, full infection removal)
- Phase 8: Spore Resistance Teaching (trust >= 2, skill grants 50% infection reduction)

**Dependencies**:
- Frozen Reaches region (ice_wand/ice_crystal items)
- Skill system for spore_resistance effect
- Trust system integration

---

#### 3. Aldric Death Timer (Future Phase)
**Status**: Designed, Not Implemented
**Scope**: Commitment-based timer system

**Current State**:
- Design specifies 50-turn timer (60 with hope bonus)
- Timer should start when player commits to help
- No timer implementation exists
- No death-by-timer logic exists (only health-based death)

**What's Needed**:
- Commitment creation hook (on_aldric_commitment handler exists but not tested)
- Timer tick mechanism (turn counter, compare to deadline)
- Death trigger when timer expires (health = 0, state = "dead")
- Warning messages at intervals (10 turns left, 5 turns left)

**Why Deferred**:
- Commitment system may not be fully implemented
- Requires turn tracking integration
- Testing requires multi-turn walkthroughs (50+ turns)

**Recommended Approach**:
- Phase 9: Aldric Commitment Timer
- Test commitment creation → timer start
- Test timer expiration → Aldric death
- Test hope bonus (+10 turns when player commits)

---

#### 4. Spore Zone Entry Warnings (Partial Implementation)
**Status**: Code exists, not validated
**Scope**: Player experience / messaging

**Current State**:
- `on_enter_spore_zone()` handler exists in spore_zones.py (lines 143-208)
- Provides warnings based on spore level and equipment
- Not tested in any walkthrough

**What's Needed**:
- Walkthrough validation of entry messages
- Verify warnings appear for high/medium/low spore zones
- Verify mask message when entering with protection
- Verify safe_path_known message variations

**Why Deferred**:
- Not blocking core infection mechanics
- User experience polish, not functional requirement
- Can be validated after core phases complete

**Recommended Approach**:
- Add to Phase 6 (Safe Path Knowledge) walkthrough
- Or create separate Phase 10: Polish & Messaging

---

### Content Gaps

#### 5. Deep Root Caverns (Not Yet Tested)
**Status**: Designed, implementation unknown
**Scope**: Toxic air zone requiring breathing mask

**Current State**:
- Location exists in design: `deep_root_caverns`
- Properties: `breathable: false`, `requires_light: true`
- Contains heartmoss (cures Spore Mother)
- Breath holding mechanic: 12 turns, then 20 damage/turn

**What's Needed**:
- Toxic air damage implementation (non-breathable zones)
- Breath holding timer
- Light requirement (darkness blocks visibility/actions)
- Heartmoss item and Spore Mother cure mechanics

**Dependencies**:
- Breathing mask validation (Phase 4 complete ✓)
- Light source system (spore lantern)
- Spore Mother healing mechanics

**Recommended Phases**:
- Phase 11: Toxic Air & Breath Holding
- Phase 12: Spore Mother Healing (heartmoss cure path)

---

#### 6. Light Puzzle (Unknown Status)
**Status**: Designed, implementation unknown
**Scope**: Environmental puzzle, safe path unlock

**Current State**:
- Design specifies mushroom + water puzzle
- Goal: Increase light level 2 → 6 to read ceiling inscription
- Mushrooms: blue (+1 safe), gold (+2 safe), violet (dangerous), black (-2 dangerous)
- Solution sets `safe_path_known` flag

**What's Needed**:
- Water bucket mechanics (fill from pool, pour on mushrooms)
- Mushroom interaction (watering causes glow, different effects)
- Light level tracking and ceiling visibility
- Flag setting on solution

**Dependencies**:
- Phase 6 will reveal what's implemented vs missing

**Recommended Approach**:
- Start Phase 6, document findings
- Implement missing mechanics as local fixes if small
- Defer large puzzle system work if needed

---

## Phase Selection Criteria

When choosing next phase:

1. **Dependency Order**: Phases with no external dependencies first
2. **Risk Reduction**: High-uncertainty phases early (discover unknowns)
3. **Incremental Value**: Each phase adds testable functionality
4. **Deferred Work Integration**: Merge deferred issues into appropriate phases

**Current Recommendation**: Phase 5 (Player Death) - no dependencies, validates end state of infection progression.

---

## Document Maintenance

This document should be updated:
- **After each phase completion**: Move phase from Planned → Completed, document findings
- **When new deferred work is identified**: Add to Deferred Work section with rationale
- **When phases are reorganized**: Update Planned Phases with new scope/dependencies
- **When deferred work is addressed**: Move from Deferred → Planned, create phase for it

**Update Process**:
1. Complete phase → document in Completed Phases
2. Identify deferred work → add to Deferred Work with justification
3. Plan next phase → update Planned Phases
4. Reorganize as needed based on discoveries
