# Infrastructure Internal Consistency Review

**Date**: 2025-12-11
**Status**: Complete - All Fixes Applied, Validation Matrix Updated
**Subject**: `infrastructure_detailed_design.md`

---

## Summary

| Category | Issues Found | Resolved | New (Detailed Review) |
|----------|--------------|----------|----------------------|
| Internal Inconsistencies | 2 | 2 | 0 |
| game_wide_rules.md Mismatches | 0 | - | 0 |
| validation_matrix.md Gaps | 2 | 2 | 0 |
| Completeness Issues | 1 | 1 | 3 |
| Type Safety Issues | 2 | 2 | 4 |
| Consolidation Opportunities | - | - | 2 |
| Testability Issues | - | - | 1 |

---

## Initial Observations and Resolutions

### Issue 1: Type Definitions Not in Part 1

**Observation**: `BroadcastGossipEntry`, `NetworkGossipEntry`, and `NetworkDefinition` are defined in Section 3.8 (Information Networks) but not in Part 1 (Type Definitions).

**Resolution**: Added Section 1.5 (Gossip Types) with `GossipType`, `BroadcastGossipEntry`, `NetworkGossipEntry`, and `NetworkDefinition` as proper TypedDicts.

**Status**: ✅ RESOLVED - Implemented in infrastructure_detailed_design.md

---

### Issue 2: Flag Storage Location Inconsistency

**Observation**: Section 3.1 (Flag System) said player flags are in `state.actors["player"].properties["flags"]`, but Section 2.5 said `get_player_flags` returns `player.flags` directly.

**Resolution**:
- Removed `get_player_flags` accessor from Section 2.5
- Updated Section 2.5 to document "Actor flags (including player): `actor.flags`"
- Updated Section 3.1 to match: "Actor flags (including player): `actor.flags`"

**Status**: ✅ RESOLVED - Implemented in infrastructure_detailed_design.md

---

### Issue 3: Gossip Knowledge Flags Type Conflict

**Observation**: Section 3.8 stores gossip knowledge as flags using dynamic string names like `knows_gossip_123`. This appeared to conflict with the bool/int restriction.

**Analysis**: The flags ARE boolean values (True). The naming is dynamic but the values are correct.

**Resolution**: Added clarifying note to Section 2.5:
> **Note on flag names**: Flag *values* must be bool or int, but flag *names* can be dynamically generated at runtime (e.g., `knows_gossip_123`). This is common for systems that track knowledge of specific events.

**Status**: ✅ RESOLVED - Implemented in infrastructure_detailed_design.md

---

### Issue 4: validation_matrix.md API Name Mismatches

**Observation**:
| Matrix Reference | Infrastructure Actual |
|-----------------|----------------------|
| `extend_survival()` | `apply_hope_bonus()` |
| `apply_companion_aura()` | Not defined |

**Resolution**:
- `extend_survival()`: The validation_matrix should use `apply_hope_bonus()` - matrix needs updating
- `apply_companion_aura()`: Added `get_cold_protection(actor, accessor)` to Section 3.3 (Condition System)
  - Checks equipment, companion auras, location properties, actor immunity
  - Returns protection factor (0.0 to 1.0)
  - Also added `get_temperature_zone()` and `calculate_hypothermia_rate()` helper functions

**Status**: ✅ RESOLVED - `get_cold_protection()` implemented in infrastructure_detailed_design.md

**Remaining**: validation_matrix.md needs updating to reference correct API names

---

### Issue 5: Environmental Spread System Missing

**Observation**: The validation_matrix.md references `process_spread()` but no spread system was defined in infrastructure.

**Resolution**: Added complete Environmental Spread System as Section 3.10:
- **Types** (Section 1.6): `SpreadEffect`, `SpreadMilestone`, `SpreadState`
- **Accessor** (Section 2.6): `get_environmental_spreads()`, `get_network_definitions()`
- **Section 3.10**: Full system design including:
  - Data structure example (spore_spread, cold_spread configurations)
  - Turn phase handler `on_spread_check()`
  - API functions: `check_spread_active()`, `halt_spread()`, `apply_spread_effects()`, `get_spread_progress()`, `match_location_pattern()`
  - Validation function
- **Turn Phase Order** (Section 4.1): Added `turn_phase_spread`

**Status**: ✅ RESOLVED - Implemented in infrastructure_detailed_design.md

---

## Changes Applied to infrastructure_detailed_design.md

1. **Section 1.5 Gossip Types** - Added `GossipType`, `BroadcastGossipEntry`, `NetworkGossipEntry`, `NetworkDefinition`
2. **Section 1.6 Environmental Spread Types** - Added `SpreadEffect`, `SpreadMilestone`, `SpreadState`
3. **Section 2.5 Flag Operations** - Removed `get_player_flags`, added clarifying note about dynamic flag names
4. **Section 2.6 Collection Accessors** - Added `get_environmental_spreads()`, `get_network_definitions()`
5. **Section 3.1 Flag System** - Fixed storage description consistency
6. **Section 3.3 Condition System** - Added `get_cold_protection()`, `get_temperature_zone()`, `calculate_hypothermia_rate()`
7. **Section 3.10 Environmental Spread System** - New section with full system design
8. **Section 4.1 Turn Phase Order** - Added `turn_phase_spread`

---

## Detailed Review Findings

### Typing Coherence

- [x] All TypedDicts have complete field definitions with proper types
- [x] Consistent use of `NotRequired[]` for optional fields
- [x] StrEnum values match JSON serialization requirements
- [x] Return types documented for most API functions

**Issues Found:**

#### T-1: `ScheduledEvent.data` uses loose typing (MINOR)
**Location**: Section 1.3, line ~211
**Issue**: `data: NotRequired[dict[str, str]]` is too restrictive (string values only) or too loose (any string keys)
**Current**: `dict[str, str]`
**Recommendation**: Keep as-is for now. The string-only restriction is intentional for simplicity. Complex event data should be stored in game state and referenced by ID.
**Status**: Acceptable - no change needed

#### T-2: Inconsistent TurnNumber usage (MINOR)
**Location**: Various sections
**Issue**: Some places use `TurnNumber`, others use bare `int` for turn values
**Examples**:
- `GossipEntry` uses `int` for `created_turn`, `arrives_turn` (line ~202-203)
- `ActiveCommitment` uses `int` for `made_at_turn` (line ~192)
- But `BroadcastGossipEntry` uses `TurnNumber` (line ~256-257)
**Recommendation**: Standardize on `TurnNumber` throughout for consistency
**Status**: Should fix

#### T-3: `npc_filter_id` loses type information (MINOR)
**Location**: Section 3.8, line ~1601
**Issue**: `BroadcastGossipEntry` stores `npc_filter.__name__` as a string, but there's no registry to look it up at delivery time
**Current**: Filter function converted to string name, but no mechanism to resolve back to function
**Recommendation**: Either:
1. Store filter ID and maintain a registry of filter functions
2. Remove the filter feature and use explicit target lists
**Status**: Needs design decision

#### T-4: Duplicate type definitions in Section 3.8 (CLEANUP)
**Location**: Section 3.8, lines ~1648-1673
**Issue**: `BroadcastGossipEntry` and `NetworkGossipEntry` are defined AGAIN in Section 3.8, duplicating Section 1.5
**Recommendation**: Remove duplicate definitions from Section 3.8, reference Part 1
**Status**: Should fix

---

### API Completeness

- [x] All turn phase handlers have proper signatures
- [x] Most API functions have implementations shown

**Issues Found:**

#### A-1: Missing helper functions referenced but not defined
**Location**: Various sections
**Missing functions**:
- `tick_actor_conditions(actor, accessor)` - referenced in line ~813 but not defined
- `check_hypothermia_thresholds(actor, severity)` - referenced in line ~850 but not defined
- `tick_drowning`, `tick_bleeding`, `tick_infection`, `tick_exhaustion`, `tick_poison` - registered in line ~829-833 but not defined
- `fire_scheduled_event(event, accessor)` - referenced in line ~729 but not defined
- `check_flag(req, accessor)` - referenced in line ~1767 but not defined
- `apply_location_effects(actor, location, accessor)` - referenced in line ~1211 but not defined
**Recommendation**: Add stub implementations or explicit "game-specific" notes
**Status**: Should document or implement

#### A-2: API functions shown as signatures only
**Location**: Various sections
**Functions with signatures but no implementation**:
- `make_commitment()` (line ~1136)
- `fulfill_commitment()` (line ~1143)
- `withdraw_commitment()` (line ~1150)
- `abandon_commitment()` (line ~1157 - has impl elsewhere)
- `check_commitment_phrase()` (line ~1163)
- `schedule_event()` (line ~745)
- `cancel_scheduled_event()` (line ~754)
- `reschedule_event()` (line ~760)
- `apply_condition()` (line ~863)
- `cure_condition()` (line ~871)
- `get_actor_condition()` (line ~878)
**Recommendation**: Either add implementations or mark as "implementation straightforward"
**Status**: Acceptable for design doc - implementations are clear from signatures

#### A-3: Validation module incomplete
**Location**: Section 4.2
**Issue**: `validate_infrastructure()` references functions not defined:
- `validate_commitment_configs()`
- `validate_state_machines()`
- `validate_zone_consistency()`
- `validate_companion_restrictions()`
- `validate_gossip_references()`
**Note**: `validate_spreads()` IS defined in Section 3.10 but not listed in the module
**Recommendation**: Either define validation functions or list as "to be implemented"
**Status**: Should document

---

### JSON/TypedDict Alignment

- [x] Example JSON structures match their TypedDict definitions
- [x] Field names match exactly
- [x] Nested structures properly typed

**No issues found** - JSON examples align well with TypedDict definitions.

---

### Cross-Reference Accuracy

- [x] Section references within document are valid
- [x] No orphaned references

**No significant issues found.**

---

### Consolidation Opportunities

#### C-1: Location pattern matching duplication
**Location**: Sections 3.7 and 3.10
**Issue**: Two similar functions for pattern matching:
- `matches_location_pattern(location_id, patterns)` in companion system
- `match_location_pattern(pattern, state)` in spread system
**Difference**: One takes a list of patterns, other takes single pattern and iterates locations
**Recommendation**: Consolidate into Part 2 utilities:
```python
def matches_pattern(target: str, pattern: str) -> bool:
    """Check if target string matches a glob pattern."""

def find_matching_locations(pattern: str, state: GameState) -> list[str]:
    """Find all locations matching a pattern."""
```
**Status**: Should consolidate

#### C-2: Trust modification patterns
**Location**: Sections 2.2 and 3.4
**Observation**: `modify_trust()` utility in 2.2 is well-designed and reused properly by `modify_echo_trust()` and `modify_npc_trust()` in 3.4
**Status**: Good - no action needed

---

### Testability Assessment

- [x] Most API functions can be tested in isolation
- [x] State mutations are generally documented
- [x] System boundaries are clear

**Issues Found:**

#### TEST-1: `check_echo_appears()` has hidden randomness
**Location**: Section 3.4, lines ~1017-1029
**Issue**: Function uses `random.random()` internally, making it non-deterministic
**Recommendation**: Either:
1. Accept a random source as parameter for testing
2. Split into `calculate_echo_chance()` (testable) and `check_echo_appears()` (uses random)
**Status**: Should fix for testability

**Testability Notes (Good Patterns)**:
- Collection accessors (2.6) initialize missing data, making tests simpler
- TypedDicts enable type checking in tests
- Turn phase handlers all return `EventResult` consistently
- Condition system tick handlers return message lists for verification

---

### Error Handling

- [x] Validation errors surface at load time
- [x] Edge cases generally addressed

**No significant issues found.** The fail-fast design is consistently applied.

---

## Detailed Review Checklist (Completed)

### Typing Coherence
- [x] All TypedDicts have complete field definitions with proper types
- [x] No critical uses of `Any` (T-1 is acceptable)
- [x] Consistent use of `NotRequired[]` for optional fields
- [x] NewType wrappers mostly consistent (T-2 needs fixing)
- [x] Return types documented for all API functions
- [x] StrEnum values match JSON serialization requirements
- **Issues**: T-2 (inconsistent TurnNumber), T-3 (filter registry), T-4 (duplicates)

### API Completeness
- [x] Most API functions have implementations shown
- [x] All turn phase handlers have proper signatures
- **Issues**: A-1 (missing helpers), A-3 (validation functions)

### JSON/TypedDict Alignment
- [x] Example JSON structures match their TypedDict definitions ✓
- [x] Field names match exactly ✓
- [x] Optional fields align with `NotRequired[]` ✓
- [x] Nested structures properly typed ✓

### Cross-Reference Accuracy
- [x] Section references valid ✓
- [x] No orphaned references ✓

### Consolidation Opportunities
- **Found**: C-1 (location pattern matching)

### Testability Assessment
- [x] Unit-level testability: Good overall
- **Issues**: TEST-1 (random in check_echo_appears)

### Error Handling
- [x] Validation errors surface at load time ✓
- [x] Edge cases addressed ✓

---

## Fixes Applied

All fixes from the detailed review have been applied to infrastructure_detailed_design.md:

### Priority 1 Fixes (All Complete ✓)

1. **T-2: Standardize TurnNumber usage** ✓
   - Updated `GossipEntry` to use `TurnNumber` for `created_turn`, `arrives_turn`, `confession_window_until`
   - Updated `ActiveCommitment` to use `TurnNumber` for `made_at_turn`, `deadline_turn`
   - Updated `TrustState` to use `TurnNumber` for `last_recovery_turn`
   - Updated `ScheduledEvent` to use `TurnNumber` for `trigger_turn`

2. **T-4: Remove duplicate type definitions** ✓
   - Removed duplicate `BroadcastGossipEntry` and `NetworkGossipEntry` from Section 3.8
   - Cleaned up orphaned "Gossip Types" section
   - Added JSON example for NetworkDefinitions

3. **C-1: Consolidate pattern matching** ✓
   - Added Section 2.7 "Pattern Matching Utilities" with:
     - `matches_pattern(target, pattern)` - single pattern matching
     - `find_matching_locations(pattern, state)` - find all locations matching pattern
     - `matches_any_pattern(target, patterns)` - check against list of patterns
   - Updated Section 3.7 companion system to use `matches_any_pattern()`
   - Updated Section 3.10 spread system to use `find_matching_locations()`

4. **TEST-1: Fix testability of check_echo_appears()** ✓
   - Split into `calculate_echo_chance(trust, base_chance)` (pure, testable)
   - Added `random_value` parameter to `check_echo_appears()` for deterministic testing

### Priority 2 Fixes (All Complete ✓)

1. **A-1: Missing helper functions** ✓
   - Added "Game-Specific Functions" notes to:
     - Section 3.2 (Turn/Timer System): `fire_scheduled_event`
     - Section 3.3 (Condition System): `tick_actor_conditions`, `tick_*` handlers, `check_hypothermia_thresholds`
     - Section 3.6 (Environmental System): `apply_location_effects`
   - Added full implementation of `check_flag()` in Section 3.9

2. **A-3: Validation module** ✓
   - Added `validate_spreads(state)` to the validation module's function list
   - Added note documenting that other validation functions are to be implemented

### Priority 3 Fixes (All Complete ✓)

1. **T-3: NPC filter for broadcast gossip** ✓
   - **Decision**: Remove the feature (option b)
   - Removed `npc_filter_id` from `BroadcastGossipEntry` TypedDict
   - Removed `npc_filter` parameter from `create_broadcast_gossip()`
   - Added docstring note explaining that property-based targeting should use `NetworkGossipEntry`

---

## Remaining Work

### validation_matrix.md Updates (Complete ✓)

The following API name updates have been applied to validation_matrix.md:
- ✓ Changed `extend_survival()` → `apply_hope_bonus()`
- ✓ Changed `apply_companion_aura()` → `get_cold_protection()`
- ✓ Replaced `process_spread()` with spread system APIs: `check_spread_active()`, `halt_spread()`, `apply_spread_effects()`, `get_spread_progress()`

---

## Review Conclusion

The infrastructure_detailed_design.md is now complete and ready for implementation:
- All typing issues resolved
- All completeness issues addressed
- Pattern matching consolidated into shared utilities
- Testability improved for `check_echo_appears()`
- Game-specific functions documented
- Validation module updated

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.4 | 2025-12-11 | Applied all fixes to infrastructure_detailed_design.md. Document ready for implementation. |
| 0.3 | 2025-12-11 | Completed detailed review. Found 4 typing issues, 3 completeness issues, 2 consolidation opportunities, 1 testability issue. All minor. |
| 0.2 | 2025-12-11 | Applied all resolutions to infrastructure_detailed_design.md. Updated status to Ready for Detailed Review. Added expanded checklist. |
| 0.1 | 2025-12-11 | Initial observations and resolutions |
