# NPC: councilor_varn

## Core Mechanics
- dialog_reactions: Political discussion, commerce perspective
- quest_preferences: Favors trade, wealth, pragmatic commerce
- council_quests: Co-presents dilemmas with other councilors

## Required Scenarios

### Success Paths (Varn-Favorable)
1. **Dangerous Traders - Trade at Distance**
   - Accept dangerous_traders dilemma
   - Choose "trade at distance" option
   - Verify: Varn +2 approval
   - Verify: "Good business" feedback

2. **Test and Admit Traders**
   - Accept dangerous_traders dilemma
   - Choose "test and admit"
   - Verify: Varn +1 approval (trade opportunity)

3. **Compromise Path (Labor + Support)**
   - Accept criminal_punishment dilemma
   - Choose "labor_support" option
   - Verify: Varn +1 approval

### Failure Paths (Varn-Unfavorable)
4. **Turn Away Traders**
   - Accept dangerous_traders dilemma
   - Choose "exile" option
   - Verify: Varn -1 disapproval
   - Verify: "Lost opportunity" feedback

5. **Criminal Punishment - Mercy**
   - Choose pure mercy without labor
   - Verify: Varn -1 disapproval
   - Verify: "Unproductive" feedback

### Edge Cases
6. **Varn Approaches Branded Player**
   - Player is branded
   - Verify: Varn may approach for deniable tasks
   - Verify: "Your coin spends the same. But I'd keep that hand in your pocket."

7. **Quarantine Quest Reaction**
   - Accept quarantine path
   - Success: Varn +1 (practical solution)
   - Failure: Varn -1 (waste of resources)

8. **Commerce Philosophy**
   - Ask about values
   - Verify: "Prosperity through commerce" philosophy
   - Verify: Sees trade as solution to town's problems

9. **Council Vote on Town Seal**
    - Guardian repaired (especially while branded)
    - Verify: Varn votes yes ("Good business")
    - Verify: Pragmatic support regardless of player's status

## Dependencies
- **NPCs**:
  - councilor_hurst (sometimes aligned)
  - councilor_asha (often opposed)
- **Mechanics**:
  - Council quest system

## Walkthrough Files
- `test_varn_commerce_choices.txt` - NEEDS CREATION

## Implementation Status
- [ ] Dialog_reactions for commerce perspective
- [ ] Quest preference system (trade-focused)
- [ ] Branded player interaction (approaches for tasks)
- [ ] Council vote behavior

## Reference Implementation

This NPC demonstrates:
- **Moral complexity**: Commerce focus, pragmatic values
- **Pragmatic voting**: Supports practical outcomes regardless of player status
