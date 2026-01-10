# NPC: whisper

## Core Mechanics
- location: undercity (requires discovery)
- services: Sell NPC secrets, location secrets, valuable secrets
- information_value: Can be used for manipulation OR empathy
- discovery_risk: 5% per service

## Required Scenarios

### Success Paths
1. **Purchase NPC Secrets**
   - Navigate to undercity
   - Talk to whisper
   - Purchase NPC secret (20g)
   - Verify: Weaknesses, backstories, or hidden motivations revealed
   - Examples: Hurst's family tragedy, Varn's corruption
   - Verify: 5% discovery risk

2. **Purchase Location Secrets**
   - Purchase location secret (30g)
   - Verify: Hidden paths, treasure locations, or dangers revealed
   - Verify: Useful gameplay information

3. **Purchase Valuable Secrets**
   - Purchase valuable secret (40-100g)
   - Examples: Varn's undercity connection, hidden entrances
   - Verify: Major game-relevant information
   - Verify: Can affect relationships and choices

### Information Uses
4. **Empathy Path**
   - Learn Hurst's family tragedy
   - Approach Hurst with sympathy
   - Verify: Can build trust through understanding
   - Verify: Information used constructively

5. **Manipulation Path**
   - Learn Varn's corruption
   - Confront Varn or use as leverage
   - Verify: Can blackmail or expose
   - Verify: Different consequences per approach

6. **Undercity Entrance Information**
   - Purchase undercity entrance location
   - Verify: Alternative discovery method to Vex trust
   - Verify: Sets knows_undercity_entrance flag

### Edge Cases
7. **Branded Player Treatment**
   - Player is branded
   - Enter undercity
   - Verify: Whisper offers MORE information
   - Verify: "Sees opportunity in your situation"
   - Verify: May offer secrets about redemption paths

8. **Repeat Purchase Same Secret**
   - Try to buy same secret twice
   - Verify: Whisper notes already told
   - Verify: No charge for repeat information

9. **Secret About Self**
   - Ask about Whisper's own secrets
   - Verify: Deflection or high price
   - Verify: Maintains mystery

## Dependencies
- **NPCs**:
  - councilor_hurst (secret: family tragedy)
  - councilor_varn (secret: undercity connection)
  - Various NPCs (weaknesses and motivations)
- **Locations**:
  - undercity (required access)
  - Hidden paths throughout game (revealed by secrets)
- **Mechanics**:
  - Information purchase system
  - Discovery risk
  - Dual-use information (empathy/manipulation)

## Walkthrough Files
- `test_whisper_secrets.txt` - NEEDS CREATION

## Implementation Status
- [ ] NPC secrets for sale (20g)
- [ ] Location secrets for sale (30g)
- [ ] Valuable secrets for sale (40-100g)
- [ ] 5% discovery risk
- [ ] Information affects dialog options
- [ ] Branded player receives more offers

## Reference Implementation

This NPC demonstrates:
- **Information economy**: Secrets as purchasable commodity
- **Dual-use design**: Same information, different applications
- **Player agency**: Choose empathy or manipulation
- **Discovery risk**: Using undercity services has costs
