# NPC: frost_wolf_2

## Core Mechanics
- pack_behavior: Follower of alpha_wolf
- state_mirroring: Mirrors alpha_wolf's state
- identical_to: frost_wolf_1 (same mechanics)

## Required Scenarios

### State Mirroring
1. **Same as frost_wolf_1**
   - Follow alpha's state
   - Companion behavior when pack allied
   - Cold region behavior

### Pack Dynamics
2. **Second Pack Member**
   - Verify: Same state as frost_wolf_1
   - Verify: Same combat contribution
   - Verify: Pack total provides +15 damage (shared, not per wolf)

## Dependencies
- Same as frost_wolf_1

## Walkthrough Files
- Covered by `test_alpha_wolf_*.txt` scenarios

## Implementation Status
- [ ] Same core mechanics as frost_wolf_1
- [ ] Part of wolf pack combat contribution

## Reference Implementation

This NPC demonstrates:
- **Pack member**: Identical mechanics to sibling
- **Shared pack contribution**: Combat bonus is for pack, not individual
