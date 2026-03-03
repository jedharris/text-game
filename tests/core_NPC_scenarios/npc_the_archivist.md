# NPC: the_archivist

## Core Mechanics
- encounter_reactions: Guardian state, spectral scholar
- dialog_reactions: Information about disaster, history, water pearl
- knowledge_quest: Bring 3 of 5 knowledge fragments
- bound_to_location: Cannot leave deep_archive

## Required Scenarios

### Success Paths
1. **Basic Information**
   - Navigate to deep_archive (requires advanced swimming OR enchanted bubble)
   - Talk to the_archivist
   - Verify: Guardian state initially
   - Ask about disaster, history, or regions
   - Verify: Information provided
   - Verify: No trust gate for basic information

2. **Enchanted Bubble (Trust 2)**
   - Demonstrate scholarly interest (bring book, engage dialog)
   - Verify: State transitions guardian→helpful
   - Request enchanted bubble
   - Verify: Bubble provided (allows breathing in all flooded areas)

3. **Water Pearl (Knowledge Quest)**
   - Reach helpful state
   - Ask about water pearl
   - Verify: "Knowledge must be earned, preservation must be valued"
   - Complete knowledge quest (bring 3 of 5 fragments)
   - Verify: State transitions helpful→allied
   - Verify: Water pearl awarded
   - Verify: Waystone fragment obtained

### Knowledge Quest Details
4. **Knowledge Fragments**
   - merchant_ledger (merchant_warehouse): Trade routes from before disaster
   - survivor_story (survivor_camp, from Jek or Mira): Firsthand flood account
   - guild_records (flooded_chambers): Guildhall administrative records
   - garrett_map (sea_caves, from Garrett if rescued): Underwater passage maps
   - delvan_contacts (merchant_warehouse, from Delvan if rescued): Black market network
   - Verify: Need 3 of 5 to complete quest
   - Verify: Some fragments require rescuing NPCs (Garrett, Delvan)

5. **Fragment Delivery**
   - Collect 3+ fragments
   - Return to Archivist
   - Deliver fragments one by one
   - Verify: Each fragment acknowledged with relevant comment
   - Verify: After 3rd fragment, quest completes
   - Verify: State becomes allied
   - Verify: Water pearl available

### Edge Cases
6. **Spectral Nature**
   - Ask about identity
   - Verify: "I am what remains of the Chief Archivist"
   - Verify: "My body is... elsewhere now. But my duty persists."
   - Verify: Cannot leave archive (bound to location)

7. **Cold Efficiency Path**
   - Reach archive with advanced swimming (requires saving Garrett)
   - Complete knowledge quest with minimal interaction
   - Verify: Valid path but yields less value
   - Verify: Still requires some NPC interaction for fragments

8. **Child Survivor Hint**
   - Talk to child_survivor in camp
   - Verify: Hint about "library lady" being "lonely"
   - Verify: Suggests Archivist is approachable

9. **No Rescue Fragments**
   - Do NOT rescue Garrett or Delvan
   - Attempt knowledge quest
   - Verify: Can still complete with merchant_ledger, survivor_story, guild_records
   - Verify: Harder but possible without rescues

## Dependencies
- **Items**:
  - water_pearl (quest reward)
  - enchanted_bubble (trust 2 reward)
  - ancient_tome (readable in archive)
  - Knowledge fragments (5 possible)
- **NPCs**:
  - sailor_garrett (source of garrett_map fragment)
  - merchant_delvan (source of delvan_contacts fragment)
  - old_swimmer_jek/camp_leader_mira (source of survivor_story)
  - child_survivor (hint giver)
- **Mechanics**:
  - Knowledge quest (3 of 5 fragments)
  - Trust progression guardian→helpful→allied
  - Spectral NPC (bound to location)

## Walkthrough Files
- `test_archivist_knowledge_quest.txt` - NEEDS CREATION
- `test_archivist_water_pearl.txt` - NEEDS CREATION

## Implementation Status
- [ ] State machine: guardian→helpful→allied
- [ ] Basic information dialog
- [ ] Enchanted bubble at trust 2
- [ ] Knowledge quest (3 of 5 fragments)
- [ ] Water pearl at quest completion
- [ ] Spectral nature (bound to archive)
- [ ] Fragment tracking and acknowledgment

## Reference Implementation

This NPC demonstrates:
- **Spectral NPC**: Echo-like existence, bound to location
- **Knowledge economy**: Information as currency
- **Multi-source quest**: Fragments from exploration and NPCs
- **Cascading value**: Rescuing NPCs provides quest fragments
- **Waystone fragment source**: Water pearl for main quest
