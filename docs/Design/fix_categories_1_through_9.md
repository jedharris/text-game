# Fix General Code Test Failures

## Context
Issue #454 renamed `behaviors/` to `game_behaviors/` across all 7 example games. The rename itself introduces zero test failures. The current test suite has 74 failures and 32 errors, all pre-existing. Game-specific failures are tracked separately in issue #455 and `docs/Design/game_specific_test_failures.md`.

## Root Causes

After investigation, the general code issues reduce to **4 independent root causes**.

### Root Cause A: `entity_` prefix violations on entity hooks (Original Cat 1)
**DONE** — fixed 4 hooks: `item_taken`, `trade_initiated`, `location_entry`, `commitment_state_change`.

Reduced errors from 43 to 32. Remaining big_game loading failures are caused by game-specific issue GS-1 (waystone `turn_death_check` dependency).

### Root Cause B: Long-path imports in tests (Original Cat 2)
**Impact: 0 current failures, but architectural risk**

Tests import via `from examples.big_game.game_behaviors...` (long path) while the engine loads modules via `game_behaviors...` (short path). No current failures since no `mock.patch` is used, but any future test using `mock.patch` on these modules will break.

**Fix:**
1. Change all test imports from `from examples.*.game_behaviors...` to `from game_behaviors...` (short path), adding `sys.path` setup in test files that need it.
2. Add a `conftest.py` check that detects dual-import violations at test collection time.
3. Add a CI-usable grep check that flags long-path imports in test files.

### Root Cause C: ContainerInfo missing `items` property (Original Cat 6)
**Impact: 4 errors**

`containers.py:on_open` does `entity.container.items` but `ContainerInfo` has no `items` property. Items in containers are tracked by `item.location == container.id`, accessed via `accessor.get_entities_at(container_id, entity_type="item")`.

**Fix:** Change `containers.py` to use `accessor.get_entities_at()` instead of `entity.container.items`.

### Root Cause D: Tests expect `state_variants` in serialized output (Original Cat 9)
**Impact: 4 failures (2 in test_json_protocol, 2 in test_entity_serializer)**

`entity_serializer.py` intentionally strips `state_variants` from output after selecting the active variant — the LLM should see only the selected variant, not the full variants dict. Tests were written expecting the old behavior where variants were preserved.

**Fix:** Update tests to assert `state_variants` is NOT in the output, and instead assert the selected variant IS applied.

### Root Cause E: Exit migration fixtures are empty stubs (Original Cat 8)
**DONE** — Migration is complete (all 7 games use exit entities, zero old-format exits remain). Deleted `tests/test_exit_migration.py` and `tests/fixtures/exit_migration/`. Migration convention documented in `docs/Guides/migration_guide.md`.

## Moved to game-specific (issue #455)

The following were originally in this plan but are game-specific:
- **Original Root Cause C** (wrong handler names in test fixtures, wrong E2E routes) → GS-8, GS-16
- **Original Root Cause E** (test mock data format mismatches: bear cubs state_machine, ScenarioState get_item, hypothermia conditions format) → GS-4, GS-7, GS-9

## Phases

### Phase 1: Fix entity hook naming — DONE
Fixed 4 hooks with `entity_` prefix violations. Errors reduced 43 → 32.

### Phase 2: Fix ContainerInfo usage (Root Cause C)
1. Change `containers.py:on_open` to use `accessor.get_entities_at(entity.id, entity_type="item")`
2. Run container-related tests

### Phase 3: Fix `state_variants` test expectations (Root Cause D)
1. Update `test_json_protocol.py` tests to expect `state_variants` stripped
2. Update `test_entity_serializer.py` tests to expect `state_variants` stripped
3. Both should instead assert the selected variant is applied correctly

### Phase 4: Delete exit migration artifacts — DONE
Migration complete. Deleted test file and fixtures.

### Phase 5: Add guardrails for dual-import risk (Root Cause B)

Import canonicalization was attempted but reverted — multiple games have `game_behaviors/`
directories, so only one game dir can be on sys.path at a time. Module-level imports in
test files must use the long path (`from examples.big_game.game_behaviors...`) since the
game dir isn't on sys.path at import time. The long-path imports are correct.

The risk is specifically `mock.patch()` with a long-path target on a module loaded via
short path at runtime. Guardrails:

1. Add CI grep check that flags `mock.patch` targets using `examples.*.game_behaviors`
2. Document in test_style_guide.md that long-path imports are correct for multi-game
   tests, but `mock.patch` targets must match the import path used by the code under test

## Estimated effort
Moderate — most fixes are small and mechanical. Phase 5 is the largest due to ~60 import statements across ~20 files, but it's straightforward. Each phase has clear TDD: run the affected tests before and after.
