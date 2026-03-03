# NPC: old_swimmer_jek

## Core Mechanics
- dialog_reactions: Swimming lessons, Garrett connection
- services: Teach basic swimming (5g or food)
- skill_progression: Basic swimming → Advanced swimming (via Garrett)
- garrett_connection: Garrett was Jek's apprentice

## Required Scenarios

### Success Paths
1. **Learn Basic Swimming (Payment)**
   - Navigate to survivor_camp
   - Talk to old_swimmer_jek
   - Pay 5 gold OR provide food item
   - Verify: basic_swimming skill granted
   - Verify: Breath extends to 15
   - Verify: Normal swim speed
   - Verify: 1 turn time cost

2. **Learn Basic Swimming (Favor)**
   - Talk to Jek about favor
   - Verify: Agrees to teach for free if Garrett rescued
   - Rescue Garrett
   - Return to Jek
   - Verify: Basic swimming granted for free

3. **Advanced Swimming Path**
   - Rescue Garrett
   - Wait 5 turns for Garrett to recover
   - Verify: Garrett (not Jek) teaches advanced swimming
   - Verify: "Jek is too old for advanced techniques"
   - Verify: advanced_swimming skill granted
   - Verify: Breath extends to 20
   - Verify: Can avoid fish attacks
   - Verify: 2 turn time cost

### Failure Paths
4. **Garrett Dies - Jek's Reaction**
   - Let Garrett die
   - Return to Jek
   - Verify: Jek turns away
   - Verify: "You were there? You SPOKE to him? And you... left?"
   - Verify: Advanced swimming lessons unavailable permanently
   - Verify: Basic lessons still available for payment

5. **Garrett Dies After Commitment**
   - Make commitment to save Garrett
   - Fail to save him
   - Verify: Jek more hostile
   - Verify: "You said you would save him"

### Edge Cases
6. **Dialog About Swimming**
   - Ask about swimming
   - Verify: "The water isn't your enemy, it's your element"
   - Verify: Unlocks "price" and "favor" dialog topics

7. **Legendary Webbed Fingers**
   - Ask about Jek's appearance
   - Verify: Birth defect made him famous swimmer
   - Verify: Explains his teaching ability despite age

## Dependencies
- **Items**:
  - 5 gold (payment option)
  - Food item (alternative payment)
- **NPCs**:
  - sailor_garrett (apprentice, advanced swimming teacher)
- **Mechanics**:
  - Skill teaching system
  - Two-tier swimming progression
  - Garrett recovery timer (5 turns)

## Walkthrough Files
- `test_jek_swimming_lessons.txt` - NEEDS CREATION

## Implementation Status
- [ ] Basic swimming teaching (5g or food)
- [ ] Favor system (free if Garrett rescued)
- [ ] Garrett death reaction
- [ ] Advanced swimming via Garrett (not Jek)
- [ ] Recovery timer for Garrett (5 turns)

## Reference Implementation

This NPC demonstrates:
- **Skill teacher**: Basic swimming for payment or favor
- **Two-tier progression**: Basic (Jek) → Advanced (Garrett)
- **NPC connection**: Mentorship relationship with Garrett
- **Consequence-aware**: Different treatment based on Garrett's fate
