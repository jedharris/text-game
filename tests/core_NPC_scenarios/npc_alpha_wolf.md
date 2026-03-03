# NPC: alpha_wolf

## Core Mechanics
- encounter_reactions: Initial hostile encounter in wolf_clearing
- dialog_reactions: Non-verbal communication (body language, vocalizations)
- gift_reactions: Feeding with venison/meat builds trust
- pack_behavior: Leader of frost_wolf_1, frost_wolf_2 (state + location mirroring)
- trust_state: -2 initial, floor -5, ceiling 5
- domestication: Feed 3-4 times to progress hostile→wary→neutral→friendly→allied

## Required Scenarios

### Success Path
1. **Domestication via Feeding**
   - Navigate to wolf_clearing
   - Receive hostile territorial warning (one turn before attack)
   - Give venison to alpha_wolf
   - Verify: State transitions hostile→wary
   - Verify: trust_state increases by 1
   - Verify: Pack wolves mirror state change
   - Feed second time
   - Verify: State transitions wary→neutral
   - Feed third time (or defeat threat to pack)
   - Verify: State transitions neutral→friendly
   - Verify: trust >= 3
   - Feed fourth time OR ask to join
   - Verify: State transitions friendly→allied (companion)
   - Verify: Pack becomes companion
   - Verify: Can travel with wolves (except restricted areas)

2. **Alpha Fang Gift**
   - Complete domestication (trust >= 5)
   - Verify: Alpha offers alpha_fang spontaneously
   - Verify: "mark of pack bond" feedback
   - Verify: alpha_fang in player inventory
   - Verify: Cannot take fang by force (corpse has no fang)

### Failure Paths
3. **Combat Death**
   - Enter wolf_clearing while hostile
   - Attack wolves or wait past warning
   - Combat ensues
   - Kill alpha_wolf
   - Verify: Pack scatters (followers become hostile loners)
   - Verify: extra.alpha_wolf_dead = true
   - Verify: Domestication permanently impossible
   - Verify: alpha_fang NOT obtainable

4. **Pack Flees**
   - Enter combat with wolves
   - Damage alpha below 15 HP
   - Verify: Alpha flees (state→fled)
   - Verify: Pack flees with alpha
   - Wait 10 turns
   - Verify: Pack returns (state→hostile)
   - Verify: Can still attempt domestication

### Edge Cases
5. **Companion Area Restrictions**
   - Complete domestication
   - Travel to nexus_chamber
   - Verify: Wolves refuse to enter (magical wards)
   - Verify: Wolves wait at last valid location
   - Travel to civilized_remnants
   - Verify: Wolves refuse to enter (guards attack beasts)
   - Travel to spider_nest_gallery
   - Verify: Wolves refuse to enter (territorial instinct)
   - Return to wolf_clearing
   - Verify: Pack rejoins player

6. **Wolf-Sira Conflict**
   - Have wolf companion
   - Encounter hunter_sira
   - Verify: Sira trust -2 immediately
   - Verify: Sira hostile to wolves ("You travel with those killers?")
   - If trust rebuilt >= 2, initiate "coexist" dialog
   - Verify: Reconciliation possible
   - Verify: anti_beast_prejudice removed
   - Verify: Both can travel together

7. **Feeding Wrong Item**
   - Attempt to give non-food item to alpha
   - Verify: No trust change
   - Verify: Feedback indicates wolves not interested

## Dependencies
- **Items**:
  - venison (primary feeding item, found in forest_edge)
  - meat (alternative feeding item)
  - alpha_fang (gift from alpha at trust 5+)
- **NPCs**:
  - frost_wolf_1, frost_wolf_2 (pack followers)
  - hunter_sira (conflict potential)
- **Mechanics**:
  - Pack dynamics (state/location mirroring)
  - Trust state progression
  - Companion restrictions by location
  - Non-verbal communication (body language)

## Walkthrough Files
- `test_alpha_wolf_domestication.txt` (scenarios 1, 2) - NEEDS CREATION
- `test_alpha_wolf_combat.txt` (scenarios 3, 4) - NEEDS CREATION
- `test_wolf_sira_conflict.txt` (scenario 6) - NEEDS CREATION

## Implementation Status
- [ ] State machine: hostile→wary→neutral→friendly→allied
- [ ] Trust progression via feeding
- [ ] Pack behavior (followers mirror state)
- [ ] Alpha fang gift at trust 5+
- [ ] Companion restrictions (Nexus, Civilized Remnants, Spider Nest)
- [ ] Wolf-Sira reconciliation dialog
- [ ] Territorial warning system

## Reference Implementation

This NPC demonstrates:
- **Multi-step domestication**: Repeated feeding over time, not instant friendship
- **Pack dynamics**: Leader state affects all followers
- **Non-verbal communication**: Body language vocabulary instead of speech
- **Companion restrictions**: Location-based travel limits
- **Cross-NPC conflict**: Sira prejudice requires reconciliation
