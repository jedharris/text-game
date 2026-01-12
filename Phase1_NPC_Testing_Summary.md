# Phase 1 NPC Testing - Executive Summary
**Date:** 2026-01-10
**Task:** Test 8 Civilized Remnants NPCs (gate_guard, herbalist_maren, weaponsmith_toran, councilor_asha, councilor_hurst, councilor_varn, curiosity_dealer_vex)

---

## Results at a Glance

**NPCs Fully Testable:** 0/7
**NPCs Partially Testable:** 2/7 (herbalist_maren, curiosity_dealer_vex)
**NPCs Not Testable:** 5/7 (gate_guard, weaponsmith_toran, 3 councilors)

### Test Execution Results

| NPC | Walkthrough | Infrastructure | Commands Passed | Main Issues |
|-----|------------|---------------|----------------|-------------|
| herbalist_maren | test_herbalist_maren.txt | ✓ Present | 9/14 (64%) | Vocabulary mismatch in walkthrough |
| curiosity_dealer_vex | test_curiosity_dealer_vex.txt | ✓ Present | 4/16 (25%) | Wrong location, path syntax errors |
| gate_guard | test_gate_guard.txt | ✗ Missing | 2/7 (29%) | Wrong location, missing infrastructure |
| weaponsmith_toran | None | ✗ Missing | N/A | No infrastructure, no walkthrough |
| councilor_asha | None | ✗ Missing | N/A | No infrastructure, quest system not implemented |
| councilor_hurst | None | ✗ Missing | N/A | No infrastructure, quest system not implemented |
| councilor_varn | None | ✗ Missing | N/A | No infrastructure, quest system not implemented |

---

## Critical Findings

### 1. Infrastructure Gaps (5 NPCs)

**gate_guard** - Has config, missing module:
```json
behaviors: []  // ❌ EMPTY
properties: {
  "dialog_reactions": { ... }  // ✓ Configured but not connected
}
```
**Fix:** Add `behaviors.shared.infrastructure.dialog_reactions`

**weaponsmith_toran** - Has services list, no handler:
```json
behaviors: []  // ❌ EMPTY
properties: {
  "services": ["sell_weapons", "sell_armor", "repair_weapons"]
}
```
**Fix:** Add service handler module (like herbalist_maren uses)

**3 Councilors (asha, hurst, varn)** - Placeholder only:
```json
behaviors: []  // ❌ EMPTY
properties: {
  "philosophy": "...",  // ✓ Basic metadata only
  "trust": {...}
}
```
**Fix:** Requires NEW quest preference system infrastructure (per npc_upgrade_plan.md Phase 2.1)

---

### 2. Walkthrough Quality Issues (3 files)

**herbalist_maren** (9/14 passed):
- ❌ Item vocabulary mismatch: asks for "silvermoss" but item is "potent healing moss"
- ❌ Keyword mismatch: "teaching" not in dialog_reactions config
- ✅ Infrastructure works: trade display, pricing, trust adjustments all work
- **Fix:** Revise walkthrough to match actual vocabulary

**curiosity_dealer_vex** (4/16 passed):
- ❌ Navigation error: tries to talk to Vex from Ice Field instead of market_square
- ❌ Path syntax errors: uses `player.properties` instead of `actors.player.properties`
- ❌ Command syntax unclear: uses `talk to vex about X` (may need `ask vex about X`)
- **Fix:** Complete walkthrough rewrite needed

**gate_guard** (2/7 passed):
- ❌ Navigation error: goes to ice_caves instead of town_gate
- ❌ @expect syntax error: uses `"guard" OR "gate"` instead of proper OR syntax
- ❌ No infrastructure to test even if navigation fixed
- **Fix:** Fix navigation + syntax, then add infrastructure before testing

---

## What Actually Works

### herbalist_maren (Best Case)
```
✅ Navigation to market_square
✅ Dialog infrastructure fires
✅ Trade inventory display with prices
✅ Trust-based pricing (30% discount at trust=3)
✅ Item display shows: "potent healing moss (50 gold)"

❌ Item purchase fails (keyword "silvermoss" not recognized)
❌ Teaching dialog fails (keyword "teaching" not in config)
```

**Diagnosis:** Infrastructure is CORRECT. Walkthrough vocabulary is WRONG.

### curiosity_dealer_vex (Unknown - Cannot Test)
- Walkthrough too broken to evaluate NPC functionality
- Infrastructure appears present but unverified

---

## Blocking Issues by Priority

### HIGH Priority (Blocks Basic Testing)

1. **Missing infrastructure on gate_guard**
   - Impact: Cannot test ANY dialog scenarios
   - Effort: 5 minutes (add one line to behaviors array)

2. **Missing infrastructure on weaponsmith_toran**
   - Impact: Cannot test ANY service scenarios
   - Effort: 1 session (add service module + dialog config)

3. **Broken walkthroughs**
   - Impact: Cannot verify working NPCs actually work
   - Effort: 1 session to fix all 3 walkthroughs

### MEDIUM Priority (Blocks Advanced Testing)

4. **Quest preference system not implemented**
   - Impact: All 3 councilors are placeholders
   - Effort: 3-4 sessions (design + implement + test per councilor)
   - Note: This is a KNOWN gap per npc_upgrade_plan.md Phase 2.1

---

## Recommendations

### Option A: Quick Wins (Fix What's Close)
1. Fix herbalist_maren walkthrough (30 min)
2. Re-run to verify 100% success
3. Add infrastructure to gate_guard (5 min)
4. Create proper gate_guard walkthrough (1 hour)
5. **Result:** 2/7 NPCs fully tested

### Option B: Complete Civilized Remnants (Systematic)
1. Fix all 3 walkthroughs (1 session)
2. Add infrastructure to gate_guard + weaponsmith_toran (1 session)
3. Test gate_guard + weaponsmith_toran scenarios (1 session)
4. **Result:** 4/7 NPCs fully tested, 3 councilors documented as "requires quest system"

### Option C: Focus on Different Phase
- Move to Phase 3.2 (Medium Priority NPCs) or Phase 3.3 (Creature Encounters)
- Come back to councilors after quest preference system is designed

---

## Detailed Diagnostics

### herbalist_maren: Vocabulary Analysis

**Walkthrough commands vs Actual vocabulary:**

| Walkthrough Says | Should Say | Actual Config |
|-----------------|------------|---------------|
| `ask maren about silvermoss` | `ask maren about moss` or `ask maren about healing` | `potent healing moss` |
| `ask maren about healing_herbs` | `ask maren about herbs` | `basic medicinal herbs` |
| `ask maren about warm_cloak` | `ask maren about cloak` | `thick wool cloak` |
| `ask maren about teaching` | Need to add keyword | Not in dialog_reactions |

**Why it fails:**
- Dialog system matches keywords, not exact item IDs
- Walkthrough uses item IDs (silvermoss) instead of natural language keywords (moss, healing)
- Teaching scenario not configured in dialog_reactions at all

**Example of what DOES work:**
```
> ask maren about trade
✅ Maren shows you her wares:
  - potent healing moss (50 gold)
  - basic medicinal herbs (30 gold)
  - thick wool cloak (100 gold)
```

### curiosity_dealer_vex: Location & Syntax Issues

**Where walkthrough is:**
```
Line 5: go north     → Frozen Pass
Line 8: go east      → Ice Caves
Line 13: talk to vex about trade   → ❌ Vex not here!
```

**Where it should be:**
```
go south    → Forest Edge
go east     → Southern Trail
go south    → Town Gate
go south    → Market Square
ask vex about trade   → ✅ Vex is here
```

**Path syntax errors:**
```
❌ @set player.properties.gold = 1000
✅ @set actors.player.properties.gold = 1000

❌ @set curiosity_dealer_vex.properties.trust_state.current = 1
✅ @set actors.curiosity_dealer_vex.properties.trust_state.current = 1
```

### gate_guard: Infrastructure Deep Dive

**Current state:**
```json
{
  "id": "gate_guard",
  "behaviors": [],  // ❌ EMPTY ARRAY
  "properties": {
    "dialog_reactions": {
      "warnings": {
        "keywords": ["frozen", "beast", "fungal", "sunken", "danger"],
        "requires_state": ["neutral", "friendly"],
        "summary": "The guard shares warnings..."
      },
      "suspicious_response": {
        "keywords": ["help", "information"],
        "requires_state": ["suspicious"],
        "summary": "The guard eyes you suspiciously."
      }
    }
  }
}
```

**What's configured:** State-gated dialog responses
**What's missing:** Infrastructure to process those responses
**The fix:**
```json
{
  "behaviors": [
    "behaviors.shared.infrastructure.dialog_reactions"  // ← Add this line
  ]
}
```

**After fix, these should work:**
```
> ask guard about frozen reaches
Expected: "The guard shares warnings about the frozen reaches..."

> ask guard about help
Expected (if state=suspicious): "The guard eyes you suspiciously. 'Move along.'"
Expected (if state=neutral): Normal help response
```

---

## Test Coverage Analysis

### What We Can Test Now (After Fixes)
- ✅ herbalist_maren: Trade, pricing, trust (after walkthrough fix)
- ✅ gate_guard: Dialog, state transitions (after infrastructure add)
- ⚠️ curiosity_dealer_vex: Unknown (walkthrough too broken)
- ❌ weaponsmith_toran: Nothing (no infrastructure)
- ❌ councilors: Nothing (requires quest system)

### What We Cannot Test Yet
- Companion filtering (gate_guard scenario mentions but not configured)
- Entry checkpoint mechanics (gate_guard)
- Weapon/armor sales and repairs (weaponsmith_toran)
- Council quest dilemmas (all councilors)
- Un-branding ceremony (councilor_asha)
- Branding ceremony (councilor_hurst)
- Branded player special interactions (councilor_varn)

---

## Time Estimates

### To Reach 100% on Testable NPCs

1. **Fix herbalist_maren walkthrough:** 30 minutes
   - Replace item IDs with keywords
   - Add teaching scenario or mark as not implemented
   - Re-run until 100% success

2. **Add gate_guard infrastructure + new walkthrough:** 2 hours
   - Add infrastructure line to game_state.json
   - Create walkthrough covering all dialog scenarios
   - Test state transitions
   - Verify all keywords work

3. **Fix curiosity_dealer_vex walkthrough:** 1 hour
   - Fix navigation
   - Fix path syntax
   - Fix command syntax
   - Re-run to identify actual NPC issues
   - Fix any real issues found

**Total: ~4 hours to complete basic testing of 3 NPCs**

### To Add weaponsmith_toran

4. **Add service infrastructure:** 1-2 sessions
   - Copy pattern from herbalist_maren services
   - Add dialog_reactions config
   - Create weapon/armor configs
   - Add reputation gating
   - Create comprehensive walkthrough
   - Test all scenarios

### To Add 3 Councilors

5. **Design quest preference system:** 1 session
6. **Implement per councilor:** 1 session each × 3 = 3 sessions
7. **Integration testing:** 1 session

**Total: 5 sessions (councilors only)**

---

## Conclusion

**Current State:** Only 2/7 NPCs have infrastructure, both have broken walkthroughs.

**Quick Win Path:** Fix 2 walkthroughs + add infrastructure to gate_guard = 3/7 NPCs testable in 4 hours.

**Complete Path:** Add weaponsmith_toran + design quest system = all 7 NPCs, estimated 10-12 sessions.

**Recommended:** Start with Option A (Quick Wins) to establish baseline, then discuss whether to continue with councilors or move to different NPC phase.

