# NPC: curiosity_dealer_vex

## Core Mechanics
- dialog_reactions: Cryptic conversation, hints about "deeper market"
- services: Trade rare items, reveal undercity access
- trust_state: Based on rare item trades
- undercity_gatekeeper: Reveals entrance at trust 3+

## Required Scenarios

### Success Paths
1. **Basic Trade (Trust 0-1)**
   - Navigate to market_square
   - Talk to curiosity_dealer_vex
   - Verify: Basic trades available
   - Verify: No rare items offered
   - Verify: No undercity hints

2. **Rare Item Trade (Trust 2+)**
   - Build trust to 2 through transactions
   - Sell spider_silk, venom_sacs, ice_crystals, or ancient_artifacts
   - Verify: Trust increases +1 per rare item
   - Verify: Rare items become available for purchase
   - Verify: Hints about "deeper market" in dialog

3. **Undercity Access (Trust 3+)**
   - Build trust to 3
   - Verify: Vex reveals undercity entrance location
   - Verify: Knock pattern provided (3-pause-2)
   - Verify: knows_undercity_entrance flag set
   - Verify: Hidden exit to undercity now visible in market_square

### Edge Cases
4. **Trust Progression from Purchases**
   - Make purchases without selling rare items
   - Verify: Trust increases +0.25 per transaction
   - Verify: Slower path to trust 3

5. **Multiple Rare Item Sales**
   - Sell spider_silk (+1 trust)
   - Sell venom_sacs (+1 trust)
   - Sell ice_crystals (+1 trust)
   - Verify: Trust 3+ achieved
   - Verify: Undercity access available

6. **Delvan Connection**
   - If merchant_delvan rescued in Sunken District
   - Verify: Vex may mention Delvan as mutual contact
   - Verify: Alternative undercity access path via Delvan

## Dependencies
- **Items**:
  - spider_silk, venom_sacs, ice_crystals, ancient_artifacts (accepts)
  - Unusual rare items (sells at trust 2+)
- **NPCs**:
  - merchant_delvan (alternative undercity connection)
  - the_fence, whisper, shadow (undercity NPCs)
- **Mechanics**:
  - Trust progression system
  - Hidden exit reveal
  - knows_undercity_entrance flag

## Walkthrough Files
- `test_vex_rare_trades.txt` - NEEDS CREATION
- `test_vex_undercity_access.txt` - NEEDS CREATION

## Implementation Status
- [ ] Basic trade at trust 0-1
- [ ] Rare item trades at trust 2+
- [ ] Undercity location reveal at trust 3+
- [ ] Trust from rare item sales (+1)
- [ ] Trust from purchases (+0.25)
- [ ] knows_undercity_entrance flag

## Reference Implementation

This NPC demonstrates:
- **Tiered trust access**: Different services at different trust levels
- **Gatekeeper role**: Controls access to hidden area
- **Rare item economy**: Rewards exploration with trust currency
- **Cross-NPC connection**: Links to Delvan from Sunken District
