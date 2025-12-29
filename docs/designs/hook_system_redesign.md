# Hook System Redesign - Complete Design Document

## Overview

This document describes the complete 9-phase redesign of the hook system.

**Parent Issue:** #321 - Hook System Redesign: Vocabulary-Based Hook Definitions
**Reference Plan:** [docs/designs/reference_validation_plan.md](reference_validation_plan.md)
**Current Baseline:** 2039 tests, ALL PASSING ✅
**Status:** Ready to begin Phase 1

**History:** Phases 1-3 were previously completed (issue #307) but reverted due to uncommitted work being lost. This implementation incorporates lessons learned from that attempt.

## Problem Statement

The current hook system has several issues:

1. **src/hooks.py dependency**: Authors must reference engine file for hook names
2. **No self-documentation**: Hook names don't indicate invocation pattern (turn phase vs entity-specific)
3. **Limited validation**: Many authoring errors only caught at runtime
4. **No dependency ordering**: Turn phases use arbitrary numeric order via extra_turn_phases
5. **Core field misuse**: `actor.properties.get("location")` silently returns None instead of failing

## Solution

Redesign the hook system to use vocabulary-based hook definitions with:

- **Hook definitions in vocabularies**: No need to reference src/hooks.py
- **Prefix-based naming**: `turn_*` for turn phases, `entity_*` for entity hooks (self-documenting)
- **Dependency ordering**: Turn phases use `after` field instead of numeric order
- **Comprehensive validation**: 90%+ of authoring errors caught at load time
- **Core field protection**: Runtime validation prevents accessing core fields via properties dict
- **Dedicated turn executor**: Clean separation of turn phase logic from protocol layer

## Design Thinking

### Current System Issues

**1. Tight Coupling to Engine Code**
Authors must import and reference `src/hooks.py` constants. This creates a dependency on engine internals and makes hook names implementation details rather than part of the authoring API.

**2. Ambiguous Hook Names**
Hook names like `npc_action` or `location_entered` don't indicate whether they're turn phases (global, runs once per turn) or entity hooks (runs per-entity). This leads to authoring errors where turn phases are attached to entities or vice versa.

**3. Validation Happens Too Late**
Most authoring errors (undefined hooks, wrong invocation type, turn phases on entities) only fail at runtime during gameplay, not at game load. This makes debugging harder and wastes development time.

**4. Fragile Turn Phase Ordering**
Turn phases use `extra_turn_phases` list in game_state.json with implicit numeric ordering. Dependencies between phases aren't explicit, making it easy to break execution order.

**5. Silent Property Access Bugs**
Code like `actor.properties.get('location')` returns None instead of raising an error, hiding bugs where core fields are accessed incorrectly.

### New System Architecture

**Vocabulary-Based Definitions**
Hooks are defined in behavior module vocabularies, not in engine code. Authors never need to look at `src/` files. Hook definitions are part of the behavior module's public API.

```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_environmental_effect",  # Note: hook_id, not hook
            "invocation": "turn_phase",
            "after": [TurnHookId("turn_npc_action")],  # Typed IDs
            "before": [],  # Optional - can run before specified hooks
            "description": "Apply environmental hazards"
        }
    ],
    "events": [
        {
            "event": "on_environmental_effect",
            "hook": "turn_environmental_effect"  # String reference to hook_id
        }
    ]
}
```

**Self-Documenting Prefixes**
- `turn_*` hooks are turn phases (invoked once per turn, `entity=None`)
- `entity_*` hooks are entity-specific (invoked per-entity)

This makes invocation pattern obvious from the hook name alone.

**Load-Time Validation**
BehaviorManager validates all hook definitions during game load:
- Prefixes match invocation type
- Dependencies reference defined hooks
- Turn phases not attached to entities
- No circular dependencies (cycles in `after`/`before` constraints)
- No impossible constraints (e.g., A before B and B before A via different paths)

90%+ of authoring errors caught before gameplay starts with clear error messages.

**Bidirectional Dependencies**
Turn phases use `after` and `before` fields to declare dependencies:
- `after: List[TurnHookId]` - This hook runs after the specified hooks
- `before: List[TurnHookId]` - This hook runs before the specified hooks

This allows game-specific hooks to insert themselves into library execution order without modifying library code. Turn executor builds execution order via topological sort. Dependencies are explicit and validated.

**Layer Ordering**: Games can declare hooks that run before library hooks using `before`, enabling clean extension without modifying deeper layers.

**Runtime Protection**
CoreFieldProtectingDict wraps entity properties dicts and raises TypeError on attempts to set core fields. Error message guides author to correct usage.

### Data Flow

1. **Load Time** (game_engine.py):
   ```
   Load game_state.json
   → BehaviorManager.load_all_behaviors()
   → Process vocabularies, collect hook_definitions
   → Run validation (prefixes, dependencies, placement)
   → turn_executor.initialize(hook_definitions)
   → Topological sort, cache execution order
   ```

2. **Turn Execution** (llm_protocol.py):
   ```
   Player command processed
   → turn_executor.execute_turn_phases(state, behavior_manager)
   → For each phase in sorted order:
       invoke_behavior(entity=None, hook=phase_name)
   → Collect narrations
   ```

3. **Entity Hook Invocation** (various handlers):
   ```
   Event occurs (actor enters location)
   → invoke_behavior(entity=actor, hook="entity_entered_location")
   → BehaviorManager finds event for hook
   → Executes handler function
   ```

### Benefits

**For Authors:**
- No need to reference engine code
- Hook names self-document usage
- Errors caught at load time with clear messages
- Explicit dependency ordering
- No silent property access bugs

**For Engine:**
- Clean separation: vocabularies define hooks, engine discovers them
- No hardcoded hook lists
- Turn phase ordering computed automatically
- Extensible: new hooks just need vocabulary definitions

**For Maintenance:**
- Single source of truth (vocabularies)
- No backward compatibility shims needed
- Easy to add new hooks without engine changes
- Validation prevents broken states

## Success Metrics

After all 9 phases complete:

- ✅ No files in `src/` define hooks
- ✅ Authors never look at `src/hooks.py` (doesn't exist)
- ✅ All hooks have clear invocation pattern from prefix
- ✅ 90%+ authoring errors caught at load time
- ✅ Core field access errors fail immediately with clear message
- ✅ All walkthroughs pass
- ✅ No legacy code or backward compatibility shims

## Lessons from Previous Attempt (Phases 1-3)

The previous implementation of Phases 1-3 was completed successfully but reverted due to:

1. **Uncommitted work got lost** - Work was done but never committed
2. **No cleanup plan** - After Phase 3 caught 838 test errors, there was no systematic plan to fix them
3. **LibCST tool issues** - The refactoring tool had bugs (double-underscore `__properties`, too broad scope)
4. **Confusion about baseline** - Unclear what the correct baseline was after changes

**This plan addresses these issues:**

### 1. Commit Strategy
- **Commit after each phase completes with all tests passing**
- Use git branches for safety: `feature/hook-system-phase-N`
- Never proceed to next phase with failing tests

### 2. Detailed Cleanup Plans
- Each phase has step-by-step implementation guide
- Clear success criteria for each step
- Rollback plans if things go wrong

### 3. Tool Improvements
- LibCST transformer properly scoped and tested
- Dry-run previews before applying changes
- Verification checks for common bugs

### 4. Baseline Tracking
- Document test count and status before/after each phase
- Clear "done" criteria before moving forward

---

# Phase-by-Phase Implementation Plan

## Phase 1: Core Infrastructure - Hook Definition Storage

**Status:** Needs re-implementation (was completed, then reverted)

### Goal
Add hook definition storage to BehaviorManager (temporary, for later handoff to turn_executor in Phase 7)

### Data Structure

```python
from dataclasses import dataclass
from typing import List
from src.types import TurnHookId

@dataclass
class HookDefinition:
    """Definition of a hook from a behavior module vocabulary."""
    hook: str                          # Hook name (e.g., "turn_environmental_effect")
    invocation: str                    # "turn_phase" or "entity"
    after: List[TurnHookId]            # Runs after these hooks (for turn phases only)
    before: List[TurnHookId]           # Runs before these hooks (for turn phases only)
    description: str                   # Human-readable description
    defined_by: str                    # Module that defined it (for error messages)
```

### Implementation

Add to `src/behavior_manager.py`:

```python
class BehaviorManager:
    def __init__(self):
        # Existing fields...
        self._hook_definitions: Dict[str, HookDefinition] = {}

    def _register_hook_definition(self, hook_def: Dict[str, Any], module_path: str) -> None:
        """Register a hook definition from a vocabulary."""
        hook_name = hook_def['hook']

        # Check for duplicates
        if hook_name in self._hook_definitions:
            existing = self._hook_definitions[hook_name]
            if existing.defined_by != module_path:
                raise ValueError(
                    f"Hook '{hook_name}' defined multiple times:\n"
                    f"  1. {existing.defined_by}\n"
                    f"  2. {module_path}"
                )
            return  # Same module re-defining - idempotent

        # Store hook definition
        # Convert string dependencies to typed IDs
        after = [TurnHookId(h) for h in hook_def.get('after', [])]
        before = [TurnHookId(h) for h in hook_def.get('before', [])]

        self._hook_definitions[hook_name] = HookDefinition(
            hook=hook_name,
            invocation=hook_def['invocation'],
            after=after,
            before=before,
            description=hook_def.get('description', ''),
            defined_by=module_path
        )

    def _register_vocabulary(self, module_path: str, vocabulary: Dict[str, Any]) -> None:
        """Register vocabulary from a behavior module."""
        # Existing code for verbs, events, etc...

        # NEW: Process hook definitions
        if 'hook_definitions' in vocabulary:
            for hook_def in vocabulary['hook_definitions']:
                self._register_hook_definition(hook_def, module_path)
```

### Tests

Create `tests/test_hook_definitions.py` with test cases for:
- Registering turn phase hooks
- Registering entity hooks
- Duplicate detection (different modules → error)
- Duplicate detection (same module → idempotent)
- Hook with dependencies stored correctly

### Success Criteria
- ✅ BehaviorManager can load hook definitions from vocabularies
- ✅ Duplicate detection works correctly
- ✅ All fields stored properly
- ✅ All tests pass
- ✅ **COMMIT:** "Phase 1: Hook definition storage in BehaviorManager"

### Files Modified
- `src/behavior_manager.py` - Add HookDefinition class and storage
- `tests/test_hook_definitions.py` - New test file

---

## Phase 2: Validation Suite

**Status:** Needs re-implementation (was completed, then reverted)

### Goal
Add 5 validation methods that catch 90%+ of authoring errors at load time.

### Validation Methods

All methods added to `src/behavior_manager.py`:

#### 1. validate_hook_prefixes()
Enforce `turn_*` for turn phases, `entity_*` for entity hooks.

#### 2. validate_turn_phase_dependencies()
Ensure `after` and `before` references point to defined turn phase hooks. Detect circular dependencies (cycles in the dependency graph). Raise ValueError for any impossible constraints with clear error messages identifying the conflicting hooks.

#### 3. validate_hooks_are_defined()
Ensure all event `hook` references point to defined hooks.

#### 4. validate_turn_phase_not_in_entity_behaviors()
Prevent turn phase behaviors in entity behaviors lists.

#### 5. validate_hook_invocation_consistency()
Ensure each hook used consistently (not as both turn_phase and entity).

### Validation Call Site

```python
def finalize_loading(self, game_state: GameState) -> None:
    """Call after all vocabularies loaded to run validations."""
    self.validate_hook_prefixes()
    self.validate_turn_phase_dependencies()
    self.validate_hooks_are_defined()
    self.validate_hook_invocation_consistency()
    self.validate_turn_phase_not_in_entity_behaviors(game_state)
```

### Tests

Create `tests/test_validation.py` with 26+ test cases covering:
- Valid cases (should not raise)
- Invalid cases (should raise ValueError with clear message)
- All edge cases

### Success Criteria
- ✅ All 5 validation methods implemented
- ✅ Validation called during finalization
- ✅ Comprehensive test coverage
- ✅ Clear error messages
- ✅ All tests pass
- ✅ **COMMIT:** "Phase 2: Validation suite for hook definitions"

### Files Modified
- `src/behavior_manager.py` - Add 5 validation methods + finalize_loading()
- `tests/test_validation.py` - New test file (26+ test cases)

**Full implementation details in:** [docs/designs/hook_system_redesign_phases_1-3.md](hook_system_redesign_phases_1-3.md) (Phase 2 section)

---

## Phase 3: Core Field Protection

**Status:** ✅ **COMPLETED** (2025-12-28)

### Goal
Add runtime protection to prevent core field access via properties dict.

### Implementation

1. **CoreFieldProtectingDict class** - Dict wrapper that raises TypeError on core field access
2. **Update entity classes** - Actor, Item, Location, Part use `_properties` with `@property` wrapper
3. **Update parsers** - JSON parsing handles `_properties` parameter
4. **LibCST refactoring** - Update ~70 test files to use `_properties=`
5. **Manual fixes** - Fix ~838 test code instances of core field access

### Phase 3 Cleanup Plan

**Critical:** This phase will cause ~838 test failures (catching real bugs). See detailed 9-step cleanup plan in [docs/designs/hook_system_redesign_phases_1-3.md](hook_system_redesign_phases_1-3.md) (Phase 3 Cleanup Plan section).

**Key steps:**
1. Implement CoreFieldProtectingDict (0 failures expected)
2. Update entity classes (don't run full suite yet)
3. Fix LibCST refactoring tool (test on single file first)
4. Run LibCST on all tests with dry-run preview
5. Analyze ~838 failures systematically
6. Fix test code in batches with checkpoint commits
7. Verify all tests pass
8. Verify big game still works
9. Documentation and cleanup

### Results

**All success criteria met!**

- ✅ CoreFieldProtectingDict prevents all core field assignments via properties dict
- ✅ Clear error messages guide developers: "Cannot set core field 'X' via properties dict. Use direct attribute access instead: entity.X = value"
- ✅ LibCST tool properly scoped with stack-based tracking for nested calls
- ✅ All test code fixed (10 files via LibCST, 2 manual fixes for conftest.py and _big_game_conditions_impl.py)
- ✅ All 2095 tests pass (5 skipped)
- ✅ Big game loads successfully (45 locations, 61 items, 43 actors)

**Real bugs caught by protection:**
- 3 game behaviors reading `location` via properties.get() (spore_zones.py, hypothermia.py, spore_mother.py)
- 6 game behaviors reading `inventory` via properties.get() (telescope_repair.py, ice_extraction.py, golem_puzzle.py, spore_zones.py, hypothermia.py, light_puzzle.py)
- 1 behavior library (crafting_lib/recipes.py) using properties= constructor param

**Commits:**
- 56c299f Phase 3: Add CoreFieldProtectingDict class and tests
- 0873ab2 Phase 3: Update entity classes to use _properties with protection
- aacf859 Phase 3: Fix LibCST refactoring tool for _properties rename
- e47e505 Phase 3: Refactor test code to use _properties parameter
- 9ba2798 Phase 3: Fix conftest.py and initial test errors
- 125da5b Phase 3: Fix all remaining test code and game behaviors
- 9397f05 Phase 3: Fix core field access bugs in game behaviors

### Success Criteria
- ✅ CoreFieldProtectingDict prevents all core field assignments
- ✅ Clear error messages guide authors
- ✅ LibCST tool properly scoped (no double-underscores)
- ✅ All test code fixed
- ✅ All 2095 tests pass
- ✅ Big game loads and plays
- ✅ **COMMITS:** 7 commits completing Phase 3

### Files Modified
- `src/state_manager.py` - CoreFieldProtectingDict + 4 entity classes + 4 parsers
- `tools/refactor_using_LibCST` - Fix transformer scoping
- `tests/**/*.py` - ~70 test files updated
- `tests/test_core_field_protection.py` - New test file (18+ test cases)

**Full implementation details in:** [docs/designs/hook_system_redesign_phases_1-3.md](hook_system_redesign_phases_1-3.md) (Phase 3 section)

---

## Phase 4: Core Hooks

**Status:** Not started

### Goal
Add hook_definitions to core behavior modules, converting from src/hooks.py constants.

### Hook Migrations

| Old Hook Name | New Hook Name | Invocation Type | Where Defined |
|---------------|---------------|-----------------|---------------|
| `location_entered` | `entity_entered_location` | `"entity"` | behaviors/core/exits.py |
| `visibility_check` | `entity_visibility_check` | `"entity"` | behaviors/core/perception.py |

### Implementation Strategy (Lessons from Phase 3)

**Incremental approach:**
1. Migrate one hook at a time
2. Add hook_definition to vocabulary
3. Update event to reference new hook name
4. Run tests to verify no breakage
5. Commit before moving to next hook

**Field name:** Use `hook_id` (not `hook`) to match actual implementation.

#### 1. Update behaviors/core/exits.py

Add to vocabulary:
```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_entered_location",  # Note: hook_id not hook
            "invocation": "entity",
            "description": "Called when an actor enters a new location"
        }
    ],
    "events": [
        {
            "event": "on_location_entered",
            "hook": "entity_entered_location"  # Updated from "location_entered"
        }
    ]
}
```

**Verification:**
```bash
# Find all invocations of this hook
grep -r 'location_entered' src/ tests/ behaviors/ behavior_libraries/ examples/

# Run tests
python -m unittest discover tests/
```

**Commit:** `git commit -m "Phase 4: Migrate entity_entered_location hook"`

#### 2. Update behaviors/core/perception.py

Add to vocabulary:
```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_visibility_check",  # Note: hook_id not hook
            "invocation": "entity",
            "description": "Called to determine if an entity is visible"
        }
    ],
    "events": [
        {
            "event": "on_visibility_check",
            "hook": "entity_visibility_check"  # Updated from "visibility_check"
        }
    ]
}
```

**Verification:**
```bash
# Find all invocations of this hook
grep -r 'visibility_check' src/ tests/ behaviors/ behavior_libraries/ examples/

# Run tests
python -m unittest discover tests/
```

**Commit:** `git commit -m "Phase 4: Migrate entity_visibility_check hook"`

#### 3. Update any code that directly invokes these hooks

If any code outside vocabularies invokes these hooks with old names, update them.

**Search commands:**
```bash
grep -r 'invoke_behavior.*location_entered' src/ tests/
grep -r 'invoke_behavior.*visibility_check' src/ tests/
```

### Tests

- Run existing tests after each migration - they should still pass (behavior unchanged, just renamed hooks)
- Verify hook definitions loaded correctly during game startup
- Verify Phase 2 validations pass (prefix checks, etc.)
- Expected: All 2095 tests pass (no new tests added in this phase)

### Success Criteria
- ✅ Core hooks defined in behavior vocabularies (not src/hooks.py)
- ✅ Hook names use `entity_*` prefix
- ✅ Hook field uses `hook_id` (matches implementation)
- ✅ All hook invocations updated to use new names
- ✅ All 2095 tests pass
- ✅ Validation passes (prefixes checked at load time)
- ✅ **COMMITS:** 2+ commits (one per hook migration)

### Files Modified
- `behaviors/core/exits.py` - Add hook_definition for entity_entered_location
- `behaviors/core/perception.py` - Add hook_definition for entity_visibility_check
- Any files that invoke these hooks - Update hook names (if any)

---

## Phase 5: Infrastructure Hooks

**Status:** Not started

### Goal
Add hook_definitions to infrastructure behavior libraries (turn phases).

### Hook Migrations

From reference plan:

| Old Hook Name | New Hook Name | Invocation Type | Where Defined |
|---------------|---------------|-----------------|---------------|
| `npc_action` | `turn_npc_action` | `"turn_phase"` | behavior_libraries/actor_lib/npc_actions.py |
| `environmental_effect` | `turn_environmental_effect` | `"turn_phase"` | behavior_libraries/actor_lib/environment.py |
| `condition_tick` | `turn_condition_tick` | `"turn_phase"` | behavior_libraries/actor_lib/conditions.py |
| `death_check` | `turn_death_check` | `"turn_phase"` | behavior_libraries/actor_lib/combat.py |

### Implementation Strategy (Same as Phase 4)

**Incremental approach:**
1. Migrate one hook at a time
2. Add hook_definition with dependencies
3. Update event to reference new hook name
4. Run tests to verify no breakage
5. Commit before moving to next hook

**Field name:** Use `hook_id` (not `hook`) to match implementation.

For each infrastructure module, add hook_definition to vocabulary:

```python
# Example: behavior_libraries/actor_lib/npc_actions.py
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_npc_action",  # Note: hook_id not hook
            "invocation": "turn_phase",
            "after": [],   # No dependencies
            "before": [],  # Optional, can be omitted if empty
            "description": "Execute NPC actions for the turn"
        }
    ],
    "events": [
        {
            "event": "on_npc_action",
            "hook": "turn_npc_action"  # Updated from "npc_action"
        }
    ]
}
```

**Dependencies to define:**
- `turn_npc_action`: `after: []`, `before: []` (no dependencies initially - will accept game hooks via `before`)
- `turn_environmental_effect`: `after: ["turn_npc_action"]`, `before: []`
- `turn_condition_tick`: `after: ["turn_environmental_effect"]`, `before: []`
- `turn_death_check`: `after: ["turn_condition_tick"]`, `before: []`

**Migration order:**
1. `turn_npc_action` first (no dependencies)
2. `turn_environmental_effect` second (depends on #1)
3. `turn_condition_tick` third (depends on #2)
4. `turn_death_check` last (depends on #3)

### Tests

- Run existing tests after each migration
- Verify Phase 2 dependency validation passes
- Verify no circular dependencies
- Expected: All 2095 tests pass after each migration

### Success Criteria
- ✅ All infrastructure hooks defined with proper prefixes
- ✅ Dependencies specified via `after` field
- ✅ All hook invocations updated to new names
- ✅ All 2095 tests pass
- ✅ Phase 2 validation passes (prefixes, dependencies checked)
- ✅ **COMMITS:** 4+ commits (one per hook migration)

### Files Modified
- `behavior_libraries/actor_lib/npc_actions.py` - turn_npc_action
- `behavior_libraries/actor_lib/environment.py` - turn_environmental_effect
- `behavior_libraries/actor_lib/conditions.py` - turn_condition_tick
- `behavior_libraries/actor_lib/combat.py` - turn_death_check

---

## Phase 6: Game Migration

**Status:** Not started

### Goal
Update big_game to use new hook system with proper prefixes and definitions.

### Tasks

#### 1. Remove extra_turn_phases from game_state.json

Delete this section:
```json
"extra_turn_phases": [
  "turn_phase_scheduled",
  "turn_phase_commitment",
  "turn_phase_gossip",
  "turn_phase_spread",
  "npc_action",
  "death_check"
]
```

Turn phases now discovered from hook definitions.

#### 2. Migrate infrastructure turn phases

Update 4 files in `examples/big_game/behaviors/shared/infrastructure/`:

| File | Old Hook | New Hook | After Dependencies |
|------|----------|----------|-------------------|
| scheduled_events.py | `turn_phase_scheduled` | `turn_scheduled_events` | `[]` (early) |
| commitments.py | `turn_phase_commitment` | `turn_commitments` | `["turn_scheduled_events"]` |
| gossip.py | `turn_phase_gossip` | `turn_gossip_spread` | `["turn_commitments"]` |
| spreads.py | `turn_phase_spread` | `turn_condition_spread` | `["turn_gossip_spread"]` |

#### 3. Migrate custom game hooks

From reference plan:

| File | Old Hook | New Hook | Invocation |
|------|----------|----------|------------|
| gift_reactions.py | `after_give` | `entity_gift_given` | `"entity"` |
| death_reactions.py | `on_actor_death` | `entity_actor_died` | `"entity"` |
| item_use_reactions.py | `after_item_use` | `entity_item_used` | `"entity"` |
| pack_mirroring.py | `after_actor_state_change` | `entity_state_changed` | `"entity"` |
| aldric_rescue.py | `receive_item` | `entity_item_received` | `"entity"` |
| waystone.py | `on_puzzle_solved` | `entity_puzzle_solved` | `"entity"` |
| waystone.py | `turn_phase_global` | `turn_ending_check` | `"turn_phase"` |

#### 4. Add hook_definitions to all behavior modules

Each module must add hook_definition section to vocabulary.

### Tests

- Run all big_game walkthroughs
- Verify game loads without errors
- Verify all turn phases fire in correct order
- Verify custom hooks still work

### Success Criteria
- ✅ extra_turn_phases removed from game_state.json
- ✅ All custom hooks use proper prefixes
- ✅ All behavior modules have hook_definitions
- ✅ All walkthroughs pass
- ✅ Game loads and plays correctly
- ✅ **COMMIT:** "Phase 6: Migrate big_game to new hook system"

### Files Modified
- `examples/big_game/game_state.json` - Remove extra_turn_phases
- `examples/big_game/behaviors/shared/infrastructure/*.py` - 4 files
- `examples/big_game/behaviors/regions/**/*.py` - Update custom hooks
- Multiple behavior modules - Add hook_definitions

---

## Phase 7: Turn Executor Module

**Status:** Not started

### Goal
Create dedicated turn_executor module with bidirectional dependency support, remove turn phase code from llm_protocol, and remove the Phase 6 workaround from library code.

### Implementation

#### 1. Create src/turn_executor.py

```python
"""Turn phase execution with dependency-based ordering."""

from typing import Dict, List
from src.behavior_manager import HookDefinition
from src.state_manager import GameState

_ordered_turn_phases: List[str] = []

def initialize(hook_definitions: Dict[str, HookDefinition]) -> None:
    """Sort and cache turn phases once at game load.

    Args:
        hook_definitions: All hook definitions from BehaviorManager

    Raises:
        ValueError: If circular dependencies detected
    """
    global _ordered_turn_phases

    # Filter to turn phases only
    turn_phases = {
        name: defn for name, defn in hook_definitions.items()
        if defn.invocation == "turn_phase"
    }

    # Topological sort by dependencies
    sorted_phases = _topological_sort(turn_phases)
    _ordered_turn_phases = sorted_phases

def _topological_sort(phases: Dict[str, HookDefinition]) -> List[str]:
    """Sort turn phases by dependencies using Kahn's algorithm.

    Handles both `after` and `before` constraints by building a unified
    dependency graph:
    - A.after=[B] creates edge B→A (A depends on B)
    - A.before=[C] creates edge A→C (C depends on A)

    Raises:
        ValueError: If circular dependencies detected (authoring error)
        ValueError: If impossible constraints detected (authoring error)
    """
    # Build directed graph from both after and before constraints
    # Use Kahn's algorithm for topological sort
    # Detect cycles and raise clear error with cycle path
    # No conflict resolution - all conflicts are authoring errors
    pass

def execute_turn_phases(state: GameState, behavior_manager) -> List[str]:
    """Execute all turn phases in dependency order.

    Returns:
        List of narration strings from each phase
    """
    narrations = []

    for hook_name in _ordered_turn_phases:
        # Invoke via behavior_manager
        result = behavior_manager.invoke_behavior(
            state=state,
            entity=None,  # Turn phases are global
            hook=hook_name
        )

        if result and result.narration:
            narrations.append(result.narration)

    return narrations
```

#### 2. Update src/game_engine.py

Call turn_executor.initialize() after loading behaviors:

```python
def load_game(self, game_state_path: str) -> None:
    """Load game state and behaviors."""
    # Existing code...
    self.behavior_manager.load_all_behaviors(game_state)

    # NEW: Initialize turn executor with hook definitions
    from src import turn_executor
    turn_executor.initialize(self.behavior_manager._hook_definitions)
```

#### 3. Update src/llm_protocol.py

**Delete ~110 lines:**
- `BASE_TURN_PHASE_HOOKS` constant
- `_get_turn_phase_hooks()` method
- `_fire_turn_phases()` method
- `_fire_commitment_phase()` method
- `_fire_scheduled_event_phase()` method
- `_fire_gossip_phase()` method
- `_fire_spread_phase()` method

**Replace with simple call:**

```python
def _execute_turn_phases(self, state: GameState) -> List[str]:
    """Execute turn phases and return narrations."""
    from src import turn_executor
    return turn_executor.execute_turn_phases(state, self.behavior_manager)
```

#### 4. Remove Phase 6 Workaround

In Phase 6, we added a temporary workaround where `turn_npc_action` depends on `turn_condition_spread` to ensure game infrastructure runs before library infrastructure. With bidirectional dependencies, we can now remove this workaround.

**Update behavior_libraries/actor_lib/npc_actions.py:**

```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_npc_action",
            "invocation": "turn_phase",
            "after": [],  # Remove temporary dependency on turn_condition_spread
            "before": [],
            "description": "Execute NPC actions for the turn"
        }
    ]
}
```

**Update examples/big_game/behaviors/shared/infrastructure/spreads.py:**

```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_condition_spread",
            "invocation": "turn_phase",
            "after": ["turn_gossip_spread"],
            "before": ["turn_npc_action"],  # Declare game hook runs before library
            "description": "Spread conditions between actors"
        }
    ]
}
```

This is the proper solution: game layer declares it runs before library layer using `before`, without modifying library code.

### Tests

Create `tests/test_turn_executor.py`:
- Test topological sort with valid dependencies (both `after` and `before`)
- Test bidirectional constraints (A before B creates same edge as B after A)
- Test circular dependency detection with clear cycle reporting
- Test turn phases execute in correct order
- Test narration collection
- Test game hooks can insert before library hooks via `before`

### Success Criteria
- ✅ turn_executor.py created with bidirectional dependency sorting
- ✅ Circular dependency detection works with clear error messages
- ✅ Turn phases execute in correct order respecting both `after` and `before`
- ✅ Phase 6 workaround removed from library code
- ✅ Game hooks properly insert via `before` field
- ✅ ~110 lines deleted from llm_protocol.py
- ✅ All tests pass
- ✅ All walkthroughs pass
- ✅ **COMMITS:** Multiple commits (turn_executor creation, workaround cleanup)

### Files Modified
- `src/turn_executor.py` - NEW FILE
- `src/game_engine.py` - Call turn_executor.initialize()
- `src/llm_protocol.py` - Delete turn phase code (~110 lines)
- `behavior_libraries/actor_lib/npc_actions.py` - Remove workaround dependency
- `examples/big_game/behaviors/shared/infrastructure/spreads.py` - Add `before` constraint
- `tests/test_turn_executor.py` - NEW FILE

---

## Phase 8: Delete Legacy Code

**Status:** Not started

### Goal
Remove src/hooks.py and update all code/tests that referenced it.

### Implementation

#### 1. Delete src/hooks.py

File is no longer needed - all hooks defined in vocabularies.

#### 2. Remove imports

Files that import from src/hooks.py (from reference plan):
- `src/llm_protocol.py`
- `behaviors/core/exits.py`
- `utilities/utils.py`
- `tests/test_turn_phase_dispatch.py`
- `tests/infrastructure/test_phase1_turn_phases.py`

Remove lines like:
```python
from src import hooks
```

Update any code using `hooks.LOCATION_ENTERED` to use string `"entity_entered_location"`.

#### 3. Update tests

Tests should reference hook names as strings or use test fixtures.

### Tests

- Run full test suite
- Verify no imports of src.hooks remain
- Verify all hook references work

### Success Criteria
- ✅ src/hooks.py deleted
- ✅ All imports removed
- ✅ All hook references updated to new names
- ✅ All tests pass
- ✅ **COMMIT:** "Phase 8: Delete src/hooks.py and legacy hook references"

### Files Modified
- `src/hooks.py` - **DELETE FILE**
- 5+ files - Remove imports, update hook references
- Test files - Update to use string hook names

---

## Phase 9: Documentation

**Status:** Not started

### Goal
Update all documentation to reflect new hook system.

### Documentation Updates

#### 1. Create docs/hook_system.md

New comprehensive guide covering:
- How to define hooks in vocabularies
- Prefix conventions (turn_* vs entity_*)
- Dependency ordering for turn phases
- Hook invocation patterns
- Common mistakes and validation errors
- Migration guide from old system

#### 2. Update docs/authoring_guide.md

- Remove references to src/hooks.py
- Add section on hook definitions
- Update examples to use new hook names
- Document validation errors and fixes

#### 3. Update docs/quick_reference.md

- Add hook definition syntax
- Add common hook patterns
- Update turn phase examples

#### 4. Update user_docs/architectural_conventions.md

- Document hook system architecture
- Explain vocabulary-based definitions
- Describe validation and turn executor

#### 5. Update README or main docs

- Mention hook system improvements
- Link to hook_system.md guide

### Success Criteria
- ✅ docs/hook_system.md created with comprehensive guide
- ✅ All docs updated to remove src/hooks.py references
- ✅ Examples use new hook names and prefixes
- ✅ Validation errors documented
- ✅ **COMMIT:** "Phase 9: Update documentation for new hook system"

### Files Modified
- `docs/hook_system.md` - NEW FILE
- `docs/authoring_guide.md` - Update
- `docs/quick_reference.md` - Update
- `user_docs/architectural_conventions.md` - Update
- Other docs as needed

---

## Implementation Workflow

Per CLAUDE.md Workflow B for large changes:

1. **Issue #307 is the top-level issue** (already exists)
2. **This document is the design** (replaces lost hook_system_redesign.md)
3. **Reopen phase issues #308, #309, #310** for Phases 1-3
4. **Create new phase issues #312-#315** for Phases 4-9
5. **For each phase:**
   - Implement using TDD
   - Follow commit strategy
   - Comment on issue when complete
   - Close issue
6. **When all phases complete:**
   - Comment on #307 summarizing work
   - Close #307

## Risk Assessment

### Risk: Phases 4-6 break existing game
**Mitigation:** Test walkthroughs after each phase, commit frequently

### Risk: Turn executor has bugs
**Mitigation:** Comprehensive tests for topological sort, circular dependency detection

### Risk: Documentation becomes stale
**Mitigation:** Phase 9 dedicated to docs, review all references

### Risk: Migration takes longer than expected
**Mitigation:** Phases are independent, can pause between phases

## Overall Timeline Estimate

Based on Phase 1-3 experience (~8 hours) and remaining work:

- **Phases 1-3:** 8-10 hours (re-implementation with better plan)
- **Phase 4:** 2-3 hours (straightforward hook migration)
- **Phase 5:** 2-3 hours (infrastructure hooks)
- **Phase 6:** 4-6 hours (big_game migration, many files)
- **Phase 7:** 3-4 hours (turn executor + topological sort)
- **Phase 8:** 1-2 hours (delete legacy code)
- **Phase 9:** 3-4 hours (comprehensive docs)

**Total:** 23-32 hours of focused work across all 9 phases

**Key to success:** Systematic approach, clear phase boundaries, frequent commits, comprehensive testing.

---

## Appendix: Bidirectional Dependencies Design

### Problem: Layer Ordering

During Phase 6 implementation, we discovered that game-specific infrastructure hooks need to run before library infrastructure hooks, but there was no clean way to achieve this without modifying library code.

**Example:** The game's `turn_condition_spread` hook needs to run before the library's `turn_npc_action` hook, but modifying `turn_npc_action` to depend on a game hook violates layering (libraries shouldn't know about games).

### Solution: `before` Field

Add bidirectional dependencies where hooks can declare both what they run `after` and what they run `before`.

**Data Structure:**
```python
@dataclass
class HookDefinition:
    hook: str
    invocation: str
    after: List[TurnHookId]   # This hook runs after these hooks
    before: List[TurnHookId]  # This hook runs before these hooks
    description: str
    defined_by: str
```

**Vocabulary Example:**
```python
# Library code (doesn't know about games)
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_npc_action",
            "invocation": "turn_phase",
            "after": [],   # No dependencies
            "before": [],  # Empty - games will declare they run before this
            "description": "Execute NPC actions"
        }
    ]
}

# Game code (extends library)
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_condition_spread",
            "invocation": "turn_phase",
            "after": ["turn_gossip_spread"],
            "before": ["turn_npc_action"],  # Game declares it runs before library
            "description": "Spread conditions"
        }
    ]
}
```

**Topological Sort:**
Build dependency graph from both `after` and `before` constraints:
- `A.after = [B]` creates edge `B → A` (A depends on B, so B must run first)
- `A.before = [C]` creates edge `A → C` (C depends on A, so A must run first)

Use Kahn's algorithm for topological sort. Cycles are authoring errors and must fail loudly with clear error messages showing the cycle path.

**Validation:**
- Both `after` and `before` lists must reference defined turn phase hooks
- No circular dependencies (detect cycles in combined graph)
- Contradictions (e.g., A before B and B before A via any path) are authoring errors

**Benefits:**
1. **Clean layering:** Games extend libraries without modifying library code
2. **Explicit:** Dependencies visible in hook definitions
3. **Symmetric:** `after` and `before` are intuitive mirror operations
4. **Validated:** Cycles and conflicts caught at load time
5. **Flexible:** Handles all ordering scenarios including complex multi-layer games

**Implementation:** Phase 7 creates turn_executor with bidirectional topological sort and removes the Phase 6 temporary workaround.
