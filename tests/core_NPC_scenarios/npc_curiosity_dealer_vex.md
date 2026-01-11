# NPC: curiosity_dealer_vex

## Core Mechanics
- dialog_reactions: Cryptic conversation about rare items and secrets
- services: Trade rare items, sell information
- trust_state: Based on rare item trades
- gift_reactions: Accepts curiosities for trust

## Required Scenarios

### Success Paths
1. **Basic Trade (Trust 0-1)**
   - Navigate to market_square
   - Talk to curiosity_dealer_vex
   - Verify: Basic trades available
   - Verify: No rare items offered
   - Verify: Limited information available

2. **Rare Item Trade (Trust 2+)**
   - Build trust to 2 through transactions
   - Sell spider_silk, venom_sacs, ice_crystals, or ancient_artifacts
   - Verify: Trust increases +1 per rare item
   - Verify: Rare items become available for purchase
   - Verify: More information available for sale

3. **Information Broker (Trust 2+)**
   - Build trust to 2
   - Ask about "information" or "secrets"
   - Verify: Can purchase information about NPCs, locations, weaknesses
   - Verify: Information costs gold

### Edge Cases
4. **Trust Progression from Purchases**
   - Make purchases without selling rare items
   - Verify: Trust increases +0.25 per transaction
   - Verify: Slower path to trust 2+

5. **Multiple Rare Item Sales**
   - Sell spider_silk (+1 trust)
   - Sell venom_sacs (+1 trust)
   - Sell ice_crystals (+1 trust)
   - Verify: Trust 3+ achieved
   - Verify: All services available

6. **Gift Curiosities**
   - Give strange_artifact or mysterious_object to Vex
   - Verify: Trust increases based on item rarity
   - Verify: Appropriate gratitude dialog

## Dependencies
- **Items**:
  - spider_silk, venom_sacs, ice_crystals, ancient_artifacts (accepts)
  - strange_artifact, mysterious_object (gift items)
  - Unusual rare items (sells at trust 2+)
- **NPCs**: None required
- **Mechanics**:
  - Trust progression system
  - Gift reactions
  - Information selling

## Walkthrough Files
- `test_vex_rare_trades.txt` - NEEDS CREATION
- `test_vex_information.txt` - NEEDS CREATION

## Implementation Status
- [x] Basic trade at trust 0-1 (vex.py)
- [x] Rare item trades at trust 2+ (vex.py)
- [x] Information broker at trust 2+ (vex.py)
- [x] Trust from rare item sales (+1) (vex.py)
- [x] Trust from purchases (+0.25) (vex.py)
- [x] Gift reactions for curiosities (vex.py)

## Reference Implementation

This NPC demonstrates:
- **Tiered trust access**: Different services at different trust levels
- **Rare item economy**: Rewards exploration with trust currency
- **Information broker**: Sells secrets for gold (trust-gated)
