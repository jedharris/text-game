# Entity Behavior Format Migration

**GitHub Issue:** TBD (follow-up to #51)

## Problem

The codebase supports two different entity behavior formats:

1. **Old dict format**: `behaviors = {"on_event": "module:function"}`
   - Signature: `on_event(entity, state, context)`
   - Behavior path stored per-event in entity data
   - Used by older behavior modules and test fixtures

2. **New list format**: `behaviors = ["module1", "module2"]`
   - Signature: `on_event(entity, accessor, context)`
   - Module names stored in list, functions discovered by convention
   - Used by newer behavior modules

The backward compatibility code in `invoke_entity_behavior` (behavior_manager.py lines 416-441) handles both formats, adding complexity.

## Goals

1. Migrate all entity behaviors to the new list format
2. Update all behavior function signatures to use `accessor` instead of `state`
3. Remove the dict format handling code from `invoke_entity_behavior`
4. Update test fixtures to use new format

## Assumptions

- No external game files use the old dict format (verified: only test fixtures)
- The new format is preferred going forward
- All migrations can be done in one pass

---

## Phase 1: Migrate Behavior Function Signatures

**Files to update:**

| File | Functions |
|------|-----------|
| `behaviors/items/rubber_duck.py` | `on_squeeze` |
| `behaviors/core/consumables.py` | `on_drink_health_potion`, `on_eat_food` |
| `behaviors/core/light_sources.py` | `on_take`, `on_drop`, `on_put` |
| `behaviors/core/containers.py` | `on_open_treasure_chest` |

**Changes per function:**
1. Change signature from `(entity, state, context)` to `(entity, accessor, context)`
2. Update any code that accesses `state` to use `accessor.game_state` or accessor methods
3. Update docstrings

**Status:** Pending

**Results:**

---

## Phase 2: Update Test Fixtures

**Fixtures using old dict format:**
- `tests/fixtures/test_game_with_behaviors.json`
- `tests/fixtures/test_game_with_core_behaviors.json`

**Changes:**
1. Convert `behaviors` from dict to list format
2. Ensure referenced modules are in the behaviors directory structure

**Example migration:**
```json
// Old format
"behaviors": {
  "on_squeeze": "behaviors.items.rubber_duck:on_squeeze"
}

// New format
"behaviors": ["behaviors.items.rubber_duck"]
```

**Status:** Pending

**Results:**

---

## Phase 3: Update Test Behavior Functions

**Tests with inline behavior functions using old signature:**
- `tests/test_protocol_behaviors.py` (multiple functions)
- `tests/test_behavior_manager.py` (1 function)

**Changes:**
1. Update inline `on_*` functions to use `(entity, accessor, context)` signature
2. Update any state access to use accessor

**Status:** Pending

**Results:**

---

## Phase 4: Remove Old Format Handling Code

**File:** `behavior_manager.py`

**Changes:**
1. Remove the dict format branch in `invoke_entity_behavior` (lines 416-441)
2. Remove the state extraction backward compatibility code
3. Simplify to only handle list format

**Current code to remove:**
```python
# Handle both old (dict) and new (list) behaviors formats
if isinstance(entity.behaviors, dict):
    # Old format: behaviors = {"on_event": "module:function"}
    behavior_path = entity.behaviors.get(event_name)
    ...
    # Old format uses state parameter instead of accessor
    # For backward compatibility, try to get state from accessor
    state = accessor.game_state if hasattr(accessor, 'game_state') else accessor
    result = behavior_func(entity, state, context)
    ...
```

**Status:** Pending

**Results:**

---

## Phase 5: Verify and Clean Up

**Verification:**
1. Run all tests
2. Search codebase for any remaining old-format references
3. Verify no "state" parameter usage in entity behaviors

**Cleanup:**
1. Update any documentation referencing old format
2. Remove old format examples from docs

**Status:** Pending

**Results:**

---

## Deferred Work

(To be populated during implementation)

---

## Final Checklist

- [ ] All behavior functions use `(entity, accessor, context)` signature
- [ ] All test fixtures use list format for behaviors
- [ ] Old dict format handling code removed from `invoke_entity_behavior`
- [ ] All tests pass
- [ ] Documentation updated
