# NPC: the_echo

## Core Mechanics
- encounter_reactions: Appears intermittently based on trust and chance
- dialog_reactions: Provides guidance, tracks commitments, reveals backstory
- trust_system: -5 to +10 scale, affects appearance rate and dialog depth
- transformation: Becomes corporeal when waystone is repaired
- omniscience: Knows all commitments and assassinations through ley lines

## Required Scenarios

### Trust System
1. **Positive Trust Gains**
   - Restore crystal (+1)
   - Heal major NPC (Aldric, Spore Mother) (+1)
   - Save any survivor (+0.5)
   - Fulfill commitment (+0.5)
   - Repair waystone (+2)
   - Verify: Trust increases appropriately

2. **Negative Trust Losses**
   - Kill friendly NPC (-2)
   - Abandon commitment (-1)
   - Assassination contract (-2, Echo always knows)
   - Verify: Trust decreases appropriately

3. **Trust Effects on Appearance**
   - Trust 5+: Echo speaks player's name
   - Trust 3-4: Echo warm, shares freely
   - Trust 1-2: Echo helpful, clearer form
   - Trust -2 to 0: Echo distant, brief
   - Trust -3 or below: Echo refuses to appear
   - Verify: Appearance rate and depth match trust level

### Dialog Topics
4. **Disaster Information**
   - Ask about disaster/meridian/shattered
   - Verify: "Five ley lines converged. Something went wrong."
   - Verify: knows_disaster_cause flag set
   - Verify: Unlocks regions, restoration topics

5. **Waystone Information**
   - Ask about waystone (requires knows_disaster_cause)
   - Verify: Lists five fragments needed
   - Verify: knows_waystone_repair flag set

6. **Commitment Tracking**
   - Ask about promises/commitments
   - Verify: Echo recites all commitments with status
   - Verify: Approving of kept words, sorrowful about broken

7. **Progress Summary**
   - Ask about progress/journey
   - Verify: Echo comments on regions visited, NPCs helped/harmed
   - Verify: Tone varies by trust level

### Commitment Awareness
8. **Commitment Made**
   - Make commitment in any region
   - Return to Nexus
   - Verify: Echo acknowledges: "A promise made. The meridian remembers."

9. **Commitment Fulfilled**
   - Fulfill commitment
   - Return to Nexus
   - Verify: Echo brightens: "A word kept. The threads of trust strengthen."
   - Verify: +0.5 trust

10. **Commitment Abandoned**
    - Abandon commitment (timer expires, NPC dies)
    - Return to Nexus
    - Verify: Echo dims: "A word broken. The fractures spread."
    - Verify: -1 trust

### Assassination Awareness
11. **Assassination Knowledge**
    - Contract assassination (even undiscovered)
    - Return to Nexus
    - Verify: Echo knows regardless of NPC discovery
    - Verify: -2 trust applied
    - Verify: Trust recovery limited (triumphant ending locked)

### Transformation
12. **Waystone Repair**
    - Gather all five fragments
    - Place each in waystone
    - Verify: Each fragment lights socket with appropriate color
    - Verify: Echo transformation begins
    - Verify: Echo becomes solid, permanent, able to act
    - Verify: "I can exist now. Truly. Because of you."

### Trust Recovery
13. **Recovery from Negative Trust**
    - Trust at -2
    - Save major NPC or restore crystal
    - Verify: Trust +1
    - Verify: Max recovery +1 per Nexus visit

14. **Recovery from Refusing State**
    - Trust at -3 (Echo refuses to appear)
    - Perform major healing act
    - Verify: Echo appears briefly
    - Verify: Can begin trust recovery

### Ending Tiers
15. **Triumphant Ending (Trust 5+)**
    - All crystals restored, waystone repaired
    - Verify: "You did more than repair the meridian. You healed it."
    - Verify: Echo offers to be permanent companion

16. **Successful Ending (Trust 3+)**
    - Waystone repaired
    - Verify: Echo grateful but relationship functional
    - Verify: "You have my gratitude."

17. **Hollow Victory (Trust -2)**
    - Waystone repaired
    - Verify: Echo transforms but refuses to speak further
    - Verify: "There is nothing more to say between us."

18. **Pyrrhic Ending (Trust -3)**
    - Waystone repaired
    - Verify: Echo does not participate in ceremony
    - Verify: Player places fragments alone
    - Verify: Echo watches from shadows but will not manifest

### Edge Cases
19. **Backstory Revelation (Trust 6+)**
    - Build trust to 6+
    - Verify: Echo reveals was training to be next Keeper
    - Verify: Full backstory about disaster

20. **Appearance Outside Nexus**
    - Critical moment in other region (NPC dying, irreversible choice)
    - Verify: Echo may appear briefly
    - Verify: Cryptic guidance only
    - Verify: Rare occurrence

21. **Multiple Assassinations**
    - Contract 3+ assassinations
    - Verify: Echo refuses to manifest permanently
    - Verify: Pyrrhic ending is best possible

## Dependencies
- **Items**:
  - Waystone fragments (5 total from all regions)
  - keepers_journal (backstory source)
- **NPCs**:
  - All major NPCs (commitment tracking)
- **Locations**:
  - keepers_quarters (primary location)
  - nexus_chamber (waystone location)
  - crystal_garden (crystal tracking)
- **Mechanics**:
  - Trust system (-5 to +10)
  - Appearance mechanics (chance-based with trust modifier)
  - Commitment tracking across all regions
  - Assassination awareness (ley line omniscience)
  - Ending tier system

## Walkthrough Files
- `test_echo_trust.txt` - NEEDS CREATION
- `test_echo_transformation.txt` - NEEDS CREATION
- `test_echo_endings.txt` - NEEDS CREATION

## Implementation Status
- [ ] Trust system (-5 to +10)
- [ ] Appearance mechanics (base chance + trust modifier)
- [ ] Dialog topics (disaster, waystone, commitments, progress)
- [ ] Commitment awareness across all regions
- [ ] Assassination omniscience (always knows)
- [ ] Transformation on waystone repair
- [ ] Ending tier system (triumphant→pyrrhic)
- [ ] Trust recovery mechanics
- [ ] Backstory revelation at high trust
- [ ] Rare outside-Nexus appearances

## Reference Implementation

This NPC demonstrates:
- **Central moral mirror**: Tracks all player actions through ley lines
- **Trust-gated content**: Appearance rate, dialog depth, backstory
- **Transformation mechanic**: Spectral→corporeal on waystone repair
- **Multiple endings**: Trust level determines ending quality
- **Omniscient awareness**: Always knows about assassinations
- **Recovery possible**: Even dark paths can partially recover
- **Sanctuary guide**: Provides information and guidance
