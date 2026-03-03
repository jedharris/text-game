# NPC: bear_cub_2

## Core Mechanics
- condition: wasting_sickness (severity 70 - worse than sibling)
- protected_by: dire_bear (mother attacks if cubs threatened)
- pack_behavior: Dependent of dire_bear, does not fight
- death_timer: 30 turns from first encounter (shared with bear_cub_1)

## Required Scenarios

### Success Path
1. **Healed by Player**
   - Player acquires healing_herbs from Civilized Remnants
   - Player uses healing_herbs on bear_cub_2
   - Verify: wasting_sickness condition removed
   - Verify: extra.cub_2_healed = true
   - Verify: Description changes from "lying still, breathing shallowly" to healthy
   - If both cubs healed:
   - Verify: dire_bear transitions grateful→allied

### Failure Paths
2. **Dies from Illness**
   - Timer expires (30 turns from first encounter)
   - Note: bear_cub_2 has higher severity (70 vs 60)
   - Verify: bear_cub_2 state → dead
   - Verify: dire_bear state → vengeful

3. **Killed by Player**
   - Same as bear_cub_1 scenarios

### Edge Cases
4. **Dies First Due to Higher Severity**
   - If condition mechanics use severity for progression
   - bear_cub_2 (severity 70) may die before bear_cub_1 (severity 60)
   - Verify: Same vengeful consequences

5. **Only bear_cub_2 Dies**
   - Heal bear_cub_1 but not bear_cub_2
   - Timer expires for bear_cub_2
   - Verify: dire_bear becomes vengeful (losing ANY cub triggers this)
   - Verify: bear_cub_1 survives but mother is enemy

## Dependencies
- **Items**:
  - healing_herbs (cures wasting_sickness)
- **NPCs**:
  - dire_bear (mother, protector)
  - bear_cub_1 (sibling)
- **Mechanics**:
  - Same as bear_cub_1

## Walkthrough Files
- Covered by `test_dire_bear_healing.txt` - NEEDS CREATION

## Implementation Status
- [ ] wasting_sickness condition with higher severity (70)
- [ ] Death timer shared with bear_cub_1
- [ ] "Breathing shallowly" description indicating worse condition
- [ ] Healing mechanics same as bear_cub_1

## Reference Implementation

This NPC demonstrates:
- **Severity variation**: Higher severity indicates worse condition
- **Sibling pair**: Both must be healed for full success
- **Any death triggers consequence**: Losing either cub triggers mother's vengeful state
