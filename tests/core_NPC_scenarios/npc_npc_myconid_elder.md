# NPC: npc_myconid_elder

## Core Mechanics
- dialog_reactions: Spore-based communication (colors convey meaning)
- services: Cure fungal_infection, teach spore_resistance, provide equipment
- trust_system: Modifiers from fungal kills, Spore Mother healing, offerings
- spore_network: Knows if player has killed fungi

## Required Scenarios

### Services
1. **Cure Fungal Infection**
   - Have fungal_infection condition
   - Provide ice_crystal, rare_mineral, or gold
   - Verify: Infection fully cured
   - Verify: Payment consumed

2. **Teach Spore Resistance**
   - Build trust to 2+
   - Provide offering (rare_mineral, ice_crystal, or offering_item)
   - Verify: spore_resistance skill granted
   - Verify: 50% reduction in infection acquisition

3. **Provide Equipment (Free)**
   - Build trust to 2+
   - Request breathing_mask or spore_lantern
   - Verify: Items given freely

4. **Provide Equipment (Offering)**
   - Trust below 2
   - Request equipment
   - Verify: Requires offering
   - Verify: Items given after offering

### Trust System
5. **Spore Network Detection**
   - Kill any fungal creature (has_killed_fungi flag)
   - First interaction with Elder
   - Verify: Trust -3 penalty applied
   - Verify: "Soft-flesh carries death-smell. You have ended our kin."

6. **Spore Mother Healing Bonus**
   - Heal Spore Mother (give heartmoss)
   - Visit Elder
   - Verify: Trust +5
   - Verify: "You have healed the Mother. The network sings."

7. **Offering Trust**
   - Provide any offering
   - Verify: Trust +1

### Dialog Topics
8. **Cold Vulnerability**
   - Ask about cold/ice/frozen
   - Verify: "Cold is death to our kind"
   - Verify: Explains why they can't get ice_crystal themselves
   - Verify: knows_myconids_fear_cold flag set

9. **Spore Mother Information**
   - Ask about Spore Mother
   - Verify: Mournful spore colors
   - Verify: "Killing her... would sever something that cannot be remade"

10. **Heartmoss Information**
    - Ask about heartmoss (requires knows_about_heartmoss)
    - Verify: "Only soft-flesh can make this journey"
    - Verify: Explains why Myconids/sporelings can't retrieve it

### Edge Cases
11. **Multiple Cures**
    - Have Aldric at critical (severity 80)
    - Use Myconid cure service on Aldric
    - Verify: Aldric fully cured (not just stabilized like silvermoss)
    - Verify: Aldric transitions to recovering state

12. **Spore Communication**
    - All dialog delivered via colored spore puffs
    - Verify: Blue spores = greeting
    - Verify: Green spores = healing/cure
    - Verify: Yellow spores = teaching
    - Verify: Grey spores = mourning/fear

## Dependencies
- **Items**:
  - ice_crystal (from Frozen Reaches, payment)
  - gold (from Civilized Remnants, payment)
  - rare_mineral (alternative payment)
  - breathing_mask, spore_lantern (provided equipment)
- **NPCs**:
  - npc_spore_mother (trust bonus if healed)
  - npc_aldric (can be cured by service)
  - All fungal creatures (spore network detection)
- **Mechanics**:
  - Trust system with modifiers
  - Spore network communication
  - Service gating by trust and payment
  - Cold vulnerability (cannot visit Frozen Reaches)

## Walkthrough Files
- `test_myconid_services.txt` - NEEDS CREATION
- `test_myconid_trust.txt` - NEEDS CREATION

## Implementation Status
- [ ] Cure service (infection fully removed)
- [ ] Spore resistance teaching (trust 2+)
- [ ] Equipment provision (free at trust 2+)
- [ ] Trust modifiers (kills -3, Mother +5, offerings +1)
- [ ] Spore network detection (has_killed_fungi)
- [ ] Spore color communication
- [ ] Cold vulnerability dialog

## Reference Implementation

This NPC demonstrates:
- **Service provider**: Cure, teaching, equipment
- **Trust gating**: Services unlocked at different trust levels
- **Spore network**: Cross-creature communication (knows kills)
- **Non-verbal communication**: Colored spore puffs
- **Environmental vulnerability**: Cannot survive cold
- **Faction dynamics**: Trust affected by Spore Mother outcome
