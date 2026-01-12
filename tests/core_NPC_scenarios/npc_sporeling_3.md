# NPC: npc_sporeling_3

## Core Mechanics
- pack_behavior: Follower of npc_spore_mother
- state_mirroring: Mirrors Mother's state
- range_limit: Bound to spore_heart
- personality: Younger (smaller, follows siblings)
- health: 20 HP (lower than siblings' 30 HP)

## Required Scenarios

### State Mirroring
1. **Follow Mother's State**
   - Same as other sporelings
   - Verify: State changes with Mother

2. **Younger Behavior**
   - When hostile: Follows siblings, less threatening
   - When wary: Hides behind siblings
   - When allied: Most curious, may approach player
   - Verify: Different behavior from older siblings

3. **Lower Health**
   - Combat encounter
   - Verify: 20 HP instead of 30 HP
   - Verify: Easier to kill but same consequences

### Death Scenarios
4. **Same as Other Sporelings**
   - Kill sets has_killed_fungi flag
   - Myconid trust penalty applies
   - Mother death → confused state

5. **Most Vulnerable**
   - If player attacks sporelings
   - sporeling_3 most likely to die first
   - Verify: Same consequences as killing any sporeling

## Dependencies
- Same as sporeling_1

## Walkthrough Files
- Covered by `test_spore_mother_*.txt` scenarios

## Implementation Status
- [ ] Same core mechanics as sporeling_1
- [ ] Younger personality variant
- [ ] Lower health (20 HP)
- [ ] "Smaller, follows siblings" description

## Reference Implementation

This NPC demonstrates:
- **Personality variant**: Younger, smaller, follows siblings
- **Stat variation**: Lower health than siblings
- **Same core mechanics**: State mirroring, range limit, spore network
