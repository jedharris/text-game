# NPC: npc_aldric

## Core Mechanics
- encounter_reactions: Found at cavern_entrance (Fungal Depths)
- condition: fungal_infection (severity 80, critical state)
- death_timer: 50 turns from game start
- services: Teaches mycology skill when stabilized
- commitment: Player can commit to finding silvermoss

## Required Scenarios

### Success Path
1. **Stabilization via Silvermoss**
   - Navigate to loc_cavern_entrance (Fungal Depths)
   - Find Aldric in critical state
   - Verify: fungal_infection severity 80
   - Verify: Death timer active (50 turns)
   - Navigate to loc_luminous_grotto
   - Obtain silvermoss
   - Give silvermoss to Aldric
   - Verify: State transitions critical→stabilized
   - Verify: Infection severity reduced by 40 (80→40)
   - Verify: Infection progression stopped
   - Verify: Gratitude +2
   - Verify: Teaching service unlocked

2. **Full Recovery**
   - Aldric stabilized
   - Give second silvermoss OR use Myconid cure service
   - Verify: State transitions stabilized→recovering
   - Verify: Infection fully cured
   - Verify: Can walk (slowly)
   - Verify: Offers to relocate to Nexus
   - Verify: Gratitude +2

3. **Learn Mycology**
   - Aldric stabilized (trust 2+)
   - Provide gift (rare_herb, research_notes, offering_item)
   - Verify: mycology skill granted
   - Verify: Can navigate spore areas safely
   - Verify: Understand fungal creatures

### Failure Paths
4. **Death by Timer**
   - Do not help Aldric within 50 turns
   - Verify: State transitions critical→dead
   - Verify: aldric_dead flag set
   - Verify: Mycology skill unavailable from this source
   - Verify: Journal remains (puzzle hints)

5. **Death by Health**
   - Aldric health reaches 0 (infection damage)
   - Verify: Same death consequences

### Commitment Scenarios
6. **Commitment Made**
   - Express commitment ("I'll find silvermoss")
   - Verify: Commitment recorded
   - Verify: Hope extends survival (+10 turns = 60 total)
   - Complete healing
   - Verify: +2 gratitude bonus (beyond base)

7. **Commitment Withdrawal**
   - Make commitment
   - Return and withdraw
   - Verify: Aldric gives journal (if not taken)
   - Verify: Unlocks myconid_equipment topic
   - Verify: "The myconids have masks that filter spores"
   - Verify: Can recommit

8. **Commitment Abandoned**
   - Make commitment
   - Let timer expire
   - Verify: broke_promise_aldric flag set
   - Verify: Echo reaction: "He waited for you"
   - Verify: Myconid reaction if they learn
   - Verify: -1 trust spread

### Dialog Topics
9. **Infection Information**
   - Ask about infection/sick/illness
   - Verify: Reveals silvermoss location (Luminous Grotto)
   - Verify: Explains why he can't get it (too weak, air would kill him)
   - Verify: knows_aldric_needs_silvermoss flag set

10. **Spore Mother Information**
    - Ask about spore mother (requires knows_aldric_needs_silvermoss)
    - Verify: Reveals heartmoss in Deep Root Caverns
    - Verify: Explains Mother is dying too
    - Verify: knows_about_heartmoss flag set

11. **Safe Path Information**
    - Ask about safe path (requires knows_about_heartmoss)
    - Verify: Ceiling inscription hint
    - Verify: Mushroom puzzle hint
    - Verify: knows_safe_path_exists flag set

### Edge Cases
12. **Relocation to Civilized Remnants**
    - Aldric fully recovered
    - Bring to Civilized Remnants
    - Verify: Townsfolk recognize him
    - Verify: Town provides lodging
    - Verify: +1 Elara trust (saved_aldric)

13. **Research Notes Gift**
    - Find research_notes on dead_explorer
    - Give to Aldric
    - Verify: Counts as gift for teaching service
    - Verify: Trust +1

## Dependencies
- **Items**:
  - silvermoss (stabilizes infection, loc_luminous_grotto)
  - aldric_journal (puzzle hints, can be taken or given by Aldric)
  - research_notes (gift item, from dead_explorer)
- **NPCs**:
  - npc_myconid_elder (alternative cure, knows if Aldric dies)
  - healer_elara (trust bonus if Aldric saved)
  - the_echo (commitment tracking)
- **Locations**:
  - loc_cavern_entrance (Aldric's location)
  - loc_luminous_grotto (silvermoss location)
- **Mechanics**:
  - Commitment system with hope extension
  - Condition progression (fungal_infection)
  - Skill teaching (mycology)
  - Cross-region relocation

## Walkthrough Files
- `test_aldric_rescue.txt` - NEEDS CREATION
- `test_aldric_mycology.txt` - NEEDS CREATION

## Implementation Status
- [ ] State machine: critical→stabilized→recovering / critical→dead
- [ ] Fungal infection with 50-turn death timer
- [ ] Silvermoss stabilization (reduces severity, stops progression)
- [ ] Full cure via second silvermoss or Myconid service
- [ ] Mycology teaching at trust 2+ with gift
- [ ] Commitment system with hope extension (+10 turns)
- [ ] Dialog topics with flag gating
- [ ] Relocation to Civilized Remnants
- [ ] Death consequences (skill unavailable, Echo/Myconid reactions)

## Reference Implementation

This NPC demonstrates:
- **Timed rescue**: Death timer with hope extension
- **Two-step healing**: Stabilize first, then full cure
- **Skill teacher**: Mycology at trust gate
- **Information source**: Hints about Spore Mother, safe path, mushroom puzzle
- **Cross-region relocation**: Can move to Civilized Remnants
- **Commitment consequences**: Abandonment affects Echo, Myconids
