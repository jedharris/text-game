# NPC: weaponsmith_toran

## Core Mechanics
- dialog_reactions: Forge conversation, equipment discussion
- services: Sell weapons, sell armor, repair weapons
- reputation_effects: Refuses service at reputation -3

## Required Scenarios

### Success Paths
1. **Purchase Weapons**
   - Navigate to market_square
   - Talk to weaponsmith_toran
   - Purchase sword (40g), silver_sword (100g), dagger (20g), or crossbow (60g)
   - Verify: Transaction completes
   - Verify: Weapon added to inventory

2. **Purchase Armor**
   - Purchase leather_armor (30g) or chain_shirt (80g)
   - Verify: Transaction completes
   - Verify: Armor added to inventory

3. **Repair Weapon**
   - Have damaged weapon
   - Request repair
   - Pay 10-30g depending on damage
   - Verify: Weapon restored to full effectiveness

### Failure Paths
4. **Service Denied (Bad Reputation)**
   - Have reputation -3 or lower
   - Attempt any service
   - Verify: Toran refuses service entirely
   - Verify: Dialog indicates distrust

### Edge Cases
5. **Salamander Companion Interest**
   - Enter market_square with salamander companion
   - Talk to Toran
   - Verify: Toran curious about fire creature
   - Verify: "Could use fire like that in the forge. Mind if I watch it work?"

6. **Damaged Weapon Assessment**
   - Present damaged weapon
   - Verify: Toran quotes repair cost based on damage level
   - Verify: 10g for minor, 20g for moderate, 30g for severe

## Dependencies
- **Items**:
  - Weapons: sword, silver_sword, dagger, crossbow
  - Armor: leather_armor, chain_shirt
- **Mechanics**:
  - Town reputation system
  - Weapon durability/repair system

## Walkthrough Files
- `test_toran_weapons.txt` - NEEDS CREATION

## Implementation Status
- [ ] Weapon sales
- [ ] Armor sales
- [ ] Weapon repair service
- [ ] Reputation -3 service refusal
- [ ] Salamander companion reaction

## Reference Implementation

This NPC demonstrates:
- **Vendor services**: Equipment sales and repairs
- **Reputation gate**: Service refusal at low reputation
- **Companion reactions**: Unique interaction with salamander
