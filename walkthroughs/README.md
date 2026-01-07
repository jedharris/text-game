# Big Game Walkthroughs

Automated test walkthroughs for the big_game example. These validate game mechanics, region content, and integration points.

## Overview

- **Total active**: 37 walkthroughs
- **Total obsolete**: 12 (marked for archival)
- **Total assertions**: ~175 across active files

## Running Walkthroughs

```bash
# Run a single walkthrough
python3 tools/walkthrough.py walkthroughs/test_fungal_light_puzzle.txt

# Run with vitals display (shows HP, equipment, conditions each turn)
python3 tools/walkthrough.py walkthroughs/test_fungal_light_puzzle.txt --show-vitals

# Run all walkthroughs in region
for f in walkthroughs/test_fungal_*.txt; do python3 tools/walkthrough.py "$f"; done
```

## Walkthrough Syntax

```
# Comments start with # and are ignored
# EXPECT_FAIL: marks next command as expected to fail
# ASSERT <expression>: validates game state

# Example:
go west
take silvermoss
ASSERT items.silvermoss.location == "player"
give silvermoss to aldric
ASSERT actors.npc_aldric.properties.conditions.fungal_infection.severity < 50
```

## By Region

### Frozen Reaches (11 walkthroughs)

**Comprehensive:**
- `frozen_hypothermia.txt` (52 cmds, 17 asserts) - Hypothermia system, hot springs cure
- `frozen_observatory.txt` (68 cmds, 17 asserts) - Extreme cold, golem password solution
- `frozen_reaches_ice_caves_final.txt` (44 cmds) - Ice extraction, telescope repair

**Feature-Specific:**
- `frozen_golem_control_crystal.txt` (13 cmds, 4 asserts) - Control crystal solution
- `frozen_golem_ritual_offering.txt` (14 cmds, 2 asserts) - Ritual offering solution
- `test_salamander_companion.txt` (44 cmds, 6 asserts) - Companion activation
- `test_hypothermia_damage.txt` (37 cmds, 14 asserts) - Health damage validation
- `test_telescope_repair.txt` (25 cmds) - Component collection puzzle

**Navigation:**
- `frozen_test_observatory.txt` (8 cmds, 3 asserts) - Path verification
- `frozen_reaches_ice_caves.txt` (52 cmds) - Ice caves navigation

**Demos:**
- `vitals_demo.txt` (8 cmds) - Shows --show-vitals flag

### Fungal Depths (10 walkthroughs)

**Comprehensive:**
- `test_fungal_depths.txt` (40 cmds) - Full region test

**Aldric Rescue:**
- `test_aldric_immediate_rescue.txt` (23 cmds, 1 assert) - Immediate rescue path, health progression
- `test_aldric_health_progression.txt` (33 cmds, 3 asserts) - Delayed rescue, stabilization

**Light Puzzle:**
- `test_fungal_light_puzzle.txt` (17 cmds, 4 asserts) - Safe path (blue/gold mushrooms)
- `test_fungal_dangerous_mushrooms.txt` (18 cmds, 3 asserts) - Trap paths (violet/black mushrooms)

**Spore Mother:**
- `test_spore_mother_heal.txt` (16 cmds) - Heartmoss healing, allied state
- `test_spore_mother_wary_state.txt` (16 cmds, 3 asserts) - Hostile → wary → allied transitions

**Equipment:**
- `test_fungal_breathing_mask.txt` (21 cmds, 4 asserts) - Infection protection

**Basic Mechanics:**
- `test_fungal_infection_basic.txt` (21 cmds) - Player infection in spore zones
- `test_myconid_elder_dialog.txt` (7 cmds) - Dialog trust system

### Beast Wilds (5 walkthroughs)

**Comprehensive:**
- `test_beast_wilds.txt` (47 cmds) - Full region test

**Salamander System:**
- `test_salamander_companion.txt` (44 cmds, 6 asserts) - Trust → companion progression
- `test_salamander_communication.txt` (33 cmds) - Gesture dialogue
- `test_salamander_trust.txt` (23 cmds) - Fire gift mechanics
- `test_salamander_gestures.txt` (6 cmds) - Basic gesture validation

**Wolf Pack:**
- `test_wolf_feeding.txt` (5 cmds) - Venison gift to alpha

### Meridian Nexus (1 walkthrough)

- `test_meridian_nexus.txt` (15 cmds) - Echo dialog, basic hub functionality

### Infrastructure & Cross-Region (10 walkthroughs)

**Golem Puzzle (all 4 solutions):**
- `test_golem_password.txt` (27 cmds) - Password deactivation
- `test_golem_crystal.txt` (36 cmds) - Control crystal installation
- `test_golem_ritual.txt` (40 cmds) - Ritual offering
- `test_golem_combat.txt` (22 cmds) - Combat solution

**System Tests:**
- `test_equipment_system.txt` (18 cmds) - Use/remove verbs
- `test_gift_reaction.txt` (12 cmds) - Item reaction system
- `test_multi_item_take.txt` (23 cmds) - JSON protocol for multiple items
- `test_thermal_shock_combat_v2.txt` (30 cmds) - Temperature damage

**Framework:**
- `test_assertions.txt` (8 cmds, 6 asserts) - Assertion syntax validation
- `test_walkthrough_features.txt` (8 cmds) - Tool feature demo

## Status by Walkthrough

### Frozen Reaches
| File | Status | Commands | Asserts | Purpose |
|------|--------|----------|---------|---------|
| frozen_hypothermia.txt | ✅ PASSING | 52 | 17 | Hypothermia system |
| frozen_observatory.txt | ✅ PASSING | 68 | 17 | Extreme cold, golem password |
| frozen_reaches_ice_caves_final.txt | ✅ PASSING | 44 | 0 | Ice extraction, telescope |
| frozen_phase3_cold_protection.txt | ⚠️ ACTIVE | 19 | 10 | Cold gear protection |
| frozen_golem_control_crystal.txt | ✅ PASSING | 13 | 4 | Golem: control crystal |
| frozen_golem_ritual_offering.txt | ✅ PASSING | 14 | 2 | Golem: ritual offering |
| test_salamander_companion.txt | ✅ PASSING | 44 | 6 | Salamander companion |
| test_hypothermia_damage.txt | ✅ PASSING | 37 | 14 | Hypothermia damage |
| test_telescope_repair.txt | ⚠️ ACTIVE | 25 | 0 | Telescope puzzle |
| frozen_test_observatory.txt | ⚠️ ACTIVE | 8 | 3 | Navigation test |
| frozen_reaches_ice_caves.txt | ⚠️ ACTIVE | 52 | 0 | Ice caves (v1) |
| vitals_demo.txt | ⚠️ ACTIVE | 8 | 0 | Demo file |

### Fungal Depths
| File | Status | Commands | Asserts | Purpose |
|------|--------|----------|---------|---------|
| test_fungal_light_puzzle.txt | ✅ PASSING | 17 | 4 | Light puzzle safe path |
| test_fungal_dangerous_mushrooms.txt | ✅ PASSING | 18 | 3 | Light puzzle trap paths |
| test_spore_mother_wary_state.txt | ✅ PASSING | 16 | 3 | Spore Mother states |
| test_aldric_immediate_rescue.txt | ✅ PASSING | 23 | 1 | Aldric health progression |
| test_fungal_breathing_mask.txt | ❌ BLOCKED | 21 | 4 | Breathing mask (navigation issue) |
| test_spore_mother_heal.txt | ⚠️ ACTIVE | 16 | 0 | Spore Mother healing |
| test_aldric_health_progression.txt | ⚠️ ACTIVE | 33 | 3 | Aldric delayed rescue |
| test_fungal_depths.txt | ⚠️ ACTIVE | 40 | 0 | Full region |
| test_fungal_infection_basic.txt | ⚠️ ACTIVE | 21 | 0 | Basic infection |
| test_myconid_elder_dialog.txt | ⚠️ ACTIVE | 7 | 0 | Elder dialog |

### Beast Wilds
| File | Status | Commands | Asserts | Purpose |
|------|--------|----------|---------|---------|
| test_beast_wilds.txt | ⚠️ ACTIVE | 47 | 0 | Full region |
| test_salamander_communication.txt | ⚠️ ACTIVE | 33 | 0 | Gesture dialogue |
| test_salamander_gestures.txt | ⚠️ ACTIVE | 6 | 0 | Basic gestures |
| test_salamander_trust.txt | ⚠️ ACTIVE | 23 | 0 | Fire gifts |
| test_wolf_feeding.txt | ⚠️ ACTIVE | 5 | 0 | Wolf gift |

### Infrastructure
| File | Status | Commands | Asserts | Purpose |
|------|--------|----------|---------|---------|
| test_golem_password.txt | ⚠️ ACTIVE | 27 | 0 | Password solution |
| test_golem_crystal.txt | ⚠️ ACTIVE | 36 | 0 | Crystal solution |
| test_golem_ritual.txt | ⚠️ ACTIVE | 40 | 0 | Ritual solution |
| test_golem_combat.txt | ⚠️ ACTIVE | 22 | 0 | Combat solution |
| test_thermal_shock_combat_v2.txt | ⚠️ ACTIVE | 30 | 0 | Thermal damage |
| test_equipment_system.txt | ⚠️ ACTIVE | 18 | 0 | Use/remove |
| test_gift_reaction.txt | ⚠️ ACTIVE | 12 | 0 | Gift reactions |
| test_multi_item_take.txt | ⚠️ ACTIVE | 23 | 0 | Multi-item JSON |
| test_assertions.txt | ⚠️ ACTIVE | 8 | 6 | Assertion syntax |
| test_walkthrough_features.txt | ⚠️ ACTIVE | 8 | 0 | Tool features |
| test_meridian_nexus.txt | ⚠️ ACTIVE | 15 | 0 | Nexus/Echo |

Legend:
- ✅ PASSING: Confirmed working in recent testing
- ⚠️ ACTIVE: Not recently tested but not obsolete
- ❌ BLOCKED: Known issues preventing success
- 🗄️ OBSOLETE: Superseded or artifact file

## Obsolete Files (Candidates for Archival)

These 12 files are marked for removal or archival:

**Phase Tests** (7 files) - Superseded by comprehensive region tests:
- `phase1_fungal_damage.txt`
- `phase2_aldric_infection.txt`
- `phase3_treatment_cure.txt`
- `phase4_breathing_mask.txt`
- `phase5_environmental_hazards.txt`
- `phase6_player_death.txt`
- `frozen_phase3_cold_protection.txt`

**Versioned/Simplified** (1 file) - Superseded by main version:
- `frozen_hypothermia_simple.txt` (superseded by `frozen_hypothermia.txt`)

**Output Artifacts** (4 files) - Test output files, not walkthroughs:
- `frozen_reaches_test_commands.txt`
- `frozen_reaches_test_output.txt`
- `frozen_reaches_test_output_v2.txt`
- `frozen_reaches_test_output_v3.txt`

## Recommended Actions

1. **Archive obsolete files**: Move 12 obsolete files to `walkthroughs/archive/` subdirectory
2. **Run validation pass**: Execute all 37 active walkthroughs and document pass/fail status
3. **Update status markers**: Change ⚠️ to ✅ or ❌ based on validation results
4. **Create comprehensive tests**: Add end-to-end walkthroughs for:
   - Sunken District (no walkthroughs yet)
   - Civilized Remnants (no walkthroughs yet)
   - Cross-region integration (waystone, bee queen trade, etc.)

## Recent Additions (2026-01-03)

From Fungal Depths completion (Issue #386):
- `test_fungal_light_puzzle.txt` - Light puzzle safe path ✅
- `test_fungal_dangerous_mushrooms.txt` - Light puzzle trap paths ✅
- `test_spore_mother_wary_state.txt` - Spore Mother state transitions ✅
- `test_aldric_immediate_rescue.txt` - Aldric health progression ✅

From Frozen Reaches completion (Issue #340):
- `frozen_golem_control_crystal.txt` - Control crystal solution ✅
- `frozen_golem_ritual_offering.txt` - Ritual offering solution ✅
