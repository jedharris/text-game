# NPC: stone_golem_2

## Core Mechanics
- linked_to: stone_golem_1 (shared state)
- identical: Same stats and behavior as stone_golem_1
- guardian: Territorial, won't leave temple
- construct: Same immunities

## Required Scenarios

### Linked Behavior
1. **Shared Deactivation**
   - Deactivate stone_golem_1 via any method
   - Verify: stone_golem_2 also deactivated
   - Verify: Single solution handles both

2. **Independent Destruction**
   - Kill stone_golem_2 in combat
   - Verify: stone_golem_1 continues alone
   - Verify: No automatic deactivation from killing one

3. **Same Stats**
   - Combat with stone_golem_2
   - Verify: 150 HP, 25-35 damage, armor 10
   - Verify: Same immunities

## Dependencies
- Same as stone_golem_1

## Walkthrough Files
- Covered by `test_golem_*.txt` scenarios

## Implementation Status
- [ ] Linked state with stone_golem_1
- [ ] Same stats and behavior
- [ ] Independent in combat (doesn't auto-die)

## Reference Implementation

This NPC demonstrates:
- **Linked puzzle**: Solving for one solves for both
- **Independent combat**: Destroying one doesn't affect other
- **Identical design**: Same stats create predictable challenge
