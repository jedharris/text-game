# NPC: salamander

## Core Mechanics
- encounter_reactions: Neutral initial disposition
- dialog_reactions: Can communicate (responds to talk)
- pack_behavior: Leader of steam_salamander_2, steam_salamander_3
- domestication: Curious→friendly→companion progression
- companion_abilities: Light source, fire damage, web burning

## Required Scenarios

### Success Path
1. **Domestication**
   - Navigate to hot_springs (Frozen Reaches)
   - Encounter salamander in neutral state
   - Build trust through positive interactions
   - Verify: State transitions neutral→friendly→companion
   - Verify: Pack followers (steam_salamander_2, steam_salamander_3) mirror state

2. **Companion Utility in Beast Wilds**
   - Have salamander as companion
   - Enter spider_nest_gallery (dark)
   - Verify: Salamander provides light
   - Verify: Can see exits, no ambush penalty
   - Use fire ability on webs
   - Verify: Webs burned, movement restored
   - Verify: Alerts all spiders in area
   - Combat with spiders
   - Verify: +10-15 fire damage from salamander

### Environmental Restrictions
3. **Cannot Enter Sunken District**
   - Have salamander companion
   - Attempt to enter Sunken District locations
   - Verify: Salamander refuses (water extinguishes fire)
   - Verify: "Elemental conflict" feedback
   - Verify: Salamander waits outside

4. **Uncomfortable in Beast Wilds**
   - Travel through Beast Wilds with salamander
   - Verify: Salamander complains about humidity/vegetation
   - Verify: No mechanical penalty, just dialog

### NPC Reactions
5. **Beast Reactions to Fire**
   - Enter wolf_clearing with salamander companion
   - Verify: Wolves curious but wary (not hostile to fire)
   - Enter predators_den with salamander
   - Verify: Bear keeps distance (neither hostile nor friendly)
   - Enter spider_nest_gallery with salamander
   - Verify: Spiders terrified of fire (-2 morale in combat)

### Edge Cases
6. **Web Burning Consequences**
   - Burn webs in spider gallery
   - Verify: Area permanently damaged
   - Verify: No web regeneration
   - Verify: Spiders lose combat bonus in cleared areas

7. **Dramatic Self-Sacrifice**
   - Enter water area with salamander (if override possible)
   - Verify: Dramatic consequences (salamander injury/death)
   - Note: This is "exceptional individual" behavior, not standard

## Dependencies
- **Items**:
  - None specific (fire abilities are innate)
- **NPCs**:
  - steam_salamander_2, steam_salamander_3 (pack followers)
  - spider_matriarch, giant_spiders (fire interaction)
  - alpha_wolf (mutual wariness)
- **Mechanics**:
  - Light source provision
  - Fire damage in combat
  - Web burning
  - Elemental companion restrictions
  - Pack leadership

## Walkthrough Files
- `test_salamander_domestication.txt` - NEEDS CREATION
- `test_salamander_spider_nest.txt` - NEEDS CREATION

## Implementation Status
- [ ] State machine: neutral→friendly→companion
- [ ] Pack leadership (steam_salamander_2, steam_salamander_3)
- [ ] Light source ability
- [ ] Fire damage in combat
- [ ] Web burning ability
- [ ] Sunken District restriction (water)
- [ ] Beast Wilds discomfort dialog
- [ ] Spider fear of fire

## Reference Implementation

This NPC demonstrates:
- **Elemental companion**: Fire-based abilities and restrictions
- **Environmental utility**: Light source, web clearing
- **Cross-region companion**: Can travel to Beast Wilds
- **Location restrictions**: Cannot enter water areas
- **NPC reactions**: Different beasts react differently to fire
- **Pack leadership**: Followers mirror state
