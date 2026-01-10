# NPC: giant_spider_1

## Core Mechanics
- pack_behavior: Follower of spider_matriarch
- respawn: Respawns every 10 turns while matriarch alive (max 2 total)
- combat: Web spray ability (immobilizes 1 turn)
- state: Always hostile (no state mirroring - spiders don't follow leader state)

## Required Scenarios

### Combat Paths
1. **Spider Killed**
   - Navigate to spider_thicket
   - Engage giant_spider_1 in combat
   - Kill spider
   - Verify: Spider drops loot (spider_silk common, venom_sac uncommon)
   - Verify: State → dead
   - If matriarch alive:
   - Wait 10 turns
   - Verify: New spider respawns

2. **Web Spray Attack**
   - Enter combat with giant_spider_1
   - Spider uses web spray
   - Verify: Player immobilized for 1 turn
   - Verify: "Webbed" condition applied
   - Verify: Movement blocked while webbed

### Pack Behavior
3. **No State Mirroring**
   - Verify: giant_spider_1 is always hostile
   - Verify: Does NOT change state when matriarch changes (matriarch only has hostile/dead)
   - Contrast with wolves (which mirror alpha state)

4. **Respawn Mechanic**
   - Kill giant_spider_1
   - Verify: Matriarch still alive
   - Wait 10 turns
   - Verify: New giant_spider appears
   - Kill matriarch
   - Kill any remaining spiders
   - Wait 10 turns
   - Verify: No new spiders (respawn stopped)

### Edge Cases
5. **Max Spider Count**
   - Both giant_spider_1 and giant_spider_2 alive
   - Verify: No additional spiders spawn
   - Kill one spider
   - Wait 10 turns
   - Verify: One new spider spawns (back to 2)
   - Verify: Max count is 2

6. **Matriarch Dies First**
   - Kill spider_matriarch
   - Verify: giant_spider_1 still hostile
   - Verify: Fights to death (doesn't scatter like wolves)
   - Verify: No respawn possible

## Dependencies
- **Items**:
  - spider_silk (common loot)
  - venom_sac (uncommon loot)
- **NPCs**:
  - spider_matriarch (pack leader, controls respawn)
  - giant_spider_2 (sibling)
- **Mechanics**:
  - Pack follower without state mirroring
  - Respawn system tied to leader
  - Web spray combat ability

## Walkthrough Files
- Covered by `test_spider_matriarch_combat.txt` - NEEDS CREATION

## Implementation Status
- [ ] Always hostile state (no diplomatic transitions)
- [ ] Pack follower of spider_matriarch
- [ ] Respawn every 10 turns while matriarch alive
- [ ] Web spray ability (immobilize 1 turn)
- [ ] Loot drops (spider_silk, venom_sac)
- [ ] Max 2 spiders at a time

## Reference Implementation

This NPC demonstrates:
- **Combat-only follower**: No diplomatic path, always hostile
- **Respawn mechanic**: Unique to spider pack (wolves don't respawn)
- **No state mirroring**: Unlike wolves, spiders don't follow leader state
- **Special combat ability**: Web spray for immobilization
