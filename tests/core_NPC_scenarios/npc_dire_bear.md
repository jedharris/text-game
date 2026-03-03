# NPC: dire_bear

## Core Mechanics
- encounter_reactions: Immediate hostile attack (no warning, protecting cubs)
- dialog_reactions: Non-verbal communication (posture, gestures, vocalizations)
- condition_reactions: Cubs have wasting_sickness, need healing_herbs
- commitment: 30-turn timer for cubs, +5 hope bonus if committed
- pack_behavior: Cubs (bear_cub_1, bear_cub_2) are dependents, not fighters

## Required Scenarios

### Success Path
1. **Cubs Healed - Full Alliance**
   - Navigate to predators_den
   - Encounter triggers immediate hostile attack
   - Survive/flee initial combat OR make commitment ("I'll heal your cubs")
   - Verify: Bear calms slightly if commitment made
   - Verify: Bear looks toward southern_trail (hint to herb source)
   - Travel to Civilized Remnants, acquire healing_herbs
   - Return to predators_den within 30 turns (+5 if committed)
   - Use healing_herbs on cubs
   - Verify: Cubs' wasting_sickness cured
   - Verify: State transitions hostile→grateful
   - Verify: Trust increases
   - Continue interactions until gratitude >= 3
   - Verify: State transitions grateful→allied
   - Verify: Can rest safely in den
   - Verify: Bear intimidates other predators

### Failure Paths
2. **Cubs Die from Timer Expiration**
   - Encounter dire_bear
   - Do NOT heal cubs within 30 turns
   - Verify: Cubs die from wasting_sickness
   - Verify: State transitions hostile→vengeful
   - Verify: Bear tracks player across Beast Wilds
   - Verify: extra.cubs_died = true
   - Verify: Bear attacks on sight (permanent enemy)
   - Verify: Safe rest in den never available

3. **Cubs Killed by Player**
   - Encounter dire_bear
   - Attack and kill cubs (or kill bear to access cubs)
   - Verify: State becomes vengeful immediately
   - Verify: Same consequences as cubs dying from timer

4. **Commitment Abandoned**
   - Encounter dire_bear
   - Make commitment ("I'll heal your cubs")
   - Verify: Hope bonus applied (+5 turns = 35 total)
   - Let timer expire without healing
   - Verify: broke_promise_bear_cubs flag set
   - Verify: The Echo reacts with sorrow
   - Verify: Hunter Sira (if alive) reacts negatively

### Edge Cases
5. **Commitment Withdrawal**
   - Make commitment to heal cubs
   - Explicitly withdraw commitment
   - Verify: Bear shows cubs' condition again
   - Verify: Bear looks toward southern_trail (reinforces hint)
   - Verify: Can recommit later
   - Verify: No immediate penalty (withdrawing is not abandoning)

6. **Partial Healing Attempt**
   - Encounter dire_bear
   - Give wrong medicine (not healing_herbs)
   - Verify: No effect on cubs
   - Verify: Bear remains hostile/wary
   - Verify: Correct item still needed

7. **Bear Combat Victory**
   - Enter combat with dire_bear
   - Kill dire_bear
   - Verify: Cubs remain (vulnerable without mother)
   - Verify: Cubs can still be healed
   - Verify: But no alliance benefit (mother dead)

## Dependencies
- **Items**:
  - healing_herbs (from Civilized Remnants, healer's garden)
- **NPCs**:
  - bear_cub_1, bear_cub_2 (dependents with wasting_sickness)
  - the_echo (reacts to abandonment)
  - hunter_sira (reacts to abandonment if alive)
- **Mechanics**:
  - Commitment system with timer (30 turns base)
  - Hope bonus extension (+5 turns)
  - Non-verbal communication (body language, hints)
  - Cross-region item dependency

## Walkthrough Files
- `test_dire_bear_healing.txt` (scenario 1) - NEEDS CREATION
- `test_dire_bear_cubs_death.txt` (scenario 2) - NEEDS CREATION
- `test_dire_bear_commitment.txt` (scenarios 4, 5) - NEEDS CREATION

## Implementation Status
- [ ] State machine: hostile→grateful→allied / hostile→vengeful
- [ ] Cubs wasting_sickness condition with 30-turn timer
- [ ] Commitment system with hope bonus
- [ ] Non-verbal hint system (looking toward southern_trail)
- [ ] healing_herbs cures cubs' condition
- [ ] Abandonment consequences (Echo reaction, Sira reaction)
- [ ] Vengeful state tracking across region

## Reference Implementation

This NPC demonstrates:
- **Protective hostility**: Initial aggression has sympathetic reason
- **Cross-region fetch quest**: Solution requires travel to another region
- **Non-verbal hints**: Bear communicates direction to help source
- **Commitment with timer**: Real stakes for promises made
- **Cascading consequences**: Cubs' fate affects multiple NPCs' reactions
- **Pack as dependents**: Cubs follow mother but don't fight
