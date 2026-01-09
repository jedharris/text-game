# NPC: camp_leader_mira

## Core Mechanics
- dialog_reactions: Quest offer, progress updates, state-based responses
- commitment_reactions: Success (on_quest_complete) and failure (on_quest_failed)
- commitment: 20-turn deadline for survivor rescue
- state_machine: neutral → friendly/allied (success) OR disappointed (failure)
- trust_state: +2 on success, -3 on failure

## Required Scenarios

### Success Path
1. **Survivor Rescue Success**
   - Talk to Mira with quest keyword → quest offered
   - Verify: Commitment "commit_mira_rescue" created
   - Verify: extra.mira_quest_active = true
   - Verify: 20-turn deadline set
   - Navigate to storage district / survivor location
   - Perform rescue action (trigger on_quest_complete)
   - Return to Mira or trigger completion
   - Verify: extra.mira_quest_completed = true
   - Verify: mira.state_machine.current = allied
   - Verify: mira.trust_state.current = +2
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

## Dependencies
- **Items**:
  - Items needed for rescue (depends on implementation)
  - May need fungal clearing items, healing supplies, etc.
- **NPCs**:
  - Survivors (may be NPCs or abstract goal)
  - Possibly related to storage district / fungal growth area
- **Mechanics**:
  - dialog_reactions infrastructure
  - commitment_reactions infrastructure
  - Commitment system with ACTIVE→ABANDONED→COMPLETED states
  - State machine transitions
  - **MISSING**: Rescue trigger mechanism (how player completes quest)

## Walkthrough Files
- `test_mira_commitment.txt` (scenario 2) - EXISTS, PASSING (failure path)
- `test_mira_rescue_success.txt` (scenario 1) - NEEDS CREATION (success path)
- `test_mira_quest_progress.txt` (scenario 4) - NEEDS CREATION (progress tracking)
- `test_mira_post_failure.txt` (scenario 5) - COULD ADD (post-failure state)
- `test_mira_post_success.txt` (scenario 6) - COULD ADD (post-success services)

## Implementation Status
- [x] Quest offer dialog (mira.py:109-175)
- [x] Quest progress dialog (mira.py:178-215)
- [x] Success handler exists (mira.py:218-265)
- [x] Failure handler exists + tested (mira.py:268-312)
- [x] State transitions on success/failure
- [x] Trust changes on success/failure
- [ ] **CRITICAL GAP**: Rescue trigger implementation (HOW does player complete rescue?)
- [ ] **CRITICAL GAP**: Survivor NPCs or rescue location mechanics
- [ ] Success walkthrough created
- [ ] Success path verified end-to-end
