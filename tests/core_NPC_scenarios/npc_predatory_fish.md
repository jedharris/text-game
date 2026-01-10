# NPC: predatory_fish

## Core Mechanics
- environmental_hazard: Not a combat encounter
- behavior: Watch in shallows, attack in deep water
- damage: 8 HP + bleeding per bite
- design_purpose: Make swimming costly without skill

## Required Scenarios

### Behavior by Location
1. **Shallow Water Behavior**
   - Enter flooded_chambers (chest-deep water)
   - Verify: Fish watch but don't attack
   - Verify: Can observe "shadows moving between columns"
   - Verify: No damage while in shallows

2. **Deep Water Behavior**
   - Enter tidal_passage (submerged)
   - Without swimming skill:
   - Verify: Fish attack once during crossing
   - Verify: 8 HP damage
   - Verify: bleeding condition applied
   - With advanced_swimming:
   - Verify: Can avoid fish attacks

3. **Attack Pattern**
   - Fish dart in, bite, retreat
   - Verify: One attack per passage (not continuous)
   - Verify: Cannot be "killed" for loot/XP
   - Verify: They retreat but return

### Combat Interaction
4. **Combat in Water**
   - Attempt to fight fish
   - Verify: Heavy penalty (-4 attack, half damage)
   - Verify: Fish retreat from combat
   - Verify: Fish return after combat ends
   - Verify: No XP or loot from fish

5. **Blood in Water**
   - Player or NPC bleeding
   - Verify: Fish become cautious (not bold)
   - Verify: Multiple wounded makes them hesitate
   - Note: Design choice - not a feeding frenzy

### Skill Mitigation
6. **Basic Swimming**
   - Enter deep water with basic_swimming
   - Verify: Passage possible but slow (2 turns)
   - Verify: Fish still attack once

7. **Advanced Swimming**
   - Enter deep water with advanced_swimming
   - Verify: Safe passage (1 turn)
   - Verify: Can avoid fish attacks entirely

### Edge Cases
8. **Wolf Companion Interaction**
   - Have wolf companion in shallow water
   - Verify: Some fish avoid wolf-accompanied player
   - Verify: Intimidation effect
   - Note: Wolves can't enter deep water

## Dependencies
- **Skills**:
  - basic_swimming (reduces passage time)
  - advanced_swimming (avoids attacks)
- **Conditions**:
  - bleeding (applied by bite)
- **Mechanics**:
  - Environmental hazard (not combat)
  - Water depth system

## Walkthrough Files
- Covered by swimming/rescue walkthroughs - NEEDS CREATION

## Implementation Status
- [ ] Behavior by water depth (watch vs attack)
- [ ] Attack mechanics (8 HP + bleeding)
- [ ] One attack per passage
- [ ] Cannot be killed/looted
- [ ] Swimming skill mitigation
- [ ] Combat penalty in water
- [ ] Blood behavior (caution, not frenzy)

## Reference Implementation

This NPC demonstrates:
- **Environmental hazard**: Obstacle, not enemy
- **Skill gate**: Swimming reduces/eliminates danger
- **Design purpose**: Cost without combat content
- **Behavior variation**: Different in shallow vs deep water
