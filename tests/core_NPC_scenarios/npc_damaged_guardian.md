# NPC: damaged_guardian

## Core Mechanics
- encounter_reactions: Silent, flickering runes when approached
- repair_quest: Multi-step fetch quest (no timer)
- state_machine: non_functional→partially_awakened→functional→active
- speech: Short directive phrases once awakened

## Required Scenarios

### Success Path
1. **Full Repair**
   - Navigate to broken_statue_hall
   - Observe damaged_guardian
   - Verify: State is non_functional
   - Verify: Runes flicker weakly
   - Obtain animator_crystal (from Nexus Crystal Garden)
   - Apply animator_crystal
   - Verify: State transitions to partially_awakened
   - Use stone_chisel (found in hall) for repairs
   - Verify: State transitions to functional
   - Learn ritual (from Frozen Reaches OR Echo)
   - Designate purpose
   - Verify: State transitions to active
   - Verify: "TO GUARD IS TO SERVE. AWAITING DESIGNATION."
   - Verify: +3 reputation
   - Verify: Town Seal available

2. **Town Seal Award**
   - Complete full repair
   - Verify: Council awards Town Seal
   - Verify: Guardian provides town defense
   - Verify: Can be used for waystone repair

### Commitment Path
3. **Repair Commitment**
   - Express commitment ("I'll repair the guardian")
   - Verify: No timer (Guardian doesn't die)
   - Verify: Commitment recorded
   - Verify: Guardian inscription: "To protect is to endure. To endure is to wait."

4. **Withdrawal Response**
   - Make commitment
   - Explicitly withdraw
   - Verify: No penalty
   - Verify: Can recommit any time
   - Verify: Guardian runes flicker but no disappointment expressed

### Special: Branded Player Repair
5. **Asha Mercy Mechanism**
   - Player is branded
   - Complete Guardian repair despite brand
   - Verify: Asha conflicted
   - Verify: Town Seal awarded despite brand
   - Verify: "I don't understand you. I don't forgive you. But I cannot deny what you've done."

6. **Redemption Through Repair**
   - Player is branded
   - Complete Guardian repair (heroic act)
   - Verify: Counts toward un-branding requirements
   - If reputation also +3:
   - Verify: Un-branding ceremony available

### Edge Cases
7. **Partial Repair States**
   - Apply animator_crystal only
   - Verify: State is partially_awakened
   - Verify: Runes glow but Guardian doesn't move
   - Leave and return
   - Verify: State persists

8. **Stone Chisel Already Present**
   - Navigate to broken_statue_hall
   - Verify: stone_chisel available in location
   - Verify: Can take without prerequisite

9. **Repair Order Flexibility**
   - Try applying chisel before crystal
   - Verify: Physical repairs possible but no awakening
   - Then apply crystal
   - Verify: Both effects combine for functional state

## Dependencies
- **Items**:
  - animator_crystal (from Nexus Crystal Garden)
  - stone_chisel (found in broken_statue_hall)
  - ritual_knowledge (from Frozen Reaches OR Echo)
- **NPCs**:
  - councilor_asha (Town Seal award, mercy mechanism)
  - the_echo (optional ritual source)
- **Mechanics**:
  - Multi-step repair quest
  - Commitment without timer
  - Town Seal waystone fragment

## Walkthrough Files
- `test_guardian_repair.txt` - NEEDS CREATION
- `test_guardian_branded_repair.txt` - NEEDS CREATION

## Implementation Status
- [ ] State machine: non_functional→partially_awakened→functional→active
- [ ] animator_crystal placement effect
- [ ] stone_chisel repair effect
- [ ] Ritual designation phase
- [ ] Short phrase speech pattern
- [ ] +3 reputation on completion
- [ ] Town Seal award
- [ ] Back tunnel access for branded players
- [ ] Asha mercy mechanism

## Reference Implementation

This NPC demonstrates:
- **Multi-step repair quest**: Cross-region item collection
- **No timer pressure**: Player-paced completion
- **Commitment without stakes**: No death if abandoned
- **Branded redemption path**: Heroic act despite social punishment
- **Construct speech pattern**: Short directive phrases
