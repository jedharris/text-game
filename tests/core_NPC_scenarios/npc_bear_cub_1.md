# NPC: bear_cub_1

## Core Mechanics
- condition: wasting_sickness (severity 60)
- protected_by: dire_bear (mother attacks if cubs threatened)
- pack_behavior: Dependent of dire_bear, does not fight
- death_timer: 30 turns from first encounter (shared with bear_cub_2)

## Required Scenarios

### Success Path
1. **Healed by Player**
   - Player acquires healing_herbs from Civilized Remnants
   - Player uses healing_herbs on bear_cub_1
   - Verify: wasting_sickness condition removed
   - Verify: extra.cub_1_healed = true
   - Verify: Description changes from "ill, whimpering" to healthy
   - If both cubs healed:
   - Verify: dire_bear transitions grateful→allied
   - Verify: extra.cubs_healed = true

### Failure Paths
2. **Dies from Illness**
   - Timer expires (30 turns from first encounter)
   - Verify: bear_cub_1 state → dead
   - Verify: dire_bear state → vengeful
   - Verify: Bear becomes permanent enemy

3. **Killed by Player**
   - Player attacks bear_cub_1
   - Verify: dire_bear immediately attacks (protective)
   - If player kills cub:
   - Verify: dire_bear state → vengeful immediately
   - Verify: Same consequences as illness death

### Edge Cases
4. **Mother Dies First**
   - Player kills dire_bear
   - Cubs remain (unprotected)
   - Player can still heal cubs
   - Verify: No alliance benefit (mother dead)
   - Verify: Cubs survive if healed

5. **Partial Healing (Only One Cub)**
   - Heal bear_cub_1 but not bear_cub_2
   - Verify: bear_cub_1 healthy
   - Verify: bear_cub_2 still has timer
   - If timer expires for bear_cub_2:
   - Verify: dire_bear still becomes vengeful (one cub died)

## Dependencies
- **Items**:
  - healing_herbs (cures wasting_sickness)
- **NPCs**:
  - dire_bear (mother, protector, state depends on cubs)
  - bear_cub_2 (sibling, same condition)
- **Mechanics**:
  - Condition system (wasting_sickness)
  - Shared timer with bear_cub_2
  - Pack dependency (not follower, but dependent)

## Walkthrough Files
- Covered by `test_dire_bear_healing.txt` - NEEDS CREATION

## Implementation Status
- [ ] wasting_sickness condition with severity
- [ ] Death timer (30 turns)
- [ ] Healing via healing_herbs
- [ ] Protected_by relationship with dire_bear
- [ ] State changes affect mother's disposition

## Reference Implementation

This NPC demonstrates:
- **Dependent NPC**: Not a follower, but fate affects leader
- **Condition with timer**: Medical emergency with deadline
- **Protected relationship**: Mother attacks if cub threatened
- **Cross-NPC consequences**: Cub health determines mother's state
