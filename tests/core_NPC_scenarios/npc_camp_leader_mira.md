# NPC: camp_leader_mira

## Core Mechanics
- dialog_reactions: Quest offer, progress updates, state-based responses
- commitment_reactions: Success (on_quest_complete) and failure (on_quest_failed)
- commitment: 20-turn deadline for dual rescue (Garrett and/or Delvan)
- state_machine: neutral → friendly (1 rescued) → allied (both rescued) OR disappointed (failure)
- trust_state: +2 per rescue on success, -3 on failure
- Dual rescue design: Rescue sailor_garrett and/or merchant_delvan from Sunken District
- Region: Sunken District (survivor_camp location)

## Required Scenarios

### Success Path
1. **Single Rescue Success (Garrett OR Delvan)**
   - Talk to Mira about missing people → quest offered
   - Verify: Commitment "commit_mira_rescue" created
   - Verify: extra.mira_quest_active = true
   - Verify: 20-turn deadline set
   - Navigate to sea_caves (Garrett) OR merchant_warehouse (Delvan)
   - Complete rescue (see npc_sailor_garrett.md or npc_merchant_delvan.md)
   - Verify: extra.garrett_rescued = true OR extra.delvan_rescued = true
   - Return to Mira at survivor_camp
   - Verify: extra.mira_quest_completed = true
   - Verify: mira.state_machine.current = friendly
   - Verify: mira.trust_state.current = +2
   - Verify: Success feedback mentions rescued person

2. **Dual Rescue Success (Both Garrett AND Delvan)**
   - Accept quest from Mira
   - Rescue both Garrett and Delvan within deadline
   - Verify: extra.garrett_rescued = true AND extra.delvan_rescued = true
   - Return to Mira
   - Verify: mira.state_machine.current = allied
   - Verify: mira.trust_state.current = +4 (both rescues)
   - Verify: extra.camp_services_unlocked = true
   - Verify: Success feedback "You did it. You actually did it."

### Failure Paths
2. **Quest Expiration - Time Runs Out**
   - Accept quest from Mira
   - Wait 20+ turns without completing
   - Verify: Commitment transitions to ABANDONED
   - Verify: on_quest_failed handler fires
   - Verify: extra.mira_quest_failed = true
   - Verify: mira.state_machine.current = disappointed
   - Verify: mira.trust_state.current = -3
   - Verify: Failure feedback about survivors not making it

3. **Quest Declined**
   - Talk to Mira about quest
   - Never accept or ignore quest
   - Verify: No commitment created
   - Verify: Mira remains neutral
   - Verify: Can ask about quest again later

### Edge Cases
4. **Quest Progress Inquiry**
   - Accept quest
   - After 5 turns, ask Mira about progress/status
   - Verify: Shows remaining turns (15 left)
   - After 15 turns, ask again
   - Verify: Shows urgency (5 turns left)

5. **Post-Failure Dialog**
   - Complete scenario 2 (quest failed)
   - Try to request another quest
   - Verify: Mira refuses "won't make that mistake again"
   - Verify: State remains disappointed
   - Verify: Services locked

6. **Post-Success Services**
   - Complete scenario 1 (quest success)
   - Verify camp services available
   - Verify Mira's dialog reflects allied status
   - Verify can't get quest again (already completed)

### Camp Services (Post-Success)
7. **Camp Services Unlocked**
   - Complete dual rescue (both Garrett and Delvan)
   - Verify: extra.camp_services_unlocked = true
   - Available services:
     - Safe rest (full heal)
     - Information about Sunken District locations
     - Swimming lessons referral to Jek
   - Verify: Mira dialog mentions available help

8. **Camp Morale**
   - Rescue Garrett: +1 camp morale
   - Rescue Delvan: +1 camp morale
   - Let either die: -1 camp morale
   - Verify: Morale affects camp dialog and atmosphere
   - Verify: Low morale may affect service availability

### Cross-NPC Interactions
9. **Jek Connection**
   - Ask Mira about swimming
   - Verify: Mira refers player to old_swimmer_jek
   - Verify: "Jek can teach you. He's the best swimmer in camp."

10. **Garrett Recovery at Camp**
    - Rescue Garrett
    - Wait 5 turns at camp
    - Verify: Garrett recovered enough to teach advanced swimming
    - Verify: Mira acknowledges Garrett's recovery

## Dependencies
- **Items**:
  - air_bladder (for Garrett rescue - breathing underwater)
  - bandages or healing items (for Delvan rescue - stop bleeding)
  - lever (for Delvan rescue - free from cargo)
- **NPCs**:
  - sailor_garrett (rescue target, see npc_sailor_garrett.md)
  - merchant_delvan (rescue target, see npc_merchant_delvan.md)
  - Both NPCs have their own rescue mechanics and timers
- **Mechanics**:
  - dialog_reactions infrastructure
  - commitment_reactions infrastructure (BOTH success and failure handlers)
  - Commitment system with ACTIVE→ABANDONED→COMPLETED states
  - State machine transitions
  - **GAP**: Missing commitment_reactions.completed config in game_state.json
  - **GAP**: Rescue completion trigger (how does Mira know rescues succeeded?)

## Walkthrough Files
- `test_mira_commitment.txt` (scenario 2) - ✅ EXISTS, PASSING (failure path)
- `test_camp_leader_mira.txt` - ✅ EXISTS, PASSING (quest dialog, progress tracking)
- `test_mira_single_rescue.txt` (scenario 1) - NEEDS CREATION (Garrett OR Delvan success trigger)
- `test_mira_dual_rescue.txt` (scenario 2) - NEEDS CREATION (both rescues - ideal outcome)
- `test_mira_post_success.txt` (scenario 6) - COULD ADD (post-success services)

**Note:** Delvan rescue verified working (Issue #437). Success path implementation depends on automatic vs manual trigger design.

## Implementation Status
- [x] Quest offer dialog (mira.py:109-175)
- [x] Quest progress dialog (mira.py:178-215)
- [x] Success handler exists (mira.py:218-265)
- [x] Failure handler exists + tested (mira.py:268-312)
- [x] State transitions on success/failure
- [x] Trust changes on success/failure
- [x] Garrett rescue mechanics (dual_rescue.py - Sunken District)
- [x] Delvan rescue mechanics (dual_rescue.py - Sunken District - VERIFIED Issue #437)
- [x] Failure path tested (commitment abandonment)
- [ ] commitment_reactions.COMPLETED config (needs success trigger design decision)
- [ ] Success walkthrough (blocked on trigger implementation)
- [ ] Camp services implementation (safe rest, information)
- [ ] Camp morale system
- [ ] Jek referral dialog
- [ ] Garrett recovery tracking

## Reference Implementation

**See:** [npc_reaction_system_guide.md](../../docs/Guides/npc_reaction_system_guide.md#camp-leader-mira-commitment-reactions) for config examples and flow diagrams.

This NPC demonstrates:
- **commitment_reactions**: Handlers for COMPLETED and ABANDONED state transitions
- **dialog_reactions**: Quest progress tracking, deadline reporting
- **Multi-objective quests**: Rescue Delvan AND/OR Garrett
- **Quest completion**: commitment_reactions fires when commitment state changes
