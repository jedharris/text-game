# NPC: waystone_spirit

## Core Mechanics
- Note: This NPC represents the waystone itself, not a separate character
- The "spirit" is the magical essence of the damaged waystone
- Interacts through item mechanics rather than dialog

## Required Scenarios

### Waystone Repair
1. **Fragment Placement**
   - Gather waystone fragment from region
   - Place fragment in corresponding socket
   - Verify: Socket lights with region color
   - Verify: Fragment consumed/placed
   - Verify: Progress toward completion

2. **Fragment Sources**
   - spore_heart: Fungal Depths (Spore Mother gift after healing)
   - beast_fang: Beast Wilds (Alpha Wolf gift at high trust)
   - water_pearl: Sunken District (Archivist quest reward)
   - ice_shard: Frozen Reaches (Ice Caves extraction)
   - town_seal: Civilized Remnants (Council reward / Guardian repair)
   - Verify: Each fragment obtainable via narrative path

3. **Completion**
   - All five fragments placed
   - Verify: Colors merge, light flares
   - Verify: Waystone heals
   - Verify: Fast travel enabled
   - Verify: Echo transforms
   - Verify: Meridian Blessing buff granted

### Fast Travel
4. **Travel After Repair**
   - Waystone repaired
   - Touch waystone, think of destination
   - Verify: Travel to any region entry point
   - Destinations: cavern_entrance, forest_edge, flooded_plaza, frozen_pass, town_gate

### Edge Cases
5. **Partial Placement**
   - Place 3 of 5 fragments
   - Verify: Waystone partially glowing
   - Verify: No fast travel yet
   - Verify: Progress saved

6. **Placement Order**
   - Place fragments in any order
   - Verify: Order doesn't matter
   - Verify: Each fragment has narrative moment

## Dependencies
- **Items**:
  - spore_heart (from npc_spore_mother)
  - beast_fang (from alpha_wolf)
  - water_pearl (from the_archivist)
  - ice_shard (from ice_caves)
  - town_seal (from councilors or damaged_guardian)
- **NPCs**:
  - the_echo (transformation on completion)
- **Mechanics**:
  - Fragment tracking (5 boolean states)
  - Fast travel system
  - Meridian Blessing buff

## Walkthrough Files
- `test_waystone_repair.txt` - NEEDS CREATION

## Implementation Status
- [ ] Fragment placement mechanics
- [ ] Socket lighting visual
- [ ] Completion detection (all 5 fragments)
- [ ] Fast travel activation
- [ ] Echo transformation trigger
- [ ] Meridian Blessing buff
- [ ] Partial progress tracking

## Reference Implementation

This NPC demonstrates:
- **Item as NPC**: Waystone functions as interactive entity
- **Multi-source quest**: Fragments from all regions
- **Narrative milestone**: Repair is game completion
- **Reward cascade**: Fast travel, Echo transformation, blessing
- **Order independence**: Any order for fragment placement
