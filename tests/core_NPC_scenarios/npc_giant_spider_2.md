# NPC: giant_spider_2

## Core Mechanics
- pack_behavior: Follower of spider_matriarch
- respawn: Same as giant_spider_1 (every 10 turns while matriarch alive)
- combat: Standard bite attack (slightly larger, more aggressive)
- state: Always hostile

## Required Scenarios

### Combat Paths
1. **Spider Killed**
   - Same as giant_spider_1
   - Verify: Loot drops
   - Verify: Respawn if matriarch alive

2. **More Aggressive Than Sibling**
   - Description notes "slightly larger and more aggressive"
   - Verify: Combat behavior reflects this (if combat system supports)
   - Note: May be purely narrative difference

### Pack Behavior
3. **Same Respawn Rules**
   - Both spiders share respawn pool
   - Max 2 total at any time
   - Killing either triggers potential respawn

## Dependencies
- Same as giant_spider_1

## Walkthrough Files
- Covered by `test_spider_matriarch_combat.txt` - NEEDS CREATION

## Implementation Status
- [ ] Same core mechanics as giant_spider_1
- [ ] "Larger and more aggressive" description
- [ ] Shared respawn pool with giant_spider_1

## Reference Implementation

This NPC demonstrates:
- **Pack member variation**: Slight differences from sibling for flavor
- **Shared respawn pool**: Max 2 spiders regardless of which dies
