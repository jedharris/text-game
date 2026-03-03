# Big Game Implementation Inventory

**Date**: 2025-12-29
**Purpose**: Comprehensive inventory of implemented vs. wired-up systems in big_game
**Context**: Foundation for infrastructure wiring implementation plan

---

## Executive Summary

This inventory reveals a significant gap between **infrastructure implementation** and **content wiring**. Most game systems are implemented and tested at the infrastructure level, but are not actually used in gameplay due to missing:

1. Hook registrations (vocabulary entries)
2. Content configurations (commitment_configs, etc.)
3. Item/equipment definitions
4. Handler implementations for key verbs (use, equip, trade)

**Key Finding**: The codebase is in a partially-migrated state due to the ongoing hook system redesign. Many handlers exist but are not registered in vocabulary.

---

## 1. Virtual Entity Infrastructure

### 1.1 Commitments

**Infrastructure**: ✅ Fully implemented
- Location: `examples/big_game/behaviors/shared/infrastructure/commitments.py`
- Handler: `on_turn_commitment` (per-entity dispatch)
- Hook: `turn_commitments` defined in vocabulary
- State management: Transitions between ACTIVE/FULFILLED/WITHDRAWN/ABANDONED

**Content**: ❌ NOT wired up
- Commitment configs in game_state.json: **NONE**
- Behavior modules that create commitments:
  - `aldric_rescue.py` - Calls `create_commitment("commit_aldric")`
  - `bear_cubs.py` - Calls `create_commitment("commit_bear_cubs")`
  - `sira_rescue.py` - Calls `create_commitment("commit_sira")`
  - `dual_rescue.py` - Calls `create_commitment("commit_garrett")` and `create_commitment("commit_delvan")`

**Gap**: All 5 commitment configs are referenced but **none exist** in `game_state.json extra.commitment_configs`

**Impact**:
- Cannot make promises to NPCs
- No deadline mechanics work
- No Echo trust changes from commitments
- No fulfillment/abandonment effects

**Walkthroughs**: None test commitment lifecycle

---

### 1.2 Scheduled Events

**Infrastructure**: ✅ Fully implemented
- Location: `examples/big_game/behaviors/shared/infrastructure/scheduled_events.py`
- Handler: `on_turn_scheduled_event` (per-entity dispatch)
- Hook: `turn_scheduled_events` defined in vocabulary
- State management: Fires events at trigger turn

**Content**: ❌ NOT wired up
- Scheduled events in game_state.json: **0**
- No behavior modules create scheduled events
- No event configurations exist

**Gap**: Infrastructure ready but zero usage

**Impact**:
- No timed game events (market days, patrols, environmental changes)
- No time-based NPC state transitions

**Walkthroughs**: None test scheduled events

---

### 1.3 Gossip

**Infrastructure**: ✅ Fully implemented
- Location: `examples/big_game/behaviors/shared/infrastructure/gossip.py`
- Handler: `on_turn_gossip` (per-entity dispatch)
- Hook: `turn_gossip_spread` defined in vocabulary
- Propagation: Point-to-point, broadcast, and network gossip

**Content**: ❌ NOT wired up
- Gossip entries in game_state.json: **0**
- Infrastructure module `examples/big_game/behaviors/regions/meridian_nexus/echo.py` has stub:
  ```python
  def on_echo_gossip(entity, accessor, context):
      # TODO: Handle gossip about player actions reaching Echo
      return EventResult(allow=True, feedback=None)
  ```
- No behavior modules create gossip

**Gap**: Infrastructure ready but zero usage

**Impact**:
- Information doesn't spread between NPCs
- No reputation system
- No confession windows (Sira-Elara mechanic)
- Echo doesn't learn about player actions indirectly

**Walkthroughs**: None test gossip propagation

---

### 1.4 Spreads

**Infrastructure**: ✅ Fully implemented
- Location: `examples/big_game/behaviors/shared/infrastructure/spreads.py`
- Handler: `on_turn_spread` (per-entity dispatch)
- Hook: `turn_condition_spread` defined in vocabulary
- Milestone application with halt flags

**Content**: ❌ NOT wired up
- Spreads in game_state.json: **0**
- No behavior modules create spreads
- No spread configurations exist

**Gap**: Infrastructure ready but zero usage

**Impact**:
- No fungal growth spreading from Fungal Depths
- No cold spreading from Frozen Reaches
- No water rising in Sunken District
- Environmental threats remain static

**Walkthroughs**: None test spreads

---

## 2. Regional Hazard Systems

### 2.1 Hypothermia (Frozen Reaches)

**Infrastructure**: ✅ Implemented
- Location: `examples/big_game/behaviors/regions/frozen_reaches/hypothermia.py`
- Handler: `on_cold_zone_turn` exists
- Uses conditions library correctly
- Severity progression: 20/40/60/80 tiers with messages
- Protection: Checks for salamander companion, cold_resistance_cloak, cold_weather_gear

**Hook Registration**: ✅ REGISTERED (likely during recent hook migration)
- Vocabulary present in file (needs verification)

**Damage**: ❌ NOT implemented
- Sets `severity` but **never sets `damage_per_turn`**
- No mechanical consequence to freezing

**Equipment**: ⚠️ Partially implemented
- Code checks for equipment properties
- Equipment items may not exist in game_state.json

**Content Gaps**:
- Need to verify cold_weather_gear, cold_resistance_cloak exist as items
- Need to verify salamander companion mechanics work
- Need to add damage scaling based on severity

**Walkthroughs**: ✅ `test_thermal_shock_combat_v2.txt` tests combat in cold, but not hypothermia progression/cure

**Blockers**: Issue #300 - Regional hazards don't deal damage

---

### 2.2 Fungal Infection (Fungal Depths)

**Infrastructure**: ✅ Implemented
- Location: `examples/big_game/behaviors/regions/fungal_depths/spore_zones.py`
- Handler: `on_spore_zone_turn` exists
- Uses conditions library correctly
- Severity progression: 20/40/60/80 tiers with messages
- Protection: Checks for breathing_mask, spore_resistance skill, safe_path_known flag

**Hook Registration**: ❌ NOT REGISTERED
- Vocabulary is **EMPTY**: `vocabulary: Dict[str, Any] = {"events": []}`
- Handler exists but is never called
- **This is the Phase 1 work that was lost in the reversion**

**Damage**: ❌ NOT implemented
- Sets `severity` but **never sets `damage_per_turn`**
- No mechanical consequence to infection

**Equipment**: ❌ NOT implemented
- Code checks for breathing_mask but no equip/wear verb exists
- breathing_mask item may not exist or be obtainable

**Content Gaps**:
- Must register `on_spore_zone_turn` to environmental_effect hook
- Must add damage scaling based on severity
- Must implement equip/wear command
- Must verify breathing_mask exists and is obtainable
- Must verify silvermoss cure works for player (currently only works for Aldric)

**Walkthroughs**:
- ✅ `test_fungal_depths.txt` - Tests Aldric's infection, NOT player infection
- ❌ `test_fungal_infection_basic.txt` - Created in Phase 1 but tests likely fail now

**Blockers**:
- Issue #300 - Regional hazards don't deal damage
- Phase 1 work lost - Hook not registered

---

### 2.3 Drowning (Sunken District)

**Infrastructure**: ✅ Implemented
- Location: `examples/big_game/behaviors/regions/sunken_district/drowning.py`
- Handler: `on_underwater_turn` exists
- Breath tracking: MAX_BREATH=12, damage at 0 breath
- Damage: DOES apply damage (20/turn when breath runs out)
- Protection: Checks for breathing equipment, gill equipment

**Hook Registration**: ❌ NOT REGISTERED
- Vocabulary is **EMPTY**: `vocabulary: Dict[str, Any] = {"events": []}`
- Handler exists but is never called

**Content Gaps**:
- Must register `on_underwater_turn` to environmental_effect hook
- Must verify underwater property gets set on locations/parts
- Must verify breathing equipment exists
- Must implement surface mechanic to reset breath

**Walkthroughs**: ❌ None

**Blockers**: Hook not registered

---

## 3. Equipment and Item Usage Systems

### 3.1 Equipment Slots

**Infrastructure**: ❌ NOT implemented
- No equip/wear/unequip verbs exist in core behaviors
- Code checks for `player.properties["equipment"]["face"]` etc.
- No equipment slot management system

**Content**: ❌ NOT implemented
- Items may have equipment properties but can't be worn

**Impact**:
- Cannot equip breathing_mask (needed for Fungal Depths)
- Cannot equip cold_weather_gear (needed for Frozen Reaches)
- Cannot equip any protective items

**Walkthroughs**: None test equipment

---

### 3.2 Item Use Verb

**Infrastructure**: ⚠️ Partially implemented
- Infrastructure reaction handler: `examples/big_game/behaviors/shared/infrastructure/item_use_reactions.py`
- No core "use" verb exists
- Items can have `item_use_reactions` that respond to being used

**Content**: ❌ NOT wired up
- silvermoss should be usable for self-healing but verb doesn't exist
- Other consumable items can't be used

**Impact**:
- Cannot use silvermoss on self (only give to NPCs)
- Cannot use any consumable items
- Cannot activate special items

**Walkthroughs**: None test item use

---

### 3.3 Trading System

**Infrastructure**: ✅ Fully implemented
- Location: `behavior_libraries/actor_lib/trading.py`
- Supports item-for-item exchanges
- Integrates with services.py

**Content**: ❌ NOT used
- No NPCs have `trades` configuration in game_state.json
- Myconid Elder ice-for-cure trade not configured
- Bee Queen flower-for-honey trade not configured

**Impact**:
- Cannot trade ice crystal for fungal cure
- Cannot trade flowers for honey
- Cannot use any bartering mechanics

**Walkthroughs**: None test trading

---

## 4. NPC Interaction Systems

### 4.1 Companion System

**Infrastructure**: ✅ Fully implemented
- Location: `behavior_libraries/companion_lib/following.py`
- Functions: `get_companions()`, `make_companion()`, `dismiss_companion()`
- Hook: `on_player_move_companions_follow()` exists
- Terrain/location restrictions supported

**Content**: ❌ NOT used
- No NPC has `is_companion: true` in game_state.json
- No behavior calls `make_companion()`
- Hook not registered (needs vocabulary entry)

**Impact**:
- Salamanders can't follow player
- Befriended wolves can't follow player
- Aldric can't become companion after rescue
- No companion mechanics work

**Walkthroughs**: None test companions

---

### 4.2 NPC Services

**Infrastructure**: ✅ Fully implemented
- Location: `behavior_libraries/actor_lib/services.py`
- Threshold-based service unlocking
- Gift acceptance tracking

**Content**: ⚠️ Partially used
- Aldric has teaching service configured (mycology)
- Other NPCs may have services but needs audit
- Service thresholds may not be configured

**Impact**:
- Teaching services may work for Aldric
- Other NPC services unknown status
- Needs comprehensive audit

**Walkthroughs**: None specifically test services

---

### 4.3 Gift Reactions

**Infrastructure**: ✅ Fully implemented
- Location: `examples/big_game/behaviors/shared/infrastructure/gift_reactions.py`
- Hook: `entity_gift_given` registered
- Dispatches to NPC-specific gift handlers

**Content**: ⚠️ Partially used
- Aldric has `on_receive_item` for silvermoss healing
- Other NPCs may have gift reactions but needs audit

**Impact**:
- Silvermoss healing for Aldric works
- Other gift mechanics unknown status

**Walkthroughs**: ✅ `test_fungal_depths.txt` tests giving silvermoss to Aldric

---

## 5. Condition System

**Infrastructure**: ✅ Fully implemented
- Location: `behavior_libraries/actor_lib/conditions.py`
- Functions: `apply_condition()`, `get_condition()`, `cure_condition()`
- Turn tick handler: `on_tick_conditions` applies `damage_per_turn`
- Hook: `turn_condition_tick` registered

**Content**: ⚠️ Partially working
- Health regeneration works (5 HP/turn for player)
- Aldric's fungal infection works (7 damage/turn, reducible to 2 with silvermoss)
- Regional hazards track severity but don't set damage_per_turn

**Gaps**:
- Hypothermia doesn't deal damage (only tracks severity)
- Fungal infection doesn't deal damage to player (handler not called)
- Drowning doesn't use condition system (uses custom breath_state)

**Walkthroughs**:
- ✅ `test_thermal_shock_combat_v2.txt` - Tests regeneration during combat
- ✅ Aldric's infection progression tested in fungal_depths walkthrough

---

## 6. Combat and Death Systems

**Infrastructure**: ✅ Implemented
- Combat handlers exist in behavior_libraries
- Death check: `turn_death_check` hook registered
- Death reactions: `entity_actor_died` hook registered

**Content**: ✅ Working
- Golem combat tested and working
- Death detection works
- Pack mirroring (wolves) works

**Walkthroughs**: ✅ Multiple combat walkthroughs pass

---

## 7. Missing Core Verbs

### Not Implemented:
1. **equip/wear** - Essential for protective gear
2. **unequip/remove** - Essential for gear management
3. **use** - Essential for consumable items
4. **trade/barter** - Essential for NPC trading
5. **confess** - Essential for gossip confession windows

### Partially Implemented:
1. **give** - Works via core manipulation, triggers gift reactions

---

## 8. Content Configuration Gaps

### Items Missing from game_state.json:
(Needs verification - may exist with different names)
1. breathing_mask (fungal_depths)
2. cold_weather_gear (frozen_reaches)
3. cold_resistance_cloak (frozen_reaches)
4. Second silvermoss (fungal_depths - only 1 exists)
5. myconid_cure (fungal_depths)
6. ice_crystal (frozen_reaches)
7. Breathing equipment for drowning (sunken_district)

### NPC Configurations Missing:
1. Commitment configs for all 5 commitments
2. Trade configs for Myconid Elder, Bee Queen
3. Companion configs for salamanders, wolves, Aldric
4. Service configs (needs audit - may partially exist)

---

## 9. Walkthrough Coverage

### Existing Walkthroughs:
1. ✅ `test_beast_wilds.txt` (47 commands) - Beast Wilds exploration, all NPCs
2. ✅ `test_fungal_depths.txt` (40 commands) - Fungal Depths with Aldric healing
3. ✅ `test_meridian_nexus.txt` (15 commands) - Nexus and observatory
4. ✅ `test_thermal_shock_combat_v2.txt` (74 lines) - Golem combat
5. ✅ `frozen_reaches_ice_caves_final.txt` - Ice extraction
6. ⚠️ `test_fungal_infection_basic.txt` - Created in Phase 1, status unknown

### Missing Walkthroughs:
1. ❌ Player infection progression (fungal_depths)
2. ❌ Hypothermia damage and cure (frozen_reaches)
3. ❌ Drowning mechanics (sunken_district)
4. ❌ Equipment usage (any region)
5. ❌ Item use/consumption (any region)
6. ❌ Trading mechanics (any region)
7. ❌ Companion following (any region)
8. ❌ Commitment lifecycle (any region)
9. ❌ Gossip propagation (cross-region)
10. ❌ Environmental spreads (cross-region)

---

## 10. Hook System Migration Status

**Context**: Ongoing hook system redesign (docs/designs/hook_system_redesign.md)

**Migration Status**:
- Infrastructure turn phases: Migrated to new hooks
- Core entity hooks: Partially migrated
- Regional hazard hooks: **NOT migrated** (spore_zones, drowning have empty vocabularies)

**Affected Systems**:
- Fungal infection: Handler exists but vocabulary empty
- Drowning: Handler exists but vocabulary empty
- Hypothermia: Status unclear (needs verification)

**This explains why Phase 1 work was lost** - the vocabulary registration was the key piece, and it's not present in current code.

---

## 11. Priority Classification

### Critical (Blocks basic gameplay):
1. **Register hazard turn phase hooks** (spore_zones, drowning)
2. **Add damage_per_turn to hazards** (hypothermia, fungal_infection)
3. **Implement equip/wear verbs** (blocks protective gear usage)
4. **Implement use verb** (blocks consumable items)
5. **Create commitment configs** (blocks all commitment mechanics)

### High (Needed for complete regional gameplay):
6. **Create equipment items** (breathing_mask, cold_weather_gear, etc.)
7. **Implement companion system** (salamanders, wolves)
8. **Implement trading system** (Myconid Elder, Bee Queen)
9. **Add second silvermoss** (needed for Aldric full cure)
10. **Verify and fix item locations** (ensure obtainable)

### Medium (Enriches gameplay):
11. **Implement gossip creation** (Sira-Elara, etc.)
12. **Implement scheduled events** (market days, patrols)
13. **Implement spreads** (fungal growth, cold spread, water rise)
14. **Add missing services configs** (needs audit first)
15. **Expand walkthroughs** (cover all mechanics)

### Low (Polish and completeness):
16. **Implement confess verb** (for gossip windows)
17. **Add more consumable items**
18. **Add more equipment variety**
19. **Comprehensive integration testing**

---

## 12. Estimated Scope

Based on this inventory, the infrastructure wiring work breaks down as:

**Part 1: Core Hazard Systems (8-12 hours)**
- Register hazard hooks (2 hours)
- Add damage scaling (2 hours)
- Implement equip/wear/use verbs (4 hours)
- Test with walkthroughs (2-4 hours)

**Part 2: Equipment and Items (6-8 hours)**
- Create missing items (2 hours)
- Create commitment configs (2 hours)
- Verify item locations/obtainability (2 hours)
- Test with walkthroughs (2 hours)

**Part 3: NPC Interaction Systems (8-10 hours)**
- Implement companion system (3 hours)
- Implement trading configs (2 hours)
- Audit and fix services (2 hours)
- Test with walkthroughs (2-3 hours)

**Part 4: Virtual Entity Content (10-12 hours)**
- Create gossip content (3 hours)
- Create scheduled events (3 hours)
- Create spread configs (3 hours)
- Test with walkthroughs (2-3 hours)

**Part 5: Integration and Polish (6-8 hours)**
- Cross-region testing (3 hours)
- Edge case handling (2 hours)
- Documentation updates (2-3 hours)

**Total Estimated: 38-50 hours** (significantly more than original 23-phase estimate because that assumed configs existed)

---

## Next Steps

1. **Validate this inventory** - Review with user
2. **Prioritize work** - Decide what's essential vs. nice-to-have
3. **Create phased plan** - Break into small, testable increments
4. **Start with critical path** - Hazard hooks + damage + basic verbs
5. **Test incrementally** - Walkthrough after every phase
