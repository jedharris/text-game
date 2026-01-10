# NPC: sailor_garrett

## Core Mechanics
- encounter_reactions: Drowning state when encountered
- condition_reactions: breath_remaining tracking (5 turns)
- commitment: 5-turn deadline (hope does NOT extend)
- rescue_mechanics: Air bladder, cure exhaustion, or physical rescue

## Required Scenarios

### Success Path
1. **Rescue via Air Bladder**
   - Navigate to sea_caves (requires swimming skill)
   - Find Garrett drowning
   - Verify: State is drowning, breath_remaining = 5
   - Give air_bladder
   - Verify: Breath restored, state transitions to stabilized
   - Verify: Still exhausted, needs help swimming out
   - Lead/escort to surface
   - Verify: State transitions to rescued
   - Verify: Gratitude 4
   - Verify: Reveals treasure location
   - Verify: Unlocks advanced swimming (after 5 turn recovery)

2. **Rescue via Cure Exhaustion**
   - Find Garrett drowning
   - Cure exhaustion condition
   - Verify: Can swim but still drowning (needs to reach surface fast)
   - Guide to surface before breath runs out
   - Verify: State transitions to rescued

3. **Rescue via Physical Pull**
   - Have swimming skill OR exceptional strength
   - Pull Garrett to safety directly
   - Verify: Exhausting for player
   - Verify: State transitions to rescued

### Failure Paths
4. **Death by Timer**
   - Enter sea_caves
   - Do not provide rescue
   - Wait 5 turns
   - Verify: Garrett dies (breath_remaining = 0)
   - Verify: broke_promise_garrett flag set (if commitment made)
   - Verify: Jek hostile, advanced swimming unavailable
   - Verify: Mira disappointed, camp morale -1

5. **Death by Health**
   - Fish attack Garrett during rescue attempt
   - Health reaches 0
   - Verify: Same death consequences

### Commitment Scenarios
6. **Commitment Made**
   - Express commitment ("I'll save you")
   - Verify: Commitment recorded
   - Verify: Hope does NOT extend timer (physics doesn't care)
   - Complete rescue
   - Verify: +2 gratitude bonus (total 6)
   - Verify: Treasure location revealed immediately

7. **Commitment Withdrawn**
   - Make commitment
   - Explicitly withdraw
   - Verify: Garrett reveals treasure location anyway
   - Verify: "The cave... east wall... merchant cache... tell Jek..."
   - Verify: garrett_last_words flag set
   - Verify: Cannot recommit (time-critical)
   - Verify: Garrett still dies without rescue

8. **Commitment Abandoned**
   - Make commitment
   - Leave without rescuing
   - Verify: Garrett dies
   - Verify: Echo reaction about broken promise
   - Verify: Jek reaction (hostile)
   - Verify: Mira reaction (trust -2)

### Edge Cases
9. **Advanced Swimming Teaching**
   - Rescue Garrett successfully
   - Wait 5 turns for recovery
   - Verify: Garrett offers advanced swimming lessons
   - Verify: Free (gratitude for saving his life)
   - Verify: advanced_swimming skill granted
   - Verify: 2 turn time cost

10. **Treasure Revelation**
    - Ask about reward/treasure after rescue
    - Verify: Reveals merchant cache location in sea_caves
    - Verify: Becomes knowledge fragment for Archivist quest

## Dependencies
- **Items**:
  - air_bladder (stabilizes drowning)
  - Exhaustion cure (alternative rescue method)
- **NPCs**:
  - old_swimmer_jek (mentor, reaction to Garrett's fate)
  - camp_leader_mira (camp morale)
  - the_archivist (treasure becomes knowledge fragment)
- **Mechanics**:
  - Breath tracking (5 turns)
  - Drowning damage (10 per turn at 0 breath)
  - Commitment system (hope does NOT extend)
  - Skill teaching (advanced swimming)

## Walkthrough Files
- `test_garrett_rescue.txt` (scenarios 1-3) - NEEDS CREATION
- `test_garrett_death.txt` (scenarios 4-5) - NEEDS CREATION

## Implementation Status
- [ ] State machine: drowning→stabilized→rescued / drowning→dead
- [ ] Breath tracking (5 turns)
- [ ] Air bladder rescue path
- [ ] Exhaustion cure rescue path
- [ ] Physical rescue path
- [ ] Commitment system (hope does NOT extend timer)
- [ ] Treasure revelation dialog
- [ ] Advanced swimming teaching (after 5 turn recovery)
- [ ] Death consequences (Jek, Mira, Echo)

## Reference Implementation

This NPC demonstrates:
- **Time-critical rescue**: 5-turn deadline with no hope extension
- **Multiple rescue methods**: Item, cure, or physical
- **Skill unlock**: Advanced swimming via rescued NPC
- **Knowledge fragment source**: Treasure location for Archivist
- **Cascading consequences**: Death affects Jek, Mira, Echo
