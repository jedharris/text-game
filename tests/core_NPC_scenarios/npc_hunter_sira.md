# NPC: hunter_sira

## Core Mechanics
- encounter_reactions: First encounter starts 8-turn timer automatically
- death_reactions: Creates gossip to healer_elara on death
- condition_reactions: Tracks bleeding + leg_injury healing progress
- commitment: 8-turn deadline, hope_applied, target_actor tracking
- Two-step healing: Must stop bleeding AND heal leg injury

## Required Scenarios

### Success Path
1. **Encounter + Quick Rescue**
   - Navigate to hunter_sira location (injured_hunter in Beast Wilds)
   - Encounter triggers automatically
   - Verify: Commitment "commit_sira_rescue" created
   - Verify: extra.sira_commitment_created = true
   - Verify: extra.sira_first_encounter_turn = current_turn
   - Apply bandages to Sira (use bandages on sira / give bandages to sira)
   - Verify: Bleeding stopped
   - Verify: extra.sira_bleeding_stopped = true
   - Verify: Feedback "bleeding stops"
   - Apply healing/splint to fix leg_injury
   - Verify: Leg healed
   - Verify: extra.sira_leg_healed = true
   - Verify: extra.sira_healed = true (full recovery)
   - Verify: Gratitude feedback "saved my life"
   - Verify: No gossip created (success prevents gossip)

### Failure Paths
2. **Death by Timer Expiration**
   - Encounter Sira → commitment starts
   - Wait 8+ turns without helping
   - Verify: Commitment transitions to ABANDONED
   - Verify: Sira dies (death_reactions triggered)
   - Verify: Gossip "gossip_sira_death" created → healer_elara
   - Verify: gossip delay_turns = 12, confession_window = 12
   - Verify: extra.sira_died_with_player = true
   - Verify: Death feedback "struggle has ended"

3. **Death by Bleeding (Conditions Worsen)**
   - Encounter Sira
   - Conditions progress naturally over time
   - Sira dies before deadline (if condition mechanics support this)
   - Verify: Same gossip/consequences as scenario 2

### Edge Cases
4. **Partial Healing - Bleeding Stopped Only**
   - Encounter Sira
   - Stop bleeding with bandages
   - Do NOT heal leg injury
   - Verify: extra.sira_bleeding_stopped = true
   - Verify: extra.sira_leg_healed = false
   - Verify: Sira survives but commitment may remain incomplete
   - Verify: Feedback indicates partial help

5. **Partial Healing - Leg First (Wrong Order)**
   - Encounter Sira
   - Try to heal leg BEFORE stopping bleeding
   - Verify: May fail or give feedback about bleeding needing treatment first
   - Verify: Leg splinted but bleeding still active
   - Then stop bleeding
   - Verify: Now both conditions clear
   - Verify: extra.sira_healed = true

6. **Confession to Elara Before Gossip**
   - Complete scenario 2 (Sira dies)
   - Within 12 turns, talk to healer_elara with confession keywords
   - Verify: extra.player_confessed_sira = true
   - Verify: Elara applies -1 trust penalty immediately
   - When gossip arrives (turn 12+), check handler
   - Verify: Gossip handler sees confession flag
   - Verify: Trust penalty is -1 total (not additional -2)
   - Verify: Elara's feedback reflects confession "told me yourself"

7. **Gossip Arrives First (No Confession)**
   - Complete scenario 2 (Sira dies)
   - Do NOT confess to Elara
   - Wait 12+ turns for gossip to arrive
   - Verify: Gossip delivered to healer_elara
   - Verify: extra.player_confessed_sira = false or not set
   - Verify: Trust penalty is -2 (full penalty)
   - Verify: Elara's feedback shows anger "didn't tell me"

## Dependencies
- **Items**:
  - bandages (stops bleeding condition)
  - healing_salve or similar (heals leg_injury condition)
  - Items must be configured to remove conditions via condition_reactions
- **NPCs**:
  - healer_elara (gossip target, confession recipient)
- **Mechanics**:
  - encounter_reactions infrastructure (auto-triggers on first encounter)
  - condition_reactions infrastructure (healing mechanics)
  - gossip_delivery infrastructure (delayed message to Elara)
  - commitment system with ACTIVE→ABANDONED states
  - Confession mechanics in services.py

## Walkthrough Files
- `test_sira_death.txt` (scenarios 2, 7) - ✅ EXISTS, PASSING (death + gossip)
- `test_sira_rescue.txt` (scenario 1) - ✅ EXISTS, PASSING (success path)
- `test_sira_rescue_success.txt` (scenario 1) - ✅ EXISTS, PASSING (alternate success)
- `test_sira_partial_bleeding.txt` (scenario 4) - NEEDS CREATION (partial healing edge case)
- `test_sira_healing_order.txt` (scenario 5) - NEEDS CREATION (wrong order edge case)

## Implementation Status
- [x] Encounter creates commitment (sira_rescue.py:28-77)
- [x] Death creates gossip (sira_rescue.py:80-123)
- [x] Healing handler tracks progress (sira_rescue.py:126-178)
- [x] Two-step healing: bleeding + leg (separate conditions)
- [x] Confession handler in services.py (services.py:126-175)
- [x] Gossip handler checks confession flag (services.py:98-103)
- [x] Condition removal triggers healing handler correctly (Issue #437 - VERIFIED)
- [x] item_use_reactions → remove_condition → entity_condition_change → condition_reactions flow working
- [x] Success walkthrough created and passing (test_sira_rescue.txt)
- [x] Death + gossip walkthrough passing (test_sira_death.txt)
- [ ] Partial healing walkthroughs (edge cases not critical for template)

## Reference Implementation

**See:** [npc_reaction_system_guide.md](../../docs/Guides/npc_reaction_system_guide.md#hunter-sira-two-phase-reaction-chains) for detailed config examples and flow diagrams.

This NPC demonstrates:
- **Two-phase reaction chains**: item_use → effect → downstream hook → handler
- **Auto-triggering commitments**: encounter_reactions creates deadline without player action
- **Gossip with confession**: death_reactions creates delayed gossip, confession mitigates penalty
- **Multi-step healing**: Two separate conditions must be cleared for full rescue
