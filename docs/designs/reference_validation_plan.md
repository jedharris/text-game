# Hook System Redesign - Reference Validation

## Current State Inventory

Based on comprehensive codebase search, here's every hook reference and how it maps to the new design:

---

## 1. CORE HOOKS (src/hooks.py) → Hook Definitions in Vocabularies

### Current (8 constants in src/hooks.py):
```python
LOCATION_ENTERED = "location_entered"
VISIBILITY_CHECK = "visibility_check"
NPC_ACTION = "npc_action"
ENVIRONMENTAL_EFFECT = "environmental_effect"
CONDITION_TICK = "condition_tick"
DEATH_CHECK = "death_check"
TURN_PHASE_SCHEDULED = "turn_phase_scheduled"
TURN_PHASE_COMMITMENT = "turn_phase_commitment"
TURN_PHASE_GOSSIP = "turn_phase_gossip"
TURN_PHASE_SPREAD = "turn_phase_spread"
```

### New Design Mapping:
**All hooks defined in behavior module vocabularies with new naming:**

| Old Hook Name | New Hook Name | Invocation Type | Where Defined |
|---------------|---------------|-----------------|---------------|
| `location_entered` | `entity_entered_location` | `"entity"` | behaviors/core/exits.py |
| `visibility_check` | `entity_visibility_check` | `"entity"` | behaviors/core/perception.py |
| `npc_action` | `turn_npc_action` | `"turn_phase"` | behavior_libraries/actor_lib/npc_actions.py |
| `environmental_effect` | `turn_environmental_effect` | `"turn_phase"` | behavior_libraries/actor_lib/environment.py |
| `condition_tick` | `turn_condition_tick` | `"turn_phase"` | behavior_libraries/actor_lib/conditions.py |
| `death_check` | `turn_death_check` | `"turn_phase"` | behavior_libraries/actor_lib/combat.py |
| `turn_phase_scheduled` | `turn_scheduled_events` | `"turn_phase"` | examples/big_game/.../scheduled_events.py |
| `turn_phase_commitment` | `turn_commitments` | `"turn_phase"` | examples/big_game/.../commitments.py |
| `turn_phase_gossip` | `turn_gossip_spread` | `"turn_phase"` | examples/big_game/.../gossip.py |
| `turn_phase_spread` | `turn_condition_spread` | `"turn_phase"` | examples/big_game/.../spreads.py |

**Action**: Delete `src/hooks.py` entirely (Phase 8)

---

## 2. EXTRA_TURN_PHASES in game_state.json → Hook Definitions

### Current (examples/big_game/game_state.json lines 8-15):
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

### New Design Mapping:
**Removed entirely** - Turn phases discovered from hook definitions, ordering via `after` field.

Example in scheduled_events.py vocabulary:
```python
"hook_definitions": [{
    "hook_id": "turn_scheduled_events",  # Note: hook_id not hook
    "invocation": "turn_phase",
    "after": [],  # No dependencies - runs early
    "description": "Process scheduled events"
}]
```

**Action**: Remove `extra_turn_phases` from game_state.json metadata (Phase 6)

---

## 3. TURN PHASE EXECUTION CODE → turn_executor Module

### Current (src/llm_protocol.py lines 398-520):
- `BASE_TURN_PHASE_HOOKS` constant (line 42)
- `_get_turn_phase_hooks()` method (line 398)
- `_fire_turn_phases()` method (line 411)
- `_fire_commitment_phase()` method (line 473)
- `_fire_scheduled_event_phase()` method (line 484)
- `_fire_gossip_phase()` method (line 495)
- `_fire_spread_phase()` method (line 506)

### New Design Mapping:
**All replaced by `src/turn_executor.py`:**

```python
# src/turn_executor.py
def initialize(hook_definitions: Dict[str, HookDefinition]) -> None:
    """Sort and cache turn phases once."""
    global _ordered_turn_phases
    # Filter, sort, cache

def execute_turn_phases(accessor: StateAccessor) -> List[str]:
    """Execute all turn phases in cached order."""
    for hook_name in _ordered_turn_phases:
        # Execute via invoke_behavior
```

**No special-case phase methods** - infrastructure hooks (commitments, gossip, etc.) handled same as core turn phases.

**Action**: Delete all turn phase code from llm_protocol.py (Phase 7 task 3)

---

## 4. CUSTOM GAME HOOKS → Hook Definitions

### Current (big_game custom hooks without src/hooks.py):

| Hook Name | File | Usage |
|-----------|------|-------|
| `after_give` | gift_reactions.py | Entity-specific gift handling |
| `on_actor_death` | death_reactions.py | Death consequence handling |
| `after_item_use` | item_use_reactions.py | Item use reactions |
| `after_actor_state_change` | pack_mirroring.py | Pack synchronization |
| `receive_item` | aldric_rescue.py | NPC item reception |
| `on_puzzle_solved` | waystone.py | Puzzle completion |
| `turn_phase_global` | waystone.py | Ending check turn phase |

### New Design Mapping:
**All require hook definitions with proper prefixes:**

| Old Hook | New Hook | Invocation | Validation Issue |
|----------|----------|------------|------------------|
| `after_give` | `entity_gift_given` | `"entity"` | ✅ Prefix required |
| `on_actor_death` | `entity_actor_died` | `"entity"` | ✅ Prefix required |
| `after_item_use` | `entity_item_used` | `"entity"` | ✅ Prefix required |
| `after_actor_state_change` | `entity_state_changed` | `"entity"` | ✅ Prefix required |
| `receive_item` | `entity_item_received` | `"entity"` | ✅ Prefix required |
| `on_puzzle_solved` | `entity_puzzle_solved` | `"entity"` | ✅ Prefix required |
| `turn_phase_global` | `turn_ending_check` | `"turn_phase"` | ✅ Prefix + dependencies |

**Action**: Update all custom hooks to use prefixes, add hook_definitions (Phase 6)

---

## 5. BEHAVIOR MANAGER HOOK STORAGE → Validated Handoff

### Current (src/behavior_manager.py line 57-58):
```python
# Hook to event mapping: hook_name -> (event_name, tier)
self._hook_to_event: Dict[str, Tuple[str, int]] = {}
```

Methods:
- `_register_event()` - Registers hook from event specs
- `get_event_for_hook()` - Retrieves event for hook
- `get_hooks()` - Returns all registered hook names

### New Design Mapping:
**BehaviorManager stores hook definitions temporarily:**

```python
# In BehaviorManager
self._hook_definitions: Dict[str, HookDefinition] = {}

def _register_hook_definition(self, hook_def):
    """Store hook definition during vocabulary loading."""
    # Validate prefix, store definition

# After validation, handoff to turn_executor:
turn_executor.initialize(self._hook_definitions)
self._hook_definitions = {}  # Clear after handoff
```

**Still keeps `_hook_to_event` mapping** for `get_event_for_hook()` - used during turn execution.

**Action**: Add hook definition storage and validation (Phases 1-2), maintain event mapping

---

## 6. IMPORTS FROM src/hooks.py → None Needed

### Current (5 files import hooks):
- src/llm_protocol.py (line 26)
- behaviors/core/exits.py
- utilities/utils.py
- tests/test_turn_phase_dispatch.py
- tests/infrastructure/test_phase1_turn_phases.py

### New Design Mapping:
**All imports removed:**
- Core behaviors define hooks in vocabularies
- llm_protocol doesn't fire turn phases
- Tests reference hook names as strings or use test fixtures

**Action**: Remove all `from src import hooks` imports (Phase 8)

---

## 7. VALIDATION COVERAGE

### Design Handles All Current Cases:

✅ **Core turn phases** - Converted to `turn_*` with dependencies defined
✅ **Infrastructure turn phases** - Same as core, just defined in game behaviors
✅ **Entity-specific hooks** - Converted to `entity_*` prefix
✅ **Custom game hooks** - Must add `hook_definitions` and prefixes
✅ **Extra turn phases** - Replaced by discovery + dependency ordering
✅ **Hook execution** - Moved to turn_executor module
✅ **Per-entity dispatch** - Still entity-specific hooks, invoked same way

### Only Breaking Change for Authors:

**Must add hook_definitions to vocabularies:**

```python
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_environmental_effect",  # Note: hook_id not hook
            "invocation": "turn_phase",
            "after": ["turn_npc_action"],
            "description": "Apply environmental hazards"
        }
    ],
    "events": [
        {
            "event": "on_environmental_effect",
            "hook": "turn_environmental_effect"  # Event still uses "hook" field
        }
    ]
}
```

**Migration checklist per behavior module:**
1. Add `hook_definitions` section to vocabulary with `hook_id` field
2. Rename hook to use prefix (`turn_*` or `entity_*`)
3. Add dependencies via `after` field (for turn phases only)
4. Update event `hook` reference to match new hook name

---

## 8. EDGE CASES AND CONCERNS

### Edge Case 1: Infrastructure Turn Phases (commitments, gossip, etc.)
**Current**: Special `_fire_*_phase()` methods that iterate entities and dispatch
**New**: Standard turn phase hooks with `entity=None`, handler iterates internally
**Status**: ✅ Works - handlers already iterate, just removing special dispatch

### Edge Case 2: Hooks with Same Name, Different Invocation
**Example**: Could someone define `turn_environmental_effect` as both turn_phase and entity?
**Validation**: BehaviorManager.validate_hook_definitions() catches this (Phase 2)
**Status**: ✅ Caught at load time

### Edge Case 3: Hook Referenced But Never Defined
**Example**: Event says `"hook": "turn_custom"` but no hook_definition exists
**Validation**: BehaviorManager.validate_hooks_are_defined() catches this (Phase 2)
**Status**: ✅ Caught at load time

### Edge Case 4: Circular Dependencies in Turn Phases
**Example**: A→B→C→A
**Validation**: turn_executor.initialize() detects via topological sort (Phase 7)
**Status**: ✅ Caught at game load

### Edge Case 5: Turn Phase in entity.behaviors List
**Example**: Entity behaviors includes "behaviors.regions.fungal_depths.spore_zones"
**Validation**: BehaviorManager.validate_turn_phase_placement() catches this (Phase 2)
**Status**: ✅ Caught at load time

---

## 9. MIGRATION IMPACT SUMMARY

### Files Requiring Changes:

**Phase 1 (Core Infrastructure):**
- `src/behavior_manager.py` - Add HookDefinition storage

**Phase 2 (Validation):**
- `src/behavior_manager.py` - Add 6 validation methods
- `tests/test_validation.py` - New validation tests

**Phase 3 (Core Field Protection):**
- `src/state_manager.py` - CoreFieldProtectingDict

**Phase 4 (Core Hooks):**
- `behaviors/core/exits.py` - Add hook_definition for entity_entered_location
- `behaviors/core/perception.py` - Add hook_definition for entity_visibility_check
- `behaviors/core/turn_phases.py` - NEW FILE with 4 turn phase definitions

**Phase 5 (Infrastructure Hooks):**
- `behavior_libraries/actor_lib/npc_actions.py` - Add hook_definition
- `behavior_libraries/actor_lib/environment.py` - Add hook_definition
- `behavior_libraries/actor_lib/conditions.py` - Add hook_definition
- `behavior_libraries/actor_lib/combat.py` - Add hook_definition

**Phase 6 (Game Migration):**
- `examples/big_game/game_state.json` - Remove extra_turn_phases
- `examples/big_game/behaviors/shared/infrastructure/*.py` - 4 files, add hook_definitions
- `examples/big_game/behaviors/shared/infrastructure/*.py` - 4 files, update custom hooks
- `examples/big_game/behaviors/regions/**/*.py` - Update custom hooks (waystone, aldric, spore_zones)

**Phase 7 (Turn Executor):**
- `src/turn_executor.py` - NEW FILE
- `src/game_engine.py` - Call turn_executor.initialize()
- `src/llm_protocol.py` - Delete ~110 lines of turn phase code

**Phase 8 (Cleanup):**
- `src/hooks.py` - DELETE FILE
- All test files using hooks - Update to use new names

---

## 10. DESIGN VALIDATION: APPROVED ✅

**All current hook references accounted for:**
- ✅ 8 core hooks from src/hooks.py → vocabularies
- ✅ 7 custom game hooks → vocabularies with prefixes
- ✅ extra_turn_phases → removed, replaced by discovery
- ✅ Turn phase execution code → turn_executor module
- ✅ Hook validation → BehaviorManager + turn_executor
- ✅ All edge cases covered by validation

**No orphaned references found.**

**Design is complete and ready for implementation.**
