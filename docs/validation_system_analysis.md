# Validation System Analysis

**Date**: 2025-12-29
**Context**: Comparing Issue #306 requirements vs. current implementation
**Purpose**: Determine what validation is missing before infrastructure wiring work

---

## Executive Summary

Issue #306 requested comprehensive validation to catch authoring errors at load time. The work was **partially completed**:

- ✅ Hook system validation is fully implemented (from hook refactoring)
- ⚠️ Entity behavior validation exists but is incomplete
- ❌ Validation methods exist but are **not called** (never integrated)
- ❌ Enhanced walkthrough logging was deferred

**Critical Gap**: `finalize_loading()` is never called, so most validation doesn't run.

---

## Validation Requested in Issue #306

### 1. Vocabulary Event/Hook Validation

**Request**: Validate event names match handler functions, hook names match engine hooks

**Current Status**: ✅ **PARTIALLY IMPLEMENTED** (but not called)

**What exists**:
- `validate_on_prefix_usage()` - Ensures all on_* functions have registered events
- `validate_hooks_are_defined()` - Ensures event hooks reference defined hooks
- `validate_hook_prefixes()` - Ensures hooks use turn_* or entity_* prefixes
- `_validate_vocabulary()` - Validates vocabulary structure (IS called during module loading)

**What's missing**:
- Suggested corrections for typos (fuzzy matching)
- Not called: The validate_* methods in `finalize_loading()` are never invoked

**Example from #306**:
```
VOCABULARY VALIDATION FAILED
Module: behaviors.regions.fungal_depths.spore_zones
Event: environmental_effect
Problem: No function named 'on_environmental_effect' found in module

Available on_* functions in module:
  - on_spore_zone_turn
  - on_enter_spore_zone

Did you mean to use event: "on_spore_zone_turn"?
```

**Current behavior**:
- `validate_on_prefix_usage()` would catch the reverse (on_* function without event)
- But if event is registered without matching function, it silently succeeds
- **This is actually acceptable** - events can be declared without handlers (handled elsewhere)

---

### 2. Entity Behaviors Path Validation

**Request**: Validate all entity.behaviors paths exist and loaded successfully

**Current Status**: ⚠️ **PARTIALLY IMPLEMENTED**

**What exists**:
- `validate_turn_phase_not_in_entity_behaviors()` - Checks turn phases not on entities
- `_invoke_entity_behaviors()` - Silently skips if module not loaded (line 898-901)

**What's missing**:
- No validation that entity behavior paths are valid
- No check that referenced modules actually loaded
- No suggestions for similar module names
- Silent failure at runtime instead of loud failure at load time

**Example from #306**:
```
ENTITY BEHAVIORS VALIDATION FAILED
Entity: player
Invalid behavior: behaviors.regions.fungal_depths.spore_zone (missing 's')

This module is not loaded. Possible causes:
  1. Typo in module path
  2. Module failed to import (check errors above)
  3. Module file doesn't exist

Did you mean: behaviors.regions.fungal_depths.spore_zones?

Entity's other behaviors (all valid):
  ✓ behaviors.shared.lib.actor_lib.combat
  ✓ behaviors.shared.lib.actor_lib.npc_actions
```

**Current behavior**:
```python
# Line 898-901 in behavior_manager.py
module = self._modules.get(behavior_module_name)
if not module:
    # Module not loaded, skip  <-- SILENT FAILURE!
    continue
```

**Impact**: If you typo a behavior module name in game_state.json, it silently does nothing.

---

### 3. Hook Registration Validation

**Request**: Validate hooks match known engine hooks, warn about unused hooks

**Current Status**: ✅ **IMPLEMENTED** (but not called)

**What exists**:
- `validate_hooks_are_defined()` - Checks event hooks reference defined hooks
- `validate_hook_prefixes()` - Validates turn_* and entity_* naming
- `validate_hook_invocation_consistency()` - No conflicting invocation types

**What's called**: None of these - `finalize_loading()` never runs

**What's missing**:
- Suggestions for similar hook names (fuzzy matching)
- Warnings about hooks with no registered events (might be intentional)

---

### 4. Turn Phase Handler Pattern Validation

**Request**: Verify turn phase handlers not in entity.behaviors

**Current Status**: ✅ **IMPLEMENTED** (but not called)

**What exists**:
- `validate_turn_phase_not_in_entity_behaviors()` - Full implementation

**Example from #306**:
```
TURN PHASE HANDLER WARNING
Module: behaviors.regions.fungal_depths.spore_zones
Event: on_spore_zone_turn
Hook: environmental_effect (turn phase hook)

This module is in entity behaviors:
  - player.behaviors

Turn phase handlers are called with entity=None and should NOT be in
entity.behaviors lists. Remove from entity behaviors or use different hook.
```

**Current**: This exact validation exists but is never called.

---

### 5. Enhanced Walkthrough Logging

**Request**: Add --verbose mode showing event flow, modules loaded, conditions changed

**Current Status**: ❌ **NOT IMPLEMENTED** (explicitly deferred)

**From #306 completion comment**:
> The --verbose flag for walkthrough.py with detailed event logging was not implemented in this phase. This can be addressed in a future enhancement when needed for debugging specific issues.

**Example requested**:
```
[TURN 1] Command: go down
  [MODULE] Loaded 45 behavior modules successfully
  [EVENT] on_before_move (player) -> 3 handlers
    - behaviors.core.spatial.on_before_move -> allow=True
  [TURN_PHASE] environmental_effect
    - behaviors.regions.fungal_depths.spore_zones.on_spore_zone_turn
      Player at: luminous_grotto, spore_level: medium, rate: 5
      Applied fungal_infection: severity 0 -> 5
  [TURN_PHASE] condition_tick
    - behaviors.shared.lib.actor_lib.conditions.on_condition_tick
      No conditions to tick
```

**Impact**: Debugging walkthrough failures is slow - can't see which handlers fired or didn't fire.

---

## Current Validation Methods

### Called During Module Loading

1. **`_validate_vocabulary(vocabulary, module_name)`**
   - ✅ Called in `load_module()` line 456
   - Validates vocabulary structure (verbs, events, hook_definitions)
   - Checks required fields, types
   - **Does run automatically**

### Called in finalize_loading() - BUT NEVER INVOKED

2. **`validate_hook_prefixes()`**
   - Ensures turn_* prefix for turn_phase hooks
   - Ensures entity_* prefix for entity hooks
   - **NOT called** - finalize_loading() not invoked

3. **`validate_turn_phase_dependencies()`**
   - Checks 'after' dependencies reference defined hooks
   - Prevents circular dependencies
   - **NOT called**

4. **`validate_hooks_are_defined()`**
   - Ensures events reference real hook definitions
   - **NOT called**

5. **`validate_hook_invocation_consistency()`**
   - Prevents same hook used as both turn_phase and entity
   - **NOT called**

6. **`validate_turn_phase_not_in_entity_behaviors(game_state)`**
   - Prevents turn phases in entity.behaviors lists
   - **NOT called**

### Standalone Method

7. **`validate_on_prefix_usage()`**
   - Ensures all on_* functions have registered events
   - Can be called manually but isn't
   - **NOT called**

---

## Integration Status

### In game_engine.py (lines 60-91):

```python
# Initialize behavior manager and load modules
self.behavior_manager = BehaviorManager()

# ... sys.path setup ...

# Load all behaviors from game directory (includes core via symlink)
modules = self.behavior_manager.discover_modules(str(behaviors_dir))
self.behavior_manager.load_modules(modules)

# Initialize turn executor with hook definitions
from src import turn_executor
turn_executor.initialize(self.behavior_manager._hook_definitions)

# Load and merge vocabulary
self.merged_vocabulary = build_merged_vocabulary(...)
```

**Missing**: No call to `finalize_loading()` or any validation methods

**Should be**:
```python
self.behavior_manager.load_modules(modules)

# Validate all loaded modules and game state
self.behavior_manager.finalize_loading(self.game_state)  # <-- ADD THIS

from src import turn_executor
...
```

---

## Gap Analysis

### Critical Gaps (Must fix before infrastructure work)

1. **finalize_loading() not called**
   - **Impact**: Hook validation doesn't run
   - **Severity**: HIGH - Missing hooks/typos go undetected
   - **Fix**: Add one line to game_engine.py
   - **Effort**: 5 minutes

2. **Entity behaviors not validated**
   - **Impact**: Typos in entity.behaviors silently ignored
   - **Severity**: HIGH - Broken behaviors appear to work
   - **Fix**: Add `validate_entity_behaviors(game_state)` method
   - **Effort**: 1-2 hours

3. **No fuzzy matching for suggestions**
   - **Impact**: Error messages less helpful
   - **Severity**: MEDIUM - Slows debugging
   - **Fix**: Add difflib-based similarity matching
   - **Effort**: 1 hour

### Medium Priority Gaps

4. **No walkthrough verbose mode**
   - **Impact**: Hard to debug walkthrough failures
   - **Severity**: MEDIUM - Slows iteration
   - **Fix**: Add logging to walkthrough.py and turn executor
   - **Effort**: 3-4 hours

5. **Module load failures not reported to entities**
   - **Impact**: Entity behaviors fail silently if module import failed
   - **Severity**: MEDIUM - Confusing errors
   - **Fix**: Track failed modules, report in validation
   - **Effort**: 1-2 hours

### Low Priority Gaps

6. **No warning for unused hooks**
   - **Impact**: Dead code accumulates
   - **Severity**: LOW - Just tech debt
   - **Fix**: Add unused hook detection
   - **Effort**: 1 hour

---

## Recommended Validation Additions

### 1. Entity Behaviors Validation (NEW)

**Method**: `validate_entity_behaviors(game_state)`

**Checks**:
- Every path in entity.behaviors is in _modules dict
- If not, check if module failed to load (track import errors)
- Suggest similar module names using difflib
- List all behaviors with loaded/failed status

**Add to**: `finalize_loading()`

**Pseudocode**:
```python
def validate_entity_behaviors(self, game_state):
    """Validate all entity behavior paths are loaded."""

    # Collect all entity behavior paths
    all_entity_behaviors = set()
    for actor in game_state.actors.values():
        all_entity_behaviors.update(actor.behaviors)
    for item in game_state.items:
        all_entity_behaviors.update(item.behaviors)
    for location in game_state.locations:
        all_entity_behaviors.update(location.behaviors)

    # Check each path
    errors = []
    for behavior_path in all_entity_behaviors:
        if behavior_path not in self._modules:
            # Find similar module names
            similar = difflib.get_close_matches(
                behavior_path,
                self._modules.keys(),
                n=3,
                cutoff=0.6
            )

            error_msg = f"Entity behavior '{behavior_path}' not loaded\n"
            if similar:
                error_msg += f"  Did you mean: {', '.join(similar)}?\n"

            errors.append(error_msg)

    if errors:
        raise ValueError("Entity behavior validation failed:\n" + "\n".join(errors))
```

---

### 2. Walkthrough Verbose Mode (DEFERRED)

**File**: `tools/walkthrough.py`

**Add**: `--verbose` flag

**Output**:
- Loaded modules count
- Each command with turn number
- Events fired (entity and turn phase)
- Handlers invoked with results
- Conditions changed
- Errors/warnings

**Defer until**: First time we need it for debugging (likely Phase 1 or 2 of wiring work)

---

### 3. Track Module Load Failures

**Add to BehaviorManager**:
- `_failed_modules: Dict[str, Exception]` - Track import errors
- Report in `validate_entity_behaviors()`
- Include error message and traceback

**Pseudocode**:
```python
def load_module(self, module_path, tier):
    try:
        module = importlib.import_module(module_path)
        self._modules[module_path] = module
    except Exception as e:
        self._failed_modules[module_path] = e
        # Still continue - maybe module isn't needed
        print(f"WARNING: Failed to load {module_path}: {e}")
```

---

## Implementation Plan

### Phase 0: Minimal Validation (30 minutes)

**Goal**: Get existing validation running

1. Add `finalize_loading()` call to game_engine.py (5 min)
2. Test that it catches hook errors (5 min)
3. Test with big_game (10 min)
4. Fix any errors found (10 min)

**Success**: Hook validation catches real errors

---

### Phase 1: Entity Behavior Validation (2 hours)

**Goal**: Catch entity behavior typos/missing modules

1. Add `validate_entity_behaviors()` method (30 min)
2. Add to `finalize_loading()` (5 min)
3. Add fuzzy matching with difflib (30 min)
4. Test with intentional typos (15 min)
5. Test with big_game (30 min)
6. Document in validation guide (10 min)

**Success**: Typo in entity.behaviors fails loudly with suggestion

---

### Phase 2: Module Load Failure Tracking (1 hour)

**Goal**: Report why modules didn't load

1. Add `_failed_modules` dict to BehaviorManager (5 min)
2. Track exceptions in `load_module()` (15 min)
3. Report failures in `validate_entity_behaviors()` (20 min)
4. Test with broken module (10 min)
5. Test with big_game (10 min)

**Success**: Import error shown when entity references failed module

---

### Phase 3: Walkthrough Verbose Mode (DEFERRED)

**Goal**: Debug walkthrough failures faster

**Defer**: Until needed during infrastructure wiring work

**Reason**: We don't know what we need yet. Add this when we hit our first confusing walkthrough failure.

---

## Verification Strategy

### Test Cases for Validation

1. **Empty vocabulary** (spore_zones, drowning currently have this)
   - Should: Pass validation (events can be empty)
   - Currently: Passes

2. **Typo in hook name**
   - Example: `"hook": "environmental_efect"` (missing 'f')
   - Should: Fail with "Did you mean: environmental_effect?"
   - Currently: Would fail if finalize_loading() called

3. **Typo in entity behavior path**
   - Example: `player.behaviors = ["behaviors.core.spatail"]` (typo)
   - Should: Fail with "Did you mean: behaviors.core.spatial?"
   - Currently: Silently skips at runtime

4. **Turn phase in entity behaviors**
   - Example: `player.behaviors = ["examples.big_game.behaviors.shared.infrastructure.commitments"]`
   - Should: Fail with "Turn phase behavior on entity"
   - Currently: Would fail if finalize_loading() called

5. **on_* function without event registration**
   - Example: Define `on_custom_event()` but don't register event
   - Should: Fail with "Function not registered"
   - Currently: Would fail if validate_on_prefix_usage() called

6. **Hook dependency on undefined hook**
   - Example: `"after": ["turn_nonexistent"]`
   - Should: Fail with "Undefined hook in dependencies"
   - Currently: Would fail if finalize_loading() called

---

## Conclusion

The validation infrastructure is **mostly built** but **not integrated**. The hook refactoring added comprehensive hook validation, but it's not being called.

**Immediate actions needed**:
1. ✅ Add `finalize_loading()` call (5 min)
2. ✅ Add entity behavior validation (2 hours)
3. ✅ Track module load failures (1 hour)
4. ⏸️ Defer walkthrough verbose mode until needed

**Total effort before infrastructure wiring**: ~3.5 hours

**Benefit**: Catch authoring errors immediately instead of during walkthrough debugging.

---

## Next Steps

1. Create new issue for validation completion
2. Implement Phase 0-2 (minimal validation + entity behaviors)
3. Test with big_game
4. Then proceed with infrastructure wiring work
