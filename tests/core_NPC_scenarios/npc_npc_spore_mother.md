# NPC: npc_spore_mother

## Core Mechanics
- encounter_reactions: Hostile initially, attacks with spores and tendrils
- condition: fungal_blight (severity 70, only heartmoss cures)
- pack_behavior: Leader of sporeling_pack
- empathic_communication: Cannot speak, communicates through spores
- regeneration: 10 HP per turn

## Required Scenarios

### Success Path
1. **Healing via Heartmoss**
   - Navigate to spore_heart
   - Verify: State is hostile, sporelings hostile
   - Wait 3 turns without attacking (optional patience path)
   - Verify: State transitions hostile→wary if patient
   - Obtain heartmoss from deep_root_caverns
   - Give heartmoss to spore_mother (works in any state, even combat)
   - Verify: State transitions to allied
   - Verify: Sporelings become friendly
   - Verify: fungal_blight begins healing
   - Verify: Gratitude +5
   - Verify: Spore levels in region decrease (1 level per 5 turns)
   - Verify: Can pass freely through Spore Heart
   - Verify: Myconid trust +3

2. **Alliance Benefits**
   - Complete healing
   - Verify: Fungal creatures throughout game become friendly
   - Verify: Spore Heart becomes safe haven
   - Verify: Mother assists player against threats

### Failure Paths
3. **Death by Combat**
   - Attack spore_mother
   - Deal 200+ damage (with regeneration)
   - Verify: State → dead
   - Verify: Sporelings become neutral (confused, leaderless)
   - Verify: spore_mother_killed flag set
   - Verify: Drops item_mother_heart
   - Verify: Spore levels remain indefinitely
   - Verify: Myconid trust -5

### Patience Path
4. **Hostile to Wary Transition**
   - Enter spore_heart
   - Survive 3 turns without attacking
   - Verify: Mother stops attacking
   - Verify: Sporelings stop attacking
   - Verify: Player senses curiosity, hope through spores
   - Verify: State transitions hostile→wary

5. **Wary to Hostile Regression**
   - Reach wary state
   - Attack Mother
   - Verify: State transitions wary→hostile
   - Verify: 5 turns to return to wary (harder second time)

### Recovery Path
6. **Death in Combat Recovery**
   - Lose combat to Spore Mother
   - Verify: Sporelings drag player out
   - Verify: Player awakens in Luminous Grotto
   - Verify: Health 20, infection +20
   - Verify: Items retained
   - Verify: Mother now wary instead of hostile

### Commitment Scenarios
7. **Commitment to Heal**
   - Express commitment ("I'll find heartmoss")
   - Verify: Commitment recorded
   - Verify: 200 turn timer (very long - not urgent)
   - Complete healing
   - Verify: +2 gratitude bonus (total 7)

8. **Commitment Withdrawal**
   - Make commitment
   - Withdraw via Myconid translation
   - Verify: Myconid conveys: "Perhaps the surfacer needs warmth first"
   - Verify: Reveals Hot Springs location in Frozen Reaches
   - Verify: Can recommit

### Edge Cases
9. **Combat Healing**
   - Enter combat with Mother
   - During combat, give heartmoss
   - Verify: Combat ends immediately
   - Verify: State transitions to allied
   - Verify: Full healing benefits apply

10. **Empathic Communication**
    - Approach Mother
    - Verify: Player senses emotions through spores
    - Verify: Desperation, pain, wordless plea
    - Verify: No verbal dialog

## Dependencies
- **Items**:
  - heartmoss (only cure for fungal_blight)
  - mother_heart (dropped if killed)
- **NPCs**:
  - npc_sporeling_1, npc_sporeling_2, npc_sporeling_3 (pack followers)
  - npc_myconid_elder (translation for complex communication)
- **Locations**:
  - spore_heart (Mother's location)
  - deep_root_caverns (heartmoss location)
- **Mechanics**:
  - Pack leadership
  - Empathic spore communication
  - Fungal blight condition
  - Commitment system with Myconid translation

## Walkthrough Files
- `test_spore_mother_healing.txt` (scenarios 1, 2) - NEEDS CREATION
- `test_spore_mother_combat.txt` (scenarios 3, 4, 5) - NEEDS CREATION

## Implementation Status
- [ ] State machine: hostile→wary→allied / hostile→dead
- [ ] Patience path (3 turns → wary)
- [ ] Heartmoss cures fungal_blight
- [ ] Pack leadership (sporelings follow state)
- [ ] Regeneration (10 HP/turn)
- [ ] Combat healing (give heartmoss mid-combat)
- [ ] Recovery path (player defeat → second chance)
- [ ] Empathic communication (no verbal dialog)
- [ ] Commitment system with Myconid translation

## Reference Implementation

This NPC demonstrates:
- **Non-verbal boss**: Empathic spore communication only
- **Patience as strategy**: Waiting 3 turns unlocks diplomatic path
- **Combat healing**: Can heal enemy mid-combat
- **Second chance**: Defeat leads to recovery, not death
- **Pack leadership**: Actions affect all sporelings
- **Environmental healing**: Curing Mother heals region over time
