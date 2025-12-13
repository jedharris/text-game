# Big Game Functional Testing Plan

This document outlines the functional testing plan for "The Shattered Meridian" (big_game).

## Goals

1. **Move tests to proper location** - Migrate `test_big_game.py` from the example directory to `tests/` following the established pattern
2. **Fix known test failures** - Address the 4 currently failing tests
3. **Comprehensive functional coverage** - Test all game systems individually to ensure they work correctly
4. **Clean implementation** - Fix any implementation issues discovered during testing

---

## Current State

### Test Organization Issues

The big_game tests are split across two locations:
- `examples/big_game/test_big_game.py` - 51 comprehensive tests (should be moved)
- `tests/test_big_game_scenarios.py` + `tests/_big_game_scenarios_impl.py` - 23 scenario tests (proper location)

This violates the project convention where all tests belong in `tests/`.

### Current Test Failures (4)

| Test | Error | Root Cause |
|------|-------|------------|
| `test_faction_disposition_changes_with_trust` | Disposition stays "neutral" | Faction representative actors don't exist (e.g., `faction_myconid`) |
| `test_all_faction_representatives_exist` | Representatives not found | Same - faction representatives not created in actor data |
| `test_check_ending_conditions_initial_state` | Expected 2 purified, got 0 | `check_ending_conditions` only checks 3 regions (fungal, beast, frozen) but test expects meridian_nexus and civilized_remnants to count |
| `test_location_exits_are_bidirectional` | Error parsing exits | Test code treats ExitDescriptor as dict, using `.get("to")` instead of `.to` |

---

## Phase 1: Test Infrastructure Setup

### 1.1 Move Tests to tests/ Directory

Move `examples/big_game/test_big_game.py` content into the standard test structure:
- Create `tests/test_big_game_functional.py` (subprocess wrapper)
- Create `tests/_big_game_functional_impl.py` (actual test implementations)

Follow the existing pattern from `test_big_game_scenarios.py`.

### 1.2 Consolidate Test Files

After moving, we'll have:
- `tests/test_big_game_scenarios.py` - Scenario/gameplay tests (existing)
- `tests/test_big_game_functional.py` - Functional unit tests (new, from moved file)

Consider whether to merge these or keep separate based on test isolation needs.

---

## Phase 2: Fix Known Test Failures

### 2.1 Create Missing Faction Representative Actors

Add missing faction representative actors to appropriate files. These are "virtual actors" that represent faction collective will (see Appendix A for details).

**fungal_actors.json - add:**
```json
{
  "id": "faction_myconid",
  "name": "Myconid Collective",
  "description": "The collective will of the Myconid colony, expressed through silent spore-communion.",
  "location": "loc_fd_myconid_sanctuary",
  "inventory": [],
  "properties": {
    "is_faction": true,
    "can_be_attacked": false,
    "relationships": {"player": {"trust": 0, "gratitude": 0, "fear": 0}}
  },
  "behaviors": []
}
```

**beast_actors.json - add:**
```json
{
  "id": "faction_beasts",
  "name": "Beast Spirits",
  "description": "The awakened consciousness of the Beast Wilds, felt as a presence in the den.",
  "location": "loc_bw_predator_den",
  "inventory": [],
  "properties": {
    "is_faction": true,
    "can_be_attacked": false,
    "relationships": {"player": {"trust": 0, "gratitude": 0, "fear": 0}}
  },
  "behaviors": []
}
```

**frozen_actors.json - add:**
```json
{
  "id": "faction_frozen",
  "name": "Frozen Keepers",
  "description": "The ancient guardians of the Frozen Reaches, their will preserved in ice and stone.",
  "location": "loc_fr_temple_sanctum",
  "inventory": [],
  "properties": {
    "is_faction": true,
    "can_be_attacked": false,
    "relationships": {"player": {"trust": 0, "gratitude": 0, "fear": 0}}
  },
  "behaviors": []
}
```

Note: `faction_council` already exists in `town_actors.json`.

### 2.2 Fix ExitDescriptor Test

In `test_location_exits_are_bidirectional`, change:
```python
dest_id = exit_data.get("to") if isinstance(exit_data, dict) else exit_data
```
to:
```python
dest_id = exit_data.to if hasattr(exit_data, 'to') else exit_data
```

### 2.3 Fix `check_ending_conditions` Region Count

**Decision:** Update the test expectation to 0.

The `regions_purified` metric should track player progress in purifying *corrupted* regions (fungal_depths, beast_wilds, frozen_reaches), not count regions that start purified (meridian_nexus, civilized_remnants, sunken_district).

Change in test:
```python
# OLD (incorrect expectation)
self.assertEqual(result["regions_purified"], 2)

# NEW (correct - no corrupted regions purified at start)
self.assertEqual(result["regions_purified"], 0)
```

---

## Phase 3: Functional Test Coverage

Organize tests by system. Each system should have tests for:
- Data validation (configuration is correct)
- Basic operations (functions work)
- Edge cases (boundary conditions)
- Integration points (how this system connects to others)

### 3.1 Game Loading Tests

**Existing coverage:** Good (7 tests)

| Test | Status |
|------|--------|
| Game loads without errors | Covered |
| Correct location count (31) | Covered |
| Correct actor count | Covered |
| Correct item count | Covered |
| Parts exist | Covered |
| Player at correct start location | Covered |
| Start location is valid | Covered |

**Additions needed:** None

### 3.2 Movement System Tests

**Existing coverage:** Good (5 tests)

| Test | Status |
|------|--------|
| Movement in all cardinal directions | Covered |
| Round-trip movement | Covered |
| Movement to all adjacent regions from hub | Covered |

**Additions needed:**
- Movement blocked by locked doors
- Movement blocked by conditional exits
- Movement to all internal region locations

### 3.3 Region System Tests

**Existing coverage:** Partial (6 tests)

| Test | Status |
|------|--------|
| Regions data structure exists | Covered |
| All region locations valid | Covered |
| Region lookup from location | Covered |
| Corruption applies to locations | Covered |
| Purification clears corruption | Covered |
| Get actors in region | Covered |

**Additions needed:**
- All 6 regions have correct location counts
- All locations correctly reference their region in properties
- Purification affects all corruption types (spore, cold, flood)
- Corruption spreads correctly for each type
- Region state persists across operations

### 3.4 Faction System Tests

**Existing coverage:** Partial (5 tests, 2 failing)

| Test | Status |
|------|--------|
| Factions data structure exists | Covered |
| Each faction has representative | Covered |
| Get faction for actor | Covered |
| Disposition starts neutral | Covered |
| Disposition changes with trust | Failing |

**Additions needed:**
- All faction representatives exist (need to create actors)
- All faction members exist
- Reputation modification works
- Reputation syncs to members
- Disposition thresholds (hostile < -5, friendly > 5, allied > 8)
- Each faction syncs correct dimensions

### 3.5 World Events System Tests

**Existing coverage:** Partial (4 tests, 1 failing)

| Test | Status |
|------|--------|
| World event config exists | Covered |
| Check ending conditions | Failing (expectations wrong) |
| Crystal restoration tracking | Covered |
| Spore spread affects NPCs | Covered |

**Additions needed:**
- Initialize world events schedules events
- Cancel spore spread works
- Cancel cold spread works
- Trigger spore spread sets flags and affects NPCs
- Trigger cold spread sets flags and affects actors
- Quest completion handlers (heal_spore_mother, repair_observatory, cure_aldric, restore_crystal_*)
- Ending condition logic:
  - Perfect ending (3 crystals + 3 regions purified)
  - Partial restoration (3 crystals, some regions)
  - Catastrophe (both spreads started)
  - In progress (default)

### 3.6 The Echo NPC Tests

**Existing coverage:** Good (4 tests)

| Test | Status |
|------|--------|
| Appearance chance base (10%) | Covered |
| Appearance chance increases with restoration | Covered |
| First meeting message | Covered |
| Returning player message | Covered |

**Additions needed:**
- Echo only appears in Nexus locations
- Echo actor has correct properties (is_spectral, can_be_attacked=false)
- Echo behaviors registered correctly
- Maximum appearance chance capped at 85%
- Warning messages for spore/cold spread

### 3.7 Actor Configuration Tests

**Existing coverage:** Partial (4 tests)

| Test | Status |
|------|--------|
| Player has required fields | Covered |
| NPCs have valid locations or null | Covered |
| Echo has behaviors | Covered |
| Echo is spectral | Covered |

**Additions needed:**
- All NPCs have required fields (id, name, location)
- NPCs in each faction have faction membership
- NPCs with dialog have dialog_topics defined
- Creatures have appropriate combat properties
- Special actors (The Echo, faction reps) have correct special properties

### 3.8 Item Configuration Tests

**Existing coverage:** Partial (1 test)

| Test | Status |
|------|--------|
| Items have valid locations | Covered |

**Additions needed:**
- Key items exist (Keeper's Journal, crystals, etc.)
- Quest items have correct properties
- Consumables have correct properties
- Container items have valid contents

### 3.9 Dialog System Tests

**Existing coverage:** Partial (3 tests in scenarios)

| Test | Status |
|------|--------|
| Healer Elara has topics | Covered |
| Gate Guard has topics | Covered |
| The Echo has topics | Covered |

**Additions needed:**
- All NPCs with dialog have valid topic structures
- Topic responses are non-empty strings
- Topic prerequisites (if any) reference valid flags
- Topic unlocks work correctly

### 3.10 Query System Tests

**Existing coverage:** Partial (2 tests)

| Test | Status |
|------|--------|
| Location query works | Covered |
| Inventory query works | Covered |

**Additions needed:**
- Actor query works
- Item query works
- Exits query returns correct structure
- Query responses contain expected fields

### 3.11 Data Consistency Tests

**Existing coverage:** Partial (3 tests, 2 failing)

| Test | Status |
|------|--------|
| Faction members exist | Covered |
| Faction representatives exist | Failing |
| Exit bidirectionality | Failing (code error) |

**Additions needed:**
- All referenced IDs exist (items in locations, actors referencing items, etc.)
- No duplicate IDs across entity types
- All behaviors referenced by entities exist
- Region location lists match actual locations
- Faction member/representative lists match actual actors

---

## Phase 4: Test Implementation Order

### Pass 1: Fix Breaking Issues (High Priority)
1. Create missing faction representative actors
2. Fix ExitDescriptor test code
3. Fix or update ending conditions test expectation
4. Verify all tests pass

### Pass 2: Move and Consolidate Tests
1. Move test file to tests/ directory following pattern
2. Update imports and paths
3. Verify all tests still pass in new location
4. Consider consolidation with scenario tests

### Pass 3: Add Missing Coverage
1. Region system gaps
2. Faction system gaps
3. World events system gaps
4. Data consistency checks
5. Dialog system validation

### Pass 4: Edge Cases and Robustness
1. Movement edge cases (blocked paths, conditional exits)
2. Faction threshold boundaries
3. Event timing edge cases
4. Invalid input handling

---

## Test Count Summary

| Category | Current | Expected After |
|----------|---------|----------------|
| Loading | 7 | 7 |
| Movement | 5 | 8 |
| Regions | 6 | 12 |
| Factions | 5 | 12 |
| World Events | 4 | 12 |
| The Echo | 4 | 8 |
| Actor Config | 4 | 10 |
| Item Config | 1 | 6 |
| Dialog | 3 | 8 |
| Queries | 2 | 5 |
| Data Consistency | 3 | 8 |
| **Total** | **44** | **~96** |

---

## Success Criteria

1. All tests pass (0 failures, 0 errors)
2. Tests located in `tests/` directory following project conventions
3. Each major system has comprehensive functional coverage
4. Data consistency validated automatically
5. Tests run in < 5 seconds total

---

## Dependencies

- No external dependencies
- Uses existing test infrastructure (unittest, subprocess isolation)
- Requires game data files to be correct and complete

---

## Appendix A: Virtual Actors

### Concept

A **virtual actor** is an actor entity that represents an abstract concept (like a faction's collective will) rather than a physical being in the game world. Virtual actors:

1. **Store shared state** - Hold relationship data, reputation scores, or other state that applies to a group
2. **Are not physically present** - Have `location: null` or a headquarters location, but players don't interact with them directly as NPCs
3. **Are never targets of commands** - Players cannot "talk to faction_myconid" or "attack faction_council"

### How the Game Knows an Actor is Virtual

The engine does **not** have special handling for virtual actors. Instead, this is a **convention** enforced by:

1. **The `is_faction: true` property** - Signals to game behaviors that this actor represents a faction
2. **Null or headquarters location** - Virtual actors either have no location or are placed at a logical headquarters
3. **No dialog topics** - Virtual actors don't respond to player conversation
4. **Behavior checks** - Game-specific behaviors (like `factions.py`) check `is_faction` to determine how to handle reputation

### Behavioral Differences

| Aspect | Regular Actor | Virtual Actor |
|--------|---------------|---------------|
| Location | Physical game location | `null` or headquarters location |
| Can be seen in room | Yes | No (unless placed for flavor) |
| Can be talked to | Yes (if has dialog_topics) | No |
| Can be attacked | Depends on properties | No (`can_be_attacked: false`) |
| Holds relationships | Yes (individual) | Yes (collective/faction-wide) |
| Referenced by behaviors | As individual | As faction representative |

### Faction Representative Locations

For The Shattered Meridian, faction representatives should be placed at logical headquarters:

| Faction | Representative | Suggested Location | Rationale |
|---------|----------------|-------------------|-----------|
| myconid_collective | `faction_myconid` | `loc_fd_myconid_sanctuary` | The sanctuary is the Myconid home |
| town_council | `faction_council` | `loc_cr_council_hall` | Already exists; council meets here |
| beast_spirits | `faction_beasts` | `loc_bw_predator_den` | Heart of the wild |
| frozen_keepers | `faction_frozen` | `loc_fr_temple_sanctum` | The ancient temple |

Note: `faction_council` already exists at `loc_cr_council_hall`. Only `faction_myconid`, `faction_beasts`, and `faction_frozen` need to be created.

### Design Rationale

Using actors for factions (rather than a separate faction system) provides:

1. **Consistency** - Factions use the same relationship system as individual NPCs
2. **Simplicity** - No new entity types needed in the engine
3. **Extensibility** - Faction actors can have behaviors, properties, and dialog if needed later
4. **Queryability** - Factions appear in standard actor queries and can be referenced uniformly

---

## Appendix B: Test Consistency Rules

### Rule for CLAUDE.md

The following rule should be added to the project's CLAUDE.md:

```markdown
## Testing Guidelines
- Tests must use the same parameter types, data formats, and calling conventions as production code
- Never create test-specific shortcuts, variant data formats, or simplified calling patterns
- If a test needs to call a function, it should call it exactly as production code would
- Test helpers should wrap complexity, not change interfaces
- When loading game state for tests, use the same loading functions as the real game
- When sending commands for tests, use the same message format as the real game engine
```

### Rationale

We've encountered problems with tests that:
- Used dict literals instead of proper command message format
- Called functions with different parameter orders
- Created mock objects with different interfaces than real objects
- Used simplified data structures that don't match the actual game state

These tests pass but don't catch real bugs, because they're testing something subtly different from what the game actually does.

### Pattern for Functional Tests

```python
# GOOD: Use same format as production
def test_movement(self):
    result = self.handler.handle_command({
        "type": "command",
        "action": {"verb": "go", "object": "north"}
    })
    self.assertTrue(result.get("success"))

# BAD: Simplified format that doesn't match production
def test_movement_bad(self):
    result = self.handler.go("north")  # Not how production works!
    self.assertTrue(result)
```

---

## Notes

- Tests should use subprocess isolation where module pollution is a concern
- Prefer testing functions directly over testing through the full game engine where possible
- Game data issues should be fixed in the data files, not worked around in tests
- Follow TDD: fix failing tests before adding new ones
