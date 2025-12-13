# Infrastructure-to-Region Validation Matrix

**Date**: 2025-12-11
**Version**: 1.0
**Status**: Initial creation after Phase 2 consistency review

This document maps infrastructure APIs to their usage across regions, enabling validation that:
1. Each infrastructure capability is used correctly by regions
2. Each region's requirements are covered by infrastructure
3. Cross-region interactions are consistent

---

## Part 1: Infrastructure API to Region Usage Matrix

### 1.1 Commitment System

| API | Beast Wilds | Civilized Remnants | Sunken District | Fungal Depths | Frozen Reaches | Meridian Nexus |
|-----|-------------|-------------------|-----------------|---------------|----------------|----------------|
| `create_commitment()` | Sira, Bear Cubs, Bee Queen | — | Garrett, Delvan | Aldric, Spore Mother | — | — |
| `apply_hope_bonus()` | ✓ Sira (+4), Cubs (+5) | — | ✓ Delvan (+3), Garrett (no bonus) | ✓ Aldric (+10) | — | — |
| `check_commitment_deadline()` | ✓ | — | ✓ | ✓ | — | — |
| `fulfill_commitment()` | ✓ | — | ✓ | ✓ | — | — |
| `abandon_commitment()` | ✓ (trust penalty) | — | ✓ (partial credit) | ✓ (trust penalty) | — | — |
| `withdraw_commitment()` | — | — | — | — | — | — |

**Timer Trigger Types Used**:
| Trigger Type | Regions Using |
|--------------|---------------|
| `on_first_encounter` | Beast Wilds (Sira, Cubs), Fungal Depths (Aldric), Sunken District (Delvan) |
| `on_room_entry` | Sunken District (Garrett) |
| `on_commitment` | Fungal Depths (Aldric - verified in Phase 2) |

**Validation Notes**:
- Frozen Reaches has no timed commitments (salamander is soft commitment, no timer)
- Civilized Remnants has no direct commitments (council quests use different mechanism)
- Meridian Nexus has no commitments (Echo trust is separate system)

### 1.2 Trust System

| API | Beast Wilds | Civilized Remnants | Sunken District | Fungal Depths | Frozen Reaches | Meridian Nexus |
|-----|-------------|-------------------|-----------------|---------------|----------------|----------------|
| `get_trust()` | NPC trust | NPC trust, Shadow | NPC trust | Myconid Elder, Aldric | NPC trust | Echo trust |
| `modify_trust()` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `check_trust_threshold()` | Wolves (5), Bees (3) | Various services | — | Myconid services (3) | Golem (5) | Echo thresholds |

**Echo Trust Tiers** (from game_wide_rules.md):
| Trust Range | Echo Behavior | Appearance Chance |
|-------------|---------------|-------------------|
| +5 or above | Full cooperation, speaks name | 100% |
| 0 to +4 | Normal guidance | 25% base + 5%/point |
| -1 to -2 | Disappointed tone | 15% |
| -3 to -5 | Reluctant, cold | 5% |
| -6 or below | Refuses entirely | 0% |

### 1.3 Gossip System

| API | Beast Wilds | Civilized Remnants | Sunken District | Fungal Depths | Frozen Reaches | Meridian Nexus |
|-----|-------------|-------------------|-----------------|---------------|----------------|----------------|
| `create_gossip()` | Sira→Elara | Various | Delvan fate | Aldric fate | — | — |
| `create_broadcast_gossip()` | Rescue reputation | Rescue reputation | Rescue reputation | Spore Mother healed | — | — |
| `create_network_gossip()` | — | — | — | Spore network (1 turn) | — | — |
| `deliver_gossip()` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `confess_action()` | Sira→Elara (5 turns) | — | — | — | — | — |

**Gossip Timing** (from game_wide_rules.md):
| Type | Delay | Examples |
|------|-------|----------|
| Point-to-point | 3-5 turns | Sira fate → Elara, Aldric fate → scholars |
| Broadcast | 15-30 turns | Spore Mother healed → all regions |
| Network (spore) | 1 turn | Fungal creature killed → all fungal creatures |
| Network (criminal) | 2-3 turns | Delvan fate → undercity |

### 1.4 Companion System

| API | Beast Wilds | Civilized Remnants | Sunken District | Fungal Depths | Frozen Reaches | Meridian Nexus |
|-----|-------------|-------------------|-----------------|---------------|----------------|----------------|
| `check_companion_comfort()` | Home region | Cannot enter | Refuses swimming | Home region | Home region | Wolves can't enter |
| `companion_follow()` | ✓ Wolf pack | — | — | ✓ Myconid | ✓ Salamander | — |
| `companion_wait()` | ✓ | — | ✓ (survivor camp) | ✓ | ✓ | ✓ |
| `check_override_trigger()` | Spider gallery rescue | — | Salamander sacrifice | — | Wolf cold tolerance | — |
| `get_cold_protection()` | — | — | — | — | Salamander heat | — |

**Companion Restrictions Matrix** (from game_wide_rules.md):
| Companion | Cannot Enter | Uncomfortable In | Combat Debuff |
|-----------|--------------|------------------|---------------|
| Wolf Pack | Nexus, Civilized (guards attack) | Sunken (refuses swim) | Bitter cold zones (-1) |
| Salamander | Sunken (death) | — | — |
| Myconid | Frozen Reaches (cold damage) | — | — |

**Sub-Location Restrictions** (from game_wide_rules.md):
| Companion | Cannot Enter Sub-Locations |
|-----------|---------------------------|
| Wolves | Spider Nest Gallery, Spore Heart, Deep Roots |

### 1.5 Environmental System

| API | Beast Wilds | Civilized Remnants | Sunken District | Fungal Depths | Frozen Reaches | Meridian Nexus |
|-----|-------------|-------------------|-----------------|---------------|----------------|----------------|
| `get_zone_hazard()` | — | — | Water levels | Spore levels | Temperature zones | Safe zone |
| `apply_condition()` | — | — | Drowning | Infection | Hypothermia | — |
| `check_protection()` | — | — | Swimming skill | Mask, resistance | Gear, salamander | — |
| `check_spread_active()` | — | — | — | Spore spread (Turn 50+) | Cold spread (Turn 75+) | — |
| `halt_spread()` | — | — | — | Spore Mother healed | Telescope repaired | — |
| `apply_spread_effects()` | — | — | — | ✓ | ✓ | — |
| `get_spread_progress()` | — | — | — | ✓ | ✓ | — |

**Environmental Spreads**:
| Spread | Source Region | Affects | Timing | Halted By |
|--------|---------------|---------|--------|-----------|
| Spore | Fungal Depths | Adjacent regions | Turn 50+ | Healing Spore Mother |
| Cold | Frozen Reaches | Adjacent regions | Turn 75+ | Repairing telescope |

### 1.6 Condition System

| Condition | Source Regions | Treatment | Thresholds |
|-----------|----------------|-----------|------------|
| Hypothermia | Frozen Reaches | Hot springs, normal zone | 30/60/80/100 |
| Drowning | Sunken District | Surface, breath items | Breath depleted |
| Fungal Infection | Fungal Depths | Silvermoss, myconid cure | 20/40/60/80/100 |
| Bleeding | Beast Wilds, Sunken | Bandages | HP loss |

### 1.7 Puzzle System

| API | Beast Wilds | Civilized Remnants | Sunken District | Fungal Depths | Frozen Reaches | Meridian Nexus |
|-----|-------------|-------------------|-----------------|---------------|----------------|----------------|
| `check_puzzle_state()` | — | — | — | Mushroom light | Guardian deactivation | Crystal restoration |
| `attempt_puzzle_solution()` | — | — | — | ✓ | ✓ | ✓ |
| `get_puzzle_progress()` | — | — | — | ✓ | ✓ | ✓ |

---

## Part 2: Region Requirements to Infrastructure Coverage

### 2.1 Beast Wilds Requirements

| Requirement | Infrastructure Coverage | Status |
|-------------|------------------------|--------|
| Sira rescue with 8-turn timer | Commitment System | ✓ Covered |
| Bear cubs rescue with 30-turn timer | Commitment System | ✓ Covered |
| Bee Queen trade (moonpetal → royal honey) | Basic item exchange | ✓ Covered |
| Wolf pack befriending (trust 5) | Trust System | ✓ Covered |
| Wolf spider gallery override | Companion Override | ✓ Covered |
| Sira-Elara gossip (5-turn confession) | Gossip System | ✓ Covered |
| Pack territorial balance | **Custom behavior needed** | Documented |

### 2.2 Civilized Remnants Requirements

| Requirement | Infrastructure Coverage | Status |
|-------------|------------------------|--------|
| Town reputation (-10 to +10) | Trust/Reputation System | ✓ Covered |
| Council quest outcomes | **Custom behavior needed** | Documented |
| Exile system | **Custom behavior needed** | Documented |
| Undercity discovery risk (5%) | **Custom behavior needed** | Documented |
| Shadow NPC trust penalty | Trust System | ✓ Covered |
| Service trust gates | Trust System | ✓ Covered |
| Wolf exclusion (guards attack) | Companion System | ✓ Covered |
| Salamander incident risk | Companion System | ✓ Covered |

### 2.3 Sunken District Requirements

| Requirement | Infrastructure Coverage | Status |
|-------------|------------------------|--------|
| Garrett rescue (5-turn physics timer) | Commitment System | ✓ Covered |
| Delvan rescue (10+3 timer) | Commitment System | ✓ Covered |
| Water zone hazards | Environmental System | ✓ Covered |
| Breath tracking | Condition System | ✓ Covered |
| Swimming skill gates | Skill System (game-specific) | Documented |
| Delvan black market mechanism | Trust + Flag System | ✓ Covered |
| Partial credit for both rescues | Commitment System | ✓ Covered |

### 2.4 Fungal Depths Requirements

| Requirement | Infrastructure Coverage | Status |
|-------------|------------------------|--------|
| Aldric rescue (50+10 timer) | Commitment System | ✓ Covered |
| Spore Mother healing | Flag System | ✓ Covered |
| Spore spread (Turn 50+) | Environmental System | ✓ Covered |
| Spore network gossip (1 turn) | Network Gossip | ✓ Covered |
| Fungal infection progression | Condition System | ✓ Covered |
| Mushroom light puzzle | Puzzle System | ✓ Covered |
| Myconid companion | Companion System | ✓ Covered |

### 2.5 Frozen Reaches Requirements

| Requirement | Infrastructure Coverage | Status |
|-------------|------------------------|--------|
| Temperature zones | Environmental System | ✓ Covered |
| Hypothermia tracking | Condition System | ✓ Covered |
| Salamander soft commitment | Commitment System (null timer) | ✓ Covered |
| Salamander heat aura | Companion System | ✓ Covered |
| Guardian deactivation puzzle | Puzzle System | ✓ Covered |
| Cold spread (Turn 75+) | Environmental System | ✓ Covered |
| Wolf cold tolerance debuff | Companion System | ✓ Covered |
| Telescope repair (halts cold) | Flag System | ✓ Covered |

### 2.6 Meridian Nexus Requirements

| Requirement | Infrastructure Coverage | Status |
|-------------|------------------------|--------|
| Echo trust (-6 to +10) | Trust System | ✓ Covered |
| Echo appearance probability | **Custom behavior needed** | Documented |
| Crystal garden restoration | Progress Tracking | ✓ Covered |
| Waystone fragment tracking | Flag System | ✓ Covered |
| Ending determination | Ending System | ✓ Covered |
| Safe zone (no hazards) | Environmental System | ✓ Covered |
| Wolf exclusion (wards) | Companion System | ✓ Covered |

---

## Part 3: Cross-Region Interaction Validation

### 3.1 Import/Export Consistency

| Item | Exported From | Imported By | Verified |
|------|---------------|-------------|----------|
| Moonpetal | Civilized Remnants (1.3) | Beast Wilds (3.5) | ✓ Phase 2 |
| Royal Honey | Beast Wilds (2.2) | All regions | ✓ |
| Silvermoss | Fungal Depths (2.2) | Beast Wilds, Civilized | ✓ |
| Fire Crystal | Frozen Reaches (2.2) | Nexus | ✓ Phase 2 |
| Spore Heart (live) | Fungal Depths (2.2) | Nexus | ✓ Phase 2 |
| Cold Weather Gear | Civilized Remnants (2.2) | Frozen Reaches | ✓ |
| Bandages | Civilized Remnants (2.2) | All regions | ✓ Phase 2 |
| Breathing Mask | Civilized Remnants (2.2) | Fungal Depths | ✓ |
| Town Seal | Civilized Remnants (8.2) | All regions (faction ID) | ✓ Phase 2 |
| Cleaning Supplies | Civilized Remnants (2.2) | Frozen Reaches (1.3) | ✓ Phase 1 |

### 3.2 Gossip Propagation Validation

| Event | Source | Targets | Timing | Type | Verified |
|-------|--------|---------|--------|------|----------|
| Sira abandoned | Beast Wilds | Elara (CR) | 3-5 turns | Point-to-point | ✓ |
| Spore Mother healed | Fungal Depths | All regions | 15 turns | Broadcast | ✓ |
| Spore Mother killed | Fungal Depths | All fungal + Echo | 1 turn | Network | ✓ |
| Aldric fate | Fungal Depths | Echo + scholars | 3-5 turns | Point-to-point | ✓ Phase 2 |
| Delvan fate | Sunken District | Undercity | 2-3 turns | Network (criminal) | ✓ |
| Rescue reputation | Any | All regions | 20-30 turns | Broadcast | ✓ |
| Violence reputation | Any | All regions | 20-30 turns | Broadcast | ✓ |

### 3.3 World State Change Validation

| Event | Trigger | Global Flag | Effects Validated |
|-------|---------|-------------|-------------------|
| Waystone complete | 5 fragments placed | `waystone_complete` | ✓ Echo transforms, fast travel, spreads halt |
| Telescope repaired | Observatory functional | `observatory_functional` | ✓ Cold spread halts, crystal +1 |
| Spore Mother healed | Heartmoss applied | `spore_mother_healed` | ✓ Spore spread halts |
| Spore Mother killed | Player kills SM | `spore_mother_killed` | ✓ Network gossip, Echo penalty |

### 3.4 Companion Cross-Region Validation

| Companion | Home | Can Follow To | Cannot Enter | Validated |
|-----------|------|---------------|--------------|-----------|
| Wolf Pack | Beast Wilds | Fungal*, Frozen*, Sunken* | Nexus, Civilized | ✓ |
| Salamander | Frozen Reaches | Beast Wilds, Fungal, Civilized, Nexus | Sunken | ✓ |
| Myconid | Fungal Depths | Beast Wilds, Sunken, Civilized, Nexus | Frozen | ✓ Phase 2 |

*With restrictions documented in game_wide_rules.md

---

## Part 4: Further Validation Work Needed

### 4.1 Infrastructure to Region Mapping Update

**Status**: The existing `infrastructure_to_regions_mapping.md` is out of date.

**Required Work**:
1. Update all schema examples to match current infrastructure_detailed_design.md
2. Update gap analysis to reflect Phase 2 changes
3. Verify all "custom behavior modules needed" still apply
4. Cross-reference with this validation matrix
5. Mark systems now covered by infrastructure_detailed_design.md

**Estimated Scope**: Medium (review + updates to ~800 line document)

### 4.2 Type Consistency Checks

**Purpose**: Verify that types used in region designs match infrastructure types.

**Checks Needed**:

| Type | Infrastructure Definition | Check |
|------|--------------------------|-------|
| `CommitmentId` | `NewType('CommitmentId', str)` | All commitment IDs follow naming convention |
| `TurnNumber` | `NewType('TurnNumber', int)` | All turn values are integers |
| `GossipId` | `NewType('GossipId', str)` | All gossip IDs follow naming convention |
| `ActorId` | From engine types | All NPC references valid |
| `LocationId` | From engine types | All location references valid |
| `CommitmentState` | `StrEnum` with ACTIVE/FULFILLED/WITHDRAWN/ABANDONED | All states valid |
| `TemperatureZone` | `StrEnum` with NORMAL/COLD/FREEZING/EXTREME_COLD | All zones valid |
| `WaterLevel` | `StrEnum` with DRY/ANKLE/WAIST/CHEST/SUBMERGED | All levels valid |

**Estimated Scope**: Small (systematic review of region designs against type definitions)

### 4.3 Cross-Region Scenario Testing

**Purpose**: Validate multi-region player journeys produce consistent results.

**Scenarios to Test**:

1. **Commitment Chain**
   - Make commitment to Sira (Beast Wilds)
   - Travel to Civilized Remnants for supplies
   - Return in time vs. late
   - Verify gossip propagation to Elara

2. **Environmental Spread**
   - Reach Turn 50+ without healing Spore Mother
   - Verify spore spread affects Beast Wilds locations
   - Verify spread halts if Spore Mother healed
   - Verify crystal garden degradation

3. **Companion Journey**
   - Befriend wolf pack (Beast Wilds)
   - Attempt to enter Civilized Remnants (blocked)
   - Attempt to enter Nexus (blocked)
   - Verify wolves wait at appropriate locations

4. **Multi-Rescue Sequence**
   - Encounter Garrett (Sunken, 5-turn physics)
   - Encounter Delvan (Sunken, 10+3 timer)
   - Save one, fail other
   - Verify partial credit applied correctly

5. **Trust Recovery**
   - Drop Echo trust to -3 (reluctant)
   - Perform positive actions
   - Verify +1/Nexus visit cap
   - Verify appearance chance changes

6. **Network Gossip**
   - Kill fungal creature in Fungal Depths
   - Verify all fungal creatures know (1 turn)
   - Verify Myconid Elder reaction

**Estimated Scope**: Large (requires game state simulation or test harness)

### 4.4 Edge Case Review

**Purpose**: Document and validate edge cases at system boundaries.

**Edge Cases to Review**:

| System | Edge Case | Expected Behavior | Validated |
|--------|-----------|-------------------|-----------|
| Commitment | Make commitment at turn 1 of deadline | Hope bonus still applies | Pending |
| Commitment | Withdraw then recommit | New timer, no penalty | Pending |
| Commitment | Target NPC dies before deadline | Commitment auto-fails, no penalty | Pending |
| Trust | Echo at exactly -3 | Reluctant tier (5% appearance) | Pending |
| Trust | Echo recovers from -6 to -2 | Full recovery possible | Pending |
| Gossip | Confession at exact window boundary | Gossip prevented | Pending |
| Gossip | Source NPC dies before delivery | Gossip still delivered | Pending |
| Companion | Wolf override triggers at 20% health | Override fires, costs wolves | Pending |
| Companion | Salamander enters water accidentally | Death, permanent loss | Pending |
| Environment | Player enters extreme cold with no protection | Rapid hypothermia | Pending |
| Environment | Player cured of infection, re-enters spore zone | Re-infection possible | Pending |

**Estimated Scope**: Medium (requires careful design review + edge case documentation)

### 4.5 Test Scenario Documentation

**Purpose**: Create concrete test scenarios for each infrastructure system.

**Format**: Each test scenario should include:
- **Setup**: Initial game state
- **Actions**: Player commands
- **Expected State Changes**: Flags, trust, conditions, gossip
- **Expected Narration Triggers**: What the LLM should know

**Scenarios Needed Per System**:

| System | Scenarios | Priority |
|--------|-----------|----------|
| Commitment | 8-10 (make, fulfill, abandon, withdraw, hope, partial credit) | High |
| Trust | 6-8 (gain, lose, threshold cross, recovery) | High |
| Gossip | 6-8 (point-to-point, broadcast, network, confession) | High |
| Companion | 8-10 (follow, wait, restrict, override, death) | Medium |
| Environment | 6-8 (zone entry, condition gain, protection, spread) | Medium |
| Puzzle | 4-6 (attempt, progress, solve, fail) | Low |

**Estimated Scope**: Large (40-50 detailed test scenarios)

---

## Part 5: Validation Checklist

### Phase 3 Validation (To Execute)

- [ ] Update infrastructure_to_regions_mapping.md
- [ ] Type consistency review
- [ ] Cross-region scenario documentation
- [ ] Edge case documentation
- [ ] Test scenario documentation (high priority systems first)

### Per-Region Validation (Complete)

- [x] Beast Wilds - Phase 2 complete
- [x] Civilized Remnants - Phase 2 complete
- [x] Sunken District - Phase 2 complete
- [x] Fungal Depths - Phase 2 complete
- [x] Frozen Reaches - Phase 2 complete
- [x] Meridian Nexus - Phase 2 complete

### Cross-Cutting Validation (Complete)

- [x] Timer format standardization (Phase 1.5)
- [x] Trust system alignment (Phase 2)
- [x] Companion restrictions (Phase 1.5 + Phase 2)
- [x] Import/export consistency (Phase 2)
- [x] Gossip API design (Phase 2)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2025-12-11 | Updated API names per infrastructure review: `apply_hope_bonus()`, `get_cold_protection()`, spread system APIs |
| 1.0 | 2025-12-11 | Initial creation after Phase 2 consistency review |
