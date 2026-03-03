# NPC: npc_sporeling_1

## Core Mechanics
- pack_behavior: Follower of npc_spore_mother
- state_mirroring: Mirrors Mother's state (hostile/wary/allied)
- range_limit: Bound to spore_heart (cannot leave Mother's presence)
- empathic_communication: Colored spore puffs reflect Mother's emotions

## Required Scenarios

### State Mirroring
1. **Follow Mother's State**
   - Mother hostile → sporeling hostile
   - Mother wary → sporeling wary (stop attacking)
   - Mother allied → sporeling friendly
   - Verify: State changes with Mother

2. **Attack Behavior (Hostile)**
   - Mother is hostile
   - Verify: Sporeling attacks with spore_puff
   - Verify: 5 damage + 10 fungal_infection severity

3. **Passive Behavior (Wary/Allied)**
   - Mother is wary or allied
   - Verify: Sporeling does not attack
   - Verify: Emits curious/friendly spore puffs

### Range Limitation
4. **Cannot Leave Spore Heart**
   - Attempt to lure sporeling out
   - Verify: Sporeling stops at spore_heart boundary
   - Verify: "Sustained by Mother's presence. Would wither if separated."
   - Verify: Cannot accompany player to deep_root_caverns

### Empathic Communication
5. **Emotion Cascade**
   - Mother feels pain → sporelings emit distress puffs
   - Mother feels gratitude → sporelings brighten
   - Mother feels curiosity → sporelings hop closer
   - Verify: Sporelings help player understand Mother's feelings

### Death Scenarios
6. **Sporeling Killed**
   - Kill sporeling_1
   - Verify: has_killed_fungi flag set
   - Verify: Myconid trust penalty (-3 on first interaction)
   - Verify: Spore network remembers

7. **Mother Dies**
   - Spore Mother killed
   - Verify: Sporeling becomes neutral (confused)
   - Verify: Does not attack but does not help
   - Verify: May wither over time (10 turns → dead)

### Edge Cases
8. **Bold Personality**
   - sporeling_1 is "bold" variant
   - Verify: Moves toward player first
   - Verify: Most aggressive of three when hostile
   - Verify: Most curious when wary

## Dependencies
- **NPCs**:
  - npc_spore_mother (pack leader)
  - npc_sporeling_2, npc_sporeling_3 (siblings)
  - npc_myconid_elder (spore network, trust penalty)
- **Mechanics**:
  - Pack state mirroring
  - Range limitation (bound to location)
  - Empathic communication
  - Spore network (Myconids detect kills)

## Walkthrough Files
- Covered by `test_spore_mother_*.txt` scenarios

## Implementation Status
- [ ] State mirroring with Mother
- [ ] spore_puff attack (5 damage + 10 infection)
- [ ] Range limit to spore_heart
- [ ] Empathic spore puff communication
- [ ] Bold personality variant
- [ ] Death sets has_killed_fungi flag
- [ ] Mother death → confused state

## Reference Implementation

This NPC demonstrates:
- **Pack follower with state mirroring**: State follows leader
- **Range limitation**: Cannot leave specific location
- **Empathic communication**: Helps convey Mother's emotions
- **Personality variant**: Bold (compared to cautious sibling)
- **Spore network**: Kill detection across fungal creatures
