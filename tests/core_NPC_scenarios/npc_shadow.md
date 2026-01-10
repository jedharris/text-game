# NPC: shadow

## Core Mechanics
- location: undercity (requires discovery)
- services: Assassination contracts (any named NPC)
- darkest_option: Massive irreversible consequences
- discovery_chance: 20% per contract

## Required Scenarios

### Contract Path
1. **Accept Assassination Contract**
   - Navigate to undercity
   - Talk to shadow
   - Request assassination of named NPC
   - Pay 100-500g (based on target importance)
   - Verify: 3-turn delay before completion
   - Verify: Irreversible once paid
   - Verify: Target dies after 3 turns
   - Verify: 20% discovery chance

### Consequence Paths
2. **Discovery Consequences**
   - Contract assassination
   - 20% chance discovered
   - If discovered:
   - Verify: Immediate public branding (-5 reputation)
   - Verify: Un-branding PERMANENTLY blocked
   - Verify: Target's faction becomes hostile
   - Verify: Echo confronts player directly
   - Verify: Good endings permanently locked

3. **Undiscovered Consequences**
   - Contract assassination
   - Discovery roll fails (80%)
   - Verify: Echo still knows
   - Verify: Echo comments on the killing
   - Verify: Echo trust -2 (cumulative per assassination)
   - Verify: "has_killed" flag set
   - Verify: Triumphant ending blocked
   - Verify: Some NPCs sense "wrongness"

### Target Examples
4. **Councilor Assassination**
   - Contract assassination on councilor
   - Verify: Price 400-500g
   - Verify: Town destabilizes if discovered
   - Verify: Remaining councilors fearful

5. **Major NPC Assassination**
   - Contract assassination on Elara, Maren, etc.
   - Verify: Permanent loss of their services
   - Verify: Cross-region consequences (Elara = no advanced herbalism ever)

### Edge Cases
6. **Warning Given**
   - Before accepting contract
   - Verify: Shadow warns "this cannot be undone"
   - Verify: Player confirmation required
   - Verify: Clear irreversibility communicated

7. **Branded Player More Welcome**
   - Player is branded
   - Talk to Shadow
   - Verify: Shadow more willing to discuss
   - Verify: "Player already marked"
   - Verify: No price change

8. **Multiple Assassinations**
   - Contract multiple assassinations
   - Verify: Each has independent 20% discovery
   - Verify: Echo trust penalty cumulative (-2 per)
   - Verify: Discovery of ANY blocks un-branding

9. **Attempt to Cancel**
   - Pay for assassination
   - Try to cancel
   - Verify: Cannot cancel once paid
   - Verify: "The deed is already in motion"

## Dependencies
- **NPCs**:
  - Any named NPC (potential targets)
  - the_echo (knows about assassinations)
  - councilor_asha (un-branding blocked if discovered)
- **Mechanics**:
  - 3-turn delay system
  - 20% discovery chance
  - Permanent flag settings
  - Echo trust penalty
  - Ending restrictions

## Walkthrough Files
- `test_shadow_assassination.txt` - NEEDS CREATION (test with non-essential NPC)

## Implementation Status
- [ ] Assassination contract system
- [ ] 100-500g pricing by target
- [ ] 3-turn delay to completion
- [ ] 20% discovery chance
- [ ] Discovered: immediate branding, un-branding permanently blocked
- [ ] Undiscovered: Echo knows, Echo trust -2, has_killed flag
- [ ] Target faction hostility
- [ ] Ending restrictions

## Reference Implementation

This NPC demonstrates:
- **Darkest option**: Available but never encouraged
- **Permanent consequences**: Cannot be undone
- **Multiple consequence layers**: Discovery vs undiscovered both bad
- **Echo omniscience**: Even hidden evil is known
- **Ending restrictions**: Murder blocks best outcomes
- **Player warning**: Clear communication of irreversibility
