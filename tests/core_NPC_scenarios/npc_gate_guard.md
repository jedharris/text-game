# NPC: gate_guard

## Core Mechanics
- encounter_reactions: Entry checkpoint, inspects all entering
- dialog_reactions: Questions about purpose, companions, infection
- companion_filter: Wolves denied, salamander hesitant, myconid hostile
- linked_npcs: gate_guard (x2) share state

## Required Scenarios

### Success Paths
1. **Normal Entry**
   - Approach town_gate
   - Guard inspects player
   - Verify: No infection, no contraband, no hostile companions
   - Verify: Entry permitted
   - Verify: State transitions suspicious→neutral

2. **Friendly Entry (High Reputation)**
   - Have town reputation 3+
   - Approach town_gate
   - Verify: Guards recognize player
   - Verify: State starts or transitions to friendly
   - Verify: Expedited entry, friendly dialog

### Failure Paths
3. **Infected Player Denied**
   - Player has fungal_infection condition
   - Approach town_gate
   - Verify: Guard detects infection
   - Verify: "Cure infection first" dialog
   - Verify: Entry denied
   - Verify: Must cure before allowed in

4. **Wolf Companion Denied**
   - Have alpha_wolf companion
   - Approach town_gate
   - Verify: "No beasts in the town!" dialog
   - Verify: Guards draw weapons
   - Verify: Entry absolutely denied
   - If player insists: Combat ensues, reputation -5

5. **Myconid Companion Denied**
   - Have myconid companion (if possible)
   - Approach town_gate
   - Verify: Horrified reaction
   - Verify: "Spore creature?!" dialog
   - Verify: Entry denied

### Edge Cases
6. **Salamander Companion Hesitant Entry**
   - Have salamander companion
   - Approach town_gate
   - Verify: Guards nervous
   - Verify: "Fire creature? If it burns anything, you're responsible."
   - Verify: Entry permitted with hesitation
   - Verify: -1 temporary reputation
   - Wait 5 turns without incident
   - Verify: Penalty removed

7. **Bribe Acceptance**
   - Approach gate while suspicious
   - Offer bribe
   - Verify: State transitions to friendly
   - Verify: Entry expedited

## Dependencies
- **NPCs**:
  - Second gate_guard (linked state)
- **Mechanics**:
  - Companion filter system
  - Infection detection
  - Town reputation system
  - Linked NPC state

## Walkthrough Files
- `test_gate_guard_entry.txt` - NEEDS CREATION

## Implementation Status
- [ ] State machine: suspicious→neutral→friendly
- [ ] Linked state between two guards
- [ ] Companion filter (wolf, salamander, myconid)
- [ ] Infection detection
- [ ] Reputation-aware behavior
- [ ] Bribe acceptance

## Reference Implementation

This NPC demonstrates:
- **Entry checkpoint**: Filter for conditions and companions
- **Linked NPC state**: Two guards share same disposition
- **Companion restrictions**: Different handling per companion type
- **Reputation awareness**: Behavior changes based on town standing
