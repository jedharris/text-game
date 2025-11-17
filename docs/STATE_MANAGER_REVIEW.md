# State Manager Documentation Review

**Date**: 2025-11-16
**Status**: ⚠️ INCONSISTENCIES FOUND - Updates needed

## Executive Summary

Reviewed `state_manager_plan.md` and `state_manager_API.md` for consistency with the completed test suite (44 tests). Found **1 critical inconsistency** that must be fixed before implementation.

## Critical Issue

### ❌ Item Location Field Format (INCONSISTENT)

**Location**: `state_manager_API.md` line 111

**Current documentation says:**
```python
location: str  # location id, container item id, or "inventory:player" / "inventory:<npc_id>"
```

**Tests expect (V2.0 ID design):**
```python
location: str  # location id, container item id, "player", or npc id (no prefixes!)
```

**Evidence from tests:**
- `test_validators.py:168`: `if i.location == "player"` (not `"inventory:player"`)
- `test_validators.py:179`: `if i.location == "npc_1"` (not `"inventory:npc_1"`)
- `test_validators.py:190`: `if i.location == "item_2"` (container, no prefix)

**Impact**: HIGH - This is a fundamental design decision that affects:
- Item location validation (TV-015, TV-016, TV-017, TV-018)
- Player inventory management
- NPC inventory tracking
- Global ID uniqueness validation

**Required fix**: Update `state_manager_API.md` section 1.5 to match V2.0 design.

## Documentation Status

### ✅ Correct and Consistent

1. **Array Storage for Locations and Locks** (CORRECT)
   - Plan: ✅ "iterate `raw["locations"]` array" (line 72)
   - API: ✅ `locations: List[Location]` (line 18)
   - API: ✅ `locks: List[Lock]` (line 21)
   - Tests: ✅ Expect `game_state.locations` to be iterable list

2. **Global ID Registry** (CORRECT)
   - Plan: ✅ "Build global ID registry and validate all IDs are globally unique" (line 77)
   - Plan: ✅ `build_global_id_registry(game_state)` validator (line 103)
   - API: ✅ `build_id_registry() -> Dict[str, str]` (line 39)
   - Tests: ✅ TV-001, TV-002, TV-003 test global uniqueness

3. **Reserved "player" ID** (CORRECT)
   - Plan: ✅ Shows `"player"` reserved in ID registry (line 103 note)
   - Tests: ✅ TV-003 validates reserved ID enforcement

4. **GameState Structure** (CORRECT)
   - Plan: Lists all required collections ✅
   - API: Defines complete GameState class ✅
   - Tests: Access `.locations`, `.items`, `.doors`, `.locks`, `.npcs`, `.scripts`, `.player`, `.metadata` ✅

5. **Extra Fields for Forward Compatibility** (CORRECT)
   - Plan: ✅ "optional `extra` fields to preserve unknown keys" (line 161-162)
   - Tests: ✅ TL-004, TR-003, TS-004 verify `game_state.extra` field

6. **Exception Types** (CORRECT)
   - Plan: ✅ Defines `SchemaError`, `ValidationError`, `FileLoadError` (lines 140-146)
   - Tests: ✅ All tests import and expect these exception types

7. **Loader Functions** (CORRECT)
   - Plan: ✅ `load_game_state(source)` and `parse_game_state(raw)` (lines 60-67)
   - Tests: ✅ Tests use both functions correctly

8. **Serializer Functions** (CORRECT)
   - Plan: ✅ `game_state_to_dict()`, `save_game_state()` (lines 81-91)
   - Tests: ✅ TS-001 through TS-005 test these functions

9. **Validation Functions** (CORRECT)
   - Plan: ✅ Comprehensive list of validators (lines 100-138)
   - Tests: ✅ TV-001 through TV-018 cover all validation scenarios

## Recommended Changes

### 1. Fix state_manager_API.md (REQUIRED)

**File**: `docs/state_manager_API.md`
**Line**: 111

**Current:**
```python
class Item:
    id: str
    name: str
    description: str
    type: ItemType
    portable: bool
    location: str  # location id, container item id, or "inventory:player" / "inventory:<npc_id>"
    states: Dict[str, Any]
    container: Optional[ContainerInfo]
```

**Should be:**
```python
class Item:
    id: str
    name: str
    description: str
    type: ItemType
    portable: bool
    location: str  # location id, container item id, "player", or npc id
    states: Dict[str, Any]
    container: Optional[ContainerInfo]
```

**Also update lines 119-125:**

**Current:**
```
**Item Location Field Format:**
- Location ID (string): `"loc_1"` - item is in that location
- Container Item ID (string): `"item_5"` - item is inside that container item
- Player inventory: `"player"` - item is in player's inventory
- NPC inventory: `<npc_id>` (string): `"npc_3"` - item is held by that NPC

All IDs are globally unique, so no special prefixes are needed. The validator checks that the referenced ID exists and is an appropriate entity type.
```

**Should be:**
```
**Item Location Field Format (V2.0 ID Design):**
- Location ID: `"loc_1"` - item is in that location
- Container item ID: `"item_5"` - item is inside that container item
- Player inventory: `"player"` - item is in player's inventory (reserved ID)
- NPC inventory: `"npc_3"` - item is held by that NPC (NPC ID directly)

All entity IDs are globally unique (including "player" which is reserved). No prefixes like "inventory:" are used. The validator checks that the referenced ID exists in the global ID registry and is an appropriate entity type (location, item, NPC, or the special "player" ID).
```

### 2. Add V2.0 Design Note to Plan (RECOMMENDED)

**File**: `docs/state_manager_plan.md`
**After line 77** (after "Build global ID registry...")

**Add:**
```markdown

**V2.0 ID Design Principles:**

This implementation follows the V2.0 ID namespace design:
- All entity IDs are globally unique across ALL entity types (locations, items, doors, locks, npcs, scripts)
- IDs are internal identifiers separate from user-visible names
- The special ID `"player"` is reserved and cannot be used by any entity
- Item locations use simple ID references with no prefixes:
  - `"loc_1"` - item in that location
  - `"item_5"` - item inside that container
  - `"player"` - item in player inventory (no `"inventory:player"` prefix!)
  - `"npc_3"` - item held by that NPC (no `"inventory:npc_3"` prefix!)
- Locations and locks are stored as arrays (not keyed objects)
```

### 3. Update PlayerState Field Name (OPTIONAL)

**File**: `docs/state_manager_API.md`
**Line**: 150

**Current:**
```python
class PlayerState:
    location_id: str
    inventory: List[str]
    flags: Dict[str, Any]
    stats: Dict[str, int]
```

**Consider:**
```python
class PlayerState:
    location: str  # For consistency with Item.location field
    inventory: List[str]
    flags: Dict[str, Any]
    stats: Dict[str, int]
```

**Rationale**: Tests use `game_state.player.location` not `game_state.player.location_id`. Choose one naming convention and stick with it.

## Test Coverage Summary

All 44 tests align with the plan/API except for the item location format issue:

- **TL-001 to TL-007**: Loader tests ✅
- **TV-001 to TV-018**: Validator tests ✅ (but TV-015, TV-016 expect no prefixes!)
- **TS-001 to TS-005**: Serializer tests ✅
- **TM-001 to TM-005**: Model tests ✅
- **TE-001 to TE-005**: Error handling tests ✅
- **TR-001 to TR-004**: Regression tests ✅

## Implementation Checklist

Before implementing the state manager, complete these updates:

- [ ] Fix `state_manager_API.md` line 111 (item location field)
- [ ] Fix `state_manager_API.md` lines 119-125 (location field format docs)
- [ ] Add V2.0 design note to `state_manager_plan.md` (optional but recommended)
- [ ] Verify PlayerState field name consistency (`location` vs `location_id`)
- [ ] Review all documentation for any other "inventory:" prefix references

## Conclusion

The documentation is **95% ready** for implementation. Only one critical inconsistency needs fixing: the item location field format. Once corrected, the plan and API docs will be fully aligned with the test suite and V2.0 ID design.

The tests are comprehensive and correctly specify V2.0 behavior. Use them as the source of truth for implementation.
