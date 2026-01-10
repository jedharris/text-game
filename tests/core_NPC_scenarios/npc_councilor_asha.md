# NPC: councilor_asha

## Core Mechanics
- dialog_reactions: Political discussion, ethical perspective
- quest_preferences: Favors ethical, merciful choices
- un_branding_role: Initiates redemption ceremony
- council_quests: Co-presents dilemmas with other councilors

## Required Scenarios

### Success Paths (Asha-Favorable)
1. **Infected Refugees - Treat**
   - Accept infected_refugees dilemma
   - Choose "treat" option
   - Verify: Asha +2 approval
   - Verify: "Compassion" feedback

2. **Criminal Punishment - Mercy**
   - Accept criminal_punishment dilemma
   - Choose "mercy" option
   - Verify: Asha +2 approval
   - Verify: "Justice must be tempered" feedback

3. **Test and Admit Traders**
   - Accept dangerous_traders dilemma
   - Choose "test and admit"
   - Verify: Asha +2 approval (if clean)
   - Verify: Asha +1 approval even if infected found

4. **Quarantine Quest Success**
   - Accept quarantine path
   - Return with cure within 30 turns
   - Verify: Asha +2 approval
   - Verify: "You saved them all" feedback

### Failure Paths (Asha-Unfavorable)
5. **Infected Refugees - Turn Away**
   - Choose "turn away" option
   - Verify: Asha -3 disapproval (strongest negative)
   - Verify: "They will die because of you"
   - Verify: Asha refuses to speak to player

6. **Criminal Punishment - Harsh**
   - Choose "harsh" option
   - Verify: Asha -2 disapproval
   - Verify: Silent, conflicted reaction

### Special Role: Un-Branding Ceremony
7. **Un-Branding Initiation**
   - Player is branded
   - Player reaches reputation +3
   - Player completes heroic act (guardian repair, major rescue)
   - Verify: Asha initiates un-branding ceremony
   - Verify: Ceremony transforms brand into redemption mark
   - Verify: "The mark cannot be erased, but its meaning can change"

8. **Un-Branding Blocked (Assassination)**
   - Player contracted assassination
   - Even if reputation +3 and heroic act
   - Verify: Asha will NOT perform un-branding
   - Verify: "Some things cannot be redeemed"

### Edge Cases
9. **Branded Player Interaction**
   - Player is branded
   - Talk to Asha
   - Verify: Silent, conflicted look
   - Verify: Won't speak unless addressed directly

10. **Guardian Repair While Branded (Asha Mercy Mechanism)**
    - Player is branded
    - Player repairs Guardian
    - Verify: Asha conflicted but awards Town Seal
    - Verify: "I don't understand you. I don't forgive you. But I cannot deny what you've done."

11. **Compromise Discovery**
    - Accept criminal_punishment dilemma
    - Explore dialog options
    - Verify: Can discover "labor_support" option
    - Verify: Asha +1 (satisfies everyone)

## Dependencies
- **NPCs**:
  - councilor_hurst (opposing philosophy)
  - councilor_varn (commerce focus)
- **Mechanics**:
  - Council quest system
  - Branding/un-branding system
  - Redemption tracking

## Walkthrough Files
- `test_asha_ethical_choices.txt` - NEEDS CREATION
- `test_unbranding_ceremony.txt` - NEEDS CREATION

## Implementation Status
- [ ] Dialog_reactions for ethical perspective
- [ ] Quest preference system (ethical choices)
- [ ] Un-branding ceremony role
- [ ] Branded player reaction (silent, conflicted)
- [ ] Asha mercy mechanism for Guardian repair

## Reference Implementation

This NPC demonstrates:
- **Moral complexity**: Idealism that can be dangerous
- **Redemption system**: Central role in un-branding ceremony
- **Strong reactions**: Refuses to speak after worst choices
- **Mercy mechanism**: Can't deny heroic acts even from branded players
