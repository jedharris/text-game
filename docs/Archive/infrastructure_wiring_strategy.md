# Infrastructure Wiring: Strategy and Test Plan

**Date**: 2025-12-29
**Status**: Phase 0 Complete (Validation + Dispatcher fixes)
**Next**: Phase 1 (Player Infection Hook-up)

---

## Executive Summary

**Goal**: Wire up all implemented infrastructure systems so they're actually used in gameplay.

**Current State**: Infrastructure exists but isn't connected to content - zero virtual entities, regional hazards don't deal damage, core verbs missing.

**Strategy**: Small vertical slices (1-3 hours each) with immediate walkthrough validation. Build confidence incrementally, upgrade tools and process based on learnings.

**Key Learning from Phase 0**: Validation catches errors early. The new validation system found 41 systematic errors and a critical dispatcher pattern bug before any walkthrough failures.

---

## I. Overall Strategy

### 1. Vertical Slice Approach

**Definition**: Each phase implements one complete feature end-to-end, from infrastructure to content to walkthrough.

**Why**:
- Proves integration works immediately
- Catches design issues early
- Provides tangible progress
- Allows course correction between phases

**Not**: "Implement all commitments, then all gossip, then test"
**Instead**: "Implement Aldric commitment fully, test, learn, then next commitment"

### 2. Test-Driven Development Flow

**Every phase follows this cycle**:

1. **Plan** (15-30 min)
   - Review current state
   - Define success criteria
   - Identify files to modify
   - Sketch walkthrough outline

2. **Implement** (30-90 min)
   - Write/modify code
   - Add content configurations
   - Update vocabularies
   - Validation catches errors during development

3. **Test** (30-60 min)
   - Write/extend walkthrough
   - Run walkthrough
   - Fix failures
   - Iterate until green

4. **Review** (15-30 min)
   - Answer phase review questions
   - Update tools if needed
   - Document learnings
   - Plan next phase

### 3. Phasing Principles

**Small phases** (1-3 hours total):
- Phase 0 taught us: even "simple" phases find unexpected issues
- Better to have 30 small wins than 3 big struggles

**Immediate validation**:
- Validation system catches config errors at load time
- Walkthroughs catch gameplay errors at test time
- Fix before moving to next phase

**Progressive complexity**:
- Start simple (player infection)
- Add layers (NPC infection, curing, equipment)
- Build toward complex (multi-commitment overlap, gossip networks)

---

## II. Testing Infrastructure

### A. Current Walkthrough Tool

**Strengths**:
- ✅ Runs commands sequentially
- ✅ Shows success/failure clearly
- ✅ EXPECT_FAIL annotation for intentional failures
- ✅ HP tracking for combat
- ✅ Save game state option
- ✅ Stop on error mode
- ✅ Failure categorization

**Limitations**:
- ❌ No state assertions (can't verify HP, conditions, flags)
- ❌ No expected output matching (can't check exact message)
- ❌ No setup/teardown (every walkthrough starts from game_state.json)
- ❌ No variable capture/reuse
- ❌ No conditional commands (if/then)

### B. Walkthrough Tool Improvements

**Implement Now (before Phase 1)**:

**1. State Assertions** (HIGH PRIORITY)
```
# Syntax in walkthrough files:
take silvermoss
ASSERT player.inventory contains silvermoss
ASSERT player.hp == 95
ASSERT aldric.condition.fungal_infection.severity >= 40
```

**Why now**: Phase 1 tests infection damage. We need to verify HP changes, condition severity, damage_per_turn values. Without assertions, we're just checking "command succeeded" not "damage actually happened."

**Implementation**:
- Add `parse_assertion()` function
- Support: `entity.field == value`, `entity.field >= value`, `entity.field contains value`
- Add `--show-state` flag to dump state after each command (debugging)
- Assertions fail walkthrough if false

**Effort**: 2-3 hours (do before Phase 1)

**2. Expected Output Matching** (DEFER)
```
go west
EXPECT_OUTPUT "You feel spores entering your lungs"
```

**Why defer**: Nice to have but not critical. We can manually verify output during initial testing. Add if we find walkthroughs are missing subtle output bugs.

**3. Verbose Event Tracking** (DEFER - Phase 3 from validation plan)
```
--verbose-events flag shows:
- Turn phases executed
- Hooks invoked
- Handlers called
- Conditions applied
```

**Why defer**: Only needed when debugging confusing failures. Current tool gives enough info for now. Implement when we hit first "why didn't that work?" moment.

**Do Not Implement**:
- Setup/teardown - Complexity not justified
- Variables - Not needed for our use cases
- Conditionals - Overengineering
- Loops - Not needed

### C. Walkthrough Organization

**Directory structure**:
```
walkthroughs/
  test_fungal_depths.txt           # Existing - full region
  test_thermal_shock_combat_v2.txt # Existing - combat

  # New phase-specific walkthroughs:
  phase_01_player_infection.txt    # Phase 1: Basic infection damage
  phase_02_infection_scaling.txt   # Phase 2: Severity scaling
  phase_03_breathing_mask.txt      # Phase 3: Equipment protection
  phase_04_self_treatment.txt      # Phase 4: Using items
  ...
```

**Naming convention**: `phase_XX_feature.txt`

**Content**: Each walkthrough tests ONLY that phase's feature. Keep focused.

---

## III. Validation Strategy

### A. Load-Time Validation (Automated)

**Current checks** (all automated in `finalize_loading()`):
1. Hook prefix validation (turn_* vs entity_*)
2. Hook dependency validation
3. Event-to-hook references
4. Hook invocation consistency
5. Turn phase placement
6. Entity behavior paths (NEW - Phase 0)

**These catch**:
- Typos in behavior paths
- Missing modules
- Import errors with diagnostics
- Hook configuration errors

**When**: Every game load (including walkthrough tests)

**Action on failure**: Fix immediately - don't proceed with broken config

### B. Walkthrough Validation (Manual + Automated)

**Every phase includes**:
1. New or extended walkthrough file
2. Run walkthrough: `python tools/walkthrough.py examples/big_game --file walkthroughs/phase_XX_feature.txt`
3. Verify all commands succeed (or expected failures marked)
4. Verify assertions pass (once implemented)
5. Manually check output makes narrative sense

**Walkthrough success criteria**:
- All commands execute (no parse errors)
- Expected successes succeed
- Expected failures fail
- Assertions pass (HP changes, conditions applied, etc.)
- Narrative coherent (manual check)

### C. Integration Testing

**After every 3-5 phases**:
- Run ALL walkthroughs
- Verify no regressions
- Check cross-feature interactions
- Update master integration walkthrough

**Integration checkpoints**:
- After Phase 8 (Fungal Depths complete)
- After Phase 11 (Frozen Reaches complete)
- After Phase 14 (Sunken District complete)
- After Phase 20 (Virtual entities complete)
- After Phase 23 (Full game integration)

---

## IV. Phase Review Questions

**Answer these after EVERY phase** (document in phase issue comments):

### A. What Worked?

1. Did validation catch errors before walkthroughs?
2. Did the walkthrough pass on first run?
3. Was the phase size appropriate (1-3 hours)?
4. Did existing tools support the work well?

### B. What Didn't Work?

1. What unexpected issues arose?
2. What took longer than estimated?
3. What validation errors were missed?
4. What walkthrough features were lacking?

### C. Tool Improvements Needed?

1. Did we need assertions this phase? (record examples)
2. Did we need verbose event tracking? (record confusion points)
3. Did we need better error messages? (record unclear errors)
4. Any other tool gaps identified?

### D. Process Improvements?

1. Should phases be smaller/larger?
2. Should we test differently?
3. Should we plan differently?
4. What did we learn about the codebase?

### E. Design Issues Discovered?

1. Any infrastructure gaps found?
2. Any design conflicts found?
3. Any missing utilities needed?
4. Any patterns to standardize?

### F. Next Phase Planning?

1. Does the next planned phase still make sense?
2. Should we reorder based on learnings?
3. Should we add/remove phases?
4. Any prerequisite work needed?

**Recording**: Use GitHub issue comments on phase-specific issues

**Review cadence**:
- Answer A-D after every phase (5-10 min)
- Discuss E-F after every phase (5-10 min)
- Deeper review after integration checkpoints (30 min)

---

## V. Detailed Phase 1 Plan

### Phase 1: Player Infection Hook-up

**Goal**: Make fungal spores actually damage the player

**Duration**: 1-2 hours
- Implementation: 30-45 min
- Walkthrough tool improvement: 1 hour (assertions)
- Testing: 30 min

**Prerequisites**:
- ✅ Validation system integrated (Phase 0)
- ✅ Dispatcher pattern fixed (Phase 0)
- ⏳ Walkthrough assertions (implement first)

---

#### 1.1 Current State Analysis

**What exists**:
- `behaviors/regions/fungal_depths/spore_zones.py`:
  - `on_environmental_effect` handler exists
  - Sets condition `fungal_infection` with `severity` and `progression_rate`
  - Shows messages at severity tiers (20/40/60/80+)
  - **Never sets `damage_per_turn`** ❌

- Condition system (`behavior_libraries/actor_lib/conditions.py`):
  - `tick_conditions()` applies `damage_per_turn` each turn
  - `apply_condition()` supports all fields (severity, damage_per_turn, progression_rate)
  - Works correctly (proven by Aldric's pre-configured infection)

- Aldric's infection (in game_state.json):
  ```json
  "conditions": {
    "fungal_infection": {
      "severity": 60,
      "damage_per_turn": 7,
      "progression_rate": 0
    }
  }
  ```
  This proves the system works when configured correctly.

**The gap**:
- Spore zones set severity but not damage_per_turn
- Player can walk through spore zones with no mechanical consequence
- Only narrative messages show

---

#### 1.2 Implementation Tasks

**File**: `examples/big_game/behaviors/regions/fungal_depths/spore_zones.py`

**Change**: Add damage_per_turn calculation in `on_environmental_effect()`

**Damage scaling design** (Option A from Issue #300):
```python
# After calculating severity, add:
if severity >= 80:
    damage_per_turn = 10  # Critical - severe lung damage
elif severity >= 60:
    damage_per_turn = 7   # Severe - matching Aldric's level
elif severity >= 40:
    damage_per_turn = 4   # Moderate - painful but survivable
elif severity >= 20:
    damage_per_turn = 2   # Mild - minor irritation
else:
    damage_per_turn = 0   # Below threshold - no damage
```

**Implementation steps**:

1. Read current `spore_zones.py` to understand structure
2. Locate where `apply_condition()` is called
3. Add damage_per_turn calculation based on severity
4. Update condition messages to mention damage
5. Test load (validation should pass)

**Expected code change** (approximately):
```python
# In on_environmental_effect(), after calculating new_severity:

# Calculate damage based on severity tiers
if new_severity >= 80:
    damage_per_turn = 10
    severity_msg = "CRITICAL: Severe fungal infection ravaging your body!"
elif new_severity >= 60:
    damage_per_turn = 7
    severity_msg = "SEVERE: Fungal growth spreading through your lungs."
elif new_severity >= 40:
    damage_per_turn = 4
    severity_msg = "MODERATE: Spores taking hold, breathing difficult."
elif new_severity >= 20:
    damage_per_turn = 2
    severity_msg = "MILD: Spore exposure causing irritation."
else:
    damage_per_turn = 0
    severity_msg = None

# Apply condition with damage
apply_condition(
    player,
    "fungal_infection",
    severity=new_severity,
    damage_per_turn=damage_per_turn,
    progression_rate=progression_rate
)
```

---

#### 1.3 Walkthrough Tool Improvement

**Before testing Phase 1, add state assertions**:

**File**: `tools/walkthrough.py`

**New features**:

1. **Assertion syntax**:
   ```
   ASSERT player.hp >= 90
   ASSERT player.conditions.fungal_infection.severity >= 20
   ASSERT player.conditions.fungal_infection.damage_per_turn == 2
   ```

2. **State dump for debugging**:
   ```
   python tools/walkthrough.py examples/big_game --file test.txt --show-state
   ```
   Dumps full player state after each command

3. **Implementation outline**:
   - Add `parse_assertion()` to extract field path and comparison
   - Add `evaluate_assertion()` to walk object tree and compare values
   - Support operators: ==, !=, >, <, >=, <=, contains
   - Fail walkthrough if assertion fails
   - Show detailed error (expected vs actual)

**Estimated effort**: 2-3 hours
**Priority**: HIGH - needed for Phase 1 testing

---

#### 1.4 Walkthrough Design

**File**: `walkthroughs/phase_01_player_infection.txt`

**Test scenario**:
```
# Phase 1: Player Fungal Infection Basic Damage
# Goal: Verify spores damage player based on severity

# Start at Forest Edge (no infection)
look
ASSERT player.hp == 100

# Enter Cavern Entrance (low spore level)
go west
ASSERT player.conditions.fungal_infection.severity >= 10
ASSERT player.conditions.fungal_infection.severity < 20
ASSERT player.conditions.fungal_infection.damage_per_turn == 0

# Enter Luminous Grotto (moderate spore level)
go down
ASSERT player.conditions.fungal_infection.severity >= 20
ASSERT player.conditions.fungal_infection.damage_per_turn == 2

# Wait one turn (should take damage)
look
ASSERT player.hp <= 98  # Took 2 damage from infection

# Go deeper to Mycelium Chamber (high spore level)
go down
ASSERT player.conditions.fungal_infection.severity >= 40
ASSERT player.conditions.fungal_infection.damage_per_turn == 4

# Wait one turn (should take more damage)
look
ASSERT player.hp <= 94  # Took 4 more damage (98 - 4 = 94)

# Return to surface to verify condition persists
go up
go up
go east
ASSERT player.conditions.fungal_infection.severity > 0
# Severity should stop increasing outside spore zones
# But damage_per_turn should remain until cured

# Wait several turns outside spore zones
look
look
look
# HP should continue decreasing even outside zones
ASSERT player.hp < 90  # Progressive damage from persistent infection
```

**Expected behavior**:
- Entering spore zones increases severity and sets damage_per_turn
- Damage applies each turn via condition tick
- Infection persists after leaving spore zones
- Damage continues until cured (Phase 4)

**Success criteria**:
- All assertions pass
- All commands succeed
- Player HP decreases as expected
- Severity increases in spore zones, stabilizes outside

---

#### 1.5 Testing Process

1. **Implement walkthrough tool assertions** (2-3 hours)
   - Test assertion parser with simple examples
   - Test state evaluation with player.hp
   - Test nested field access (player.conditions.X.severity)
   - Commit tool improvements

2. **Implement infection damage** (30-45 min)
   - Modify spore_zones.py
   - Add damage_per_turn calculation
   - Test game loads without errors (validation)

3. **Run walkthrough** (15 min first run)
   - Execute phase_01_player_infection.txt
   - Expect some failures (tuning needed)
   - Check which assertions fail

4. **Debug and tune** (15-30 min)
   - Adjust damage values if needed
   - Fix any logic errors
   - Re-run until all assertions pass

5. **Verify narrative** (10 min)
   - Read through walkthrough output
   - Check messages make sense
   - Verify severity messages appear correctly

6. **Integration check** (10 min)
   - Run existing test_fungal_depths.txt
   - Ensure no regressions
   - Player should now take damage (different outcome than before)

---

#### 1.6 Success Criteria

**Code**:
- ✅ `spore_zones.py` sets damage_per_turn based on severity
- ✅ Damage values match design (0/2/4/7/10 at severity tiers)
- ✅ Game loads without validation errors
- ✅ No import errors, no typos

**Tools**:
- ✅ Walkthrough tool supports ASSERT syntax
- ✅ Assertions evaluate correctly
- ✅ Clear error messages when assertions fail
- ✅ --show-state flag works for debugging

**Testing**:
- ✅ Phase 1 walkthrough passes (all assertions)
- ✅ Existing walkthroughs still pass (or updated appropriately)
- ✅ Manual verification: damage values feel right in gameplay

**Process**:
- ✅ Phase review questions answered (document in issue)
- ✅ Learnings recorded for Phase 2 planning
- ✅ Tool improvements identified (if any)

---

#### 1.7 Risks and Mitigation

**Risk 1**: Damage values too high/low
- **Mitigation**: Start conservative (use Issue #300 values), tune based on walkthrough
- **Fallback**: Easy to adjust damage tiers and re-test

**Risk 2**: Assertion implementation takes longer than estimated
- **Mitigation**: Start simple (just == and >= operators), add more later
- **Fallback**: Test Phase 1 manually first, add assertions for Phase 2

**Risk 3**: Existing walkthroughs break (player now takes damage)
- **Mitigation**: Expected! Update walkthroughs to account for infection
- **Fallback**: Add "cure infection" command at start of non-infection tests

**Risk 4**: Condition system has bugs we haven't found
- **Mitigation**: Aldric's infection proves it works. Player infection should work same way.
- **Fallback**: Debug using --show-state flag to inspect condition state

---

#### 1.8 Files Modified

**Code**:
- `examples/big_game/behaviors/regions/fungal_depths/spore_zones.py` (~20 lines changed)

**Tools**:
- `tools/walkthrough.py` (~100-150 lines added for assertions)

**Tests**:
- `walkthroughs/phase_01_player_infection.txt` (new file, ~40 lines)
- `walkthroughs/test_fungal_depths.txt` (update if needed)

**Docs**:
- GitHub issue comment documenting Phase 1 results
- Update this strategy doc if process changes learned

---

#### 1.9 Estimated Timeline

**Preparation** (before starting Phase 1):
- Walkthrough tool assertions: 2-3 hours

**Phase 1 execution**:
- Implementation: 30-45 min
- Walkthrough writing: 15 min
- Testing and tuning: 30-45 min
- Documentation: 15 min

**Total Phase 1**: 4-5 hours (including tool improvement)

**Note**: Tool improvement is one-time cost. Phase 2+ will be faster.

---

## VI. Open Questions for Discussion

### A. Walkthrough Tool Priorities

**Question 1**: Should we implement assertions before Phase 1, or start Phase 1 with manual verification and add assertions for Phase 2?

**Option A**: Implement assertions now (2-3 hours upfront)
- Pro: Phase 1 test is rigorous and automated
- Pro: Proves tool works before we need it for harder phases
- Con: Delays starting actual feature work

**Option B**: Manual verification for Phase 1, assertions for Phase 2
- Pro: Start feature work immediately
- Pro: Learn what assertions we actually need
- Con: Phase 1 test less rigorous
- Con: Risk finding tool issues during harder phase

**My recommendation**: Option A - invest in tooling now. Phase 0 proved that good validation catches errors early.

---

**Question 2**: Should we add --show-state flag now or wait until we need it for debugging?

**Option A**: Add now as part of assertion work
- Pro: Minimal extra effort (10-15 min)
- Pro: Useful for verifying assertions during development
- Con: Might not need it

**Option B**: Wait until first confusing debugging session
- Pro: Don't build what we don't need yet
- Con: Will slow down debugging when needed

**My recommendation**: Option A - trivial to add, high utility for debugging.

---

### B. Phase 1 Scope

**Question 3**: Should Phase 1 include breathing mask protection, or save that for Phase 3?

**Phase 1A** (current plan): Just damage, no protection
- Player gets infected, takes damage
- No way to reduce damage yet
- Simpler, proves core mechanic

**Phase 1B** (expanded): Damage + basic mask protection
- Player can equip breathing mask
- Mask reduces severity/damage
- Requires implementing "equip" verb first
- More complex, tests protection mechanic

**My recommendation**: Phase 1A - prove damage works first, add protection in Phase 3. Don't mix concerns.

---

**Question 4**: Should we tune damage values in Phase 1, or use Issue #300 values and tune later?

**Option A**: Use Issue #300 values (0/2/4/7/10), tune if walkthrough shows problems
- Pro: Values already designed, based on Aldric's infection
- Pro: Can adjust if too harsh/lenient
- Con: Might need re-tuning in Phase 2

**Option B**: Spend extra time playtesting in Phase 1 to get values perfect
- Pro: Values correct from start
- Con: Delays later phases
- Con: Hard to judge without full context (healing, equipment, etc.)

**My recommendation**: Option A - use designed values, tune incrementally as we add healing/protection.

---

### C. Testing Strategy

**Question 5**: Should we run full integration tests after every phase, or only at checkpoints?

**Option A**: After every phase (23 full test runs)
- Pro: Catches regressions immediately
- Pro: Ensures everything works together
- Con: Time consuming (each integration test ~5-10 min)
- Con: May slow momentum

**Option B**: Only at checkpoints (5 full test runs)
- Pro: Faster iteration on phases
- Pro: Still catches regressions before moving to next part
- Con: Might discover regression late (harder to debug)

**My recommendation**: Option B - checkpoint integration tests. Phase-specific tests catch most issues.

---

**Question 6**: Should walkthroughs test edge cases, or just happy paths?

**Option A**: Happy path only
- Pro: Faster to write
- Pro: Proves feature works
- Con: Misses edge cases

**Option B**: Happy path + edge cases
- Pro: More robust testing
- Pro: Catches bugs early
- Con: Takes longer

**My recommendation**: Start with happy path (Phase 1-5), add edge cases as we discover them. Don't over-engineer tests upfront.

---

### D. Process Questions

**Question 7**: Should we create a GitHub issue for each phase, or track all 23 phases in issue #302?

**Option A**: One issue per phase (23 issues)
- Pro: Clear tracking, can close as we go
- Pro: Easy to link commits/PRs
- Pro: Good for review questions (comment per phase)
- Con: Issue spam

**Option B**: Track all in issue #302 with comments per phase
- Pro: Less issue clutter
- Pro: One place to see all progress
- Con: Hard to track individual phase status
- Con: Long comment thread

**My recommendation**: Option A - one issue per phase. Easier to track and review.

---

**Question 8**: How should we handle learnings that affect the plan?

**Scenario**: Phase 3 reveals we need a new utility function that would make Phases 4-8 easier.

**Option A**: Stop and refactor immediately
- Pro: Makes future phases easier
- Pro: Cleaner codebase
- Con: Disrupts momentum
- Con: Might not be worth it

**Option B**: Note it, finish current part (Phases 1-8), refactor between parts
- Pro: Maintains momentum
- Pro: More context for refactoring
- Con: Might repeat code across phases

**My recommendation**: Option B - note it, refactor at checkpoints. Unless it's trivial (<30 min) or blocks progress.

---

## VII. Next Steps

1. **Discuss this document**:
   - Review strategy and test plan
   - Answer open questions
   - Adjust Phase 1 plan based on discussion

2. **Decide on walkthrough tool**:
   - Implement assertions now, or defer?
   - Add --show-state flag?
   - Any other tool improvements?

3. **Approve Phase 1 plan**:
   - Scope correct?
   - Timeline reasonable?
   - Success criteria clear?

4. **Execute Phase 1**:
   - Implement tool improvements (if decided)
   - Implement infection damage
   - Write and run walkthrough
   - Document results and learnings

5. **Plan Phase 2**:
   - Based on Phase 1 learnings
   - Adjust as needed
   - Continue iteration

---

## VIII. Success Metrics

**For overall infrastructure wiring**:
- All 23 phases completed
- All virtual entities used in gameplay (>0 instances)
- All regional hazards deal damage
- Core verbs implemented (use, equip, trade)
- Full game integration test passes
- Zero validation errors
- All walkthroughs pass

**For each phase**:
- Code changes minimal and focused
- Validation passes on load
- Phase walkthrough passes
- Review questions answered
- No regressions in integration tests (at checkpoints)
- Time within estimate (1-3 hours)

---

**Ready to discuss and proceed with Phase 1.**
