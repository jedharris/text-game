# NPC: npc_sporeling_2

## Core Mechanics
- pack_behavior: Follower of npc_spore_mother
- state_mirroring: Mirrors Mother's state
- range_limit: Bound to spore_heart
- personality: Cautious (hangs back, observes)

## Required Scenarios

### State Mirroring
1. **Follow Mother's State**
   - Same as sporeling_1
   - Verify: State changes with Mother

2. **Cautious Behavior**
   - When hostile: Hangs back, attacks from distance
   - When wary: Observes player carefully
   - When allied: Watches but doesn't approach first
   - Verify: Different behavior from bold sporeling_1

### Attack Behavior
3. **Combat When Hostile**
   - Mother is hostile
   - Verify: sporeling_2 attacks but less aggressively
   - Verify: Same stats (30 HP, spore_puff attack)
   - Verify: Tends to follow sporeling_1's lead

### Death Scenarios
4. **Same as Sporeling 1**
   - Kill sets has_killed_fungi flag
   - Myconid trust penalty applies
   - Mother death → confused state

## Dependencies
- Same as sporeling_1

## Walkthrough Files
- Covered by `test_spore_mother_*.txt` scenarios

## Implementation Status
- [ ] Same core mechanics as sporeling_1
- [ ] Cautious personality variant
- [ ] "Hangs back, observes" description

## Reference Implementation

This NPC demonstrates:
- **Personality variant**: Cautious (compared to bold sibling)
- **Same core mechanics**: State mirroring, range limit, spore network
