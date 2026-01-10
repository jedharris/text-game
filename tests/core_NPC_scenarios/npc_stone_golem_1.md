# NPC: stone_golem_1

## Core Mechanics
- encounter_reactions: Activates when player enters temple without authorization
- guardian: Territorial, won't leave temple
- construct: Immune to poison, disease, bleeding, drowning, cold, fire
- linked_to: stone_golem_2 (share deactivation state)

## Required Scenarios

### Deactivation Methods
1. **Password Deactivation**
   - Enter temple_sanctum
   - Golems activate (hostile)
   - Read lore_tablets for password
   - Speak: "Fire-that-gives-life and water-that-cleanses, united in purpose"
   - Verify: Golems become passive
   - Verify: Allow passage but don't serve
   - Verify: Both golems deactivated together

2. **Control Crystal Deactivation**
   - Find control_crystal in ice_caves side passage
   - Extract with heat source
   - Use control_crystal on golem
   - Verify: Golems become serving state
   - Verify: Golems bow, await orders
   - Verify: Full control (best solution)

3. **Ritual Offering Deactivation**
   - Obtain fire_aspected_item (fire_crystal, torch)
   - Obtain water from hot_springs
   - Present ritual offering at altar
   - Verify: Golems recognize ancient protocol
   - Verify: Golems become passive

4. **Combat Path (Hard Mode)**
   - Choose to fight golems
   - Verify: 150 HP each, 25-35 damage, armor 10
   - Verify: ~18 rounds to kill one with optimal play
   - Use pillar cover (80% damage reduction)
   - Verify: Requires multiple healing potions
   - Verify: Intentionally punishing

### Guardian Behavior
5. **Territorial Limits**
   - Deactivate golems
   - Try to lead golems out of temple
   - Verify: Golems won't leave temple
   - Verify: Even "serving" golems stay

6. **Threshold Pause**
   - Stand in doorway of temple
   - Verify: Golems don't attack in doorway
   - Verify: Allows observation before commitment

7. **Memory**
   - Deactivate golems (passive or serving)
   - Leave temple
   - Return later
   - Verify: Golems remember player
   - Verify: Return to guarding but recognize player

### Edge Cases
8. **Partial Password**
   - Try partial phrase: "Fire-that-gives-life and water-that-cleanses, united"
   - Verify: May produce partial response or hint
   - Verify: Full password required for deactivation

9. **One Golem Destroyed**
   - Kill stone_golem_1
   - Verify: stone_golem_2 continues alone
   - Verify: Other deactivation methods still work on remaining golem

10. **Wolf Companion Interaction**
    - Have wolf pack companion
    - Enter temple
    - Verify: Wolves hesitate, sense threat
    - Verify: Wolves do minimal damage (5 per hit)
    - If player trapped: Alpha may charge in (one-time rescue)

## Dependencies
- **Items**:
  - lore_tablets (password source)
  - control_crystal (full control method)
  - fire_aspected_item + hot_springs_water (ritual offering)
- **NPCs**:
  - stone_golem_2 (linked state)
- **Mechanics**:
  - Multiple deactivation methods
  - Construct immunities
  - Territorial behavior
  - Cover system in combat

## Walkthrough Files
- `test_golem_password.txt` - NEEDS CREATION
- `test_golem_control_crystal.txt` - NEEDS CREATION
- `test_golem_combat.txt` - NEEDS CREATION

## Implementation Status
- [ ] State machine: guarding→hostile→passive/serving/destroyed
- [ ] Password deactivation
- [ ] Control crystal deactivation (full control)
- [ ] Ritual offering deactivation
- [ ] Combat stats (150 HP, 25-35 damage, armor 10)
- [ ] Pillar cover system
- [ ] Territorial limits (won't leave temple)
- [ ] Threshold pause (doorway safe)
- [ ] Player memory (remembers authorization)
- [ ] Linked state with stone_golem_2

## Reference Implementation

This NPC demonstrates:
- **Puzzle boss**: Multiple peaceful solutions preferable to combat
- **Hard mode available**: Combat possible but punishing
- **Linked NPCs**: Both golems share deactivation state
- **Territorial**: Won't leave guarded area
- **Player memory**: Remembers authorized players
- **Construct immunities**: Many conditions don't affect
