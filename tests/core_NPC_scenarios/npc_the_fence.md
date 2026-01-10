# NPC: the_fence

## Core Mechanics
- location: undercity (requires discovery)
- services: Buy any items (50% value), sell contraband
- no_trust_gate: Services always available in undercity
- discovery_risk: 5% per service contributes to town reputation damage

## Required Scenarios

### Success Paths
1. **Sell Stolen/Any Items**
   - Discover undercity entrance
   - Navigate to undercity
   - Talk to the_fence
   - Sell any item
   - Verify: 50% of normal value received
   - Verify: No questions asked
   - Verify: 5% discovery risk

2. **Purchase Contraband**
   - Navigate to undercity
   - Talk to the_fence
   - Purchase lockpicks (30g), poison (50g), or disguise_kit (40g)
   - Verify: Items added to inventory
   - Verify: 5% discovery risk per transaction

### Failure Paths
3. **Discovery Consequences**
   - Use services multiple times
   - Roll discovery (5% per service)
   - If discovered:
   - Verify: Town reputation -2
   - Verify: 3+ discoveries leads to branding

### Edge Cases
4. **Branded Player Interaction**
   - Player is branded
   - Enter undercity
   - Verify: Fence treats player normally
   - Verify: "Business is business" attitude
   - Verify: Prices unchanged

5. **Sell Valuable Quest Items**
   - Attempt to sell quest-critical items
   - Verify: Fence accepts (no questions)
   - Verify: Player loses item permanently
   - Note: This can break quests - player choice

6. **Multiple Transactions Same Visit**
   - Sell item (5% risk)
   - Buy item (5% risk)
   - Sell another item (5% risk)
   - Verify: Each transaction has independent discovery chance
   - Verify: Cumulative risk per undercity visit

## Dependencies
- **Items**:
  - lockpicks, poison, disguise_kit (sells)
  - Any item (buys at 50%)
- **Locations**:
  - undercity (requires discovery via Vex, Delvan, or overhearing)
- **Mechanics**:
  - Undercity discovery system
  - Discovery risk per service
  - Town reputation damage on discovery

## Walkthrough Files
- `test_undercity_fence.txt` - NEEDS CREATION

## Implementation Status
- [ ] Buy any items at 50% value
- [ ] Sell contraband (lockpicks, poison, disguise_kit)
- [ ] 5% discovery risk per service
- [ ] Discovery reduces town reputation -2
- [ ] Branded player normal treatment

## Reference Implementation

This NPC demonstrates:
- **Criminal vendor**: No-questions commerce
- **Discovery risk**: Cumulative reputation danger
- **Business pragmatism**: Treats all players equally
- **Player agency**: Can sell quest items (with consequences)
