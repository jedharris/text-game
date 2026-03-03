# NPC: councilor_hurst

## Core Mechanics
- dialog_reactions: Political discussion, quest presentation
- quest_preferences: Favors pragmatic, security-focused choices
- backstory: Family killed by beasts (explains harshness)
- council_quests: Co-presents dilemmas with other councilors

## Required Scenarios

### Success Paths (Hurst-Favorable)
1. **Infected Refugees - Turn Away**
   - Accept infected_refugees dilemma
   - Choose "turn away" option
   - Verify: Hurst +2 approval
   - Verify: "Practical decision" feedback

2. **Dangerous Traders - Exile**
   - Accept dangerous_traders dilemma
   - Choose "exile after investigation"
   - Verify: Hurst +2 approval

3. **Criminal Punishment - Harsh**
   - Accept criminal_punishment dilemma
   - Choose "harsh" option (flogging, stocks)
   - Verify: Hurst +2 approval
   - Verify: "Deterrence" feedback

4. **Compromise Path (Labor + Support)**
   - Accept criminal_punishment dilemma
   - Discover "labor_support" option through dialog
   - Choose compromise
   - Verify: Hurst +1 approval (all councilors satisfied)

### Failure Paths (Hurst-Unfavorable)
5. **Infected Refugees - Treat**
   - Choose "treat" option
   - Verify: Hurst -2 disapproval
   - Verify: "Waste of resources" feedback

6. **Criminal Punishment - Mercy**
   - Choose "mercy" option
   - Verify: Hurst -2 disapproval
   - Verify: "Encourages others" feedback

7. **Quarantine Quest Failure**
   - Accept quarantine path for refugees
   - Fail to return with cure within 30 turns
   - Verify: Hurst blames player (-2)
   - Verify: Will not support player in future quests

### Edge Cases
8. **Test and Admit - Infected Found**
   - Choose "test and admit" for traders
   - 20% chance: One infected discovered
   - Verify: Hurst -2 ("I warned you")
   - Verify: Player must handle infected trader

9. **Branding Ceremony**
   - Player reaches reputation -5
   - Verify: Hurst reads crimes aloud
   - Verify: Hurst participates in branding

10. **Beast Backstory**
    - Ask about family
    - Verify: Reveals family killed by beasts
    - Verify: Explains his harsh stance
    - Verify: May soften slightly if player helped tame beasts peacefully

## Dependencies
- **NPCs**:
  - councilor_asha (opposing philosophy)
  - councilor_varn (commerce focus)
- **Mechanics**:
  - Council quest system
  - Councilor approval tracking
  - Branding ceremony

## Walkthrough Files
- `test_council_dilemmas.txt` - NEEDS CREATION
- `test_hurst_approval.txt` - NEEDS CREATION

## Implementation Status
- [ ] Dialog_reactions for quest presentation
- [ ] Quest preference system
- [ ] Approval tracking per choice
- [ ] Backstory dialog (family killed by beasts)
- [ ] Branding ceremony participation

## Reference Implementation

This NPC demonstrates:
- **Moral complexity**: Pragmatic philosophy with sympathetic backstory
- **Quest preference system**: Different reactions to same choices
- **Councilor dynamics**: Conflict with Asha, alignment with some Varn choices
- **Backstory motivation**: Tragedy explains harshness
