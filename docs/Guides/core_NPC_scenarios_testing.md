# Core NPC Scenarios Testing Guide

## Purpose

This guide defines how to create and use **NPC scenario documents** - comprehensive specifications that ensure every NPC's core gameplay mechanics are fully validated before completion.

Without complete scenario coverage, we cannot verify the game is fully playable. These documents serve as:
1. **Design validation checklist** - ensures all mechanics are designed
2. **Implementation guide** - documents what code must exist
3. **Testing specification** - defines required walkthroughs
4. **Completion criteria** - establishes when an NPC is "done"

## Document Structure

Each NPC gets a scenario document in `tests/core_NPC_scenarios/` following this template:

```markdown
# NPC: <npc_id>

## Core Mechanics
- List all reaction types used (encounter_reactions, death_reactions, etc.)
- List key systems (commitments, state machines, trust, gossip)
- Note any special mechanics unique to this NPC

## Required Scenarios

### Success Path
<Primary positive outcome - what happens when player succeeds>

1. **<Scenario Name>**
   - Step 1: Action
   - Step 2: Action
   - Verify: Expected outcomes, state changes, feedback

### Failure Paths
<All ways the player can fail or trigger negative outcomes>

2. **<Failure Scenario Name>**
   - Steps...
   - Verify: Consequences

3. **<Another Failure Scenario>**
   - Steps...
   - Verify: Different consequences

### Edge Cases
<Boundary conditions, partial completion, timing variations>

4. **<Edge Case Name>**
   - Steps...
   - Verify: Edge behavior

## Dependencies
- **Items**: List required items (bandages, flowers, etc.)
- **NPCs**: List connected NPCs (gossip targets, quest givers)
- **Mechanics**: List infrastructure dependencies

## Walkthrough Files
- `test_<npc>_<scenario>.txt` - maps each scenario to walkthrough file
- Note which files exist vs need creation

## Implementation Status
- [ ] All mechanics implemented
- [ ] All dependencies present
- [ ] All walkthroughs created
- [ ] All walkthroughs passing
```

## Key Principles

### 1. Completeness Over Brevity
Document EVERY core scenario, not just the "happy path". Include:
- Success path (primary positive outcome)
- All failure paths (different ways to fail)
- Edge cases (partial completion, timing, interactions)

### 2. Actionable Steps
Each scenario must have:
- Clear step-by-step player actions
- Expected game state changes
- Verifiable outcomes (assertions)

### 3. Dependency Tracking
Explicitly list:
- Required items (must exist in game_state.json)
- Related NPCs (for gossip, quests, etc.)
- Infrastructure (reaction types, systems)

### 4. Implementation Mapping
For each scenario, document:
- Which handlers implement it
- Which walkthrough tests it
- Current status (implemented/tested/passing)

## Example: hunter_sira

```markdown
# NPC: hunter_sira

## Core Mechanics
- encounter_reactions: First encounter starts 8-turn timer
- death_reactions: Creates gossip to healer_elara on death
- condition_reactions: Tracks bleeding + leg_injury healing
- commitment: 8-turn deadline, hope_applied, target_actor tracking

## Required Scenarios

### Success Path
1. **Encounter + Quick Rescue**
   - Find Sira at injured_hunter location
   - Commitment "commit_sira_rescue" created automatically
   - Apply bandages to stop bleeding
   - Apply healing/splint to fix leg_injury
   - Verify: Both conditions removed, Sira grateful feedback
   - Verify: Commitment transitions to COMPLETED
   - Verify: No gossip created

### Failure Paths
2. **Death by Timer Expiration**
   - Find Sira → commitment starts
   - Wait 8+ turns without helping
   - Verify: Commitment transitions to ABANDONED
   - Verify: Sira dies (death_reactions triggered)
   - Verify: Gossip "gossip_sira_death" created → healer_elara
   - Verify: extra.sira_died_with_player = true

3. **Death by Condition**
   - Find Sira → commitment starts
   - Conditions worsen naturally over time
   - Verify: Sira dies before deadline
   - Verify: Same gossip/consequence as timer expiration

### Edge Cases
4. **Partial Healing - Bleeding Only**
   - Stop bleeding but don't heal leg
   - Verify: Sira survives but commitment incomplete
   - Verify: Appropriate feedback about partial help

5. **Partial Healing - Leg Only**
   - Heal leg without stopping bleeding
   - Verify: Bleeding still active
   - Verify: Feedback indicates bleeding must be stopped first

6. **Confession Before Gossip**
   - Sira dies (scenario 2 or 3)
   - Talk to Elara with confession keywords before gossip arrives
   - Verify: extra.player_confessed_sira = true
   - Verify: When gossip arrives, trust penalty is -1 (not -2)

## Dependencies
- **Items**: bandages, healing_salve (or similar healing items)
- **NPCs**: healer_elara (gossip target, confession recipient)
- **Mechanics**:
  - condition_reactions infrastructure
  - gossip_delivery infrastructure
  - commitment system with ACTIVE→ABANDONED→COMPLETED states

## Walkthrough Files
- `test_sira_rescue_success.txt` (scenario 1) - NEEDS CREATION
- `test_hunter_sira.txt` (scenario 2) - EXISTS, PASSING
- `test_sira_partial_bleeding.txt` (scenario 4) - NEEDS CREATION
- `test_sira_confession.txt` (scenario 6) - NEEDS CREATION

## Implementation Status
- [x] Encounter creates commitment (sira_rescue.py:28-77)
- [x] Death creates gossip (sira_rescue.py:80-123)
- [x] Healing tracked (sira_rescue.py:126-178)
- [ ] Condition removal triggers success (needs verification)
- [ ] Commitment completion handler (may need implementation)
- [ ] Success walkthrough created
- [ ] Edge case walkthroughs created
```

## Workflow Integration

### Phase 0: Scenario Definition
1. Create scenario document for each NPC
2. Research existing code to determine implementation status
3. Identify gaps (missing mechanics, missing tests)
4. Post summary to issue

### Implementation Phases (1-N)
1. Review NPC's scenario document
2. Implement missing mechanics
3. Create walkthroughs for all scenarios
4. Run walkthroughs until 100% success
5. Check off items in "Implementation Status"
6. NPC phase complete when ALL scenarios verified

### Completion Criteria
An NPC is complete when:
- [ ] Scenario document exists
- [ ] All scenarios have implementation
- [ ] All scenarios have walkthroughs
- [ ] All walkthroughs pass 100%
- [ ] All checkboxes in document marked

## Template NPCs

The 5 template NPCs provide reaction type coverage:
- **hunter_sira**: encounter_reactions, death_reactions, condition_reactions, commitments
- **bee_queen**: gift_reactions, take_reactions, state_machine, trust
- **camp_leader_mira**: dialog_reactions, commitment_reactions (success/failure)
- **healer_elara**: gossip_reactions, confession mechanics, trust-gated services
- **merchant_delvan**: dual rescue mechanics, impossible choice design

Together these cover all core reaction infrastructure.

## Common Pitfalls

### 1. Incomplete Scenario Coverage
❌ Only documenting success path
✅ Document all failure paths and edge cases

### 2. Vague Verification
❌ "Verify: Quest completes"
✅ "Verify: extra.mira_quest_completed = true, mira.state_machine.current = 'allied', trust = +2"

### 3. Missing Dependencies
❌ Scenario assumes items exist without listing them
✅ Dependencies section lists all required items/NPCs/mechanics

### 4. No Implementation Mapping
❌ Scenario described but no link to code
✅ Reference handler functions, config locations, file:line numbers

### 5. Claiming Completion Without Walkthroughs
❌ "Code looks right, probably works"
✅ "All scenarios tested with passing walkthroughs"

### 6. Testing Happy Path Without Verifying Infrastructure
❌ "Walkthrough passes, ship it!"
✅ "Walkthrough passes AND underlying infrastructure is complete"

**Problem:** Config can look perfect and match architecture spec, but fail if infrastructure is incomplete.

**Example from Issue #437 (hunter_sira healing):**
```json
// This config looks perfect and matches the architecture doc
{
  "item_use_reactions": {
    "stop_bleeding": {
      "accepted_items": ["bandages"],
      "remove_condition": "bleeding",  // Effect exists in spec!
      "response": "The bleeding stops."
    }
  },
  "condition_reactions": {
    "bleeding": {
      "handler": "path:to:on_sira_healed"  // Handler exists!
    }
  }
}
```

**Reality:** Test shows "Nothing special happens" because:
1. `remove_condition` effect used wrong property name (`active_conditions` vs `conditions`)
2. Effect didn't fire `entity_condition_change` hook
3. `condition_reactions` handler never got notified

**Verification Checklist:**
```bash
# 1. Check effect implementation matches NPCs
grep -n "remove_condition" behaviors/shared/infrastructure/reaction_effects.py
grep -r "\"conditions\"" examples/big_game/game_state.json  # What NPCs actually use

# 2. Verify effect fires required hooks
# In reaction_effects.py, check if _remove_condition calls invoke_behavior()

# 3. Trace complete chain
# Command → Hook → Infrastructure → Effect → Hook → Handler
# Verify each step exists and connects to next
```

**Fix:** Don't assume architecture is complete. Verify infrastructure before blaming config.

### 7. Assuming Architecture Spec Matches Implementation
❌ "Architecture doc says this works, so my config is correct"
✅ "Let me verify the infrastructure actually implements what the spec describes"

**Root Cause:** Architecture documents describe *intended* design, not always *current* implementation.

**Symptoms:**
- Config perfectly matches spec examples
- No obvious typos or path errors
- Still doesn't work

**Debugging Approach:**
1. **Verify property names:** Do effects use same property names as NPCs?
   ```bash
   # Find what NPCs use
   grep -r "\"conditions\"" game_state.json
   # Find what effect uses
   grep "properties.get" reaction_effects.py
   # Do they match?
   ```

2. **Verify hook firing:** Is hook defined but never invoked?
   ```bash
   # Find hook definition
   grep "hook_id.*entity_condition_change" behaviors/
   # Find hook invocations
   grep "invoke_behavior.*entity_condition_change" behaviors/ examples/
   # Second search should return results!
   ```

3. **Trace complete flow:** Follow data through all 7 layers
   ```
   1. Command fires hook
   2. Engine checks target.behaviors
   3. Infrastructure subscribes to hook
   4. Handler processes properties config
   5. Unified interpreter applies effect
   6. Effect fires notification hook
   7. Downstream handler receives notification
   ```

   If ANY layer is missing, data-driven pattern breaks.

**Solution:** Fix infrastructure gaps, document them, update architecture spec if needed.

## Usage for New NPCs

When implementing a new NPC:

1. **Start with scenario document** - write scenarios BEFORE coding
2. **Review with stakeholder** - ensure complete coverage
3. **Use as implementation guide** - build to satisfy scenarios
4. **Create walkthroughs incrementally** - test as you implement
5. **Update status checkboxes** - track progress
6. **Verify 100% before claiming done** - no partial credit

## Maintenance

Scenario documents are **living specifications**:
- Update when mechanics change
- Add scenarios when edge cases discovered
- Keep walkthrough mappings current
- Mark checkboxes as work completes

They serve as **regression test specs** - if a scenario document says something should work, it must continue working.
