# NPC: spider_matriarch

## Core Mechanics
- encounter_reactions: Always hostile, no diplomatic path
- death_reactions: Stops spider respawn, spider_queen_dead flag
- pack_behavior: Leader of giant_spider_1, giant_spider_2
- respawn_mechanic: 2 spiders respawn every 10 turns while queen alive
- combat_bonus: +5 damage, +2 armor in web zones

## Required Scenarios

### Combat Paths
1. **Queen Defeated**
   - Navigate to spider_matriarch_lair
   - Engage in combat with spider_matriarch
   - Kill spider_matriarch
   - Verify: State → dead
   - Verify: spider_queen_dead flag set to true
   - Verify: death_reactions handler fires
   - Verify: Remaining spiders no longer respawn
   - Verify: Loot: spider_silk_bundle, queen_venom_sac

2. **Queen Defeated with Pack**
   - Kill spider_matriarch while giant_spiders alive
   - Verify: Spiders do NOT scatter (unlike wolves)
   - Verify: Remaining spiders fight to death
   - Verify: No more respawns

3. **Pack Respawn While Queen Lives**
   - Enter spider_thicket, kill giant_spider_1
   - Wait 10 turns
   - Verify: New spider spawns (if queen alive)
   - Verify: max 2 spiders can exist
   - Kill queen
   - Wait 10 turns
   - Verify: No new spiders spawn

### Avoidance Path
4. **Sneak Through Territory**
   - Enter spider_thicket without engaging
   - If stealth/light mechanics support:
   - Verify: Can pass through without combat
   - Verify: Queen remains hostile but not encountered

### Environmental Interaction
5. **Web Burning**
   - Bring salamander companion or torch
   - Burn webs in spider_nest_gallery
   - Verify: Alerts ALL spiders in area
   - Verify: Web effects removed (movement restored)
   - Verify: Spider combat bonus removed
   - Verify: Area permanently damaged (no web regeneration)

### Edge Cases
6. **Wolf Companion Refusal**
   - Have alpha_wolf as companion
   - Attempt to enter spider_nest_gallery
   - Verify: Wolves refuse to enter (territorial instinct)
   - Verify: Wolves wait at wolf_clearing
   - If player in danger (low health, losing combat):
   - Verify: Wolves MAY charge in (exceptional bravery, one-time)
   - Verify: Wolf sacrifice (1-2 wolves may die)

7. **Darkness Without Light**
   - Enter spider_nest_gallery without light source
   - Verify: Cannot see exits
   - Verify: Ambush attacks (combat disadvantage)
   - Verify: Salamander companion provides light

## Dependencies
- **Items**:
  - spider_silk_bundle (loot)
  - queen_venom_sac (loot)
  - torch (light source alternative to salamander)
- **NPCs**:
  - giant_spider_1, giant_spider_2 (pack followers)
  - salamander (companion for light/web burning)
  - alpha_wolf (refuses to enter, exceptional bravery possible)
- **Mechanics**:
  - Pack respawn system (unique to spiders)
  - Web zone environmental effects
  - Darkness/light mechanics
  - No diplomatic path (combat only)

## Walkthrough Files
- `test_spider_matriarch_combat.txt` (scenarios 1, 2, 3) - NEEDS CREATION
- `test_spider_web_burning.txt` (scenario 5) - NEEDS CREATION

## Implementation Status
- [ ] State machine: hostile→dead (no other paths)
- [ ] Pack respawn every 10 turns while alive
- [ ] death_reactions handler fires on death
- [ ] spider_queen_dead flag
- [ ] Combat bonus in web zones
- [ ] Loot drops on death
- [ ] Web burning mechanics
- [ ] Darkness/light source requirements

## Reference Implementation

This NPC demonstrates:
- **Combat-only encounter**: Deliberate contrast to diplomatic beasts
- **Pack respawn mechanic**: Unique to spiders (wolves don't respawn)
- **Environmental combat bonus**: Web zones give advantages
- **Light source requirement**: Darkness mechanics
- **Web burning consequences**: Permanent area damage
- **No diplomatic path**: Design choice, not missing content
