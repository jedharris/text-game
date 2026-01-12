# Phase 1 NPC Testing Report - Civilized Remnants
**Date:** 2026-01-10
**Tester:** Claude
**Scope:** Test 8 Civilized Remnants NPCs per npc_upgrade_plan.md Phase 3.1

## Summary

| NPC | Walkthrough Exists | Infrastructure | Status | Priority |
|-----|-------------------|---------------|--------|----------|
| herbalist_maren | ✓ | ✓ | PARTIAL - Walkthrough outdated | HIGH |
| curiosity_dealer_vex | ✓ | ✓ | PARTIAL - Walkthrough broken | MEDIUM |
| gate_guard | ✗ | ✗ | NOT TESTABLE - No infrastructure | HIGH |
| weaponsmith_toran | ✗ | ✗ | NOT TESTABLE - No infrastructure | HIGH |
| councilor_asha | ✗ | ✗ | NOT TESTABLE - No infrastructure | MEDIUM |
| councilor_hurst | ✗ | ✗ | NOT TESTABLE - No infrastructure | MEDIUM |
| councilor_varn | ✗ | ✗ | NOT TESTABLE - No infrastructure | MEDIUM |
| militia_captain_hurst | N/A | N/A | NOT FOUND - May be same as councilor_hurst | N/A |

---

## Detailed Findings

### 1. herbalist_maren

**Configuration Status:**
- ✅ behaviors: `["behaviors.regions.civilized_remnants.services", "behaviors.shared.infrastructure.dialog_reactions"]`
- ✅ properties: `dialog_reactions`, `services`, `trust_state`

**Walkthrough: test_herbalist_maren.txt**
- **Result:** 9/14 commands succeeded, 5 unexpected failures, 10 assertion failures
- **Root Cause:** Vocabulary mismatch between walkthrough and actual item names

**Specific Issues:**
1. **Item name mismatch:**
   - Walkthrough asks about: `silvermoss`, `warm_cloak`, `healing_herbs`
   - Actual items in config: `potent healing moss`, `thick wool cloak`, `basic medicinal herbs`
   - Result: "doesn't seem interested in discussing that"

2. **Missing keywords:**
   - `ask maren about silvermoss` → fails (should be "moss" or "healing")
   - `ask maren about teaching` → fails (keyword not in dialog_reactions)

3. **Transaction mechanics:**
   - Trade display WORKS: Shows wares with prices
   - Trust-based discount WORKS: 30% discount at trust=3
   - Item purchase FAILS: Can't complete transactions due to keyword mismatch

**What Works:**
- ✅ Navigation to market_square
- ✅ Display of trade inventory with prices
- ✅ Trust-based pricing adjustments
- ✅ Dialog infrastructure fires correctly

**What Fails:**
- ❌ Specific item purchases (keyword mismatch)
- ❌ Teaching mechanics (keyword not configured)
- ❌ Transaction completion (item name vocabulary)

**Required Fixes:**
1. Revise walkthrough to use correct item keywords from vocabulary
2. Add "teaching" keywords to dialog_reactions
3. Verify item vocabulary matches config item IDs
4. Test transaction completion flow

---

### 2. curiosity_dealer_vex

**Configuration Status:**
- ✅ behaviors: `["behaviors.regions.civilized_remnants.vex"]`
- ✅ properties: `dialog_reactions`, `gift_reactions`, `services`, `state_machine`, `trust_state`

**Walkthrough: test_curiosity_dealer_vex.txt**
- **Result:** 4/16 commands succeeded, 12 parse errors, 15 assertion failures
- **Root Cause:** Multiple fundamental issues

**Specific Issues:**
1. **Location error:**
   - Walkthrough tries to talk to Vex from Ice Field
   - Vex is located in market_square
   - Result: Parse errors (NPC not present)

2. **Path syntax errors:**
   - Uses: `@set player.properties.gold = 1000`
   - Correct: `@set actors.player.properties.gold = 1000`
   - Uses: `@set curiosity_dealer_vex.properties...`
   - Correct: `@set actors.curiosity_dealer_vex.properties...`

3. **Command syntax:**
   - Uses: `talk to vex about trade`
   - Likely should be: `ask vex about trade` (matching dialog command pattern)

**Required Fixes:**
1. Navigate to market_square before attempting dialog
2. Fix all @set and @assert paths to use `actors.` prefix
3. Verify command syntax (talk vs ask)
4. Re-run to identify actual dialog/service issues

**Cannot evaluate actual NPC functionality until walkthrough is fixed.**

---

### 3. gate_guard

**Configuration Status:**
- ❌ behaviors: `[]` (EMPTY - missing infrastructure)
- ⚠️ properties: Has `dialog_reactions` config but no infrastructure to use it

**Property Configuration:**
```json
{
  "state_machine": {
    "states": ["suspicious", "neutral", "friendly"],
    "initial": "suspicious"
  },
  "dialog_reactions": {
    "warnings": {
      "keywords": ["frozen", "beast", "fungal", "sunken", "danger", "warn", "advice"],
      "requires_state": ["neutral", "friendly"],
      "summary": "The guard shares warnings about the dangerous regions..."
    },
    "suspicious_response": {
      "keywords": ["help", "information", "tell", "ask"],
      "requires_state": ["suspicious"],
      "summary": "The guard eyes you suspiciously. 'Move along.'"
    },
    "default_response": "The guard watches the horizon, alert."
  }
}
```

**Diagnosis:**
- Config exists for dialog_reactions with state-gated responses
- NO infrastructure module in behaviors array
- **Missing:** `behaviors.shared.infrastructure.dialog_reactions`

**What Cannot Be Tested:**
- Dialog responses (no infrastructure to process dialog_reactions)
- State transitions (suspicious → neutral → friendly)
- Companion filtering (mentioned in scenario doc but not in config)
- Entry checkpoint mechanics (not configured)

**Required Before Testing:**
1. Add `behaviors.shared.infrastructure.dialog_reactions` to behaviors array
2. Verify state_machine infrastructure exists
3. Add encounter_reactions config for entry checkpoint
4. Create walkthrough testing all scenarios from npc_gate_guard.md

**Scenario Coverage Needed:**
- Normal entry
- Friendly entry (high reputation)
- Infected player denied
- Wolf companion denied
- Myconid companion denied
- Salamander companion hesitant
- Bribe acceptance

---

### 4. weaponsmith_toran

**Configuration Status:**
- ❌ behaviors: `[]` (EMPTY - missing infrastructure)
- ⚠️ properties: Has `services` property but no infrastructure to use it

**Property Configuration:**
```json
{
  "services": [
    "sell_weapons",
    "sell_armor",
    "repair_weapons"
  ]
}
```

**Diagnosis:**
- Services listed but no service handler module
- NO dialog_reactions property
- **Missing:** Service infrastructure module (likely `behaviors.regions.civilized_remnants.services`)

**What Cannot Be Tested:**
- Weapon/armor sales
- Weapon repair service
- Reputation-based service refusal (rep < -3)
- Price quotes for repairs

**Required Before Testing:**
1. Add service infrastructure module to behaviors
2. Add dialog_reactions property for service conversations
3. Add service configs similar to herbalist_maren pattern
4. Create walkthrough for all scenarios from npc_weaponsmith_toran.md

**Scenario Coverage Needed:**
- Purchase weapons (sword, silver_sword, dagger, crossbow)
- Purchase armor (leather_armor, chain_shirt)
- Repair weapon (with damage assessment)
- Service denied at reputation -3
- Salamander companion interest

---

### 5. councilor_asha

**Configuration Status:**
- ❌ behaviors: `[]` (EMPTY)
- ⚠️ properties: Philosophy, trust, can_perform_unbranding only

**Property Configuration:**
```json
{
  "philosophy": "idealist",
  "trust": {
    "current": 0,
    "floor": -3,
    "ceiling": 5
  },
  "can_perform_unbranding": true
}
```

**Diagnosis:**
- Placeholder NPC with trust tracking but no mechanics
- NO dialog_reactions, quest_preferences, or un_branding_role config
- Scenario doc describes complex quest system not yet implemented

**What Cannot Be Tested:**
- Council quest dilemmas
- Ethical choice preferences
- Un-branding ceremony
- Branded player interactions
- Dialog responses

**Required Before Testing:**
1. Design and implement council quest system infrastructure
2. Add dialog_reactions for political discussions
3. Add quest_preferences config for ethical choices
4. Implement un-branding ceremony mechanics
5. Create walkthrough for scenarios from npc_councilor_asha.md

**Scenario Coverage Needed:**
- Infected refugees dilemma (treat vs turn away)
- Criminal punishment dilemma (mercy vs harsh)
- Dangerous traders dilemma (test/admit vs exile)
- Un-branding ceremony (triggered by reputation + heroic act)
- Branded player interactions

**Note:** This NPC requires NEW infrastructure (quest preference system) per npc_upgrade_plan.md Phase 2.1

---

### 6. councilor_hurst

**Configuration Status:**
- ❌ behaviors: `[]` (EMPTY)
- ⚠️ properties: Philosophy and trust only

**Property Configuration:**
```json
{
  "philosophy": "pragmatist",
  "trust": {
    "current": 0,
    "floor": -3,
    "ceiling": 5
  }
}
```

**Diagnosis:**
- Same as councilor_asha - placeholder with no mechanics
- Shares quest system with Asha (opposing philosophy)
- Scenario doc describes backstory (family killed by beasts) not in config

**Required Before Testing:**
1. Same infrastructure as councilor_asha (quest preference system)
2. Add backstory property or dialog for family tragedy
3. Add branding ceremony participation config
4. Create walkthrough for scenarios from npc_councilor_hurst.md

**Scenario Coverage Needed:**
- Same dilemmas as Asha but opposite preferences
- Beast backstory reveal dialog
- Branding ceremony participation
- Compromise path discovery (labor_support)

---

### 7. councilor_varn

**Configuration Status:**
- ❌ behaviors: `[]` (EMPTY)
- ⚠️ properties: Philosophy and trust only

**Property Configuration:**
```json
{
  "philosophy": "commerce",
  "trust": {
    "current": 0,
    "floor": -3,
    "ceiling": 5
  }
}
```

**Diagnosis:**
- Same as other councilors - placeholder only
- Commerce-focused philosophy distinct from Asha/Hurst
- May approach branded player for "deniable tasks" (not configured)

**Required Before Testing:**
1. Same infrastructure as other councilors
2. Add dialog_reactions for commerce philosophy
3. Add branded player approach mechanics
4. Create walkthrough for scenarios from npc_councilor_varn.md

**Scenario Coverage Needed:**
- Trader dilemmas (favors trade at distance)
- Commerce philosophy dialog
- Branded player approach for tasks
- Council vote on Town Seal

---

## Infrastructure Gaps Summary

### Missing Infrastructure Modules

1. **gate_guard:**
   - Missing: `behaviors.shared.infrastructure.dialog_reactions`
   - Has config for: dialog_reactions (with state gates)

2. **weaponsmith_toran:**
   - Missing: Service handler module (e.g., `behaviors.regions.civilized_remnants.services`)
   - Missing: dialog_reactions property and infrastructure

3. **All 3 Councilors (asha, hurst, varn):**
   - Missing: Quest preference system (NEW infrastructure needed per upgrade plan)
   - Missing: dialog_reactions infrastructure
   - Missing: Un-branding ceremony mechanics (Asha only)
   - Missing: Branding ceremony mechanics (Hurst)

### Walkthrough Issues

1. **herbalist_maren:**
   - Walkthrough exists but uses wrong vocabulary
   - Needs revision to match actual item keywords
   - Infrastructure works correctly

2. **curiosity_dealer_vex:**
   - Walkthrough has fundamental errors (location, path syntax, commands)
   - Cannot evaluate NPC functionality until walkthrough is fixed
   - Infrastructure appears present but untested

---

## Recommendations

### Immediate Actions (High Priority)

1. **Fix herbalist_maren walkthrough:**
   - Update item keywords to match vocabulary
   - Add teaching scenarios
   - Re-run to verify all scenarios pass

2. **Fix curiosity_dealer_vex walkthrough:**
   - Navigate to market_square first
   - Fix path syntax (@set actors.X not just X)
   - Verify command syntax
   - Re-run to identify real NPC issues

3. **Add infrastructure to gate_guard:**
   - Add `behaviors.shared.infrastructure.dialog_reactions`
   - Create walkthrough for entry checkpoint scenarios
   - Test state transitions

4. **Add infrastructure to weaponsmith_toran:**
   - Add service handler module (reference herbalist_maren pattern)
   - Add dialog_reactions property
   - Create walkthrough for all service scenarios

### Medium Priority

5. **Design quest preference system:**
   - Required for all 3 councilors
   - Document in separate design doc before implementing
   - Consider: mutual exclusivity, approval tracking, dilemma presentation

6. **Create walkthroughs for councilors:**
   - After quest system designed
   - Cover all dilemma scenarios from scenario docs
   - Test opposing preferences (Asha vs Hurst)

---

## Testing Blockers

**Cannot proceed with systematic testing until:**

1. Infrastructure modules added to NPCs with empty behaviors arrays
2. Existing walkthroughs revised to fix vocabulary/syntax issues
3. Quest preference system designed and implemented for councilors

**Estimated Work:**
- Fix 2 walkthroughs: 1 session
- Add infrastructure to gate_guard + test: 1 session
- Add infrastructure to weaponsmith_toran + test: 1 session
- Design quest preference system: 1 session
- Implement councilor mechanics + test: 3 sessions (1 per councilor)
- **Total: ~7 sessions to complete Phase 1 testing**

---

## Next Steps

Per user instructions "DO NOT modify code or game_state.json", this report documents findings only.

To proceed, user should decide:
1. Fix walkthroughs first (herbalist_maren, curiosity_dealer_vex)?
2. Add infrastructure to gate_guard and weaponsmith_toran?
3. Proceed with councilor quest system design?
4. Focus on different NPCs from Phase 3?

