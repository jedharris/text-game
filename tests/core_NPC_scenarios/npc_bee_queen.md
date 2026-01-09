# NPC: bee_queen

## Core Mechanics
- gift_reactions: Accepts unique flower types for honey trade
- take_reactions: Prevents honey theft when not allied
- state_machine: neutral → trading → allied (or hostile)
- trust_state: Increases +1 per flower accepted
- cross-region collection: Flowers from 3 different regions required

## Required Scenarios

### Success Path
1. **Three-Flower Alliance**
   - Navigate to bee_queen_clearing
   - Give moonpetal (Civilized Remnants) → queen accepts
   - Verify: extra.bee_queen_flowers_traded = ["moonpetal"], trust = 1, state = trading
   - Give frost_lily (Frozen Reaches) → queen accepts
   - Verify: flowers_traded = ["moonpetal", "frost_lily"], trust = 2, state = trading
   - Give water_bloom (Sunken District) → queen accepts
   - Verify: flowers_traded = [...3 flowers], trust = 3, state = allied
   - Verify: Allied feedback mentions "no longer trader but ally"
   - Take royal_honey (should succeed now)
   - Verify: No hostile reaction, honey acquired

### Failure Paths
2. **Invalid Gift Rejection**
   - Give non-flower item (e.g., venison)
   - Verify: Rejection feedback "not what she seeks"
   - Verify: flowers_traded unchanged, trust unchanged

3. **Duplicate Flower Rejection**
   - Give moonpetal → accepted
   - Give moonpetal again
   - Verify: Rejection feedback "already received"
   - Verify: flowers_traded has only 1 moonpetal, trust +1 only once

4. **Theft Before Alliance**
   - Give 0-2 flowers (not allied yet)
   - Take royal_honey
   - Verify: Hostile reaction "furious buzzing", "hatred"
   - Verify: state_machine.current = hostile
   - Verify: extra.bee_trade_destroyed = true
   - Verify: Future trades blocked

### Edge Cases
5. **Partial Trade Sequence**
   - Give 1 flower
   - Talk to queen
   - Verify: Trading state dialog mentions remaining flowers needed
   - Give 2nd flower
   - Talk to queen
   - Verify: Dialog shows 1 more flower needed

6. **Theft After Alliance**
   - Complete 3-flower sequence (scenario 1)
   - Take royal_honey multiple times
   - Verify: No hostile reaction
   - Verify: Honey freely available to allied player

## Dependencies
- **Items**:
  - moonpetal (Civilized Remnants region)
  - frost_lily (Frozen Reaches region)
  - water_bloom (Sunken District region)
  - royal_honey (bee_queen_clearing, take_reactions configured)
- **NPCs**: None (bee_queen is self-contained)
- **Mechanics**:
  - gift_reactions infrastructure
  - take_reactions infrastructure
  - state_machine with neutral/trading/allied/hostile states
  - trust_state tracking

## Walkthrough Files
- `test_bee_queen.txt` (scenarios 2-4) - EXISTS, PASSING (infrastructure only)
- `test_bee_queen_alliance.txt` (scenario 1) - NEEDS CREATION (success path)
- `test_bee_queen_partial.txt` (scenario 5) - NEEDS CREATION (edge cases)
- `test_bee_queen_allied_theft.txt` (scenario 6) - NEEDS CREATION (post-alliance)

## Implementation Status
- [x] gift_reactions: Flower acceptance (bee_queen.py:29-145)
- [x] gift_reactions: Invalid gift rejection (bee_queen.py:69-77)
- [x] gift_reactions: Duplicate flower rejection (bee_queen.py:89-96)
- [x] gift_reactions: Trust increase per flower (bee_queen.py:119-124)
- [x] State transition: neutral → trading (bee_queen.py:112-113)
- [x] State transition: trading → allied (bee_queen.py:116-117)
- [x] take_reactions: Theft detection when not allied (bee_queen.py:148-200)
- [x] take_reactions: Theft allowed when allied (bee_queen.py:178-183)
- [x] Dialog reactions: State-based responses (bee_queen.py:203-296)
- [ ] Success walkthrough: 3-flower → allied → theft allowed
- [ ] Edge case walkthrough: Partial trade states
- [ ] Post-alliance walkthrough: Free honey access
