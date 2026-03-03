# NPC: frost_wolf_1

## Core Mechanics
- pack_behavior: Follower of alpha_wolf (from Beast Wilds)
- state_mirroring: Mirrors alpha_wolf's state
- environmental: Comfortable in cold zones, uncomfortable in extreme cold
- location: Beast Wilds primarily, may follow alpha as companion

## Required Scenarios

### State Mirroring
1. **Follow Alpha's State**
   - Alpha hostile → frost_wolf_1 hostile
   - Alpha wary → frost_wolf_1 wary
   - Alpha friendly → frost_wolf_1 friendly
   - Alpha allied → frost_wolf_1 follows as companion
   - Verify: State changes with alpha_wolf

2. **Companion Behavior**
   - Alpha becomes allied (companion)
   - Verify: frost_wolf_1 follows pack
   - Verify: Can travel to most regions with player

### Cold Region Behavior
3. **Frozen Reaches Comfort**
   - Travel to Frozen Reaches with wolf pack
   - Verify: Wolves comfortable in cold zones
   - Verify: Wolves have natural fur protection
   - Travel to extreme cold (Observatory)
   - Verify: Wolves refuse or wait at temple
   - Verify: "Too cold even for wolves"

4. **Combat Assistance**
   - Combat encounter with wolf companions
   - Verify: +15 damage from wolf pack
   - Verify: Wolves attack but do minimal damage to golems
   - Verify: Wolves sense golem threat, hesitate at temple

### Death Scenarios
5. **Wolf Killed**
   - frost_wolf_1 killed in combat
   - Verify: Alpha becomes aggressive/hostile (if not already allied)
   - Verify: Pack reduced by one
   - Verify: May scatter if alpha also killed

6. **Alpha Dies First**
   - Alpha killed before frost_wolf_1
   - Verify: frost_wolf_1 becomes hostile loner
   - Verify: No longer follows pack behavior

## Dependencies
- **NPCs**:
  - alpha_wolf (pack leader)
  - frost_wolf_2 (sibling)
- **Mechanics**:
  - Pack state mirroring
  - Companion system
  - Cold tolerance

## Walkthrough Files
- Covered by `test_alpha_wolf_*.txt` scenarios

## Implementation Status
- [ ] State mirroring with alpha_wolf
- [ ] Companion behavior when pack allied
- [ ] Cold tolerance (comfortable in cold, not extreme)
- [ ] Combat assistance (+15 damage)
- [ ] Golem interaction (minimal damage, sense threat)

## Reference Implementation

This NPC demonstrates:
- **Pack follower**: State mirrors leader
- **Cross-region companion**: Can travel with player
- **Environmental comfort**: Different zones have different comfort levels
- **Combat support**: Assists in fights
