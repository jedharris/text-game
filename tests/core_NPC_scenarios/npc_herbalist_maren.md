# NPC: herbalist_maren

## Core Mechanics
- dialog_reactions: Trade conversation, herbalism teaching
- services: Sell healing items, buy plants, teach basic herbalism
- trust_state: Based on transactions and town reputation
- reputation_effects: Prices vary with reputation

## Required Scenarios

### Success Paths
1. **Basic Trade**
   - Navigate to market_square
   - Talk to herbalist_maren
   - Purchase healing_potion (15g), antidote (20g), or bandages (5g)
   - Verify: Transaction completes
   - Verify: Items added to inventory
   - Verify: Trust increases +0.5

2. **Sell Plants**
   - Have rare herbs, nightshade, or moonpetal
   - Sell to Maren
   - Verify: Fair market value received
   - Verify: Trust increases +0.5 per rare plant

3. **Learn Basic Herbalism**
   - Build trust to 2+ (through transactions or reputation)
   - Pay 50g OR provide rare plant
   - Verify: basic_herbalism skill granted
   - Verify: Can identify dangerous plants
   - Verify: Can safely handle most herbs (not nightshade)
   - Verify: Supervised access to Elara's garden unlocked

### Failure Paths
4. **Teaching Denied (Low Trust)**
   - Trust below 2
   - Ask to learn herbalism
   - Verify: Teaching refused
   - Verify: Hint to build trust through transactions

5. **Service Denied (Bad Reputation)**
   - Have reputation -3 or lower
   - Attempt any service
   - Verify: Prices increased 20%
   - At reputation -3 for Toran (Maren still serves at higher prices)

### Edge Cases
6. **Reputation Price Adjustment**
   - Have good reputation (2+)
   - Purchase item
   - Verify: -10% discount applied
   - Have bad reputation (-2 to -4)
   - Purchase item
   - Verify: +20% markup applied

7. **Trust from Town Reputation**
   - Trust partially mirrors town reputation /2
   - High town rep contributes to Maren trust
   - Verify: Trust calculation includes reputation component

8. **Branded Player**
   - Player has branded flag
   - Approach Maren
   - Verify: Won't meet eyes
   - Verify: Doubled prices
   - Verify: Teaching unavailable

## Dependencies
- **Items**:
  - healing_potion, antidote, bandages (sells)
  - rare herbs, nightshade, moonpetal (buys)
- **NPCs**:
  - healer_elara (garden access requires Maren OR Elara trust)
- **Mechanics**:
  - Trust system
  - Town reputation system
  - Basic herbalism skill
  - Branding effects

## Walkthrough Files
- `test_maren_trade.txt` - NEEDS CREATION
- `test_maren_herbalism.txt` - NEEDS CREATION

## Implementation Status
- [ ] Trade services (buy/sell)
- [ ] Trust progression via transactions
- [ ] Basic herbalism teaching at trust 2
- [ ] Reputation-based price adjustment
- [ ] Branding effects (doubled prices, no teaching)

## Reference Implementation

This NPC demonstrates:
- **Vendor services**: Buy and sell goods
- **Skill teaching**: Basic herbalism at trust gate
- **Trust from transactions**: Commerce builds relationship
- **Reputation-aware pricing**: Discounts and markups
- **Two-tier skill progression**: Basic (Maren) → Advanced (Elara)
