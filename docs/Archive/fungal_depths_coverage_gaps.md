# Fungal Depths Walkthrough - Coverage Gaps

## Current Coverage (test_fungal_depths.txt - 40 commands)

### ✅ What Works
1. **Aldric Dialog** - All topics accessible
2. **Light Puzzle** - Mushroom watering mechanics
3. **Silvermoss Healing** - Fixed! Now reduces Aldric's damage from 7 to 2 HP/turn
4. **Myconid Elder Dialog** - All topics accessible
5. **Spore Mother Encounter** - Empathic communication works
6. **Gift Exchange** - Notebook to Aldric

### ❌ What's Missing

#### 1. Player Infection (Critical Gap)
**Problem**: Player never gets infected despite walking through high spore zones
**Root Cause**: `on_spore_zone_turn()` handler not hooked up to turn phases
**Impact**: Can't test:
- Spore severity progression (20/40/60/80 tier messages)
- Breathing mask protection
- Safe path knowledge reducing infection rate
- Spore resistance skill (50% reduction)
- Silvermoss curing player (only tested on Aldric)

**Locations with spore_level**:
- cavern_entrance: none
- luminous_grotto: medium (rate: 5/turn)
- spore_heart: high (rate: 10/turn)
- myconid_sanctuary: none

#### 2. Equipment Mechanics
**Problem**: Items are collected but never worn/equipped
**Items obtained**:
- Spore lantern (taken, never used)
- Breathing mask (taken, never equipped)

**Missing**:
- Equip/wear command for breathing mask
- Light level changes from spore lantern
- Visual confirmation of protection

#### 3. Self-Treatment
**Problem**: Can only give silvermoss to NPCs, not use on self
**Missing**:
- "use silvermoss" command for self-healing
- "eat silvermoss" alternative
- Cure message for player

#### 4. Condition Damage
**Problem**: Even if infection worked, it wouldn't deal damage (Issue #300)
**Root Cause**: `spore_zones.py` never sets `damage_per_turn`
**Missing**:
- Damage scaling with severity tiers
- Health loss from infection
- Death risk from high spore exposure

#### 5. Second Silvermoss Dose
**Problem**: Aldric's healing expects 2 doses but only 1 exists
**Code says**: "One more dose, or the Myconid's remedy, would heal me completely"
**Reality**: Only 1 silvermoss in luminous_grotto
**Missing**:
- Second silvermoss location OR
- Alternative cure path via Myconids

#### 6. Myconid Cure Path
**Problem**: Elder mentions cure but no way to obtain it
**Elder says**: "Ice-crystal cools the cure-making... Bring ice from the frozen heights"
**Missing**:
- Trading ice for cure
- Giving cure to Aldric
- Spore Mother healing (alternative path)

#### 7. Safe Path Knowledge
**Feature exists**: `safe_path_known` flag reduces high spore rate from 10 to 3
**Missing**:
- How player discovers safe path
- Where it's taught/revealed
- Testing that it actually works

## Recommended Fixes

### Phase 1: Hook Up Core Systems (Issue #300)
1. Register `on_spore_zone_turn` to turn phase hook
2. Add `damage_per_turn` scaling with severity
3. Test infection accumulation

### Phase 2: Equipment System
1. Implement equip/wear command
2. Make breathing mask provide immunity when equipped
3. Make spore lantern affect light levels

### Phase 3: Self-Treatment
1. Add "use <item>" verb
2. Route silvermoss use to healing logic
3. Support player as target

### Phase 4: Expand Walkthrough
```
# Part 7: Player Infection Test (new)

# Enter medium spore zone without protection
# (luminous grotto, rate 5/turn)
go down
look
# Expected: "You cough as spores irritate your lungs." (after reaching severity 20)

# Accumulate severity via exploration
examine mushrooms
look around
inventory
# Expected: Progressively worse messages at 40/60/80 severity

# Show damage is being dealt
# Expected: HP decreasing, infection messages

# Equip breathing mask
wear mask
# Expected: "You fit the breathing mask. The filtered air is a relief."

# Verify protection
go down  # Enter high spore zone (spore_heart)
look
# Expected: No infection message, severity stops increasing

# Return and get second silvermoss
go up
take silvermoss
# (Need to place second silvermoss in world)

# Cure self
use silvermoss
# Expected: Cure message, severity reduced or removed

# Verify cure
look
# Expected: No infection messages
```

### Phase 5: Complete Cure Paths
1. **Option A**: Second silvermoss location
   - Add silvermoss to myconid_sanctuary as reward
   - Or deeper fungal caverns

2. **Option B**: Myconid cure trade
   - Get ice from Frozen Reaches
   - Trade to Elder for cure
   - Use cure on self or Aldric

3. **Option C**: Spore Mother healing
   - Gain her trust (unclear how)
   - Request healing
   - Receive cure

## Testing Requirements

To fully validate Fungal Depths, we need:
1. ✅ NPC infection (Aldric) - VALIDATED
2. ❌ Player infection progression
3. ❌ Equipment protection mechanics
4. ❌ Self-treatment with items
5. ❌ Multiple cure paths
6. ❌ Damage from infection (requires #300)
7. ❌ Death from untreated infection

## Current Status

**Coverage**: ~40% of intended mechanics
- Dialog/narrative: ✅ Good
- Puzzle mechanics: ✅ Good
- Infection system: ❌ Not hooked up
- Equipment: ❌ Not functional
- Cure paths: ⚠️ Partial (NPC only)

**Blockers**:
1. Issue #300 - Hazards need damage hookup
2. Issue #301 - Equipment/trading systems not used
3. Missing verbs: wear/equip, use
4. Missing content: second silvermoss, cure items

**Recommendation**: Fix #300 first (damage hookup), then expand walkthrough to test player infection while tuning damage values.
