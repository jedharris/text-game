# NPC: merchant_delvan

## Core Mechanics
- encounter_reactions: First encounter creates rescue commitment
- death_reactions: Creates gossip on death to echo and healer_elara
- condition_reactions: Bleeding condition, rescue via condition removal
- commitment: 10-turn deadline for rescue
- Dual rescue design: Competing urgent rescues (Delvan vs Garrett)
- Impossible choice: Can't save both in time

## Required Scenarios

### Success Path
1. **Delvan Rescue Success**
   - Navigate to merchant_delvan location (Sunken District)
   - Encounter triggers automatically
   - Verify: Commitment "commit_delvan_rescue" created
   - Verify: extra.delvan_commitment_created = true
   - Verify: extra.delvan_encounter_turn = current_turn
   - Verify: Encounter feedback "pinned beneath debris", "blood seeping", "SOS"
   - Apply treatment to stop bleeding
   - Verify: Condition "bleeding" removed
   - Verify: on_rescue_success handler fires
   - Verify: extra.delvan_rescued = true
   - Verify: Success feedback "stop Delvan's bleeding", "You came"
   - Verify: Commitment transitions to COMPLETED
   - Verify: No death gossip created

### Failure Paths
2. **Death by Timer Expiration**
   - Encounter Delvan → commitment starts
   - Wait 10+ turns without treating
   - Verify: Commitment transitions to ABANDONED
   - Verify: Delvan dies (death_reactions triggered)
   - Verify: on_npc_death handler fires
   - Verify: extra.delvan_died = true
   - Verify: Gossip "gossip_delvan_death" created
   - Verify: Gossip targets: echo, healer_elara
   - Verify: Gossip delay_turns = 15
   - Verify: Death feedback "tapping stops", "too late"

3. **Choose Garrett Over Delvan (Impossible Choice)**
   - Encounter both Delvan and Garrett (sailor_garrett)
   - Verify: Both commitments created
   - Choose to rescue Garrett first
   - Complete Garrett rescue
   - Verify: Delvan's timer continues
   - Delvan dies due to timer expiration
   - Verify: Delvan death gossip created
   - Verify: extra.delvan_died = true, extra.garrett_rescued = true
   - Verify: Guilt/choice feedback in narrative

4. **Choose Delvan Over Garrett**
   - Encounter both NPCs
   - Choose to rescue Delvan first
   - Complete Delvan rescue (scenario 1)
   - Garrett dies due to timer
   - Verify: extra.delvan_rescued = true, extra.garrett_died = true
   - Verify: Garrett death gossip created
   - Verify: Consequences reflect the choice made

### Edge Cases
5. **Encounter Delvan Without Resources**
   - Encounter Delvan
   - Have no bandages or healing items
   - Verify: Commitment still created (timer pressure exists)
   - Verify: Must find treatment elsewhere or fail

6. **Rescue After Partial Timer**
   - Encounter Delvan
   - Wait 5 turns (half the deadline)
   - Then rescue
   - Verify: Success still possible
   - Verify: Narrative reflects urgency

7. **Post-Rescue Interaction**
   - Complete scenario 1 (Delvan rescued)
   - Talk to Delvan afterward
   - Verify: Gratitude dialog
   - Verify: Potential services unlocked (if designed)

### Post-Rescue Services
8. **Black Market Contacts (Knowledge Fragment)**
   - Rescue Delvan
   - Ask about "contacts" or "network"
   - Verify: delvan_contacts knowledge fragment obtained
   - Verify: Can be given to the_archivist for knowledge quest
   - Verify: Alternative fragment source (vs requiring other NPCs)

9. **Trade Services**
    - Rescue Delvan
    - Wait for recovery (returns to camp or Civilized Remnants)
    - Verify: Trade services available
    - Verify: Better prices than normal merchants (gratitude discount)
    - Verify: Access to unusual/rare items

## Dependencies
- **Items**:
  - bandages or healing items (to stop bleeding)
  - Items must trigger condition removal via condition_reactions
- **NPCs**:
  - sailor_garrett (dual rescue mechanic, competing commitment)
  - echo (gossip target for ending calculations)
  - healer_elara (gossip target)
  - the_archivist (delvan_contacts as knowledge fragment)
- **Mechanics**:
  - encounter_reactions infrastructure
  - condition_reactions infrastructure (bleeding removal)
  - death_reactions infrastructure
  - gossip_delivery infrastructure
  - commitment system with competing deadlines
  - Dual rescue design (impossible choice)

## Walkthrough Files
- `test_merchant_delvan.txt` (scenario 2) - ✅ EXISTS, PASSING (death path)
- `test_delvan_rescue_success.txt` (scenario 1) - ✅ EXISTS, PASSING (success + Mira quest integration)
- `test_delvan_infection.txt` - ✅ EXISTS, PASSING (infection mechanic)
- `test_delvan_garrett_choice.txt` (scenarios 3-4) - ✅ EXISTS, PASSING (impossible choice: save Delvan, Garrett dies)
- `test_delvan_partial_timer.txt` (scenario 6) - COULD ADD (timing edge case, not critical)

## Implementation Status
- [x] Encounter creates commitment (dual_rescue.py:29-74)
- [x] Death creates gossip (dual_rescue.py:169-229)
- [x] Rescue success handler exists (dual_rescue.py:125-166)
- [x] Bleeding condition removal tracked
- [x] Garrett parallel mechanics (dual rescue)
- [x] Death walkthrough exists and passing
- [x] Condition removal triggers rescue success correctly (Issue #437 - VERIFIED)
- [x] Commitment completion on rescue (extra.delvan_rescued flag set)
- [x] Success walkthrough created and passing (with Mira quest integration)
- [x] Dual rescue walkthrough (impossible choice: save Delvan, Garrett dies)
- [ ] delvan_contacts knowledge fragment
- [ ] Post-rescue trade services

## Reference Implementation

**See:** [npc_reaction_system_guide.md](../../docs/Guides/npc_reaction_system_guide.md#merchant-delvan-encounter--condition-reactions) for config examples.

This NPC demonstrates:
- **Auto-triggering commitments**: encounter_reactions on first look at location
- **Single-step rescue**: One condition removal completes rescue
- **Dual rescue impossible choice**: Delvan vs Garrett timing conflict (designed trap)
