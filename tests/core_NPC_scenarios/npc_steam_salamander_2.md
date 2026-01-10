# NPC: steam_salamander_2

## Core Mechanics
- follows: steam_salamander_1 (becomes friendly when leader does)
- elemental: Fire-aspected
- cannot_companion: Stays at hot springs (only salamander_1 can companion)

## Required Scenarios

### Following Behavior
1. **Follow Leader's State**
   - steam_salamander_1 becomes friendly
   - Verify: steam_salamander_2 becomes friendly
   - Verify: All salamanders react together

2. **Cannot Become Companion**
   - All salamanders friendly
   - Try to recruit salamander_2
   - Verify: Only salamander_1 can become companion
   - Verify: salamander_2 stays at hot springs

### Social Interaction
3. **Meeting Companion**
   - Have salamander_1 as companion
   - Return to hot springs
   - Verify: Joyful reunion
   - Verify: Companion introduces player to others
   - Verify: +1 gratitude with all

4. **Hostility Check**
   - Attack any salamander
   - Verify: All three become hostile
   - Verify: salamander_2 joins combat

## Dependencies
- **NPCs**:
  - steam_salamander_1 (leader, companion option)
  - steam_salamander_3 (sibling)
- **Mechanics**:
  - Following behavior
  - Group hostility

## Walkthrough Files
- Covered by `test_salamander_*.txt` scenarios

## Implementation Status
- [ ] Follow salamander_1's state
- [ ] Cannot become companion
- [ ] Reunion behavior when companion visits
- [ ] Group hostility if attacked

## Reference Implementation

This NPC demonstrates:
- **Follower behavior**: State mirrors leader
- **Non-companion**: Adds social depth without being recruitable
- **Group dynamics**: Hostility/friendship applies to all
